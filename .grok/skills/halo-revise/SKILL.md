---
name: halo-revise
description: Unlock locked specs for product pivot; re-enter spec_review then lock + readiness again.
---

# Halo Revise (spec unlock)

When human changes scope mid-flight:

```bash
halo unlock
# edit .halo/spec/*
halo lock
halo ready
```

Do not scaffold/build on unlocked drafting specs.
