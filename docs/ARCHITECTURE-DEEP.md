# Halo Deep Architecture — AI-Centric, Self-Building Systems

**Purpose of this document:** Explain what actually happens when Halo runs, why the design is novel, what can go wrong, and the discipline required so we do not miss critical paths as the system evolves.

**Audience:** Humans designing Halo + agents modifying Halo or running products.

If something in this doc conflicts with code, **code wins for mechanism**; **this doc wins for intent** until the code is updated to match.

---

## 1. The novel claim

Most “AI coding tools” are **chat over a repo**: human drives, model responds, memory dies with the session.

Halo is different on three axes:

| Axis | Normal agent | Halo |
|------|--------------|------|
| **Who operates** | Human issues every step | Agent is the primary operator after intake lock |
| **What persists** | Chat transcript (lossy) | Filesystem control plane (state, baton, specs, evidence) |
| **What is being built** | One app | A **product** *and* the **procedure that builds products** (skills/scripts) |

Halo is therefore both:

1. **A product factory** (turns ideas into apps with demos).
2. **A meta-system** (procedures that can improve the factory itself).

That second layer is where novelty and danger live. Self-build / self-modify is not a slogan — it is a recursive architecture that must be constrained or it eats itself.

---

## 2. Two worlds (never conflate)

```
┌─────────────────────────────────────────────────────────────┐
│  WORLD A — HALO SYSTEM REPO                                 │
│  github.com/JamesFincher/halo  ·  ~/code/halo               │
│                                                             │
│  Contains: skills, python/, scripts/halo, templates, docs   │
│  Role:    "operating system" for product development        │
│  Changes: only via deliberate meta-work (improve Halo)      │
└────────────────────────────┬────────────────────────────────┘
                             │ install / invoke / copy templates
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  WORLD B — PRODUCT REPO                                     │
│  any app: empty folder or existing codebase                 │
│                                                             │
│  Contains: app code + .halo/ runtime memory + AGENTS.md     │
│  Role:    the thing demos, deploys, ships to users          │
│  Changes: every build cycle                                 │
└─────────────────────────────────────────────────────────────┘
```

### Hard rule

**World A is not a product.** Bootstrap must refuse (or require explicit dogfood flag) to treat the Halo system repo as TARGET.

**World B never owns the truth of “how Halo works.”** Product `.halo/` holds *this product’s* phase and specs. The *protocol* lives in World A skills/docs. Product `AGENTS.md` is a **pointer + local rules**, not a full copy of Halo’s brain (copies drift).

### Why agents get this wrong

Context windows load whatever is open. If cwd is World A and the user says “build my app,” a naive agent scaffolds into Halo itself. The decision tree in root `AGENTS.md` exists to prevent that. Any new skill must restate: **resolve TARGET first.**

---

## 3. Layered architecture

Think in five layers. Lower layers must not depend on higher ones.

```
L5  HUMAN INTENT     idea, taste, lock/unlock, secrets, prod promote
L4  AGENT JUDGMENT   intake dialogue, plan quality, code design, critique
L3  SKILL PROTOCOL   SKILL.md procedures — what the agent is allowed to do when
L2  DETERMINISTIC    python/ + scripts/halo — state, probe, scaffold, readiness
L1  ARTIFACTS        .halo/*, git, evidence files — survive session death
```

| Layer | Trust | Fail mode if weak |
|-------|-------|-------------------|
| L5 | Highest authority | Wrong product built correctly |
| L4 | Untrusted without L2 gates | Hallucinated “done”, fake deploys |
| L3 | Contract | Skills ignored → freestyle chaos |
| L2 | High trust (stdlib scripts) | Bugs are systemic — fix immediately |
| L1 | Source of truth | Without baton/state, multi-session death |

### Design implication

**Anything safety-critical must live in L2 or L1**, not in prose skills alone:

- Phase transitions → `halo_state.py` / CLI  
- “Is URL live?” → `halo_probe.py` (not model opinion)  
- Readiness GO/NO_GO → `halo_readiness.py`  
- Scaffold file trees → `scaffold/*.py`  

Skills (L3) tell the agent *when* to call L2. They do not replace L2.

---

## 4. Control plane vs data plane

### Control plane (orchestration)

| Artifact | Job |
|----------|-----|
| `.halo/state.json` | Machine status, phase, verdicts, pointers |
| `.halo/baton.md` | Human-readable next action for cold sessions |
| Skills + WORKFLOWS.md | What transitions exist |
| `scripts/halo` | Stable verbs humans/agents share |

### Data plane (product value)

| Artifact | Job |
|----------|-----|
| App source | The product |
| `.halo/spec/*` | Locked product definition |
| `.halo/milestones/*` | Work units + logs |
| Deployed previews | Human-visible progress |
| `.halo/evidence/*` | Proof, not claims |

**Invariant:** Progress is only real when data plane changes are *backed by* control plane + evidence.  
A green chat message with no state/evidence update is **not progress**.

---

## 5. The runtime story: what actually happens

### 5.1 Cold start (human has an idea)

