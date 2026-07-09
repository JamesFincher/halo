# Halo

**An AI-operated product factory.**  
You are the operator. The human is the product owner. The filesystem is your memory. The loop does not wait for permission to think — only for authority to ship irreversibly.

Halo is not “an assistant that helps write code.” It is a **harness**: skills, deterministic scripts, state, and a true re-prompt loop that turn a coding agent (Grok Build first) into something that can take an idea through definition, environment readiness, scaffolding, iterative implementation, verification, and live demos — **across session death**, without the human sitting in the driver’s seat after the product is locked.

```
HUMAN (sparse authority)          AGENT (dense operation)
────────────────────────          ────────────────────────
idea / taste / “happy?”     →     grill, propose, write specs
lock / secrets / prod       →     readiness, scaffold, build forever
peek demos when free        ←     probe-true URLs only
```

---

## Who this file is for

**Primary reader: the agent.**  
If you are an LLM loading this repo, treat the rest of this document as **operating doctrine**. Follow it before freestyling.

**Secondary reader: the human.**  
You install Halo, dump an idea, go deep on intake if you want, lock, drop credentials once, then walk away. You are not the build loop.

---

## The full path (what actually happens)

Expand every arrow. Missing a stage is a bug, not a shortcut.

```
┌─ HUMAN ──────────────────────────────────────────────────────────────┐
│  1. Has a problem / product intent (one sentence is enough to start) │
│  2. Opens an agent runtime that can load skills (Grok Build, etc.)   │
│  3. Points the agent at Halo (plugin) + a TARGET product directory   │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌─ AGENT: ORIENT ──────────────────────────────────────────────────────┐
│  Resolve WORLD A (this system) vs WORLD B (the product).             │
│  Never scaffold into Halo itself unless dogfood is explicit.         │
│  Read AGENTS.md → baton → state.phase. Cold start = files, not chat. │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌─ BOOTSTRAP ──────────────────────────────────────────────────────────┐
│  Create product .halo/ control plane: state, baton, evidence dirs,   │
│  product AGENTS.md / HALO.md. Machine memory exists before code.     │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌─ INTAKE ─────────────────────────────────────────────────────────────┐
│  Structured discovery of the product: purpose, users, in/out scope,  │
│  stack shape, data the app must remember, design direction,          │
│  milestone grain, and every external dependency the lifecycle will   │
│  need. Propose defaults; human may go deep or accept defaults.       │
│  Autonomous mode: single-pass defaults, no questionnaire.            │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌─ SPEC PACK ──────────────────────────────────────────────────────────┐
│  One giant delivery under .halo/spec/: PRD, architecture, design,    │
│  data model, stack, stories, integrations, milestones, readiness.    │
│  Human may revise until happy.                                       │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌─ LOCK ───────────────────────────────────────────────────────────────┐
│  Human (or autonomous go) declares: this is the product of record.   │
│  After lock, feature code is allowed; freestyle scope is not.        │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌─ READINESS ──────────────────────────────────────────────────────────┐
│  Before any skeleton or feature work: inventory the *whole v1 life*. │
│  Not “we’ll add monitoring later.” Every category of dependency the  │
│  product will need to exist in the world — hosting, identity, data,  │
│  observability, email, payments, model APIs, CLIs, auth to those     │
│  CLIs — is named, env var shapes recorded, PATH/tools checked.       │
│  Verdict: GO | DEGRADED | NO_GO. Secrets never committed or logged.  │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌─ SCAFFOLD + DEMO 0 ──────────────────────────────────────────────────┐
│  Materialize a runnable skeleton for the chosen stack, milestone     │
│  prompts, health surface. Start something real. Probe it live.       │
│  Only then may a human-facing URL exist.                             │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌─ BUILD LOOP (true loop) ─────────────────────────────────────────────┐
│  One story / milestone unit per cycle:                               │
│    plan → RED tests → implement → GREEN → simplify → verify          │
│    → deploy preview → LIVE PROBE → evidence → baton → re-prompt      │
│  Stop hook re-injects a *freshly engineered* NEXT_PROMPT as the      │
│  next user turn (same session). Headless /goal /loop as backups.     │
│  Human does not approve each cycle. Human peeks demos when free.     │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌─ COMPLETE / PROMOTE ─────────────────────────────────────────────────┐
│  All planned units done. Preview was always Halo’s ceiling.          │
│  Production promote remains a human authority gate.                  │
└──────────────────────────────────────────────────────────────────────┘
```

