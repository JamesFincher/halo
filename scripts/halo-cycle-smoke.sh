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

echo "[cycle-smoke] 3/4 dogfood hygiene (denylist + gitignore)"
# D044: fail if tracked denylist paths (dogfood control plane + secret patterns)
python3 "$HALO_SYS/python/halo_denylist.py" check-tracked --repo "$ROOT" || {
  echo "[cycle-smoke] FAIL: denylist paths in git ls-files" >&2
  exit 2
}
if git -C "$ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$ROOT" check-ignore -q .halo/state.json || {
    echo "[cycle-smoke] FAIL: .halo/ not gitignored" >&2
    exit 2
  }
fi

echo "[cycle-smoke] 4/4 features summary"
python3 "$HALO_SYS/python/halo_features.py" summary --repo "$ROOT" >/dev/null

EV="$ROOT/.halo/evidence"
mkdir -p "$EV"
cat > "$EV/D-cycle-smoke-latest.json" <<JSON
{"cert":"GREEN_TEST","feature":"cycle-smoke","exit_code":0,"ok":true,"at":"$(date -u +%Y-%m-%dT%H:%M:%SZ)"}
JSON
echo "[cycle-smoke] PASS (evidence $EV/D-cycle-smoke-latest.json)"
exit 0
