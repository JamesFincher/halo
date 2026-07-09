#!/usr/bin/env python3
"""Engineer a custom synthetic user message each loop iteration.

Not a static template — assembles context from state, baton, logs, readiness,
milestones, evidence, git, and optional last-assistant turn, then emits a
tight, phase-specific prompt engineered for the next unit of work only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from halo_go import next_actions, load as load_state
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from halo_go import next_actions, load as load_state  # type: ignore


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_halo_system() -> Path:
    env = os.environ.get("HALO_SYSTEM")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent


def _read(path: Path, limit: int = 4000) -> str:
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    if len(text) > limit:
        return text[:limit] + "\n…[truncated]"
    return text


def _json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _tail_lines(path: Path, n: int = 12) -> str:
    text = _read(path, limit=20000)
    if not text:
        return "(empty)"
    lines = text.strip().splitlines()
    return "\n".join(lines[-n:]) if lines else "(empty)"


def extract_last_assistant(transcript_path: str | None, max_chars: int = 1200) -> str:
    """Best-effort last assistant text from Claude/Grok JSONL transcript."""
    if not transcript_path:
        return ""
    p = Path(transcript_path)
    if not p.exists():
        return ""
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    texts: list[str] = []
    for line in lines[-200:]:
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        role = obj.get("role") or (obj.get("message") or {}).get("role")
        if role != "assistant":
            continue
        content = obj.get("message", {}).get("content") or obj.get("content") or []
        if isinstance(content, str):
            texts.append(content)
            continue
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    texts.append(str(block.get("text") or ""))
                elif isinstance(block, str):
                    texts.append(block)
    if not texts:
        return ""
    last = texts[-1].strip()
    # strip huge code dumps somewhat
    if len(last) > max_chars:
        last = last[:max_chars] + "\n…[truncated last assistant]"
    return last


def git_snapshot(repo: Path) -> dict[str, str]:
    out: dict[str, str] = {"branch": "?", "head": "?", "status": "?", "log": "?"}
    try:
        out["branch"] = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo, text=True, stderr=subprocess.DEVNULL
        ).strip()
        out["head"] = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=repo, text=True, stderr=subprocess.DEVNULL
        ).strip()
        out["status"] = subprocess.check_output(
            ["git", "status", "-sb"], cwd=repo, text=True, stderr=subprocess.DEVNULL
        ).strip()[:800]
        out["log"] = subprocess.check_output(
            ["git", "log", "--oneline", "-5"], cwd=repo, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass
    return out


def pending_stories(repo: Path, limit: int = 5) -> list[str]:
    stories = _read(repo / ".halo" / "spec" / "STORIES.md", limit=8000)
    pending: list[str] = []
    current = None
    for line in stories.splitlines():
        if line.startswith("### "):
            current = line[4:].strip()
        if current and "pending" in line.lower():
            pending.append(current)
            current = None
        if line.strip().startswith("- **Status**:") and "pending" in line.lower() and current:
            pending.append(current)
            current = None
    # also milestone index
    idx = _json(repo / ".halo" / "milestones" / "index.json")
    for m in idx.get("milestones") or []:
        if m.get("status") == "pending":
            pending.append(f"M{m.get('n')}: {m.get('name')} ({m.get('prompt')})")
    # dedupe preserve order
    seen = set()
    out = []
    for p in pending:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out[:limit]


def readiness_blockers(repo: Path) -> list[str]:
    r = _json(repo / ".halo" / "readiness.json")
    out = []
    for it in r.get("items") or []:
        if it.get("skipped") or it.get("ok"):
            continue
        tag = "BLOCKING" if it.get("blocking") else "optional"
        out.append(f"[{tag}] {it.get('id')}: {it.get('human_action') or 'fix'}")
    return out[:8]


def feature_summary(repo: Path) -> dict[str, Any]:
    try:
        from halo_features import summary

        return summary(repo)
    except Exception:
        data = _json(repo / ".halo" / "feature-list.json")
        feats = data.get("features") or []
        pending = [f for f in feats if not f.get("passes")]
        return {
            "total": len(feats),
            "passed": len(feats) - len(pending),
            "remaining": len(pending),
            "all_pass": bool(feats) and not pending,
            "next": pending[0] if pending else None,
        }


def progress_tail(repo: Path, n: int = 8) -> str:
    try:
        from halo_progress import tail

        rows = tail(repo, n)
        if not rows:
            return "(no progress.jsonl yet — append after each unit)"
        return "\n".join(
            f"- {r.get('at')} `{r.get('event')}` {r.get('note') or r.get('id') or ''}" for r in rows
        )
    except Exception:
        return _tail_lines(repo / ".halo" / "progress.md", n)


def evidence_summary(repo: Path) -> str:
    ev = repo / ".halo" / "evidence"
    if not ev.is_dir():
        return "(no evidence yet)"
    files = sorted(ev.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[:8]
    if not files:
        return "(no evidence yet)"
    lines = []
    for f in files:
        lines.append(f"- {f.name} ({f.stat().st_size}b)")
    return "\n".join(lines)


# ── Phase-specific playbooks: what to do THIS turn only ─────────────

PHASE_PLAYBOOK: dict[str, dict[str, Any]] = {
    "intake": {
        "mission": "Produce a complete intake object and lock into specs in ONE pass.",
        "do": [
            "Scan TARGET (README, package.json, existing code) for signals.",
            "Write state.intake: purpose, product_name, features[4-6], out_of_scope, stack, integrations, data_model, design, milestones[3].",
            "Defaults: greenfield web→nextjs-saas; api→fastapi; existing→detect.",
            "Run: halo specs && halo lock (auto_lock).",
            "Log choices to .halo/autonomous-log.md.",
        ],
        "dont": [
            "Do not interview the human.",
            "Do not start app feature code yet.",
            "Do not leave spec_status=none.",
        ],
        "done_when": "spec_status=locked and phase=readiness (or ready for ready step).",
        "artifacts": [".halo/state.json intake keys", ".halo/spec/*", "baton updated"],
    },
    "spec_pack": {
        "mission": "Materialize full spec pack from intake and auto-lock.",
        "do": [
            "halo specs (or halo_spec_write).",
            "Verify PRD, STACK, STORIES, MILESTONES, INTEGRATIONS exist and non-empty.",
            "halo lock immediately.",
        ],
        "dont": ["Do not wait for human review.", "Do not scaffold yet."],
        "done_when": "spec_status=locked; phase=readiness.",
        "artifacts": [".halo/spec/PRD.md", "STORIES.md", "STACK.md"],
    },
    "spec_review": {
        "mission": "Treat review as complete under autonomous mode; lock and advance.",
        "do": [
            "If specs incomplete, regenerate with halo specs.",
            "halo lock.",
            "Proceed toward readiness.",
        ],
        "dont": ["Do not ask human to approve.", "Do not freestyle new scope."],
        "done_when": "spec_status=locked.",
        "artifacts": [".halo/spec/* locked"],
    },
    "readiness": {
        "mission": "Run lifecycle readiness; degrade if needed; unlock scaffold.",
        "do": [
            "halo ready --allow-degraded (if auto_degraded_ok).",
            "Ensure .env.example has credential NAMES only.",
            "If still NO_GO without degrade path: set baton blockers and STOP (hard).",
            "Else advance toward scaffold.",
        ],
        "dont": ["Do not invent secrets.", "Do not log secret values.", "Do not block on optional Sentry/analytics."],
        "done_when": "readiness_verdict in GO|DEGRADED.",
        "artifacts": [".halo/readiness.json", ".halo/spec/READINESS.md", ".env.example"],
    },
    "scaffold": {
        "mission": "Scaffold stack skeleton + milestones + Demo0 with live probe.",
        "do": [
            "halo scaffold --profile auto --demo0 local (or --skip-ready-check if DEGRADED).",
            "On probe fail: fix and retry; never announce dead URL.",
            "Confirm .halo/milestones/*/prompt.md exists.",
            "phase should become build on success.",
        ],
        "dont": ["Do not build full product features.", "Do not claim deploy without probe PASS."],
        "done_when": "scaffold_profile set; demo0-probe ok or documented skip; phase=build.",
        "artifacts": ["app skeleton", ".halo/milestones/", ".halo/evidence/demo0-probe.json"],
    },
    "build": {
        "mission": "Ship exactly ONE pending feature-list item with TDD + evidence.",
        "do": [
            "Boot: read feature-list next failing item; run ./init.sh if present; check git log -5.",
            "Pick ONE feature with passes:false (machine truth). Prefer .halo/feature-list.json over markdown alone.",
            "If state.dogfood_mode=compounding: this unit MUST upgrade factory code (or verify a harness path) then run scripts/halo-cycle-smoke.sh.",
            "Write .halo/plans/Sxxx-plan.md with AC and files.",
            "RED test → implement min code → GREEN full suite. Never delete tests (ratchet).",
            "Run: bash $HALO_SYSTEM/scripts/halo-cycle-smoke.sh .  (required for dogfood; strongly encouraged always).",
            "Write GREEN evidence: .halo/evidence/Sxxx-green.json (exit_code:0) including smoke PASS note.",
            "Arena: halo arena --id Sxxx when verify matters.",
            "Mark pass only via: halo features pass --id Sxxx --evidence .halo/evidence/Sxxx-green.json",
            "Append progress; baton; autonomous-log.",
            "Safe commit factory files only (never force-add .halo/ or .halo-archive/).",
            "ONE unit only this turn (unless tiny residual fix).",
        ],
        "dont": [
            "Do not start 3 stories in one turn.",
            "Do not skip RED when adding behavior.",
            "Do not mark passes:true by hand-editing JSON without evidence.",
            "Do not share unprobed URLs.",
            "Do not touch denylist paths.",
            "Do not commit dogfood-only noise if factory gitignore forbids .halo/ (factory dogfood is local).",
        ],
        "done_when": "One feature-list item advanced (GREEN evidence + pass tool) OR hard-stop documented.",
        "artifacts": ["code+tests", ".halo/evidence/Sxxx-green.json", "progress.jsonl"],
    },
    "complete": {
        "mission": "Confirm complete; do not re-open work.",
        "do": [
            "Verify no pending high-priority stories.",
            "Write final baton summary.",
            "Output <promise>HALO_COMPLETE</promise> if loop expects it.",
            "Disarm loop: leave phase complete; do not force more builds.",
        ],
        "dont": ["Do not invent new scope.", "Do not keep looping."],
        "done_when": "Loop can stop cleanly.",
        "artifacts": ["final baton", "optional scores"],
    },
}


def playbook_for(phase: str) -> dict[str, Any]:
    return PHASE_PLAYBOOK.get(phase, {
        "mission": f"Advance phase '{phase}' per WORKFLOWS.md using defaults.",
        "do": ["Read baton and state.", "Execute halo go --plan items.", "Update baton."],
        "dont": ["Do not ask the human.", "Do not skip evidence."],
        "done_when": "Phase advanced or hard stop.",
        "artifacts": ["updated state/baton"],
    })


def primary_action(plan: list[str], phase: str) -> str:
    if not plan:
        return f"Advance phase `{phase}` one concrete step."
    # prefer first non-STOP
    for p in plan:
        if not str(p).startswith("STOP"):
            return str(p)
    return str(plan[0])


def detect_issues_from_last_turn(last_assistant: str, phase: str) -> list[str]:
    issues = []
    if not last_assistant:
        return issues
    low = last_assistant.lower()
    if "should i" in low or "would you like" in low or "please confirm" in low:
        issues.append("Previous turn asked the human — forbidden in autonomous mode. Decide yourself.")
    if "error" in low and phase == "build":
        issues.append("Previous turn mentioned errors — prioritize root-cause fix this turn.")
    if "404" in low or "unreachable" in low:
        issues.append("Deploy/probe failure signal — fix probe before any URL share.")
    if "todo" in low and "implement" in low:
        issues.append("Avoid leaving TODOs; ship minimal working path.")
    return issues


def spec_digest(repo: Path, limit: int = 3000) -> str:
    '''Read .halo/spec file list and key document snippets for the prompt context.'''
    spec = repo / ".halo" / "spec"
    parts: list[str] = []
    if spec.is_dir():
        files = sorted(p.name for p in spec.iterdir() if p.is_file())
        if files:
            parts.append(f"**Spec files ({len(files)}):** " + ", ".join(files))
    for name in ("PRD.md", "STACK.md", "API.md", "DATA-MODEL.md", "STORIES.md", "MILESTONES.md"):
        p = spec / name
        if p.exists():
            text = _read(p, limit=limit)
            if text:
                parts.append(f"\n### {name}\n")
                parts.append(text[:limit])
    return "\n".join(parts) if parts else "(no spec pack yet — run halo specs)"


def build_prompt(
    repo: Path,
    halo_sys: Path,
    *,
    transcript_path: str | None = None,
    iteration: int | None = None,
    max_iterations: int | None = None,
) -> str:
    repo = repo.resolve()
    try:
        data = load_state(repo)
    except SystemExit:
        data = {}

    try:
        plan = next_actions(repo)
    except SystemExit:
        plan = ["halo init", "enable autonomous", "drive phase machine"]

    loop = _json(repo / ".halo" / "loop.json")
    phase = data.get("phase") or "intake"
    status = data.get("status") or "ACTIVE"
    product = data.get("product_name") or repo.name
    if isinstance(product, dict):
        product = product.get("name") or repo.name
    auto = bool(data.get("autonomous"))
    ready = data.get("readiness_verdict")
    profile = data.get("scaffold_profile")
    story = data.get("current_story")
    demo = data.get("last_demo_url")
    iter_n = iteration if iteration is not None else int(loop.get("iteration") or 0)
    max_n = max_iterations if max_iterations is not None else int(
        loop.get("max_iterations") or data.get("autonomous_max_cycles") or 50
    )

    pb = playbook_for(str(phase))
    primary = primary_action(plan, str(phase))
    baton = _tail_lines(repo / ".halo" / "baton.md", 20)
    alog = _tail_lines(repo / ".halo" / "autonomous-log.md", 15)
    # D083: explicit last-3 autonomous-log lines under Progress (truncated)
    alog_raw = _tail_lines(repo / ".halo" / "autonomous-log.md", 3)
    alog_last3 = "\n".join(
        (ln[:200] + ("…" if len(ln) > 200 else "")) for ln in alog_raw.splitlines() if ln.strip()
    ) or "(empty)"
    git = git_snapshot(repo)
    stories = pending_stories(repo)
    blockers = readiness_blockers(repo)
    evidence = evidence_summary(repo)
    feats = feature_summary(repo)
    budget_line = "(budget n/a)"
    try:
        from halo_budget import check as budget_check
        bv = budget_check(repo)
        bb = bv.get('budget') or {}
        budget_line = (
            f"verdict={bv.get('verdict')} reason={bv.get('reason')} "
            f"iter={bv.get('iteration')} day_cycles={bv.get('day_cycles')} "
            f"max_iter={bb.get('max_iterations')} max_daily={bb.get('max_daily_cycles')}"
        )
    except Exception as _e:
        budget_line = f"(budget error: {_e})"
    prog = progress_tail(repo)
    last_asst = extract_last_assistant(transcript_path)
    turn_issues = detect_issues_from_last_turn(last_asst, str(phase))
    spec_block = spec_digest(repo, limit=3000)

    intake = data.get("intake") or {}
    purpose = intake.get("purpose") or ""
    if isinstance(purpose, dict):
        purpose = purpose.get("text") or purpose.get("purpose") or json.dumps(purpose)
    purpose = str(purpose)[:400]

    features = intake.get("features") or []
    feat_lines = []
    for f in features[:6]:
        if isinstance(f, dict):
            feat_lines.append(f"- {f.get('title') or f.get('id')}: {f.get('one_liner') or ''}")
        else:
            feat_lines.append(f"- {f}")
    feat_block = "\n".join(feat_lines) if feat_lines else "(none yet — create in intake)"

    stack = intake.get("stack") or {}
    stack_s = json.dumps(stack, indent=2)[:500] if stack else "(detect or choose default)"

    do_list = "\n".join(f"{i}. {x}" for i, x in enumerate(pb["do"], 1))
    dont_list = "\n".join(f"- {x}" for x in pb["dont"])
    plan_list = "\n".join(f"- {p}" for p in plan)
    stories_list = "\n".join(f"- {s}" for s in stories) if stories else "- (none listed — pick next milestone or mark complete)"
    blockers_list = "\n".join(f"- {b}" for b in blockers) if blockers else "- (none / not run)"
    issues_list = "\n".join(f"- {i}" for i in turn_issues) if turn_issues else "- (none detected from last turn)"

    last_asst_block = (
        f"```\n{last_asst}\n```"
        if last_asst
        else "(no transcript excerpt — rely on baton/state/files)"
    )

    # Focus banner: one sentence the model must not ignore
    focus = f"**THIS TURN ONLY:** {primary}"

    # D094: surface exhausted compound templates so agents expand ROADMAP
    seed_meta = _json(repo / ".halo" / "compound-seed.json")
    roadmap_exhausted = seed_meta.get("last_reason") == "no_new_roadmap"
    if roadmap_exhausted:
        focus = (
            f"{focus}\n\n"
            "**ROADMAP EXHAUSTED:** expand `ROADMAP_TEMPLATES` in `python/halo_features.py`, "
            "then `halo features seed --force` and implement the first requires_code unit."
        )

    return f"""# Halo synthetic user turn · {utc_now()}
