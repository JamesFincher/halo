#!/usr/bin/env python3
"""Machine-readable feature list (Anthropic-style passes: bool).

Source of truth for "is the product done?" — harder to corrupt than markdown-only STORIES.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_list(repo: Path) -> dict[str, Any]:
    p = repo / ".halo" / "feature-list.json"
    if not p.exists():
        return {"version": 1, "features": [], "updated_at": None}
    return json.loads(p.read_text(encoding="utf-8"))


def save_list(repo: Path, data: dict[str, Any]) -> Path:
    data["updated_at"] = utc_now()
    p = repo / ".halo" / "feature-list.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return p


def parse_stories_md(text: str) -> list[dict[str, Any]]:
    features: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    ac: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^###\s+(S\d+)\s*[—\-–:]\s*(.+)$", line)
        if m:
            if current:
                current["steps"] = ac
                features.append(current)
            current = {
                "id": m.group(1),
                "description": m.group(2).strip(),
                "category": "story",
                "passes": False,
                "steps": [],
            }
            ac = []
            continue
        if current and line.strip().startswith("- [ ]"):
            ac.append(line.strip()[5:].strip())
        if current and "**Status**:" in line and "deployed" in line.lower():
            current["passes"] = True
        if current and "**Milestone**:" in line:
            current["milestone"] = line.split(":", 1)[-1].strip()
    if current:
        current["steps"] = ac
        features.append(current)
    return features


def sync_from_stories(repo: Path) -> dict[str, Any]:
    stories_p = repo / ".halo" / "spec" / "STORIES.md"
    existing = load_list(repo)
    by_id = {f["id"]: f for f in existing.get("features") or [] if f.get("id")}

    if stories_p.exists():
        parsed = parse_stories_md(stories_p.read_text(encoding="utf-8"))
    else:
        # from intake features
        state = {}
        sp = repo / ".halo" / "state.json"
        if sp.exists():
            state = json.loads(sp.read_text(encoding="utf-8"))
        feats = (state.get("intake") or {}).get("features") or []
        parsed = []
        for i, f in enumerate(feats, 1):
            if isinstance(f, dict):
                parsed.append(
                    {
                        "id": f.get("id") or f"S{i:03d}",
                        "description": f.get("title") or f.get("name") or str(f),
                        "category": "intake",
                        "passes": False,
                        "steps": [f.get("one_liner")] if f.get("one_liner") else [],
                    }
                )
            else:
                parsed.append(
                    {
                        "id": f"S{i:03d}",
                        "description": str(f),
                        "category": "intake",
                        "passes": False,
                        "steps": [],
                    }
                )

    merged = []
    for f in parsed:
        old = by_id.get(f["id"], {})
        f["passes"] = bool(old.get("passes", f.get("passes", False)))
        if old.get("verified_at"):
            f["verified_at"] = old["verified_at"]
        merged.append(f)

    data = {"version": 1, "features": merged, "updated_at": utc_now()}
    save_list(repo, data)
    return data


def _find_green_evidence(repo: Path, feature_id: str, explicit: str | None) -> Path | None:
    """Locate GREEN evidence scoped to this feature id only (no cross-feature reuse)."""
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = (repo / p).resolve()
        if not p.exists() or p.stat().st_size <= 0:
            return None
        # explicit path must still mention feature id (blocks reusing another story's cert)
        if feature_id.lower() not in p.name.lower() and feature_id.lower() not in str(p).lower():
            return None
        return p
    ev = repo / ".halo" / "evidence"
    if not ev.is_dir():
        return None
    # id must appear in filename — never steal another feature's green cert
    patterns = [
        f"{feature_id}-green*",
        f"green-test-{feature_id}*",
        f"*{feature_id}*green*",
        f"*green*{feature_id}*",
        f"{feature_id}.*",
        f"*{feature_id}*",
    ]
    for pat in patterns:
        hits = sorted(ev.glob(pat), key=lambda x: x.stat().st_mtime, reverse=True)
        for h in hits:
            if feature_id.lower() not in h.name.lower():
                continue
            if h.stat().st_size > 0:
                return h
    return None


def _evidence_looks_green(path: Path) -> bool:
    try:
        from halo_evidence import validate_green_test

        ok, _ = validate_green_test(path)
        if ok:
            return True
    except Exception:  # noqa: BLE001
        pass
    text = path.read_text(encoding="utf-8", errors="replace")
    if re.search(r"exit_code\s*[:=]\s*0\b", text) or re.search(r'"ok"\s*:\s*true', text, re.I):
        return True
    if "PASS" in text and path.stat().st_size > 20:
        return True
    # non-empty named evidence with feature id is accepted if not clearly red
    if path.stat().st_size > 0 and not re.search(r"exit_code\s*[:=]\s*[1-9]", text):
        return True
    return False


def append_features(repo: Path, features: list[dict[str, Any]]) -> dict[str, Any]:
    """Add features by id if missing (for milestone seeding under go)."""
    data = load_list(repo)
    existing = {f.get("id") for f in data.get("features") or []}
    for f in features:
        fid = f.get("id")
        if not fid or fid in existing:
            continue
        row = {
            "id": fid,
            "description": f.get("description") or f.get("title") or fid,
            "category": f.get("category") or "story",
            "passes": False,
            "steps": list(f.get("steps") or []),
        }
        if f.get("milestone"):
            row["milestone"] = f["milestone"]
        # Preserve compounding flags (FILE_DIFF gate)
        if "requires_code" in f:
            row["requires_code"] = bool(f.get("requires_code"))
        data.setdefault("features", []).append(row)
        existing.add(fid)
    save_list(repo, data)
    return data


def _load_state(repo: Path) -> dict[str, Any]:
    sp = repo / ".halo" / "state.json"
    if not sp.exists():
        return {}
    try:
        return json.loads(sp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _utc_day(ts: str | None = None) -> str:
    if ts:
        return str(ts)[:10]
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _next_d_ids(features: list[dict[str, Any]], n: int = 3) -> list[str]:
    """Allocate next free D### ids (max existing + 1)."""
    max_n = 0
    for f in features:
        fid = str(f.get("id") or "")
        m = re.match(r"^D(\d+)$", fid, re.I)
        if m:
            max_n = max(max_n, int(m.group(1)))
    start = max_n + 1
    return [f"D{start + i:03d}" for i in range(n)]


