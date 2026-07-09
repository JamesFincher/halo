# HALO.md — Product loop config

## Deploy policy

- Preview/dev only by default.
- **Live probe required** before any human-facing deploy message.
- Probe tool: factory `python/halo_probe.py`.

## Budget defaults

| Parameter | Value |
|-----------|-------|
| Max story attempts | 3 |
| Daily cycle soft cap | 20 |
| Coverage regression block | >10% |

## Denylist

Never touch without human:

```
.env
.env.*
*credentials*
*secret*
```

## Status

`ACTIVE` | set `PAUSED` via `.halo/state.json` to halt autonomous loop.
