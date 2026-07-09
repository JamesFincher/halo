# Halo Workflows — No Blind Spots

Machine entry: `scripts/halo <command>`  
Agent entry: skill matching phase / baton, or `halo go` for autonomous self-prompt  
State truth: `.halo/state.json`  
Session truth: `.halo/baton.md`

## State machine

```
bootstrap → intake → spec_pack → spec_review ⇄ (revise)
                  ↓ lock-specs
              readiness ⇄ (fill env, re-check)
                  ↓ GO | DEGRADED
              scaffold → (demo0 probe)
                  ↓
                build ⇄ (plan → tdd → verify → deploy → probe)
                  ↓ all stories
              complete
```

Any phase → `PAUSED` (human/kill switch)  
Any phase → `BLOCKED` (secrets, 3 fails, denylist, budget)  
`blocked/paused` → `resume` → prior phase  
`build` → `escalate` → human handoff  
`spec_review` ← `unlock-specs` for product pivot

| `status` | Meaning |
|----------|---------|
| `ACTIVE` | Normal progress |
| `PAUSED` | Human or kill switch; no autonomous cycles |
| `BLOCKED` | Cannot proceed until checklist cleared |
| `ESCALATED` | Human packet written; loop stopped |
| `COMPLETE` | All milestones/stories done |

## Phase allowed next

| `phase` | Allowed next |
|---------|--------------|
| `bootstrap` | `intake` |
| `intake` | `spec_pack` |
| `spec_pack` | `spec_review` |
| `spec_review` | `readiness` (lock) or `intake` (re-open) |
| `readiness` | `scaffold` (GO/DEGRADED) or stay (NO_GO) |
| `scaffold` | `build` (demo0 ok) or retry scaffold |
| `build` | `build` (next story) or `complete` |
| `complete` | — |

## Human journeys

- **H1 Greenfield idea**: install → open empty folder → bootstrap → intake → specs → lock → ready → scaffold → walk away.
- **H2 Existing codebase**: bootstrap non-destructively → detect stack → delta PRD → scaffold `existing` → build.
- **H3 Fast defaults**: one paragraph → `go` → auto intake/specs/lock → auto-degraded readiness → scaffold → build.
- **H4 Deep product owner**: full intake → multiple spec loops → unlock/lock if pivot.
- **H5 Secrets later / degraded**: readiness NO_GO → `--allow-degraded` → local Demo 0.
- **H6 Progress check**: `halo status`, `halo triage`.
- **H7 Pause/resume**: `halo stop` / `halo resume`.
- **H8 On fire**: 3 fails → `ESCALATED` + packet.
- **H9 Demo looks wrong**: new story or NEEDS_REVISION.
- **H10 Wrong stack**: `halo unlock` → edit `STACK.md` → lock → re-ready.
- **H11 Multi-session**: new agent reads AGENTS.md + baton + state; continue phase.
- **H12 Install Halo**: `git clone` + `grok plugin install <path> --trust`.

## Agent journeys

| ID | Trigger | Skill / tool | Exit |
|----|---------|--------------|------|
| A0 | Empty / no `.halo` | `halo-bootstrap` | `intake` |
| A1 | `phase: intake` | `halo-intake` | `spec_pack` |
| A2 | `phase: spec_pack` | `halo-spec-pack` / `halo_spec_write` | `spec_review` |
| A3 | "change PRD" | edit specs + rewrite | stay `spec_review` |
| A4 | "lock" | `halo_state lock-specs` | `readiness` |
| A5 | `phase: readiness` | `halo_readiness --write` | GO→scaffold / NO_GO stay |
| A6 | `phase: scaffold` | `halo_scaffold` | `build` + demo0 evidence |
| A7 | `phase: build` | `halo-build` cycle | next story / `complete` |
| A8 | deploy done | `halo_probe` then notify | evidence cert |
| A9 | verifier NEEDS_REVISION | re-impl ≤3 | APPROVED or escalate |
| A10 | `status: PAUSED` | stop tools | wait human |
| A11 | `status: BLOCKED` | list human_action only | wait |
| A12 | 3 fails | `halo-escalate` | `ESCALATED` |
| A13 | "handoff" | `halo-handoff` packet | human |
| A14 | "status" | `halo status` | report |
| A15 | kill switch env | refuse run | — |
| A16 | denylist touch | REJECT | escalate |
| A17 | unlock mid-flight | `unlock-specs` | `spec_review` |
| A18 | AI self-instantiates Halo on this repo | `halo init .` + custom intake; `halo reinstantiate .` to reset compounding | `build` with `state.dogfood=true` |

## CLI command map

| Command | Phase impact | Description |
|---------|--------------|-------------|
| `init [path]` | bootstrap → intake | Init product `.halo` |
| `status [path]` | — | Phase, verdict, story, last demo |
| `specs [path]` | → spec_review | Write spec pack from intake |
| `lock [path]` | → readiness | Lock specs |
| `unlock [path]` | → spec_review | Unlock for revision |
| `ready [path]` | readiness | Run readiness gate |
| `scaffold [path]` | → build | Scaffold + milestones + demo0 |
| `build [path]` | build | One cycle instruction |
| `go [path]` | autonomous | Start continuous drive |
| `stop [path]` | PAUSED | Kill switch soft |
| `resume [path]` | ACTIVE | Clear pause |
| `continue [path]` | — | Refresh NEXT_PROMPT |
| `handoff [path]` | — | Context pack for another agent |
| `doctor [path]` | — | Validate install + product |
| `help` | — | Show command list |

## Evidence certificates

| Cert | When |
|------|------|
| `RED_TEST` / `GREEN_TEST` | build cycle |
| `SPEC_OK` / `SIMPLIFY_OK` | build cycle |
| `demo0-probe` / `DEPLOY_OK` | scaffold / deploy — probe required |
| `SMOKE_OK` | after deploy |
| `VERIFIER_APPROVED` | arena/single |
| `readiness.json` | readiness gate |
| `escalation` | blocked path |

Never: human-facing URL without probe PASS.

## Blind-spot checklist

- [x] Greenfield bootstrap
- [x] Existing repo bootstrap
- [x] Intake resume
- [x] Spec generate / revise / lock / unlock
- [x] Readiness GO / NO_GO / DEGRADED
- [x] Scaffold nextjs / fastapi / existing
- [x] Milestone prompts + index
- [x] Demo 0 local + probe gate
- [x] Deploy share only after probe
- [x] Pause / resume / blocked
- [x] Escalation packet
- [x] Status / triage / doctor
- [x] Handoff pack
- [x] Session resume via baton
- [x] Workflow map (this file)
- [ ] Full autonomous multi-cycle runner (skill contract present)
- [ ] Design-system full port
- [ ] Remote Vercel demo0 (optional)

## AI self-instantiation on this repo

When an AI is pointed at this factory repo and is the product being built:

1. Set `TARGET` = this repo and `HALO_SYSTEM` = this repo.
2. `.halo/` and `.halo-archive/` are local runtime state; they are gitignored and not part of the factory source.
3. If `.halo/` exists, it is a leftover local instance. Read `baton.md` and `state.json` to decide:
   - Continue it if the use case matches.
   - Reset for a custom use case: `halo reinstantiate .` to reset compounding, or `rm -rf .halo .halo-archive` and `halo init .` for a clean start.
4. Customize intake for your local use case and environment.
5. Run `halo specs`, `halo lock`, `halo ready --allow-degraded`, `halo scaffold --profile existing`, `halo go`.
6. Each unit upgrades the factory and runs `halo cycle-smoke`.
7. Never `git add -f .halo/` or `.halo-archive/`.
