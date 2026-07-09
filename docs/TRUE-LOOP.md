# Halo True Loop — Continuous Drive

## How to STOP the loop

| What | How |
|------|-----|
| Halo loop + autonomous | `/stop-loop` or `halo go --off` or `halo loop-cancel` |
| Watchdog (15s planner+spawn) | `pkill -f halo-watchdog` |
| Grok TUI `/loop` / scheduler (60s min) | `Ctrl+B` tasks pane → delete · or `scheduler_delete <id>` |
| Global Stop hook still runs | Harmless if `loop.json` inactive (exits immediately) |

## Why the “one minute” wait happened

Grok’s **`/loop` / `scheduler_create` minimum interval is 60 seconds**.  
We created a 60s scheduler so the **same TUI chat** got synthetic turns. That felt slow and spammy.

**Better continuous modes (use these):**

| Mode | Latency | Same chat? | Command |
|------|---------|------------|---------|
| **Headless chain** | Immediate on turn end | No (background agent) | `/go` (default spawn) |
| **Watchdog** | ~15s (configurable) | No | `halo watchdog . 15` |
| **Planner only** | On demand | N/A | `halo plan .` |
| **TUI /loop** | ≥60s | Yes | Only if you want same-session inject |

## Planner (background study → NEXT_PROMPT)

`python/halo_planner.py` / `halo plan .`:

- Reads state, feature-list, git log, dirty factory files  
- Writes `.halo/plan-latest.json` + baton recommendation  
- Regenerates `.halo/NEXT_PROMPT.md` with a **RECOMMENDATION** banner  

Watchdog = planner every N seconds + ensure headless builder alive.  
That is the “always studying the repo / shaping next prompt” path — deterministic study today; can be upgraded to a dedicated LLM planner headless pass later.

## Root cause (2026-07): why "armed" still needed a human message

**Grok Build official hooks docs:** only `PreToolUse` is blocking. **`Stop` is passive.**

Ralph `decision:block` works on Claude Code; Grok ignores it for re-prompt.

### Fix (current)

| Path | Role |
|------|------|
| **Headless spawn** | On Stop + `/go`: `grok --prompt-file NEXT_PROMPT --always-approve` |
| **Watchdog** | Planner + spawn every 15s (no 60s floor) |
| **Planner** | Refresh NEXT_PROMPT from live repo study |
| **TUI /loop** | Optional; min 60s — avoid for dogfood thrash |
| Ralph JSON | Still emitted for Claude hosts |

---


This is the **core loop mechanism**: how Halo makes Grok Build (and Claude Code) keep working **as if the user typed the next message**, without the human being present.

---

## The discovery

### What does *not* work as “intercept last message”

| Approach | Why not |
|----------|---------|
| Skill alone | Skills only run when the model chooses them or user slash-invokes |
| Rewrite chat history | No public API for plugins to mutate transcript mid-session |
| Passive `Stop` stdout (Grok docs) | Official docs: only `PreToolUse` is blocking; other hooks “passive” |

### What *does* work (proven in the wild)

#### 1. **Stop hook + `decision: block` + `reason` = next user prompt** (Ralph Wiggum / Claude Code)

Anthropic’s Ralph Loop plugin (loaded via Grok marketplace cache as Claude-compatible) does this:

```bash
# On Stop event, if loop active:
jq -n --arg prompt "$PROMPT_TEXT" '{
  "decision": "block",
  "reason": $prompt,
  "systemMessage": "iteration N"
}'
```

- **`decision: "block"`** — prevent the agent from ending the turn/session  
- **`reason`** — text **fed back as the next user input**  
- Files hold durable state; the **prompt text** can be fixed (Ralph) or **dynamic** (Halo NEXT_PROMPT)

Grok Build claims full Claude Code hook compatibility and loads `~/.claude` / marketplace plugins. Official Grok docs underspecify Stop as non-blocking for *tools*, but the **Ralph protocol is the de-facto “true loop”** across agent CLIs. Halo implements it and degrades gracefully if a build ignores `block` (see fallbacks).

#### 2. **Grok-native injectors** (from binary / docs)

| Signal | Behavior |
|--------|----------|
| `scheduler_create` / `/loop` | `Scheduled task fired, injecting prompt into session` |
| Background task complete | `auto-wake: injecting synthetic prompt` |
| Monitor events | `Monitor event received, injecting into session` |
| Hook `asyncRewake` + `rewakeMessage` | Security plugin pattern: rewake agent after async hook |
| `/goal` + `update_goal` | Multi-turn standing objective inside one session |

These are **platform-injected user turns**, not skill fiction.

#### 3. **Headless re-entry**

```bash
grok --prompt-file .halo/NEXT_PROMPT.md --cwd TARGET --always-approve --max-turns 80
```

Do **not** use `grok -p --prompt-file` (`-p/--single` requires a prompt string and breaks). New process; that file **is** the user message. Reliable always.

---

## Halo architecture for the true loop

