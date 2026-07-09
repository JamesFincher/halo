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
import os
import signal
from pathlib import Path
root = Path("$ROOT")
# D095: disarm loop + kill drive pid from lock if process still owned/alive
# Also set OFF kill switch so any headless children or Stop hooks stop immediately.
off_p = root / ".halo" / "OFF"
off_p.write_text("cancelled\n", encoding="utf-8")
for name in ("loop.json", "drive.lock", "state.json"):
    p = root / ".halo" / name
    if name == "loop.json" and p.exists():
        try:
            d = json.loads(p.read_text())
        except Exception:
            d = {}
        d["active"] = False
        d["stopped_reason"] = "cancel"
        p.write_text(json.dumps(d, indent=2) + "\n")
    elif name == "state.json" and p.exists():
        try:
            d = json.loads(p.read_text())
        except Exception:
            d = {}
        d["autonomous"] = False
        p.write_text(json.dumps(d, indent=2) + "\n")
    elif name == "drive.lock" and p.exists():
        try:
            d = json.loads(p.read_text())
            pid = int(d.get("pid") or 0)
            if pid:
                try:
                    os.kill(pid, signal.SIGTERM)
                    print(f"drive killed pid={pid}")
                except ProcessLookupError:
                    print(f"drive pid {pid} already dead")
                except PermissionError as e:
                    print(f"drive kill skipped: {e}")
        except Exception as e:
            print(f"drive lock parse: {e}")
        p.unlink(missing_ok=True)
print("Halo drive disarmed (OFF set, loop inactive, drive.lock cleared)")
print("Optional: if you manually created a TUI /loop inject, remove it from the Tasks pane")
# kill watchdog via pidfile (avoid pkill self-match)
wp = Path("$ROOT/.halo/logs/watchdog.pid")
if wp.exists():
    try:
        pid = int(wp.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        print(f"watchdog killed pid={pid}")
    except Exception as e:
        print(f"watchdog kill skipped: {e}")
    wp.unlink(missing_ok=True)
PY
