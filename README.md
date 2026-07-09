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
halo init [path]                         bootstrap .halo
halo status [path]                       phase / story / demo
halo baton [path]                        print handoff
halo specs [path]                        write .halo/spec/*
halo lock [path]                         spec_status → locked
halo unlock [path]                       return to spec_review
halo ready [path] [--allow-degraded]     lifecycle readiness gate
halo scaffold [path] [--profile ...]     skeleton + Demo 0
halo milestones [path]                   regenerate milestone prompts
halo probe --url URL                     live HTTP probe
halo build [path]                        next cycle instructions
halo stop [path]                         PAUSE loop
halo resume [path]                       ACTIVE
halo escalate [path] [reason]            write escalation packet
halo triage [path]                       health summary
halo handoff [path]                      context pack for another agent
halo doctor [path] [--strict]            system + product integrity
halo evidence [path]                     validate evidence certs
halo go [path] [--max N] [--spawn]       arm autonomous mode
halo continue [path] [--spawn]           write NEXT_PROMPT; optionally spawn
halo link-skills [path]                  symlink factory skills into product
halo loop [path] [--max N]               arm Stop-hook loop
halo loop-cancel [path]                  disarm loop
halo features [path] sync|summary|pass|fail|seed
halo progress [path] add|tail
halo budget [path] check|show|record|halt
halo ratchet [path]                      test-ratchet scan
halo arena [path] --id Sxxx [--spawn-check]
halo commit-unit [path] --id Sxxx
halo drive [path] spawn|status|should-drive
halo plan [path]                         refresh NEXT_PROMPT
halo watchdog [path] [secs]              planner + spawn loop
halo cycle-smoke [path]                  factory smoke test
halo reinstantiate [path]                reset local control plane
```

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
