#!/usr/bin/env python3
"""Background planner — study repo and refresh NEXT_PROMPT without a 60s wait.

Grok /loop minimum interval is 60s. For tighter continuous work use:
  1) headless chain on Stop (immediate when a turn ends)
  2) this planner as a short headless pass that only updates NEXT_PROMPT + baton
  3) optional monitor/watchdog that re-spawns when drive.lock goes stale

Does NOT implement features — only plans so the next builder turn is sharp.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def study(repo: Path) -> dict[str, Any]:
    """Deterministic study (no LLM) — file/git/feature signals for NEXT_PROMPT."""
    repo = repo.resolve()
    state = _json(repo / ".halo" / "state.json")
    loop = _json(repo / ".halo" / "loop.json")
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from halo_features import summary as feature_summary

        feats = feature_summary(repo, compound=False)
    except Exception as e:  # noqa: BLE001
        feats = {"error": str(e)}

    git: dict[str, str] = {}
    try:
        git["status"] = subprocess.check_output(
            ["git", "status", "-sb"], cwd=repo, text=True, stderr=subprocess.DEVNULL
        ).strip()[:600]
        git["log"] = subprocess.check_output(
            ["git", "log", "--oneline", "-8"], cwd=repo, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        git = {"status": "?", "log": "?"}

    # open factory diffs
    try:
        dirty = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repo, text=True, stderr=subprocess.DEVNULL
        )
        factory_dirty = [
            ln
            for ln in dirty.splitlines()
            if ln.strip()
            and not ln[3:].startswith(".halo/")
            and not ln[3:].startswith(".halo-archive/")
        ]
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        factory_dirty = []

    next_f = feats.get("next") if isinstance(feats, dict) else None
    seed_meta = _json(repo / ".halo" / "compound-seed.json")
    roadmap_exhausted = seed_meta.get("last_reason") == "no_new_roadmap"
    scores_dir = repo / ".halo" / "scores"
    scores_count = (
        len(list(scores_dir.glob("S*.json"))) if scores_dir.is_dir() else 0
    )
    traj_dir = repo / ".halo" / "trajectories"
    trajectories_count = (
        len(list(traj_dir.glob("GT-*.json"))) if traj_dir.is_dir() else 0
    )
    # D118/D119: prefer summary helpers (max S### / GT-### + payload id) when available
    latest_score_id = None
    if isinstance(feats, dict) and "latest_score_id" in feats:
        latest_score_id = feats.get("latest_score_id")
    latest_trajectory_id = None
    if isinstance(feats, dict) and "latest_trajectory_id" in feats:
        latest_trajectory_id = feats.get("latest_trajectory_id")
    plan = {
        "at": utc_now(),
        "phase": state.get("phase"),
        "status": state.get("status"),
        "autonomous": state.get("autonomous"),
        "dogfood_mode": state.get("dogfood_mode") or state.get("dogfood"),
        "loop_active": loop.get("active"),
        "loop_iteration": loop.get("iteration"),
        "features": {
            "passed": feats.get("passed"),
            "total": feats.get("total"),
            "remaining": feats.get("remaining"),
            "all_pass": feats.get("all_pass"),
            "next": next_f,
        },
        "roadmap_exhausted": roadmap_exhausted,
        "scores_count": scores_count,
        "scores_missing": scores_count == 0,
        "latest_score_id": latest_score_id,
        "trajectories_count": trajectories_count,
        "latest_trajectory_id": latest_trajectory_id,
        "factory_dirty_count": len(factory_dirty),
        "factory_dirty_sample": factory_dirty[:12],
        "git_log": git.get("log"),
        "recommendation": _recommend(
            repo, state, feats, factory_dirty, scores_count=scores_count
        ),
    }
    return plan


def _recommend(
    repo: Path,
    state: dict,
    feats: dict,
    dirty: list[str],
    *,
    scores_count: int | None = None,
) -> str:
    if (state.get("status") or "").upper() in ("PAUSED", "ESCALATED"):
        return "STOP: status not ACTIVE"
    nxt = feats.get("next") if isinstance(feats, dict) else None
    if isinstance(nxt, dict) and nxt.get("id"):
        req = " (requires_code — must land factory FILE_DIFF)" if nxt.get("requires_code") else ""
        return f"ONE unit: {nxt.get('id')} — {nxt.get('description')}{req}"
    dogfood = bool(state.get("dogfood") or state.get("dogfood_mode") == "compounding")
    if dogfood and scores_count == 0:
        return (
            "scores_missing: run a requires_code unit so set_pass writes "
            ".halo/scores/S###.json then continue compounding"
        )
    if feats.get("all_pass"):
        if dogfood:
            # Exhausted templates → expand ROADMAP, do not thrash smoke units
            reason = _json(repo / ".halo" / "compound-seed.json").get("last_reason")
            if reason == "no_new_roadmap":
                return (
                    "all_pass+no_new_roadmap: expand ROADMAP_TEMPLATES in "
                    "halo_features.py then force seed and implement first requires_code unit"
                )
            return "all_pass: force compound seed roadmap batch then implement first requires_code unit"
        return "all_pass: complete or seed next milestone"
    if dirty:
        return f"finish or commit factory dirty files first ({len(dirty)} paths)"
    return "pick next passes:false feature from feature-list"


def write_plan(repo: Path, plan: dict[str, Any]) -> Path:
    path = repo / ".halo" / "plan-latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    # baton pointer (D100: always rewrite recommendation + next id; dash when all_pass)
    baton = repo / ".halo" / "baton.md"
    nxt = (plan.get("features") or {}).get("next")
    if isinstance(nxt, dict) and nxt.get("id"):
        nid = str(nxt.get("id"))
        desc = str(nxt.get("description") or "")
    else:
        nid = "-"
        desc = "all_pass" if (plan.get("features") or {}).get("all_pass") else ""
    # D120: surface scores/trajectories counts on baton (0 when missing/empty)
    try:
        sc = int(plan.get("scores_count") or 0)
    except (TypeError, ValueError):
        sc = 0
    try:
        tc = int(plan.get("trajectories_count") or 0)
    except (TypeError, ValueError):
        tc = 0
    baton.write_text(
        "# Baton — planner refresh\n"
        f"- at: {plan.get('at')}\n"
        f"- recommendation: {plan.get('recommendation')}\n"
        f"- next: **{nid}** — {desc[:120]}\n"
        f"- features: {plan.get('features')}\n"
        f"- scores_count: {sc}\n"
        f"- trajectories_count: {tc}\n"
        f"- dirty_factory: {plan.get('factory_dirty_count')}\n"
        "- Never force-add .halo/\n",
        encoding="utf-8",
    )
    return path


def refresh_next_prompt(repo: Path, halo_sys: Path | None = None) -> Path:
    hs = halo_sys or Path(__file__).resolve().parent.parent
    cmd = [
        sys.executable,
        str(hs / "python" / "halo_next_prompt.py"),
        "--repo",
        str(repo),
        "--halo-system",
        str(hs),
        "--write",
    ]
    subprocess.run(cmd, check=False, capture_output=True, timeout=45)
    return repo / ".halo" / "NEXT_PROMPT.md"


def run_planner(repo: Path, halo_sys: Path | None = None) -> dict[str, Any]:
    plan = study(repo)
    write_plan(repo, plan)
    refresh_next_prompt(repo, halo_sys)
    # inject recommendation into top of NEXT_PROMPT
    np = repo / ".halo" / "NEXT_PROMPT.md"
    if np.exists():
        body = np.read_text(encoding="utf-8")
        exhausted = bool(plan.get("roadmap_exhausted"))
        # D094: surface roadmap_exhausted so agents expand ROADMAP_TEMPLATES
        exhausted_line = (
            f"**roadmap_exhausted:** true — expand ROADMAP_TEMPLATES in "
            f"halo_features.py then force seed\n"
            if exhausted
            else f"**roadmap_exhausted:** false\n"
        )
        banner = (
            f"# Planner refresh {plan['at']}\n"
            f"**RECOMMENDATION:** {plan['recommendation']}\n"
            f"{exhausted_line}\n"
        )
        if not body.startswith("# Planner refresh"):
            np.write_text(banner + body, encoding="utf-8")
        else:
            # replace first banner block
            rest = body.split("\n\n", 1)[-1] if "\n\n" in body else body
            np.write_text(banner + rest, encoding="utf-8")
    return {"ok": True, "plan": plan, "next_prompt": str(np)}


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_planner")
    p.add_argument("--repo", default=".")
    p.add_argument("--halo-system", default=None)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    repo = Path(args.repo).resolve()
    hs = Path(args.halo_system).resolve() if args.halo_system else None
    out = run_planner(repo, hs)
    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        rec = out["plan"]["recommendation"]
        print(f"planner ok — {rec}")
        print(f"wrote {out['next_prompt']} and .halo/plan-latest.json")


if __name__ == "__main__":
    main()
