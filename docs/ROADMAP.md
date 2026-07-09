# Halo Roadmap

## Slice 0 — Bootstrap + Intake + Spec pack ✅

- [x] Repo skeleton, AGENTS, ARCHITECTURE, LIFECYCLE
- [x] `halo-bootstrap` skill
- [x] `halo-intake` + steps
- [x] `halo-spec-pack` skill
- [x] `halo_state.py`, `halo_probe.py`, `halo_spec_write.py`
- [x] Templates for product AGENTS/HALO

## Slice 1 — Readiness automation ✅

- [x] `halo_catalog.py` lifecycle baseline + intake merge
- [x] `halo_readiness.py` CLI/env checks (never log secrets)
- [x] GO / NO_GO / DEGRADED + `--allow-degraded`
- [x] Writes readiness.json, READINESS.md, .env.example, baton
- [x] `lock-specs` state command

## Slice 2 — Scaffold + Demo 0 + full workflows ✅

- [x] `docs/WORKFLOWS.md` — all human/agent paths
- [x] `scripts/halo` CLI (init/status/specs/lock/ready/scaffold/…)
- [x] nextjs-saas + fastapi + existing scaffolders
- [x] Demo 0 local + live probe gate
- [x] Milestone prompt generation + index.json
- [x] Control skills: pause, escalate, handoff, revise, doctor, triage, deploy, verify, build

## Slice 2.5 — Safety beams ✅

- [x] Phase transition graph (halo_phases + state gate)
- [x] Evidence cert validator
- [x] halo doctor --strict
- [x] halo-go autonomous

## Slice 3 — Build loop

- [x] `halo-build` / `halo-verify` / `halo-deploy` skill contracts
- [ ] Port grok-halo v2 runner automation (budget, Arena, scores)
- [ ] Self-authored next prompts from baton + remaining stories

## Slice 4 — Walk-away runner

- [x] `scripts/halo` surface (status/stop/resume/…)
- [ ] Background loop lock + daily caps
- [ ] Human dashboard notes / voice optional

## Non-goals near-term

- Multi-agent cloud fleet
- Non-Grok plugin manifests
- Auto production promote
