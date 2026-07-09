# AGENTS.md — Halo System Protocol

**Voice**: Dark. Direct. Evidence-first. No vibes.

**Prime directive**: Human idea → locked specs → ready lifecycle → autonomous ship. Root cause dies. Dead demos never shared.

## First contact

If this is a cold open of the Halo system repo or the human says `start / instantiate / set up Halo`:

1. Read `README.md` first contact.
2. Resolve World A (this repo) vs World B (product TARGET).
3. If `TARGET/.halo/state.json` exists: read `baton.md` and resume the phase.
4. Else: bootstrap `.halo/` into TARGET, then `link-skills`, then intake.

## Self-instantiate decision tree

```
1. Is cwd the Halo system repo (README.md + .grok/skills/halo-*)?
   YES → README first contact. Get TARGET + idea (or go).
         If TARGET == this repo (AI self-instantiation): factory = product.
         Else: bootstrap into TARGET.

2. Does TARGET / cwd contain .halo/state.json?
   YES → Read phase. Resume from baton.md. Load the skill for the phase.
         If the repo is the factory and .halo/ exists: it is a leftover local instance.

3. Empty or non-Halo project?
   YES → HALO_SYSTEM + init + link-skills → intake (or halo-go if autonomous).
```

## AI self-instantiation on this repo

When the AI is the operator and the product is the Halo repo itself:

- `TARGET` = this repo. `HALO_SYSTEM` = this repo.
- `.halo/` and `.halo-archive/` are local runtime state; they are gitignored and not part of the factory source.
- Existing `.halo/` → resume from `baton.md` if it matches your use case.
- Fresh custom use case → remove `.halo/` and `.halo-archive/`, then `halo init .` and run your own intake.
- Customize intake to your local use case and environment.
- Never `git add -f .halo/` or `.halo-archive/`.

## Phases (v0)

| Phase | Skill | Human | Output |
|-------|-------|-------|--------|
| 0 Bootstrap | `halo-bootstrap` | low | `.halo/`, product AGENTS.md, state |
| 1 Intake | `halo-intake` | high | locked decisions (or defaults if go) |
| 2 Spec pack | `halo-spec-pack` / `halo_spec_write.py` | review | `.halo/spec/*` |
| 2b Spec iterate | chat + rewrite | until happy | revised pack |
| 3 Readiness | `halo-readiness` | secrets once | `.halo/readiness.json` GO/NO_GO/DEGRADED |
| 4 Scaffold | `halo-scaffold` | none | skeleton + Demo 0 |
| 5 Milestones | derived from specs | none | `.halo/milestones/` + stories |
| 6 Build loop | `halo-build` | async demos | code + live preview URLs |
| 7 Complete | — | promote prod | all stories deployed |

## Autonomous mode

`/go` or `halo go` arms the loop. Defaults win. No optional questions. Drive the phase machine until a hard stop. After every unit, refresh `NEXT_PROMPT.md`.

## Hard rules

1. No code for product features before `spec_status: locked`.
2. No deploy URL to the human without a live probe (HTTP 200/30x).
3. Whole-lifecycle foresight at readiness.
4. Async demos — do not block waiting for human approval unless `require_human_gate: true`.
5. Grok Build first — skills live in `.grok/skills/`; Python in `python/`.
6. Intake is interactive only when `autonomous` is false.
7. PRD is what, not how.
8. Test ratchet — never delete or weaken tests to go green.
9. Done tracking — `.halo/feature-list.json` `passes: bool` is machine truth.
10. Progress log — append via `halo_progress.py` after each unit.
11. Evidence-gated pass — `halo features pass` requires GREEN evidence or human `--force`.
12. Budget — `halo budget check`; Stop honors max_iterations / daily / wall / halt.
13. Local self-improvement — allowed when explicit; never push `.halo/` state. Ship only protocol code.

## Artifact map (product)

```
.halo/
  state.json
  baton.md
  loop.json
  NEXT_PROMPT.md
  autonomous-log.md
  spec/
  milestones/
  evidence/
  plans/
  prompt-history/
  readiness.json
AGENTS.md
HALO.md
```

## Skill load order

1. `halo-bootstrap`
2. `halo-intake`
3. `halo-spec-pack`
4. Lock
5. `halo-readiness`
6. `halo-scaffold`
7. `halo-build` / `halo-verify` / `halo-deploy`
8. `halo-go`

## CLI

```bash
./scripts/halo help
./scripts/halo status
python3 python/halo_state.py --help
python3 python/halo_probe.py --url https://example.com
```

Prefer `scripts/halo` and `python/` tools over ad-hoc shell for state mutations.

## Stop conditions

- User says stop / pause → write baton, set state `PAUSED`.
- Missing secrets after readiness → `BLOCKED` with checklist only.
- Three failed build attempts on the same story → escalate.
- Budget HALT.
- Kill switch.
- Denylist or production deploy.

When unsure: re-read this file and `.halo/baton.md`. Do not freestyle lifecycle.
