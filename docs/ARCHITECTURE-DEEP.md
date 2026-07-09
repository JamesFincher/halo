# Halo Deep Architecture

## Novel claim

Most AI coding tools are chat over a repo. Halo is a filesystem-backed state machine whose transitions are executed by an LLM but whose safety gates are deterministic programs.

| Axis | Normal agent | Halo |
|------|--------------|------|
| Operator | Human | Agent after lock |
| Memory | Chat transcript | Filesystem control plane |
| Output | One app | Product + the procedure that builds products |

## Two worlds (never conflate)

- **World A** — this repo: factory instructions, skills, scripts, python.
- **World B** — any product repo: app code, `.halo/`, AGENTS.md.

Rule: World A is never the product. World B never owns the factory protocol.

## Layered architecture

```
L5  HUMAN INTENT     idea, taste, lock, secrets, prod promote
L4  AGENT JUDGMENT   intake, plan, code, critique
L3  SKILL PROTOCOL   SKILL.md procedures
L2  DETERMINISTIC    python/ + scripts/halo
L1  ARTIFACTS        .halo/*, git, evidence
```

Safety-critical gates must live in L2 or L1, not skills alone.

## Control plane vs data plane

Control plane: `state.json`, `baton.md`, skills, `scripts/halo`.
Data plane: app source, `.halo/spec/*`, milestones, evidence, previews.

Progress is real only when data plane changes are backed by control plane and evidence.

## Runtime story

1. Cold open → read AGENTS.md → resolve TARGET.
2. Bootstrap → create `.halo/` before feature code.
3. Intake → write `state.intake`.
4. Spec pack → write `.halo/spec/*`.
5. Human lock → `spec_status: locked`.
6. Readiness → GO / NO_GO / DEGRADED.
7. Scaffold → skeleton + Demo 0 with probe.
8. Build loop → one story per cycle until complete.

## Session death

Assume every session ends. Recovery is L1 files only:

- `.halo/state.json`
- `.halo/baton.md`
- `.halo/spec/` (if locked)
- `git log -5` and `git status`
- Last evidence / escalation

## Self-build / self-modify levels

- Level 0 — operate a product (default).
- Level 1 — extend product harness (AGENTS.md, plans, logs).
- Level 2 — evolve the Halo factory (skills, scripts, docs). Requires explicit intent, branch + probe, workflow update, compatibility.

Forbidden: evidence cheating, rewriting readiness thresholds, deleting denylist, infinite self-prompt without completion criteria.

## Authority boundaries

| Object | Human | Agent (product) | Agent (meta) |
|--------|-------|-----------------|--------------|
| Product idea / lock | Yes | Propose only | No |
| Secrets / .env | Yes | Never commit/log | Same |
| Prod promote | Yes | No | No |
| Phase/status transitions | CLI ok | Via scripts only | Via scripts only |
| App code (World B) | Yes | Yes after lock | N/A |
| Skills (World A) | Yes | No by default | Only on meta task |
| Evidence | Audit | Write truthfully | Same |

## Completeness model

Three inventories must stay in sync:

- **Workflows** in `docs/WORKFLOWS.md`
- **Skills** in `.grok/skills/`
- **Determinism** in `python/` and `scripts/halo`

Every PR adding a journey or phase must update all three.

## Definition of done

| Level | Done means |
|-------|------------|
| Story | AC green + evidence + probed demo |
| Milestone | All stories + milestone log |
| Product v1 | All milestones + readiness still GO |
| Halo slice | workflows + skills + python + smoke + docs |

## Failure taxonomy

| Class | Example | Response |
|-------|---------|----------|
| Intent | Wrong product | Unlock specs, human revises |
| Environment | Missing API key | BLOCKED + readiness list |
| Implementation | Bug / red tests | Inner fix ≤3, then escalate |
| Verification | AC untested | NEEDS_REVISION |
| Deploy | Probe fail | No notify; stay/fix |
| Process | Phase skip | Doctor / refuse transition |
| Integrity | Evidence cheat | Reject; escalate |
| Meta | Skill bug | Pin version; hotfix World A |

## What is hard vs soft

Hardened (L2 real): state init/lock/set, spec write, readiness, scaffold, probe, CLI, workflow map, phase graph, evidence validator, doctor, halo-go.

Soft (L3/contract): intake quality, spec content depth, full TDD runner, dual verifier Arena, budget/golden trajectory port, walk-away daemon.

## Evolution doctrine

For product work:
- Never freestyle past phase.
- Prefer `scripts/halo` over ad-hoc shell.
- After every session: baton is accurate enough for a stranger agent.
- Never announce deploys without probe.

For factory work (Level 2):
- Change one workflow at a time.
- Update workflow + skill + CLI + smoke in the same change.
- Smoke on a throwaway product before claiming done.
- Prefer adding L2 gates over longer skill prose.

## Mental model

> Halo is a filesystem-backed state machine whose transitions are mostly executed by an LLM, but whose safety gates are deterministic programs — building products in one world while occasionally rewriting its own instructions in another.

See `WORKFLOWS.md` for paths, `GAPS.md` for open risk, `ROADMAP.md` for slice status.
