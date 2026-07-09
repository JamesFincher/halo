---
name: halo-readiness
description: Lifecycle foresight gate — merge intake integrations with baseline (hosting, auth, DB, Sentry, …), probe CLIs/env names, write readiness.json. GO/NO_GO/DEGRADED before scaffold. Never logs secret values.
---

# Halo Readiness

**When**: Specs locked (`spec_status: locked`) or human says “check readiness” / after lock.  
**Tool**: `python/halo_readiness.py` (stdlib).  
**Law**: Foresight now — Sentry/Clerk/Vercel/DB asked before first scaffold, not mid-flight.

## Agent procedure

### 1. Preconditions

```bash
test -f .halo/state.json
# prefer locked specs; if drafting, still can inventory but do not GO to scaffold
```

If no state → run `halo-bootstrap` first.

### 2. Ensure intake.integrations populated

If empty but `.halo/spec/INTEGRATIONS.md` exists, parse known providers into state (or re-run intake integrations phase). Prefer structured `intake.integrations` in state.

### 3. Run checker (write artifacts)

From **Halo system** install path (or copy `python/` into path):

```bash
HALO_SYS="${HALO_SYSTEM:-/Users/james/code/halo}"
python3 "$HALO_SYS/python/halo_readiness.py" --repo . --write
```

Explicit degraded accept (human said ship without optional blockers still blocking? use only when human accepts missing **blocking** items temporarily):

```bash
python3 "$HALO_SYS/python/halo_readiness.py" --repo . --write --allow-degraded
```

### 4. Interpret verdict

| Verdict | Meaning | Next |
|---------|---------|------|
| `GO` | No blocking failures | `phase: scaffold` — run **halo-scaffold** |
| `DEGRADED` | Human allowed missing blockers | Scaffold allowed; log risk in baton |
| `NO_GO` | Blocking gaps | Stay `readiness` / `BLOCKED`; list human_action only |

**Never invent GO.** Re-run after human fills `.env`.

### 5. Human message format

```
READINESS: NO_GO
Blocking:
- vercel: Install CLI; vercel login; set VERCEL_TOKEN
- database: set DATABASE_URL
Fill .env from .env.example (values never committed).
Re-run: python3 …/halo_readiness.py --repo . --write
```

Do **not** paste secret values. Do **not** ask human to paste secrets into chat if avoidable — point to local `.env`.

### 6. Artifacts written

| Path | Content |
|------|---------|
| `.halo/readiness.json` | Machine report |
| `.halo/spec/READINESS.md` | Human checklist table |
| `.env.example` | Key names only |
| `.halo/state.json` | `readiness_verdict`, phase |
| `.halo/baton.md` | Next step |

### 7. Live probe reminder

Deploy URLs later: only share after `halo_probe.py --url …` exit 0.

## Forbidden

- Committing `.env`
- Logging API keys
- Scaffold on NO_GO without `--allow-degraded` + human accept
- Deferring “we'll add Sentry later” when intake listed monitoring

## Catalog

Baseline integrations live in `python/halo_catalog.py` — git, gh, node/python (stack-aware), vercel, database, auth/clerk, sentry, email, stripe, openai, analytics. Intake merges and can force blocking.
