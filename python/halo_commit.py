#!/usr/bin/env python3
"""Safe auto-commit for one story unit.

- Never force-adds gitignored paths (factory dogfood `.halo/` stays local)
- Blocks denylist paths
- Stages only explicit paths or current non-ignored changes
- One conventional message: `Sxxx: summary`
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from halo_denylist import is_denylist_path as _is_denylist_path

# Build artifacts (not secret, but never auto-commit bulk)
_BUILD_DENY = re.compile(
    r"(^|/)node_modules/|(^|/)dist/|(^|/)build/",
    re.I,
)

# Back-compat export for callers that imported DENY
DENY = re.compile(
    r"(^|/)\.env$|(^|/)\.env\.(local|production|prod|development|dev|staging|test)|"
    r"id_rsa|credentials\.json|(^|/)secrets?/|"
    r"(^|/)node_modules/|(^|/)dist/|(^|/)build/",
    re.I,
)


def _run(repo: Path, *args: str, check: bool = True) -> str:
    r = subprocess.run(
        ["git", *args],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    if check and r.returncode != 0:
        raise SystemExit(r.stderr.strip() or r.stdout.strip() or f"git {' '.join(args)} failed")
    return (r.stdout or "").strip()


def is_factory_repo(repo: Path) -> bool:
    return (repo / ".grok" / "skills" / "halo-go" / "SKILL.md").exists() and (
        repo / "python" / "halo_state.py"
    ).exists()


def list_changed(repo: Path) -> list[str]:
    names: set[str] = set()
    for args in (
        ["diff", "--name-only"],
        ["diff", "--cached", "--name-only"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        try:
            out = _run(repo, *args, check=False)
        except SystemExit:
            out = ""
        for line in out.splitlines():
            line = line.strip()
            if line:
                names.add(line)
    return sorted(names)


def filter_safe(repo: Path, paths: list[str]) -> tuple[list[str], list[str]]:
    """Return (ok_paths, rejected_reasons)."""
    ok: list[str] = []
    bad: list[str] = []
    for p in paths:
        if _is_denylist_path(p) or _BUILD_DENY.search(p):
            bad.append(f"denylist: {p}")
            continue
        # never stage dogfood control plane when ignored
        if p.startswith(".halo/") or p == ".halo":
            # check ignore
            r = subprocess.run(
                ["git", "check-ignore", "-q", p],
                cwd=repo,
                capture_output=True,
            )
            if r.returncode == 0:
                bad.append(f"gitignored dogfood (skip): {p}")
                continue
        if p in ("init.sh", "halo-health.json", "HALO.md") and is_factory_repo(repo):
            r = subprocess.run(["git", "check-ignore", "-q", p], cwd=repo, capture_output=True)
            if r.returncode == 0:
                bad.append(f"gitignored factory dogfood: {p}")
                continue
        ok.append(p)
    return ok, bad


def commit_unit(
    repo: Path,
    feature_id: str,
    message: str | None = None,
    paths: list[str] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    repo = repo.resolve()
    if not (repo / ".git").exists():
        return {"ok": False, "error": "not a git repo"}

    candidates = paths if paths else list_changed(repo)
    safe, rejected = filter_safe(repo, candidates)
    if not safe:
        return {
            "ok": False,
            "error": "nothing safe to commit",
            "rejected": rejected,
            "candidates": candidates,
        }

    msg = message or f"{feature_id}: unit complete"
    if not msg.startswith(feature_id):
        msg = f"{feature_id}: {msg}"

    if dry_run:
        return {"ok": True, "dry_run": True, "paths": safe, "rejected": rejected, "message": msg}

    _run(repo, "add", "--", *safe)
    # avoid empty commit
    staged = _run(repo, "diff", "--cached", "--name-only", check=False)
    if not staged.strip():
        return {"ok": False, "error": "nothing staged after filter", "rejected": rejected}

    _run(repo, "commit", "-m", msg)
    head = _run(repo, "rev-parse", "--short", "HEAD", check=False)
    return {
        "ok": True,
        "head": head,
        "paths": safe,
        "rejected": rejected,
        "message": msg,
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_commit")
    p.add_argument("--repo", default=".")
    p.add_argument("--id", required=True, help="feature id e.g. S006")
    p.add_argument("--message", default=None)
    p.add_argument("--path", action="append", default=[], help="explicit path to stage (repeatable)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    result = commit_unit(
        Path(args.repo),
        args.id,
        message=args.message,
        paths=args.path or None,
        dry_run=args.dry_run,
    )
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result.get("ok") else 2)


if __name__ == "__main__":
    main()
