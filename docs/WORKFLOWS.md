# Halo Workflows — No Blind Spots

Every path a **human** or **agent** takes. If a path is missing here, it is a bug.

**Machine entry:** `scripts/halo <command>`  
**Agent entry:** skill matching phase / baton  
**State truth:** `.halo/state.json`  
**Session truth:** `.halo/baton.md`

---

## 0. State machine

```
bootstrap → intake → spec_pack → spec_review ⇄ (revise)
                  ↓ lock-specs
              readiness ⇄ (fill env, re-check)
                  ↓ GO | DEGRADED
              scaffold → (demo0 probe)
                  ↓
                build ⇄ (cycle: plan→tdd→verify→deploy→probe→critique)
                  ↓ all stories deployed
              complete

Any phase → paused (human/kill switch)
Any phase → blocked (secrets, 3 fails, denylist, budget)
blocked/paused → resume → prior phase
build → escalate (handoff packet) → human
spec_review ← unlock-specs (from readiness/scaffold/build) if product pivot
```

| `status` | Meaning |
|----------|---------|
| `ACTIVE` | Normal progress |
| `PAUSED` | Human or kill switch; no autonomous cycles |
| `BLOCKED` | Cannot proceed until checklist cleared |
| `ESCALATED` | Human packet written; loop stopped |
| `COMPLETE` | All milestones/stories done |

| `phase` | Allowed next |
|---------|----------------|
| `bootstrap` | intake |
| `intake` | spec_pack |
| `spec_pack` | spec_review |
| `spec_review` | readiness (lock) or intake (re-open) |
| `readiness` | scaffold (GO/DEGRADED) or stay (NO_GO) |
| `scaffold` | build (demo0 ok) or retry scaffold |
| `build` | build (next story) or complete |
| `complete` | — |

---

## 1. Human journeys (forecasted)

### H1 — Greenfield idea (happy path)

1. Open empty folder + install Halo skills  
2. Agent: bootstrap → intake grill (depth optional)  
3. Giant delivery `.halo/spec/*`  
4. Human edits docs / chats revisions  
5. Human: “lock” / `halo lock`  
6. Human fills `.env` from readiness checklist  
7. `halo ready` → GO  
8. `halo scaffold` → Demo 0 live link (probed)  
9. Walk away; receive async demo links per story  
10. Promote prod themselves when happy  

**Commands:** `halo init` → (agent intake) → `halo specs` → `halo lock` → `halo ready` → `halo scaffold` → `halo status`

### H2 — Existing codebase

1. Bootstrap into existing repo (non-destructive)  
2. Intake detects stack; PRD scopes *delta* not rewrite  
3. Scaffold profile = `existing` (wire health + Halo surface only)  
4. Build loop implements stories only  

### H3 — Fast defaults (low energy)

1. Brain dump one paragraph  
2. “use defaults for rest of intake”  
3. Spec pack generated; human skims; lock  
4. Same as H1 from readiness  

### H3b — Full autonomous (`halo go`)

1. Human: idea (optional) + **go** / `halo go`  
2. Agent enables `autonomous: true`, never asks optional questions  
3. Single-pass intake defaults → auto specs → auto-lock  
4. Readiness with `--allow-degraded` if needed  
5. Scaffold Demo0 local (probe)  
6. Build cycles up to `autonomous_max_cycles` (default 5)  
7. Stop only on hard stop; log decisions in `.halo/autonomous-log.md`  
8. Human peeks demos async; no mid-flight questionnaires  

**Commands:** `halo go` · agent skill `halo-go` · `halo go --off` to return interactive  

**Self-prompt (Grok Build):**

| Mode | Mechanism |
|------|-----------|
| Inline | Agent continues phase driver same session (no "continue?") |
| Headless | `.halo/NEXT_PROMPT.md` + `halo continue --spawn` → `grok -p --prompt-file … --yolo` |
| Goal/Loop | `/goal <standing>` · `/loop 20m <read NEXT_PROMPT>` |

See `docs/GROK-BUILD.md`. Skills linked via `halo link-skills`.

### H4 — Deep product owner

1. Full intake every phase  
2. Multiple spec revision loops  
3. `halo unlock` mid-build if scope changes → re-lock → readiness delta → continue  

### H5 — Secrets later / degraded

1. Readiness NO_GO  
2. Human accepts DEGRADED (`halo ready --allow-degraded`)  
3. Scaffold + local Demo 0 only; remote deploy stories blocked until keys present  

### H6 — Check progress without coding

1. `halo status` / `halo triage`  
2. Read baton, last demo URL (only if probe still green optional re-probe), scores  

### H7 — Pause / resume

1. `halo stop` → PAUSED  
2. `halo resume` → ACTIVE, baton phase  

### H8 — Something on fire

1. Build fails 3× same story → `ESCALATED` + `.halo/escalations/Sxxx.md`  
2. Human reads packet; `halo resume` after fix or skip story  

### H9 — Demo looks wrong

1. Human comments on demo  
2. Agent: new story or NEEDS_REVISION cycle; never force-approve  

### H10 — Wrong stack chosen

