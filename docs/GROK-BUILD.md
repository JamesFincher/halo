# Halo × Grok Build

## Grok concept map

| Grok concept | Path / mechanism | Halo equivalent |
|--------------|------------------|-----------------|
| Project rules | `AGENTS.md` | `AGENTS.md` + product template |
| Skills | `.grok/skills/<name>/SKILL.md` | `halo-*` skills |
| Plugin | `.grok-plugin/`, `grok plugin install` | This repo as plugin |
| Headless one-shot | `grok -p` | `halo continue` / self-prompt spawn |
| Goal mode | `/goal` | `halo go` + standing objective |
| Recurring prompt | `/loop` (if documented by your TUI) | `halo watchdog` (supervisor) |
| Auto-approve | `/hooks-trust` or `--trust` | Required for project hooks to run |
| Max turns | `--max-turns` if supported | `max_iterations` in `loop.json` |

## Skill discovery order

1. `./.grok/skills/` (cwd → repo root walk)
2. `~/.grok/skills/`
3. Plugin skill dirs
4. Compat: `.claude/skills`, `.cursor/skills`

Product TARGET must see Halo skills via plugin install or `halo link-skills`.

## Continuous drive (Stop is passive)

On Grok Build, **only `PreToolUse` can block**. `Stop` is **passive**; `decision:block` + `reason` is best-effort and ignored for continuity.

```
agent works → Stop event (passive) → hooks/halo-stop-loop.sh
  → if .halo/loop.json active and no .halo/OFF
  → spawn headless: grok -p "$(cat .halo/NEXT_PROMPT.md)" --always-approve --no-auto-update --output-format streaming-json
  → next process loads skill halo-go and executes one unit
```

The primary supervisor is the watchdog: `halo watchdog . 15`.

Slash: `/halo-loop` (arm) · CLI: `halo loop` · Cancel: `/halo-loop-cancel` (sets `.halo/OFF`).

## Self-prompt modes

- **A — Inline**: same session, continue phase driver, cap `autonomous_max_cycles`.
- **B — Headless re-entry**: `halo continue --spawn` runs `grok -p "$(cat .halo/NEXT_PROMPT.md)" --always-approve --no-auto-update --output-format streaming-json`.
- **C — Goal / optional `/loop`**: `/goal <standing>` or a same-session inject command if your TUI documents one.

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

## Watchdog recipe

```bash
halo watchdog . 15
```

## Optional same-session TUI inject

Only if your TUI documents a stable command. Otherwise prefer headless or watchdog. Do not invent `scheduler_create`, `scheduler_list`, or `scheduler_delete`.

## Failure modes

| Failure | Fix |
|---------|-----|
| Next session ignores halo-go | `link-skills` / plugin install |
| Headless hangs on permissions | `/hooks-trust` or `grok --trust` + `XAI_API_KEY` for non-interactive |
| Infinite headless spawn | `max_cycles` + `self_prompt_spawn` only when ACTIVE |
| Skills not found | `halo link-skills` |
| Context blowup | `max_iterations` + compact |

## Alignment checklist

When adding a phase or skill:

1. Discoverable under `.grok/skills/`
2. Named in `halo-go` phase driver
3. Appears in `NEXT_PROMPT` generator plan
4. CLI verb if control-plane
5. Documented in `WORKFLOWS.md` and this file if Grok-specific
