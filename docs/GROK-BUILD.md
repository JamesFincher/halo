# Halo × Grok Build — Code Structure & Self-Prompt

How Halo maps onto **Grok Build** (xAI CLI / TUI) so autonomous mode can **self-prompt** without a human in the loop.

Sources: local `~/.grok/docs/user-guide/` (skills, headless, background tasks, slash commands), [docs.x.ai/build](https://docs.x.ai/build/overview).

---

## 1. Grok Build layout (what we align to)

| Grok concept | Path / mechanism | Halo equivalent |
|--------------|------------------|-----------------|
| Project rules | `AGENTS.md` (walk-up) | System `AGENTS.md` + product template |
| Skills | `.grok/skills/<name>/SKILL.md` | All `halo-*` skills |
| Plugin / marketplace | `.grok-plugin/`, `grok plugin install` | This repo as installable plugin |
| Headless one-shot | `grok -p "…"` / `--prompt-file` | `halo continue` / self-prompt spawn |
| Goal mode | `/goal <objective>` + `update_goal` tool | `halo go` + standing objective text |
| Recurring prompt | `/loop <interval> <prompt>` / scheduler | `halo loop` / `self_prompt_mode: loop` |
| Session continue | `grok -c` / `-r <id>` | Resume + baton + NEXT_PROMPT |
| Auto-approve | `--yolo` / `--always-approve` | Required for unattended headless |
| Max turns | `--max-turns N` | Bound one headless segment |
| Subagents | `spawn_subagent` / explore/plan | Future: verify Arena |
| Inspect | `grok inspect` | Discovery of skills/hooks |

### Skill discovery order (Grok)

1. `./.grok/skills/` (cwd → repo root walk)  
2. `~/.grok/skills/`  
3. Plugin skill dirs  
4. Compat: `.claude/skills`, `.cursor/skills`  

**Implication:** Product TARGET must see Halo skills via **plugin install** or **bootstrap copy** into `TARGET/.grok/skills/`. Self-prompt fails silently if the next session cannot load `halo-go`.

---

## 2. Self-prompt model (three modes)

```
┌─────────────────────────────────────────────────────────────┐
│  MODE A — INLINE (same session)                             │
│  Agent finishes unit → immediately continues phase driver   │
│  No process exit. Cap: autonomous_max_cycles.               │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  MODE B — HEADLESS RE-ENTRY (cross session / context)       │
│  Write .halo/NEXT_PROMPT.md → spawn:                        │
│    grok -p --prompt-file .halo/NEXT_PROMPT.md \             │
│         --cwd TARGET --yolo --max-turns N                   │
│  New process; loads AGENTS + skills; baton carries truth. │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│  MODE C — GOAL / LOOP (Grok-native long run)                │
│  /goal <halo-go standing objective>                         │
│  /loop 15m <continue prompt from NEXT_PROMPT.md>            │
│  scheduler_create for durable poll                          │
└─────────────────────────────────────────────────────────────┘
```

Default under `halo go`: **A then B**.  
- Within one invocation: inline loop.  
- When max cycles / context risk: write NEXT_PROMPT + optional headless spawn if `self_prompt_spawn: true`.

---

## 3. NEXT_PROMPT contract

File: `TARGET/.halo/NEXT_PROMPT.md`

Must be a **complete user message** a cold Grok session can execute alone:

1. Load skill `halo-go` (autonomous on).  
2. TARGET path.  
3. Read state + baton + autonomous-log.  
4. Execute `halo go --plan` next actions without asking.  
5. Hard stops list.  
6. End by regenerating NEXT_PROMPT or clearing if complete.

Generator: `python/halo_next_prompt.py`  
CLI: `halo continue` (print path) · `halo continue --spawn` (run grok if available)

---

## 4. Standing /goal text (copy-paste)

```
Standing goal: Run Halo autonomous product factory on this repo.
Load skill halo-go. State.autonomous must stay true.
Never AskUserQuestion for optional decisions. Use defaults.
Drive phases: intake→specs→lock→ready(degrade ok)→scaffold→build cycles.
After each unit update .halo/baton.md and .halo/NEXT_PROMPT.md.
Live probe before any deploy URL. No production deploy.
Stop only: PAUSED, ESCALATED, kill switch, denylist, true BLOCKED.
When max_cycles hit, write NEXT_PROMPT and stop cleanly (headless will re-enter).
```

---

## 5. Headless recipe

```bash
export HALO_SYSTEM=~/code/halo   # or install path
export TARGET=/path/to/product

# Ensure skills visible in TARGET
"$HALO_SYSTEM/scripts/halo" link-skills "$TARGET"

"$HALO_SYSTEM/scripts/halo" go "$TARGET"
"$HALO_SYSTEM/scripts/halo" continue "$TARGET" --write
"$HALO_SYSTEM/scripts/halo" continue "$TARGET" --spawn
```

`continue --spawn` runs approximately:

```bash
grok -p --prompt-file "$TARGET/.halo/NEXT_PROMPT.md" \
  --cwd "$TARGET" \
  --yolo \
  --max-turns 80 \
  --output-format plain
```

If `grok` missing: write NEXT_PROMPT only; human/CI invokes later.

---

## 6. /loop recipe (TUI)

```
/loop 20m Read .halo/NEXT_PROMPT.md and .halo/state.json. If autonomous and not complete, execute skill halo-go one unit. Never ask. Update baton and NEXT_PROMPT.
```

---

## 7. Failure modes

| Failure | Fix |
|---------|-----|
| Next session ignores halo-go | link-skills / plugin install; NEXT_PROMPT must name skill |
| Headless hangs on permissions | `--yolo` / `bypassPermissions` |
| Infinite headless spawn | max_cycles + `self_prompt_spawn` only when status ACTIVE and not complete |
| Skills not found in product | `halo link-skills` copies or symlinks |
| Context blowup | max_turns + compact; prefer headless re-entry over infinite inline |

---

## 8. Alignment checklist for Halo changes

When adding a phase or skill:

1. Discoverable under `.grok/skills/`  
2. Named in `halo-go` phase driver  
3. Appears in `NEXT_PROMPT` generator plan  
4. CLI verb if control-plane  
5. Documented in WORKFLOWS.md + this file if Grok-specific  

---

**Version:** 1.0 · ties to Halo v0.4+
