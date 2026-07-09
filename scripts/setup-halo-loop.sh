#!/usr/bin/env bash
# Initialize Halo true loop in the current product workspace.
set -euo pipefail

HALO_SYS="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}}"
ROOT="$(pwd)"
MAX=50
SPAWN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --max) MAX="$2"; shift 2 ;;
    --spawn) SPAWN=1; shift ;;
    *) shift ;;
  esac
done

if [[ -z "$HALO_SYS" || ! -f "$HALO_SYS/python/halo_go.py" ]]; then
  # try relative to this script
  HALO_SYS="$(cd "$(dirname "$0")/.." && pwd)"
fi

export HALO_SYSTEM="$HALO_SYS"
export PYTHONPATH="${HALO_SYS}/python${PYTHONPATH:+:$PYTHONPATH}"
PY="${PYTHON:-python3}"

# init product if needed
if [[ ! -f "$ROOT/.halo/state.json" ]]; then
  "$PY" "$HALO_SYS/python/halo_state.py" init --repo "$ROOT" --force
fi

# enable autonomous + self-prompt
ARGS=(--repo "$ROOT" --enable --max-cycles "$MAX")
if [[ "$SPAWN" -eq 1 ]]; then ARGS+=(--spawn); fi
"$PY" "$HALO_SYS/python/halo_go.py" "${ARGS[@]}"

# link skills for discovery
"$PY" "$HALO_SYS/python/halo_link_skills.py" --halo-system "$HALO_SYS" --repo "$ROOT" >/dev/null

# write NEXT_PROMPT
"$PY" "$HALO_SYS/python/halo_next_prompt.py" --repo "$ROOT" --halo-system "$HALO_SYS" --write >/dev/null

# loop control file (Stop hook reads this)
python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path
p = Path("$ROOT/.halo/loop.json")
d = {
  "active": True,
  "iteration": 0,
  "max_iterations": int("$MAX"),
  "started_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
  "session_id": "",
  "completion_promise": "HALO_COMPLETE",
  "protocol": "stop-hook-block-reason",
}
p.write_text(json.dumps(d, indent=2) + "\n")
print("Halo loop armed: .halo/loop.json active=true max=$MAX")
print("Stop hook will re-inject .halo/NEXT_PROMPT.md until complete/max/hard-stop")
print("Cancel: /halo-loop-cancel or scripts/cancel-halo-loop.sh")
PY