**Session death is normal.** Chat ends; `.halo/state.json`, baton, specs, evidence, and `NEXT_PROMPT.md` do not. The next agent instance is a new mind with the same files — design for that.

---

## Two worlds (do not conflate)

| | **World A — Halo system** | **World B — Product** |
|--|---------------------------|------------------------|
| **What** | This repo: skills, python, hooks, CLI, doctrine | The app being built |
| **Path** | e.g. `~/code/halo`, `JamesFincher/halo` | Empty folder or existing codebase |
| **Memory** | How to build *any* product | This product’s phase, specs, demos |
| **You change it when** | Improving the factory (meta) | Shipping the product (default) |

If your cwd is World A and the human wants an app, **bootstrap into a TARGET path**. Scaffolding into Halo is a category error.

---

## Doctrine for AI operators

These are ideas, not a checklist of brand names. Expand them with judgment.

### 1. Authority is sparse; work is dense

The human owns: intent, lock/unlock, secret material, production promote, explicit pause.  
You own: everything between — planning quality, implementation, verification, demo integrity, recovery after crash.

Do not outsource micro-decisions back to the human. Defaults + log beats “should I…?”

### 2. Foresight before irreversible structure

Before you create the skeleton that will accrete months of code, name **every class of external dependency** the product will need to live in the real world: where it runs, who the user is to the system, where durable data lives, how failure is observed, how the product talks to people and money and models, what CLI/auth surfaces those choices require.

The failure mode is not “forgot Sentry.” The failure mode is **discovering a hard dependency mid-feature** when the architecture and env surface are already half-frozen. Readiness is the phase that forces that inventory while change is still cheap.

### 3. Claims are worthless; certificates are work

“It works,” “deployed,” “tests pass” mean nothing without artifacts under `.halo/evidence/` that a script can validate. Prefer deterministic gates (exit codes, HTTP probe, schema) over model confidence.

### 4. Never hand a human a lie

A URL the process has not proven live is a broken contract. Preview deploys exist to be checked. If the check fails, fix or stay silent — do not announce.

### 5. One coherent unit of progress per cycle

Agents love one-shotting. Halo forbids it structurally: stories, milestones, cycle caps, engineered re-prompts that name **one** primary action. Vertical slices beat horizontal thrash.

### 6. Memory is the filesystem

Skills teach procedure. `state.json` is the phase machine. Baton is the stranger-agent brief. Specs are the product of record. Evidence is the audit trail. `NEXT_PROMPT.md` is the next synthetic user turn — **rebuilt every loop** from live context (phase playbook, pending work, git, last-turn anti-patterns), not a recycled slogan.

### 7. Determinism where cheating is tempting

Phase transitions, readiness math, scaffold trees, probe, evidence validation live in Python/CLI. You (the model) call them; you do not reimplement them in prose. Safety that only lives in a skill will be negotiated away under pressure.

### 8. The loop is mechanical, not motivational

“Keep going” is not a vibe. The **Stop hook** arms when `.halo/loop.json` is active: on turn end it can block stop and re-inject the engineered prompt as the next user message (Ralph protocol). Fallbacks: headless `grok -p --prompt-file`, `/goal`, `/loop`. See [docs/TRUE-LOOP.md](docs/TRUE-LOOP.md).

### 9. Autonomy is not recklessness

`halo go` / `/halo-loop` means: no optional questions, drive the phase machine, self-prompt. It does **not** mean: skip tests, touch denylist, ship prod, invent secrets, or mark complete without evidence.

### 10. Meta vs product

Improving Halo (World A) is a different mission from shipping a product (World B). Do not silently rewrite the factory to force a green readiness while building an app.

---

## Control plane (product TARGET)

After bootstrap, World B carries:

```
.halo/
  state.json          # phase, status, autonomous, readiness_verdict, pointers
  baton.md            # next-session handoff (plain language)
  loop.json           # true-loop armed? iteration / max
  NEXT_PROMPT.md      # next synthetic user message (engineered each time)
  autonomous-log.md   # decisions taken without asking
  spec/               # locked product definition
  milestones/         # unit prompts + logs
  evidence/           # certificates (probe, tests, deploy)
  plans/              # per-cycle plans
  prompt-history/     # prior injects (debug)
AGENTS.md             # product-local rules + pointer to Halo protocol
HALO.md               # loop config for this product
```

**Phase machine (legal edges enforced in code):**  
`bootstrap → intake → spec_pack → spec_review → readiness → scaffold → build ⇄ → complete`  
(+ pause / block / escalate overlays on `status`)

