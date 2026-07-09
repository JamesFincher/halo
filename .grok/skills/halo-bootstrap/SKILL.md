---
name: halo-bootstrap
description: Self-instantiate Halo into a target product project. Creates .halo/ state, product AGENTS.md, HALO.md, baton. Run first when starting a new product with Halo.
---

# Halo Bootstrap

**When**: Empty project, or project without `.halo/state.json`.  
**Not when**: Already inside the Halo system repo as the product (bootstrap *out* to a target path).

## Goal

Make the target project Halo-ready so the next step is always **intake**, never freestyle coding.

## Steps

### 1. Resolve TARGET

- If user gave a path → use it.
- If cwd is Halo system repo (`halo-bootstrap` skill present at `.grok/skills/halo-bootstrap`) **and** no product intent on this repo → ask for product directory.
- If cwd is empty/other project → TARGET = cwd.

Refuse to bootstrap *into* the Halo system repo itself unless user explicitly says “dogfood Halo on itself.”

### 2. Detect existing work

```bash
ls -la "$TARGET"
test -f "$TARGET/.halo/state.json" && echo ALREADY
```

If `ALREADY` → read state phase; tell user; offer resume skill for that phase. Do not wipe without confirm.

### 3. Create skeleton

Create:

```
$TARGET/.halo/
  state.json
  baton.md
  evidence/
  plans/
  spec/
  milestones/
  scores/
  trajectories/
$TARGET/AGENTS.md          # product rules (from template)
$TARGET/HALO.md            # loop config stub
$TARGET/.env.example       # empty placeholders filled at readiness
```

Copy skill references or symlink instruction: product `AGENTS.md` must point agents to continue Halo protocol (short form from templates).

Use:

```bash
python3 <HALO_SYSTEM>/python/halo_state.py init --repo "$TARGET" --phase bootstrap
```

If python tool missing, write state.json by hand using schema in this skill.

### 4. state.json schema (min)

```json
{
  "version": 1,
  "status": "ACTIVE",
  "phase": "intake",
  "spec_status": "none",
  "product_name": null,
  "require_human_gate": false,
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "intake": {},
  "integrations": [],
  "current_milestone": null,
  "current_story": null,
  "last_cycle_commit": null,
  "last_cycle_status": null,
  "warm_start_directives": []
}
```

After bootstrap files written, set `phase` to `intake`.

### 5. baton.md

```markdown
# Baton
- Phase: intake
- Next: run skill halo-intake
- Do not: write product feature code yet
```

### 6. Exit

Tell human:

1. Halo instantiated at TARGET
2. Next: intake grill (skill `halo-intake`)
3. They may dump the idea now in free text

Immediately continue to **halo-intake** unless user stops.

## Product AGENTS.md essentials

Include:

- Phase machine pointer
- No feature code before `spec_status: locked`
- Read `.halo/baton.md` every session
- Live probe rule for deploys
- Link relative paths to `.halo/spec/`

## Forbidden

- Scaffolding app frameworks in this skill
- Collecting API keys here (that’s readiness)
- Marking specs locked
