#!/usr/bin/env bash
# Arm Halo continuous drive for this product workspace.
# CRITICAL (Grok Build): Stop hooks are PASSIVE — decision:block does NOT re-prompt.
# Continuous work = headless spawn (default) + single supervisor (watchdog).
set -euo pipefail

HALO_SYS="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}}"
ROOT="$(pwd)"
MAX=50
NO_SPAWN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --max) MAX="$2"; shift 2 ;;
    --spawn) shift ;; # legacy; spawn is default ON
    --no-spawn) NO_SPAWN=1; shift ;;
    *) shift ;;
  esac
done

if [[ -z "$HALO_SYS" || ! -f "$HALO_SYS/python/halo_go.py" ]]; then
  HALO_SYS="$(cd "$(dirname "$0")/.." && pwd)"
fi

export HALO_SYSTEM="$HALO_SYS"
export PYTHONPATH="${HALO_SYS}/python${PYTHONPATH:+:$PYTHONPATH}"
PY="${PYTHON:-python3}"

if [[ ! -f "$ROOT/.halo/state.json" ]]; then
  "$PY" "$HALO_SYS/python/halo_state.py" init --repo "$ROOT" --force
fi

ARGS=(--repo "$ROOT" --enable --max-cycles "$MAX")
if [[ "$NO_SPAWN" -eq 1 ]]; then
  ARGS+=(--no-spawn)
fi
"$PY" "$HALO_SYS/python/halo_go.py" "${ARGS[@]}"

"$PY" "$HALO_SYS/python/halo_link_skills.py" --halo-system "$HALO_SYS" --repo "$ROOT" >/dev/null || true
"$PY" "$HALO_SYS/python/halo_next_prompt.py" --repo "$ROOT" --halo-system "$HALO_SYS" --write >/dev/null

# Install always-on user Stop hook (trusted globally) so drive runs even if plugin hooks miss
HOOK_DIR="${HOME}/.grok/hooks"
mkdir -p "$HOOK_DIR"
cat > "$HOOK_DIR/halo-true-loop.json" <<EOF
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "export HALO_SYSTEM=\"$HALO_SYS\"; export GROK_WORKSPACE_ROOT=\"\${GROK_WORKSPACE_ROOT:-\$PWD}\"; bash \"$HALO_SYS/hooks/halo-stop-loop.sh\"",
            "timeout": 60
          }
        ]
      }
    ],
    "StopFailure": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "export HALO_SYSTEM=\"$HALO_SYS\"; export GROK_WORKSPACE_ROOT=\"\${GROK_WORKSPACE_ROOT:-\$PWD}\"; export HALO_HOOK_TYPE=StopFailure; bash \"$HALO_SYS/hooks/halo-stop-loop.sh\"",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
EOF

# Persist drive protocol note for cold agents
python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path
root = Path("$ROOT")
loop_p = root / ".halo" / "loop.json"
d = {}
if loop_p.exists():
    try:
        d = json.loads(loop_p.read_text())
    except Exception:
        d = {}
d.update({
  "active": True,
  "max_iterations": int("$MAX"),
  "started_at": d.get("started_at") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
  "completion_promise": "HALO_COMPLETE",
  "protocol": "grok-acp" if os.environ.get("HALO_ACP") else "grok-headless+watchdog",
  "protocol_note": "ACP supervisor (grok agent stdio) drives the session" if os.environ.get("HALO_ACP") else "Grok Stop is passive; headless re-entry via grok --prompt-file NEXT_PROMPT --max-turns 1 is the continue path",
  "acp": bool(os.environ.get("HALO_ACP")),
})
if "iteration" not in d:
    d["iteration"] = 0
loop_p.write_text(json.dumps(d, indent=2) + "\n")

# Clear kill switch so a new arming can run (cancel writes OFF)
off_p = root / ".halo" / "OFF"
if off_p.exists():
    off_p.unlink()

print("Halo continuous drive ARMED")
print(f"  loop.json active=true max=$MAX")
print(f"  protocol: headless re-entry via grok --prompt-file NEXT_PROMPT --max-turns 1 + watchdog supervisor")
print(f"  user hook: ~/.grok/hooks/halo-true-loop.json")
print(f"  NEXT_PROMPT: $ROOT/.halo/NEXT_PROMPT.md")
print("")
print("Cancel: /stop-loop  |  halo loop-cancel  |  halo go --off")
if "$NO_SPAWN" == "1":
    print("WARNING: --no-spawn set; on Grok you WILL need to message manually")
PY
