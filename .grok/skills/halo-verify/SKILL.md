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
```

- **A adversarial** — hunt missing GREEN, denylist, ratchet breaks, dishonest pass  
- **B constructive** — approve only if evidence/AC present  
- Split → `NEEDS_REVISION` (fail closed for ship)

Verdicts: `APPROVED` | `NEEDS_REVISION` | `REJECTED`  
Unknown/malformed → never APPROVED.

## Factory dogfood

When TARGET is the Halo factory itself, never `git add -f .halo/`. Auto-commit skips gitignored dogfood paths.