```
                 ┌──────────────────────────────┐
  human: /halo-loop  or  halo go
                 └────────────┬─────────────────┘
                              ▼
                 .halo/loop.json  active=true
                 .halo/state.json autonomous=true
                 .halo/NEXT_PROMPT.md  (dynamic plan)
                              │
              agent works (skill halo-go)
                              │
                              ▼
                    turn ends → Stop event
                              │
              hooks/halo-stop-loop.sh
                              │
              ┌───────────────┼───────────────┐
              │ loop inactive │ loop active   │
              ▼               ▼               │
           exit 0      refresh NEXT_PROMPT    │
           (allow stop)      │                │
                             ▼                │
                    stdout JSON:              │
                    decision=block            │
                    reason=<NEXT_PROMPT>      │
                             │                │
                             ▼                │
                    harness injects reason    │
                    as next user message      │
                             │                │
                             └──────► loop ───┘
```

### Files

| Path | Role |
|------|------|
| `hooks/hooks.json` | Register `Stop` + `SessionStart` |
| `hooks/halo-stop-loop.sh` | Ralph-compatible re-inject |
| `hooks/halo-session-start.sh` | Soft reminder if loop active |
| `commands/halo-loop.md` | Slash start |
| `commands/halo-loop-cancel.md` | Slash stop |
| `scripts/setup-halo-loop.sh` | Arm loop.json + autonomous |
| `scripts/cancel-halo-loop.sh` | Disarm |
| `.halo/loop.json` | iteration, max, active, session_id |
| `.halo/NEXT_PROMPT.md` | **The injected “user” text** |

### Prompt engineering each inject

Every Stop re-builds `.halo/NEXT_PROMPT.md` via `halo_next_prompt.py` — **not** a static string.

### Inputs assembled

| Source | Use |
|--------|-----|
| `state.json` | phase, status, readiness, story, demo URL, autonomous flags |
| `intake` | purpose, features, stack |
| `baton.md` tail | handoff landmines |
| `autonomous-log.md` tail | prior decisions |
| `readiness.json` | blocking gaps |
| `STORIES.md` / milestones index | pending work list |
| `evidence/` | recent cert filenames |
| `git status/log` | dirty tree + recent commits |
| Stop hook `transcript_path` | last assistant text (detect "should I?", errors) |
| `loop.json` | iteration / max |

### Structure of synthetic user message

1. **Focus banner** — one primary action (`THIS TURN ONLY`)  
2. **Role/authority** — halo-go, no questions, hard stops  
3. **Live situation table** — product, phase, readiness, git  
4. **Phase playbook** — mission / do / don't / done_when / artifacts (per phase)  
5. **Machine plan** — from `halo go --plan`  
6. **Issues from last turn** — anti-regression (asked human, 404, etc.)  
7. **Output contract** — log, baton, refresh NEXT_PROMPT, optional promise  
8. **Execute** — start with primary action  

Phase playbooks live in `PHASE_PLAYBOOK` inside `python/halo_next_prompt.py` (intake / readiness / scaffold / build / complete).

History: `.halo/prompt-history/NEXT_*.md` (last 20) for debug.

### Goal of engineering

| Bad inject | Good inject |
|------------|-------------|
| Generic "continue halo" | "THIS TURN ONLY: RED test for S003 login" |
| Re-explain whole product | Cite pending story + baton landmine |
| Ignore last failure | "Previous turn mentioned probe fail — fix first" |
| Multi-story sprawl | One unit done_when |

---

## Completion

Agent may only exit the loop when:

1. `phase == complete` / no pending work → Stop hook sees inactive or promise, or  
2. Model outputs `<promise>HALO_COMPLETE</promise>` (optional check — currently max_iter + state gates), or  
3. Human runs `/halo-loop-cancel`, or  
4. `status` PAUSED / ESCALATED, or  
5. `max_iterations` reached  

---

## Install / enable

```bash
# From Halo repo — install as trusted plugin
grok plugin install /Users/james/code/halo --trust

# In product workspace
cd /path/to/product
/halo-loop --max 50
# or
HALO_SYSTEM=/Users/james/code/halo bash $HALO_SYSTEM/scripts/setup-halo-loop.sh --max 50
```

Trust project hooks if using project-local hooks: `/hooks-trust`.

Verify: `/hooks` modal → Stop hook from plugin **halo**.

---

## Fallbacks if Stop re-inject is ignored

Grok docs claim Stop is non-blocking. If your build ignores `decision:block`:

1. **Always** still writes `NEXT_PROMPT.md` (cold start ready)  
2. Set `self_prompt_spawn` + `HALO_STOP_SPAWN=1` → headless `grok -p` on Stop  
3. Use `/goal` with standing Halo objective  
4. Use `/loop 15m` with body from NEXT_PROMPT  

True loop = **prefer Stop inject**; **never rely on it alone**.

---

## Security

Stop re-inject is powerful. Only active when:

- `.halo/loop.json` `active: true` **or** `state.autonomous`  
- Not PAUSED / ESCALATED / complete  
- Optional `session_id` match  

Do not enable autonomous on untrusted repos without folder trust.

---

## Relation to earlier Halo “self-prompt”

| Layer | Mechanism |
|-------|-----------|
| L0 skill discipline | Inline continue (no stop) |
| L1 NEXT_PROMPT file | Cold / headless user message |
| L2 **Stop hook** | **Same-session inject (this doc)** |
| L3 goal / loop / scheduler | Platform inject |

**L2 is the answer to “intercept last message and prompt.”**  
Technically: intercept **stop**, not the previous user message; replace the *next* user turn.

---

**Version:** 1.0

<!-- plugin 0.8.2 continuous-drive surface: status budget+watchdog age, arena green gate, spawn --force -->
