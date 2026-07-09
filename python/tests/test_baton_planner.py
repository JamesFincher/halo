#!/usr/bin/env python3
"""write_plan rewrites baton recommendation + next id (D100)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_planner import write_plan  # noqa: E402


class TestBatonPlanner(unittest.TestCase):
    def test_baton_has_recommendation_and_next(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo").mkdir()
            plan = {
                "at": "2026-01-01T00:00:00Z",
                "recommendation": "ONE unit: D100 — baton",
                "features": {
                    "all_pass": False,
                    "next": {"id": "D100", "description": "baton test"},
                },
                "factory_dirty_count": 0,
            }
            write_plan(repo, plan)
            text = (repo / ".halo" / "baton.md").read_text(encoding="utf-8")
            self.assertIn("recommendation: ONE unit: D100", text)
            self.assertIn("**D100**", text)

    def test_all_pass_next_is_dash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo").mkdir()
            write_plan(
                repo,
                {
                    "at": "t",
                    "recommendation": "all_pass",
                    "features": {"all_pass": True, "next": None},
                    "factory_dirty_count": 0,
                },
            )
            text = (repo / ".halo" / "baton.md").read_text(encoding="utf-8")
            self.assertIn("next: **-**", text)
            self.assertIn("all_pass", text)
            self.assertIn("recommendation:", text)


if __name__ == "__main__":
    unittest.main()
