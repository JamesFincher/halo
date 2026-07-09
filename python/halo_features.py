#!/usr/bin/env python3
"""Machine-readable feature list (Anthropic-style passes: bool).

Source of truth for "is the product done?" — harder to corrupt than markdown-only STORIES.
"""

from __future__ import annotations

import argparse
import json
import re
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


def set_pass(
    repo: Path,
    feature_id: str,
    passes: bool,
    note: str = "",
    *,
    evidence: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Mark feature pass/fail. Pass requires evidence unless --force (Anthropic premature-done gate)."""
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
                f["evidence"] = str(ev_path.relative_to(repo) if ev_path.is_relative_to(repo) else ev_path)
            f["passes"] = passes
            f["verified_at"] = utc_now() if passes else None
            if note:
                f["note"] = note
            if not passes:
                f.pop("evidence", None)
            found = True
            break
    if not found:
        raise SystemExit(f"unknown feature id: {feature_id}")
    save_list(repo, data)
    return data


def summary(repo: Path) -> dict[str, Any]:
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

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
