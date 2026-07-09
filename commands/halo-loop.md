---
name: halo-loop
description: Arm Halo continuous build drive. Stop is passive on Grok — re-entry is headless spawn/supervisor, not decision:block.
argument-hint: "[--max N] [--spawn]"
---

# /halo-loop — arm continuous drive (Grok)

## Grok constraint (do not ignore)

On Grok Build, **only `PreToolUse` can block**. `Stop` hooks are **passive**: Ralph-style `decision:block` + `reason` does **not** prevent exit or re-inject a prompt into the same turn. Continuity = **headless / supervisor** re-entry using `.halo/NEXT_PROMPT.md`.

## 1. Arm

```!
export HALO_SYSTEM="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}}"
export TARGET="${GROK_WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-$PWD}}"
cd "$TARGET"
bash "${HALO_SYSTEM}/scripts/setup-halo-loop.sh" $ARGUMENTS
```

Setup should: write `.halo/loop.json` + baton + self-contained `NEXT_PROMPT.md`, clear `OFF`, enable `autonomous`, install/refresh Stop (+ optional StopFailure) hook and/or watchdog, respect `--max N`.

Project hooks: if hooks live under the repo, user needs `/hooks-trust` or `grok --trust` once (see hooks).

## 2. Work now (do not wait for the human)

- Read `.halo/state.json`, `.halo/baton.md`, `.halo/NEXT_PROMPT.md`
- Execute one unit from the phase plan (defaults only)
- Refresh baton + self-contained `NEXT_PROMPT.md` for the next process
- When this turn ends, Stop is passive — the armed hook/watchdog continues drive via headless spawn (or external supervisor), not via blocking Stop
- Stop conditions: max iterations, phase complete, PAUSED / ESCALATED / kill switch (`.halo/OFF` or cancel)
- Output `<promise>HALO_COMPLETE</promise>` only when phase is complete or no pending work remains

Do not claim Stop “blocks exit”. Do not wait for confirmation. Work now.
