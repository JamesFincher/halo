# Milestone {N} — {NAME}

You are planning and building **only** milestone {N} of this product (Halo build phase).

## Context

- Read `.halo/spec/PRD.md` for product scope.
- Read `.halo/spec/MILESTONES.md` and `.halo/spec/STORIES.md` for this milestone's stories.
- Read prior logs: `.halo/milestones/*/milestone-log.md` (if any).
- Read `.halo/baton.md` and `.halo/state.json`.

## Scope

{SCOPE}

## Done when

{DONE_WHEN}

## Rules

1. Do **not** implement later milestones.
2. TDD: failing test before feature code when tests exist.
3. After work: full test suite green.
4. Deploy preview only; run live probe before any human-facing URL.
5. When complete, write `milestone-log.md` in this folder:

```markdown
## What's new in the app
- (user-facing bullets)

## Built
- files, routes, models

## Decisions
- …

## For next milestone
- …

## Deviations from PRD
- …
```

6. Update baton to next pending story/milestone.
