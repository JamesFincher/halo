#!/usr/bin/env python3
"""Cycle-smoke evidence writer — surfaces scores/trajectories health (D138).

Invoked by scripts/halo-cycle-smoke.sh after smoke steps pass.
Does not run smoke itself (avoids unittest recursion).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from halo_features import summary


def build_evidence(repo: Path) -> dict[str, Any]:
    """Build GREEN_TEST payload including scores/trajectories counts + match."""
    fs = summary(Path(repo), compound=False)
    sc = int(fs.get("scores_count") or 0)
    tc = int(fs.get("trajectories_count") or 0)
    if "scores_trajectories_match" in fs:
        match = bool(fs.get("scores_trajectories_match"))
    else:
        match = sc == tc
    return {
        "cert": "GREEN_TEST",
        "feature": "cycle-smoke",
        "exit_code": 0,
        "ok": True,
        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "steps": ["py_compile", "doctor", "denylist", "unittest", "features"],
        "scores_count": sc,
        "trajectories_count": tc,
        "scores_trajectories_match": match,
    }


def write_evidence(repo: Path) -> Path:
    """Write .halo/evidence/D-cycle-smoke-latest.json; return path."""
    repo = Path(repo)
    ev_dir = repo / ".halo" / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    path = ev_dir / "D-cycle-smoke-latest.json"
    path.write_text(json.dumps(build_evidence(repo), separators=(",", ":")) + "\n", encoding="utf-8")
    return path


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_cycle_smoke")
    sub = p.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("write-evidence", help="write D-cycle-smoke-latest.json")
    w.add_argument("--repo", default=".")
    args = p.parse_args()
    if args.cmd == "write-evidence":
        path = write_evidence(Path(args.repo))
        print(str(path))
        return
    p.error(f"unknown cmd {args.cmd}")


if __name__ == "__main__":
    main()
