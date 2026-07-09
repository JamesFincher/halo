#!/usr/bin/env python3
"""Make Halo skills visible inside a product TARGET for Grok discovery."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path


def link_skills(halo_sys: Path, target: Path, mode: str = "symlink") -> dict:
    halo_sys = halo_sys.resolve()
    target = target.resolve()
    src = halo_sys / ".grok" / "skills"
    dest_root = target / ".grok" / "skills"
    if not src.is_dir():
        return {"ok": False, "error": f"no skills at {src}"}

    # Dogfood: World A == World B — skills already live here. Never rmtree them.
    if src.resolve() == dest_root.resolve() or halo_sys == target:
        return {
            "ok": True,
            "mode": "dogfood-skip",
            "linked": [],
            "dest": str(dest_root),
            "note": "TARGET is Halo system; skills already present — no link",
        }

    dest_root.mkdir(parents=True, exist_ok=True)
    linked = []

    for skill_dir in sorted(src.iterdir()):
        if not skill_dir.is_dir():
            continue
        if not (skill_dir / "SKILL.md").exists() and not (skill_dir / "skill.md").exists():
            continue
        dest = dest_root / skill_dir.name
        # Never delete a real skill directory that is the factory source
        try:
            if dest.resolve() == skill_dir.resolve() and not dest.is_symlink():
                linked.append(skill_dir.name)
                continue
        except OSError:
            pass
        if dest.exists() or dest.is_symlink():
            if dest.is_symlink():
                dest.unlink()
            elif dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
        if mode == "symlink":
            dest.symlink_to(skill_dir.resolve())
        else:
            shutil.copytree(skill_dir, dest)
        linked.append(skill_dir.name)

    # minimal product AGENTS pointer
    agents = target / "AGENTS.md"
    marker = "<!-- halo-go-self-prompt -->"
    note = (
        f"\n{marker}\n"
        "## Halo autonomous\n\n"
        "If `.halo/state.json` has `autonomous: true`, load skill **halo-go** and continue without asking.\n"
        "Read `.halo/NEXT_PROMPT.md` when present.\n"
        f"{marker}\n"
    )
    if agents.exists():
        text = agents.read_text(encoding="utf-8")
        if marker not in text:
            agents.write_text(text.rstrip() + "\n" + note, encoding="utf-8")
    else:
        agents.write_text("# AGENTS.md\n" + note, encoding="utf-8")

    return {"ok": True, "mode": mode, "linked": linked, "dest": str(dest_root)}


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_link_skills")
    p.add_argument("--halo-system", default=os.environ.get("HALO_SYSTEM"))
    p.add_argument("--repo", default=".")
    p.add_argument("--mode", choices=["symlink", "copy"], default="symlink")
    args = p.parse_args()
    hs = Path(args.halo_system or Path(__file__).resolve().parent.parent).resolve()
    result = link_skills(hs, Path(args.repo).resolve(), mode=args.mode)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
