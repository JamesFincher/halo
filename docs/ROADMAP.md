# Halo Roadmap

## Slice 0 — Bootstrap + Intake + Spec pack ✅ (this commit family)

- [x] Repo skeleton, AGENTS, ARCHITECTURE, LIFECYCLE
- [x] `halo-bootstrap` skill
- [x] `halo-intake` + steps
- [x] `halo-spec-pack` skill
- [x] `halo_state.py`, `halo_probe.py`
- [x] Templates for product AGENTS/HALO
- [x] Readiness skill stub

## Slice 1 — Readiness automation

- [ ] Full readiness checks + CLI probes
- [ ] Secret inventory UX (write-only `.env`, never log values)
- [ ] GO / NO_GO / DEGRADED machine verdict
- [ ] Block scaffold until GO or explicit DEGRADED accept

## Slice 2 — Scaffold + Demo 0

- [ ] Stack-specific scaffolders (start: Next.js SaaS + FastAPI profiles)
- [ ] Port design-system patterns from bm-skills (optional profile)
- [ ] Demo 0 deploy + **live probe** gate
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