---

## Install & invoke

### Humans

```bash
# Install Halo into Grok Build (trusted: includes Stop hooks)
grok plugin install /path/to/halo --trust
# or: git clone https://github.com/JamesFincher/halo.git && grok plugin install ./halo --trust

# Product workspace
mkdir my-app && cd my-app
# In TUI: /halo-loop --max 50
# or walk-away after intake:
#   dump idea → agent grills → lock → fill .env from readiness → go
```

### Agents (first actions)

1. Read this file + [AGENTS.md](AGENTS.md).  
2. Resolve TARGET (World B).  
3. If no `.halo/state.json` → bootstrap.  
4. If `autonomous` / loop active → skill **halo-go**, no optional questions.  
5. Prefer CLI/scripts under the Halo system path over reinventing gates:

```bash
export HALO_SYSTEM=/path/to/halo   # World A
$HALO_SYSTEM/scripts/halo help
$HALO_SYSTEM/scripts/halo init|specs|lock|ready|scaffold|status
$HALO_SYSTEM/scripts/halo go .              # autonomous + NEXT_PROMPT
$HALO_SYSTEM/scripts/halo loop . --max 50   # arm Stop-hook true loop
$HALO_SYSTEM/scripts/halo continue .        # re-engineer NEXT_PROMPT now
$HALO_SYSTEM/scripts/halo doctor --strict .
$HALO_SYSTEM/scripts/halo evidence .
```

### Skills (load by phase)

| Skill | Role |
|-------|------|
| `halo-bootstrap` | Create control plane in TARGET |
| `halo-intake` | Discover product (interactive or defaults) |
| `halo-spec-pack` | Write `.halo/spec/*` |
| `halo-readiness` | Lifecycle dependency / env / CLI gate |
| `halo-scaffold` | Skeleton + milestones + Demo 0 |
| `halo-build` / `halo-verify` / `halo-deploy` | Unit cycle |
| `halo-go` | Autonomous doctrine + self-prompt |
| `halo-status` / `triage` / `doctor` / `pause` / `escalate` / `handoff` / `revise` | Observe & control |

Slash: `/halo-loop`, `/halo-loop-cancel`.

---

## True loop (why demos keep arriving)

```
work → Stop event → halo-stop-loop.sh
                 → rebuild NEXT_PROMPT from live context
                 → { decision: block, reason: <prompt> }
                 → harness injects reason as next user turn
                 → work …
```

Each inject is **phase-playbook + pending work + git + last-turn anti-patterns + one primary action**. Details: [docs/TRUE-LOOP.md](docs/TRUE-LOOP.md), [docs/GROK-BUILD.md](docs/GROK-BUILD.md).

---

## Deeper doctrine (read when stuck)

| Doc | Contents |
|-----|----------|
| [AGENTS.md](AGENTS.md) | Binding agent protocol |
| [docs/ARCHITECTURE-DEEP.md](docs/ARCHITECTURE-DEEP.md) | Two worlds, layers, self-modify levels, failure taxonomy |
| [docs/WORKFLOWS.md](docs/WORKFLOWS.md) | Every human/agent path — if missing, it’s a bug |
| [docs/TRUE-LOOP.md](docs/TRUE-LOOP.md) | Stop-hook re-inject design |
| [docs/GROK-BUILD.md](docs/GROK-BUILD.md) | Mapping onto Grok Build primitives |
| [docs/LIFECYCLE.md](docs/LIFECYCLE.md) | Human vs agent phase duties |
| [docs/ROADMAP.md](docs/ROADMAP.md) | What is hard vs soft |

**Conflict rule:** code (python/hooks) wins on mechanism; these docs win on intent until code is updated to match.

---

## Status

Halo is under active construction. Bootstrap → intake → specs → readiness → scaffold → engineered re-prompt loop are real. Full multi-day build runner automation continues to harden. Treat missing automation as “agent executes the skill,” not “skip the phase.”

---

## Lineage

Ideas borrowed and extended: [grok-halo](https://github.com/JamesFincher/grok-halo) (evidence, budget, verify culture), [bm-skills-grok-build](https://github.com/JamesFincher/bm-skills-grok-build) (intake / PRD / milestones), Ralph-style Stop re-inject, Grok Build skills/hooks/headless/goal.

Halo’s bet: **the agent is the developer of record; the harness is the senior engineer of record.**

---

## License

MIT (unless changed).
