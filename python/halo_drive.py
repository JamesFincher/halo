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


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def clear_stale_drive_lock(repo: Path) -> dict[str, Any]:
    """Remove drive.lock if PID dead or expired (S016)."""
    lp = drive_lock_path(repo)
    if not lp.exists():
        return {"cleared": False, "reason": "absent"}
    try:
        data = json.loads(lp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        lp.unlink(missing_ok=True)
        return {"cleared": True, "reason": "corrupt"}
    now = time.time()
    pid = data.get("pid")
    expired = float(data.get("expires_at") or 0) <= now
    alive = bool(pid) and _pid_alive(int(pid))
    if expired or not alive:
        lp.unlink(missing_ok=True)
        return {
            "cleared": True,
            "reason": "expired" if expired else "dead_pid",
            "pid": pid,
        }
    return {"cleared": False, "reason": "held", "pid": pid}


def acquire_drive_lock(repo: Path, ttl_sec: int = 3600) -> bool:
    """Single headless driver at a time."""
    clear_stale_drive_lock(repo)
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


def _watchdog_status(repo: Path) -> dict[str, Any]:
    """PID + heartbeat age for continuous-drive observability (D075 roadmap)."""
    repo = Path(repo).resolve()
    pid_path = repo / ".halo" / "logs" / "watchdog.pid"
    hb_path = repo / ".halo" / "logs" / "watchdog-heartbeat.json"
    watchdog_pid: int | None = None
    alive = False
    if pid_path.is_file():
        try:
            raw = pid_path.read_text(encoding="utf-8").strip()
            watchdog_pid = int(raw) if raw else None
        except (ValueError, OSError):
            watchdog_pid = None
        if watchdog_pid is not None:
            alive = _pid_alive(watchdog_pid)
    age: float | None = None
    hb = _json(hb_path)
    at = hb.get("at") if isinstance(hb, dict) else None
    if at:
        try:
            # tolerate trailing Z
            ts = str(at).replace("Z", "+00:00")
            then = datetime.fromisoformat(ts)
            if then.tzinfo is None:
                then = then.replace(tzinfo=timezone.utc)
            age = max(0.0, (datetime.now(timezone.utc) - then).total_seconds())
        except (TypeError, ValueError, OSError):
            age = None
    return {
        "watchdog_pid": watchdog_pid,
        "watchdog_alive": alive,
        "heartbeat_age_sec": age,
    }


def _budget_status(repo: Path) -> dict[str, Any]:
    """Budget gate for drive status (D079).

    Vocabulary for agents: ALLOW | DEGRADE | PAUSE.
    Maps halo_budget HALT → PAUSE; exception → DEGRADE (never crash status).
    """
    repo = Path(repo).resolve()
    try:
        from halo_budget import check as budget_check

        raw = budget_check(repo)
        if not isinstance(raw, dict):
            return {"verdict": "DEGRADE", "reason": "budget check returned non-dict"}
        out = dict(raw)
        v = str(out.get("verdict") or "").upper()
        if v == "HALT":
            out["budget_verdict"] = "HALT"
            out["verdict"] = "PAUSE"
        elif v not in ("ALLOW", "DEGRADE", "PAUSE"):
            # unknown → DEGRADE so agents don't treat as green light
            out["budget_verdict"] = v or None
            out["verdict"] = "DEGRADE"
            out.setdefault("reason", f"unknown budget verdict {v!r}")
        else:
            out["verdict"] = v
        return out
    except Exception as e:  # noqa: BLE001 — status must stay readable
        return {"verdict": "DEGRADE", "reason": f"budget check failed: {e}"}


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
        stale = clear_stale_drive_lock(repo)
        loop = _json(repo / ".halo" / "loop.json")
        next_feat = None
        try:
            from halo_features import summary as feature_summary

            fs = feature_summary(repo, compound=False)
            next_feat = fs.get("next")
            feat_summary = {
                "passed": fs.get("passed"),
                "total": fs.get("total"),
                "remaining": fs.get("remaining"),
                "all_pass": fs.get("all_pass"),
                "next_id": (next_feat or {}).get("id") if isinstance(next_feat, dict) else None,
            }
        except Exception as e:  # noqa: BLE001
            feat_summary = {"error": str(e)}
        wd = _watchdog_status(repo)
        budget: dict[str, Any] = {}
        try:
            from halo_budget import check as budget_check

            b = budget_check(repo)
            budget = {
                "verdict": b.get("verdict"),  # ALLOW | HALT (map DEGRADE if present)
                "reason": b.get("reason"),
            }
            # Normalize for roadmap wording ALLOW|DEGRADE|PAUSE
            v = str(budget.get("verdict") or "")
            if v == "HALT":
                budget["verdict_ui"] = "PAUSE"
            elif v == "ALLOW":
                budget["verdict_ui"] = "ALLOW"
            else:
                budget["verdict_ui"] = v or "ALLOW"
        except Exception as e:  # noqa: BLE001
            budget = {"verdict": "ALLOW", "verdict_ui": "ALLOW", "error": str(e)}
        print(
            json.dumps(
                {
                    "loop_active": loop_active(repo),
                    "work_remains": work_remains(repo),
                    "loop": {
                        "iteration": loop.get("iteration"),
                        "max_iterations": loop.get("max_iterations"),
                        "active": loop.get("active"),
                    },
                    "features": feat_summary,
                    "budget": budget,
                    "watchdog_pid": wd.get("watchdog_pid"),
                    "watchdog_alive": wd.get("watchdog_alive"),
                    "heartbeat_age_sec": wd.get("heartbeat_age_sec"),
                    "lock": _json(drive_lock_path(repo)),
                    "stale_clear": stale,
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
