#!/usr/bin/env python3
"""Generate .halo/milestones/N-slug/prompt.md + index.json from intake or MILESTONES.md."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def load_state(repo: Path) -> dict[str, Any]:
    p = repo / ".halo" / "state.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return s[:48] or "milestone"


def milestones_from_intake(intake: dict[str, Any]) -> list[dict[str, Any]]:
    raw = intake.get("milestones") or []
    out = []
    for i, m in enumerate(raw, start=1):
        if not isinstance(m, dict):
            continue
        n = int(m.get("n") or i)
        name = str(m.get("name") or f"Milestone {n}")
        slug = str(m.get("slug") or slugify(name))
        out.append(
            {
                "n": n,
                "slug": slug,
                "name": name,
                "scope": m.get("scope") or "",
                "done_when": m.get("done_when_draft") or m.get("done_when") or "User-visible value delivered; tests green.",
                "depends_on": m.get("depends_on") or [],
            }
        )
    return out


def milestones_from_md(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    # ## M1 — Name  or  ## Milestone 1 — Name
    blocks = re.split(r"(?m)^##\s+", text)
    out = []
    n = 0
    for block in blocks[1:]:
        first, _, rest = block.partition("\n")
        m = re.match(r"M?(\d+)\s*[—\-–:]\s*(.+)", first.strip())
        if not m:
            m2 = re.match(r"Milestone\s+(\d+)\s*[—\-–:]\s*(.+)", first.strip(), re.I)
            if not m2:
                continue
            m = m2
        n = int(m.group(1))
        name = m.group(2).strip()
        scope = ""
        done = ""
        for line in rest.splitlines():
            if re.match(r"-\s*(?:\*\*)?Scope(?:\*\*)?\s*:", line, re.I):
                scope = line.split(":", 1)[-1].strip()
            if re.match(r"-\s*(?:\*\*)?Done when(?:\*\*)?\s*:", line, re.I):
                done = line.split(":", 1)[-1].strip()
        out.append(
            {
                "n": n,
                "slug": slugify(name),
                "name": name,
                "scope": scope,
                "done_when": done or "Done when criteria met in browser/API.",
                "depends_on": [],
            }
        )
    return out


def default_milestones() -> list[dict[str, Any]]:
    return [
        {
            "n": 1,
            "slug": "foundation",
            "name": "Foundation",
            "scope": "Core app shell, health, auth stub if required, first user path.",
            "done_when": "User can open the app and complete the primary empty-state path.",
            "depends_on": [],
        },
        {
            "n": 2,
            "slug": "core-value",
            "name": "Core value",
            "scope": "Main feature from PRD in-scope list.",
            "done_when": "Primary user job works end-to-end with tests.",
            "depends_on": [1],
        },
        {
            "n": 3,
            "slug": "integrations",
            "name": "Integrations",
            "scope": "External services from INTEGRATIONS.md wired safely.",
            "done_when": "Integrations work in preview with env vars; probe green.",
            "depends_on": [2],
        },
    ]


def render_prompt(template: str, m: dict[str, Any]) -> str:
    return (
        template.replace("{N}", str(m["n"]))
        .replace("{NAME}", m["name"])
        .replace("{SCOPE}", m.get("scope") or "(see PRD)")
        .replace("{DONE_WHEN}", m.get("done_when") or "Criteria met.")
    )


def write_milestones(repo: Path, halo_system: Path | None = None) -> dict[str, Any]:
    repo = repo.resolve()
    state = load_state(repo)
    intake = state.get("intake") or {}
    ms = milestones_from_intake(intake)
    if not ms:
        ms = milestones_from_md(repo / ".halo" / "spec" / "MILESTONES.md")
    if not ms:
        ms = default_milestones()

    tpl_path = None
    if halo_system:
        tpl_path = halo_system / "templates" / "milestones" / "prompt.md"
    if not tpl_path or not tpl_path.exists():
        # sibling relative
        here = Path(__file__).resolve().parent.parent
        tpl_path = here / "templates" / "milestones" / "prompt.md"
    template = tpl_path.read_text(encoding="utf-8") if tpl_path.exists() else (
        "# Milestone {N} — {NAME}\n\nScope: {SCOPE}\n\nDone when: {DONE_WHEN}\n"
    )

    base = repo / ".halo" / "milestones"
    base.mkdir(parents=True, exist_ok=True)
    written = []
    index = {"milestones": [], "generated_from": "intake" if milestones_from_intake(intake) else "default"}

    for m in sorted(ms, key=lambda x: x["n"]):
        folder = base / f"{m['n']}-{m['slug']}"
        folder.mkdir(parents=True, exist_ok=True)
        prompt = folder / "prompt.md"
        prompt.write_text(render_prompt(template, m), encoding="utf-8")
        written.append(str(prompt.relative_to(repo)))
        index["milestones"].append(
            {
                "n": m["n"],
                "slug": m["slug"],
                "name": m["name"],
                "path": str(folder.relative_to(repo)),
                "prompt": str(prompt.relative_to(repo)),
                "status": "pending",
            }
        )

    idx_path = base / "index.json"
    idx_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    written.append(str(idx_path.relative_to(repo)))
    return {"ok": True, "count": len(ms), "files": written, "index": index}


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_milestones")
    p.add_argument("--repo", default=".")
    p.add_argument("--halo-system", default=None, help="path to Halo system repo")
    args = p.parse_args()
    hs = Path(args.halo_system).resolve() if args.halo_system else Path(__file__).resolve().parent.parent
    result = write_milestones(Path(args.repo), hs)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
