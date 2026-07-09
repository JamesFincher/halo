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

# update loop counter first so prompt can include iteration
loop["active"] = True
loop["iteration"] = next_iter
loop["max_iterations"] = max_iter
loop["last_fire_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
if hook_session:
    loop["session_id"] = hook_session
loop_p.parent.mkdir(parents=True, exist_ok=True)
loop_p.write_text(json.dumps(loop, indent=2) + "\n", encoding="utf-8")

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

msg = f"Halo loop iteration {next_iter}/{max_iter} | skill halo-go | never ask | hard stops only"
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