# iteration {iter_n}/{max_n} · phase={phase} · status={status}

You are **not** chatting with a human. This message was **injected** by the Halo Stop-hook loop to continue autonomous work. There is nobody waiting to answer questions.

{focus}

---

## Role & authority

- Load and obey skill **halo-go** (autonomous + self-prompt).
- You are the **operator**. Decide with defaults. Log decisions to `.halo/autonomous-log.md`.
- **Forbidden:** AskUserQuestion, "should I…?", waiting for approval, inventing secrets, production deploy, denylist paths, fake evidence.
- **Hard stop only if:** status PAUSED/ESCALATED, kill switch, 3 fails on same story, true blocking secrets with no degrade, denylist/prod.

---

## Situation (live context)

| Field | Value |
|-------|-------|
| Product | {product} |
| TARGET | `{repo}` |
| Halo system | `{halo_sys}` |
| Phase | **{phase}** |
| Status | **{status}** |
| Autonomous | {auto} |
| Readiness | {ready} |
| Scaffold profile | {profile} |
| Current story | {story} |
| Last demo URL | {demo} |
| Loop iteration | {iter_n} / {max_n} |
| roadmap_exhausted | {roadmap_exhausted} |

### Spec context
{spec_block}

### Purpose (from intake)
{purpose or "(not set — define this turn if in intake)"}

