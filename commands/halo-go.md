---
name: halo-go
description: Alias for continuous Halo drive (Grok headless re-entry; Stop is passive).
argument-hint: "[--max N] [--no-spawn]"
---

# /halo-go → continuous drive

```!
export HALO_SYSTEM="${HALO_SYSTEM:-${GROK_PLUGIN_ROOT:-$CLAUDE_PLUGIN_ROOT}}"
export TARGET="${GROK_WORKSPACE_ROOT:-${CLAUDE_PROJECT_DIR:-$PWD}}"
cd "$TARGET"
bash "${HALO_SYSTEM}/scripts/setup-halo-loop.sh" $ARGUMENTS
```

Grok: Stop is passive — continuous work uses **headless spawn / supervisor**, not `decision:block` on Stop.

Then immediately:

- Read baton + `.halo/NEXT_PROMPT.md` + feature/phase list
- Execute one unit
- Rewrite self-contained `.halo/NEXT_PROMPT.md`
- Do not wait for the human

Prefer documented headless form for spawns:

```bash
grok -p "$(cat .halo/NEXT_PROMPT.md)" --always-approve --no-auto-update --output-format streaming-json
```

`--no-spawn`: arm state/files only; do not start watchdog/headless children.

Project hooks: if hooks live under the repo, user needs `/hooks-trust` or `grok --trust` once.