1. `halo unlock` → edit STACK → lock → ready → scaffold may be non-destructive or re-scaffold with confirm  

### H11 — Multi-session (context death)

1. New agent session  
2. Read `AGENTS.md` + baton + state  
3. Continue phase skill — never restart from zero unless baton says cold  

### H12 — Install Halo itself

1. Clone JamesFincher/halo  
2. `grok plugin install ./halo --trust`  
3. Point agent at product dir  

---

## 2. Agent journeys (forecasted)

| ID | Trigger | Skill / tool | Exit |
|----|---------|--------------|------|
| A0 | Empty / no `.halo` | `halo-bootstrap` | phase intake |
| A1 | phase intake | `halo-intake` | phase spec_pack |
| A2 | phase spec_pack | `halo-spec-pack` / `halo_spec_write` | spec_review |
| A3 | “change the PRD” | edit specs + optional re-write | stay spec_review |
| A4 | “lock” | `halo_state lock-specs` | readiness |
| A5 | phase readiness | `halo_readiness --write` | GO→scaffold / NO_GO stay |
| A6 | phase scaffold | `halo_scaffold` | build + demo0 evidence |
| A7 | phase build | `halo-build` cycle | next story / complete |
| A8 | deploy done | `halo_probe` then notify | evidence cert |
| A9 | verifier NEEDS_REVISION | re-impl ≤3 | APPROVED or escalate |
| A10 | status PAUSED | stop tools | wait human |
| A11 | status BLOCKED | list human_action only | wait |
| A12 | 3 fails | `halo-escalate` | ESCALATED |
| A13 | “handoff” | `halo-handoff` packet | human |
| A14 | “status” | `halo status` | report |
| A15 | kill switch env | refuse run | — |
| A16 | denylist touch | REJECT | escalate |
| A17 | unlock mid-flight | unlock-specs | spec_review |

---

## 3. CLI command map (`scripts/halo`)

| Command | Phase impact | Description |
|---------|--------------|-------------|
| `init [path]` | bootstrap→intake | Init product `.halo` |
| `status [path]` | — | Print phase, verdict, story, last demo |
| `baton [path]` | — | Print baton |
| `specs [path]` | →spec_review | Write spec pack from intake |
| `lock [path]` | →readiness | Lock specs |
| `unlock [path]` | →spec_review | Unlock for revision |
| `ready [path]` | readiness | Run readiness gate |
| `scaffold [path]` | →build | Scaffold + milestones + demo0 |
| `milestones [path]` | — | Regenerate milestone prompts |
| `probe --url` | — | Live probe only |
| `build [path]` | build | One cycle instruction / runner hook |
| `stop [path]` | PAUSED | Kill switch soft |
| `resume [path]` | ACTIVE | Clear pause |
| `escalate [path]` | ESCALATED | Write escalation packet |
| `triage [path]` | — | Health summary |
| `handoff [path]` | — | Context pack for other agent/human |
| `doctor [path]` | — | Validate Halo install + product integrity |

---

## 4. Blind-spot checklist (must stay green)

- [x] Greenfield bootstrap  
- [x] Existing repo bootstrap  
- [x] Intake resume mid-grill (state.intake keys)  
- [x] Spec generate + revise + lock + unlock  
- [x] Readiness GO / NO_GO / DEGRADED  
- [x] Scaffold nextjs + fastapi + existing  
- [x] Milestone prompts + index  
- [x] Demo 0 local + probe gate  
- [x] Deploy share only after probe  
- [x] Pause / resume / blocked  
- [x] Escalation packet  
- [x] Status / triage / doctor  
- [x] Handoff pack  
- [x] Session resume via baton  
- [x] Workflow map document (this file)  
- [ ] Full autonomous multi-cycle runner (slice 3–4 — skill contract present)  
- [ ] Design-system full port (optional profile later)  
- [ ] Remote Vercel demo0 (optional; local first)  

---

## 5. Skill inventory (system repo)

| Skill | Workflow |
|-------|----------|
| `halo-bootstrap` | A0 |
| `halo-intake` | A1 |
| `halo-spec-pack` | A2–A3 |
| `halo-readiness` | A5 |
| `halo-scaffold` | A6 |
| `halo-build` | A7–A9 |
| `halo-deploy` | A8 |
| `halo-verify` | A9 |
| `halo-status` | A14 |
| `halo-triage` | H6 |
| `halo-pause` | H7 |
| `halo-escalate` | H8 |
| `halo-handoff` | A13 |
| `halo-revise` | H4 / A17 |
| `halo-doctor` | H12 integrity |

---

## 6. Evidence certificates (product)

| Cert | When |
|------|------|
| `RED_TEST` / `GREEN_TEST` | build cycle |
| `SPEC_OK` / `SIMPLIFY_OK` | build cycle |
| `demo0-probe` / `DEPLOY_OK` | scaffold / deploy — **probe required** |
| `SMOKE_OK` | after deploy |
| `VERIFIER_APPROVED` | arena/single |
| `readiness.json` | readiness gate |
| `escalation` | blocked path |

Never: human-facing URL without probe PASS.
