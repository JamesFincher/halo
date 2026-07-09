#!/usr/bin/env python3
"""Planner recommends expand ROADMAP when compound-seed last_reason=no_new_roadmap."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_planner import _recommend  # noqa: E402


class TestPlannerNoRoadmap(unittest.TestCase):
    def test_no_new_roadmap_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir(parents=True)
            (halo / "compound-seed.json").write_text(
                json.dumps({"last_reason": "no_new_roadmap", "batch": 5}) + "\n",
                encoding="utf-8",
            )
            rec = _recommend(
                repo,
                {"dogfood": True, "dogfood_mode": "compounding", "status": "ACTIVE"},
                {"all_pass": True, "next": None},
                [],
            )
            self.assertIn("no_new_roadmap", rec)
            self.assertIn("ROADMAP_TEMPLATES", rec)

    def test_all_pass_without_reason(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo").mkdir(parents=True)
            rec = _recommend(
                repo,
                {"dogfood": True, "status": "ACTIVE"},
                {"all_pass": True, "next": None},
                [],
            )
            self.assertIn("force compound seed", rec)
            self.assertNotIn("no_new_roadmap", rec)


if __name__ == "__main__":
    unittest.main()
