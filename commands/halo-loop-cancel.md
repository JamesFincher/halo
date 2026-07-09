---
name: halo-loop-cancel
description: Cancel active Halo continuous drive (allows normal agent stop).
---

# /halo-loop-cancel

```!
export HALO_SYSTEM="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}}"
export TARGET="${GROK_WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-$PWD}}"
cd "$TARGET"
bash "${HALO_SYSTEM}/scripts/cancel-halo-loop.sh"
pkill -f "halo-watchdog.sh" 2>/dev/null || true
pkill -f "scripts/halo-watchdog" 2>/dev/null || true
```

Loop disarmed (kill switch + `autonomous=false`). You may stop normally. Headless children already running may finish their current turn; they must not re-arm if `OFF` is set.
