#!/usr/bin/env python3
"""Halo escalate — write escalation packet, set ESCALATED, emit operator JSON.

D156: stdout + packet JSON include latest_score_id and latest_trajectory_id
(null when scores/trajectories dirs empty or missing).
D164: scores_count / trajectories_count / scores_trajectories_match
(true when equal, including both zero).
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def escalate_score_fields(repo: Path) -> dict[str, Any]:
    """Score culture fields for escalate packet/stdout/state.

    D156: latest_score_id / latest_trajectory_id (null when empty/missing)
    D164: scores_count / trajectories_count / scores_trajectories_match
    """
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
            "latest_score_id": fs.get("latest_score_id"),
            "latest_trajectory_id": fs.get("latest_trajectory_id"),
        }
    except Exception:  # noqa: BLE001
        return {
            "scores_count": 0,
            "trajectories_count": 0,
            "scores_trajectories_match": True,
            "latest_score_id": None,
            "latest_trajectory_id": None,
        }


def escalate(repo: Path, reason: str = "unspecified failure") -> dict[str, Any]:
    """Write escalation packet (md + json), set status ESCALATED, return JSON envelope."""
    repo = Path(repo).resolve()
    halo = repo / ".halo"
    esc_dir = halo / "escalations"
    esc_dir.mkdir(parents=True, exist_ok=True)

    ts = int(time.time())
    when = utc_now()
    score_fields = escalate_score_fields(repo)

    state_raw = ""
    state: dict[str, Any] = {}
    state_path = halo / "state.json"
    if state_path.is_file():
        try:
            state_raw = state_path.read_text(encoding="utf-8")
            state = json.loads(state_raw)
        except (OSError, json.JSONDecodeError):
            state_raw = state_path.read_text(encoding="utf-8", errors="replace")
            state = {}

    baton_raw = ""
    baton_path = halo / "baton.md"
    if baton_path.is_file():
        try:
            baton_raw = baton_path.read_text(encoding="utf-8")
        except OSError:
            baton_raw = ""

    md_path = esc_dir / f"esc-{ts}.md"
    json_path = esc_dir / f"esc-{ts}.json"

    md_body = (
        f"# Escalation\n\n"
        f"- When: {when}\n"
        f"- Reason: {reason}\n"
        f"- scores_count: {score_fields.get('scores_count')}\n"
        f"- trajectories_count: {score_fields.get('trajectories_count')}\n"
        f"- scores_trajectories_match: {score_fields.get('scores_trajectories_match')}\n"
        f"- latest_score_id: {score_fields.get('latest_score_id')}\n"
        f"- latest_trajectory_id: {score_fields.get('latest_trajectory_id')}\n"
        f"\n## State\n"
        f"{state_raw or '(missing state.json)'}\n"
        f"\n## Baton\n"
        f"{baton_raw or '(missing baton.md)'}\n"
    )
    md_path.write_text(md_body, encoding="utf-8")

    packet: dict[str, Any] = {
        "when": when,
        "reason": reason,
        "status": "ESCALATED",
        "md_path": str(md_path),
        "state": state if state else None,
        **score_fields,
    }
    json_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")

    # Set ESCALATED (preserve other state fields)
    if state_path.is_file() or state:
        try:
            data = state if state else {}
            data["status"] = "ESCALATED"
            data["updated_at"] = when
            data["escalation"] = {
                "reason": reason,
                "when": when,
                "packet": str(json_path),
                **score_fields,
            }
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass
    else:
        # minimal state so operators see ESCALATED
        try:
            state_path.parent.mkdir(parents=True, exist_ok=True)
            state_path.write_text(
                json.dumps(
                    {
                        "status": "ESCALATED",
                        "updated_at": when,
                        "escalation": {
                            "reason": reason,
                            "when": when,
                            "packet": str(json_path),
                            **score_fields,
                        },
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass

    return {
        "ok": True,
        "status": "ESCALATED",
        "reason": reason,
        "when": when,
        "packet": str(json_path),
        "md": str(md_path),
        **score_fields,
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_escalate")
    p.add_argument("--repo", default=".")
    p.add_argument("--reason", default="unspecified failure")
    args = p.parse_args()
    result = escalate(Path(args.repo), reason=args.reason)
    print(json.dumps(result, indent=2))
    raise SystemExit(0)


if __name__ == "__main__":
    main()
