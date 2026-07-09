#!/usr/bin/env python3
"""Hard budget gate — max iterations, optional daily cycle + wall-clock caps."""

from __future__ import annotations

import argparse
import json
import os
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


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_budget(repo: Path) -> dict[str, Any]:
    """Merge env + .halo/budget.json + loop.json defaults."""
    b = {
        "max_iterations": 50,
        "max_daily_cycles": 0,  # 0 = unlimited
        "max_wall_minutes": 0,  # 0 = unlimited
        "halted": False,
        "halt_reason": None,
    }
    file_b = _json(repo / ".halo" / "budget.json")
    b.update({k: v for k, v in file_b.items() if v is not None})
    loop = _json(repo / ".halo" / "loop.json")
    if loop.get("max_iterations"):
        b["max_iterations"] = int(loop["max_iterations"])
    state = _json(repo / ".halo" / "state.json")
    if state.get("autonomous_max_cycles"):
        # prefer loop max when armed; else state
        if not loop.get("max_iterations"):
            b["max_iterations"] = int(state["autonomous_max_cycles"])
    env_max = os.environ.get("HALO_MAX_ITERATIONS")
    if env_max:
        b["max_iterations"] = int(env_max)
    env_daily = os.environ.get("HALO_MAX_DAILY_CYCLES")
    if env_daily:
        b["max_daily_cycles"] = int(env_daily)
    env_wall = os.environ.get("HALO_MAX_WALL_MINUTES")
    if env_wall:
        b["max_wall_minutes"] = int(env_wall)
    return b


def check(repo: Path, *, next_iteration: int | None = None) -> dict[str, Any]:
    """Return ALLOW or HALT verdict before continuing the loop."""
    repo = repo.resolve()
    b = load_budget(repo)
    loop = _json(repo / ".halo" / "loop.json")
    spend = _json(repo / ".halo" / "spend.json")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if b.get("halted"):
        return {
            "verdict": "HALT",
            "reason": b.get("halt_reason") or "budget.json halted=true",
            "budget": b,
        }

    iteration = int(loop.get("iteration") or 0)
    if next_iteration is not None:
        iteration = next_iteration
    max_iter = int(b.get("max_iterations") or 0)
    if max_iter > 0 and iteration > max_iter:
        return {
            "verdict": "HALT",
            "reason": f"max_iterations {iteration}>{max_iter}",
            "budget": b,
        }

    # daily cycles
    daily_max = int(b.get("max_daily_cycles") or 0)
    day_key = spend.get("day")
    day_count = int(spend.get("day_cycles") or 0)
    if day_key != today:
        day_count = 0
    if daily_max > 0 and day_count >= daily_max:
        return {
            "verdict": "HALT",
            "reason": f"max_daily_cycles {day_count}>={daily_max}",
            "budget": b,
            "spend": spend,
        }

    # wall clock from loop start
    wall_max = int(b.get("max_wall_minutes") or 0)
    started = loop.get("started_at")
    if wall_max > 0 and started:
        try:
            t0 = datetime.strptime(started, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            mins = (datetime.now(timezone.utc) - t0).total_seconds() / 60.0
            if mins > wall_max:
                return {
                    "verdict": "HALT",
                    "reason": f"max_wall_minutes {mins:.0f}>{wall_max}",
                    "budget": b,
                }
        except ValueError:
            pass

    return {
        "verdict": "ALLOW",
        "reason": "within budget",
        "budget": b,
        "iteration": iteration,
        "day_cycles": day_count,
    }


def record_cycle(repo: Path) -> dict[str, Any]:
    """Increment daily spend after a loop iteration fires."""
    repo = repo.resolve()
    spend_p = repo / ".halo" / "spend.json"
    spend = _json(spend_p)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if spend.get("day") != today:
        spend = {"day": today, "day_cycles": 0, "total_cycles": int(spend.get("total_cycles") or 0)}
    spend["day_cycles"] = int(spend.get("day_cycles") or 0) + 1
    spend["total_cycles"] = int(spend.get("total_cycles") or 0) + 1
    spend["last_at"] = utc_now()
    _save(spend_p, spend)
    return spend


def halt(repo: Path, reason: str) -> None:
    p = repo / ".halo" / "budget.json"
    b = load_budget(repo)
    b["halted"] = True
    b["halt_reason"] = reason
    b["halted_at"] = utc_now()
    # strip runtime-only merges
    keep = {
        "max_iterations": b.get("max_iterations"),
        "max_daily_cycles": b.get("max_daily_cycles"),
        "max_wall_minutes": b.get("max_wall_minutes"),
        "halted": True,
        "halt_reason": reason,
        "halted_at": b["halted_at"],
    }
    _save(p, keep)


def show_score_fields(repo: Path) -> dict[str, Any]:
    """D141: scores/trajectories counts + match for budget show JSON."""
    try:
        from halo_features import summary as feature_summary

        fs = feature_summary(repo, compound=False)
        sc = int(fs.get("scores_count") or 0)
        tc = int(fs.get("trajectories_count") or 0)
        if "scores_trajectories_match" in fs:
            match = bool(fs.get("scores_trajectories_match"))
        else:
            match = sc == tc
        return {
            "scores_count": sc,
            "trajectories_count": tc,
            "scores_trajectories_match": match,
        }
    except Exception:  # noqa: BLE001
        return {
            "scores_count": 0,
            "trajectories_count": 0,
            "scores_trajectories_match": True,
        }


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_budget")
    p.add_argument("--repo", default=".")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="ALLOW or HALT")
    c.add_argument("--next-iteration", type=int, default=None)

    sub.add_parser("record", help="increment daily cycle counter")
    h = sub.add_parser("halt", help="hard halt")
    h.add_argument("--reason", default="manual halt")

    s = sub.add_parser("show", help="show budget + spend")
    args = p.parse_args()
    repo = Path(args.repo)

    if args.cmd == "check":
        r = check(repo, next_iteration=args.next_iteration)
        print(json.dumps(r, indent=2))
        raise SystemExit(0 if r["verdict"] == "ALLOW" else 2)
    if args.cmd == "record":
        print(json.dumps(record_cycle(repo), indent=2))
        return
    if args.cmd == "halt":
        halt(repo, args.reason)
        print(json.dumps({"ok": True, "halted": True, "reason": args.reason}, indent=2))
        return
    if args.cmd == "show":
        # D097: spend + max_iterations always co-present for operators
        # D141: scores/trajectories counts + match for operators
        b = load_budget(repo)
        out = {
            "budget": b,
            "spend": _json(repo / ".halo" / "spend.json") or {},
            "loop": _json(repo / ".halo" / "loop.json") or {},
            "max_iterations": b.get("max_iterations"),
            **show_score_fields(repo),
        }
        print(json.dumps(out, indent=2))
        raise SystemExit(0)


if __name__ == "__main__":
    main()
