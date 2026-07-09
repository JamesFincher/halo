#!/usr/bin/env python3
"""Single-runner lock — prevent two agents thrashing the same product."""

from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def lock_path(repo: Path) -> Path:
    return repo / ".halo" / "runner.lock"


def acquire(repo: Path, owner: str, ttl_sec: int = 7200) -> dict:
    repo = repo.resolve()
    (repo / ".halo").mkdir(parents=True, exist_ok=True)
    lp = lock_path(repo)
    now = time.time()
    if lp.exists():
        try:
            data = json.loads(lp.read_text(encoding="utf-8"))
            if data.get("expires_at", 0) > now and data.get("owner") != owner:
                return {
                    "ok": False,
                    "error": "locked",
                    "owner": data.get("owner"),
                    "expires_at": data.get("expires_at_iso"),
                }
        except (json.JSONDecodeError, OSError):
            pass
    payload = {
        "owner": owner,
        "pid": os.getpid(),
        "acquired_at": utc_now(),
        "expires_at": now + ttl_sec,
        "expires_at_iso": datetime.fromtimestamp(now + ttl_sec, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    lp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, **payload}


def release(repo: Path, owner: str) -> dict:
    lp = lock_path(repo)
    if not lp.exists():
        return {"ok": True, "released": False}
    try:
        data = json.loads(lp.read_text(encoding="utf-8"))
        if data.get("owner") not in (owner, None) and data.get("expires_at", 0) > time.time():
            return {"ok": False, "error": "not_owner", "owner": data.get("owner")}
    except (json.JSONDecodeError, OSError):
        pass
    lp.unlink(missing_ok=True)
    return {"ok": True, "released": True}


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_lock")
    p.add_argument("--repo", default=".")
    p.add_argument("--owner", default=f"pid-{os.getpid()}")
    p.add_argument("--ttl", type=int, default=7200)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--acquire", action="store_true")
    g.add_argument("--release", action="store_true")
    g.add_argument("--status", action="store_true")
    args = p.parse_args()
    repo = Path(args.repo)
    if args.acquire:
        r = acquire(repo, args.owner, args.ttl)
        print(json.dumps(r, indent=2))
        raise SystemExit(0 if r.get("ok") else 2)
    if args.release:
        print(json.dumps(release(repo, args.owner), indent=2))
        return
    lp = lock_path(repo)
    if not lp.exists():
        print(json.dumps({"locked": False}, indent=2))
    else:
        print(lp.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
