"""Shared scaffold helpers — stdlib only."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_text(path: Path, content: str, overwrite: bool = False) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return False
    path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
    return True


def merge_gitignore(repo: Path, lines: list[str]) -> None:
    path = repo / ".gitignore"
    existing = set()
    if path.exists():
        existing = {ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()}
    out = list(path.read_text(encoding="utf-8").splitlines()) if path.exists() else []
    if out and out[-1] != "":
        out.append("")
    out.append("# Halo scaffold")
    for ln in lines:
        if ln not in existing:
            out.append(ln)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def copy_halo_templates(repo: Path, halo_system: Path) -> list[str]:
    written = []
    tpl = halo_system / "templates" / "project"
    for name in ("AGENTS.md", "HALO.md"):
        src = tpl / name
        dst = repo / name
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
            written.append(name)
    return written


def load_state(repo: Path) -> dict[str, Any]:
    p = repo / ".halo" / "state.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def save_state(repo: Path, data: dict[str, Any]) -> None:
    data["updated_at"] = utc_now()
    p = repo / ".halo" / "state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_baton(repo: Path, lines: list[str]) -> None:
    body = "# Baton\n" + "\n".join(f"- {ln}" if not ln.startswith("-") else ln for ln in lines) + "\n"
    (repo / ".halo" / "baton.md").write_text(body, encoding="utf-8")


def write_evidence(repo: Path, name: str, payload: dict[str, Any]) -> Path:
    ev = repo / ".halo" / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    path = ev / name
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


NEXT_GITIGNORE = [
    "node_modules/",
    ".next/",
    "out/",
    ".env",
    ".env.local",
    ".env*.local",
    "npm-debug.log*",
    ".DS_Store",
    "coverage/",
    ".vercel",
]

FASTAPI_GITIGNORE = [
    ".venv/",
    "venv/",
    "__pycache__/",
    "*.py[cod]",
    ".env",
    ".env.local",
    ".pytest_cache/",
    ".mypy_cache/",
    "dist/",
    "*.egg-info/",
    ".DS_Store",
]
