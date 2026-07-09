---
name: halo-doctor
description: Validate Halo system install and product integrity.
---

# Halo Doctor

```bash
halo doctor
halo doctor /path/to/product
halo doctor --strict /path/to/product   # CI: exit 2 on errors
halo evidence /path/to/product          # cert schema, not just files
```

Checks:
- required skills / python modules / CLI verbs
- docs present (WORKFLOWS, ARCHITECTURE-DEEP)
- product state phase known; locked specs complete
- evidence validator when files exist
- network probe

**Strict mode** = fail closed for system integrity matrix.
