#!/usr/bin/env python3
"""ACP supervisor for Halo continuous drive.

Runs `grok agent stdio` and drives one repo session by repeatedly sending the
NEXT_PROMPT as a session/prompt. This avoids the per-turn `grok --prompt-file`
spawn tree and keeps a single long-lived Grok session.

Docs: https://docs.x.ai/build/cli/headless-scripting (ACP section)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from queue import Queue
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _set_loop_inactive(repo: Path, reason: str = "acp_done") -> None:
    loop_p = repo / ".halo" / "loop.json"
    if not loop_p.exists():
        return
    try:
        d = _json(loop_p)
        d["active"] = False
        d["stopped_reason"] = reason
        d["stopped_at"] = utc_now()
        _write_json(loop_p, d)
    except Exception:  # noqa: BLE001
        pass


def _increment_iteration(repo: Path) -> int:
    loop_p = repo / ".halo" / "loop.json"
    if not loop_p.exists():
        return 0
    try:
        d = _json(loop_p)
        d["iteration"] = int(d.get("iteration", 0)) + 1
        d["last_turn_at"] = utc_now()
        _write_json(loop_p, d)
        return int(d["iteration"])
    except Exception:  # noqa: BLE001
        return 0


def _should_continue(repo: Path) -> tuple[bool, str]:
    """Return (continue, reason)."""
    if (repo / ".halo" / "OFF").exists():
        return False, "OFF kill switch"
    state = _json(repo / ".halo" / "state.json")
    loop = _json(repo / ".halo" / "loop.json")
    status = (state.get("status") or "ACTIVE").upper()
    phase = (state.get("phase") or "").lower()
    if status in ("PAUSED", "ESCALATED", "BLOCKED", "COMPLETE"):
        return False, f"state.status={status}"
    if phase == "complete":
        return False, "phase=complete"
    if not (loop.get("active") or state.get("autonomous")):
        return False, "loop not active and not autonomous"
    iteration = int(loop.get("iteration", 0))
    max_iter = int(loop.get("max_iterations", state.get("autonomous_max_cycles", 50)))
    if iteration >= max_iter:
        _set_loop_inactive(repo, "max_iterations")
        return False, f"max_iterations={max_iter}"
    return True, ""


def _write_next_prompt(repo: Path, halo_sys: Path | None) -> Path:
    try:
        from halo_next_prompt import write_prompt

        write_prompt(repo, halo_sys)
    except Exception:  # noqa: BLE001
        pass
    return repo / ".halo" / "NEXT_PROMPT.md"


class ACPClient:
    """Minimal JSON-RPC client for `grok agent stdio`."""

    def __init__(
        self,
        repo: Path,
        grok: str = "grok",
        plugin_dir: str | None = None,
        model: str | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.repo = repo
        self.grok = grok
        self.plugin_dir = plugin_dir
        self.model = model
        self._env = env
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._next_id = 1
        self._pending: dict[int, threading.Event] = {}
        self._results: dict[int, Any] = {}
        self._updates: Queue[str] = Queue()
        self._reader_thread: threading.Thread | None = None
        self._stderr_thread: threading.Thread | None = None
        self._closed = False
        self.log_path: Path = repo / ".halo" / "logs" / "acp-supervisor.log"
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def _log(self, msg: str) -> None:
        line = f"[{utc_now()}] {msg}\n"
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(line)

    def start(self) -> None:
        if self._proc is not None:
            return
        # Build grok agent stdio command. Options that apply to the `agent`
        # subcommand are placed before the `stdio` subcommand.
        cmd: list[str] = [self.grok, "--no-auto-update", "agent", "--no-leader"]
        if self.plugin_dir:
            cmd.extend(["--plugin-dir", self.plugin_dir])
        if self.model:
            cmd.extend(["--model", self.model])
        cmd.append("stdio")
        self._log(f"start grok agent stdio cwd={self.repo} cmd={' '.join(cmd)}")
        env = {**os.environ, **(self._env or {})}
        if not env.get("GROK_SANDBOX"):
            env["GROK_SANDBOX"] = "workspace"
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(self.repo),
            text=True,
            bufsize=1,
            env=env,
        )
        self._reader_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader_thread.start()
        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stderr_thread.start()

    def _read_stdout(self) -> None:
        assert self._proc is not None
        assert self._proc.stdout is not None
        try:
            for line in self._proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    self._log(f"non-json stdout: {line[:200]}")
                    continue
                if msg.get("method") == "session/update":
                    update = msg.get("params", {}).get("update", {})
                    if update.get("sessionUpdate") == "agent_message_chunk":
                        text = update.get("content", {}).get("text") or ""
                        if text:
                            self._updates.put(text)
                elif "id" in msg:
                    req_id = int(msg["id"])
                    with self._lock:
                        self._results[req_id] = msg
                        ev = self._pending.pop(req_id, None)
                    if ev is not None:
                        ev.set()
                else:
                    self._log(f"ignored message: {msg.keys()}")
        except Exception as e:  # noqa: BLE001
            self._log(f"stdout reader exit: {e}")

    def _read_stderr(self) -> None:
        assert self._proc is not None
        assert self._proc.stderr is not None
        try:
            for line in self._proc.stderr:
                self._log(f"stderr: {line.rstrip()}")
        except Exception as e:  # noqa: BLE001
            self._log(f"stderr reader exit: {e}")

    def _request(self, method: str, params: dict[str, Any], timeout: float = 30.0) -> Any:
        with self._lock:
            req_id = self._next_id
            self._next_id += 1
            ev = threading.Event()
            self._pending[req_id] = ev
        assert self._proc is not None
        assert self._proc.stdin is not None
        payload = json.dumps({"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}) + "\n"
        self._log(f"-> {method} id={req_id}")
        try:
            self._proc.stdin.write(payload)
            self._proc.stdin.flush()
        except BrokenPipeError as e:
            self._log(f"stdin broken: {e}")
            raise RuntimeError("grok agent stdio stdin closed") from e
        if not ev.wait(timeout=timeout):
            self._log(f"timeout waiting for {method} id={req_id}")
            raise TimeoutError(f"{method} timeout after {timeout}s")
        with self._lock:
            msg = self._results.pop(req_id, {})
        if msg.get("error"):
            raise RuntimeError(msg["error"])
        self._log(f"<- {method} id={req_id} ok")
        return msg.get("result", {})

    def initialize(self, timeout: float = 30.0) -> dict[str, Any]:
        return self._request(
            "initialize",
            {
                "protocolVersion": 1,
                "clientCapabilities": {
                    "fs": {"readTextFile": True, "writeTextFile": True},
                    "terminal": True,
                },
            },
            timeout=timeout,
        )

    def authenticate(self, method_id: str, timeout: float = 30.0) -> Any:
        return self._request(
            "authenticate",
            {"methodId": method_id, "_meta": {"headless": True}},
            timeout=timeout,
        )

    def session_new(self, cwd: str, timeout: float = 30.0) -> str:
        result = self._request(
            "session/new",
            {"cwd": cwd, "mcpServers": []},
            timeout=timeout,
        )
        session_id = result.get("sessionId") if isinstance(result, dict) else None
        if not session_id:
            raise RuntimeError("session/new did not return sessionId")
        return str(session_id)

    def prompt(self, session_id: str, text: str, post_response_stable_ms: float = 500.0) -> dict[str, Any]:
        """Send session/prompt and return accumulated text + stopReason."""
        # drain old updates
        while not self._updates.empty():
            self._updates.get()
        turn_timeout = float(os.environ.get("HALO_ACP_TURN_TIMEOUT", "600"))
        # session/prompt returns completion metadata after the turn completes;
        # assistant text arrives as session/update chunks while we wait.
        result = self._request(
            "session/prompt",
            {"sessionId": session_id, "prompt": [{"type": "text", "text": text}]},
            timeout=turn_timeout,
        )
        self._log("session/prompt response received; draining remaining updates")
        chunks: list[str] = []
        deadline = time.time() + (post_response_stable_ms / 1000.0)
        while time.time() < deadline:
            try:
                chunk = self._updates.get(timeout=0.1)
                chunks.append(chunk)
                deadline = time.time() + (post_response_stable_ms / 1000.0)
            except Exception:
                break
        while not self._updates.empty():
            chunks.append(self._updates.get())
        full_text = "".join(chunks)
        stop_reason = result.get("stopReason") if isinstance(result, dict) else None
        self._log(f"prompt done: chars={len(full_text)} stop_reason={stop_reason}")
        return {"text": full_text, "stop_reason": stop_reason}

    def close(self) -> None:
        self._closed = True
        if self._proc is not None:
            for stream in (self._proc.stdin, self._proc.stdout, self._proc.stderr):
                if stream is not None:
                    try:
                        stream.close()
                    except Exception:  # noqa: BLE001
                        pass
            try:
                self._proc.terminate()
            except Exception:  # noqa: BLE001
                pass
            try:
                self._proc.wait(timeout=5.0)
            except Exception:  # noqa: BLE001
                try:
                    self._proc.kill()
                except Exception:  # noqa: BLE001
                    pass
            for t in (self._reader_thread, self._stderr_thread):
                if t and t.is_alive():
                    t.join(timeout=2.0)


def _acp_client_for_repo(repo: Path, halo_sys: Path, log: Any) -> ACPClient:
    grok = shutil.which("grok") or "grok"
    if not grok:
        raise RuntimeError("grok not found in PATH")
    model = os.environ.get("HALO_MODEL") or os.environ.get("GROK_DEFAULT_MODEL") or "grok-build"
    return ACPClient(
        repo,
        grok=grok,
        plugin_dir=str(halo_sys),
        model=model,
        env={"HALO_SYSTEM": str(halo_sys), "HALO_ACP": "1"},
    )


def _authenticate(client: ACPClient) -> None:
    init = client.initialize()
    auth_methods = {m.get("id") for m in init.get("authMethods", []) if isinstance(m, dict)}
    method_id: str | None = None
    if os.environ.get("XAI_API_KEY") and "xai.api_key" in auth_methods:
        method_id = "xai.api_key"
    elif "cached_token" in auth_methods:
        method_id = "cached_token"
    if not method_id:
        raise RuntimeError("No usable auth method; set XAI_API_KEY or run grok login")
    client.authenticate(method_id)


def run_supervisor(repo: Path, halo_sys: Path | None, max_iterations: int | None = None) -> int:
    """Run one ACP supervisor session. Returns shell exit code."""
    repo = repo.resolve()
    if halo_sys is None:
        halo_sys = Path(__file__).resolve().parent.parent

    log_path = repo / ".halo" / "logs" / "acp-supervisor.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        with log_path.open("a", encoding="utf-8") as f:
            f.write(f"[{utc_now()}] {msg}\n")

    log("supervisor start")
    client = _acp_client_for_repo(repo, halo_sys, log)
    try:
        client.start()
        _authenticate(client)
        session_id = client.session_new(str(repo))
        log(f"session_id={session_id}")
    except Exception as e:  # noqa: BLE001
        log(f"ACP setup failed: {e}")
        return 2

    try:
        while True:
            cont, reason = _should_continue(repo)
            if not cont:
                log(f"stop: {reason}")
                break

            prompt_path = _write_next_prompt(repo, halo_sys)
            if not prompt_path.exists():
                log("NEXT_PROMPT missing")
                break
            prompt_text = prompt_path.read_text(encoding="utf-8")

            iteration = _increment_iteration(repo)
            log(f"turn iteration={iteration} prompt_chars={len(prompt_text)}")
            result = client.prompt(session_id, prompt_text)
            log(f"turn result chars={len(result.get('text', ''))} stop_reason={result.get('stop_reason')}")

            # If halo-go set status to complete or disabled the loop, we exit next cycle.
            cont, reason = _should_continue(repo)
            if not cont:
                log(f"stop after turn: {reason}")
                break
    except Exception as e:  # noqa: BLE001
        log(f"supervisor error: {e}")
    finally:
        client.close()
        log("supervisor closed")

    return 0


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_acp_supervisor")
    p.add_argument("--repo", default=".")
    p.add_argument("--halo-system", default=None)
    p.add_argument("--max-iterations", type=int, default=None)
    args = p.parse_args()
    repo = Path(args.repo).resolve()
    hs = Path(args.halo_system).resolve() if args.halo_system else None
    raise SystemExit(run_supervisor(repo, hs, max_iterations=args.max_iterations))


if __name__ == "__main__":
    main()
