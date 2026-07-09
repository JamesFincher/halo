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

# START HERE — Instantiation playbook

**If you are an AI and the human just pointed you at this repo:**  
Your **first reply** must not be a vague summary. Run the playbook below, then tell the human **exactly what to do next** (paths, commands, what you need from them). That first message *is* the onboarding.

**If you are a human:** open this repo in your coding agent and say *“start Halo”* / *“instantiate”* / *“read the playbook and set me up.”* Your agent should answer with the next steps from §1–§4.

---

## 0. What “point AI at Halo” means

There are **two directories**. Confusing them breaks everything.

| Directory | Call it | Purpose |
|-----------|---------|---------|
| **This repo** (where `README.md` + `.grok/skills/halo-*` live) | **World A — Halo system** | The factory instructions + tools |
| **Where the app will live** (empty folder or existing app) | **World B — product TARGET** | The thing that gets built and demoed |

- Opening **only** World A → agent learns *how* to run Halo, then must bootstrap a TARGET.  
- Opening **only** World B with no prior bootstrap → agent has no Halo state yet; must install/link Halo first.  
- Best path: install Halo once, open World B, agent bootstraps `.halo/` into B.

---

## 1. First agent actions (in order)

Do these **before** writing product feature code.

### Step A — Confirm you can see Halo

```bash
# You should be able to find these relative to the Halo system checkout:
ls AGENTS.md README.md .grok/skills/halo-go/SKILL.md scripts/halo python/halo_state.py
```

If the human opened a **clone of this GitHub repo**, cwd *is* World A.  
If they only installed the plugin and opened an empty app folder, set:

```bash
export HALO_SYSTEM=/absolute/path/to/halo   # World A checkout
# or wherever they cloned it
```

### Step B — Get Halo onto the machine (tell the human if not done)

**Human does this once** (or agent runs it with approval):

```bash
# Clone the factory (World A)
git clone https://github.com/JamesFincher/halo.git ~/code/halo
cd ~/code/halo

# Grok Build: install as trusted plugin (skills + Stop-hook loop)
grok plugin install ~/code/halo --trust

# Optional: put CLI on PATH for this shell
export HALO_SYSTEM=~/code/halo
alias halo='$HALO_SYSTEM/scripts/halo'
```

Other runtimes: ensure project/plugin skills can load `~/code/halo/.grok/skills/*` and that `python3` can run `$HALO_SYSTEM/python/*.py`.

### Step C — Choose / create the product TARGET (World B)

**Ask once** (or use a default if human said “go” / autonomous):

- Path to new or existing product, e.g. `~/code/my-app`
- One-sentence product idea if they have it

```bash
mkdir -p ~/code/my-app   # if greenfield
export TARGET=~/code/my-app
export HALO_SYSTEM=~/code/halo
```

**Never** use `~/code/halo` as TARGET unless the human explicitly wants to dogfood Halo on itself.

### Step D — Bootstrap the product (creates the control plane)

```bash
cd "$TARGET"
"$HALO_SYSTEM/scripts/halo" init .
"$HALO_SYSTEM/scripts/halo" link-skills .
# Creates: .halo/state.json, baton.md, product AGENTS.md, HALO.md, skills symlinks
```

Agent skill equivalent: **`halo-bootstrap`** (same outcome).

### Step E — Tell the human what happens next (template)

After bootstrap, your message to the human should look like this (fill real paths):

