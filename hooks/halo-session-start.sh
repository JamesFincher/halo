#!/usr/bin/env bash
# Halo SessionStart — boot ritual reminder when product/dogfood state present.
set -euo pipefail
cat >/dev/null || true
CWD="${GROK_WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-${PWD}}}"
STATE="$CWD/.halo/state.json"
LOOP="$CWD/.halo/loop.json"
if [[ -f "$STATE" ]]; then
  python3 - <<PY 2>/dev/null || true
import json
from pathlib import Path
import sys
cwd = Path(r"""$CWD""")
s = json.loads((cwd / ".halo" / "state.json").read_text())
loop = {}
lp = cwd / ".halo" / "loop.json"
if lp.exists():
    try:
        loop = json.loads(lp.read_text())
    except Exception:
        pass
phase = s.get("phase")
auto = bool(s.get("autonomous") or loop.get("active"))
fl = cwd / ".halo" / "feature-list.json"
remaining = "?"
if fl.exists():
    try:
        feats = json.loads(fl.read_text()).get("features") or []
        remaining = sum(1 for f in feats if not f.get("passes"))
    except Exception:
        pass
msg = (
    f"Halo boot: phase={phase} auto={auto} remaining_features={remaining}. "
    "Read .halo/baton.md + .halo/NEXT_PROMPT.md + feature-list; run ./init.sh if present; "
    "load halo-go when autonomous; never ask; one unit only."
)
print(msg, file=sys.stderr)
if auto:
    print("Halo: true loop armed — Stop re-injects NEXT_PROMPT until complete/budget/halt.", file=sys.stderr)
PY
fi
exit 0
