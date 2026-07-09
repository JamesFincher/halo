---
name: halo-intake
description: Structured grill from raw idea to locked product decisions. Proposes defaults. Depth adapts to user energy. Feeds halo-spec-pack. Ported from Builder Methods PRD creator, Halo-native.
---

# Halo Intake

**Audience**: Product-minded humans (may be non-technical). Explain jargon in one line when it appears.  
**Output**: Locked answers in `.halo/state.json` → `intake` object — **not** final markdown yet (spec-pack writes files).

## Principles (from BM + Halo)

1. **Propose default + reason → confirm.** Never blank “what do you want?”
2. **AskUserQuestion** for discrete options. Free-form for brain dump / names.
3. **One decision at a time.** Lock phase before next.
4. **Adapt depth** — simple idea → compress; complex → expand.
5. **What not how** — behavior, flows, scope, integrations, data remembered. Stack *names* ok; no algorithms.
6. **Tight prose.** Momentum over essays.
7. **Foresight seed** — every integration mentioned now feeds readiness later.

## Phases (execute in order)

Read each step file fully when entering that phase:

| # | Phase | File |
|---|-------|------|
| 1 | Brain dump | `steps/brain-dump.md` |
| 2 | Core purpose | `steps/core-purpose.md` |
| 3 | In-scope features | `steps/features.md` |
| 4 | Out of scope | `steps/out-of-scope.md` |
| 5 | Users & success | `steps/users.md` |
| 6 | Stack choice | `steps/stack.md` |
| 7 | Integrations (lifecycle) | `steps/integrations.md` |
| 8 | Data model | `steps/data-model.md` |
| 9 | Design direction | `steps/design.md` |
| 10 | Milestone strategy | `steps/milestones.md` |
| 11 | Lock intake | `steps/lock.md` |

Persist after each phase:

```bash
python3 python/halo_state.py set-intake --repo "$TARGET" --key <phase> --json '<blob>'
```

## Energy escape hatch

If fatigue: offer “use recommended defaults for remaining intake phases” → fill sensible defaults, summarize, confirm once, jump to lock.

## After lock

1. Set `phase: spec_pack`, `spec_status: drafting`
2. Run **halo-spec-pack** immediately
3. Do not start scaffold

## Forbidden

- Writing production code
- Skipping integrations “we’ll decide later” for known needs
- Technical library laundry lists beyond stack names
