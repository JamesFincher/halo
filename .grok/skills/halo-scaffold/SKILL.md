---
name: halo-scaffold
description: Create product skeleton from locked STACK.md + readiness GO. Design-system hooks optional. Demo 0 deploy only after live probe PASS. Slice 2 — implement profiles incrementally.
---

# Halo Scaffold

**When**: `readiness_verdict` is `GO` or `DEGRADED`. Specs locked.  
**Not when**: `NO_GO`.

## Goal

Turn docs into a **runnable skeleton** + Demo 0 URL that **probes live** before human sees it.

## Preconditions

```bash
python3 "$HALO_SYS/python/halo_readiness.py" --repo . --json | jq -r .verdict
# GO | DEGRADED only
jq -r .spec_status .halo/state.json  # locked
```

## Steps

### 1. Read stack

`.halo/spec/STACK.md` + `intake.stack` in state.

### 2. Profile dispatch

| Profile signals | Action |
|-----------------|--------|
| next / nextjs / web-saas | `references/nextjs-saas.md` (create app, app router, tailwind) |
| fastapi / api-ui | `references/fastapi.md` |
| existing package.json | Do not overwrite; add missing scripts only |

If unknown → ask human once with 2–3 options (defaults proposed).

### 3. Wire Halo surface into product

Ensure present:

- `AGENTS.md`, `HALO.md` (from templates)
- `.halo/` already from bootstrap
- `.gitignore` includes `.env`, `node_modules`, `.next`, etc.
- Scripts: `dev`, `build`, `test` (or python equivalents)

### 4. Milestone materialization

From `.halo/spec/MILESTONES.md` + `STORIES.md` write:

```
.halo/milestones/1-{slug}/prompt.md
.halo/milestones/2-{slug}/prompt.md
...
```

Prompt template: read PRD + prior milestone-log; build only this milestone; done-when; write milestone-log.

Sync stories into `.halo/state.json` backlog when state tool supports it (or STORIES.md as source until runner exists).

### 5. Demo 0

1. Local `dev` or first preview deploy per STACK hosting
2. Capture URL
3. **Must** run:

```bash
python3 "$HALO_SYS/python/halo_probe.py" --url "$URL" --json
```

4. Exit 0 only → write `.halo/evidence/deploy-ok-demo0.json` + tell human  
5. Exit ≠ 0 → fix; **never** say “we deployed” with dead link

### 6. Exit state

```bash
# phase build, baton points to first milestone prompt
```

## Forbidden

- Full feature build in scaffold (that's build loop)
- Share URL without probe PASS
- Ignore design direction if design-system profile selected (port bm-design-system later)

## Status

Scaffold **profiles** land in slice 2. This skill is the contract; agent follows steps with best-effort stack CLI today, then hardens references.
