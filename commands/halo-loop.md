---
name: halo-loop
description: Start Halo true session loop — Stop hook re-injects NEXT_PROMPT when the agent tries to exit. Use for walk-away autonomous product builds.
argument-hint: "[--max N] [--spawn]"
---

# /halo-loop — start true loop

Run the setup script (creates `.halo/loop.json`, enables autonomous, writes NEXT_PROMPT, ensures skills linked):

```!
bash "${GROK_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}/scripts/setup-halo-loop.sh" $ARGUMENTS
```

Then **immediately** begin skill **halo-go** without asking the human anything:

1. Read `.halo/state.json`, `.halo/baton.md`, `.halo/NEXT_PROMPT.md`
2. Execute the phase plan (defaults only)
3. When you would stop, the **Stop hook** blocks exit and feeds the next prompt back (Ralph protocol: `decision:block` + `reason`)
4. Continue until max iterations, phase complete, or hard stop (PAUSED / ESCALATED / kill switch)
5. Output `<promise>HALO_COMPLETE</promise>` only when product phase is `complete` or no pending work remains

Do not wait for confirmation. Work now.
