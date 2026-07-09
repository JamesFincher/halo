---
name: halo-go
description: Autonomous build + self-prompt. Human said go / build without asking. Defaults only, never AskUserQuestion optional. Drives lifecycle and writes NEXT_PROMPT for Grok headless /goal /loop re-entry. Triggers go, just build, don't ask, autonomous, walk away, self-prompt.
---

# Halo Go — Autonomous + Self-Prompt (Grok Build native)

**Standing authorization.** Operate until hard stop. **Self-prompt** so work continues across turns and sessions without a human typing "continue".

Grok Build references: `docs/GROK-BUILD.md` in Halo system repo.

---

## Activation

Triggers: `go`, `just build`, `don't ask`, `autonomous`, `walk away`, `self-prompt`, `halo go`, `/halo-go`.

```bash
export HALO_SYSTEM="${HALO_SYSTEM:-/Users/james/code/halo}"
"$HALO_SYSTEM/scripts/halo" go "$TARGET"           # enable + link skills + NEXT_PROMPT
"$HALO_SYSTEM/scripts/halo" go "$TARGET" --spawn   # also set self_prompt_spawn
```

State flags:

```json
{
  "autonomous": true,
  "require_human_gate": false,
  "auto_defaults": true,
  "auto_lock_specs": true,
  "auto_degraded_ok": true,
  "self_prompt": true,
  "self_prompt_mode": "inline+headless",
  "self_prompt_spawn": false
}
```

---

## Continuous drive — core (Grok vs Claude)

Arm with **`/go`** or `halo go . --max 50` → `.halo/loop.json` active + headless drive.

### Grok Build (primary target)

**Stop hooks are passive** (only PreToolUse blocks). Ralph `decision:block` is **ignored**.

Real continue path:

1. **Headless spawn** (default ON): Stop runs `halo_drive.spawn_headless` →  
   `grok -p --prompt-file .halo/NEXT_PROMPT.md --cwd TARGET --yolo`
2. **Optional same-session TUI:** `/loop 60s` with text from `.halo/scheduler-prompt.txt`  
   (or agent `scheduler_create` interval `60s`, fire_immediately)

Disable spawn only with `halo go --no-spawn` / `HALO_NO_SPAWN=1` (then you must message).

### Claude-compatible hosts

Stop still emits Ralph JSON; host may re-inject `reason` as next user turn.

See `docs/TRUE-LOOP.md`. Cancel: `/stop-loop` / `halo loop-cancel`.

---

## Self-prompt protocol (mandatory under go)

After **every** completed unit (phase advance, story cycle, or hard stop check):

### 1. Inline (same session) — Mode A

If `self_prompt` and context remains and cycles < `autonomous_max_cycles`:

- **Do not stop to report and wait.**
- Immediately execute next item from `halo go --plan`.
- No "Should I continue?"

### 2. Refresh cold-start prompt — always

```bash
"$HALO_SYSTEM/scripts/halo" continue "$TARGET"
# writes $TARGET/.halo/NEXT_PROMPT.md
```

### 3. Headless re-entry — Mode B (when inline must end)

End inline when: max_cycles hit, context high, or session must exit **and** more work remains (`phase != complete`, status ACTIVE).

Then either:

```bash
"$HALO_SYSTEM/scripts/halo" continue "$TARGET" --spawn
```

or (equivalent):

```bash
grok -p --prompt-file "$TARGET/.halo/NEXT_PROMPT.md" \
  --cwd "$TARGET" --yolo --max-turns 80
```

Only spawn if `self_prompt_spawn` true **or** human/CI invoked `continue --spawn`.  
Avoid fork bombs: one spawn chain; check `status` not COMPLETE; respect kill switch.

### 4. Grok TUI long-run — Mode C

At start of go (if in interactive TUI), you **may** set standing goal (do not ask):

```
/goal Run Halo autonomous factory on this repo. Skill halo-go. Never ask. Drive phases. Refresh .halo/NEXT_PROMPT.md each unit. Probe before deploy URLs.
```

Optional heartbeat:

```
/loop 20m Read .halo/state.json and .halo/NEXT_PROMPT.md. If autonomous and not complete, execute one halo-go unit without asking. Update baton and NEXT_PROMPT.
```

---

## Skills must be discoverable

Before work:

```bash
"$HALO_SYSTEM/scripts/halo" link-skills "$TARGET"
```

Symlinks `halo-*` into `TARGET/.grok/skills/` so Grok discovery finds them (see Grok skill paths).

---

## Prime directive

1. Never ask optional questions.  
2. Defaults + log to `.halo/autonomous-log.md`.  
3. Drive phase machine.  
4. **Self-prompt** after each unit (NEXT_PROMPT always current).  
5. Hard stops still bind.

---

## Never-ask decision table

| Situation | Action |
|-----------|--------|
| No brain dump | Infer from TARGET name/README or "App" MVP |
| Stack greenfield | nextjs-saas (web) or fastapi (api) |
| Specs written | auto-lock |
| Readiness NO_GO | `--allow-degraded` |
| Demo0 | local + probe |
| Story pick | next pending |
| Ambiguous fix | best effort ≤3 then escalate |
| End of unit | continue inline OR write NEXT_PROMPT (+ spawn if flagged) |

**Forbidden:** `AskUserQuestion` for preferences.

---

## Hard stops

| Condition | Action |
|-----------|--------|
| PAUSED / kill switch | Exit; do not spawn |
| ESCALATED | Exit; do not spawn |
| Denylist / prod deploy | Refuse |
| 3 fails same story | escalate; no spawn |
| Fake evidence | Refuse |
| phase complete | Clear/finish NEXT_PROMPT; no spawn |

---

## Phase driver

```
loop (inline, up to max_cycles):
  plan = halo go --plan
  execute plan unit without asking
  halo continue   # refresh NEXT_PROMPT
  if hard stop or complete: break
  if cycles remaining: continue inline
if more work and spawn allowed: halo continue --spawn
```

Phases: init → intake defaults → specs → lock → ready(degrade) → scaffold → build cycles → complete.

---

## Deactivate

```bash
halo go --off
```

---

## Success

- complete / no pending work, OR  
- hard stop with baton + NEXT_PROMPT explaining resume, OR  
- max_cycles with NEXT_PROMPT ready for headless  

Report once at real exit — not between every micro-step.
