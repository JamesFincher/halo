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

## Slice 2.6 — Peer-harness gap close ✅

- [x] `docs/GAPS.md` register vs Anthropic / Ralph / open-ralph / grok-halo
- [x] `feature-list.json` machine done-tracking (`halo_features.py`)
- [x] `progress.jsonl` / `progress.md` cold-session log
- [x] Struggle detection + false completion-promise reject on Stop
- [x] Test ratchet doctrine + build skill
- [x] Single-runner lock helper
- [x] Engineered NEXT_PROMPT includes feature list + progress + boot ritual

## Slice 3 — Build loop

- [x] `halo-build` / `halo-verify` / `halo-deploy` skill contracts
- [x] Self-authored NEXT_PROMPT from live state (engineered)
- [ ] Port grok-halo v2 runner automation (budget, Arena, scores)
- [ ] Auto-commit per story unit

## Slice 4 — Walk-away runner

- [x] `scripts/halo` surface (status/stop/resume/…)
- [x] Runner lock helper (`.halo/runner.lock`)
- [ ] Daily token/cycle budget hard stop
- [ ] Human dashboard notes / voice optional

## Non-goals near-term

- Multi-agent cloud fleet
- Non-Grok plugin manifests
- Auto production promote

See **docs/GAPS.md** for full severity table.
