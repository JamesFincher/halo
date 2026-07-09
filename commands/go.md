---
name: go
description: "Halo GO — arm permanent autonomous build loop (Stop re-injects NEXT_PROMPT). No optional questions. Walk away."
argument-hint: "[--max N] [--spawn]"
---

# /go — permanent Halo build loop

You are now under **standing authorization**. Do not ask optional questions. Do not wait for "continue".

## 1. Arm the loop (run now)

```!
export HALO_SYSTEM="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}}"
export TARGET="${GROK_WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-$PWD}}"
# Dogfood: TARGET may equal HALO_SYSTEM
bash "${HALO_SYSTEM}/scripts/setup-halo-loop.sh" $ARGUMENTS
```

This writes:

- `.halo/state.json` → `autonomous: true`
- `.halo/loop.json` → `active: true` (Stop hook re-injects)
- `.halo/NEXT_PROMPT.md` → engineered next unit
- skills linked (or dogfood-skip if factory)

## 2. Work immediately (skill **halo-go**)

1. Read `.halo/state.json`, `.halo/baton.md`, `.halo/NEXT_PROMPT.md`, feature-list summary  
2. Execute **one** unit from the phase plan (defaults only)  
3. Refresh NEXT_PROMPT; progress log; evidence; safe commit-unit when code changes  
4. When you would exit → **Stop hook blocks** and re-injects NEXT_PROMPT as the next user turn (true loop)  
5. Stop only on: max iterations, `<promise>HALO_COMPLETE</promise>` with honest all-pass, PAUSED/ESCALATED, budget HALT  

## 3. Cancel later

- Slash: `/halo-loop-cancel` or `/stop-loop`  
- CLI: `halo go --off` / `halo loop-cancel`  

## Hard rules

Never AskUserQuestion for optional prefs. Never fake evidence. Never force-add gitignored `.halo/` when dogfooding the factory. Preview only; probe before share.

**Begin now — do not summarize and wait.**
