# Halo × Grok Build

## Grok concept map

| Grok concept | Path / mechanism | Halo equivalent |
|--------------|------------------|-----------------|
| Project rules | `AGENTS.md` | `AGENTS.md` + product template |
| Skills | `.grok/skills/<name>/SKILL.md` | `halo-*` skills |
| Plugin | `.grok-plugin/`, `grok plugin install` | This repo as plugin |
| Headless one-shot | `grok -p` / `--prompt-file` | `halo continue` / self-prompt spawn |
| Goal mode | `/goal` + `update_goal` | `halo go` + standing objective |
| Recurring prompt | `/loop` / scheduler | `halo loop` / `self_prompt_mode: loop` |
| Auto-approve | `--yolo` / `--always-approve` | Required for unattended headless |
| Max turns | `--max-turns N` | Bound one headless segment |

## Skill discovery order

1. `./.grok/skills/` (cwd → repo root walk)
2. `~/.grok/skills/`
3. Plugin skill dirs
4. Compat: `.claude/skills`, `.cursor/skills`

Product TARGET must see Halo skills via plugin install or `halo link-skills`.

## True session loop (Stop hook)

```
Stop event → hooks/halo-stop-loop.sh
  → if .halo/loop.json active
  → stdout: { "decision": "block", "reason": <NEXT_PROMPT text> }
  → harness re-injects reason as next user message
```

Slash: `/halo-loop` · CLI: `halo loop` · Cancel: `/halo-loop-cancel`.

## Self-prompt modes

- **A — Inline**: same session, continue phase driver, cap `autonomous_max_cycles`.
- **B — Headless re-entry**: `halo continue --spawn` runs `grok --prompt-file .halo/NEXT_PROMPT.md --cwd TARGET --always-approve --max-turns 80`.
- **C — Goal / Loop**: `/goal <standing>` or `/loop 15m <read NEXT_PROMPT>`.

Default under `halo go`: A then B.

## NEXT_PROMPT contract

`TARGET/.halo/NEXT_PROMPT.md` must be a complete user message a cold Grok session can execute:

1. Load skill `halo-go`.
2. TARGET path.
3. Read state + baton + autonomous-log.
4. Execute `halo go --plan` items without asking.
5. List hard stops.
6. Regenerate NEXT_PROMPT or clear if complete.

## Headless recipe

```bash
export HALO_SYSTEM=/path/to/halo
export TARGET=/path/to/product

# Ensure skills visible in TARGET
"$HALO_SYSTEM/scripts/halo" link-skills "$TARGET"

"$HALO_SYSTEM/scripts/halo" go "$TARGET"
"$HALO_SYSTEM/scripts/halo" continue "$TARGET" --write
"$HALO_SYSTEM/scripts/halo" continue "$TARGET" --spawn
```

## /loop recipe

```
/loop 20m Read .halo/NEXT_PROMPT.md and .halo/state.json. If autonomous and not complete, execute skill halo-go one unit. Never ask. Update baton and NEXT_PROMPT.
```

## Failure modes

| Failure | Fix |
|---------|-----|
| Next session ignores halo-go | `link-skills` / plugin install |
| Headless hangs on permissions | `--always-approve` / `bypassPermissions` |
| Infinite headless spawn | `max_cycles` + `self_prompt_spawn` only when ACTIVE |
| Skills not found | `halo link-skills` |
| Context blowup | `max_turns` + compact |

## Alignment checklist

When adding a phase or skill:

1. Discoverable under `.grok/skills/`
2. Named in `halo-go` phase driver
3. Appears in `NEXT_PROMPT` generator plan
4. CLI verb if control-plane
5. Documented in `WORKFLOWS.md` and this file if Grok-specific
