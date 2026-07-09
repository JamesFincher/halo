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
        "factory_dirty_count": len(factory_dirty),
        "factory_dirty_sample": factory_dirty[:12],
        "git_log": git.get("log"),
        "recommendation": _recommend(state, feats, factory_dirty),
    }
    return plan


def _recommend(state: dict, feats: dict, dirty: list[str]) -> str:
    if (state.get("status") or "").upper() in ("PAUSED", "ESCALATED"):
        return "STOP: status not ACTIVE"
    nxt = feats.get("next") if isinstance(feats, dict) else None
    if isinstance(nxt, dict) and nxt.get("id"):
        req = " (requires_code — must land factory FILE_DIFF)" if nxt.get("requires_code") else ""
        return f"ONE unit: {nxt.get('id')} — {nxt.get('description')}{req}"
    if feats.get("all_pass"):
        if state.get("dogfood") or state.get("dogfood_mode") == "compounding":
            return "all_pass: force compound seed roadmap batch then implement first requires_code unit"
        return "all_pass: complete or seed next milestone"
    if dirty:
        return f"finish or commit factory dirty files first ({len(dirty)} paths)"
    return "pick next passes:false feature from feature-list"


def write_plan(repo: Path, plan: dict[str, Any]) -> Path:
    path = repo / ".halo" / "plan-latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    # baton pointer
    baton = repo / ".halo" / "baton.md"
    nxt = (plan.get("features") or {}).get("next") or {}
    nid = nxt.get("id") if isinstance(nxt, dict) else "-"
    desc = (nxt.get("description") if isinstance(nxt, dict) else "") or ""
    baton.write_text(
        "# Baton — planner refresh\n"
        f"- at: {plan.get('at')}\n"
        f"- recommendation: {plan.get('recommendation')}\n"
        f"- next: **{nid}** — {desc[:120]}\n"
        f"- features: {plan.get('features')}\n"
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
        banner = (
            f"# Planner refresh {plan['at']}\n"
            f"**RECOMMENDATION:** {plan['recommendation']}\n\n"
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
