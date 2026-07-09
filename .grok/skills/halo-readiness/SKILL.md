---
name: halo-readiness
description: Lifecycle foresight gate — verify accounts, API keys, CLIs, deploy tools exist before scaffold. Collect secrets inventory without committing secrets. STUB until slice 1 complete.
---

# Halo Readiness (stub)

**Status**: Spec exists; full automation in slice 1.

## Intent

Before any scaffold or build:

1. Read `.halo/spec/INTEGRATIONS.md` + `READINESS.md` + intake.integrations
2. Expand to **whole v1 lifecycle** (hosting, auth, DB, monitoring, email, payments, AI, analytics)
3. For each item, check:
   - Account signup needed?
   - Env var names
   - CLI install + auth (`vercel login`, `gh auth`, etc.)
4. Probe what can be probed without secrets (CLI present on PATH)
5. Write `.halo/readiness.json`:

```json
{
  "verdict": "GO|NO_GO|DEGRADED",
  "checked_at": "ISO8601",
  "items": [
    {
      "id": "vercel",
      "ok": false,
      "blocking": true,
      "human_action": "Install Vercel CLI and run vercel login; set project link",
      "env": ["VERCEL_TOKEN"]
    }
  ]
}
```

6. Human fills `.env` locally (gitignored). Never commit secrets.
7. On GO → `phase: scaffold`

## Live probe rule (forward reference)

Deploy share requires `python/halo_probe.py` success. Implemented early so scaffold Demo 0 obeys same law.

## Current agent behavior (stub)

If invoked now:

1. Generate/update `.halo/spec/READINESS.md` from integrations
2. Create `.env.example` with all keys empty
3. Check PATH for common CLIs (`node`, `npm`, `git`, `gh`, `vercel`, `python3`)
4. Set `phase: readiness`, `readiness_verdict` in state
5. List blocking human actions clearly
6. Do **not** pretend GO if keys missing for required integrations
