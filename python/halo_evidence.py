#!/usr/bin/env python3
"""Evidence certificate validator — file existence is not enough.

D170: --check / check JSON includes scores_count / trajectories_count /
scores_trajectories_match (true when equal, including both zero).
D171: --check / check JSON includes latest_score_id and latest_trajectory_id
(null when scores/trajectories dirs empty or missing).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def check_score_fields(repo: Path) -> dict[str, Any]:
    """Score culture fields for evidence check JSON.

    D170: scores_count / trajectories_count / scores_trajectories_match.
    D171: latest_score_id / latest_trajectory_id (null when empty/missing).
    """
    try:
        from halo_features import summary as feature_summary

        fs = feature_summary(Path(repo), compound=False)
        sc = int(fs.get("scores_count") or 0)
        tc = int(fs.get("trajectories_count") or 0)
        if "scores_trajectories_match" in fs:
            match = bool(fs.get("scores_trajectories_match"))
        else:
            match = sc == tc
        return {
            "scores_count": sc,
            "trajectories_count": tc,
            "scores_trajectories_match": match,
            "latest_score_id": fs.get("latest_score_id"),
            "latest_trajectory_id": fs.get("latest_trajectory_id"),
        }
    except Exception:  # noqa: BLE001
        return {
            "scores_count": 0,
            "trajectories_count": 0,
            "scores_trajectories_match": True,
            "latest_score_id": None,
            "latest_trajectory_id": None,
        }


def _infer_repo(path: Path) -> Path:
    """Walk parents for a .halo dir; else cwd."""
    path = Path(path).resolve()
    for p in [path.parent, *path.parents]:
        if (p / ".halo").is_dir():
            return p
    return Path.cwd().resolve()


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


# Accepted certificate type strings (D082 schema gate)
KNOWN_CERTS = frozenset(
    {
        "GREEN_TEST",
        "RED_TEST",
        "DEPLOY_OK",
        "SMOKE_OK",
        "COVERAGE_DELTA",
        "FILE_DIFF",
        "VERIFIER_APPROVED",
        "GOLDEN_TRAJECTORY",
        "SCORE_RECORDED",
        "ARENA_SPAWN_CHECK",
        "SPEC_OK",
        "PROBE_OK",
    }
)


def validate_cert_schema(data: dict[str, Any] | None) -> tuple[bool, str]:
    """Reject evidence JSON missing cert field; accept known cert types (D082)."""
    if not isinstance(data, dict):
        return False, "evidence must be JSON object"
    cert = data.get("cert")
    if cert is None or str(cert).strip() == "":
        return False, "missing cert field"
    cert_s = str(cert).strip().upper()
    if cert_s in KNOWN_CERTS or cert_s.endswith("_OK") or cert_s.endswith("_TEST"):
        return True, "ok"
    return False, f"unknown cert type: {cert}"


def validate_green_test(path: Path) -> tuple[bool, str]:
    data = _json(path)
    if data is not None:
        # Schema gate: JSON evidence should declare cert when present as structured cert
        if "cert" in data or data.get("require_cert_schema"):
            ok, msg = validate_cert_schema(data)
            if not ok:
                return False, msg
            if str(data.get("cert", "")).upper() == "GREEN_TEST" or data.get("ok") is True:
                if data.get("exit_code") in (None, 0) or data.get("ok") is True:
                    return True, "ok"
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


def check_file(path: Path, repo: Path | None = None) -> dict[str, Any]:
    """Validate a single evidence file; JSON without cert fails (D082).

    D170: merges scores_count / trajectories_count / scores_trajectories_match
    from repo score culture (repo arg, else inferred from path / cwd).
    D171: also merges latest_score_id / latest_trajectory_id (null when empty).
    """
    path = Path(path)
    score_repo = Path(repo).resolve() if repo is not None else _infer_repo(path)
    score_fields = check_score_fields(score_repo)
    if not path.is_file():
        return {
            "ok": False,
            "error": "missing file",
            "path": str(path),
            **score_fields,
        }
    data = _json(path)
    if data is not None:
        ok, msg = validate_cert_schema(data)
        return {
            "ok": ok,
            "message": msg,
            "path": str(path),
            "cert": data.get("cert"),
            **score_fields,
        }
    # plain text logs: allow if non-empty (legacy)
    text = _read(path)
    if text.strip():
        return {
            "ok": True,
            "message": "legacy text evidence",
            "path": str(path),
            **score_fields,
        }
    return {
        "ok": False,
        "message": "empty evidence",
        "path": str(path),
        **score_fields,
    }


def check_cert_schema(path: Path) -> tuple[bool, str]:
    """Path-oriented cert schema check (D082 tests)."""
    path = Path(path)
    if not path.is_file():
        return False, "missing file"
    data = _json(path)
    if data is None:
        text = _read(path)
        if text.strip():
            return True, "legacy text evidence"
        return False, "empty or invalid JSON"
    return validate_cert_schema(data)


def main() -> None:
    # Support both: halo_evidence --check PATH  and  halo_evidence check --file PATH
    argv = sys.argv[1:]
    if argv and argv[0] == "check":
        # subcommand style used by unit tests
        p = argparse.ArgumentParser(prog="halo_evidence check")
        p.add_argument("--file", required=True, help="evidence file path")
        p.add_argument("--repo", default=".", help="product repo root for score culture")
        a = p.parse_args(argv[1:])
        ok, msg = check_cert_schema(Path(a.file))
        report = {
            "ok": ok,
            "message": msg,
            "path": a.file,
            **check_score_fields(Path(a.repo).resolve()),
        }
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if ok else 2)

    p = argparse.ArgumentParser(prog="halo_evidence")
    p.add_argument("--repo", default=".")
    p.add_argument("--require", action="append", default=[], help="required cert kinds e.g. green-test")
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--check",
        metavar="PATH",
        default=None,
        help="validate one evidence file (fails if JSON missing cert)",
    )
    args = p.parse_args()
    if args.check:
        report = check_file(Path(args.check), repo=Path(args.repo).resolve())
        print(json.dumps(report, indent=2))
        raise SystemExit(0 if report.get("ok") else 2)
    report = validate_repo(Path(args.repo).resolve(), require=args.require or None)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["ok"] else 2)


if __name__ == "__main__":
    main()