# Real factory upgrades only — never pure "still green" smoke (anti-thrash).
# When all descs already exist, seed returns no_new_roadmap — expand this list.
ROADMAP_TEMPLATES: list[tuple[str, list[str]]] = [
    (
        "Stop hook writes .halo/logs/stop-last.json with spawn result",
        ["stop-last.json written on Stop", "includes iteration + spawn ok/error"],
    ),
    (
        "Compounding feature pass requires factory FILE_DIFF unless requires_code false",
        ["set_pass refuses code units with empty factory git diff", "--force still works"],
    ),
    (
        "halo drive status JSON includes loop iteration and feature next id",
        ["drive status prints loop.iteration and next feature id"],
    ),
    (
        "Auto-commit unit helper refuses .halo/ and stages only factory paths",
        ["halo commit-unit dry-run lists factory files only"],
    ),
    (
        "cycle-smoke fails if tracked denylist paths appear in git ls-files",
        ["already partly present; strengthen denylist check for secrets patterns"],
    ),
    (
        "Independent Arena runner optional second-pass via subagent spawn flag",
        ["halo arena documents dual-lens; optional --spawn-check flag stub"],
    ),
    # Batch 6+ — keep compounding when earlier templates already passed
    (
        "Watchdog single-instance: exit if pidfile PID is still alive",
        [
            "second watchdog start exits non-zero when pidfile process lives",
            "pidfile written only by the winning instance",
        ],
    ),
    (
        "cycle-smoke runs unittest discover and fails on non-zero",
        [
            "halo-cycle-smoke.sh invokes python -m unittest discover -s python/tests",
            "failure exits non-zero before features summary",
        ],
    ),
    (
        "drive status JSON includes watchdog_pid and heartbeat_age_sec",
        [
            "status reads .halo/logs/watchdog.pid + watchdog-heartbeat.json",
            "heartbeat_age_sec is null when heartbeat missing",
        ],
    ),
    (
        "Planner surfaces no_new_roadmap when compound templates exhausted",
        [
            "recommendation mentions expand ROADMAP_TEMPLATES when seed blocked",
            "compound-seed.json records last_reason=no_new_roadmap",
        ],
    ),
    (
        "scripts/halo features seed forwards --force to halo_features",
        ["halo features seed --force works from CLI", "help lists seed subcommand"],
    ),
    (
        "Doctor warns when autonomous loop has stale watchdog heartbeat",
        [
            "strict mode surfaces stale heartbeat older than 90s",
            "fresh heartbeat under 90s is not a doctor error",
        ],
    ),
    (
        "Budget gate verdict printed in drive status JSON",
        ["drive status includes budget.verdict ALLOW|DEGRADE|PAUSE", "reads spend.json safely"],
    ),
    (
        "Stop hook increments loop.iteration only when spawn ok",
        ["failed spawn does not burn iteration", "stop-last records skip reason"],
    ),
    (
        "halo go --spawn starts watchdog if not already running",
        ["go with spawn checks pidfile", "does not double-start watchdog"],
    ),
    (
        "Evidence cert schema validator rejects missing cert field",
        ["halo evidence check fails without cert key", "GREEN_TEST accepted"],
    ),
    (
        "NEXT_PROMPT lists last 3 autonomous-log lines under Progress",
        ["tail autonomous-log.md into prompt context", "truncated lines"],
    ),
    (
        "Compound seed skip reason no_new_roadmap triggers roadmap_exhausted in plan-latest",
        ["plan-latest.json has roadmap_exhausted bool", "true only when last_reason matches"],
    ),
    (
        "halo status prints budget verdict and watchdog age",
        ["status human output includes budget ALLOW/PAUSE", "watchdog heartbeat age when present"],
    ),
    (
        "Arena verify refuses pass without GREEN evidence path",
        ["arena NEEDS_REVISION when evidence missing", "writes arena cert"],
    ),
    (
        "drive spawn --force clears dead lock and restarts",
        ["--force reaps dead pid and spawns", "alive pid without force refuses"],
    ),
    (
        "plugin.json version bumps when continuous-drive surface changes",
        ["document version in plugin.json matches CHANGELOG or TRUE-LOOP note", "minor bump for this release"],
    ),
    (
        "scripts/halo help lists plan watchdog cycle-smoke reinstantiate",
        ["help text contains all continuous-drive verbs", "regression test on help string"],
    ),
    (
        "compound seed force refuses when backlog has open requires_code units",
        ["force does not seed over pending features", "reason not_all_pass"],
    ),
    (
        "progress add records factory dirty count on unit events",
        ['progress.jsonl unit events include dirty_count field', 'zero when clean'],
    ),
    (
        "halo doctor --strict fails if plugin.json missing version",
        ['doctor error code plugin_version_missing', 'present version is info only'],
    ),
    (
        "drive should-drive exits 0 only when loop active and work remains",
        ['exit 1 when all_pass and not compounding seed pending', 'exit 0 with open backlog'],
    ),
    (
        "NEXT_PROMPT includes roadmap_exhausted flag when true",
        ['prompt text mentions ROADMAP_TEMPLATES expand when exhausted'],
    ),
    (
        "cancel-halo-loop disarms loop.json and kills drive pid if owned",
        ['loop active false after cancel', 'watchdog pidfile cleared'],
    ),
    (
        "arena --spawn-check writes ARENA_SPAWN_CHECK cert with feature id",
        ['evidence file contains cert and feature', 'CLI exit 0 on APPROVED'],
    ),
    # Batch 14+ — anti thrash after D096
    (
        "halo budget show prints spend and max_iterations together",
        [
            "budget show JSON has spend and budget.max_iterations",
            "CLI exit 0",
        ],
    ),
    (
        "feature summary JSON includes next.requires_code when present",
        [
            "summary next object carries requires_code bool",
            "null next when all_pass",
        ],
    ),
    (
        "halo probe --url rejects empty URL with non-zero exit",
        [
            "empty or missing url exits non-zero",
            "help lists --url",
        ],
    ),
    (
        "baton.md records recommendation and next id after planner run",
        [
            "write_plan always rewrites baton recommendation line",
            "next id dash when all_pass",
        ],
    ),
    (
        "cycle-smoke evidence cert field is GREEN_TEST",
        [
            "D-cycle-smoke-latest.json has cert GREEN_TEST",
            "exit_code 0",
        ],
    ),
    (
        "halo handoff writes .halo/handoff.md with phase and next feature",
        [
            "handoff.md created non-empty",
            "includes phase and next feature id or all_pass",
        ],
    ),
    (
        "Compounding approved cycle writes .halo/scores/SNNN.json six-dimension stub",
        ['score file has tool_selection and warm_start_directive fields', 'id matches cycle or sequential S###'],
    ),
    (
        "Compounding approved cycle records golden trajectory GT stub",
        ['writes .halo/trajectories/GT-NNN.json with step sequence', 'includes git head and feature id'],
    ),
    (
        "loop.json last_head refreshed on successful features pass",
        ['set_pass updates loop.last_head to current HEAD when loop active', 'missing loop.json is non-fatal'],
    ),
    (
        "halo plan surfaces scores_missing warn when scores dir empty under compounding",
        ['plan-latest.json has scores_count int', 'recommendation mentions scores when count 0 and compounding'],
    ),
    (
        "progress unit event includes feature_id when provided",
        ['progress add --event unit --json with feature_id persists field', 'optional field'],
    ),
    (
        "doctor warns when compounding self-instance and scores directory empty",
        ['level warn code scores_empty', 'not an error so strict still passes'],
    ),
    # Batch 18+ — compound after D108 / scores culture
    (
        "features summary JSON includes top-level scores_count",
        [
            "summary has scores_count int (0 when dir missing/empty)",
            "counts *.json under .halo/scores/",
        ],
    ),
    (
        "halo scores list CLI prints count and latest id",
        [
            "python halo_scores.py list --repo exits 0",
            "JSON has count and latest fields",
        ],
    ),
    (
        "plan-latest includes trajectories_count alongside scores_count",
        [
            "study/write_plan sets trajectories_count int",
            "0 when trajectories dir missing",
        ],
    ),
    # Batch 19+ — trajectories parity with scores culture
    (
        "features summary JSON includes top-level trajectories_count",
        [
            "summary has trajectories_count int (0 when dir missing/empty)",
            "counts GT-*.json under .halo/trajectories/",
        ],
    ),
    (
        "halo scores trajectories list CLI prints count and latest id",
        [
            "python halo_scores.py trajectories --repo exits 0",
            "JSON has count and latest fields for GT-*.json",
        ],
    ),
    (
        "doctor warns when compounding self-instance and trajectories directory empty",
        [
            "level warn code trajectories_empty",
            "not an error so strict still passes",
        ],
    ),
    # Batch 20+ — latest id surfaces + count parity health
    (
        "features summary JSON includes top-level latest_score_id",
        [
            "summary has latest_score_id string or null",
            "max S### id under .halo/scores/; null when empty/missing",
        ],
    ),
    (
        "features summary JSON includes top-level latest_trajectory_id",
        [
            "summary has latest_trajectory_id string or null",
            "max GT-### id under .halo/trajectories/; null when empty/missing",
        ],
    ),
    (
        "doctor warns when compounding self-instance and scores_count differs from trajectories_count",
        [
            "level warn code scores_trajectories_diverge when counts unequal",
            "not an error so strict still passes; skip when both zero",
        ],
    ),
    # Batch 21+ — plan/baton surface latest score+trajectory ids
    (
        "plan-latest includes latest_score_id alongside scores_count",
        [
            "study/write_plan sets latest_score_id string or null",
            "max S### under .halo/scores/; null when empty/missing",
        ],
    ),
    (
        "plan-latest includes latest_trajectory_id alongside trajectories_count",
        [
            "study/write_plan sets latest_trajectory_id string or null",
            "max GT-### under .halo/trajectories/; null when empty/missing",
        ],
    ),
    (
        "baton.md records scores_count and trajectories_count after planner run",
        [
            "write_plan baton lines include scores_count and trajectories_count",
            "zeros when dirs empty/missing",
        ],
    ),
    # Batch 22+ — baton/status/summary surface latest ids + count match
    (
        "baton.md records latest_score_id and latest_trajectory_id after planner run",
        [
            "write_plan baton lines include latest_score_id and latest_trajectory_id",
            "dash or null when missing/empty",
        ],
    ),
    (
        "halo status prints latest_score_id and latest_trajectory_id when present",
        [
            "status human or JSON includes latest_score_id from features summary",
            "latest_trajectory_id printed when non-null",
        ],
    ),
    (
        "features summary JSON includes top-level scores_trajectories_match bool",
        [
            "true when scores_count == trajectories_count (including both zero)",
            "false when counts diverge",
        ],
    ),
    # Batch 23+ — plan/baton/status surface scores_trajectories_match + counts
    (
        "plan-latest includes scores_trajectories_match bool",
        [
            "study/write_plan sets scores_trajectories_match bool",
            "true when scores_count == trajectories_count (including both zero)",
        ],
    ),
    (
        "baton.md records scores_trajectories_match after planner run",
        [
            "write_plan baton line includes scores_trajectories_match",
            "true/false matching plan field",
        ],
    ),
    (
        "halo status prints scores_count trajectories_count and scores_trajectories_match",
        [
            "status human output includes scores_count and trajectories_count ints",
            "scores_trajectories_match printed as true/false",
        ],
    ),
    # Batch 24+ — NEXT_PROMPT / progress / planner surface match culture
    (
        "NEXT_PROMPT includes scores_count trajectories_count scores_trajectories_match",
        [
            "feature list section lists scores_count and trajectories_count ints",
            "scores_trajectories_match printed as true/false",
        ],
    ),
    (
        "progress unit event auto-records scores_count and trajectories_count",
        [
            "progress.jsonl unit events include scores_count and trajectories_count ints",
            "zeros when dirs empty/missing",
        ],
    ),
    (
        "planner recommendation warns when scores_trajectories_match is false under compounding",
        [
            "recommendation mentions scores_trajectories_diverge when counts unequal",
            "skip when match true or not compounding",
        ],
    ),
    # Batch 25+ — latest ids in prompt + match in progress + handoff health
    (
        "NEXT_PROMPT includes latest_score_id and latest_trajectory_id",
        [
            "feature list section lists latest_score_id and latest_trajectory_id",
            "dash or null when missing/empty",
        ],
    ),
    (
        "progress unit event auto-records scores_trajectories_match",
        [
            "progress.jsonl unit events include scores_trajectories_match bool",
            "true when counts equal including both zero",
        ],
    ),
    (
        "halo handoff writes scores_count trajectories_count scores_trajectories_match",
        [
            "handoff.md includes scores_count and trajectories_count",
            "scores_trajectories_match true/false",
        ],
    ),
    # Batch 26+ — latest ids in handoff/progress + drive status health
    (
        "halo handoff writes latest_score_id and latest_trajectory_id",
        [
            "handoff.md includes latest_score_id and latest_trajectory_id",
            "dash when missing/empty",
        ],
    ),
    (
        "progress unit event auto-records latest_score_id and latest_trajectory_id",
        [
            "progress.jsonl unit events include latest_score_id and latest_trajectory_id",
            "null when dirs empty/missing",
        ],
    ),
    (
        "drive status JSON includes scores_count trajectories_count scores_trajectories_match",
        [
            "drive status features object has scores_count and trajectories_count ints",
            "scores_trajectories_match bool when summary available",
        ],
    ),
    # Batch 27+ — drive latest ids + go plan health + cycle-smoke score surface
    (
        "drive status JSON includes latest_score_id and latest_trajectory_id",
        [
            "drive status features object has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
    (
        "halo go --plan JSON includes scores_count trajectories_count scores_trajectories_match",
        [
            "go --plan top-level has scores_count and trajectories_count ints",
            "scores_trajectories_match bool when summary available",
        ],
    ),
    (
        "cycle-smoke evidence includes scores_count trajectories_count scores_trajectories_match",
        [
            "D-cycle-smoke-latest.json has scores_count and trajectories_count ints",
            "scores_trajectories_match bool",
        ],
    ),
    # Batch 28+ — latest ids on cycle-smoke + go plan + budget show health
    (
        "cycle-smoke evidence includes latest_score_id and latest_trajectory_id",
        [
            "D-cycle-smoke-latest.json has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
    (
        "halo go --plan JSON includes latest_score_id and latest_trajectory_id",
        [
            "go --plan top-level has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
    (
        "halo budget show JSON includes scores_count trajectories_count scores_trajectories_match",
        [
            "budget show JSON has scores_count and trajectories_count ints",
            "scores_trajectories_match bool when summary available",
        ],
    ),
    # Batch 29+ — budget show latest ids + budget check score surface
    (
        "halo budget show JSON includes latest_score_id and latest_trajectory_id",
        [
            "budget show top-level has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
    (
        "halo budget check JSON includes scores_count trajectories_count scores_trajectories_match",
        [
            "budget check JSON has scores_count and trajectories_count ints",
            "scores_trajectories_match bool when summary available",
        ],
    ),
    (
        "halo budget check JSON includes latest_score_id and latest_trajectory_id",
        [
            "budget check top-level has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
    # Batch 30+ — doctor JSON score culture (operators + inject)
    (
        "halo doctor JSON report includes scores_count trajectories_count scores_trajectories_match",
        [
            "doctor --json top-level has scores_count and trajectories_count ints",
            "scores_trajectories_match bool when summary available",
        ],
    ),
    (
        "halo doctor JSON report includes latest_score_id and latest_trajectory_id",
        [
            "doctor --json top-level has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
    (
        "halo features pass JSON includes scores_count trajectories_count scores_trajectories_match",
        [
            "features pass stdout JSON has scores_count and trajectories_count ints",
            "scores_trajectories_match bool after mark",
        ],
    ),
    # Batch 31+ — features pass/fail latest ids + arena score culture
    (
        "halo features pass JSON includes latest_score_id and latest_trajectory_id",
        [
            "features pass stdout JSON has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
    (
        "halo features fail JSON includes latest_score_id and latest_trajectory_id",
        [
            "features fail stdout JSON has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
    (
        "halo arena JSON includes scores_count trajectories_count scores_trajectories_match",
        [
            "arena stdout or cert JSON has scores_count and trajectories_count ints",
            "scores_trajectories_match bool when summary available",
        ],
    ),
    # Batch 32+ — arena latest ids + features fail counts + seed surface
    (
        "halo arena JSON includes latest_score_id and latest_trajectory_id",
        [
            "arena stdout or cert JSON has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
    (
        "halo features fail JSON includes scores_count trajectories_count scores_trajectories_match",
        [
            "features fail stdout JSON has scores_count and trajectories_count ints",
            "scores_trajectories_match bool after mark",
        ],
    ),
    (
        "halo features seed JSON includes latest_score_id and latest_trajectory_id",
        [
            "seed stdout JSON has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
    # Batch 33+ — seed counts lock + compound-seed meta + escalate surface
    (
        "halo features seed JSON includes scores_count trajectories_count scores_trajectories_match",
        [
            "seed stdout JSON has scores_count and trajectories_count ints",
            "scores_trajectories_match bool (true when equal including both zero)",
        ],
    ),
    (
        "compound-seed.json records latest_score_id and latest_trajectory_id on seed write",
        [
            "compound-seed.json has latest_score_id and latest_trajectory_id after successful seed",
            "null when scores/trajectories dirs empty or missing at seed time",
        ],
    ),
    (
        "halo escalate JSON includes latest_score_id and latest_trajectory_id",
        [
            "escalate packet or stdout JSON has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
    # Batch 34+ — escalate counts + commit-unit score culture
    (
        "halo escalate JSON includes scores_count trajectories_count scores_trajectories_match",
        [
            "escalate packet or stdout JSON has scores_count and trajectories_count ints",
            "scores_trajectories_match bool (true when equal including both zero)",
        ],
    ),
    (
        "halo commit-unit JSON includes latest_score_id and latest_trajectory_id",
        [
            "commit-unit stdout JSON has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
    (
        "halo commit-unit JSON includes scores_count trajectories_count scores_trajectories_match",
        [
            "commit-unit stdout JSON has scores_count and trajectories_count ints",
            "scores_trajectories_match bool (true when equal including both zero)",
        ],
    ),
    # Batch 38+ — seed meta counts + evidence score culture (after D168 exhaust)
    (
        "compound-seed.json records scores_count trajectories_count scores_trajectories_match on seed write",
        [
            "compound-seed.json has scores_count and trajectories_count ints after successful seed",
            "scores_trajectories_match bool (true when equal including both zero)",
        ],
    ),
    (
        "halo evidence check JSON includes scores_count trajectories_count scores_trajectories_match",
        [
            "evidence --check JSON has scores_count and trajectories_count ints",
            "scores_trajectories_match bool (true when equal including both zero)",
        ],
    ),
    (
        "halo evidence check JSON includes latest_score_id and latest_trajectory_id",
        [
            "evidence --check JSON has latest_score_id and latest_trajectory_id",
            "null when scores/trajectories dirs empty or missing",
        ],
    ),
]


def _default_compound_batch(ids: list[str]) -> list[dict[str, Any]]:
    """Three factory-upgrade units (requires_code) for compounding day."""
    out: list[dict[str, Any]] = []
    for i, fid in enumerate(ids):
        desc, steps = ROADMAP_TEMPLATES[i % len(ROADMAP_TEMPLATES)]
        out.append(
            {
                "id": fid,
                "requires_code": True,
                "description": desc,
                "category": "dogfood",
                "passes": False,
                "milestone": "M-compound",
                "steps": steps,
            }
        )
    return out


def maybe_seed_compounding_batch(
    repo: Path,
    *,
    force: bool = False,
    count: int = 3,  # noqa: ARG001 — fixed batch of 3 for now
) -> dict[str, Any]:
    """Alias for maybe_compound_seed with stable keys for tests/CLI (D030).

    Returns {seeded, added, reason, date?} plus score surface via pass_score_fields:
    D154 counts/match + D153 latest_score_id / latest_trajectory_id.
    Seed never allocates score stubs — pure read of .halo/scores|trajectories.
    """
    repo = Path(repo).resolve()
    r = maybe_compound_seed(repo, force=force)
    if r.get("seeded"):
        out: dict[str, Any] = {
            "seeded": True,
            "added": list(r.get("ids") or []),
            "reason": "seeded",
            "date": r.get("day"),
            "batch": r.get("batch"),
        }
    else:
        reason_map = {
            "not_dogfood": "not compounding",
            "not_all_pass": "not all_pass",
            "already_seeded_today": "already seeded today",
            "empty_list": "not all_pass",
        }
        raw = str(r.get("reason") or "noop")
        out = {
            "seeded": False,
            "added": [],
            "reason": reason_map.get(raw, raw),
        }
    # D153–D154: merge latest ids + counts/match into seed CLI/library JSON
    return {**out, **pass_score_fields(repo)}


def _factory_diff_paths(repo: Path) -> list[str]:
    """Changed factory paths (excludes .halo/ and archives).

    D167: .halo/ and .halo-archive/ alone never satisfy the FILE_DIFF gate.
    """
    import subprocess

    names: set[str] = set()
    for args in (
        ["diff", "--name-only"],
        ["diff", "--cached", "--name-only"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        try:
            out = subprocess.check_output(
                ["git", *args], cwd=repo, text=True, stderr=subprocess.DEVNULL
            )
        except (subprocess.CalledProcessError, FileNotFoundError, OSError):
            continue
        for line in out.splitlines():
            line = line.strip()
            if not line or line.startswith(".halo/") or line.startswith(".halo-archive/"):
                continue
            if line in ("init.sh", "halo-health.json"):
                continue
            names.add(line)
    return sorted(names)


def _needs_factory_file_diff(feature: dict[str, Any]) -> bool:
    """D167: only requires_code=true units need factory FILE_DIFF before pass.

    requires_code false or absent → no gate (docs/meta units allowed).
    """
    return feature.get("requires_code") is True


def pass_score_fields(repo: Path) -> dict[str, Any]:
    """D147–D154: scores/trajectories surface on features pass/fail/seed stdout JSON.

    Counts + match: D147 (pass) / D152 (fail) / D154 (seed).
    Latest ids: D148 (pass) / D149 (fail) / D153 (seed).
    Pass path may create on_feature_pass stubs first (counts rise);
    fail and seed never do — pure pre-op counts and null ids when dirs empty/missing.
    Not persisted into feature-list.json — stdout envelope only.
    """
    sc = _scores_count(repo)
    tc = _trajectories_count(repo)
    return {
        "scores_count": sc,
        "trajectories_count": tc,
        "scores_trajectories_match": sc == tc,
        # D148–D149: latest ids (null when empty/missing)
        "latest_score_id": _latest_score_id(repo),
        "latest_trajectory_id": _latest_trajectory_id(repo),
    }


def set_pass(
    repo: Path,
    feature_id: str,
    passes: bool,
    note: str = "",
    *,
    evidence: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Mark feature pass/fail. Pass requires evidence unless --force.

    D167: requires_code=true features also need factory FILE_DIFF (anti smoke-thrash).
    requires_code false/absent skips the FILE_DIFF gate. --force bypasses both gates.
    D147–D152: return value includes scores_count / trajectories_count /
    scores_trajectories_match + latest_score_id / latest_trajectory_id
    (post-mark) for both pass and fail CLI stdout (operators + inject).
    Fail leaves counts unchanged (no on_feature_pass); D152 locks that surface.
    """
    repo = Path(repo)
    data = load_list(repo)
    found = False
    for f in data.get("features") or []:
        if f.get("id") == feature_id:
            if passes and not force:
                ev_path = _find_green_evidence(repo, feature_id, evidence)
                if not ev_path or not _evidence_looks_green(ev_path):
                    raise SystemExit(
                        f"refuse pass for {feature_id}: need GREEN evidence under "
                        f".halo/evidence/ (e.g. {feature_id}-green.json) or --evidence PATH. "
                        f"Use --force only for human override."
                    )
                if _needs_factory_file_diff(f):
                    diffs = _factory_diff_paths(repo)
                    if not diffs:
                        raise SystemExit(
                            f"refuse pass for {feature_id}: requires_code but no factory "
                            f"FILE_DIFF (.halo/ alone does not count). "
                            f"Implement code first, or --force."
                        )
                    f["factory_diff"] = diffs[:40]
                try:
                    f["evidence"] = str(
                        ev_path.relative_to(repo) if ev_path.is_relative_to(repo) else ev_path
                    )
                except (ValueError, TypeError):
                    f["evidence"] = str(ev_path)
            f["passes"] = passes
            f["verified_at"] = utc_now() if passes else None
            if note:
                f["note"] = note
            if not passes:
                f.pop("evidence", None)
                f.pop("factory_diff", None)
            found = True
            # D103–D105: score stub + golden trajectory + refresh loop.last_head
            if passes:
                try:
                    from halo_scores import on_feature_pass

                    f["dogfood_meta"] = on_feature_pass(repo, feature_id, note=note)
                except Exception as e:  # noqa: BLE001 — never block pass on meta
                    f["dogfood_meta"] = {"error": str(e)}
            break
    if not found:
        raise SystemExit(f"unknown feature id: {feature_id}")
    save_list(repo, data)
    # Keep markdown STORIES in sync with machine feature-list (S015)
    try:
        from halo_stories_sync import sync as stories_sync

        stories_sync(repo)
    except Exception:  # noqa: BLE001
        pass
    # Compounding: never idle on all_pass — seed next batch once/day
    if passes:
        try:
            maybe_compound_seed(repo)
        except Exception:  # noqa: BLE001
            pass
    # D147: merge post-mark score surface into CLI JSON (do not persist into list)
    return {**data, **pass_score_fields(repo)}


def _next_d_id(existing_ids: set[str]) -> str:
    """Allocate next D### id above current max."""
    max_n = 0
    for i in existing_ids:
        m = re.match(r"^D(\d+)$", str(i), re.I)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"D{max_n + 1:03d}"


def maybe_compound_seed(repo: Path, *, force: bool = False) -> dict[str, Any]:
    """When compounding mode + all_pass, append 3 new D-features once per UTC day (D030).

    On successful seed write, compound-seed.json records latest_score_id and
    latest_trajectory_id (D155); null when scores/trajectories empty or missing.
    Also records scores_count, trajectories_count, scores_trajectories_match (D169).
    """
    repo = Path(repo).resolve()
    state = _load_state(repo)
    data = load_list(repo)
    dogfood = bool(
        state.get("dogfood")
        or state.get("dogfood_mode") == "compounding"
        or data.get("dogfood")
        or data.get("dogfood_mode") == "compounding"
    )
    if not dogfood:
        return {"seeded": False, "reason": "not_dogfood"}

    feats = list(data.get("features") or [])
    if not feats:
        return {"seeded": False, "reason": "empty_list"}
    # force only overrides once-per-day, never seeds over an open backlog
    if not all(f.get("passes") for f in feats):
        return {"seeded": False, "reason": "not_all_pass"}

    today = _utc_day()
    seed_p = repo / ".halo" / "compound-seed.json"
    seed_meta: dict[str, Any] = {}
    if seed_p.exists():
        try:
            seed_meta = json.loads(seed_p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            seed_meta = {}
    last_day = seed_meta.get("last_seed_day") or data.get("last_compound_seed_date")
    if last_day and _utc_day(str(last_day)) == today and not force:
        return {"seeded": False, "reason": "already_seeded_today", "day": today}

    existing = {str(f.get("id")) for f in feats if f.get("id")}
    existing_desc = {
        str(f.get("description") or "").strip().lower() for f in feats if f.get("description")
    }
    batch_n = int(seed_meta.get("batch") or 0) + 1
    # Real roadmap only — ban pure smoke/verify templates (anti-thrash)
    picks: list[tuple[str, list[str]]] = []
    for i in range(len(ROADMAP_TEMPLATES) * 2):
        desc, steps = ROADMAP_TEMPLATES[(batch_n + i) % len(ROADMAP_TEMPLATES)]
        if desc.strip().lower() in existing_desc or any(desc == p[0] for p in picks):
            continue
        picks.append((desc, steps))
        if len(picks) >= 3:
            break
    if not picks:
        # Persist reason so planner/drive can surface exhausted templates
        seed_meta = {
            **seed_meta,
            "last_seed_day": last_day or seed_meta.get("last_seed_day"),
            "last_reason": "no_new_roadmap",
            "last_reason_at": utc_now(),
            "day": today,
            "batch": int(seed_meta.get("batch") or 0),
        }
        seed_p.parent.mkdir(parents=True, exist_ok=True)
        seed_p.write_text(json.dumps(seed_meta, indent=2) + "\n", encoding="utf-8")
        return {"seeded": False, "reason": "no_new_roadmap", "day": today}
    new_feats: list[dict[str, Any]] = []
    for desc, steps in picks:
        fid = _next_d_id(existing)
        existing.add(fid)
        new_feats.append(
            {
                "id": fid,
                "description": desc,
                "category": "dogfood",
                "requires_code": True,
                "passes": False,
                "milestone": f"M-compound-{batch_n}",
                "steps": steps
                + ["Factory code diff required", "Run halo cycle-smoke .", "Evidence + features pass"],
            }
        )
    append_features(repo, new_feats)
    data = load_list(repo)
    data["last_compound_seed_date"] = today
    data["dogfood"] = True
    data["dogfood_mode"] = data.get("dogfood_mode") or "compounding"
    save_list(repo, data)

    # D155: persist latest score/trajectory ids at seed write (null when empty/missing)
    # D169: also persist counts + scores_trajectories_match (true when equal, incl. both zero)
    sc = _scores_count(repo)
    tc = _trajectories_count(repo)
    seed_meta = {
        "last_seed_day": today,
        "batch": batch_n,
        "seeded_ids": [f["id"] for f in new_feats],
        "at": utc_now(),
        "last_reason": "seeded",
        "latest_score_id": _latest_score_id(repo),
        "latest_trajectory_id": _latest_trajectory_id(repo),
        "scores_count": sc,
        "trajectories_count": tc,
        "scores_trajectories_match": sc == tc,
    }
    seed_p.parent.mkdir(parents=True, exist_ok=True)
    seed_p.write_text(json.dumps(seed_meta, indent=2) + "\n", encoding="utf-8")

    sp = repo / ".halo" / "state.json"
    if sp.exists():
        try:
            st = json.loads(sp.read_text(encoding="utf-8"))
            st["dogfood_last_seed_date"] = today
            st["updated_at"] = utc_now()
            sp.write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8")
        except (OSError, json.JSONDecodeError):
            pass

    return {"seeded": True, "batch": batch_n, "ids": seed_meta["seeded_ids"], "day": today}


def _summary_next(feat: dict[str, Any] | None) -> dict[str, Any] | None:
    """Slim next feature for operators/agents (D098: always include requires_code)."""
    if not feat:
        return None
    out: dict[str, Any] = {
        "id": feat.get("id"),
        "description": feat.get("description"),
        "category": feat.get("category"),
        "passes": bool(feat.get("passes")),
        "requires_code": bool(feat.get("requires_code")),
        "milestone": feat.get("milestone"),
        "steps": list(feat.get("steps") or []),
    }
    if feat.get("evidence"):
        out["evidence"] = feat.get("evidence")
    return out


def _scores_count(repo: Path) -> int:
    """Count score stub JSON files under .halo/scores/ (D109)."""
    scores = repo / ".halo" / "scores"
    if not scores.is_dir():
        return 0
    try:
        return sum(1 for p in scores.iterdir() if p.is_file() and p.suffix == ".json")
    except OSError:
        return 0


def _latest_score_id(repo: Path) -> str | None:
    """Max numeric S### id under .halo/scores/ (D115); null when empty/missing."""
    scores = repo / ".halo" / "scores"
    if not scores.is_dir():
        return None
    best_n = -1
    best_id: str | None = None
    try:
        for p in scores.iterdir():
            if not p.is_file() or p.suffix != ".json":
                continue
            m = re.match(r"^S(\d+)$", p.stem, re.I)
            if not m:
                continue
            n = int(m.group(1))
            if n > best_n:
                best_n = n
                # Prefer payload id when present and well-formed
                try:
                    payload = json.loads(p.read_text(encoding="utf-8"))
                    pid = payload.get("id") if isinstance(payload, dict) else None
                    if isinstance(pid, str) and re.match(r"^S\d+$", pid, re.I):
                        best_id = pid
                    else:
                        best_id = p.stem
                except (OSError, json.JSONDecodeError):
                    best_id = p.stem
    except OSError:
        return None
    return best_id


def _trajectories_count(repo: Path) -> int:
    """Count GT-*.json golden trajectories under .halo/trajectories/ (D112)."""
    traj = repo / ".halo" / "trajectories"
    if not traj.is_dir():
        return 0
    try:
        return sum(
            1
            for p in traj.iterdir()
            if p.is_file() and p.suffix == ".json" and p.name.upper().startswith("GT-")
        )
    except OSError:
        return 0


def _latest_trajectory_id(repo: Path) -> str | None:
    """Max numeric GT-### id under .halo/trajectories/ (D116); null when empty/missing."""
    traj = repo / ".halo" / "trajectories"
    if not traj.is_dir():
        return None
    best_n = -1
    best_id: str | None = None
    try:
        for p in traj.iterdir():
            if not p.is_file() or p.suffix != ".json":
                continue
            m = re.match(r"^GT-(\d+)$", p.stem, re.I)
            if not m:
                continue
            n = int(m.group(1))
            if n > best_n:
                best_n = n
                # Prefer payload id when present and well-formed
                try:
                    payload = json.loads(p.read_text(encoding="utf-8"))
                    pid = payload.get("id") if isinstance(payload, dict) else None
                    if isinstance(pid, str) and re.match(r"^GT-\d+$", pid, re.I):
                        best_id = pid
                    else:
                        best_id = p.stem
                except (OSError, json.JSONDecodeError):
                    best_id = p.stem
    except OSError:
        return None
    return best_id


def summary(repo: Path, *, compound: bool = True) -> dict[str, Any]:
    """Pass/fail counts. Optionally auto-seed compounding batch when all_pass (D030)."""
    if compound:
        try:
            maybe_compound_seed(repo)
        except Exception:  # noqa: BLE001
            pass
    data = load_list(repo)
    feats = data.get("features") or []
    total = len(feats)
    passed = sum(1 for f in feats if f.get("passes"))
    pending = [f for f in feats if not f.get("passes")]
    nxt = _summary_next(pending[0]) if pending else None
    scores_count = _scores_count(repo)
    trajectories_count = _trajectories_count(repo)
    return {
        "total": total,
        "passed": passed,
        "remaining": total - passed,
        "all_pass": total > 0 and passed == total,
        "next": nxt,
        "scores_count": scores_count,
        "trajectories_count": trajectories_count,
        "scores_trajectories_match": scores_count == trajectories_count,
        "latest_score_id": _latest_score_id(repo),
        "latest_trajectory_id": _latest_trajectory_id(repo),
        "features": feats,
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_features")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sync", help="rebuild feature-list from STORIES.md / intake")
    s.add_argument("--repo", default=".")
    s.set_defaults(func=lambda a: print(json.dumps(sync_from_stories(Path(a.repo)), indent=2)))

    g = sub.add_parser("summary", help="pass/fail counts")
    g.add_argument("--repo", default=".")
    g.set_defaults(func=lambda a: print(json.dumps(summary(Path(a.repo)), indent=2)))

    m = sub.add_parser("pass", help="mark feature passes=true (requires GREEN evidence)")
    m.add_argument("--repo", default=".")
    m.add_argument("--id", required=True)
    m.add_argument("--note", default="")
    m.add_argument("--evidence", default=None, help="path to GREEN evidence file")
    m.add_argument(
        "--force",
        action="store_true",
        help="skip evidence gate (human override only)",
    )
    m.set_defaults(
        func=lambda a: print(
            json.dumps(
                set_pass(
                    Path(a.repo),
                    a.id,
                    True,
                    a.note,
                    evidence=a.evidence,
                    force=a.force,
                ),
                indent=2,
            )
        )
    )

    f = sub.add_parser("fail", help="mark feature passes=false")
    f.add_argument("--repo", default=".")
    f.add_argument("--id", required=True)
    f.set_defaults(func=lambda a: print(json.dumps(set_pass(Path(a.repo), a.id, False), indent=2)))

    a = sub.add_parser("append", help="append features from JSON file or stdin")
    a.add_argument("--repo", default=".")
    a.add_argument("--file", default=None, help="JSON list or {features:[…]}")
    def _append(args: argparse.Namespace) -> None:
        raw = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
        obj = json.loads(raw)
        feats = obj if isinstance(obj, list) else obj.get("features") or []
        print(json.dumps(append_features(Path(args.repo), feats), indent=2))

    a.set_defaults(func=_append)

    seed = sub.add_parser(
        "seed",
        help="compounding: if all_pass, append next D-batch (once/UTC day)",
    )
    seed.add_argument("--repo", default=".")
    seed.add_argument("--force", action="store_true", help="allow same-day reseed")
    seed.add_argument("--count", type=int, default=3)
    seed.set_defaults(
        func=lambda a: print(
            json.dumps(
                maybe_seed_compounding_batch(Path(a.repo), force=a.force, count=a.count),
                indent=2,
            )
        )
    )

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
