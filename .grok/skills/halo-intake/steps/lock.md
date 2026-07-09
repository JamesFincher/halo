# Lock intake

Show compact summary of all locked intake fields.

AskUserQuestion:

- **Lock and write spec pack** (recommended)
- Edit a section (which?)
- Pause — write baton only

On lock:

```bash
python3 python/halo_state.py set --repo "$TARGET" --phase spec_pack --spec-status drafting
```

Then invoke **halo-spec-pack**.
