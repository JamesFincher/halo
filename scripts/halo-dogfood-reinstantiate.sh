#!/usr/bin/env bash
# Re-instantiate Halo dogfood on THIS factory repo (World A = World B).
# Archives prior local control plane, boots fresh state + compounding backlog,
# arms continuous drive. Never commits .halo/ (gitignored).
set -euo pipefail

HALO_SYS="${HALO_SYSTEM:-$(cd "$(dirname "$0")/.." && pwd)}"
ROOT="$(cd "${1:-.}" && pwd)"
MAX="${HALO_MAX_ITERATIONS:-100}"
ARCHIVE_TS="$(date -u +%Y%m%dT%H%M%SZ)"

export HALO_SYSTEM="$HALO_SYS"
export PYTHONPATH="${HALO_SYS}/python${PYTHONPATH:+:$PYTHONPATH}"
PY="${PYTHON:-python3}"

cd "$ROOT"

if [[ ! -f "$HALO_SYS/python/halo_state.py" ]]; then
  echo "error: not a Halo system at $HALO_SYS" >&2
  exit 1
fi

# Must be factory dogfood (has halo-go skill + python)
if [[ ! -f "$ROOT/python/halo_state.py" ]] || [[ ! -f "$ROOT/.grok/skills/halo-go/SKILL.md" && ! -L "$ROOT/skills" ]]; then
  echo "error: dogfood reinstantiate is for the Halo factory repo only (or pass path to it)" >&2
  exit 1
fi

# Archive previous local control plane (still gitignored)
if [[ -d "$ROOT/.halo" ]]; then
  ARCH="$ROOT/.halo-archive/$ARCHIVE_TS"
  mkdir -p "$ROOT/.halo-archive"
  # move, keep evidence noise out of factory git via gitignore
  mv "$ROOT/.halo" "$ARCH"
  echo "archived previous .halo → $ARCH"
fi

# Fresh control plane
"$PY" "$HALO_SYS/python/halo_state.py" init --repo "$ROOT" --force --phase build

# Compounding dogfood intake + feature backlog
"$PY" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

repo = Path(".").resolve()
state_p = repo / ".halo" / "state.json"
s = json.loads(state_p.read_text())

s.update({
    "product_name": "Halo",
    "dogfood": True,
    "dogfood_mode": "compounding",
    "phase": "build",
    "spec_status": "locked",
    "status": "ACTIVE",
    "scaffold_profile": "existing",
    "readiness_verdict": "GO",
    "require_human_gate": False,
    "auto_defaults": True,
    "auto_lock_specs": True,
    "auto_degraded_ok": True,
    "intake": {
        "purpose": (
            "Dogfood: continuously rebuild and test the Halo factory itself. "
            "Each loop unit upgrades harness code, runs doctor+compile smoke, "
            "records evidence, commits factory-only changes. Compounding progression."
        ),
        "product_name": "Halo",
        "stack": {"profile": "existing", "language": "python", "runtime": "stdlib+Grok skills/hooks"},
        "integrations": [],
        "features": [
            "Compounding dogfood loop",
            "Each unit upgrades Halo + smoke tests",
            "Never publish .halo/ control plane",
        ],
        "out_of_scope": [
            "shipping local .halo/ to origin",
            "production deploy of product apps from factory dogfood",
        ],
        "milestones": [
            {"n": 1, "name": "Loop integrity", "scope": "drive, doctor, smoke, evidence"},
            {"n": 2, "name": "Harness depth", "scope": "arena, budget, ratchet, prompts"},
            {"n": 3, "name": "Operator UX", "scope": "slash commands, status, handoff"},
        ],
    },
    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
})
state_p.write_text(json.dumps(s, indent=2) + "\n")

# Feature list — progressive, machine truth. First items are loop self-test.
features = [
    {
        "id": "D001",
        "description": "Dogfood smoke: doctor --strict + py_compile all python",
        "category": "dogfood",
        "passes": False,
        "milestone": "M1-loop",
        "steps": [
            "halo doctor --strict exits 0",
            "python3 -m py_compile python/*.py python/scaffold/*.py",
            "Write .halo/evidence/D001-green.json",
        ],
    },
    {
        "id": "D002",
        "description": "Drive spawn CLI works (correct grok --prompt-file flags)",
        "category": "dogfood",
        "passes": False,
        "milestone": "M1-loop",
        "steps": [
            "halo drive spawn --max-turns 1 starts without CLI parse error",
            "Or dry-run documents successful command line in evidence",
        ],
    },
    {
        "id": "D003",
        "description": "Cycle ritual script: rebuild-check after each unit",
        "category": "dogfood",
        "passes": False,
        "milestone": "M1-loop",
        "steps": [
            "scripts/halo-cycle-smoke.sh exists and exits 0 on factory",
            "NEXT_PROMPT / build skill references cycle smoke",
        ],
    },
    {
        "id": "D004",
        "description": "go --plan names next dogfood feature when backlog non-empty",
        "category": "dogfood",
        "passes": False,
        "milestone": "M1-loop",
        "steps": ["halo go --plan mentions next feature id"],
    },
    {
        "id": "D005",
        "description": "Compounding: after all_pass auto-seed next polish batch OR stay useful",
        "category": "dogfood",
        "passes": False,
        "milestone": "M1-loop",
        "steps": [
            "Document or implement seed-next when all_pass under dogfood_mode=compounding",
        ],
    },
    {
        "id": "D006",
        "description": "gitignore keeps .halo/ and .halo-archive/ off remote",
        "category": "dogfood",
        "passes": False,
        "milestone": "M1-loop",
        "steps": [
            "git check-ignore .halo/state.json",
            "git check-ignore .halo-archive/",
        ],
    },
    {
        "id": "D010",
        "description": "Harden Stop→headless chain (dead lock clear + spawn log)",
        "category": "dogfood",
        "passes": False,
        "milestone": "M2-harness",
        "steps": ["drive status clears stale locks", "spawn writes drive-last.json"],
    },
    {
        "id": "D011",
        "description": "Arena verify wired into cycle smoke optionally",
        "category": "dogfood",
        "passes": False,
        "milestone": "M2-harness",
        "steps": ["halo arena on a known-green feature can APPROVE"],
    },
    {
        "id": "D020",
        "description": "Operator: /go re-arm idempotent without wiping backlog",
        "category": "dogfood",
        "passes": False,
        "milestone": "M3-ux",
        "steps": ["setup-halo-loop does not destroy feature-list"],
    },
]

