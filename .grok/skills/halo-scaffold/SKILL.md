---
name: halo-scaffold
description: Scaffold product skeleton (nextjs-saas|fastapi|existing), generate milestone prompts, Demo 0 with live probe. Never share URL on probe fail.
---

# Halo Scaffold

## Preconditions

- `.halo/state.json` exists
- `spec_status: locked` preferred
- `readiness_verdict` is `GO` or `DEGRADED` (or pass `--skip-ready-check` only for dry runs)

## Command (preferred)

```bash
HALO_SYS="${HALO_SYSTEM:-/Users/james/code/halo}"
"$HALO_SYS/scripts/halo" scaffold . --profile auto --demo0 local
```

Profiles: `auto` | `nextjs-saas` | `fastapi` | `existing`  
Demo0: `local` (default) | `skip` | `vercel` (not yet)

## What it does

1. Detect/write stack skeleton (offline templates — no network required for files)
2. `npm install` / `pip install` if needed
3. Write `.halo/milestones/*/prompt.md` + `index.json`
4. Start local server → **halo_probe** → write evidence only on PASS
5. phase → `build`, baton → first milestone

## On Demo0 fail

- Do **not** tell human the app is live
- phase stays `scaffold`
- Fix and re-run

## References

- `references/nextjs-saas.md`
- `references/fastapi.md`
