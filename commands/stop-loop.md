---
name: stop-loop
description: Disarm Halo permanent build loop (alias for /halo-loop-cancel).
---

# /stop-loop — kill continuous drive

```!
export HALO_SYSTEM="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}}"
export TARGET="${GROK_WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-$PWD}}"
cd "$TARGET"
bash "${HALO_SYSTEM}/scripts/cancel-halo-loop.sh"
# kill local watchdog if running
pkill -f "halo-watchdog.sh" 2>/dev/null || true
pkill -f "scripts/halo-watchdog" 2>/dev/null || true
```

Also cancel any Grok TUI `/loop` or scheduler jobs (they are separate from Halo loop.json):
- Tasks pane: `Ctrl+B` → delete the Halo drive scheduler
- Or agent: `scheduler_list` then `scheduler_delete` for the Halo prompt id

After this: autonomous=false, loop inactive, no headless spawn, no 60s injects.
