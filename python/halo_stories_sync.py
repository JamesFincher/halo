#!/usr/bin/env python3
"""Sync STORIES.md status lines from feature-list.json passes."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def sync(repo: Path) -> dict:
    fl = repo / ".halo" / "feature-list.json"
    stories = repo / ".halo" / "spec" / "STORIES.md"
    if not fl.exists():
        return {"ok": False, "error": "no feature-list"}
    feats = {f["id"]: f for f in json.loads(fl.read_text()).get("features") or [] if f.get("id")}
    if not stories.exists():
        # generate minimal STORIES from feature-list
        lines = ["# Stories\n", "> Synced from feature-list.json\n"]
        for fid, f in feats.items():
            st = "deployed" if f.get("passes") else "pending"
            lines.append(f"\n### {fid} — {f.get('description','')}\n")
            lines.append(f"- **Status**: {st}\n")
            for step in f.get("steps") or []:
                lines.append(f"- [ ] {step}\n")
        stories.parent.mkdir(parents=True, exist_ok=True)
        stories.write_text("".join(lines), encoding="utf-8")
        return {"ok": True, "written": "created", "count": len(feats)}
    text = stories.read_text(encoding="utf-8")
    # update Status lines under ### Sxxx headers
    parts = re.split(r"(?=^###\s+S\d+)", text, flags=re.M)
    out = []
    updated = 0
    for part in parts:
        m = re.match(r"^###\s+(S\d+)", part)
        if not m:
            out.append(part)
            continue
        fid = m.group(1)
        f = feats.get(fid)
        if not f:
            out.append(part)
            continue
        st = "deployed" if f.get("passes") else "pending"
        if re.search(r"\*\*Status\*\*:", part):
            part2 = re.sub(r"(\*\*Status\*\*:\s*)\w+", r"\1" + st, part, count=1)
        else:
            # insert after header line
            lines = part.splitlines(True)
            lines.insert(1, f"- **Status**: {st}\n")
            part2 = "".join(lines)
        if part2 != part:
            updated += 1
        out.append(part2)
    stories.write_text("".join(out), encoding="utf-8")
    return {"ok": True, "updated": updated, "features": len(feats)}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", default=".")
    args = p.parse_args()
    r = sync(Path(args.repo))
    print(json.dumps(r, indent=2))
    raise SystemExit(0 if r.get("ok") else 1)
if __name__ == "__main__":
    main()
