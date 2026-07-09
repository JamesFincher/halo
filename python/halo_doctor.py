#!/usr/bin/env python3
"""Halo doctor — system integrity + optional --strict consistency matrix."""

from __future__ import annotations

import argparse
import json
import re
import urllib.request
from pathlib import Path
from typing import Any

# Skills that must exist (workflow inventory)
REQUIRED_SKILLS = [
    "halo-bootstrap",
    "halo-intake",
    "halo-spec-pack",
    "halo-readiness",
    "halo-scaffold",
    "halo-build",
    "halo-verify",
    "halo-deploy",
    "halo-go",
    "halo-status",
    "halo-triage",
    "halo-pause",
    "halo-escalate",
    "halo-handoff",
    "halo-revise",
    "halo-doctor",
]

# CLI verbs that must appear in scripts/halo help/case
REQUIRED_CLI = [
    "init",
    "status",
    "specs",
    "lock",
    "unlock",
    "ready",
    "scaffold",
    "milestones",
    "probe",
    "build",
    "stop",
    "resume",
    "escalate",
    "triage",
    "handoff",
    "doctor",
    "go",
    "continue",
    "link-skills",
    "features",
    "progress",
    "budget",
    "ratchet",
    "arena",
    "commit-unit",
    "loop",
]

REQUIRED_PYTHON = [
    "halo_state.py",
    "halo_readiness.py",
    "halo_scaffold.py",
    "halo_probe.py",
    "halo_go.py",
    "halo_spec_write.py",
    "halo_milestones.py",
    "halo_evidence.py",
    "halo_phases.py",
    "halo_doctor.py",
    "halo_catalog.py",
    "halo_next_prompt.py",
    "halo_link_skills.py",
    "halo_features.py",
    "halo_progress.py",
    "halo_lock.py",
    "halo_budget.py",
    "halo_ratchet.py",
    "halo_arena.py",
    "halo_commit.py",
    "halo_stories_sync.py",
    "halo_drive.py",
]


