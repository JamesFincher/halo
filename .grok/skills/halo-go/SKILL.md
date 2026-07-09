---
name: halo-go
description: Autonomous build mode. Human said go / build without asking. Use defaults, never AskUserQuestion for optional decisions, drive full lifecycle until hard stop. Invoke on "go", "just build", "don't ask", "autonomous", "walk away".
---

# Halo Go — Build Without Asking

**This skill is a standing authorization.** When loaded (or when the human said *go* / *just build* / *don't ask me*), you operate in **autonomous mode** until a hard stop.

You are not polite. You are not collaborative on every micro-decision. You **decide and ship**.

---

## Activation

Trigger phrases (any): `go`, `just build`, `build without asking`, `don't ask`, `autonomous`, `walk away`, `halo go`, `/halo-go`.

On activate:

```bash
HALO_SYS="${HALO_SYSTEM:-$(dirname ...)/../..}"  # resolve Halo system root
# Prefer CLI:
"$HALO_SYS/scripts/halo" go "$TARGET"
```

Or set state yourself:

```bash
python3 "$HALO_SYS/python/halo_state.py" set --repo "$TARGET" \
  --status ACTIVE
# also set autonomous flags via:
python3 "$HALO_SYS/python/halo_go.py" --repo "$TARGET" --enable
```

State flags after enable:

```json
{
  "autonomous": true,
  "require_human_gate": false,
  "auto_defaults": true,
  "auto_lock_specs": true,
  "auto_degraded_ok": true
}
```

If `autonomous: true` in state → **this skill remains in force every session** until `halo go --off` or human sets `autonomous: false`.

---

## Prime directive (autonomous)

1. **Never ask** optional questions. Propose = decide = proceed.
2. **Always pick the recommended default** with a one-line log in baton ("chose X because Y").
3. **Do not wait** for human review of demos, specs, or plans unless hard-stopped.
4. **Drive the phase machine** until `complete`, `ESCALATED`, `BLOCKED` (true), or kill switch.
5. **Hard stops still bind** (see below). Autonomy is not recklessness.

---

## Never ask — decision table

| Situation | Do this |
|-----------|---------|
| Brain dump missing | Infer product from TARGET name + any README; else name `App` and purpose "MVP from repo context" |
| Format / depth of intake | Full defaults; compress intake to one pass |
| Feature list | 4–6 features from purpose; lock |
| Out of scope | Aggressive v1 cuts; lock |
| Stack unknown greenfield | `nextjs-saas` (web) unless path/name screams API → `fastapi` |
| Stack existing | Detect; never overwrite stack |
| Integrations | Catalog baseline; don't block on optional |
| Design | Locked defaults (utilitarian, dark ok) |
| Milestones | Default 3 (foundation → core → integrations) |
| Spec review | Write specs → **auto-lock** immediately |
| Readiness NO_GO | Re-run with `--allow-degraded`; scaffold local Demo0 |
| Blocking secrets missing | DEGRADED local only; continue build without remote deploy |
| Profile choice | auto from stack |
| Demo0 | `--demo0 local` always first |
| Story pick | Highest priority pending in STORIES / milestone index |
| Test framework | Project default or minimal node/pytest already scaffolded |
| Naming | Short, boring, consistent |
| Ambiguous bugfix | Root-cause best effort ≤3; then escalate packet, don't ask |
| "Should I…?" impulse | Yes if it advances phase; no if denylist/prod |

**Forbidden tools for optional UX:** `AskUserQuestion` for preferences.  
**Allowed ask:** only if a **hard stop** requires a secret value that cannot be degraded (see Hard stops). Even then prefer writing `.env.example` + BLOCKED checklist over chat Q&A.

---

## Hard stops (MUST stop; may notify human)

Stop autonomous loop and set baton when:

| Condition | Action |
|-----------|--------|
| `HALO_KILL_SWITCH=true` or `status: PAUSED` | Exit |
| Denylist path would be edited | REJECT, escalate |
| Production deploy requested | Refuse; preview only |
| Story failed 3 attempts | `halo escalate`, status ESCALATED |
| Evidence would be faked | Refuse; fix real gate |
| `status: ESCALATED` already | Wait human |
| True data-loss / `rm -rf` outside project | Refuse |
| Human message in-session explicitly "stop" / "pause" | `halo stop` |

**Not hard stops** (continue):

- Specs "not reviewed by human" → auto-lock  
- Optional Sentry/analytics missing → DEGRADED  
- Soft lint nits → fix or skip  
- Unsure between two library choices → pick default, note in milestone-log  

---

## Phase driver (execute without waiting)

Resolve TARGET first (never scaffold into Halo system repo unless dogfood flag).

```
loop:
  read state.phase + baton
  if autonomous != true → enable (this skill was invoked)
  if status in (PAUSED, ESCALATED) → exit
  if status == BLOCKED and cannot degrade → exit with checklist
  switch phase:
    missing .halo     → halo init / bootstrap
    intake            → fill intake defaults in one shot → specs
    spec_pack/review  → halo_spec_write → lock-specs
    readiness         → halo ready --allow-degraded (if auto_degraded_ok)
    scaffold          → halo scaffold --demo0 local --profile auto
    build             → ONE story cycle (halo-build), then loop
    complete          → exit success
  update baton every phase change
  never idle waiting for human approval
```

### Intake in autonomous mode (single pass)

Do **not** walk 11 interactive phases with questions. Instead:

1. Read TARGET files (README, package.json, existing code).  
2. Write complete `intake` object to state (purpose, features, oos, stack, integrations, data_model, design, milestones).  
3. `halo specs` → `halo lock` immediately.  
4. Log summary in baton (not a question).

### Build cycle in autonomous mode

Follow `halo-build` fully. Between cycles:

- Do not ask "continue to next story?"  
- Continue until no pending stories or hard stop.  
- Cap: max **N** cycles per invocation (default **5** from state `autonomous_max_cycles` or 5). Leave baton "run halo go again" if more remain — avoids infinite context blowups. Still no questions.

---

## Logging (replace questions)

After each major decision append to baton or `.halo/autonomous-log.md`:

```markdown
- [ISO time] chose nextjs-saas — greenfield web default
- [ISO time] auto-locked specs
- [ISO time] readiness DEGRADED — missing DATABASE_URL; local only
- [ISO time] Demo0 PASS http://127.0.0.1:…
- [ISO time] shipped S001
```

Human can read the log later. That is the async contract.

---

## What you may NOT skip

Even in go mode:

- RED before GREEN when adding behavior  
- Live probe before any human-facing deploy URL  
- Denylist  
- Preview-only deploys  
- Writing evidence for claims  

Autonomy without evidence is vandalism.

---

## Deactivate

```bash
halo go --off
# or
python3 python/halo_go.py --repo . --disable
```

Human "stop caveman" / "stop" / "pause" → treat as deactivate autonomous **and** pause if they said pause.

---

## Relationship to other skills

| Skill | Under halo-go |
|-------|----------------|
| halo-intake | Defaults-only single pass |
| halo-spec-pack | Write + auto-lock |
| halo-readiness | allow-degraded when flag set |
| halo-scaffold | Always run when phase says |
| halo-build | Cycle without "continue?" |
| halo-pause | Only on hard stop / explicit stop |

---

## Success exit

```
phase complete OR
pending stories = 0 after build OR
hard stop with baton explaining why
```

Report once at end: what shipped, demo URLs that **probed**, blockers remaining. No mid-flight questionnaires.
