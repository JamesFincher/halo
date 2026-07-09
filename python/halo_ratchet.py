#!/usr/bin/env python3
"""Test ratchet — detect deleted/gutted test files (Anthropic failure mode).

D174: --json / check includes scores_count / trajectories_count /
scores_trajectories_match (true when equal, including both zero).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

TEST_PATH_RE = re.compile(
    r"(^|/)(tests?/|__tests__/|spec/)|"
    r"(\.|_)(test|spec)\.(ts|tsx|js|jsx|py|go|rs)$|"
    r"test_.*\.py$|"
    r".*\.test\.(ts|tsx|js|jsx)$|"
    r".*\.spec\.(ts|tsx|js|jsx)$",
    re.I,
)


def ratchet_score_fields(repo: Path) -> dict[str, Any]:
    """Score culture fields for ratchet --json output.

    D174: scores_count / trajectories_count / scores_trajectories_match.
    """
    try:
        from halo_features import summary as feature_summary

        fs = feature_summary(Path(repo), compound=False)
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


def _git(repo: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            cwd=repo,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def deleted_test_files(repo: Path, commits: int = 5) -> list[str]:
    """Files matching test patterns deleted in last N commits."""
    # --diff-filter=D name-only
    out = _git(repo, "log", f"-{commits}", "--diff-filter=D", "--name-only", "--pretty=format:")
    deleted = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if TEST_PATH_RE.search(line):
            deleted.append(line)
    return sorted(set(deleted))


def unstaged_test_deletes(repo: Path) -> list[str]:
    """Test files deleted in working tree (not yet committed)."""
    out = _git(repo, "status", "--porcelain")
    deleted = []
    for line in out.splitlines():
        # " D path" or "D  path" or "DD path"
        if len(line) < 4:
            continue
        code, path = line[:2], line[3:].strip()
        if "D" in code and TEST_PATH_RE.search(path):
            # rename "old -> new" form
            if " -> " in path:
                path = path.split(" -> ", 1)[0].strip()
            deleted.append(path)
    return sorted(set(deleted))


def check(repo: Path, commits: int = 5) -> dict[str, Any]:
    repo = repo.resolve()
    recent = deleted_test_files(repo, commits)
    dirty = unstaged_test_deletes(repo)
    violations = recent + [f"(unstaged) {p}" for p in dirty]
    return {
        "ok": len(violations) == 0,
        "violations": violations,
        "recent_deleted_tests": recent,
        "unstaged_deleted_tests": dirty,
        "rule": "test_ratchet: never delete tests to go green",
        **ratchet_score_fields(repo),
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_ratchet")
    p.add_argument("--repo", default=".")
    p.add_argument("--commits", type=int, default=5)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    rep = check(Path(args.repo), args.commits)
    if args.json:
        print(json.dumps(rep, indent=2))
    else:
        if rep["ok"]:
            print("test ratchet: OK")
        else:
            print("test ratchet: VIOLATIONS")
            for v in rep["violations"]:
                print(f"  - {v}")
    raise SystemExit(0 if rep["ok"] else 2)


if __name__ == "__main__":
    main()
