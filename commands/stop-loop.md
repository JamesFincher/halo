---
name: stop-loop
description: Disarm Halo permanent build loop (alias for /halo-loop-cancel).
---

# /stop-loop

```!
export HALO_SYSTEM="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}}"
bash "${HALO_SYSTEM}/scripts/cancel-halo-loop.sh"
```

Confirm loop inactive; do not continue autonomous work unless human says go again.
