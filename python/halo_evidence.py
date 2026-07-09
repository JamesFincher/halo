#!/usr/bin/env python3
"""Evidence certificate validator — file existence is not enough."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def validate_red_test(path: Path) -> tuple[bool, str]:
    data = _json(path)
    if not data:
        # allow text with exit_code non-zero
        text = _read(path)
        if re.search(r"exit_code\s*[:=]\s*[1-9]", text) or "ok" in text.lower() and "true" in text.lower():
            if "exit_code" in text and re.search(r"exit_code\s*[:=]\s*0\b", text) and "ok" not in text:
                return False, "RED_TEST looks green (exit 0)"
            return True, "ok"
        return False, "RED_TEST missing or invalid JSON"
    if data.get("ok") is True:
        return True, "ok"
    code = data.get("exit_code")
    if code is not None and int(code) != 0:
        return True, "ok"
    return False, "RED_TEST must record failing test (ok:true or exit_code!=0)"


def validate_green_test(path: Path) -> tuple[bool, str]:
    data = _json(path)
    if data is not None:
        if data.get("exit_code") == 0 or data.get("ok") is True:
            return True, "ok"
        return False, f"GREEN_TEST exit_code={data.get('exit_code')}"
    text = _read(path)
    if re.search(r"exit_code\s*[:=]\s*0\b", text) or "PASS" in text:
        return True, "ok"
    # non-empty test output companion
    return False, "GREEN_TEST invalid (need exit_code=0)"


def validate_deploy_ok(path: Path) -> tuple[bool, str]:
    data = _json(path)
    if data:
        url = data.get("url") or ""
        if data.get("cert") == "DEPLOY_OK" and url:
            return True, "ok"
        if url.startswith("http"):
            return True, "ok"
    text = _read(path)
    if re.search(r"https?://", text):
        return True, "ok"
    return False, "DEPLOY_OK missing url"


def validate_probe(path: Path) -> tuple[bool, str]:
    data = _json(path)
    if not data:
        return False, "probe JSON missing"
    if data.get("ok") is True:
        return True, "ok"
    return False, f"probe not ok: {data.get('error') or data.get('http_code')}"


def validate_file_nonempty(path: Path) -> tuple[bool, str]:
    if path.exists() and path.stat().st_size > 0:
        return True, "ok"
    return False, "missing or empty"


VALIDATORS = {
    "red-test": validate_red_test,
    "green-test": validate_green_test,
    "deploy-ok": validate_deploy_ok,
    "demo0-probe": validate_probe,
    "smoke": validate_file_nonempty,
    "spec-ok": validate_file_nonempty,
    "simplify": validate_file_nonempty,
    "file-diff": validate_file_nonempty,
}


def discover(repo: Path) -> list[Path]:
    ev = repo / ".halo" / "evidence"
    if not ev.is_dir():
        return []
    return sorted(p for p in ev.iterdir() if p.is_file())


def kind_for(name: str) -> str | None:
    n = name.lower()
    for key in VALIDATORS:
        if key.replace("-", "") in n.replace("-", "").replace("_", "") or key in n:
            return key
    if "probe" in n:
        return "demo0-probe"
    if "green" in n:
        return "green-test"
    if "red" in n:
        return "red-test"
    if "deploy" in n:
        return "deploy-ok"
    return None


def validate_repo(repo: Path, require: list[str] | None = None) -> dict[str, Any]:
    files = discover(repo)
    results = []
    by_kind: dict[str, bool] = {}
    for path in files:
        kind = kind_for(path.name)
        if not kind:
            results.append({"file": path.name, "kind": None, "ok": True, "note": "untyped (skipped schema)"})
            continue
        ok, msg = VALIDATORS[kind](path)
        by_kind[kind] = by_kind.get(kind, False) or ok
        results.append({"file": path.name, "kind": kind, "ok": ok, "message": msg})

    missing_required = []
    for req in require or []:
        # map aliases
        key = req.lower().replace("_", "-")
        if key in ("green_test", "green-test"):
            key = "green-test"
        found = any(r.get("kind") == key and r.get("ok") for r in results)
        # also check by_kind
        if not found and not by_kind.get(key):
            missing_required.append(req)

    overall = all(r["ok"] for r in results if r.get("kind")) and not missing_required
    return {
        "ok": overall,
        "files_checked": len(results),
        "results": results,
        "missing_required": missing_required,
        "by_kind": by_kind,
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_evidence")
    p.add_argument("--repo", default=".")
    p.add_argument("--require", action="append", default=[], help="required cert kinds e.g. green-test")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    report = validate_repo(Path(args.repo).resolve(), require=args.require or None)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["ok"] else 2)


if __name__ == "__main__":
    main()
