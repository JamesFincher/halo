---
name: halo-escalate
description: Write escalation packet and set ESCALATED. Use after 3 fails, denylist, or unrecoverable block.
---

# Halo Escalate

```bash
halo escalate . "reason text"
```

Creates `.halo/escalations/esc-*.md` with state + baton snapshot. Stops loop.
