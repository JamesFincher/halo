---
name: halo-build
description: One autonomous build cycle — pick story/milestone unit, TDD, verify, deploy preview, live probe before share, baton update. Port of grok-halo v2 discipline.
---

# Halo Build (cycle)

**When**: `phase: build`, status ACTIVE, readiness not NO_GO for required deploys.

## Cycle (one story)

1. **Prime** — baton, last critique, failure patterns, git status  
2. **Pick** — next pending story in `.halo/spec/STORIES.md` or milestone prompt  
3. **Plan** — write `.halo/plans/Sxxx-plan.md`  
4. **RED** — failing test cert  
5. **Impl** — min code  
6. **GREEN** — full suite  
7. **Simplify** — no behavior change  
8. **Verify** — self-check AC map; optional dual Arena later  
9. **Deploy** preview if configured  
10. **Probe** — `halo probe --url …` MUST pass before human message  
11. **Evidence** — write certs under `.halo/evidence/`  
12. **Baton** — next unit; warm-start note  

## Hard stops

- status PAUSED / BLOCKED / ESCALATED  
- denylist paths  
- 3 fails same story → `halo escalate`  
- probe fail → do not share URL  

## CLI helper

```bash
halo build   # prints next milestone prompt path
```

Full runner automation = slice 4. Until then agent executes this skill manually each cycle.
