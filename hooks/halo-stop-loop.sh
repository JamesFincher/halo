#!/usr/bin/env bash
# Halo Stop hook — true session loop (Ralph protocol)
# Emits: {"decision":"block","reason":"<NEXT_PROMPT>","systemMessage":"..."}
# Fail-open: errors → exit 0 with no stdout (allow stop).

set -euo pipefail

HOOK_INPUT=$(cat || true)
CWD="${GROK_WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-${PWD}}}"
cd "$CWD" 2>/dev/null || exit 0

PLUGIN_ROOT="${GROK_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}"
HALO_SYS="${HALO_SYSTEM:-$PLUGIN_ROOT}"
if [[ -z "$HALO_SYS" || ! -d "${HALO_SYS}/python" ]]; then
  if [[ -f "$CWD/python/halo_next_prompt.py" ]]; then
    HALO_SYS="$CWD"
  elif [[ -n "$PLUGIN_ROOT" && -f "$PLUGIN_ROOT/python/halo_next_prompt.py" ]]; then
    HALO_SYS="$PLUGIN_ROOT"
  else
    exit 0
  fi
fi

export HALO_SYSTEM="$HALO_SYS"
export PYTHONPATH="${HALO_SYS}/python${PYTHONPATH:+:$PYTHONPATH}"

# Single python driver: decide + print block JSON or exit clean
python3 - "$CWD" "$HOOK_INPUT" <<'PY'
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

cwd = Path(sys.argv[1])
hook_raw = sys.argv[2] if len(sys.argv) > 2 else ""
state_p = cwd / ".halo" / "state.json"
loop_p = cwd / ".halo" / "loop.json"
next_p = cwd / ".halo" / "NEXT_PROMPT.md"
halo_sys = Path(os.environ.get("HALO_SYSTEM", ""))

if not state_p.exists():
    raise SystemExit(0)

try:
    state = json.loads(state_p.read_text(encoding="utf-8"))
except Exception:
    raise SystemExit(0)

loop = {}
if loop_p.exists():
    try:
        loop = json.loads(loop_p.read_text(encoding="utf-8"))
    except Exception:
        loop = {}

auto = bool(state.get("autonomous") or state.get("self_prompt"))
status = (state.get("status") or "ACTIVE").upper()
phase = state.get("phase") or ""
active = bool(loop.get("active", auto))
if status in ("PAUSED", "ESCALATED", "COMPLETE") or phase == "complete":
    active = False
if state.get("HALO_KILL_SWITCH"):
    active = False
if not active:
    raise SystemExit(0)

# session isolation
hook_session = ""
try:
    hook = json.loads(hook_raw) if hook_raw.strip() else {}
    hook_session = hook.get("sessionId") or hook.get("session_id") or ""
except Exception:
    hook = {}
state_session = loop.get("session_id") or ""
if state_session and hook_session and state_session != hook_session:
    raise SystemExit(0)

iteration = int(loop.get("iteration") or 0)
max_iter = int(loop.get("max_iterations") or state.get("autonomous_max_cycles") or 50)
next_iter = iteration + 1

# Budget hard stop (max iter / daily / wall / budget.json halt)
sys.path.insert(0, str(halo_sys / "python"))
try:
    from halo_budget import check as budget_check, record_cycle  # type: ignore

    bver = budget_check(cwd, next_iteration=next_iter)
    if bver.get("verdict") == "HALT":
        loop["active"] = False
        loop["stopped_reason"] = f"budget:{bver.get('reason')}"
        loop_p.write_text(json.dumps(loop, indent=2) + "\n", encoding="utf-8")
        raise SystemExit(0)
except SystemExit:
    raise
except Exception:
    if max_iter > 0 and next_iter > max_iter:
        loop["active"] = False
        loop["stopped_reason"] = "max_iterations"
        loop_p.write_text(json.dumps(loop, indent=2) + "\n", encoding="utf-8")
        raise SystemExit(0)

# transcript for last-assistant-aware prompt engineering
transcript = ""
try:
    transcript = str(hook.get("transcript_path") or hook.get("transcriptPath") or "")
except Exception:
    transcript = ""


def last_assistant_text(path: str) -> str:
    if not path or not Path(path).exists():
        return ""
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    texts = []
    for line in lines[-150:]:
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
        elif isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "text":
                    texts.append(str(b.get("text") or ""))
    return texts[-1] if texts else ""


last_text = last_assistant_text(transcript)
# normalize promise detection (allow whitespace inside tags)
promise = loop.get("completion_promise") or "HALO_COMPLETE"
import re as _re

promise_hit = bool(
    last_text
    and (
        f"<promise>{promise}</promise>" in last_text
        or _re.search(
            rf"<promise>\s*{_re.escape(promise)}\s*</promise>", last_text, _re.I
        )
    )
)


def features_honestly_done(feats: list) -> bool:
    """All pass AND each has verified_at (blocks silent JSON edits without tool)."""
    if not feats:
        return False
    for f in feats:
        if not f.get("passes"):
            return False
        # allow force-pass without evidence only if verified_at set by tool
        if not f.get("verified_at") and not f.get("evidence"):
            return False
    return True


