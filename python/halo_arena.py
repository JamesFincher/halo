#!/usr/bin/env python3
"""Arena verify — independent dual-lens check before treating a unit as shippable.

Not a second LLM by default (that needs subagent spawn). Deterministic dual pass:
  A = adversarial (try to reject: missing certs, denylist, dishonest pass)
  B = constructive (try to approve if evidence + AC present)

Consensus:
  both APPROVED → APPROVED
  both REJECTED → REJECTED
  split / either NEEDS_REVISION → NEEDS_REVISION

Writes .halo/evidence/verdict-{id}.json and .halo/arena/{id}.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from halo_evidence import validate_repo
    from halo_features import load_list, summary as feature_summary
    from halo_ratchet import check as ratchet_check
except ImportError:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from halo_evidence import validate_repo  # type: ignore
    from halo_features import load_list, summary as feature_summary  # type: ignore
    from halo_ratchet import check as ratchet_check  # type: ignore


DENYLIST = re.compile(
    r"(^|/)\.env$|(^|/)\.env\.|/node_modules/|(^|/)dist/|(^|/)build/|"
    r"id_rsa|credentials\.json|secrets?\.",
    re.I,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_diff_names(repo: Path) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=repo,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        staged = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"],
            cwd=repo,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return []
    names = [n.strip() for n in (out + "\n" + staged).splitlines() if n.strip()]
    return sorted(set(names))


def _feature(repo: Path, feature_id: str) -> dict[str, Any] | None:
    data = load_list(repo)
    for f in data.get("features") or []:
        if f.get("id") == feature_id:
            return f
    return None


def pass_a_adversarial(repo: Path, feature_id: str) -> dict[str, Any]:
    """Adversarial lens: look for reasons to reject."""
    reasons: list[str] = []
    feat = _feature(repo, feature_id)
    if not feat:
        reasons.append(f"unknown feature id {feature_id}")
        return {"lens": "A_adversarial", "verdict": "REJECTED", "reasons": reasons}

    # evidence must exist and validate
    ev_rep = validate_repo(repo)
    green_ok = bool(ev_rep.get("by_kind", {}).get("green-test"))
    # also accept id-scoped green file even if kind map missed
    ev_dir = repo / ".halo" / "evidence"
    id_green = list(ev_dir.glob(f"{feature_id}*green*")) if ev_dir.is_dir() else []
    id_green += list(ev_dir.glob(f"*{feature_id}*green*")) if ev_dir.is_dir() else []
    if not green_ok and not id_green:
        reasons.append("no GREEN evidence for suite / feature")

    if feat.get("passes") and not (feat.get("verified_at") or feat.get("evidence")):
        reasons.append("feature marked passes without verified_at/evidence")

    # denylist in diff
    for name in _git_diff_names(repo):
        if DENYLIST.search(name):
            reasons.append(f"denylist path in diff: {name}")

    # test ratchet
    r = ratchet_check(repo)
    if not r.get("ok"):
        reasons.append(f"test ratchet violations: {r.get('violations')}")

    # AC steps present?
    steps = feat.get("steps") or []
    if not steps:
        reasons.append("feature has no acceptance steps")

    if reasons:
        # missing green is hard reject; soft gaps → NEEDS_REVISION
        hard = any(
            x.startswith("denylist")
            or x.startswith("test ratchet")
            or x.startswith("unknown")
            or "without verified" in x
            for x in reasons
        )
        if hard or any("no GREEN" in x for x in reasons):
            return {"lens": "A_adversarial", "verdict": "REJECTED", "reasons": reasons}
        return {"lens": "A_adversarial", "verdict": "NEEDS_REVISION", "reasons": reasons}

    return {"lens": "A_adversarial", "verdict": "APPROVED", "reasons": ["no adversarial findings"]}


def pass_b_constructive(repo: Path, feature_id: str) -> dict[str, Any]:
    """Constructive lens: look for reasons to approve."""
    notes: list[str] = []
    feat = _feature(repo, feature_id)
    if not feat:
        return {
            "lens": "B_constructive",
            "verdict": "REJECTED",
            "reasons": [f"unknown feature id {feature_id}"],
        }

    ev_dir = repo / ".halo" / "evidence"
    has_evidence = False
    if ev_dir.is_dir():
        for p in ev_dir.iterdir():
            if p.is_file() and feature_id.lower() in p.name.lower() and p.stat().st_size > 0:
                has_evidence = True
                notes.append(f"evidence file {p.name}")
                break
    if not has_evidence:
        # any green cert
        ev_rep = validate_repo(repo)
        if ev_rep.get("by_kind", {}).get("green-test"):
            has_evidence = True
            notes.append("suite-level GREEN present")

    if not has_evidence:
        return {
            "lens": "B_constructive",
            "verdict": "NEEDS_REVISION",
            "reasons": ["need GREEN or id-scoped evidence to approve"],
        }

    # plan file optional but good
    plans = repo / ".halo" / "plans"
    if plans.is_dir() and any(feature_id in p.name for p in plans.iterdir()):
        notes.append("plan artifact present")

    if feat.get("steps"):
        notes.append(f"{len(feat['steps'])} AC steps recorded")

    return {
        "lens": "B_constructive",
        "verdict": "APPROVED",
        "reasons": notes or ["evidence sufficient for constructive approve"],
    }


def consensus(a: dict[str, Any], b: dict[str, Any]) -> str:
    va, vb = a.get("verdict"), b.get("verdict")
    if va == "APPROVED" and vb == "APPROVED":
        return "APPROVED"
    if va == "REJECTED" and vb == "REJECTED":
        return "REJECTED"
    if "REJECTED" in (va, vb) and "APPROVED" in (va, vb):
        return "NEEDS_REVISION"  # split → revise, not ship
    return "NEEDS_REVISION"


def verify(repo: Path, feature_id: str) -> dict[str, Any]:
    repo = repo.resolve()
    a = pass_a_adversarial(repo, feature_id)
    b = pass_b_constructive(repo, feature_id)
    final = consensus(a, b)
    report = {
        "cert": "VERIFIER_APPROVED" if final == "APPROVED" else "VERIFIER_NOT_APPROVED",
        "feature_id": feature_id,
        "verdict": final,
        "at": utc_now(),
        "A": a,
        "B": b,
        "feature_summary": feature_summary(repo),
    }

    arena_dir = repo / ".halo" / "arena"
    arena_dir.mkdir(parents=True, exist_ok=True)
    (arena_dir / f"{feature_id}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    ev_dir = repo / ".halo" / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    (ev_dir / f"verdict-{feature_id}.json").write_text(
        json.dumps(
            {
                "cert": report["cert"],
                "feature_id": feature_id,
                "verdict": final,
                "ok": final == "APPROVED",
                "at": report["at"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return report


def spawn_check_note(repo: Path, feature_id: str, report: dict[str, Any]) -> dict[str, Any]:
    """Optional second-pass stub: record that a dual-lens verify completed.

    Full subagent spawn is host-dependent; this writes a spawn-check cert so the
    loop can require an explicit second-pass artifact without faking LLM isolation.
    """
    out = {
        "cert": "ARENA_SPAWN_CHECK",
        "feature_id": feature_id,
        "mode": "stub-second-pass",
        "note": (
            "Deterministic dual-lens already ran (A adversarial + B constructive). "
            "True multi-agent spawn remains optional; this cert proves second-pass hook."
        ),
        "base_verdict": report.get("verdict"),
        "at": utc_now(),
    }
    ev = repo / ".halo" / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    path = ev / f"arena-spawn-check-{feature_id}.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    out["path"] = str(path)
    return out


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_arena")
    p.add_argument("--repo", default=".")
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify", help="dual-lens verify one feature")
    v.add_argument("--id", required=True)
    v.add_argument("--repo", dest="repo_sub", default=None, help="repo (also allowed after verify)")
    v.add_argument(
        "--spawn-check",
        action="store_true",
        help="write arena-spawn-check-{id}.json second-pass cert (stub for multi-agent)",
    )
    args = p.parse_args()
    repo = Path(args.repo_sub or args.repo or ".")
    if args.cmd == "verify":
        rep = verify(repo, args.id)
        if args.spawn_check:
            rep["spawn_check"] = spawn_check_note(repo, args.id, rep)
        print(json.dumps(rep, indent=2))
        raise SystemExit(0 if rep["verdict"] == "APPROVED" else 2)


if __name__ == "__main__":
    main()