### Features in scope
{feat_block}

### Stack
```json
{stack_s}
```

### Feature list (machine truth — passes: bool)
- total={feats.get('total')} passed={feats.get('passed')} remaining={feats.get('remaining')} all_pass={feats.get('all_pass')}
- **next failing feature:** {json.dumps(feats.get('next'), indent=2) if feats.get('next') else '(none — all pass or list empty; sync with halo features sync)'}
- scores_count: {int(feats.get('scores_count') or 0)}
- trajectories_count: {int(feats.get('trajectories_count') or 0)}
- scores_trajectories_match: {'true' if bool(feats.get('scores_trajectories_match', int(feats.get('scores_count') or 0) == int(feats.get('trajectories_count') or 0))) else 'false'}
- latest_score_id: {feats.get('latest_score_id') or '-'}
- latest_trajectory_id: {feats.get('latest_trajectory_id') or '-'}

### Pending work (markdown view)
{stories_list}

### Budget gate
{budget_line}

### Progress log (tail)
{prog}

### Autonomous log (last 3)
{alog_last3}

### Readiness gaps
{blockers_list}

### Recent evidence files
{evidence}

### Git
- branch: `{git.get('branch')}` @ `{git.get('head')}`
- status:
```
{git.get('status')}
```
- recent commits:
```
{git.get('log')}
```

