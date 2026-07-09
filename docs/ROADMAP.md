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

## Slice 2 — Scaffold + Demo 0

- [x] `halo-scaffold` skill contract (probe-before-share)
- [ ] Stack-specific scaffolders (Next.js SaaS + FastAPI)
- [ ] Port design-system patterns from bm-skills (optional)
- [ ] Demo 0 deploy + live probe gate automated
- [ ] Milestone prompt generation from MILESTONES.md + STORIES.md

## Slice 3 — Build loop

- [ ] Port grok-halo v2: budget, TDD, Arena, simplify, baton, golden trajectory
- [ ] Wire probe into deploy notify
- [ ] Self-authored next prompts from baton + remaining stories

## Slice 4 — Walk-away runner

- [ ] `scripts/halo` or `python -m halo` start/stop/status
- [ ] Lock file, daily caps, escalation packets
- [ ] Human dashboard notes / voice optional

## Non-goals near-term

- Multi-agent cloud fleet
- Non-Grok plugin manifests
- Auto production promote
