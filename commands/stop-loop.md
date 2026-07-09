---
name: stop-loop
description: Disarm Halo continuous build drive (alias for /halo-loop-cancel).
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

`cancel-halo-loop.sh` must:

- Set kill switch (`.halo/OFF` and/or `autonomous=false` in `.halo/loop.json` / `state.json`)
- Ensure Stop/watchdog paths no-op when `OFF`
- Not rely on TUI-only teardown

Optional (TUI only): if you started a same-session inject job, remove it from the Tasks pane (`Ctrl+B`) if present. Do not require undocumented `scheduler_*` tools for a successful cancel.

After this: autonomous off, no headless spawn, no watchdog. Normal agent stop is allowed.
