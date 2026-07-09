#!/usr/bin/env python3
"""baton.md records scores_count and trajectories_count after planner run (D120)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_planner import write_plan  # noqa: E402


class TestBatonScoresTrajectoriesCount(unittest.TestCase):
    def test_baton_includes_scores_and_trajectories_count(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo").mkdir()
            plan = {
                "at": "2026-01-01T00:00:00Z",
                "recommendation": "ONE unit: D120",
                "features": {
                    "all_pass": False,
                    "next": {"id": "D120", "description": "baton counts"},
                },
                "factory_dirty_count": 0,
                "scores_count": 3,
                "trajectories_count": 2,
            }
            write_plan(repo, plan)
            text = (repo / ".halo" / "baton.md").read_text(encoding="utf-8")
            self.assertIn("scores_count: 3", text)
            self.assertIn("trajectories_count: 2", text)

    def test_baton_zeros_when_counts_missing_or_zero(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo").mkdir()
            write_plan(
                repo,
                {
                    "at": "t",
                    "recommendation": "go",
                    "features": {"all_pass": True, "next": None},
                    "factory_dirty_count": 0,
                    "scores_count": 0,
                    "trajectories_count": 0,
                },
            )
            text = (repo / ".halo" / "baton.md").read_text(encoding="utf-8")
            self.assertIn("scores_count: 0", text)
            self.assertIn("trajectories_count: 0", text)

    def test_baton_defaults_missing_counts_to_zero(self) -> None:
        """Plan without keys still emits zero lines (empty/missing dirs path)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo").mkdir()
            write_plan(
                repo,
                {
                    "at": "t",
                    "recommendation": "go",
                    "features": {"all_pass": False, "next": {"id": "D001"}},
                    "factory_dirty_count": 0,
                },
            )
            text = (repo / ".halo" / "baton.md").read_text(encoding="utf-8")
            self.assertIn("scores_count: 0", text)
            self.assertIn("trajectories_count: 0", text)


if __name__ == "__main__":
    unittest.main()
