#!/usr/bin/env python3
"""Append-only progress log for cold-session recovery (Anthropic/Ralph style)."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def factory_dirty_count(repo: Path) -> int:
    """Count non-.halo factory dirty paths (D091)."""
    import subprocess

    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=repo,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return 0
    n = 0
    for ln in out.splitlines():
        if not ln.strip():
            continue
        path = ln[3:].strip() if len(ln) > 3 else ln
        if path.startswith(".halo/") or path.startswith(".halo-archive/"):
            continue
        n += 1
    return n


def append(repo: Path, event: str, detail: dict[str, Any] | None = None) -> Path:
    halo = repo / ".halo"
    halo.mkdir(parents=True, exist_ok=True)
    jsonl = halo / "progress.jsonl"
    md = halo / "progress.md"
    detail = dict(detail or {})
    # D091: unit events auto-record factory dirty count
    if str(event).lower() in ("unit", "unit_done", "feature_pass", "cycle") and "dirty_count" not in detail:
        detail["dirty_count"] = factory_dirty_count(repo)
    row = {"at": utc_now(), "event": event, **detail}
    with jsonl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    line = f"- **{row['at']}** · `{event}`"
    if detail:
        bits = ", ".join(f"{k}={v}" for k, v in detail.items() if k != "note")
        if bits:
            line += f" — {bits}"
        if detail.get("note"):
            line += f" — {detail['note']}"
    with md.open("a", encoding="utf-8") as f:
        if md.stat().st_size == 0 if md.exists() else True:
            if not md.exists() or md.stat().st_size == 0:
                f.write("# Progress\n\nAppend-only. Cold sessions read the tail.\n\n")
        f.write(line + "\n")
    return jsonl


def tail(repo: Path, n: int = 15) -> list[dict[str, Any]]:
    p = repo / ".halo" / "progress.jsonl"
    if not p.exists():
        return []
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_progress")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add")
    a.add_argument("--repo", default=".")
    a.add_argument("--event", required=True)
    a.add_argument("--note", default="")
    a.add_argument("--json", default="{}", help="extra fields as JSON object")

    a.add_argument(
        "--feature-id",
        default="",
        help="optional feature id recorded on unit events (D107)",
    )

    def do_add(args: argparse.Namespace) -> None:
        detail = json.loads(args.json)
        if args.note:
            detail["note"] = args.note
        if getattr(args, "feature_id", None):
            detail["feature_id"] = args.feature_id
        path = append(Path(args.repo), args.event, detail)
        print(json.dumps({"ok": True, "path": str(path)}, indent=2))

    a.set_defaults(func=do_add)

    t = sub.add_parser("tail")
    t.add_argument("--repo", default=".")
    t.add_argument("-n", type=int, default=15)
    t.set_defaults(func=lambda args: print(json.dumps(tail(Path(args.repo), args.n), indent=2)))

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
