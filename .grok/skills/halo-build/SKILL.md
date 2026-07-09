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

## Test ratchet (non-negotiable)

- **Never delete, skip, or gut tests** to make the suite green.
- If a test is wrong, fix the test to match locked AC — do not remove coverage.
- Run `halo ratchet` (or `python3 $HALO_SYS/python/halo_ratchet.py`) if suspect.
- Mark feature `passes: true` only after GREEN suite + evidence file:
  ```bash
  # write .halo/evidence/Sxxx-green.json with exit_code:0 first
  python3 $HALO_SYS/python/halo_features.py pass --repo . --id Sxxx \
    --evidence .halo/evidence/Sxxx-green.json --note "…"
  ```
  Hand-editing `passes: true` without `verified_at`/`evidence` is rejected by Stop completion.

## After each unit

```bash
python3 $HALO_SYS/python/halo_arena.py --repo . verify --id Sxxx   # dual-lens; need APPROVED
python3 $HALO_SYS/python/halo_progress.py add --repo . --event story_done --note "Sxxx …"
python3 $HALO_SYS/python/halo_next_prompt.py --repo . --write
# safe commit (skips gitignored dogfood .halo/ automatically):
python3 $HALO_SYS/python/halo_commit.py --repo . --id Sxxx --message "…"
# or: halo commit-unit . --id Sxxx --message "…"
```

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
