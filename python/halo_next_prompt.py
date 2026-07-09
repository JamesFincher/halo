#!/usr/bin/env python3
"""Write .halo/NEXT_PROMPT.md — cold-start self-prompt for Grok Build headless /goal /loop."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from halo_go import next_actions, load as load_state
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from halo_go import next_actions, load as load_state  # type: ignore


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_halo_system() -> Path:
    env = os.environ.get("HALO_SYSTEM")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent


def build_prompt(repo: Path, halo_sys: Path) -> str:
    data: dict[str, Any] = {}
    try:
        data = load_state(repo)
    except SystemExit:
        data = {}

    plan = []
    try:
        plan = next_actions(repo)
    except SystemExit:
        plan = ["halo init", "halo go --enable", "single-pass intake → specs → lock → ready → scaffold → build"]

    phase = data.get("phase") or "unknown"
    status = data.get("status") or "unknown"
    auto = bool(data.get("autonomous"))
    product = data.get("product_name") or repo.name
    max_c = data.get("autonomous_max_cycles") or 5

    plan_bullets = "\n".join(f"- {p}" for p in plan)

    return f"""# Halo self-prompt (auto-generated {utc_now()})

You are Grok Build operating **Halo autonomous mode**. This message is a self-prompt — there is no human waiting to answer questions.

## Authorization

- Skill: **halo-go** (load and obey fully)
- `autonomous: true` — never AskUserQuestion for optional decisions
- Defaults only; log choices to `.halo/autonomous-log.md`
- Hard stops only: PAUSED, ESCALATED, HALO_KILL_SWITCH, denylist, production deploy, 3-fail escalate, true BLOCKED

## TARGET product repo

```
{repo}
```

Halo system (tools/skills):

```
{halo_sys}
```

Product: **{product}** · phase: **{phase}** · status: **{status}** · autonomous: **{auto}** · max_cycles: **{max_c}**

## Bootstrap this turn

1. `export HALO_SYSTEM={halo_sys}`
2. Ensure skills visible: `{halo_sys}/scripts/halo link-skills {repo}` if needed
3. Read: `{repo}/.halo/state.json`, `{repo}/.halo/baton.md`, `{repo}/.halo/autonomous-log.md`
4. If not autonomous: `{halo_sys}/scripts/halo go {repo}`
5. Run plan (no questions):

{plan_bullets}

6. Use CLI under `$HALO_SYSTEM/scripts/halo` and `$HALO_SYSTEM/python/` for control plane.
7. After work: update baton + autonomous-log; run:
   `python3 {halo_sys}/python/halo_next_prompt.py --repo {repo} --write`
8. If more work remains and status is ACTIVE and phase != complete:
   - Prefer **inline continue** if context remains
   - Else exit cleanly; NEXT_PROMPT is ready for headless re-entry:
     `grok -p --prompt-file {repo}/.halo/NEXT_PROMPT.md --cwd {repo} --yolo --max-turns 80`
9. If phase complete or hard stop: write final baton; do **not** spawn another self-prompt.

## Standing rules

- Live probe before any human-facing deploy URL
- Preview only — never production
- Evidence must be real (halo evidence validator)
- One story per build cycle; TDD when adding behavior
- Do not modify Halo system repo unless TARGET is Halo and dogfood is explicit

## End

Execute now. No preamble asking the human what to do.
"""


def write_prompt(repo: Path, halo_sys: Path | None = None) -> Path:
    repo = repo.resolve()
    hs = halo_sys or find_halo_system()
    (repo / ".halo").mkdir(parents=True, exist_ok=True)
    path = repo / ".halo" / "NEXT_PROMPT.md"
    path.write_text(build_prompt(repo, hs), encoding="utf-8")
    sp = repo / ".halo" / "state.json"
    if sp.exists():
        try:
            data = json.loads(sp.read_text(encoding="utf-8"))
            data["next_prompt_at"] = utc_now()
            data["next_prompt_path"] = str(path)
            data["updated_at"] = utc_now()
            sp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        except json.JSONDecodeError:
            pass
    return path


def spawn_headless(repo: Path, max_turns: int = 80) -> dict[str, Any]:
    prompt = repo / ".halo" / "NEXT_PROMPT.md"
    if not prompt.exists():
        write_prompt(repo)
    grok = shutil.which("grok")
    if not grok:
        return {"ok": False, "error": "grok binary not on PATH", "prompt": str(prompt)}
    cmd = [
        grok,
        "-p",
        "--prompt-file",
        str(prompt),
        "--cwd",
        str(repo),
        "--yolo",
        "--max-turns",
        str(max_turns),
        "--output-format",
        "plain",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        return {
            "ok": r.returncode == 0,
            "returncode": r.returncode,
            "cmd": cmd,
            "stdout_tail": (r.stdout or "")[-4000:],
            "stderr_tail": (r.stderr or "")[-2000:],
            "prompt": str(prompt),
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "cmd": cmd, "prompt": str(prompt)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e), "cmd": cmd, "prompt": str(prompt)}


def main() -> None:
    p = argparse.ArgumentParser(prog="halo_next_prompt")
    p.add_argument("--repo", default=".")
    p.add_argument("--halo-system", default=None)
    p.add_argument("--write", action="store_true", default=True)
    p.add_argument("--print", dest="do_print", action="store_true")
    p.add_argument("--spawn", action="store_true", help="run grok -p with NEXT_PROMPT")
    p.add_argument("--max-turns", type=int, default=80)
    args = p.parse_args()
    repo = Path(args.repo).resolve()
    hs = Path(args.halo_system).resolve() if args.halo_system else find_halo_system()

    path = write_prompt(repo, hs)
    if args.do_print:
        print(path.read_text(encoding="utf-8"))
    else:
        print(json.dumps({"ok": True, "path": str(path)}, indent=2))

    if args.spawn:
        result = spawn_headless(repo, max_turns=args.max_turns)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
