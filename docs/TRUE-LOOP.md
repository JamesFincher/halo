# Halo True Loop — Continuous Drive

## How to stop the loop

| What | How |
|------|-----|
| Halo loop + autonomous | `/stop-loop` or `halo go --off` or `halo loop-cancel` (sets `.halo/OFF`) |
| Watchdog | `pkill -f halo-watchdog` |
| Grok TUI `/loop` (optional) | manually delete from Tasks pane if you created one |
| Global Stop hook | Harmless if `loop.json` is inactive or `.halo/OFF` exists |

## Core mechanism

On Grok Build, **Stop is passive** (only `PreToolUse` can block). `decision:block` + `reason` is **best-effort** and is not the continue path.

```
agent works → Stop event (passive) → hooks/halo-stop-loop.sh
  → if loop.json active and no .halo/OFF → spawn headless or signal watchdog
  → headless: grok --no-auto-update --prompt-file .halo/NEXT_PROMPT.md --cwd . --always-approve --output-format streaming-json --max-turns 1
  → next process loads skill halo-go and executes one unit
```

The reliable continue path is **headless re-entry** or a **single watchdog supervisor** (`halo watchdog . 15`).

## Continuous modes

| Mode | Latency | Same chat? | Command |
|------|---------|------------|---------|
| Watchdog (supervisor) | ~15s | No | `halo watchdog . 15` |
| Headless chain | On turn end | No | `halo continue --spawn` |
| Stop hook fallback | Immediate on turn end | No | `hooks/halo-stop-loop.sh` |
| Planner | On demand | N/A | `halo plan .` |
| TUI `/loop` | ≥60s | Yes | Only if your TUI documents a stable inject command |

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
3. Human runs `/halo-loop-cancel` or `halo loop-cancel` (sets `.halo/OFF`)
4. `status` is `PAUSED` / `ESCALATED` / `BLOCKED`
5. `max_iterations` reached

## Security

Stop re-inject / headless spawn is active only when:

- `.halo/loop.json` `active: true` or `state.autonomous`
- No `.halo/OFF` kill switch
- Not `PAUSED` / `ESCALATED` / `complete`
- Optional `session_id` match

Do not enable autonomous on untrusted repos without folder trust.

## Fallbacks if Stop re-inject is ignored

1. Always writes `NEXT_PROMPT.md` for cold re-entry.
2. `self_prompt_spawn` + `HALO_STOP_SPAWN=1` → headless `grok --no-auto-update --prompt-file .halo/NEXT_PROMPT.md --cwd . --always-approve --output-format streaming-json --max-turns 1`.
3. Watchdog (`halo watchdog`) ensures re-spawn even if the Stop hook is missed.
4. `/goal` with standing Halo objective.

True loop = prefer **ACP supervisor** (`HALO_ACP=1 halo watchdog .`) or watchdog supervisor; Stop hook is a fallback; never rely on blocking Stop.

<!-- plugin 0.8.2 continuous-drive surface: status budget+watchdog age, arena green gate, spawn --force -->