def check_system(halo_sys: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    skills_dir = halo_sys / ".grok" / "skills"
    for name in REQUIRED_SKILLS:
        p = skills_dir / name / "SKILL.md"
        if not p.exists():
            # also allow skill.md lowercase
            p2 = skills_dir / name / "skill.md"
            if not p2.exists():
                issues.append({"level": "error", "code": "skill_missing", "item": name})

    for py in REQUIRED_PYTHON:
        if not (halo_sys / "python" / py).exists():
            issues.append({"level": "error", "code": "python_missing", "item": py})

    cli = halo_sys / "scripts" / "halo"
    if not cli.exists():
        issues.append({"level": "error", "code": "cli_missing", "item": "scripts/halo"})
    else:
        text = cli.read_text(encoding="utf-8")
        for verb in REQUIRED_CLI:
            # case "$cmd" in arms use verb)
            if not re.search(rf"\n\s*{re.escape(verb)}\)", text) and f" {verb}" not in text:
                # help text mention
                if verb not in text:
                    issues.append({"level": "error", "code": "cli_verb_missing", "item": verb})

    for doc in (
        "docs/WORKFLOWS.md",
        "docs/ARCHITECTURE.md",
        "docs/ARCHITECTURE-DEEP.md",
        "docs/GROK-BUILD.md",
        "AGENTS.md",
    ):
        if not (halo_sys / doc).exists():
            issues.append({"level": "error", "code": "doc_missing", "item": doc})

    # WORKFLOWS should mention halo go / autonomous / self-prompt
    wf = halo_sys / "docs" / "WORKFLOWS.md"
    if wf.exists():
        w = wf.read_text(encoding="utf-8")
        for needle in ("halo go", "autonomous", "probe", "NEXT_PROMPT", "self-prompt"):
            if needle.lower() not in w.lower():
                issues.append({"level": "warn", "code": "workflows_gap", "item": needle})


    hooks = halo_sys / "hooks" / "hooks.json"
    if not hooks.exists():
        issues.append({"level": "error", "code": "hooks_missing", "item": "hooks/hooks.json"})
    else:
        try:
            import json as _json
            hj = _json.loads(hooks.read_text())
            if "Stop" not in (hj.get("hooks") or {}):
                issues.append({"level": "warn", "code": "hooks_no_stop", "item": "Stop hook required for /go true loop"})
        except Exception:
            issues.append({"level": "warn", "code": "hooks_unreadable", "item": "hooks/hooks.json"})
    # hint: plugin must be installed for /go slash + Stop
    if not (halo_sys / "commands" / "go.md").exists():
        issues.append({"level": "warn", "code": "go_command_missing", "item": "commands/go.md"})
    else:
        issues.append({
            "level": "info",
            "code": "plugin_hint",
            "item": "for /go + Stop loop: grok plugin install <halo-path> --trust",
        })


    # Factory cleanliness: dogfood control plane must never be git-tracked
    # (clones of Halo are for use on *other* projects — not full of self-instance state)
    if (halo_sys / "python" / "halo_state.py").exists() and (halo_sys / ".git").exists():
        try:
            import subprocess

            tracked = subprocess.check_output(
                ["git", "ls-files"],
                cwd=halo_sys,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            bad = []
            for line in tracked.splitlines():
                if line.startswith(".halo/") or line in (
                    "init.sh",
                    "halo-health.json",
                ):
                    bad.append(line)
            if bad:
                issues.append(
                    {
                        "level": "error",
                        "code": "dogfood_tracked",
                        "item": bad[:20],
                    }
                )
            # .gitignore must exclude .halo/
            gi = halo_sys / ".gitignore"
            if gi.exists() and ".halo/" not in gi.read_text(encoding="utf-8"):
                issues.append(
                    {
                        "level": "error",
                        "code": "gitignore_missing_halo",
                        "item": "factory .gitignore must ignore .halo/ for dogfood",
                    }
                )
        except (subprocess.CalledProcessError, OSError, FileNotFoundError):
            pass

    return issues


def check_product(repo: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    state_p = repo / ".halo" / "state.json"
    if not state_p.exists():
        issues.append({"level": "info", "code": "not_a_product", "item": str(repo)})
        return issues
    try:
        state = json.loads(state_p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        issues.append({"level": "error", "code": "state_corrupt", "item": "state.json"})
        return issues

    phase = state.get("phase")
    from halo_phases import PHASE_EDGES

    if phase and str(phase).lower() not in PHASE_EDGES:
        issues.append({"level": "warn", "code": "unknown_phase", "item": str(phase)})

    if state.get("spec_status") == "locked":
        spec = repo / ".halo" / "spec"
        for f in ("PRD.md", "STORIES.md", "STACK.md"):
            if not (spec / f).exists():
                issues.append({"level": "error", "code": "locked_missing_spec", "item": f})

    if state.get("autonomous") and state.get("require_human_gate") is True:
        issues.append({"level": "warn", "code": "auto_gate_conflict", "item": "autonomous but require_human_gate"})

    fl = repo / ".halo" / "feature-list.json"
    if state.get("spec_status") == "locked" and not fl.exists():
        issues.append({"level": "warn", "code": "no_feature_list", "item": "run halo_features.py sync"})
    if fl.exists():
        try:
            feats = json.loads(fl.read_text()).get("features") or []
            if state.get("phase") == "build" and not feats:
                issues.append({"level": "warn", "code": "empty_feature_list", "item": "sync from STORIES.md"})
            # passes:true without verified_at/evidence = dishonest done (gaming)
            if state.get("phase") == "build":
                for f in feats:
                    if f.get("passes") and not (f.get("verified_at") or f.get("evidence")):
                        issues.append(
                            {
                                "level": "warn",
                                "code": "feature_pass_unverified",
                                "item": f.get("id") or f.get("description"),
                            }
                        )
        except json.JSONDecodeError:
            issues.append({"level": "error", "code": "feature_list_corrupt", "item": "feature-list.json"})

    if state.get("autonomous"):
        # Fail closed: autonomous without an active true loop is a broken drive (D037)
        loop_p = repo / ".halo" / "loop.json"
        if loop_p.exists():
            try:
                loop = json.loads(loop_p.read_text(encoding="utf-8"))
                if not loop.get("active"):
                    issues.append(
                        {
                            "level": "error",
                            "code": "loop_inactive",
                            "item": "autonomous but loop.json active=false — run halo go or halo loop",
                        }
                    )
            except json.JSONDecodeError:
                issues.append({"level": "error", "code": "loop_corrupt", "item": "loop.json"})
        else:
            issues.append(
                {
                    "level": "error",
                    "code": "loop_not_armed",
                    "item": "autonomous without loop.json — run halo go",
                }
            )

    skills = repo / ".grok" / "skills" / "halo-go"
    if state.get("autonomous") and not skills.exists() and not skills.is_symlink():
        issues.append({"level": "warn", "code": "skills_not_linked", "item": "run halo link-skills"})

    # test ratchet (warn only — agent must fix)
    try:
        from halo_ratchet import check as ratchet_check

        rrep = ratchet_check(repo)
        if not rrep.get("ok"):
            issues.append(
                {
                    "level": "warn",
                    "code": "test_ratchet",
                    "item": rrep.get("violations"),
                }
            )
    except Exception:  # noqa: BLE001
        pass

    # evidence validate if any
    try:
        from halo_evidence import validate_repo

        rep = validate_repo(repo)
        if rep["files_checked"] and not rep["ok"]:
            issues.append({"level": "error", "code": "evidence_invalid", "item": rep.get("results")})
    except Exception as e:  # noqa: BLE001
        issues.append({"level": "warn", "code": "evidence_check_failed", "item": str(e)})

    return issues


def network_ok() -> bool:
    try:
        urllib.request.urlopen("https://example.com", timeout=5)
        return True
    except Exception:  # noqa: BLE001
        return False


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_doctor")
    p.add_argument("--halo-system", default=None)
    p.add_argument("--repo", default=".")
    p.add_argument("--strict", action="store_true", help="exit 2 on any error-level issue")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    halo_sys = Path(args.halo_system).resolve() if args.halo_system else Path(__file__).resolve().parent.parent
    repo = Path(args.repo).resolve()

    issues = check_system(halo_sys)
    issues.extend(check_product(repo))
    net = network_ok()
    if not net:
        issues.append({"level": "warn", "code": "network", "item": "example.com unreachable"})

    errors = [i for i in issues if i["level"] == "error"]
    report = {
        "ok": len(errors) == 0,
        "halo_system": str(halo_sys),
        "repo": str(repo),
        "network": net,
        "error_count": len(errors),
        "issues": issues,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Halo doctor  system={halo_sys}")
        print(f"  network: {'ok' if net else 'fail'}")
        print(f"  errors:  {len(errors)}  total_issues: {len(issues)}")
        for i in issues:
            print(f"  [{i['level']}] {i['code']}: {i['item']}")
        print("PASS" if report["ok"] else "FAIL")

    if args.strict and not report["ok"]:
        raise SystemExit(2)
    raise SystemExit(0 if report["ok"] else 1)


if __name__ == "__main__":
    main()