```
Human opens agent tool with Halo skills installed
        │
        ▼
Agent reads Halo AGENTS.md (World A) or product AGENTS.md (World B)
        │
        ▼
Resolve TARGET ──► bootstrap if no .halo/state.json
        │
        ▼
INTAKE (L4 heavy) — model proposes defaults, human confirms
        │  writes intake.* into state (L1)
        ▼
SPEC PACK (L2+L4) — deterministic writer + model fill
        │  .halo/spec/* giant delivery
        ▼
HUMAN LOCK (L5) — only human can declare "this is the product"
        │
        ▼
READINESS (L2) — foresight inventory, CLI/env presence
        │  GO | DEGRADED | NO_GO
        ▼
SCAFFOLD (L2) — skeleton + milestones + Demo0 probe
        │
        ▼
BUILD LOOP (L4+L2) — one story/cycle until complete
```

### 5.2 Session death (the real multi-hour problem)

Agents do not have continuous consciousness. Halo assumes:

1. Session ends mid-work.  
2. New session has **zero** chat memory.  
3. Recovery = read **only** L1 artifacts.

**Minimum recovery kit for any session:**

```
1. .halo/state.json     → phase, status, readiness_verdict
2. .halo/baton.md       → next verb in plain language
3. .halo/spec/ (if locked)
4. git log -5 + git status
5. Last evidence / escalation if any
```

If baton and state disagree, **state.phase wins for gates**; baton is rewritten to match after diagnosis.

### 5.3 One build cycle (micro-loop)

Inside `phase: build`:

```
prime → pick story → plan file → RED test → impl → GREEN
  → simplify → verify (fail closed) → deploy preview
  → probe → (only if PASS) notify human
  → evidence + baton + optional score
```

This is where grok-halo DNA lives. The outer Halo lifecycle is the **macro-loop**; build is the **micro-loop**.

---

## 6. Self-build / self-modify — three recursion levels

Without naming levels, “Halo improves itself” becomes uncontrolled.

### Level 0 — Operate (default)

Agent uses Halo skills to build **World B** products.  
**Does not** change World A skills/scripts.

### Level 1 — Extend product harness

Agent writes product-local rules: `AGENTS.md` sections, `.halo/plans`, milestone logs, failure patterns in product STATE.  
Still not changing Halo system.

### Level 2 — Evolve Halo system (meta)

Agent (or human) changes World A: new skills, readiness catalog entries, scaffold profiles, WORKFLOWS.md.

**Level 2 requires different rules:**

| Rule | Why |
|------|-----|
| Explicit intent | “Improve Halo” ≠ “build my SaaS” |
| Branch + probe | Meta bugs break all future products |
| WORKFLOWS checklist | New path must appear in WORKFLOWS.md or it is incomplete |
| Compatibility | Products mid-flight on old phases must not brick |
| Dogfood last | Only after Level 0 works on a throwaway product |

### Forbidden recursion

- Halo build loop silently rewriting its own readiness thresholds to force GO  
- Scaffold “fixing” probe by writing a local file that always 200s without running a server (cheating evidence)  
- Skills that say “if stuck, delete denylist”  
- Infinite self-prompt without story completion criterion  

**Evidence cheating is the central risk of self-modifying agent systems.** L2 must make cheating hard: probe is real HTTP; tests must fail before pass; state transitions are scripted.

---

## 7. Authority boundaries (who may change what)

| Object | Human | Agent (product) | Agent (meta) |
|--------|-------|-----------------|--------------|
| Product idea / lock specs | Yes | Propose only | No |
| Secrets / .env values | Yes | Never commit / never log | Same |
| Prod promote | Yes | No | No |
| phase/status transitions | CLI ok | Via scripts only | Via scripts only |
| App code (World B) | Yes | Yes after lock | N/A |
| Skills (World A) | Yes | No by default | Only on meta task |
| Denylist paths | Override explicit | Never | Never |
| Evidence files | Audit | Write truthfully | Same |

**Human is not out of the loop.** Human is at **asymmetric** points: intent, lock, secrets, prod, escalation. Between those points, the agent is the operator.

---

## 8. Completeness model — how we avoid missing things

### 8.1 Three inventories that must stay in sync

| Inventory | Location | Incomplete if… |
|-----------|----------|----------------|
| **Workflows** | `docs/WORKFLOWS.md` | A journey exists in product use but not listed |
| **Skills** | `.grok/skills/*` | A workflow step has no skill or CLI verb |
| **Determinism** | `python/*`, `scripts/halo` | A safety gate is “model please remember” only |

**PR / change rule for Halo system:**

Any PR that adds a human journey or phase transition must update **all three** or be rejected.

### 8.2 Definition of “done” is multi-level

| Level | Done means |
|-------|------------|
| Story | AC green + evidence + optional probed demo |
| Milestone | All stories + milestone-log with user-facing “what’s new” |
| Product v1 | All milestones + readiness still GO for required integrations |
| Halo slice | WORKFLOWS + skills + python + smoke + docs version |

