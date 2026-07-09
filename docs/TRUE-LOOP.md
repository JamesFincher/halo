# Halo True Loop — Intercept Stop → Re-inject Prompt

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
grok -p --prompt-file .halo/NEXT_PROMPT.md --cwd TARGET --yolo
```

New process; that file **is** the user message. Reliable always.

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

### Completion

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