### Baton (tail)
```
{baton}
```

### Autonomous log (tail)
```
{alog}
```

### Last assistant turn (excerpt)
{last_asst_block}

### Issues inferred from last turn
{issues_list}

---

## Mission this turn (phase playbook: {phase})

**Mission:** {pb['mission']}

**Do now (in order):**
{do_list}

**Do not:**
{dont_list}

**Done when:** {pb['done_when']}

**Expected artifacts:** {', '.join(pb.get('artifacts') or [])}

### Machine plan (from halo go --plan)
{plan_list}

---

## Session boot (every cold inject — do first)

1. `export HALO_SYSTEM={halo_sys}`
2. Read: `.halo/state.json`, baton.md, feature-list summary, progress tail, `git log -5`
3. If `./init.sh` exists: run it (install + baseline). Fix breakages before new features.
4. If feature-list empty but STORIES exist: `python3 {halo_sys}/python/halo_features.py sync --repo {repo}`
5. Budget: `python3 {halo_sys}/python/halo_budget.py check --repo {repo}` — stop if HALT
6. Pick **one** feature with `passes: false` (or phase work if not in build yet)

## Output contract (end of turn)

1. Perform the work (tools/CLI). Prefer `$HALO_SYSTEM/scripts/halo` and `$HALO_SYSTEM/python/`.
2. **Test ratchet:** never delete or weaken tests to go green.
3. If a feature is truly done (GREEN suite + AC): write evidence then:  
   `python3 {halo_sys}/python/halo_features.py pass --repo {repo} --id Sxxx --evidence .halo/evidence/Sxxx-green.json --note "…"`
