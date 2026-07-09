#!/usr/bin/env python3
"""Six-dimension cycle scores + golden trajectory stubs for dogfood (D103/D104/D110/D113/D157/D158)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# D157: explicit six-dimension contract for compounding score stubs.
# Top-level keys + nested `dimensions` map must stay in sync.
SIX_DIMENSIONS: tuple[str, ...] = (
    "tool_selection",
    "argument_extraction",
    "result_utilization",
    "error_recovery",
    "plan_coherence",
    "task_completion",
)

# Default neutral stub values (critic skill may overwrite later).
_DEFAULT_DIM_SCORES: dict[str, float] = {
    "tool_selection": 0.7,
    "argument_extraction": 0.7,
    "result_utilization": 0.7,
    "error_recovery": 0.7,
    "plan_coherence": 0.7,
    "task_completion": 0.8,
}

# D158: explicit golden trajectory step sequence for compounding APPROVED cycles.
# GT-NNN.json `steps` defaults must stay in sync with this contract.
GOLDEN_TRAJECTORY_STEPS: tuple[str, ...] = (
    "plan",
    "implement",
    "unittest",
    "cycle-smoke",
    "evidence",
    "features pass",
    "factory commit",
)
GOLDEN_TRAJECTORY_SIGNATURE = "dogfood-stub-v1"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_head(repo: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return None


def _next_num(dir_path: Path, prefix: str) -> int:
    dir_path.mkdir(parents=True, exist_ok=True)
    max_n = 0
    for p in dir_path.iterdir():
        m = re.match(rf"^{re.escape(prefix)}(\d+)\.json$", p.name, re.I)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1


def _score_files(repo: Path) -> list[Path]:
    """Return S*.json score paths sorted by numeric id."""
    scores = repo / ".halo" / "scores"
    if not scores.is_dir():
        return []
    found: list[tuple[int, Path]] = []
    for p in scores.glob("S*.json"):
        m = re.match(r"^S(\d+)\.json$", p.name, re.I)
        if m:
            found.append((int(m.group(1)), p))
    found.sort(key=lambda t: t[0])
    return [p for _, p in found]


def list_scores(repo: Path) -> dict[str, Any]:
    """List cycle scores: count + latest id (D110)."""
    files = _score_files(repo)
    count = len(files)
    latest: str | None = None
    if files:
        last = files[-1]
        try:
            payload = json.loads(last.read_text(encoding="utf-8"))
            latest = str(payload.get("id") or last.stem)
        except (OSError, json.JSONDecodeError):
            latest = last.stem
    return {
        "count": count,
        "latest": latest,
        "ids": [p.stem for p in files],
    }


def _trajectory_files(repo: Path) -> list[Path]:
    """Return GT-*.json trajectory paths sorted by numeric id."""
    traj = repo / ".halo" / "trajectories"
    if not traj.is_dir():
        return []
    found: list[tuple[int, Path]] = []
    for p in traj.glob("GT-*.json"):
        m = re.match(r"^GT-(\d+)\.json$", p.name, re.I)
        if m:
            found.append((int(m.group(1)), p))
    found.sort(key=lambda t: t[0])
    return [p for _, p in found]


def list_trajectories(repo: Path) -> dict[str, Any]:
    """List golden trajectories: count + latest id (D113)."""
    files = _trajectory_files(repo)
    count = len(files)
    latest: str | None = None
    if files:
        last = files[-1]
        try:
            payload = json.loads(last.read_text(encoding="utf-8"))
            latest = str(payload.get("id") or last.stem)
        except (OSError, json.JSONDecodeError):
            latest = last.stem
    return {
        "count": count,
        "latest": latest,
        "ids": [p.stem for p in files],
    }


def write_cycle_score(
    repo: Path,
    *,
    feature_id: str,
    note: str = "",
) -> Path:
    """Write six-dimension score stub with warm_start_directive (D103/D157).

    D157: sequential id S### equals path stem; all SIX_DIMENSIONS present as
    unit-interval floats at top level and under nested ``dimensions`` map;
    ``schema_version`` is 1; ``tool_selection`` + ``warm_start_directive`` always set.
    """
    scores = repo / ".halo" / "scores"
    n = _next_num(scores, "S")
    sid = f"S{n:03d}"
    path = scores / f"{sid}.json"
    # Neutral stub scores — critic skill can overwrite later; structure is the contract
    dim_vals = {k: float(_DEFAULT_DIM_SCORES[k]) for k in SIX_DIMENSIONS}
    payload: dict[str, Any] = {
        "id": sid,
        "schema_version": 1,
        "feature_id": feature_id,
        "at": utc_now(),
        "git_head": _git_head(repo),
        **dim_vals,
        "dimensions": dict(dim_vals),
        "warm_start_directive": (
            note
            or "Next cycle: prefer requires_code FILE_DIFF units; expand ROADMAP when exhausted."
        ),
        "note": "stub scores — replace with halo-critic when spawned",
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def write_golden_trajectory(
    repo: Path,
    *,
    feature_id: str,
    steps: list[str] | None = None,
) -> Path:
    """Record golden trajectory stub for APPROVED dogfood unit (D104/D158).

    D158: sequential id GT-### equals path stem; non-empty step sequence
    (defaults from GOLDEN_TRAJECTORY_STEPS); ``feature_id`` and ``git_head``
    always present; ``schema_version`` is 1; signature is
    GOLDEN_TRAJECTORY_SIGNATURE.
    """
    traj = repo / ".halo" / "trajectories"
    n = _next_num(traj, "GT-")
    gtid = f"GT-{n:03d}"
    path = traj / f"{gtid}.json"
    step_seq = list(steps) if steps is not None else list(GOLDEN_TRAJECTORY_STEPS)
    if not step_seq:
        step_seq = list(GOLDEN_TRAJECTORY_STEPS)
    payload: dict[str, Any] = {
        "id": gtid,
        "schema_version": 1,
        "feature_id": feature_id,
        "at": utc_now(),
        "git_head": _git_head(repo),
        "steps": step_seq,
        "signature": GOLDEN_TRAJECTORY_SIGNATURE,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def refresh_loop_last_head(repo: Path) -> dict[str, Any]:
    """Update loop.json last_head to current git HEAD (D105)."""
    loop_p = repo / ".halo" / "loop.json"
    if not loop_p.is_file():
        return {"ok": False, "reason": "no_loop"}
    try:
        loop = json.loads(loop_p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"ok": False, "reason": "loop_corrupt"}
    if not loop.get("active"):
        return {"ok": False, "reason": "loop_inactive"}
    head = _git_head(repo)
    if not head:
        return {"ok": False, "reason": "no_git_head"}
    loop["last_head"] = head
    loop["last_head_at"] = utc_now()
    loop_p.write_text(json.dumps(loop, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "last_head": head}


def on_feature_pass(repo: Path, feature_id: str, note: str = "") -> dict[str, Any]:
    """Side effects after successful set_pass (scores, trajectory, last_head)."""
    out: dict[str, Any] = {}
    try:
        out["score"] = str(write_cycle_score(repo, feature_id=feature_id, note=note))
    except OSError as e:
        out["score_error"] = str(e)
    try:
        out["trajectory"] = str(write_golden_trajectory(repo, feature_id=feature_id))
    except OSError as e:
        out["trajectory_error"] = str(e)
    try:
        out["loop"] = refresh_loop_last_head(repo)
    except Exception as e:  # noqa: BLE001
        out["loop_error"] = str(e)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="halo_scores")
    sub = p.add_subparsers(dest="cmd", required=True)

    lst = sub.add_parser("list", help="list cycle scores (count + latest id)")
    lst.add_argument("--repo", default=".")
    lst.set_defaults(
        func=lambda args: print(
            json.dumps(list_scores(Path(args.repo)), indent=2)
        )
    )

    trj = sub.add_parser(
        "trajectories", help="list golden trajectories (count + latest id)"
    )
    trj.add_argument("--repo", default=".")
    trj.set_defaults(
        func=lambda args: print(
            json.dumps(list_trajectories(Path(args.repo)), indent=2)
        )
    )

    args = p.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
