---
name: halo-go
description: Alias for /go — continuous autonomous drive (Grok headless + optional /loop).
argument-hint: "[--max N] [--no-spawn]"
---

# /halo-go → same as /go

```!
export HALO_SYSTEM="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}}"
export TARGET="${GROK_WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-$PWD}}"
cd "$TARGET"
bash "${HALO_SYSTEM}/scripts/setup-halo-loop.sh" $ARGUMENTS
```

Grok **Stop is passive** — continuous work uses **headless spawn**, not decision:block alone.  
Load skill **halo-go**, execute `.halo/NEXT_PROMPT.md`, do not wait for the human.
