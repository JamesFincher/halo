"""Existing codebase: wire Halo surface + generic health if possible."""

from __future__ import annotations

from pathlib import Path

from scaffold.common import write_text


def scaffold(repo: Path, product_name: str = "Product") -> dict:
    created: list[str] = []
    health_file = repo / "halo-health.json"
    if write_text(health_file, '{\n  "ok": true,\n  "service": "halo-demo0"\n}\n'):
        created.append("halo-health.json")

    # static file server via python for demo0
    return {
        "profile": "existing",
        "mode": "existing",
        "created": created,
        "health_path": "/halo-health.json",
        "dev_cmd": ["python3", "-m", "http.server", "8899", "--bind", "127.0.0.1"],
        "dev_url": "http://127.0.0.1:8899/halo-health.json",
        "install_cmd": None,
        "note": "Existing project — only Halo health marker added. Prefer nextjs/fastapi profile if greenfield.",
    }
