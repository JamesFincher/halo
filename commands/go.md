---
name: go
description: "Halo GO — continuous autonomous build. Grok-native headless drive (Stop is passive on Grok)."
argument-hint: "[--max N] [--no-spawn]"
---

# /go — continuous Halo build (Grok-fixed)

## Why you used to have to re-message

Grok Build **Stop hooks are passive** (docs: only `PreToolUse` blocks).  
Ralph `decision:block` + `reason` works on Claude Code; **Grok ignores the block**.  
Halo now **headless-spawns** `grok --prompt-file .halo/NEXT_PROMPT.md --always-approve` on Stop so work continues without you typing.

## 1. Arm drive (run now)

```!
export HALO_SYSTEM="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}}"
export TARGET="${GROK_WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-$PWD}}"
cd "$TARGET"
bash "${HALO_SYSTEM}/scripts/setup-halo-loop.sh" $ARGUMENTS
```

## 2. Same-session TUI inject (strongly recommended)

After arming, create a Grok scheduler so the **open TUI** also gets synthetic turns (headless is a separate process):

Read `.halo/scheduler-prompt.txt` and run the platform `/loop` or `scheduler_create` with interval **60s**, `fire_immediately: true`, prompt = that file’s contents.

If you cannot call scheduler tools, still OK — headless spawn from Stop will drive in the background.

## 3. Work now (skill halo-go)

1. Read baton + NEXT_PROMPT + feature-list  
2. Execute **one** unit  
3. Refresh NEXT_PROMPT; when you stop, drive continues without the human  

## Cancel

`/stop-loop` · `halo go --off` · `halo loop-cancel`

**Begin work immediately. Do not wait for another human message.**
