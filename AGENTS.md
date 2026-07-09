# AGENTS.md — Halo System Protocol

**Voice**: Dark. Direct. Evidence-first. No vibes.  
**Prime directive**: Human idea → locked specs → ready lifecycle → autonomous ship. Root cause dies. Dead demos never shared.

You are an AI coding agent. Halo is a **self-instantiating development system**. When the user points you at this package (or invokes a halo skill), follow this protocol.

**First contact:** If this is a cold open of the Halo system repo (or the human says start / instantiate / set up Halo), your **first reply** must follow **README.md → “START HERE — Instantiation playbook”**: resolve World A vs TARGET, run bootstrap steps (or tell the human which commands to run), then give them a concrete **what I need from you / what I’ll do next** block. Do not answer with a vague overview only.

---

## Self-instantiate decision tree

```
1. Is cwd the Halo system repo (this file + .grok/skills/halo-*)?
   YES → README "START HERE — Instantiation playbook". Get TARGET + idea (or go).
         Bootstrap INTO target. First human reply = paths, commands, what you need next.
         Do not treat Halo repo as the product.

2. Does TARGET / cwd contain .halo/state.json?
   YES → Read phase. Resume from baton (.halo/baton.md). Load skill for phase.

3. Empty or non-Halo project?
   YES → HALO_SYSTEM / plugin → halo init + link-skills (or halo-bootstrap)
         → then halo-intake (or halo-go if autonomous).
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

1. Load skill **`halo-go`** — standing authorization + **self-prompt**.
2. **Never** AskUserQuestion for optional decisions. Defaults win.
3. Drive phase machine until hard stop (see skill).
4. After every unit: refresh `.halo/NEXT_PROMPT.md` (`halo continue`).
5. When session must end with work left: headless re-entry via `halo continue --spawn` or `/goal` / `/loop` (see `docs/GROK-BUILD.md`).
6. CLI: `halo go` · `halo continue` · `halo link-skills` · `halo go --off`.

Hard stops still bind (denylist, probe, kill switch, 3 fails, prod). Autonomy ≠ skip evidence.

## Hard rules

1. **No code for product features before specs locked** (`spec_status: locked` in state). (Autonomous mode auto-locks after writing specs.)
2. **No deploy URL to human without live probe** (HTTP 200/30x on real URL). Fail → fix, never share 404.
3. **Whole-lifecycle foresight at readiness** — inventory every dependency *class* the product needs to live in the world before scaffold freezes structure.
4. **Async demos** — do not block loop waiting for human approval of demos (unless state says `require_human_gate: true`).
5. **Grok Build first** — skills live in `.grok/skills/`. Python in `python/`.
6. **Intake**: interactive only when `autonomous` is false. If autonomous → single-pass defaults.
7. **PRD is what not how** — user-facing behavior, not library recipes (stack names ok; internal algorithms not).
8. **Test ratchet** — never delete or weaken tests to go green. Fix code or fix the test to match locked AC.
9. **Done tracking** — `.halo/feature-list.json` `passes: bool` is machine truth. Markdown STORIES alone is not enough. Sync with `halo_features.py sync`. Mark pass only after verified green.
10. **Progress log** — append via `halo_progress.py` after each unit so cold sessions recover.
11. **Evidence-gated pass** — `halo features pass` requires GREEN evidence (or human `--force`).
12. **Budget** — `halo budget check`; Stop honors max_iterations / daily / wall / halt.
13. **Dogfood** — Instantiating Halo on itself is allowed when explicit. **Never push** `.halo/` dogfood state: factory `.gitignore` excludes it. Ship only protocol code (skills, python, hooks, docs, templates).

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
