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
        "mission": "Ship exactly ONE pending story/milestone unit with TDD + evidence.",
        "do": [
            "Pick highest-priority pending story from STORIES.md or first pending milestone prompt.",
            "Write .halo/plans/Sxxx-plan.md with AC and files.",
            "RED test → implement min code → GREEN full suite.",
            "Simplify pass; map AC→tests (SPEC_OK).",
            "Deploy preview only if configured; halo probe before any URL share.",
            "Write evidence certs; update story status; baton; autonomous-log.",
            "ONE unit only this turn (unless tiny residual fix).",
        ],
        "dont": [
            "Do not start 3 stories in one turn.",
            "Do not skip RED when adding behavior.",
            "Do not share unprobed URLs.",
            "Do not touch denylist paths.",
        ],
        "done_when": "One story advanced (tests green + evidence) OR hard-stop documented.",
        "artifacts": ["code+tests", ".halo/evidence/*", "milestone-log if milestone done"],
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
    git = git_snapshot(repo)
    stories = pending_stories(repo)
    blockers = readiness_blockers(repo)
    evidence = evidence_summary(repo)
    last_asst = extract_last_assistant(transcript_path)
    turn_issues = detect_issues_from_last_turn(last_asst, str(phase))

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

### Purpose (from intake)
{purpose or "(not set — define this turn if in intake)"}

### Features in scope
{feat_block}

### Stack
```json
{stack_s}
```

### Pending work
{stories_list}

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

## Output contract (end of turn)

1. Perform the work (tools/CLI). Prefer:
   - `$HALO_SYSTEM/scripts/halo …`
   - `$HALO_SYSTEM/python/…`
2. Append 1–5 lines to `.halo/autonomous-log.md` with **what you decided and why** (not questions).
3. Update `.halo/baton.md` with: phase, what shipped, next unit, landmines.
4. Refresh next inject (always):
   ```
   python3 {halo_sys}/python/halo_next_prompt.py --repo {repo} --write
   ```
5. If this unit finishes the product (no pending work / phase complete), write baton accordingly and emit:
   `<promise>HALO_COMPLETE</promise>`
6. If hard-stopped, set status/baton clearly — do not pretend success.

### Quality bar for this turn
- One coherent unit of progress (not a tour of the repo).
- Observable outcome (files, tests, probe, phase advance).
- Custom to **this** product/state — do not re-explain Halo architecture.
- No filler, no asking, no waiting.

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


def spawn_headless(repo: Path, max_turns: int = 80) -> dict[str, Any]:
    prompt = repo / ".halo" / "NEXT_PROMPT.md"
    if not prompt.exists():
        write_prompt(repo)
    grok = shutil.which("grok")
    if not grok:
        return {"ok": False, "error": "grok binary not on PATH", "prompt": str(prompt)}
    cmd = [
        grok,
        "-p",
        "--prompt-file",
        str(prompt),
        "--cwd",
        str(repo),
        "--yolo",
        "--max-turns",
        str(max_turns),
        "--output-format",
        "plain",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        return {
            "ok": r.returncode == 0,
            "returncode": r.returncode,
            "cmd": cmd,
            "stdout_tail": (r.stdout or "")[-4000:],
            "stderr_tail": (r.stderr or "")[-2000:],
            "prompt": str(prompt),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "cmd": cmd, "prompt": str(prompt)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e), "cmd": cmd, "prompt": str(prompt)}


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_next_prompt")
    p.add_argument("--repo", default=".")
    p.add_argument("--halo-system", default=None)
    p.add_argument("--write", action="store_true", default=True)
    p.add_argument("--print", dest="do_print", action="store_true")
    p.add_argument("--spawn", action="store_true")
    p.add_argument("--max-turns", type=int, default=80)
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
