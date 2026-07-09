#!/usr/bin/env bash
set -euo pipefail
ROOT="$(pwd)"
LOOP="$ROOT/.halo/loop.json"
if [[ -f "$LOOP" ]]; then
  python3 - <<PY
import json
from pathlib import Path
p = Path("$LOOP")
d = json.loads(p.read_text()) if p.exists() else {}
d["active"] = False
d["stopped_reason"] = "cancelled"
p.write_text(json.dumps(d, indent=2) + "\n")
print("Halo loop cancelled (loop.json active=false)")
PY
fi
if [[ -f "$ROOT/.halo/state.json" ]]; then
  HALO_SYS="${HALO_SYSTEM:-$(cd "$(dirname "$0")/.." && pwd)}"
  export PYTHONPATH="${HALO_SYS}/python${PYTHONPATH:+:$PYTHONPATH}"
  python3 "$HALO_SYS/python/halo_go.py" --repo "$ROOT" --disable 2>/dev/null || true
fi
echo "Normal stop allowed."
