#!/usr/bin/env python3
"""Tests for file-to-file lifecycle connections and edge cases fixed after the verbose spec pack."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_doctor import check_product
from halo_milestones import milestones_from_md
from halo_next_prompt import spec_digest
from halo_readiness import check_spec_pack


class TestMilestonesParser(unittest.TestCase):
    def test_parses_bold_scope_and_done_when(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "MILESTONES.md"
            p.write_text(
                "# Milestones\n\n## M1 — Foundation\n"
                "- **Slug**: `foundation`\n"
                "- **Scope**: Core app shell and first user path.\n"
                "- **Done when**: User can open the app and complete the primary path.\n"
                "- **Depends on**: []\n",
                encoding="utf-8",
            )
            ms = milestones_from_md(p)
            self.assertEqual(len(ms), 1)
            self.assertEqual(ms[0]["n"], 1)
            self.assertEqual(ms[0]["name"], "Foundation")
            self.assertEqual(ms[0]["scope"], "Core app shell and first user path.")
            self.assertEqual(
                ms[0]["done_when"],
                "User can open the app and complete the primary path.",
            )


class TestReadinessSpecPack(unittest.TestCase):
    def test_blocking_when_locked_and_missing_core(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo" / "spec").mkdir(parents=True)
            result = check_spec_pack(repo, "locked")
            self.assertFalse(result["ok"])
            self.assertTrue(result["blocking"])
            self.assertIn("PRD.md", result["human_action"])

    def test_non_blocking_when_not_locked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo" / "spec").mkdir(parents=True)
            result = check_spec_pack(repo, "ready_for_review")
            self.assertFalse(result["ok"])
            self.assertFalse(result["blocking"])

    def test_ok_when_all_spec_files_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec = repo / ".halo" / "spec"
            spec.mkdir(parents=True)
            for f in [
                "PRD.md", "STACK.md", "DATA-MODEL.md", "STORIES.md", "MILESTONES.md", "READINESS.md",
                "API.md", "USER-FLOWS.md", "ARCHITECTURE-DECISIONS.md", "SEQUENCE.md", "STATE.md",
                "SECURITY.md", "TEST-PLAN.md", "FRONTEND.md", "BACKEND.md", "MOBILE.md",
                "DEPLOYMENT.md", "RUNBOOK.md", "METRICS.md", "PROMPTS.md", "GLOSSARY.md",
                "RISKS.md", "PERSONAS.md", "SEED.md", "CHANGELOG.md", "CONTRIBUTING.md",
            ]:
                (spec / f).write_text("# stub", encoding="utf-8")
            result = check_spec_pack(repo, "locked")
            self.assertTrue(result["ok"])
            self.assertFalse(result["blocking"])


class TestDoctorSpecCheck(unittest.TestCase):
    def test_reports_missing_expanded_spec_files_when_locked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            spec = halo / "spec"
            spec.mkdir()
            (spec / "PRD.md").write_text("# PRD", encoding="utf-8")
            (spec / "STACK.md").write_text("# Stack", encoding="utf-8")
            (spec / "STORIES.md").write_text("# Stories", encoding="utf-8")
            (halo / "state.json").write_text(
                json.dumps({"version": 1, "spec_status": "locked", "spec_pack_version": 2}),
                encoding="utf-8",
            )
            issues = check_product(repo)
            codes = {i["code"] for i in issues}
            self.assertIn("locked_missing_spec", codes)
            items = [i["item"] for i in issues if i["code"] == "locked_missing_spec"]
            self.assertIn("API.md", items)
            self.assertIn("MILESTONES.md", items)


class TestNextPromptSpecDigest(unittest.TestCase):
    def test_spec_digest_lists_files_and_snippets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            spec = repo / ".halo" / "spec"
            spec.mkdir(parents=True)
            (spec / "PRD.md").write_text("# PRD\n\nBuild a thing.", encoding="utf-8")
            (spec / "STACK.md").write_text("# Stack\n\nNext.js.", encoding="utf-8")
            (spec / "API.md").write_text("# API\n\nPOST /things", encoding="utf-8")
            digest = spec_digest(repo, limit=200)
            self.assertIn("PRD.md", digest)
            self.assertIn("STACK.md", digest)
            self.assertIn("API.md", digest)
            self.assertIn("Build a thing.", digest)


if __name__ == "__main__":
    unittest.main()
