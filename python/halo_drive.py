#!/usr/bin/env python3
"""Grok-native continuous drive — Stop decision:block is IGNORED by Grok Build.

Official Grok hooks docs: only PreToolUse is blocking; Stop is passive.
Halo still emits Ralph-compatible JSON for Claude-compatible hosts, but on Grok
the real continue path is:

  1) headless: grok --prompt-file .halo/NEXT_PROMPT.md --cwd TARGET --always-approve
  2) scheduler / /loop injecting a synthetic user turn into the TUI session

This module implements (1) with a single-runner lock to avoid fork bombs.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def work_remains(repo: Path) -> bool:
    state = _json(repo / ".halo" / "state.json")
    if not state:
        return False
    if state.get("HALO_KILL_SWITCH"):
        return False
    status = (state.get("status") or "ACTIVE").upper()
    if status in ("PAUSED", "ESCALATED", "COMPLETE"):
        return False
    if (state.get("phase") or "") == "complete":
        return False
    loop = _json(repo / ".halo" / "loop.json")
    if loop and not loop.get("active", True):
        return False
    # feature-list: if all pass and total>0, still allow drive if autonomous wants more
    # (agent may seed next milestone). Only stop if loop inactive.
    return bool(state.get("autonomous") or loop.get("active"))


def loop_active(repo: Path) -> bool:
    state = _json(repo / ".halo" / "state.json")
    loop = _json(repo / ".halo" / "loop.json")
    if state.get("HALO_KILL_SWITCH"):
        return False
    if (state.get("status") or "").upper() in ("PAUSED", "ESCALATED", "COMPLETE"):
        return False
    return bool(loop.get("active") or state.get("autonomous"))


def drive_lock_path(repo: Path) -> Path:
    return repo / ".halo" / "drive.lock"


def acquire_drive_lock(repo: Path, ttl_sec: int = 3600) -> bool:
    """Single headless driver at a time."""
    lp = drive_lock_path(repo)
    lp.parent.mkdir(parents=True, exist_ok=True)
    now = time.time()
    if lp.exists():
        try:
            data = json.loads(lp.read_text(encoding="utf-8"))
            if data.get("expires_at", 0) > now:
                pid = data.get("pid")
                if pid and _pid_alive(int(pid)):
                    return False
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    payload = {
        "pid": os.getpid(),
        "acquired_at": utc_now(),
        "expires_at": now + ttl_sec,
    }
    lp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return True


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def release_drive_lock(repo: Path) -> None:
    lp = drive_lock_path(repo)
    try:
        if lp.exists():
            data = json.loads(lp.read_text(encoding="utf-8"))
            if data.get("pid") == os.getpid():
                lp.unlink(missing_ok=True)
    except (json.JSONDecodeError, OSError):
        lp.unlink(missing_ok=True)


def ensure_next_prompt(repo: Path, halo_sys: Path | None = None) -> Path:
    prompt = repo / ".halo" / "NEXT_PROMPT.md"
    if prompt.exists() and prompt.stat().st_size > 50:
        return prompt
    hs = halo_sys or Path(os.environ.get("HALO_SYSTEM") or Path(__file__).resolve().parent.parent)
    cmd = [
        sys.executable,
        str(hs / "python" / "halo_next_prompt.py"),
        "--repo",
        str(repo),
        "--halo-system",
        str(hs),
        "--write",
    ]
    subprocess.run(cmd, check=False, capture_output=True, timeout=45)
    return prompt


def spawn_headless(
    repo: Path,
    *,
    max_turns: int = 80,
    force: bool = False,
    halo_sys: Path | None = None,
) -> dict[str, Any]:
    """Spawn grok -p with NEXT_PROMPT. Fail closed if loop inactive or locked."""
    repo = repo.resolve()
    if os.environ.get("HALO_NO_SPAWN") == "1" and not force:
        return {"ok": False, "error": "HALO_NO_SPAWN=1"}
    if not loop_active(repo) and not force:
        return {"ok": False, "error": "loop inactive"}
    if not work_remains(repo) and not force:
        return {"ok": False, "error": "no work remains"}

    grok = shutil.which("grok")
    if not grok:
        return {"ok": False, "error": "grok not on PATH"}

    if not acquire_drive_lock(repo):
        return {"ok": False, "error": "drive.lock held (another driver running)"}

    prompt = ensure_next_prompt(repo, halo_sys)
    if not prompt.exists():
        release_drive_lock(repo)
        return {"ok": False, "error": "NEXT_PROMPT missing"}

    log_dir = repo / ".halo" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"drive-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.log"

    # NOTE: Do NOT use `grok -p --prompt-file` — `-p/--single` requires a
    # positional prompt value, so `-p --prompt-file` fails CLI parse.
    # Correct headless: --prompt-file alone + --always-approve (not --yolo).
    cmd = [
        grok,
        "--prompt-file",
        str(prompt),
        "--cwd",
        str(repo),
        "--always-approve",
        "--max-turns",
        str(max_turns),
    ]
    # Prefer plugin trust if available
    try:
        with log_path.open("w", encoding="utf-8") as logf:
            logf.write(f"# halo_drive spawn {utc_now()}\n# cmd: {' '.join(cmd)}\n\n")
            logf.flush()
            proc = subprocess.Popen(
                cmd,
                cwd=str(repo),
                stdout=logf,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                env={**os.environ, "HALO_SYSTEM": str(halo_sys or os.environ.get("HALO_SYSTEM") or ""), "HALO_DRIVE": "1"},
            )
    except OSError as e:
        release_drive_lock(repo)
        return {"ok": False, "error": str(e)}

    # lock held by child conceptually — write child pid into lock
    drive_lock_path(repo).write_text(
        json.dumps(
            {
                "pid": proc.pid,
                "acquired_at": utc_now(),
                "expires_at": time.time() + 7200,
                "log": str(log_path),
                "mode": "headless",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    meta = {
        "ok": True,
        "pid": proc.pid,
        "log": str(log_path),
        "prompt": str(prompt),
        "protocol": "headless-spawn",
        "note": "Grok Stop is passive; headless re-entry is the real continue path",
    }
    (repo / ".halo" / "drive-last.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def scheduler_prompt(repo: Path) -> str:
    """Text for Grok /loop or scheduler_create — same-session inject."""
    return (
        f"Halo autonomous drive (Grok-native). TARGET={repo}. "
        "Read .halo/NEXT_PROMPT.md and .halo/baton.md and .halo/state.json. "
        "If autonomous or loop active and not COMPLETE/PAUSED/ESCALATED: "
        "load skill halo-go; execute ONE unit only; never ask; "
        "refresh NEXT_PROMPT via `halo continue .`; "
        "evidence-gated feature pass; never force-add .halo/ when dogfooding factory. "
        "If loop inactive or phase complete: stop and do nothing."
    )


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_drive")
    p.add_argument("--repo", default=".")
    p.add_argument("--halo-system", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("spawn", help="spawn headless grok -p with NEXT_PROMPT")
    s.add_argument("--force", action="store_true")
    s.add_argument("--max-turns", type=int, default=80)

    sub.add_parser("status", help="show drive/loop status")
    sub.add_parser("scheduler-prompt", help="print prompt text for /loop or scheduler")
    sub.add_parser("should-drive", help="exit 0 if drive should continue")

    args = p.parse_args()
    repo = Path(args.repo).resolve()
    hs = Path(args.halo_system).resolve() if args.halo_system else None

    if args.cmd == "spawn":
        r = spawn_headless(repo, max_turns=args.max_turns, force=args.force, halo_sys=hs)
        print(json.dumps(r, indent=2))
        raise SystemExit(0 if r.get("ok") else 2)
    if args.cmd == "status":
        print(
            json.dumps(
                {
                    "loop_active": loop_active(repo),
                    "work_remains": work_remains(repo),
                    "lock": _json(drive_lock_path(repo)),
                    "last": _json(repo / ".halo" / "drive-last.json"),
                    "state_status": _json(repo / ".halo" / "state.json").get("status"),
                    "phase": _json(repo / ".halo" / "state.json").get("phase"),
                },
                indent=2,
            )
        )
        return
    if args.cmd == "scheduler-prompt":
        print(scheduler_prompt(repo))
        return
    if args.cmd == "should-drive":
        raise SystemExit(0 if loop_active(repo) and work_remains(repo) else 1)


if __name__ == "__main__":
    main()
