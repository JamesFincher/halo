---
name: halo-go
description: Alias for /go — Halo autonomous + permanent Stop-hook build loop.
argument-hint: "[--max N] [--spawn]"
---

# /halo-go → same as /go

Run the GO arming script, then operate under skill **halo-go** without asking.

```!
export HALO_SYSTEM="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}}"
bash "${HALO_SYSTEM}/scripts/setup-halo-loop.sh" $ARGUMENTS
```

Immediately load doctrine from skill `halo-go` and execute `.halo/NEXT_PROMPT.md`. True loop = Stop re-inject until complete/cancel/budget.
