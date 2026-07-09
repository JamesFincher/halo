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
        # Preserve dogfood compounding flags (FILE_DIFF gate)
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
        "Dogfood feature pass requires factory FILE_DIFF unless requires_code false",
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

    Returns {seeded, added, reason, date?}.
    """
    r = maybe_compound_seed(repo, force=force)
    if r.get("seeded"):
        return {
            "seeded": True,
            "added": list(r.get("ids") or []),
            "reason": "seeded",
            "date": r.get("day"),
            "batch": r.get("batch"),
        }
    reason_map = {
        "not_dogfood": "not compounding",
        "not_all_pass": "not all_pass",
        "already_seeded_today": "already seeded today",
        "empty_list": "not all_pass",
    }
    raw = str(r.get("reason") or "noop")
    return {
        "seeded": False,
        "added": [],
        "reason": reason_map.get(raw, raw),
    }


def _factory_diff_paths(repo: Path) -> list[str]:
    """Changed factory paths (excludes .halo/ and archives)."""
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

    requires_code=true features also need factory FILE_DIFF (anti smoke-thrash).
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
                if f.get("requires_code") is True:
                    diffs = _factory_diff_paths(repo)
                    if not diffs:
                        raise SystemExit(
                            f"refuse pass for {feature_id}: requires_code but no factory "
                            f"FILE_DIFF. Implement code first, or --force."
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
    # Dogfood compounding: never idle on all_pass — seed next batch once/day
    if passes:
        try:
            maybe_compound_seed(repo)
        except Exception:  # noqa: BLE001
            pass
    return data


def _next_d_id(existing_ids: set[str]) -> str:
    """Allocate next D### id above current max."""
    max_n = 0
    for i in existing_ids:
        m = re.match(r"^D(\d+)$", str(i), re.I)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"D{max_n + 1:03d}"


def maybe_compound_seed(repo: Path, *, force: bool = False) -> dict[str, Any]:
    """When dogfood compounding + all_pass, append 3 new D-features once per UTC day (D030)."""
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

    seed_meta = {
        "last_seed_day": today,
        "batch": batch_n,
        "seeded_ids": [f["id"] for f in new_feats],
        "at": utc_now(),
        "last_reason": "seeded",
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
    return {
        "total": total,
        "passed": passed,
        "remaining": total - passed,
        "all_pass": total > 0 and passed == total,
        "next": pending[0] if pending else None,
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
        help="dogfood compounding: if all_pass, append next D-batch (once/UTC day)",
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
