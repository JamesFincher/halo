---
name: halo-spec-pack
description: Write the giant Halo delivery — PRD, architecture, design, data model, stack, stories, integrations, readiness checklist, milestones — from locked intake. Human reviews then locks.
---

# Halo Spec Pack

**When**: Intake locked (`phase` is `spec_pack` or `spec_review`).  
**Input**: `.halo/state.json` → `intake`.  
**Output**: `.halo/spec/*.md` + state `spec_status: ready_for_review`.

## Principles

- Write files. Do not ask permission for draft structure — intake already locked content.
- Voice: sharp product/engineering hybrid. Concrete. Opinionated.
- **What not how** in PRD/stories; architecture may name patterns and boundaries.
- Every integration from intake appears in INTEGRATIONS.md + READINESS.md credential table.
- Stories binary-testable (no weasel words).

## Files to write (all)

| File | Purpose |
|------|---------|
| `.halo/spec/PRD.md` | Product requirements (user-facing) |
| `.halo/spec/ARCHITECTURE.md` | System boundaries, services, deploy topology |
| `.halo/spec/DESIGN.md` | UX direction, screens list, design-system intent |
| `.halo/spec/DATA-MODEL.md` | Entities + relationships (conceptual + suggested tables) |
| `.halo/spec/STACK.md` | Locked stack + why + repo layout target |
| `.halo/spec/STORIES.md` | User stories with AC checkboxes, priority, milestone map |
| `.halo/spec/INTEGRATIONS.md` | Providers, env var names, which milestone needs them |
| `.halo/spec/READINESS.md` | Pre-scaffold checklist (keys, CLIs, accounts) |
| `.halo/spec/MILESTONES.md` | Milestone scopes + done-when + story IDs |

Optional templates under `templates/` in Halo system repo — copy structure, fill from intake.

## PRD structure

```markdown
# {product_name}

## What we're building
## Who it's for
## In scope
## Out of scope
## Success metric
## Features (detail)
## Data the app remembers (summary)
## Integrations (summary)
## Milestones (summary)
## Open questions
```

## Stories format

```markdown
### S001 — {title}
- **Priority**: high|medium|low
- **Milestone**: M1
- **Status**: pending
- **Acceptance criteria**:
  - [ ] observable binary criterion
  - [ ] ...
```

## After write

1. `spec_status: ready_for_review`, `phase: spec_review`
2. Update baton: human should read `.halo/spec/` and say what to change or **lock specs**
3. Print short index of files + how to open them

## On human “lock specs” / “go”

```bash
python3 python/halo_state.py set --repo "$TARGET" --phase readiness --spec-status locked
```

Then run **halo-readiness** (when available). Until then: tell human readiness skill is next slice; dump READINESS.md checklist for manual fill.

## Forbidden

- Locking without human signal
- Scaffolding code
- Putting secrets in files
