# Halo Lifecycle

## Human journey

1. Idea — one sentence ok.
2. Grill — Halo proposes defaults; depth optional.
3. Giant delivery — `.halo/spec/*`.
4. Iterate — chat fixes until lock.
5. Lock — "lock specs" or "go".
6. Supply keys once — readiness list.
7. Walk away — live links arrive; peek when free.
8. Promote — human decides production.

## Agent journey

| Phase | Must do | Must not |
|-------|---------|----------|
| Bootstrap | Create `.halo/`, state, product AGENTS | Code features |
| Intake | One question at a time, defaults | Skip to code |
| Spec pack | Write complete docs | Partial PRD |
| Spec review | Edit docs on feedback | Start scaffold |
| Readiness | Full lifecycle integrations | Defer "we'll add later" |
| Scaffold | Skeleton + smoke | Fake deploy URL |
| Build | TDD, verify, probe then share | Share 404 |

## Milestone unit

- Visible user-facing value.
- Done-when verifiable in browser/API.
- Own `prompt.md` + later `milestone-log.md`.
- Maps to stories in `STORIES.md`.

## Demo contract

Message to human only if:

```
DEPLOY_OK cert exists AND
halo_probe.py exit 0 AND
smoke path from done-when is green
```

Else keep iterating or escalate.
