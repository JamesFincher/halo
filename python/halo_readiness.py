#!/usr/bin/env python3
"""Lifecycle readiness gate — CLI presence, env presence, foresight inventory.

Never prints secret values. Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# sibling import when run as script or module
try:
    from halo_catalog import merge_integrations
except ImportError:  # pragma: no cover
    from python.halo_catalog import merge_integrations  # type: ignore


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE; never return values to logs — caller uses keys only for presence."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k:
            out[k] = v
    return out


def env_present(key: str, file_env: dict[str, str]) -> bool:
    val = file_env.get(key) or os.environ.get(key)
    if val is None:
        return False
    return bool(str(val).strip()) and not str(val).strip().startswith("<")


def cli_on_path(name: str) -> bool:
    return shutil.which(name) is not None


def run_cli_auth(cmd: str, timeout: float = 8.0) -> bool:
    """Best-effort auth check; exit 0 = ok. Never capture secrets into output."""
    try:
        r = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy(),
        )
        return r.returncode == 0
    except (subprocess.TimeoutExpired, OSError):
        return False


def check_item(item: dict[str, Any], file_env: dict[str, str]) -> dict[str, Any]:
    if item.get("optional_skip"):
        return {
            "id": item["id"],
            "ok": True,
            "blocking": False,
            "skipped": True,
            "skip_reason": item.get("skip_reason"),
            "provider": item.get("provider"),
            "purpose": item.get("purpose"),
            "env": item.get("credentials") or [],
            "env_missing": [],
            "cli_missing": [],
            "cli_auth_failed": [],
            "human_action": None,
        }

    creds = list(item.get("credentials") or [])
    # Auth: any one of clerk publishable variants counts if secret present
    env_missing = [c for c in creds if not env_present(c, file_env)]
    # Soften clerk: if CLERK_SECRET_KEY present and either publishable present, drop other publishable miss
    if item["id"] == "auth":
        if env_present("CLERK_SECRET_KEY", file_env) and (
            env_present("CLERK_PUBLISHABLE_KEY", file_env)
            or env_present("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", file_env)
        ):
            env_missing = [
                c
                for c in env_missing
                if c
                not in (
                    "CLERK_PUBLISHABLE_KEY",
                    "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY",
                    "CLERK_SECRET_KEY",
                )
            ]

    clis = list(item.get("cli") or [])
    cli_missing = [c for c in clis if not cli_on_path(c)]

    cli_auth_failed = []
    for auth_cmd in item.get("cli_auth") or []:
        # Only run auth check if CLI binary present
        bin_name = auth_cmd.split()[0]
        if cli_on_path(bin_name) and not run_cli_auth(auth_cmd):
            cli_auth_failed.append(auth_cmd)

    blocking = bool(item.get("blocking"))
    ok = not env_missing and not cli_missing and not cli_auth_failed

    # Non-blocking items with missing optional creds still ok=False but non-blocking
    human = None
    if not ok:
        parts = []
        if cli_missing:
            parts.append(f"install CLI: {', '.join(cli_missing)}")
        if cli_auth_failed:
            parts.append(f"auth: {', '.join(cli_auth_failed)}")
        if env_missing:
            parts.append(f"set env (names only): {', '.join(env_missing)}")
        human = item.get("human_action") or "; ".join(parts)

    return {
        "id": item["id"],
        "ok": ok,
        "blocking": blocking,
        "skipped": False,
        "provider": item.get("provider"),
        "purpose": item.get("purpose"),
        "env": creds,
        "env_missing": env_missing,
        "env_present_count": len(creds) - len(env_missing),
        "cli": clis,
        "cli_missing": cli_missing,
        "cli_auth_failed": cli_auth_failed,
        "human_action": human,
        "required_for_milestones": item.get("required_for_milestones") or [],
    }


def render_readiness_md(report: dict[str, Any]) -> str:
    lines = [
        "# Readiness",
        "",
        f"**Verdict:** `{report['verdict']}`  ",
        f"**Checked:** {report['checked_at']}",
        "",
        "Secrets never appear in this file — only key **names** and pass/fail.",
        "",
        "## Summary",
        "",
        f"- Blocking failures: **{report['blocking_failures']}**",
        f"- Non-blocking gaps: **{report['nonblocking_gaps']}**",
        f"- Skipped (stack N/A): **{report['skipped']}**",
        "",
        "## Checklist",
        "",
        "| ID | Provider | Blocking | OK | Missing env | Missing CLI | Action |",
        "|----|----------|----------|----|-------------|-------------|--------|",
    ]
    for it in report["items"]:
        if it.get("skipped"):
            lines.append(
                f"| {it['id']} | {it.get('provider','')} | no | skip | — | — | {it.get('skip_reason','')} |"
            )
            continue
        lines.append(
            f"| {it['id']} | {it.get('provider','')} | {'yes' if it['blocking'] else 'no'} | "
            f"{'yes' if it['ok'] else 'NO'} | "
            f"{', '.join(it.get('env_missing') or []) or '—'} | "
            f"{', '.join(it.get('cli_missing') or []) or '—'} | "
            f"{(it.get('human_action') or '—').replace('|', '/')} |"
        )
    lines.extend(
        [
            "",
            "## Human next steps",
            "",
        ]
    )
    actions = [it for it in report["items"] if not it.get("ok") and not it.get("skipped")]
    if not actions:
        lines.append("All checks green. Scaffold may proceed.")
    else:
        for it in actions:
            tag = "BLOCKING" if it["blocking"] else "optional"
            lines.append(f"1. **[{tag}] {it['id']}**: {it.get('human_action')}")
    lines.extend(
        [
            "",
            "## Env file",
            "",
            "Copy keys from `.env.example` into local `.env` (gitignored). "
            "Re-run readiness after filling.",
            "",
            "```bash",
            "python3 <HALO_SYSTEM>/python/halo_readiness.py --repo . --write",
            "```",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def render_env_example(items: list[dict[str, Any]]) -> str:
    keys: list[str] = []
    for it in items:
        if it.get("optional_skip"):
            continue
        for c in it.get("credentials") or []:
            if c not in keys:
                keys.append(c)
    lines = [
        "# Halo readiness — fill locally as .env (never commit)",
        "# Generated by halo_readiness.py",
        "",
    ]
    for k in keys:
        lines.append(f"{k}=")
    if not keys:
        lines.append("# (no credentials required yet)")
    return "\n".join(lines) + "\n"


def compute_verdict(items: list[dict[str, Any]], allow_degraded: bool) -> str:
    blocking_fail = [i for i in items if i.get("blocking") and not i.get("ok") and not i.get("skipped")]
    soft_fail = [i for i in items if not i.get("blocking") and not i.get("ok") and not i.get("skipped")]
    if not blocking_fail and not soft_fail:
        return "GO"
    if not blocking_fail and soft_fail:
        return "GO"  # optional gaps don't block
    if blocking_fail and allow_degraded:
        return "DEGRADED"
    return "NO_GO"


def check_spec_pack(repo: Path, spec_status: str | None, spec_pack_version: int = 0) -> dict[str, Any]:
    '''Verify core spec pack exists. Expanded pack is required only when the state says it was generated.'''
    spec = repo / ".halo" / "spec"
    required = [
        "PRD.md", "STACK.md", "DATA-MODEL.md", "STORIES.md", "MILESTONES.md", "READINESS.md",
    ]
    expanded = [
        "API.md", "USER-FLOWS.md", "ARCHITECTURE-DECISIONS.md", "SEQUENCE.md", "STATE.md",
        "SECURITY.md", "TEST-PLAN.md", "FRONTEND.md", "BACKEND.md", "MOBILE.md",
        "DEPLOYMENT.md", "RUNBOOK.md", "METRICS.md", "PROMPTS.md", "GLOSSARY.md",
        "RISKS.md", "PERSONAS.md", "SEED.md", "CHANGELOG.md", "CONTRIBUTING.md",
    ]
    missing = [f for f in required if not (spec / f).exists()]
    missing_expanded: list[str] = []
    if spec_pack_version >= 2:
        missing_expanded = [f for f in expanded if not (spec / f).exists()]
    locked = spec_status == "locked"
    blocking = locked and bool(missing)
    ok = not missing and not missing_expanded
    human = None
    if missing:
        human = f"run halo specs to generate {', '.join(missing)}"
    elif missing_expanded:
        human = f"regenerate spec pack with halo specs for {', '.join(missing_expanded)}"
    return {
        "id": "spec_pack",
        "ok": ok,
        "blocking": blocking,
        "skipped": False,
        "provider": "halo",
        "purpose": "spec documents exist",
        "env": [],
        "env_missing": [],
        "env_present_count": 0,
        "cli": [],
        "cli_missing": [],
        "cli_auth_failed": [],
        "human_action": human or "All expected spec files present.",
    }


def run(repo: Path, allow_degraded: bool, write: bool) -> dict[str, Any]:
    repo = repo.resolve()
    os.chdir(repo)
    state = load_json(repo / ".halo" / "state.json")
    intake = state.get("intake") or {}
    integrations = intake.get("integrations") or state.get("integrations") or []
    stack = intake.get("stack") or {}
    profile = ""
    if isinstance(stack, dict):
        profile = str(stack.get("profile") or stack.get("framework") or "")
    elif isinstance(stack, str):
        profile = stack

    merged = merge_integrations(integrations if isinstance(integrations, list) else [], profile)
    file_env = {}
    file_env.update(parse_env_file(repo / ".env"))
    file_env.update(parse_env_file(repo / ".env.local"))

    # git repo check: if no .git, mark git not ok
    checked = []
    for item in merged:
        result = check_item(item, file_env)
        if result["id"] == "git":
            if not (repo / ".git").exists():
                result["ok"] = False
                result["blocking"] = True
                result["human_action"] = "git init (or clone) this product repo"
            elif not cli_on_path("git"):
                result["ok"] = False
                result["cli_missing"] = ["git"]
                result["human_action"] = "Install git"
        checked.append(result)

    checked.append(check_spec_pack(repo, state.get("spec_status"), int(state.get("spec_pack_version") or 0)))

    verdict = compute_verdict(checked, allow_degraded=allow_degraded)
    blocking_failures = sum(1 for i in checked if i.get("blocking") and not i.get("ok") and not i.get("skipped"))
    nonblocking_gaps = sum(1 for i in checked if not i.get("blocking") and not i.get("ok") and not i.get("skipped"))
    skipped = sum(1 for i in checked if i.get("skipped"))

    report: dict[str, Any] = {
        "verdict": verdict,
        "checked_at": utc_now(),
        "repo": str(repo),
        "stack_profile": profile or None,
        "blocking_failures": blocking_failures,
        "nonblocking_gaps": nonblocking_gaps,
        "skipped": skipped,
        "allow_degraded": allow_degraded,
        "items": checked,
        "rules": {
            "live_probe_before_share": True,
            "never_log_secret_values": True,
        },
    }

    if write:
        halo = repo / ".halo"
        halo.mkdir(parents=True, exist_ok=True)
        (halo / "readiness.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        spec = halo / "spec"
        spec.mkdir(parents=True, exist_ok=True)
        (spec / "READINESS.md").write_text(render_readiness_md(report), encoding="utf-8")
        (repo / ".env.example").write_text(render_env_example(merged), encoding="utf-8")

        # update state if present
        state_path = halo / "state.json"
        if state_path.exists():
            state["readiness_verdict"] = verdict
            state["phase"] = "scaffold" if verdict in ("GO", "DEGRADED") else "readiness"
            if verdict == "NO_GO":
                state["status"] = "BLOCKED"
            elif state.get("status") == "BLOCKED":
                state["status"] = "ACTIVE"
            state["updated_at"] = utc_now()
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

        baton = halo / "baton.md"
        next_line = (
            "Next: halo-scaffold (Demo 0)"
            if verdict in ("GO", "DEGRADED")
            else "Next: fill .env + install CLIs; re-run readiness"
        )
        baton.write_text(
            f"# Baton\n- Phase: {state.get('phase', 'readiness')}\n"
            f"- Readiness: {verdict}\n- {next_line}\n"
            f"- Do not: share deploy URLs without halo_probe PASS\n",
            encoding="utf-8",
        )

    return report


def main() -> None:
    # allow running as script from python/ dir
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    p = argparse.ArgumentParser(prog="halo_readiness")
    p.add_argument("--repo", default=".")
    p.add_argument("--write", action="store_true", help="write readiness.json, READINESS.md, .env.example, state")
    p.add_argument(
        "--allow-degraded",
        action="store_true",
        help="blocking gaps → DEGRADED instead of NO_GO (explicit human accept)",
    )
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    report = run(Path(args.repo), allow_degraded=args.allow_degraded, write=args.write)
    if args.json or not args.write:
        print(json.dumps(report, indent=2))
    else:
        print(f"READINESS {report['verdict']}  blocking_fail={report['blocking_failures']}  soft_gaps={report['nonblocking_gaps']}")
        print(f"wrote .halo/readiness.json + .halo/spec/READINESS.md + .env.example")

    # exit codes: 0 GO/DEGRADED, 2 NO_GO
    if report["verdict"] == "NO_GO":
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
