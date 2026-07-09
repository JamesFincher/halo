# AGENTS.md — Product (Halo-managed)

This project is developed by **Halo**. Read `.halo/baton.md` and `.halo/state.json` before acting.

## Phase rules

| `phase` | Do |
|---------|-----|
| `intake` / `spec_pack` / `spec_review` | Docs only. No product feature code. |
| `readiness` | Keys, CLIs, `.env.example` — no app scaffold until GO |
| `scaffold` | Skeleton + Demo 0 with live probe |
| `build` | One story per cycle; TDD; verify; deploy; **probe before share** |

## Spec source of truth

`.halo/spec/` after lock. Do not contradict locked PRD/stories without human unlock.

## Hard rules

1. No feature code before `spec_status: locked`
2. Never announce deploy URL without `python -m` / `python3` probe PASS
3. No secrets in git
4. Preview/dev deploys only unless human promotes

## Continue

If unsure: run matching halo skill (`halo-intake`, `halo-spec-pack`, …) from the Halo system install.
