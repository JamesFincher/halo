# Halo Architecture

Halo is a skill-packaged, self-instantiating product development system for agentic AI.

## What it is

- Full lifecycle: idea → specs → readiness → scaffold → iterate → live demos.
- Harness: loop structure, certs, readiness, and baton beat clever prompts.
- Filesystem memory: state, specs, baton, milestones survive context death.
- Foresight gate: lifecycle integrations and credentials collected before scaffold.
- Live probe before share: deploy URL never announced until HTTP is alive.

## Components

| Layer | Role |
|-------|------|
| Skills | Agent procedures (`SKILL.md`) |
| Python | Deterministic state, probe, scaffold, readiness |
| Templates | Spec / AGENTS / HALO skeletons |
| Target `.halo/` | Runtime memory for one product |
| Evidence certs | Typed proof files |

## Lifecycle

```
BOOTSTRAP → INTAKE → SPEC PACK → READINESS → SCAFFOLD → MILESTONES → BUILD LOOP → LIVE DEMO
```

## Phase machine

`bootstrap` → `intake` → `spec_pack` → `spec_review` → `readiness` → `scaffold` → `build` → `complete` | `paused` | `blocked`

## Deploy safety

```
deploy_cmd → capture URL → halo_probe.py --url →
  PASS → write DEPLOY_OK + notify human
  FAIL → no notify; fix or NEEDS_REVISION
```

## Stack policy

Stack is chosen in intake, not hardcoded by Halo. `STACK.md` and scaffolds match the chosen stack.

## Non-goals

- Production promote automation.
- Multi-cloud agent fleet.
- Non-Grok skill manifests (later).

See `ARCHITECTURE-DEEP.md` for the full design rationale.
