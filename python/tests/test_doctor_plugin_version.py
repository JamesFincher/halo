#!/usr/bin/env python3
"""doctor errors when plugin.json missing version (D092)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_doctor import check_system  # noqa: E402


class TestDoctorPluginVersion(unittest.TestCase):
    def test_missing_version_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sys_root = Path(td)
            # minimal factory shape so check_system runs plugin path
            (sys_root / "python").mkdir()
            (sys_root / "python" / "halo_state.py").write_text("#\n", encoding="utf-8")
            for py in (
                "halo_readiness.py",
                "halo_scaffold.py",
                "halo_probe.py",
                "halo_go.py",
                "halo_spec_write.py",
                "halo_milestones.py",
                "halo_evidence.py",
                "halo_phases.py",
                "halo_doctor.py",
                "halo_catalog.py",
                "halo_next_prompt.py",
                "halo_link_skills.py",
                "halo_features.py",
                "halo_progress.py",
                "halo_lock.py",
                "halo_budget.py",
                "halo_ratchet.py",
                "halo_arena.py",
                "halo_commit.py",
                "halo_stories_sync.py",
                "halo_drive.py",
                "halo_planner.py",
            ):
                (sys_root / "python" / py).write_text("#\n", encoding="utf-8")
            # skills stubs
            skills = sys_root / ".grok" / "skills"
            for name in (
                "halo-bootstrap",
                "halo-intake",
                "halo-spec-pack",
                "halo-readiness",
                "halo-scaffold",
                "halo-build",
                "halo-verify",
                "halo-deploy",
                "halo-go",
                "halo-status",
                "halo-triage",
                "halo-pause",
                "halo-escalate",
                "halo-handoff",
                "halo-revise",
                "halo-doctor",
            ):
                d = skills / name
                d.mkdir(parents=True)
                (d / "SKILL.md").write_text("#\n", encoding="utf-8")
            (sys_root / "scripts").mkdir()
            (sys_root / "scripts" / "halo").write_text(
                "init)\nstatus)\nspecs)\nlock)\nunlock)\nready)\nscaffold)\n"
                "milestones)\nprobe)\nbuild)\nstop)\nresume)\nescalate)\ntriage)\n"
                "handoff)\ndoctor)\ngo)\ncontinue)\nlink-skills)\nfeatures)\nprogress)\n"
                "budget)\nratchet)\narena)\ncommit-unit)\nloop)\n",
                encoding="utf-8",
            )
            for doc in (
                "docs/WORKFLOWS.md",
                "docs/ARCHITECTURE.md",
                "docs/ARCHITECTURE-DEEP.md",
                "docs/GROK-BUILD.md",
                "AGENTS.md",
            ):
                path = sys_root / doc
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    "halo go autonomous probe NEXT_PROMPT self-prompt\n", encoding="utf-8"
                )
            (sys_root / "hooks").mkdir()
            (sys_root / "hooks" / "hooks.json").write_text(
                json.dumps({"hooks": {"Stop": []}}) + "\n", encoding="utf-8"
            )
            (sys_root / "commands").mkdir()
            (sys_root / "commands" / "go.md").write_text("# go\n", encoding="utf-8")
            plug = sys_root / ".grok-plugin"
            plug.mkdir()
            (plug / "plugin.json").write_text(
                json.dumps({"name": "halo"}) + "\n", encoding="utf-8"
            )
            issues = check_system(sys_root)
            codes = [i["code"] for i in issues]
            self.assertIn("plugin_version_missing", codes)


if __name__ == "__main__":
    unittest.main()
