#!/usr/bin/env python3
"""Test ratchet — detect deleted/gutted test files (Anthropic failure mode)."""

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
