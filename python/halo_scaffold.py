#!/usr/bin/env python3
"""Scaffold product skeleton + milestones + optional Demo 0 with live probe."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# package path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from halo_milestones import write_milestones  # noqa: E402
from halo_probe import probe  # noqa: E402
from scaffold import existing as existing_mod  # noqa: E402
from scaffold import fastapi_app  # noqa: E402
from scaffold import nextjs_saas  # noqa: E402
from scaffold.common import (  # noqa: E402
    copy_halo_templates,
    load_state,
    save_state,
    utc_now,
    write_baton,
    write_evidence,
)


def detect_profile(repo: Path, state: dict[str, Any], explicit: str | None) -> str:
    if explicit:
        return explicit
    intake = state.get("intake") or {}
    stack = intake.get("stack") or {}
    blob = json.dumps(stack).lower() if stack else ""
    if (repo / "package.json").exists() or "next" in blob or "web-saas" in blob or "vite" in blob:
        if (repo / "package.json").exists() and "next" not in blob and not (repo / "app").exists():
            # generic node existing
            if (repo / "app").exists() or "next" in (repo / "package.json").read_text(encoding="utf-8"):
                return "nextjs-saas"
            return "existing"
        return "nextjs-saas"
    if (repo / "pyproject.toml").exists() or (repo / "requirements.txt").exists() or "fastapi" in blob or "api-ui" in blob:
        return "fastapi"
    if any((repo / x).exists() for x in ("package.json", "src", "lib", "app")):
        return "existing"
    # default greenfield
    return "nextjs-saas"


def run_install(cmd: list[str] | None, repo: Path, timeout: int = 600) -> dict[str, Any]:
    if not cmd:
        return {"ok": True, "skipped": True}
    try:
        r = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, timeout=timeout)
        return {
            "ok": r.returncode == 0,
            "cmd": cmd,
            "returncode": r.returncode,
            "stderr_tail": (r.stderr or "")[-2000:],
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e), "cmd": cmd}


def demo0_local(repo: Path, meta: dict[str, Any], timeout_boot: float = 45.0) -> dict[str, Any]:
    """Start dev server, probe health URL, stop server. Never report URL if probe fails."""
    url = meta["dev_url"]
    cmd = meta["dev_cmd"]
    proc = None
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=repo,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        deadline = time.time() + timeout_boot
        last = {}
        while time.time() < deadline:
            last = probe(url, timeout=2.0, expect_substring=None)
            if last.get("ok"):
                break
            if proc.poll() is not None:
                return {
                    "ok": False,
                    "url": url,
                    "error": "dev process exited early",
                    "probe": last,
                    "returncode": proc.returncode,
                }
            time.sleep(0.5)
        result = {
            "ok": bool(last.get("ok")),
            "url": url if last.get("ok") else None,
            "probe": last,
            "dev_cmd": cmd,
            "checked_at": utc_now(),
        }
        if last.get("ok"):
            write_evidence(repo, "demo0-probe.json", result)
            write_evidence(
                repo,
                "deploy-ok-demo0.json",
                {"cert": "DEPLOY_OK", "url": url, "kind": "local-demo0", "at": utc_now()},
            )
        return result
    finally:
        if proc and proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError, OSError):
                proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError, OSError):
                    proc.kill()


def scaffold(
    repo: Path,
    halo_system: Path,
    profile: str | None,
    demo0: str,
    skip_ready_check: bool,
    force: bool,
) -> dict[str, Any]:
    repo = repo.resolve()
    state = load_state(repo)
    if not state and not force:
        raise SystemExit("missing .halo/state.json — run halo init / bootstrap first")

    verdict = state.get("readiness_verdict")
    if not skip_ready_check and verdict not in ("GO", "DEGRADED", None):
        # None allowed only with force for smoke tests; prefer check
        if verdict == "NO_GO":
            raise SystemExit("readiness NO_GO — fill .env and re-run halo ready (or --skip-ready-check)")

    if state.get("spec_status") not in ("locked", "ready_for_review", "none", None) and not force:
        pass  # allow scaffold after readiness even if
    if state.get("spec_status") != "locked" and not force and not skip_ready_check:
        # soft warn in result
        pass

    prof = detect_profile(repo, state, profile)
    name = state.get("product_name") or (state.get("intake") or {}).get("product_name") or "Halo App"
    if isinstance(name, dict):
        name = name.get("name") or "Halo App"

    if prof == "nextjs-saas":
        meta = nextjs_saas.scaffold(repo, str(name))
    elif prof == "fastapi":
        meta = fastapi_app.scaffold(repo, str(name))
    else:
        meta = existing_mod.scaffold(repo, str(name))

    tpl_written = copy_halo_templates(repo, halo_system)
    ms = write_milestones(repo, halo_system)
    install = run_install(meta.get("install_cmd"), repo)

    demo_result: dict[str, Any] | None = None
    # After venv install, refresh dev_cmd to use .venv python if present
    vpy = repo / ".venv" / "bin" / "python"
    if vpy.exists() and meta.get("profile") == "fastapi":
        meta["dev_cmd"] = [
            str(vpy),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ]

    if demo0 == "local":
        if not install.get("ok") and meta.get("install_cmd"):
            demo_result = {"ok": False, "error": "install failed; skip demo0", "install": install}
        else:
            demo_result = demo0_local(repo, meta)
    elif demo0 == "skip":
        demo_result = {"ok": True, "skipped": True}
    elif demo0 == "vercel":
        demo_result = {"ok": False, "error": "vercel demo0 not implemented in slice 2 — use local"}

    # state transition
    if demo0 == "skip" or (demo_result and demo_result.get("ok") and not demo_result.get("error")):
        if demo0 == "skip" or demo_result.get("skipped") or demo_result.get("ok"):
            state["phase"] = "build" if (demo0 == "skip" or demo_result.get("ok")) else "scaffold"
            if demo_result and demo_result.get("ok") and demo_result.get("url"):
                state["last_demo_url"] = demo_result["url"]
            state["scaffold_profile"] = prof
            save_state(repo, state)
            first = (ms.get("index") or {}).get("milestones") or []
            first_path = first[0]["prompt"] if first else ".halo/milestones/"
            write_baton(
                repo,
                [
                    f"Phase: {state.get('phase')}",
                    f"Profile: {prof}",
                    f"Next: open {first_path} and run halo-build cycle",
                    "Do not: share URLs without halo_probe PASS",
                    f"Demo0: {demo_result.get('url') if demo_result else 'skipped'}",
                ],
            )

    if demo_result and not demo_result.get("ok") and not demo_result.get("skipped"):
        state["phase"] = "scaffold"
        save_state(repo, state)
        write_baton(
            repo,
            [
                "Phase: scaffold",
                "Demo0 probe FAILED — fix server, re-run scaffold --demo0 local",
                "Do not: tell human deploy is live",
            ],
        )

    return {
        "ok": bool(demo0 == "skip" or (demo_result and (demo_result.get("ok") or demo_result.get("skipped")))),
        "profile": prof,
        "scaffold": meta,
        "templates": tpl_written,
        "milestones": {"count": ms.get("count"), "files": ms.get("files")},
        "install": install,
        "demo0": demo_result,
        "phase": load_state(repo).get("phase"),
    }


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_scaffold")
    p.add_argument("--repo", default=".")
    p.add_argument("--halo-system", default=None)
    p.add_argument("--profile", choices=["nextjs-saas", "fastapi", "existing", "auto"], default="auto")
    p.add_argument("--demo0", choices=["local", "skip", "vercel"], default="local")
    p.add_argument("--skip-ready-check", action="store_true")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    hs = Path(args.halo_system).resolve() if args.halo_system else Path(__file__).resolve().parent.parent
    profile = None if args.profile == "auto" else args.profile
    result = scaffold(
        Path(args.repo),
        hs,
        profile,
        args.demo0,
        skip_ready_check=args.skip_ready_check,
        force=args.force,
    )
    print(json.dumps(result, indent=2))
    # exit 1 if demo0 failed when requested
    if args.demo0 == "local" and result.get("demo0") and not result["demo0"].get("ok"):
        sys.exit(1)
    if not result.get("ok"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
