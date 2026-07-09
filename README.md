# Halo

**Autonomous product development system for Grok Build.**

Human has an idea → points AI at Halo → Halo grills, plans, scaffolds, builds, deploys, iterates.  
Minimal human after intake. Working demos every ship. Dead links never shared.

```
idea → INTAKE → SPEC PACK → human iterate until happy
     → READINESS (keys, CLIs, deploy, whole-lifecycle foresight)
     → SCAFFOLD → MILESTONES → BUILD LOOP → live demo URLs
```

**Every path documented:** [docs/WORKFLOWS.md](docs/WORKFLOWS.md) — no blind spots.  
**CLI:** `./scripts/halo help`

Steal DNA: [grok-halo](https://github.com/JamesFincher/grok-halo) + [bm-skills-grok-build](https://github.com/JamesFincher/bm-skills-grok-build).

---

## For humans

### Install (Grok Build)

```bash
# From local path while developing:
grok plugin install /Users/james/code/halo --trust

# Or add as marketplace once published
# grok plugin marketplace add JamesFincher/halo
# grok plugin install halo --trust
```

### Start a product

1. Open empty (or existing) project folder in Grok Build / Hermes.
2. Tell the agent: **run halo-bootstrap** (or paste `AGENTS.md` instructions).
3. Answer the intake grill — go as deep as you want; defaults exist for speed.
4. Receive **one giant delivery**: PRD, architecture, design, data model, stack, stories, readiness checklist.
5. Iterate on docs until happy → say **go** / **lock specs**.
6. Halo readiness-gates secrets & tools for the **whole** lifecycle (e.g. Sentry now, not later).
7. Scaffold → autonomous build loop → demo URLs that already probe live (HTTP must work before share).

### CLI (`scripts/halo`)

```bash
./scripts/halo help
./scripts/halo init ~/code/my-app
./scripts/halo specs ~/code/my-app    # after intake in state
./scripts/halo lock ~/code/my-app
./scripts/halo ready ~/code/my-app    # or --allow-degraded
./scripts/halo scaffold ~/code/my-app --profile fastapi --demo0 local
./scripts/halo status ~/code/my-app
./scripts/halo stop|resume|escalate|handoff|triage|doctor
./scripts/halo go ~/code/my-app          # AUTONOMOUS — build without asking
./scripts/halo go --off ~/code/my-app    # back to interactive
```

**Autonomous:** skill `halo-go` + `halo go`. Defaults only; hard stops still bind.

### Skills (all workflows)

| Skill | When |
|-------|------|
| `halo-bootstrap` | Instantiate into product |
| `halo-intake` | Grill |
| `halo-spec-pack` | Giant docs |
| `halo-readiness` | Foresight gate |
| `halo-scaffold` | Skeleton + milestones + Demo 0 |
| `halo-build` / `halo-verify` / `halo-deploy` | Build cycle |
| `halo-status` / `halo-triage` / `halo-doctor` | Observe |
| `halo-pause` / `halo-escalate` / `halo-handoff` / `halo-revise` | Control |

---

## For AI agents (read this first)

You are looking at the **Halo system repo**, not a product app.

1. Read `AGENTS.md` (authoritative protocol).
2. If cwd is this repo and user wants a product → ask target project path, then bootstrap **into that path**.
3. If cwd is already a product project with `.halo/` → continue from baton / phase in `.halo/state.json`.
4. If cwd is empty product project → run **halo-bootstrap**, then **halo-intake**.

Do not invent a half-PRD and start coding. Spec pack locks first.

---

## Status (v0.3)

| Slice | Status |
|-------|--------|
| Bootstrap + Intake + Spec pack | **done** |
| Readiness foresight gate | **done** |
| Full workflow map (no blind spots) | **done** — WORKFLOWS.md + CLI |
| Scaffold nextjs/fastapi/existing + Demo 0 probe | **done** |
| Build cycle skill | **contract** (agent-run) |
| Multi-cycle walk-away runner | planned |

Architecture: `docs/ARCHITECTURE.md` · **Deep:** `docs/ARCHITECTURE-DEEP.md` · Lifecycle: `docs/LIFECYCLE.md` · Workflows: `docs/WORKFLOWS.md`

---

## Principles

1. **Foresight** — ask for Sentry/Clerk/Vercel/etc. before first scaffold, not mid-flight.
2. **Evidence** — typed certs; no prose “it works.”
3. **Live probe** — never hand human a deploy URL that 404s.
4. **Async demos** — loop does not wait for human after lock; human peeks when free.
5. **One story / one milestone unit per cycle** — no one-shot apps.
6. **Self-instantiate** — skills + state files teach the next session what to do.
7. **Python for glue** — scripts deterministic; model for judgment.

---

## License

MIT (unless you change it).
