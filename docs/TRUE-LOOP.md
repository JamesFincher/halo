# Halo True Loop — Continuous Drive

## How to stop the loop

| What | How |
|------|-----|
| Halo loop + autonomous | `/stop-loop` or `halo go --off` or `halo loop-cancel` |
| Watchdog | `pkill -f halo-watchdog` |
| Grok TUI `/loop` | Ctrl+B tasks pane → delete, or `scheduler_delete <id>` |
| Global Stop hook | Harmless if `loop.json` is inactive |

## Core mechanism

```
agent works → Stop event → hooks/halo-stop-loop.sh
  → if loop.json active → refresh NEXT_PROMPT.md
  → stdout: { "decision": "block", "reason": <NEXT_PROMPT> }
  → harness re-injects reason as next user message
  → loop
```

On Grok Build, `Stop` is passive; `decision:block` is best-effort. The reliable continue path is headless spawn.

## Continuous modes

| Mode | Latency | Same chat? | Command |
|------|---------|------------|---------|
| Headless chain | Immediate on turn end | No | `halo go` (default spawn) |
| Watchdog | ~15s | No | `halo watchdog . 15` |
| Planner | On demand | N/A | `halo plan .` |
| TUI `/loop` | ≥60s | Yes | Only if you want same-session inject |

## Engineered inject

`python/halo_next_prompt.py` rebuilds `NEXT_PROMPT.md` each turn from:

- `state.json`
- `baton.md`
- `autonomous-log.md`
- `readiness.json`
- `STORIES.md` / milestones index
- `evidence/`
- `git status/log`
- Stop hook `transcript_path` (last assistant text)
- `loop.json` iteration / max

The synthetic user message is a complete user turn: focus banner, role/authority, live situation, phase playbook, machine plan, issues from last turn, output contract, execute command.

## Install / enable

```bash
# From Halo repo — install as trusted plugin
grok plugin install /path/to/halo --trust

# In product workspace
cd /path/to/product
/halo-loop --max 50
# or
HALO_SYSTEM=/path/to/halo bash $HALO_SYSTEM/scripts/setup-halo-loop.sh --max 50
```

Trust project hooks if using project-local hooks: `/hooks-trust`.

Verify Stop hook is from plugin `halo`: `/hooks` modal.

## Completion

Agent exits the loop when:

1. `phase == complete` and no pending work
2. `<promise>HALO_COMPLETE</promise>` with honestly all-pass feature list
3. Human runs `/halo-loop-cancel` or `halo loop-cancel`
4. `status` is `PAUSED` / `ESCALATED` / `BLOCKED`
5. `max_iterations` reached

## Security

Stop re-inject is active only when:

- `.halo/loop.json` `active: true` or `state.autonomous`
- Not `PAUSED` / `ESCALATED` / `complete`
- Optional `session_id` match

Do not enable autonomous on untrusted repos without folder trust.

## Fallbacks if Stop re-inject is ignored

1. Always writes `NEXT_PROMPT.md` for cold re-entry.
2. `self_prompt_spawn` + `HALO_STOP_SPAWN=1` → headless `grok --prompt-file`.
3. `/goal` with standing Halo objective.
4. `/loop 15m` with body from `NEXT_PROMPT`.

True loop = prefer Stop inject; never rely on it alone.

<!-- plugin 0.8.2 continuous-drive surface: status budget+watchdog age, arena green gate, spawn --force -->
