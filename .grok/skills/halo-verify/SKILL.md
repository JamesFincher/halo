---
name: halo-verify
description: Pre-deploy evidence + AC check. APPROVED only with RED/GREEN/SPEC certs. Fail closed.
---

# Halo Verify

Check before deploy:

| Cert | Required |
|------|----------|
| RED_TEST | yes (tests failed before impl) |
| GREEN_TEST | yes |
| FILE_DIFF | no denylist |
| SPEC_OK | AC mapped |

Verdicts: `APPROVED` | `NEEDS_REVISION` | `REJECTED`  
Unknown/malformed → never APPROVED.
