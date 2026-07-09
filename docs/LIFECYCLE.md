# Halo Lifecycle — Human & Agent View

## Human journey

1. **Idea** — free-form dump (one sentence ok).
2. **Grill** — Halo proposes defaults; you confirm/change. Depth optional.
3. **Giant delivery** — open `.halo/spec/*` (PRD, arch, design, data, stack, stories, integrations, readiness, milestones).
4. **Iterate** — chat fixes until happy.
5. **Lock** — “lock specs” / “go”.
6. **Supply keys once** — readiness list (Clerk, Vercel, Sentry, OpenAI, …) for whole v1.
7. **Walk away** — demos arrive as live links; peek when free.
8. **Promote** — you decide production; Halo stays on preview/dev.

## Agent journey

| Phase | Must do | Must not |
|-------|---------|----------|
| Bootstrap | Create `.halo/`, state, product AGENTS | Code features |
| Intake | One question at a time, defaults | Skip to code |
| Spec pack | Write complete docs | Partial PRD |
| Spec review | Edit docs on feedback | Start scaffold |
| Readiness | Full lifecycle integrations | Defer “we’ll add Sentry later” |
| Scaffold | Skeleton + smoke | Fake deploy URL |
| Build | TDD, verify, **probe** then share | Share 404 |

## Milestone unit

Each milestone:

- Visible user-facing value
- Done-when verifiable in browser/API
- Own `prompt.md` + later `milestone-log.md`
- Maps to stories in STORIES.md

## Demo contract

Message to human only if:

```
DEPLOY_OK cert exists AND
halo_probe.py exit 0 AND
smoke path from Done-when green
```

Else: keep iterating silently (or escalate if blocked).
