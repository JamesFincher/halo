# Halo Gap Analysis — vs peer harnesses

**Method:** Compare to Anthropic long-running harness, Ralph/open-ralph, continuous-claude, Codex long-horizon, OpenHands, grok-halo.

## Peer patterns

| System | Pattern |
|--------|---------|
| Anthropic long-running | `feature-list.json` with `passes: false`; `init.sh` boot ritual; test ratchet |
| Ralph / ralph-loop | Stop hook re-inject; max iterations; completion promise |
| open-ralph | Struggle indicators; status dashboard; iteration history |
| continuous-claude | Intake → PRD → milestones; baton notes |
| Codex long-horizon | Plan.md / Implement.md durable artifacts |
| OpenHands | Context condensation preserving goals + failing tests |
| grok-halo | Budget, Arena dual verify, coverage delta, typed certs |

## Halo strengths

- Instantiation playbook.
- Two-worlds model (factory vs product).
- Phase machine with legal edges.
- Readiness / foresight gate.
- Engineered `NEXT_PROMPT` per inject.
- Stop-hook true loop.
- Live HTTP probe before share.
- `halo doctor --strict`.
- `halo go` autonomous mode.

## Gap register

### P0 — closed

- G01: Machine feature list with `passes: bool` — `feature-list.json` + `halo_features.py`.
- G02: Struggle detection — Stop hook checks git dirty + iteration.
- G03: Completion promise verified — `<promise>HALO_COMPLETE</promise>` + feature-list all pass.
- G04: Test ratchet — doctrine + `halo_ratchet.py` + Stop inject.
- G05: Session boot ritual — progress log + feature list in NEXT_PROMPT.

### P1 — reliability

- G06: Independent verifier runner — `halo_arena.py` dual-lens present; optional `--spawn-check` still open.
- G07: Single-runner lock — `.halo/runner.lock` helper.
- G08: Hard budget stop — `halo_budget.py` + Stop HALT.
- G09: Stories in markdown — `feature-list.json` is source of truth.
- G10: Grok ignores Stop `decision:block` — fallbacks (headless, /goal, /loop).
- G11: Auto-commit discipline — `halo_commit.py` skips gitignored dogfood.
- G12: Plugin install verified — doctor checks loop.json + skills symlink.

### P2 — polish

- G13: CI smoke — `.github/workflows/halo-smoke.yml` + dogfood-track guard.
- G14: CLAUDE.md / AGENTS dual pointer — template + init copy.
- G15: Design-system port — optional later.
- G16: Worktree isolation — open.
- G17: Voice / dashboard — nice-to-have.
- G18: Promise gaming — classifier later; feature-list gate is harder to game.

### P3 — future

- G19: Multi-agent planner/generator/evaluator triad.
- G20: Context condensation policy beyond NEXT_PROMPT.
- G21: Cross-model dual judge.
- G22: Remote Demo0 Vercel automated.

## Failure modes to resist

1. One-shot the app → feature-list + one unit per cycle.
2. Declare victory early → passes false until verified.
3. Delete tests to go green → test ratchet.
4. Thrash without progress → struggle detection.
5. Token death spiral → max_iterations + budget.
6. Context death amnesia → baton + progress + feature-list + NEXT_PROMPT.
7. Self-grade approve → evidence + Arena.
8. Mid-flight SaaS dependency → readiness.
9. 404 demos → probe.
10. Factory/product cwd mix → two worlds.

## Priority to close

1. G06 Arena independent runner.
2. G08 Budget hard stop (done).
3. G11 Auto-commit per story (done).
4. G13 CI smoke (done).
5. G16 Worktrees.

When you close a gap: update this table and `ROADMAP.md`.
