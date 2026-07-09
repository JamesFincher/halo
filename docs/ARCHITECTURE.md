# Halo Architecture

> **Deep dive (normative intent):** [ARCHITECTURE-DEEP.md](./ARCHITECTURE-DEEP.md) — AI-centric design, two worlds, self-modify levels, completeness, failure taxonomy.

## What Halo is

Halo is a **skill-packaged, self-instantiating product development system** for agentic AI (Grok Build first).

It is not:

- A single chat prompt
- Only a PRD writer (BM)
- Only a build loop (grok-halo)

It is the **full path**: idea → specs → readiness → scaffold → autonomous iterate → live demos.

## Design thesis

1. **Harness > model** — loop structure, certs, readiness, baton beat clever prompts.
2. **Initializer then worker** — Anthropic long-running agents: first session sets environment; later sessions one unit of work + clean handoff.
3. **Filesystem memory** — state, specs, baton, milestone logs survive context death.
4. **Foresight gate** — all lifecycle integrations/credentials collected before scaffold.
5. **Live probe before share** — deploy URL never announced until HTTP proves alive.
6. **Grok-native skills** — `.grok/skills/*/SKILL.md` + progressive step files.

## Lifecycle (full vision)

```
┌─────────────┐
│  BOOTSTRAP  │  copy halo surface into target project
└──────┬──────┘
       ▼
┌─────────────┐
│   INTAKE    │  human depth optional; defaults always proposed
└──────┬──────┘
       ▼
┌─────────────┐
│  SPEC PACK  │  giant docs delivery → human iterate → LOCK
└──────┬──────┘
       ▼
┌─────────────┐
│  READINESS  │  keys, CLIs, auth, deploy, monitoring foresight
└──────┬──────┘
       ▼
┌─────────────┐
│  SCAFFOLD   │  stack skeleton, design system, Demo 0 live
└──────┬──────┘
       ▼
┌─────────────┐
│ MILESTONES  │  self-authored prompts + stories + tests plan
└──────┬──────┘
       ▼
┌─────────────┐     ┌──────────────┐
│ BUILD LOOP  │────▶│ LIVE DEMO N  │  probe OK → notify human
│ TDD/verify  │     └──────────────┘
│ deploy      │◀──────── async, non-blocking
└─────────────┘
```

## Components

| Layer | Role |
|-------|------|
| Skills | Agent-facing procedures (SKILL.md) |
| Python | Deterministic state, probe, later runner |
| Templates | Spec / AGENTS / HALO skeletons |
| Target `.halo/` | Runtime memory for one product |
| Evidence certs | Typed proof (from grok-halo v2) |

## Phase machine (`state.phase`)

`bootstrap` → `intake` → `spec_pack` → `spec_review` → `readiness` → `scaffold` → `milestones` → `build` → `complete` | `paused` | `blocked`

## Deploy safety

```
deploy_cmd → capture URL → halo_probe.py --url →
  PASS → write DEPLOY_OK + notify human
  FAIL → no notify; fix or NEEDS_REVISION
```

## Stack policy

Stack is **chosen in intake**, not hardcoded by Halo.  
Halo generates STACK.md + scaffolds that match.  
Python is Halo's own automation language.

## Slice plan

| Slice | Deliverable |
|-------|-------------|
| **0 (now)** | Repo + bootstrap + intake + spec-pack skills + state tool |
| 1 | Readiness skill + probe + secret inventory templates |
| 2 | Scaffold + design-system port + Demo 0 |
| 3 | Milestone author + build loop port from grok-halo |
| 4 | Runner walk-away (`halo start`) + budget/Arena |

## Non-goals (v0)

- Production promote automation
- Multi-cloud agent fleet
- Non-Grok skill manifests (later)
- Replacing human product judgment at intake
