"""FastAPI skeleton scaffolder."""

from __future__ import annotations

from pathlib import Path

from scaffold.common import FASTAPI_GITIGNORE, merge_gitignore, write_text


def scaffold(repo: Path, product_name: str = "Halo API") -> dict:
    created: list[str] = []
    main = repo / "app" / "main.py"

    venv_python = repo / ".venv" / "bin" / "python"
    venv_uvicorn = [
        str(venv_python),
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8765",
    ]
    # install: create venv then pip (PEP 668 safe)
    install_cmd = [
        "bash",
        "-lc",
        "python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt",
    ]

    if main.exists():
        merge_gitignore(repo, FASTAPI_GITIGNORE)
        return {
            "profile": "fastapi",
            "mode": "existing",
            "created": created,
            "health_path": "/health",
            "dev_cmd": venv_uvicorn if venv_python.exists() else [
                "python3",
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8765",
            ],
            "dev_url": "http://127.0.0.1:8765/health",
            "install_cmd": install_cmd,
        }

    files = {
        "requirements.txt": "fastapi>=0.115.0\nuvicorn[standard]>=0.32.0\nhttpx>=0.27.0\npytest>=8.0.0\n",
        "app/__init__.py": "",
        "app/main.py": (
            '"""Scaffolded by Halo."""\n'
            "from fastapi import FastAPI\n\n"
            f'app = FastAPI(title={product_name!r}, version="0.1.0")\n\n'
            '@app.get("/")\ndef root():\n'
            f'    return {{"ok": True, "product": {product_name!r}, "service": "halo-demo0"}}\n\n'
            '@app.get("/health")\ndef health():\n'
            '    return {"ok": True, "service": "halo-demo0"}\n'
        ),
        "tests/test_health.py": (
            "from fastapi.testclient import TestClient\n"
            "from app.main import app\n\n"
            "client = TestClient(app)\n\n"
            "def test_health():\n"
            '    r = client.get("/health")\n'
            "    assert r.status_code == 200\n"
            '    assert r.json()["ok"] is True\n'
        ),
        "scripts/dev.sh": (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'cd "$(dirname "$0")/.."\n'
            "if [[ ! -d .venv ]]; then python3 -m venv .venv; .venv/bin/pip install -q -r requirements.txt; fi\n"
            "exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload\n"
        ),
        "README.md": (
            f"# {product_name}\n\nScaffolded by **Halo**.\n\n"
            "```bash\npython3 -m venv .venv\n.venv/bin/pip install -r requirements.txt\n"
            ".venv/bin/python -m uvicorn app.main:app --port 8765\n```\n"
        ),
        "pyproject.toml": (
            "[project]\n"
            f'name = "{product_name.lower().replace(" ", "-")[:64] or "halo-api"}"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.11"\n'
        ),
    }

    for rel, content in files.items():
        if write_text(repo / rel, content):
            created.append(rel)
    dev = repo / "scripts" / "dev.sh"
    if dev.exists():
        dev.chmod(dev.stat().st_mode | 0o111)

    merge_gitignore(repo, FASTAPI_GITIGNORE)
    return {
        "profile": "fastapi",
        "mode": "fresh",
        "created": created,
        "health_path": "/health",
        "dev_cmd": [
            str(repo / ".venv" / "bin" / "python"),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ],
        "dev_url": "http://127.0.0.1:8765/health",
        "install_cmd": install_cmd,
    }
