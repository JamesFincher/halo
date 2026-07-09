#!/usr/bin/env python3
"""Tracked-path denylist for Halo factory hygiene.

Used by cycle-smoke (git ls-files) and available to commit/arena checks.
Never allow dogfood control plane or secret-like paths into tracked git.

Safe env templates (.env.example / .sample / .template) are allowed.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

# Paths that must never appear in `git ls-files` for a clean factory/product tree.
# Note: .env.example|.sample|.template are explicitly allowed (not secret values).
_SECRET_ENV_NAME = re.compile(
    r"^\.env$"
    r"|^\.env\.(local|production|prod|development|dev|staging|stage|test|secret)(\..+)?$",
    re.I,
)
_SECRET_ENV_SUFFIX = re.compile(
    r"(^|/)\.env\.(local|production|prod|development|dev|staging|stage|test|secret)(\.|$)",
    re.I,
)
_CREDENTIALS = re.compile(
    r"(^|/)id_rsa$|(^|/)id_rsa\.pub$|(^|/)credentials\.json$|(^|/)secrets?/",
    re.I,
)
_DOGFOOD = re.compile(r"(^|/)\.halo(-archive)?(/|$)", re.I)

# Allowlisted env template basenames (committed name-only samples)
_ENV_TEMPLATE_OK = frozenset({".env.example", ".env.sample", ".env.template"})


def is_denylist_path(path: str) -> bool:
    """True if path must never be git-tracked."""
    p = path.strip().replace("\\", "/")
    if not p:
        return False
    # Dogfood control plane
    if p == ".halo" or p.startswith(".halo/") or p.startswith(".halo-archive"):
        return True
    if _DOGFOOD.search(p):
        return True

    name = Path(p).name
    if name in _ENV_TEMPLATE_OK:
        return False

    # Bare .env or secret-flavored .env.*
    if name == ".env" or _SECRET_ENV_NAME.match(name) or _SECRET_ENV_SUFFIX.search(p):
        return True

    if _CREDENTIALS.search(p):
        return True

    return False


def find_tracked_violations(paths: Iterable[str]) -> list[str]:
    """Return sorted unique denylist paths from an iterable of git paths."""
    bad: set[str] = set()
    for p in paths:
        p = (p or "").strip()
        if p and is_denylist_path(p):
            bad.add(p)
    return sorted(bad)


def list_tracked_files(repo: Path) -> list[str] | None:
    """Return git ls-files paths, or None if not a git repo / git missing."""
    repo = repo.resolve()
    if not (repo / ".git").exists() and not (repo / ".git").is_file():
        # also try rev-parse for worktrees
        try:
            r = subprocess.run(
                ["git", "-C", str(repo), "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
            )
            if r.returncode != 0 or (r.stdout or "").strip() != "true":
                return None
        except (OSError, FileNotFoundError):
            return None
    try:
        out = subprocess.check_output(
            ["git", "-C", str(repo), "ls-files"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, OSError, FileNotFoundError):
        return None
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def check_tracked_in_repo(repo: Path) -> dict[str, Any]:
    """Check git ls-files for denylist violations.

    If not a git repo, returns ok=True with skip reason (smoke soft-pass).
    """
    repo = Path(repo).resolve()
    tracked = list_tracked_files(repo)
    if tracked is None:
        return {
            "ok": True,
            "skipped": True,
            "reason": "not a git work tree",
            "violations": [],
            "repo": str(repo),
        }
    violations = find_tracked_violations(tracked)
    return {
        "ok": len(violations) == 0,
        "skipped": False,
        "violations": violations,
        "checked": len(tracked),
        "repo": str(repo),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Halo tracked denylist check")
    p.add_argument(
        "cmd",
        nargs="?",
        default="check-tracked",
        choices=["check-tracked", "is-deny"],
    )
    p.add_argument("--repo", default=".", help="repo root for check-tracked")
    p.add_argument("path", nargs="?", help="path for is-deny")
    args = p.parse_args(argv)

    if args.cmd == "is-deny":
        path = args.path or ""
        denied = is_denylist_path(path)
        print("deny" if denied else "allow")
        return 1 if denied else 0

    result = check_tracked_in_repo(Path(args.repo))
    if result.get("skipped"):
        print(f"[denylist] skip: {result.get('reason')}")
        return 0
    viol = result.get("violations") or []
    if viol:
        print("[denylist] FAIL: tracked denylist paths:", file=sys.stderr)
        for v in viol[:50]:
            print(f"  {v}", file=sys.stderr)
        if len(viol) > 50:
            print(f"  ... +{len(viol) - 50} more", file=sys.stderr)
        return 2
    print(f"[denylist] ok ({result.get('checked', 0)} tracked files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
