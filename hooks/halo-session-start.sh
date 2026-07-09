#!/usr/bin/env bash
# Halo SessionStart — boot ritual + progress.jsonl tail (D040).
set -euo pipefail
cat >/dev/null || true
CWD="${GROK_WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-${PWD}}}"
export CWD
if [[ -f "$CWD/.halo/state.json" ]]; then
  python3 - <<'PY' 2>/dev/null || true
import json
import os
import sys
from pathlib import Path

cwd = Path(os.environ.get("CWD") or os.environ.get("GROK_WORKSPACE_ROOT") or ".")
state_p = cwd / ".halo" / "state.json"
if not state_p.exists():
    raise SystemExit(0)
s = json.loads(state_p.read_text(encoding="utf-8"))
loop = {}
lp = cwd / ".halo" / "loop.json"
if lp.exists():
    try:
        loop = json.loads(lp.read_text(encoding="utf-8"))
    except Exception:
        pass
phase = s.get("phase")
auto = bool(s.get("autonomous") or loop.get("active"))
remaining, nxt = "?", "-"
fl = cwd / ".halo" / "feature-list.json"
if fl.exists():
    try:
        feats = json.loads(fl.read_text(encoding="utf-8")).get("features") or []
        remaining = sum(1 for f in feats if not f.get("passes"))
        pending = [f for f in feats if not f.get("passes")]
        if pending:
            nxt = pending[0].get("id") or "-"
    except Exception:
        pass
print(
    f"Halo boot: phase={phase} auto={auto} remaining_features={remaining} next={nxt}. "
    "Read baton + NEXT_PROMPT + feature-list; ./init.sh if present; halo-go when auto; one unit.",
    file=sys.stderr,
)
# progress.jsonl tail
pj = cwd / ".halo" / "progress.jsonl"
if pj.exists() and pj.stat().st_size > 0:
    try:
        lines = pj.read_text(encoding="utf-8", errors="replace").strip().splitlines()[-5:]
        if lines:
            print("Halo progress (tail):", file=sys.stderr)
            for line in lines:
                try:
                    o = json.loads(line)
                    note = str(o.get("note") or "")[:80]
                    print(
                        f"  - {o.get('at', '?')} {o.get('event', '?')}: {note}",
                        file=sys.stderr,
                    )
                except Exception:
                    print(f"  - {line[:100]}", file=sys.stderr)
    except Exception:
        pass
if auto:
    print(
        "Halo: drive armed — headless/scheduler continues until complete/budget/halt.",
        file=sys.stderr,
    )
PY
fi
exit 0
