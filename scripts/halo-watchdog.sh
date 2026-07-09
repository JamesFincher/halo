#!/usr/bin/env bash
# Continuous drive without the 60s Grok /loop floor.
# Runs planner (refresh NEXT_PROMPT) then ensures a headless builder is alive.
# Usage: halo-watchdog.sh [repo] [sleep_seconds]
# Stop: kill the watchdog PID or: scripts/cancel-halo-loop.sh / halo go --off
# Single-instance: refuses to start if pidfile PID is still alive (D073).
set -euo pipefail
HALO_SYS="${HALO_SYSTEM:-$(cd "$(dirname "$0")/.." && pwd)}"
ROOT="$(cd "${1:-.}" && pwd)"
SLEEP="${2:-15}"
export HALO_SYSTEM="$HALO_SYS"
export PYTHONPATH="${HALO_SYS}/python${PYTHONPATH:+:$PYTHONPATH}"
PY="${PYTHON:-python3}"
cd "$ROOT"
mkdir -p "$ROOT/.halo/logs"

PIDFILE="$ROOT/.halo/logs/watchdog.pid"
if [[ -f "$PIDFILE" ]]; then
  old="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [[ -n "${old:-}" ]] && kill -0 "$old" 2>/dev/null && [[ "$old" != "$$" ]]; then
    echo "[watchdog] refuse: already running pid=$old (pidfile $PIDFILE)" >&2
    exit 3
  fi
fi

echo "[watchdog] root=$ROOT sleep=${SLEEP}s pid=$$  stop: halo go --off; kill \$(cat .halo/logs/watchdog.pid)"
echo $$ > "$PIDFILE"

while true; do
  if [[ -f "$ROOT/.halo/OFF" ]]; then
    echo "[watchdog] .halo/OFF present — exit"
    exit 0
  fi
  if [[ -f "$ROOT/.halo/loop.json" ]]; then
    active="$($PY -c "import json;print(json.load(open('$ROOT/.halo/loop.json')).get('active'))" 2>/dev/null || echo False)"
  else
    active=False
  fi
  auto="$($PY -c "import json;print(json.load(open('$ROOT/.halo/state.json')).get('autonomous'))" 2>/dev/null || echo False)"
  if [[ "$active" != "True" && "$auto" != "True" ]]; then
    echo "[watchdog] loop inactive — exit"
    exit 0
  fi

  $PY "$HALO_SYS/python/halo_planner.py" --repo "$ROOT" --halo-system "$HALO_SYS" || true

  $PY -c "
import json, os
from pathlib import Path
from datetime import datetime, timezone
root = Path(r'''$ROOT''')
rec = None
pl = root / '.halo' / 'plan-latest.json'
if pl.exists():
    try:
        rec = json.loads(pl.read_text()).get('recommendation')
    except Exception:
        pass
(root / '.halo' / 'logs' / 'watchdog-heartbeat.json').write_text(
    json.dumps({
        'at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'pid': $$,
        'ok': True,
        'recommendation': rec,
    }, indent=2) + '\n'
)
" || true

  $PY "$HALO_SYS/python/halo_drive.py" --repo "$ROOT" --halo-system "$HALO_SYS" spawn 2>/dev/null || true

  sleep "$SLEEP"
done