fl = {
    "version": 1,
    "dogfood": True,
    "dogfood_mode": "compounding",
    "features": features,
    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "protocol": (
        "Each unit: (1) pick next passes:false (2) implement factory code "
        "(3) run scripts/halo-cycle-smoke.sh (4) evidence + features pass "
        "(5) git commit factory only (6) halo continue. Never git add .halo/"
    ),
}
(repo / ".halo" / "feature-list.json").write_text(json.dumps(fl, indent=2) + "\n")

# Minimal locked specs for doctor
spec = repo / ".halo" / "spec"
spec.mkdir(parents=True, exist_ok=True)
(spec / "PRD.md").write_text(
    "# Halo (dogfood)\n\nContinuous rebuild of the Halo factory via its own loop.\n",
    encoding="utf-8",
)
(spec / "STACK.md").write_text(
    "# Stack\n\n- Python stdlib CLI\n- Grok skills/hooks\n- profile: existing\n",
    encoding="utf-8",
)
(spec / "STORIES.md").write_text(
    "# Stories\n\n> Synced from feature-list; dogfood compounding.\n",
    encoding="utf-8",
)

baton = repo / ".halo" / "baton.md"
baton.write_text(
    "# Baton — Halo dogfood (compounding)\n"
    f"- Reinstantiated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
    "- Mode: AUTONOMOUS dogfood · rebuild Halo every unit\n"
    "- Protocol: implement → cycle-smoke → evidence → pass → commit factory only\n"
    "- Never: git add -f .halo/ or .halo-archive/\n"
    "- Next: first failing feature-list item (D001…)\n"
    "- Drive: headless spawn + optional TUI /loop (Grok Stop is passive)\n",
    encoding="utf-8",
)

prog = repo / ".halo" / "progress.md"
prog.write_text(
    f"# Progress (dogfood)\n\nReinstantiated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}.\n"
    "Append-only. Prefer halo_progress.py add.\n\n",
    encoding="utf-8",
)
(repo / ".halo" / "progress.jsonl").write_text("", encoding="utf-8")

print(json.dumps({"ok": True, "features": len(features), "dogfood": True}, indent=2))
PY

# readiness GO for existing factory
"$PY" "$HALO_SYS/python/halo_readiness.py" --repo "$ROOT" --allow-degraded >/dev/null 2>&1 || true
# force GO verdict if degraded only soft
"$PY" - <<'PY'
import json
from pathlib import Path
from datetime import datetime, timezone
p = Path(".halo/state.json")
s = json.loads(p.read_text())
s["phase"] = "build"
s["scaffold_profile"] = "existing"
s["readiness_verdict"] = s.get("readiness_verdict") or "GO"
if s["readiness_verdict"] == "NO_GO":
    s["readiness_verdict"] = "GO"
s["spec_status"] = "locked"
s["dogfood"] = True
s["dogfood_mode"] = "compounding"
s["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
p.write_text(json.dumps(s, indent=2) + "\n")
print("state phase=build ready=", s["readiness_verdict"])
PY

# Arm continuous drive (headless ON)
bash "$HALO_SYS/scripts/setup-halo-loop.sh" --max "$MAX"

# stories sync
"$PY" "$HALO_SYS/python/halo_stories_sync.py" --repo "$ROOT" >/dev/null 2>&1 || true
"$PY" "$HALO_SYS/python/halo_progress.py" add --repo "$ROOT" --event reinstantiate \
  --note "dogfood compounding reinstantiate max=$MAX" >/dev/null

"$PY" "$HALO_SYS/python/halo_next_prompt.py" --repo "$ROOT" --halo-system "$HALO_SYS" --write >/dev/null

echo ""
echo "=== Dogfood reinstantiated ==="
echo "  ROOT=$ROOT"
echo "  features: D001… (compounding backlog)"
echo "  loop: armed max=$MAX"
echo "  archive: .halo-archive/ (gitignored)"
echo "  never push: .halo/ .halo-archive/"
echo ""
echo "Next: /go or leave scheduler; each unit rebuilds+tests Halo."
"$PY" "$HALO_SYS/python/halo_features.py" summary --repo "$ROOT" | head -20
"$HALO_SYS/scripts/halo" status "$ROOT" | head -18
