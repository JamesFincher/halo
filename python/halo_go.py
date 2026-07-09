#!/usr/bin/env python3
"""Enable/disable autonomous mode and print the phase driver plan. Stdlib only."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(repo: Path) -> dict[str, Any]:
    p = repo / ".halo" / "state.json"
    if not p.exists():
        raise SystemExit(f"missing {p} — run: halo init")
    return json.loads(p.read_text(encoding="utf-8"))


def save(repo: Path, data: dict[str, Any]) -> None:
    data["updated_at"] = utc_now()
    (repo / ".halo" / "state.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def log_line(repo: Path, msg: str) -> None:
    path = repo / ".halo" / "autonomous-log.md"
    if not path.exists():
        path.write_text("# Autonomous log\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"- [{utc_now()}] {msg}\n")


def enable(repo: Path, max_cycles: int) -> dict[str, Any]:
    data = load(repo)
    data["autonomous"] = True
    data["require_human_gate"] = False
    data["auto_defaults"] = True
    data["auto_lock_specs"] = True
    data["auto_degraded_ok"] = True
    data["autonomous_max_cycles"] = max_cycles
    if data.get("status") == "PAUSED":
        data["status"] = "ACTIVE"
    save(repo, data)
    baton = repo / ".halo" / "baton.md"
    baton.write_text(
        "# Baton\n"
        "- Mode: AUTONOMOUS (halo-go)\n"
        f"- Phase: {data.get('phase')}\n"
        "- Rule: never ask optional questions; use defaults; drive phase machine\n"
        "- Hard stops only: kill switch, denylist, 3 fails, true BLOCKED secrets, explicit stop\n"
        f"- Max cycles this run: {max_cycles}\n"
        "- Next: agent reads skill halo-go and advances phase without asking\n",
        encoding="utf-8",
    )
    log_line(repo, f"autonomous ENABLED max_cycles={max_cycles}")
    return data


def disable(repo: Path) -> dict[str, Any]:
    data = load(repo)
    data["autonomous"] = False
    data["require_human_gate"] = True
    save(repo, data)
    log_line(repo, "autonomous DISABLED")
    baton = repo / ".halo" / "baton.md"
    prev = data.get("phase") or "unknown"
    baton.write_text(
        f"# Baton\n- Mode: interactive\n- Phase: {prev}\n- Autonomous off — ask before major gates\n",
        encoding="utf-8",
    )
    return data


def next_actions(repo: Path) -> list[str]:
    """Deterministic checklist for the agent — no questions."""
    data = load(repo)
    phase = data.get("phase") or "intake"
    status = data.get("status") or "ACTIVE"
    actions: list[str] = []

    if status in ("PAUSED", "ESCALATED"):
        return [f"STOP: status={status}. Human must resume/resolve."]
    if status == "BLOCKED" and not data.get("auto_degraded_ok"):
        return ["STOP: BLOCKED. Clear readiness or enable auto_degraded_ok."]

    if not data.get("autonomous"):
        actions.append("enable autonomous first: halo go")

    if phase in ("bootstrap", None) or not (repo / ".halo" / "state.json").exists():
        actions.append("halo init / bootstrap")
        phase = "intake"

    if phase == "intake" or data.get("spec_status") in (None, "none"):
        actions.append("single-pass intake defaults → write state.intake")
        actions.append("halo specs && halo lock")
    elif phase in ("spec_pack", "spec_review") or data.get("spec_status") == "drafting":
        if data.get("auto_lock_specs", True):
            actions.append("halo specs && halo lock")
        else:
            actions.append("halo specs; wait lock")
    elif phase == "readiness" or (
        data.get("spec_status") == "locked" and data.get("readiness_verdict") not in ("GO", "DEGRADED")
    ):
        if data.get("auto_degraded_ok", True):
            actions.append("halo ready --allow-degraded")
        else:
            actions.append("halo ready")
    elif phase == "scaffold" or (
        data.get("readiness_verdict") in ("GO", "DEGRADED") and not data.get("scaffold_profile")
    ):
        actions.append("halo scaffold --profile auto --demo0 local --skip-ready-check")
    elif phase == "build":
        n = data.get("autonomous_max_cycles") or 5
        actions.append(f"run up to {n} halo-build cycles; no continue prompts")
        actions.append("probe before any deploy URL share")
    elif phase == "complete":
        actions.append("DONE: phase complete")
    else:
        actions.append(f"advance from phase={phase} per WORKFLOWS.md without asking")

    return actions


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_go")
    p.add_argument("--repo", default=".")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--enable", action="store_true")
    g.add_argument("--disable", action="store_true")
    g.add_argument("--status", action="store_true")
    g.add_argument("--plan", action="store_true", help="print next autonomous actions")
    p.add_argument("--max-cycles", type=int, default=5)
    args = p.parse_args()
    repo = Path(args.repo).resolve()

    if args.enable:
        data = enable(repo, args.max_cycles)
        plan = next_actions(repo)
        print(json.dumps({"ok": True, "autonomous": True, "phase": data.get("phase"), "plan": plan}, indent=2))
    elif args.disable:
        data = disable(repo)
        print(json.dumps({"ok": True, "autonomous": False, "phase": data.get("phase")}, indent=2))
    elif args.status:
        data = load(repo)
        print(
            json.dumps(
                {
                    "autonomous": bool(data.get("autonomous")),
                    "require_human_gate": data.get("require_human_gate"),
                    "phase": data.get("phase"),
                    "status": data.get("status"),
                    "max_cycles": data.get("autonomous_max_cycles"),
                },
                indent=2,
            )
        )
    elif args.plan:
        if not load(repo).get("autonomous"):
            print(json.dumps({"autonomous": False, "plan": ["halo go --enable first"]}, indent=2))
            sys.exit(0)
        print(json.dumps({"autonomous": True, "plan": next_actions(repo)}, indent=2))


if __name__ == "__main__":
    main()
