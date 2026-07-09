#!/usr/bin/env bash
# Halo SessionStart — remind agent if autonomous loop is active (non-blocking).
set -euo pipefail
cat >/dev/null || true
CWD="${GROK_WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-${PWD}}}"
STATE="$CWD/.halo/state.json"
LOOP="$CWD/.halo/loop.json"
if [[ -f "$STATE" ]]; then
  python3 - <<PY 2>/dev/null || true
import json
from pathlib import Path
s = json.loads(Path("$STATE").read_text())
loop = {}
lp = Path("$LOOP")
if lp.exists():
    try: loop = json.loads(lp.read_text())
    except Exception: pass
if s.get("autonomous") or loop.get("active"):
    print("Halo: autonomous loop active — load skill halo-go; never ask; read .halo/NEXT_PROMPT.md + baton.", file=__import__("sys").stderr)
PY
fi
exit 0
