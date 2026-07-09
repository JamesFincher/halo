# Halo Roadmap

## Slice 0 — Bootstrap + Intake + Spec pack ✅

- [x] Repo skeleton, AGENTS, ARCHITECTURE, LIFECYCLE
- [x] `halo-bootstrap` skill
- [x] `halo-intake` + steps
- [x] `halo-spec-pack` skill
- [x] `halo_state.py`, `halo_probe.py`, `halo_spec_write.py`
- [x] Templates for product AGENTS/HALO

## Slice 1 — Readiness automation ✅

- [x] `halo_catalog.py` lifecycle baseline
- [x] `halo_readiness.py` CLI/env checks
- [x] GO / NO_GO / DEGRADED + `--allow-degraded`
- [x] `readiness.json`, `READINESS.md`, `.env.example`
- [x] `lock-specs` state command

## Slice 2 — Scaffold + Demo 0 + workflows ✅

- [x] `docs/WORKFLOWS.md`
- [x] `scripts/halo` CLI
- [x] nextjs-saas / fastapi / existing scaffolders
- [x] Demo 0 local + probe gate
- [x] Milestone prompts + `index.json`
- [x] Control skills: pause, escalate, handoff, revise, doctor, triage, deploy, verify, build

## Slice 2.5 — Safety beams ✅

- [x] Phase transition graph
- [x] Evidence cert validator
- [x] `halo doctor --strict`
- [x] `halo-go` autonomous

## Slice 2.6 — Peer gap close ✅

- [x] `docs/GAPS.md`
- [x] `feature-list.json` + `halo_features.py`
- [x] `progress.jsonl` / `progress.md`
- [x] Struggle detection + false completion promise reject
- [x] Test ratchet
- [x] Single-runner lock helper
- [x] Engineered `NEXT_PROMPT`

## Slice 3 — Build loop ✅

- [x] `halo-build` / `halo-verify` / `halo-deploy` skills
- [x] Engineered `NEXT_PROMPT` from live state
- [x] Evidence-gated feature pass
- [x] Hard budget + test ratchet
- [x] `halo go` arms Stop loop
- [x] Dogfood-safe `.gitignore`
- [x] Arena dual-lens verify
- [x] Safe auto-commit per unit

## Slice 4 — Walk-away runner

- [x] `scripts/halo` surface
- [x] Runner lock helper
- [x] Daily/iter/wall budget hard stop
- [x] CI smoke workflow
- [ ] Human dashboard / voice (optional)

## Non-goals

- Multi-agent cloud fleet
- Non-Grok plugin manifests
- Auto production promote

See `docs/GAPS.md` for severity table.