4. Append progress:  
   `python3 {halo_sys}/python/halo_progress.py add --repo {repo} --event unit --note "…"`
5. Append 1–5 lines to `.halo/autonomous-log.md` (decisions, not questions).
6. Update `.halo/baton.md`.
7. Refresh inject: `python3 {halo_sys}/python/halo_next_prompt.py --repo {repo} --write`
8. Emit `<promise>HALO_COMPLETE</promise>` **only if** every feature has `passes:true` + verified_at/evidence (or phase=complete). Stop hook rejects false promises.
9. Prefer a git commit per completed **factory code** unit. Never force-add gitignored dogfood `.halo/` into the factory remote.

### Quality bar
- One unit only. Observable outcome. No asking. No test deletion. No fake pass.

---

## Execute

Begin with the primary action:

### → {primary}

Work now.
"""


def write_prompt(
    repo: Path,
    halo_sys: Path | None = None,
    *,
    transcript_path: str | None = None,
    iteration: int | None = None,
    max_iterations: int | None = None,
) -> Path:
    repo = repo.resolve()
    hs = halo_sys or find_halo_system()
    (repo / ".halo").mkdir(parents=True, exist_ok=True)
    path = repo / ".halo" / "NEXT_PROMPT.md"
    body = build_prompt(
        repo,
        hs,
        transcript_path=transcript_path,
        iteration=iteration,
        max_iterations=max_iterations,
    )
    path.write_text(body, encoding="utf-8")
    # archive last few prompts for debug
    hist = repo / ".halo" / "prompt-history"
    hist.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (hist / f"NEXT_{ts}.md").write_text(body, encoding="utf-8")
    # keep only last 20
    old = sorted(hist.glob("NEXT_*.md"))
    for f in old[:-20]:
        try:
            f.unlink()
        except OSError:
            pass

    sp = repo / ".halo" / "state.json"
    if sp.exists():
        try:
            data = json.loads(sp.read_text(encoding="utf-8"))
            data["next_prompt_at"] = utc_now()
            data["next_prompt_path"] = str(path)
            data["next_prompt_phase"] = data.get("phase")
            data["next_prompt_primary"] = primary_action(
                next_actions(repo) if data else [], str(data.get("phase") or "")
            )
            data["updated_at"] = utc_now()
            sp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        except (json.JSONDecodeError, SystemExit, OSError):
            pass
    return path


def spawn_headless(repo: Path, max_turns: int = 1) -> dict[str, Any]:
    """Delegate to halo_drive (documented headless: grok --prompt-file NEXT_PROMPT)."""
    try:
        from halo_drive import spawn_headless as drive_spawn

        return drive_spawn(Path(repo), max_turns=max_turns, force=True)
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_next_prompt")
    p.add_argument("--repo", default=".")
    p.add_argument("--halo-system", default=None)
    p.add_argument("--write", action="store_true", default=True)
    p.add_argument("--print", dest="do_print", action="store_true")
    p.add_argument("--spawn", action="store_true")
    p.add_argument("--max-turns", type=int, default=1)
    p.add_argument("--transcript", default=None, help="JSONL transcript path from Stop hook")
    p.add_argument("--iteration", type=int, default=None)
    p.add_argument("--max-iterations", type=int, default=None)
    args = p.parse_args()
    repo = Path(args.repo).resolve()
    hs = Path(args.halo_system).resolve() if args.halo_system else find_halo_system()

    path = write_prompt(
        repo,
        hs,
        transcript_path=args.transcript,
        iteration=args.iteration,
        max_iterations=args.max_iterations,
    )
    if args.do_print:
        print(path.read_text(encoding="utf-8"))
    else:
        # summary only — avoid dumping full prompt to hook logs accidentally
        data = _json(repo / ".halo" / "state.json")
        print(
            json.dumps(
                {
                    "ok": True,
                    "path": str(path),
                    "phase": data.get("phase"),
                    "primary": data.get("next_prompt_primary"),
                    "chars": path.stat().st_size,
                },
                indent=2,
            )
        )

    if args.spawn:
        result = spawn_headless(repo, max_turns=args.max_turns)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
