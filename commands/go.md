---
name: go
description: "Halo GO — continuous autonomous build. Grok-native headless drive (Stop is passive on Grok)."
argument-hint: "[--max N] [--no-spawn]"
---

# /go — continuous Halo build

## Why you used to have to re-message

Grok Build **Stop hooks are passive** (docs: only `PreToolUse` blocks).  
Ralph `decision:block` + `reason` works on Claude Code; **Grok ignores the block**.  
Halo can either **headless-spawn** each turn via `grok --no-auto-update --prompt-file .halo/NEXT_PROMPT.md --cwd . --always-approve --output-format streaming-json --max-turns 1` or run the **ACP supervisor** (`HALO_ACP=1`) for a single long-lived `grok agent stdio` session.

## 1. Arm drive (run now)

```!
export HALO_SYSTEM="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}}"
export TARGET="${GROK_WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-$PWD}}"
cd "$TARGET"
bash "${HALO_SYSTEM}/scripts/setup-halo-loop.sh" $ARGUMENTS
```

## 2. Work now (skill halo-go)

1. Read baton + NEXT_PROMPT + feature-list  
2. Execute **one** unit  
3. Refresh NEXT_PROMPT; when you stop, drive continues via headless re-entry or supervisor

## Cancel

`/stop-loop` · `halo go --off` · `halo loop-cancel`

**Begin work immediately. Do not wait for another human message.**
