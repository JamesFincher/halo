# Halo

**Autonomous product development system for Grok Build.**

Human has an idea → points AI at Halo → Halo grills, plans, scaffolds, builds, deploys, iterates.  
Minimal human after intake. Working demos every ship. Dead links never shared.

```
idea → INTAKE → SPEC PACK → human iterate until happy
     → READINESS (keys, CLIs, deploy, whole-lifecycle foresight)
     → SCAFFOLD → MILESTONES → BUILD LOOP → live demo URLs
```

Steal DNA: [grok-halo](https://github.com/JamesFincher/grok-halo) (loop, evidence, budget) + [bm-skills-grok-build](https://github.com/JamesFincher/bm-skills-grok-build) (intake grill, PRD, milestones). Halo is larger than either.

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

### Commands (later phases)

| Skill | When |
|-------|------|
| `halo-bootstrap` | First touch — instantiate Halo into target project |
| `halo-intake` | Grill: idea → locked product decisions |
| `halo-spec-pack` | Write full doc suite under `.halo/spec/` |
| `halo-readiness` | Lifecycle foresight + credential/tool gate |
| `halo-scaffold` | *(slice 2)* Create app skeleton + design system hooks |
| `halo-build` | *(slice 2)* Autonomous TDD → verify → deploy loop |

Python tooling (stdlib-first) lives in `python/`.

---

## For AI agents (read this first)

You are looking at the **Halo system repo**, not a product app.

1. Read `AGENTS.md` (authoritative protocol).
2. If cwd is this repo and user wants a product → ask target project path, then bootstrap **into that path**.
3. If cwd is already a product project with `.halo/` → continue from baton / phase in `.halo/state.json`.
4. If cwd is empty product project → run **halo-bootstrap**, then **halo-intake**.

Do not invent a half-PRD and start coding. Spec pack locks first.

---

## Status (v0)

| Slice | Status |
|-------|--------|
| Bootstrap + Intake + Spec pack | **in progress** |
| Readiness foresight gate | stubs |
| Scaffold + build loop + live deploy probe | planned (from grok-halo v2) |

Architecture: `docs/ARCHITECTURE.md` · Lifecycle: `docs/LIFECYCLE.md`

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
