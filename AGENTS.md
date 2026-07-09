# AGENTS.md — Halo System Protocol

**Voice**: Dark. Direct. Evidence-first. No vibes.  
**Prime directive**: Human idea → locked specs → ready lifecycle → autonomous ship. Root cause dies. Dead demos never shared.

You are an AI coding agent. Halo is a **self-instantiating development system**. When the user points you at this package (or invokes a halo skill), follow this protocol.

---

## Self-instantiate decision tree

```
1. Is cwd the Halo system repo (this file + .grok/skills/halo-*)?
   YES → User wants a product: ask TARGET_DIR (or use sibling empty folder).
         Bootstrap INTO target. Do not treat Halo repo as the product.

2. Does TARGET / cwd contain .halo/state.json?
   YES → Read phase. Resume from baton (.halo/baton.md). Load skill for phase.

3. Empty or non-Halo project?
   YES → Run skill: halo-bootstrap → then halo-intake → halo-spec-pack.
```

---

## Phases (v0 scope bold)

| Phase | Skill | Human | Output |
|-------|-------|-------|--------|
| **0 Bootstrap** | `halo-bootstrap` | low | `.halo/`, project AGENTS.md, state |
| **1 Intake** | `halo-intake` | **high** | locked decisions (interview) |
| **2 Spec pack** | `halo-spec-pack` / `halo_spec_write.py` | review | full docs under `.halo/spec/` |
| 2b Spec iterate | chat + rewrite | until happy | revised pack |
| **3 Readiness** | `halo-readiness` / `halo_readiness.py` | secrets once | `.halo/readiness.json` GO/NO_GO/DEGRADED |
| 4 Scaffold | `halo-scaffold` | none | app skeleton + Demo 0 |
| 5 Milestones | derived from specs | none | `.halo/milestones/` + stories |
| 6 Build loop | `halo-build` | async demos | code + **live** preview URLs |
| 7 Complete | — | promote prod | all stories deployed |

**Implementable now**: 0–6 (build cycle agent-driven). Runner automation later.  
**Workflow map (no blind spots):** `docs/WORKFLOWS.md`  
**CLI:** `scripts/halo help`

---

## Autonomous mode (`halo-go`)

If human says **go** / **just build** / **don't ask** / **walk away**, OR `state.autonomous === true`:

1. Load skill **`halo-go`** — standing authorization.
2. **Never** AskUserQuestion for optional decisions. Defaults win.
3. Drive phase machine until hard stop (see skill).
4. CLI: `halo go [path]` enable · `halo go --off` disable · `halo go --plan` next actions.

Hard stops still bind (denylist, probe, kill switch, 3 fails, prod). Autonomy ≠ skip evidence.

## Hard rules

1. **No code for product features before specs locked** (`spec_status: locked` in state). (Autonomous mode auto-locks after writing specs.)
2. **No deploy URL to human without live probe** (HTTP 200/30x on real URL). Fail → fix, never share 404.
3. **Whole-lifecycle foresight at readiness** — every integration for v1 asked once (API keys, CLI auth, deploy targets).
4. **Async demos** — do not block loop waiting for human approval of demos (unless state says `require_human_gate: true`).
5. **Grok Build first** — skills live in `.grok/skills/`. Python in `python/`.
6. **Intake**: interactive only when `autonomous` is false. If autonomous → single-pass defaults.
7. **PRD is what not how** — user-facing behavior, not library recipes (stack names ok; internal algorithms not).

---

## Artifact map (in target product project)

```
.halo/
  state.json           # machine source of truth
  baton.md             # next session handoff
  evidence/            # certs (later)
  plans/               # per-cycle plans (later)
  spec/                # giant delivery
    PRD.md
    ARCHITECTURE.md
    DESIGN.md
    DATA-MODEL.md
    STACK.md
    STORIES.md
    INTEGRATIONS.md
    READINESS.md
    MILESTONES.md
  milestones/          # after lock: N-slug/prompt.md + logs
  readiness.json
AGENTS.md              # product project agent rules (generated)
HALO.md                # product loop config (generated)
```

---

## Skill load order (first product run)

1. Read `halo-bootstrap/SKILL.md` — create structure
2. Read `halo-intake/SKILL.md` + `steps/*` — grill
3. Read `halo-spec-pack/SKILL.md` — write files; tell human how to review
4. Wait for human: iterate specs or **lock**
5. On lock → readiness (when skill complete)

---

## CLI + Python

```bash
./scripts/halo help
./scripts/halo status
python3 python/halo_state.py --help
python3 python/halo_probe.py --url https://example.com
```

Prefer `scripts/halo` and python tools over ad-hoc shell for state mutations.

If stuck: read `docs/WORKFLOWS.md` — every journey is listed.

---

## Steal / port map

| From | What |
|------|------|
| bm-prd-creator | Intake phases, defaults, milestone prompts, what-not-how |
| bm-design-system | Scaffold design system later (React/Tailwind) |
| grok-halo | Budget, Arena verify, golden trajectory, runner, evidence certs v2 |

---

## Stop conditions

- User says stop / pause → write baton, set state `PAUSED`
- Missing secrets after readiness → `BLOCKED` with checklist only (no silent mock prod)
- Three failed build attempts on same story → escalate packet (later)

When unsure: re-read this file + `.halo/baton.md`. Do not freestyle lifecycle.