### 8.3 Blind-spot hunting (ongoing)

On every major change, run this review (human or agent):

1. **New state?** → Can a cold session recover?  
2. **New failure?** → pause / block / escalate path?  
3. **New external?** → readiness catalog entry?  
4. **New deploy?** → probe before share?  
5. **New skill?** → CLI verb? WORKFLOWS row?  
6. **Cheating?** → Can model mark APPROVED without L2 certs?  

### 8.4 Forecasted miss list (watch these)

These are the places systems like Halo historically fail:

1. **Mid-intake abandon** — partial `intake.*`, no baton; next session restarts grill from zero.  
2. **Spec lock without readiness** — code starts, secrets explode later.  
3. **Scaffold without probe** — human gets 404.  
4. **Build without story pointer** — agent freestyles features not in STORIES.  
5. **Unlock without re-readiness** — new integration never inventoried.  
6. **Existing repo destroy** — scaffold overwrites; must stay non-destructive.  
7. **Meta/product cwd confusion** — Halo repo mutated as product.  
8. **Runner without lock** — two agents, corrupted state.  
9. **Evidence theater** — empty files named GREEN_TEST.  
10. **Complete without human prod intent** — status COMPLETE while never usable.  

Each should have an explicit guard (script or skill hard rule). If a guard is missing, track it as open risk.

---

## 9. Failure taxonomy

| Class | Example | System response |
|-------|---------|-----------------|
| **Intent failure** | Wrong product | Unlock specs; human revises |
| **Environment failure** | Missing API key | BLOCKED + readiness list |
| **Implementation failure** | Bug / red tests | Inner fix ≤3 → escalate |
| **Verification failure** | AC untested | NEEDS_REVISION |
| **Deploy failure** | Probe fail | No notify; stay/fix |
| **Process failure** | Phase skip | Doctor / refuse transition |
| **Integrity failure** | Evidence cheat | Reject; escalate |
| **Meta failure** | Skill bug breaks all products | Pin version; hotfix World A |

Do not collapse all failures into “try again.” Different classes need different exits.

---

## 10. What exists today vs what is still soft

### Hardened (L2 real)

- State init / lock / set  
- Spec write from intake  
- Readiness catalog + verdicts  
- Scaffold profiles (nextjs / fastapi / existing)  
- Milestone prompts  
- Live HTTP probe  
- CLI surface for major verbs  
- Workflow map document  
- **Phase transition graph** (`halo_phases.py` + state set gate)  
- **Evidence cert validator** (`halo_evidence.py`)  
- **`halo doctor --strict`** consistency matrix  
- **`halo-go` autonomous mode**  
- `halo_system_version` on init  

### Soft (L3 skill / agent discipline)

- Full intake interview quality  
- Spec *content* quality (architecture depth)  
- Build cycle (TDD/Arena) — skill contract, not automated runner  
- Dual verifier Arena  
- Budget / golden trajectory port  
- Background walk-away loop with lock file  

### Missing / thin (known)

- Story backlog machine object (still mostly STORIES.md)  
- Concurrent agent lock  
- Full multi-cycle runner daemon  
- Design-system full port

---

## 11. How Halo should evolve (operating doctrine)

### For product work (Level 0)

1. Never freestyle past phase.  
2. Prefer `scripts/halo` over ad-hoc shell for control plane.  
3. After every session: baton accurate enough for a stranger agent.  
4. Never announce deploys without probe.  

### For Halo system work (Level 2)

1. Change one workflow at a time.  
2. Update WORKFLOWS + skill + CLI + smoke in the same change.  
3. Smoke on throwaway product before claiming done.  
4. Prefer adding L2 gates over longer skill prose.  
5. Document new failure class in §9 if novel.  

### For “don’t miss anything”

Maintain a living **Capability Matrix** (rows = workflows H* and A*, columns = skill / CLI / L2 / smoke).  
`halo doctor --strict` should eventually fail CI if a row is incomplete.

Until that exists, **manual matrix review is required on every slice.**

---

## 12. Mental model one-liner

> **Halo is a filesystem-backed state machine whose transitions are mostly executed by an LLM, but whose safety gates are deterministic programs — building products in one world while occasionally rewriting its own instructions in another.**

If you remember only that, you will not confuse chat vibes with shipped systems, or product apps with the factory.

---

## 13. Next architectural priorities (ordered by risk reduction)

1. **Phase transition enforcer** — `halo_state` only allows legal edges; illegal = exit 2.  
2. **Evidence validator** — cert schema + content checks; verify fail-closed.  
3. **`halo doctor --strict`** — WORKFLOWS/skills/CLI consistency.  
4. **Build runner** — port grok-halo micro-loop with single-runner lock.  
5. **Story object in state.json** — stop relying only on markdown parse.  
6. **Version field** — product records `halo_system_version` at bootstrap.  

These are not features for users. They are **load-bearing beams** for a self-modifying AI system.

---

**Document version:** 1.0 · 2026-07-09  
**Status:** Normative for intent; implementers must close §10 gaps deliberately.
