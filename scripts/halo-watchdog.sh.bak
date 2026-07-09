#!/usr/bin/env bash
# Continuous drive without the 60s Grok /loop floor.
# Runs planner (refresh NEXT_PROMPT) then ensures a headless builder is alive.
# Usage: halo-watchdog.sh [repo] [sleep_seconds]
# Stop: kill the watchdog PID or: halo go --off && pkill -f halo-watchdog
set -euo pipefail
HALO_SYS="${HALO_SYSTEM:-$(cd "$(dirname "$0")/.." && pwd)}"
ROOT="$(cd "${1:-.}" && pwd)"
SLEEP="${2:-15}"  # default 15s — much faster than Grok /loop 60s min
export HALO_SYSTEM="$HALO_SYS"
export PYTHONPATH="${HALO_SYS}/python${PYTHONPATH:+:$PYTHONPATH}"
PY="${PYTHON:-python3}"
cd "$ROOT"

echo "[watchdog] root=$ROOT sleep=${SLEEP}s  stop: halo go --off; kill $$"

while true; do
  # stop if loop disarmed
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

  # planner always refreshes NEXT_PROMPT + baton
  $PY "$HALO_SYS/python/halo_planner.py" --repo "$ROOT" --halo-system "$HALO_SYS" || true

  # ensure headless builder running
  $PY "$HALO_SYS/python/halo_drive.py" --repo "$ROOT" --halo-system "$HALO_SYS" spawn 2>/dev/null || true

  sleep "$SLEEP"
done
