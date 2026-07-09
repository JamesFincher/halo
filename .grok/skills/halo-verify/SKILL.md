---
name: halo-verify
description: Pre-deploy evidence + AC check. APPROVED only with RED/GREEN/SPEC certs. Fail closed. Prefer Arena dual-lens.
---

# Halo Verify

Check before deploy:

| Cert | Required |
|------|----------|
| RED_TEST | yes (tests failed before impl) |
| GREEN_TEST | yes |
| FILE_DIFF | no denylist |
| SPEC_OK | AC mapped |
| VERIFIER (Arena) | strongly preferred: `halo arena --id Sxxx` |

## Arena (independent dual lens)

```bash
halo arena . --id Sxxx
# writes .halo/evidence/verdict-Sxxx.json + .halo/arena/Sxxx.json
# exit 0 only on APPROVED consensus

# optional second-pass stub (records ARENA_SPAWN_CHECK; not a second LLM yet)
halo arena . --id Sxxx --spawn-check
# also writes .halo/evidence/arena-spawn-check-Sxxx.json
```

- **A adversarial** — hunt missing GREEN, denylist, ratchet breaks, dishonest pass  
- **B constructive** — approve only if evidence/AC present  
- Split → `NEEDS_REVISION` (fail closed for ship)
- **`--spawn-check`** — explicit second-pass hook cert (`mode: stub-second-pass`). True multi-agent subagent spawn remains host-dependent; the flag proves the optional second-pass path without faking isolation.

Verdicts: `APPROVED` | `NEEDS_REVISION` | `REJECTED`  
Unknown/malformed → never APPROVED.

## Factory dogfood

When TARGET is the Halo factory itself, never `git add -f .halo/`. Auto-commit skips gitignored dogfood paths.
