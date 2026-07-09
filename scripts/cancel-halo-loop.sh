#!/usr/bin/env bash
# Disarm continuous drive
set -euo pipefail
ROOT="$(pwd)"
HALO_SYS="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-}}}"
if [[ -z "$HALO_SYS" || ! -d "$HALO_SYS/python" ]]; then
  HALO_SYS="$(cd "$(dirname "$0")/.." && pwd)"
fi
export PYTHONPATH="${HALO_SYS}/python${PYTHONPATH:+:$PYTHONPATH}"
PY="${PYTHON:-python3}"

if [[ -f "$ROOT/.halo/state.json" ]]; then
  "$PY" "$HALO_SYS/python/halo_go.py" --repo "$ROOT" --disable 2>/dev/null || true
fi

python3 - <<PY
import json
from pathlib import Path
root = Path("$ROOT")
for name in ("loop.json", "drive.lock"):
    p = root / ".halo" / name
    if name == "loop.json" and p.exists():
        try:
            d = json.loads(p.read_text())
        except Exception:
            d = {}
        d["active"] = False
        d["stopped_reason"] = "cancel"
        p.write_text(json.dumps(d, indent=2) + "\n")
    elif p.exists():
        p.unlink(missing_ok=True)
print("Halo drive disarmed (loop inactive, drive.lock cleared)")
print("Also cancel TUI /loop jobs via scheduler_list + scheduler_delete if you created any")
PY
