# Halo

AI-operated product factory. Filesystem-backed state machine with deterministic safety gates.

## Two worlds

- **World A**: this repo (the factory). Never treat as the product.
- **World B**: the target product directory (empty or existing). `.halo/`, app code, and demos live here.

## First contact (agent cold-open)

1. Read `AGENTS.md` and this file.
2. Resolve `TARGET` (World B). Ask once: product path and one-sentence idea. If the human said "go", use defaults.
3. If `TARGET/.halo/state.json` exists: read `baton.md` and `state.json`, then resume the phase.
4. Else bootstrap:
   ```bash
   export HALO_SYSTEM=/absolute/path/to/halo
   export TARGET=/absolute/path/to/product
   "$HALO_SYSTEM/scripts/halo" init "$TARGET"
   "$HALO_SYSTEM/scripts/halo" link-skills "$TARGET"
   ```
5. Start the phase machine: `intake` → `specs` → `lock` → `ready` → `scaffold` → `build`.

### AI self-instantiation on this repo

If **you are the AI** and the goal is to instantiate Halo on this repo for your own local use case:

- Set `TARGET` to this repo (factory = product). This is a normal Halo product boot.
- `.halo/` and `.halo-archive/` are local runtime state; they are gitignored and not part of the factory source.
- If a previous `.halo/` exists, it is a leftover local instance. Decide:
  - Continue it: read `.halo/baton.md` and `.halo/state.json`.
  - Reset for a custom use case: `rm -rf .halo .halo-archive` then `halo init .` and run your own intake.
- Customize intake to your local use case and environment. Then `halo specs`, `halo lock`, `halo go`.

## Phase machine

```
bootstrap → intake → spec_pack → spec_review → readiness → scaffold → build → complete
```

Status values: `ACTIVE`, `PAUSED`, `BLOCKED`, `ESCALATED`, `COMPLETE`.

## CLI

```
halo init [path]          bootstrap .halo
halo status [path]        phase / story / demo
halo specs [path]         write .halo/spec/*
halo lock [path]          spec_status → locked
halo unlock [path]        return to spec_review
halo ready [path]         lifecycle readiness gate
halo scaffold [path]      skeleton + Demo 0
halo build [path]         next cycle instructions
halo go [path]            start autonomous mode
halo stop [path]          PAUSE loop
halo resume [path]        ACTIVE
halo continue [path]      refresh NEXT_PROMPT
halo handoff [path]       context pack for another agent
halo doctor [path]        system + product integrity
halo help                 show this list
```

Advanced tooling still lives under `python/` and `scripts/` for direct use.

## Hard rules

1. No product feature code before `spec_status: locked`.
2. No deploy URL to the human without a live HTTP probe.
3. No secrets in chat, logs, or commits.
4. No production deploy.
5. Never delete or weaken tests to go green.
6. One feature per cycle.
7. Feature pass only with GREEN evidence.
8. Inventory the whole v1 lifecycle at readiness.
9. Never conflate World A (factory) with World B (product).

## Build cycle

1. Read `state.json` + `baton.md` + `feature-list.json`.
2. Pick one `passes: false` feature.
3. RED test → implement → GREEN.
4. Run `halo cycle-smoke` (or equivalent smoke test).
5. Write evidence: `.halo/evidence/Sxxx-green.json`.
6. Mark pass: `halo features pass --id Sxxx --evidence ...`.
7. Append progress: `halo progress add --event unit --note ...`.
8. Update `baton.md` and refresh `NEXT_PROMPT.md`.
9. If all features pass and `phase: complete`, emit `<promise>HALO_COMPLETE</promise>`.

## Stop conditions

- Human says stop/pause.
- `status: PAUSED`, `ESCALATED`, `BLOCKED`, `COMPLETE`.
- `max_iterations` reached.
- Budget HALT.
- Kill switch (`state.HALO_KILL_SWITCH`).
- 3 failed attempts on the same story.
- True blocking secrets with no degrade path.

## True loop

`halo go` or `/halo-loop` arms `.halo/loop.json`. On Stop, `hooks/halo-stop-loop.sh` refreshes `NEXT_PROMPT.md` and attempts to re-inject it. Grok Build's Stop hook is passive, so the continue path is headless spawn: `halo continue --spawn`.

## Install (human-run once)

```bash
git clone https://github.com/JamesFincher/halo.git ~/code/halo
grok plugin install ~/code/halo --trust
```

After that, the agent drives.

## Deeper docs

- `AGENTS.md` — binding protocol
- `docs/WORKFLOWS.md` — every agent/human path
- `docs/ARCHITECTURE-DEEP.md` — layers, failure taxonomy, self-modify levels
- `docs/TRUE-LOOP.md` — Stop hook and re-prompt mechanism
- `docs/GROK-BUILD.md` — Grok Build integration
- `docs/GAPS.md` — open/closed gap register
- `docs/ROADMAP.md` — slice status