```markdown
## Halo is ready to run on your product

**Factory (World A):** `~/code/halo`  
**Product (World B):** `~/code/my-app`  
**State:** `.halo/state.json` phase=`intake`

### What I need from you
1. **Product idea** in your own words (one paragraph is enough).  
   Or say **“go”** / **“use defaults”** and I’ll decide and proceed.
2. Optional: how deep to grill (quick defaults vs full interview).
3. Later (after lock): fill `.env` from the readiness checklist — never paste secrets in chat if you can avoid it.

### What I’ll do next
1. Intake → write full `.halo/spec/*` (PRD, architecture, stories, …).  
2. You review specs and say **lock** (or I auto-lock if you said **go**).  
3. Readiness gate (hosting, auth, data, observability, CLIs — whole v1 life).  
4. Scaffold + Demo 0 (live probe before any URL).  
5. Build loop; I’ll re-prompt myself via Halo’s loop when armed.

### Commands you can run anytime
- Status: `~/code/halo/scripts/halo status ~/code/my-app`
- Walk away: in product dir, `/halo-loop` or `~/code/halo/scripts/halo loop . --max 50`
- Stop loop: `/halo-loop-cancel` or `halo loop-cancel`
- Pause: `halo stop .`

### Files to open
- Doctrine: `~/code/halo/README.md` (this file)
- Protocol: `~/code/halo/AGENTS.md`
- After specs exist: `~/code/my-app/.halo/spec/PRD.md`
```

Then **start intake** (skill `halo-intake` or autonomous single-pass if they said go).

---

## 2. Instantiation paths (pick one)

### Path H1 — Human has Grok Build, wants a new product

| # | Who | Action |
|---|-----|--------|
| 1 | Human | `git clone https://github.com/JamesFincher/halo.git ~/code/halo` |
| 2 | Human | `grok plugin install ~/code/halo --trust` |
| 3 | Human | `mkdir -p ~/code/my-app && cd ~/code/my-app && grok` (or open folder in TUI) |
| 4 | Human | Say: *“Start Halo for this folder. Product idea: …”* or *“go”* |
| 5 | Agent | `halo init` + `link-skills` + intake → … (playbook §1) |
| 6 | Human | Review `.halo/spec/*` when offered → **lock** (unless go) |
| 7 | Human | Fill `.env` from readiness / `.env.example` |
| 8 | Human | Optional: `/halo-loop` and walk away; peek demos when notified |

### Path H2 — Human already has a half-built app

Same as H1, but TARGET is the existing app path. Agent must **detect stack** and use non-destructive scaffold (`existing` profile). Intake scopes *delta*, not rewrite-from-scratch, unless human asks for greenfield.

### Path H3 — Human only opened the Halo git repo (no product yet)

Agent **must not** start implementing a random app inside Halo.

First message to human:

```markdown
You’re in the **Halo factory repo**, not a product repo.

**Next for you:**
1. Pick where the product should live, e.g. `mkdir -p ~/code/my-app`
2. Reply with: path + product idea  
   or: “use ~/code/my-app and go”

**Next for me:** bootstrap that path, then intake.
```

### Path H4 — Autonomous (“go” / walk away)

```bash
export HALO_SYSTEM=~/code/halo
export TARGET=~/code/my-app
mkdir -p "$TARGET"
"$HALO_SYSTEM/scripts/halo" init "$TARGET"
"$HALO_SYSTEM/scripts/halo" link-skills "$TARGET"
"$HALO_SYSTEM/scripts/halo" go "$TARGET" --max 10
"$HALO_SYSTEM/scripts/halo" loop "$TARGET" --max 50   # arm Stop-hook true loop
# Agent: skill halo-go — defaults only, no optional questions
```

### Path H5 — Dogfood (build Halo with Halo)

Allowed **only when explicit**. TARGET = this factory repo.

```bash
export HALO_SYSTEM=~/code/halo
cd "$HALO_SYSTEM"
./scripts/halo init .          # creates local .halo/ (gitignored)
./scripts/halo go . --max 30   # arms true loop on Halo itself
# Work feature-list items; polish the factory
```

**Clone hygiene (non-negotiable):**  
The factory `.gitignore` ignores **all of** `.halo/`, plus dogfood leftovers (`/init.sh`, `/halo-health.json`, `/HALO.md`).  
Maintainers **never** `git add -f .halo/`. CI fails if dogfood paths are tracked.  

When someone clones Halo to use on *their* product, they get skills/python/hooks/docs only — **not** our self-instance baton, evidence, specs, or loop counters. Their product’s `.halo/` lives in *their* TARGET repo.

---

## 3. What “bootstrapped” means (definition of ready)

TARGET is instantiated when **all** of these exist:

| Artifact | Meaning |
|----------|---------|
| `.halo/state.json` | Phase machine lives |
| `.halo/baton.md` | Next-session handoff |
| `AGENTS.md` (product) | Local rules + Halo pointer |
| `HALO.md` | Loop config stub |
| Skills visible | Via plugin install **or** `halo link-skills` → `.grok/skills/halo-*` |

Not yet required at bootstrap: specs, readiness GO, app code. Those come in later phases.

---

## 4. After bootstrap — phase cheat sheet for the agent

| `state.phase` | Load skill / command | Human role |
|---------------|----------------------|------------|
| `intake` | `halo-intake` or go-defaults | Idea + depth preference |
| `spec_pack` / `spec_review` | `halo-spec-pack` / `halo specs` | Read specs, lock or revise |
| `readiness` | `halo ready` | Fill `.env` once for whole v1 life |
| `scaffold` | `halo scaffold` | Peek Demo 0 if URL probed |
| `build` | `halo-build` + loop | Peek demos; promote prod later |
| `complete` | stop loop | Promote if desired |

Always: read **baton** first on a cold session.

---

## 5. Verify instantiation

```bash
export HALO_SYSTEM=~/code/halo
"$HALO_SYSTEM/scripts/halo" doctor --strict "$HALO_SYSTEM"   # factory healthy
"$HALO_SYSTEM/scripts/halo" status "$TARGET"                 # product phase
"$HALO_SYSTEM/scripts/halo" doctor "$TARGET"                 # product integrity
ls "$TARGET/.halo/state.json" "$TARGET/.grok/skills/halo-go"
```

---

## Who this file is for (after you’re running)

**Primary reader: the agent.**  
Doctrine and playbooks below are operating rules. Instantiation is § START HERE.

**Secondary reader: the human.**  
You clone, install plugin, name a TARGET and an idea, lock specs, supply secrets once, then walk away. You are not the build loop.

---

## The full path (what actually happens after instantiate)

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
