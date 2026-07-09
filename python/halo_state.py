#!/usr/bin/env python3
"""Halo durable state helper — stdlib only."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def state_path(repo: Path) -> Path:
    return repo / ".halo" / "state.json"


def load(repo: Path) -> dict[str, Any]:
    p = state_path(repo)
    if not p.exists():
        raise SystemExit(f"missing state: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def save(repo: Path, data: dict[str, Any]) -> None:
    data["updated_at"] = utc_now()
    p = state_path(repo)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> None:
    repo = Path(args.repo).resolve()
    halo = repo / ".halo"
    for sub in (
        "evidence",
        "plans",
        "spec",
        "milestones",
        "scores",
        "trajectories",
        "worktrees",
        "arena",
        "logs",
    ):
        (halo / sub).mkdir(parents=True, exist_ok=True)

    if state_path(repo).exists() and not args.force:
        raise SystemExit("state exists; use --force to overwrite")

    data = {
        "version": 1,
        "status": "ACTIVE",
        "phase": args.phase,
        "spec_status": "none",
        "product_name": None,
        "require_human_gate": False,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "intake": {},
        "integrations": [],
        "current_milestone": None,
        "current_story": None,
        "last_cycle_commit": None,
        "last_cycle_status": None,
        "warm_start_directives": [],
        "readiness_verdict": None,
    }
    save(repo, data)

    baton = halo / "baton.md"
    if not baton.exists() or args.force:
        baton.write_text(
            "# Baton\n"
            f"- Phase: {args.phase}\n"
            "- Next: run skill halo-intake\n"
            "- Do not: write product feature code yet\n",
            encoding="utf-8",
        )

    print(json.dumps({"ok": True, "repo": str(repo), "phase": args.phase}, indent=2))


def cmd_get(args: argparse.Namespace) -> None:
    data = load(Path(args.repo).resolve())
    if args.key:
        cur: Any = data
        for part in args.key.split("."):
            cur = cur[part]
        print(json.dumps(cur, indent=2) if not isinstance(cur, str) else cur)
    else:
        print(json.dumps(data, indent=2))


def cmd_set(args: argparse.Namespace) -> None:
    repo = Path(args.repo).resolve()
    data = load(repo)
    if args.phase:
        data["phase"] = args.phase
    if args.spec_status:
        data["spec_status"] = args.spec_status
    if args.status:
        data["status"] = args.status
    if args.product_name:
        data["product_name"] = args.product_name
    if args.readiness_verdict:
        data["readiness_verdict"] = args.readiness_verdict
    save(repo, data)
    print(
        json.dumps(
            {
                "ok": True,
                "phase": data.get("phase"),
                "spec_status": data.get("spec_status"),
                "readiness_verdict": data.get("readiness_verdict"),
            },
            indent=2,
        )
    )


def cmd_lock_specs(args: argparse.Namespace) -> None:
    """Mark specs locked and move to readiness phase."""
    repo = Path(args.repo).resolve()
    data = load(repo)
    data["spec_status"] = "locked"
    data["phase"] = "readiness"
    data["status"] = "ACTIVE"
    save(repo, data)
    baton = repo / ".halo" / "baton.md"
    baton.write_text(
        "# Baton\n- Phase: readiness\n- Next: run halo-readiness (python/halo_readiness.py --write)\n"
        "- Specs: locked\n",
        encoding="utf-8",
    )
    print(json.dumps({"ok": True, "phase": "readiness", "spec_status": "locked"}, indent=2))


def cmd_set_intake(args: argparse.Namespace) -> None:
    repo = Path(args.repo).resolve()
    data = load(repo)
    intake = data.setdefault("intake", {})
    value = json.loads(args.json)
    intake[args.key] = value
    if args.key == "product_name" and isinstance(value, str):
        data["product_name"] = value
        intake["product_name"] = value
    if isinstance(value, dict) and value.get("product_name"):
        data["product_name"] = value["product_name"]
    if args.key in ("core_purpose", "purpose") and isinstance(value, dict) and value.get("product_name"):
        data["product_name"] = value["product_name"]
    save(repo, data)
    print(json.dumps({"ok": True, "key": args.key}, indent=2))


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_state")
    sub = p.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init", help="create .halo skeleton + state")
    i.add_argument("--repo", default=".")
    i.add_argument("--phase", default="intake")
    i.add_argument("--force", action="store_true")
    i.set_defaults(func=cmd_init)

    g = sub.add_parser("get", help="print state or key")
    g.add_argument("--repo", default=".")
    g.add_argument("--key", default=None)
    g.set_defaults(func=cmd_get)

    s = sub.add_parser("set", help="set top-level fields")
    s.add_argument("--repo", default=".")
    s.add_argument("--phase")
    s.add_argument("--spec-status", dest="spec_status")
    s.add_argument("--status")
    s.add_argument("--product-name", dest="product_name")
    s.add_argument("--readiness-verdict", dest="readiness_verdict")
    s.set_defaults(func=cmd_set)

    si = sub.add_parser("set-intake", help="set intake.<key> from JSON")
    si.add_argument("--repo", default=".")
    si.add_argument("--key", required=True)
    si.add_argument("--json", required=True)
    si.set_defaults(func=cmd_set_intake)

    lk = sub.add_parser("lock-specs", help="spec_status=locked, phase=readiness")
    lk.add_argument("--repo", default=".")
    lk.set_defaults(func=cmd_lock_specs)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
