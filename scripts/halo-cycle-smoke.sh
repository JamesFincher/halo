#!/usr/bin/env bash
# Post-unit smoke for Halo factory dogfood. Exit 0 = unit may mark evidence green.
set -euo pipefail
HALO_SYS="${HALO_SYSTEM:-$(cd "$(dirname "$0")/.." && pwd)}"
ROOT="$(cd "${1:-.}" && pwd)"
export HALO_SYSTEM="$HALO_SYS"
export PYTHONPATH="${HALO_SYS}/python${PYTHONPATH:+:$PYTHONPATH}"
cd "$ROOT"

echo "[cycle-smoke] factory=$ROOT"
echo "[cycle-smoke] 1/4 py_compile"
python3 -m py_compile "$HALO_SYS"/python/*.py
if [[ -d "$HALO_SYS/python/scaffold" ]]; then
  python3 -m py_compile "$HALO_SYS"/python/scaffold/*.py
fi

echo "[cycle-smoke] 2/4 doctor --strict"
python3 "$HALO_SYS/python/halo_doctor.py" --halo-system "$HALO_SYS" --repo "$ROOT" --strict

echo "[cycle-smoke] 3/4 dogfood hygiene (no tracked .halo)"
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git -C "$ROOT" ls-files | grep -E '^\.halo/|^\.halo-archive/' ; then
    echo "[cycle-smoke] FAIL: dogfood paths tracked" >&2
    exit 2
  fi
  git -C "$ROOT" check-ignore -q .halo/state.json || {
    echo "[cycle-smoke] FAIL: .halo/ not gitignored" >&2
    exit 2
  }
fi

echo "[cycle-smoke] 4/4 features summary"
python3 "$HALO_SYS/python/halo_features.py" summary --repo "$ROOT" >/dev/null

echo "[cycle-smoke] PASS"
exit 0
