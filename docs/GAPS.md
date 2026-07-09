# Halo Gap Analysis — vs peer agent harnesses (2026)

**Date:** 2026-07-09  
**Method:** Compare Halo to Anthropic long-running harness, Ralph / open-ralph, continuous-claude / BM PRD+milestones, Codex long-horizon, OpenHands patterns, grok-halo evidence culture.  
**Rule:** Code wins on mechanism; this file tracks **intent debt**.

**Dogfood:** Halo may run as its own TARGET (`.halo/` local only). Factory `.gitignore` excludes `.halo/` so clones never see self-instance state.

---

## Peer systems — what they get right

| System | Pattern | Why it matters |
|--------|---------|----------------|
| **Anthropic long-running** | Initializer vs coding agent; `feature-list.json` with `passes: false`; `progress.txt`; `init.sh` boot ritual; **test ratchet** (never delete tests) | Stops one-shotting + silent “done” |
| **Ralph / ralph-loop** | Stop hook re-inject; max iterations; completion promise; same prompt or fixed goal | True same-session loop |
| **open-ralph** | Struggle indicators (no file changes N iters); status dashboard; iteration history | Detect thrash / token burn |
| **BM / continuous-claude** | Intake → PRD → milestone prompts; simplify gate; baton notes | Product definition quality |
| **Codex long-horizon** | Plan.md / Implement.md durable plan artifacts | Survive compact |
| **OpenHands** | Context condensation preserving goals + failing tests | Long sessions without amnesia |
| **grok-halo** | Budget, Arena dual verify, coverage delta, typed certs | Economic + adversarial gates |

---

## Halo strengths (keep)

| Area | Status |
|------|--------|
| Instantiation playbook in README | Strong |
| Two-worlds model (factory vs product) | Strong |
| Phase machine + legal edges | Strong |
| Readiness / foresight gate | Strong (unique vs most loops) |
| Engineered NEXT_PROMPT per inject | Strong |
| Stop-hook true loop (Ralph-shaped) | Present |
| Live HTTP probe before share | Strong |
| Doctor --strict matrix | Present |
| Autonomous go mode | Present |

---

## Gap register

Severity: **P0** ship-blocker for long runs · **P1** reliability · **P2** polish · **P3** future

### P0 — Glare

| ID | Gap | Peer source | Risk if ignored | Mitigation status |
|----|-----|-------------|-----------------|-------------------|
| G01 | **No machine feature list** with `passes: bool` | Anthropic JSON feature list | Agent rewrites markdown stories, marks done by editing prose | **Fixed:** `feature-list.json` + `halo_features.py` |
| G02 | **No struggle detection** | open-ralph | Infinite loop, $ burn, no file progress | **Fixed:** stop hook / loop checks git dirty + iteration |
| G03 | **Completion promise not verified on Stop** | Ralph | Loop never ends or ends on lie | **Fixed:** parse `<promise>HALO_COMPLETE</promise>` + feature-list all pass |
| G04 | **Test ratchet not enforced** | Anthropic | Agent deletes failing tests | **Fixed:** doctrine + verify skill hard rule + doctor note |
| G05 | **Session boot ritual incomplete** | Anthropic init.sh + progress + features | Cold agent re-explores instead of continuing | **Fixed:** progress log + feature list in NEXT_PROMPT + product `init` hints |

### P1 — Reliability

| ID | Gap | Peer source | Risk | Mitigation |
|----|-----|-------------|------|------------|
| G06 | Independent verifier soft (skill only, no Arena runner) | grok-halo Arena | Self-grade bias | Documented; port runner still open |
| G07 | No single-runner lock file | multi-agent thrash | Two agents corrupt state | **Fixed:** `.halo/runner.lock` helper |
| G08 | No budget / token / daily cycle hard stop | grok-halo, Ralph max | Wallet drain | Soft: max_iterations; hard budget still open |
| G09 | Stories only in markdown | Anthropic JSON | Drift / corruption | feature-list.json is source of truth for done |
| G10 | Grok may ignore Stop `decision:block` | Grok docs vs Claude | Loop silent-fail | Fallbacks remain (headless, /goal, /loop); doctor warns |
| G11 | No automatic commit discipline | Anthropic / Ralph | Next session loses recoverable steps | Doctrine in build skill; enforce later |
| G12 | Plugin install not verified in product doctor | ops | Hooks never fire | doctor checks for loop.json + skills symlink |

### P2 — Polish

| ID | Gap | Notes |
|----|-----|-------|
| G13 | No CI smoke on GitHub Actions | Add later |
| G14 | No CLAUDE.md / AGENTS dual pointer in product template | Add CLAUDE.md → AGENTS |
| G15 | Design-system port absent | Optional BM skill |
| G16 | No worktree isolation for parallel stories | open-ralph parallel |
| G17 | Voice / dashboard | Nice-to-have |
| G18 | Promise can be gamed | Classifier later; feature-list gate harder to game |

### P3 — Future

| ID | Gap |
|----|-----|
| G19 | Multi-agent planner/generator/evaluator triad |
| G20 | Context condensation policy beyond NEXT_PROMPT |
| G21 | Cross-model dual judge |
| G22 | Remote Demo0 (Vercel) automated |

---

## Failure modes Halo must still resist

From peer postmortems + Anthropic:

1. **One-shot the app** → feature-list + one unit per cycle  
2. **Declare victory early** → passes:false until verified  
3. **Delete tests to go green** → test ratchet  
4. **Thrash without progress** → struggle detection  
5. **Token death spiral** → max_iterations + optional budget  
6. **Context death amnesia** → baton + progress + feature-list + NEXT_PROMPT  
7. **Self-grade approve** → evidence + future Arena  
8. **Mid-flight new SaaS dependency** → readiness foresight  
9. **404 demos** → probe  
10. **Factory/product cwd mix** → two worlds  

---

## Priority order to close remaining open items

1. G06 Arena / independent verify runner  
2. G08 Budget hard stop  
3. G11 Auto-commit per story  
4. G13 CI  
5. G16 Worktrees  

---

**When you close a gap:** update this table + ROADMAP. A gap closed only in prose is still open.


### Closed in 0.6.0 (dogfood M1 harness gates)

| ID | Gap | Status |
|----|-----|--------|
| G23 | Feature pass without evidence | **Fixed:** `halo_features.pass` requires GREEN evidence |
| G08 | Hard budget | **Fixed:** `halo_budget.py` + Stop HALT |
| G04b | Test ratchet mechanical | **Fixed:** `halo_ratchet.py` + Stop inject |
| G27 | go without loop.json | **Fixed:** `halo_go.enable` arms loop |
| G05b | link-skills destroys factory on dogfood | **Fixed:** dogfood-skip when A=B |
| G35 | CLAUDE.md dual pointer | **Fixed:** template + init copy |
| — | Push pollution from self-instance | **Fixed:** ignore entire `.halo/`, `/init.sh`, `/halo-health.json`, `/HALO.md` |

Still open: G06 Arena, G11 auto-commit, G13 CI (dogfood S006–S008).