# Completion promise (Ralph) — only honor if feature-list honestly done OR phase complete
if promise_hit:
    fl = {}
    fl_p = cwd / ".halo" / "feature-list.json"
    if fl_p.exists():
        try:
            fl = json.loads(fl_p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            fl = {}
    feats = fl.get("features") or []
    all_pass = features_honestly_done(feats)
    if phase == "complete" or all_pass:
        loop["active"] = False
        loop["stopped_reason"] = "completion_promise"
        loop_p.write_text(json.dumps(loop, indent=2) + "\n", encoding="utf-8")
        raise SystemExit(0)
    # promise without honest all_pass — scold below

# Struggle detection: no git changes for N consecutive iterations
try:
    import subprocess as sp

    dirty = sp.check_output(["git", "status", "--porcelain"], cwd=cwd, text=True, stderr=sp.DEVNULL)
    head = sp.check_output(["git", "rev-parse", "HEAD"], cwd=cwd, text=True, stderr=sp.DEVNULL).strip()
except Exception:
    dirty, head = "?", loop.get("last_head")

no_progress = (not dirty or not str(dirty).strip()) and head == loop.get("last_head")
if no_progress and head and head != "?":
    loop["stagnant_iters"] = int(loop.get("stagnant_iters") or 0) + 1
else:
    loop["stagnant_iters"] = 0
loop["last_head"] = head if head != "?" else loop.get("last_head")

if int(loop.get("stagnant_iters") or 0) >= 3:
    struggle = True
else:
    struggle = False

# Test ratchet — deleted tests → inject hard correction (still block stop)
ratchet_violations = []
try:
    from halo_ratchet import check as ratchet_check  # type: ignore

    rrep = ratchet_check(cwd)
    if not rrep.get("ok"):
        ratchet_violations = rrep.get("violations") or []
except Exception:
    ratchet_violations = []

# update loop counter first so prompt can include iteration
loop["active"] = True
loop["iteration"] = next_iter
loop["max_iterations"] = max_iter
loop["last_fire_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
if hook_session:
    loop["session_id"] = hook_session
loop_p.parent.mkdir(parents=True, exist_ok=True)
loop_p.write_text(json.dumps(loop, indent=2) + "\n", encoding="utf-8")

# record budget spend
try:
    record_cycle(cwd)  # type: ignore[name-defined]
except Exception:
    pass

# refresh NEXT_PROMPT — custom engineered for this iteration + last turn
cmd = [
    sys.executable,
    str(halo_sys / "python" / "halo_next_prompt.py"),
    "--repo",
    str(cwd),
    "--halo-system",
    str(halo_sys),
    "--write",
    "--iteration",
    str(next_iter),
    "--max-iterations",
    str(max_iter),
]
if transcript:
    cmd.extend(["--transcript", transcript])
try:
    subprocess.run(cmd, check=False, capture_output=True, timeout=30)
except Exception:
    pass

if not next_p.exists():
    raise SystemExit(0)

prompt = next_p.read_text(encoding="utf-8")
if struggle:
    prompt = (
        "## STRUGGLE DETECTED\n"
        f"No git progress for {loop.get('stagnant_iters')} consecutive iterations "
        "(same HEAD, clean tree). You are thrashing.\n\n"
        "THIS TURN: either (1) make a real file/test change that advances the next "
        "feature-list item with passes:false, or (2) run `halo escalate` with root cause "
        "and stop looping. Do NOT claim completion. Do NOT delete tests.\n\n"
        "---\n\n" + prompt
    )
if ratchet_violations:
    prompt = (
        "## TEST RATCHET VIOLATION\n"
        "Test files were deleted or gutted. Restore them and fix the code instead.\n"
        + "\n".join(f"- {v}" for v in ratchet_violations[:12])
        + "\n\nIt is **unacceptable** to remove tests to go green.\n\n---\n\n"
        + prompt
    )
if promise_hit:
    prompt = (
        f"## INVALID COMPLETION PROMISE\n"
        f"You emitted <promise>{promise}</promise> but feature-list is not honestly "
        f"all passes (each needs passes:true + verified_at/evidence) and phase is not complete. "
        f"Forbidden. Continue real work.\n\n---\n\n"
        + prompt
    )

if not prompt.strip():
    raise SystemExit(0)

# optional headless spawn fallback
if state.get("self_prompt_spawn") and os.environ.get("HALO_STOP_SPAWN") == "1":
    import shutil

    grok = shutil.which("grok")
    if grok:
        subprocess.Popen(
            [
                grok,
                "-p",
                "--prompt-file",
                str(next_p),
                "--cwd",
                str(cwd),
                "--yolo",
                "--max-turns",
                "80",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

msg = (
    f"Halo loop {next_iter}/{max_iter} | halo-go | never ask"
    + (" | STRUGGLE" if struggle else "")
)
# Ralph / Claude Code Stop protocol — reason is re-injected as next user message
out = {
    "decision": "block",
    "reason": prompt,
    "systemMessage": msg,
    "continue": True,
    "additionalContext": prompt,
}
sys.stdout.write(json.dumps(out))
PY

exit 0
