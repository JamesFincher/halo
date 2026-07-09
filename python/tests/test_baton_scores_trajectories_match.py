#!/usr/bin/env python3
"""baton.md records scores_trajectories_match after planner run (D125)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_planner import write_plan  # noqa: E402


class TestBatonScoresTrajectoriesMatch(unittest.TestCase):
    def test_baton_includes_scores_trajectories_match_true(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo").mkdir()
            plan = {
                "at": "2026-01-01T00:00:00Z",
                "recommendation": "ONE unit: D125",
                "features": {
                    "all_pass": False,
                    "next": {"id": "D125", "description": "baton match"},
                },
                "factory_dirty_count": 0,
                "scores_count": 3,
                "trajectories_count": 3,
                "scores_trajectories_match": True,
            }
            write_plan(repo, plan)
            text = (repo / ".halo" / "baton.md").read_text(encoding="utf-8")
            self.assertIn("scores_trajectories_match: true", text)

    def test_baton_includes_scores_trajectories_match_false(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo").mkdir()
            plan = {
                "at": "2026-01-01T00:00:00Z",
                "recommendation": "ONE unit: D125",
                "features": {
                    "all_pass": False,
                    "next": {"id": "D125", "description": "baton match"},
                },
                "factory_dirty_count": 0,
                "scores_count": 3,
                "trajectories_count": 2,
                "scores_trajectories_match": False,
            }
            write_plan(repo, plan)
            text = (repo / ".halo" / "baton.md").read_text(encoding="utf-8")
            self.assertIn("scores_trajectories_match: false", text)

    def test_baton_derives_match_when_field_missing(self) -> None:
        """Plan without scores_trajectories_match derives from counts (incl. both zero)."""
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
                    "scores_count": 0,
                    "trajectories_count": 0,
                },
            )
            text = (repo / ".halo" / "baton.md").read_text(encoding="utf-8")
            self.assertIn("scores_trajectories_match: true", text)

    def test_baton_derives_false_when_counts_diverge_and_match_missing(self) -> None:
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
                    "scores_count": 2,
                    "trajectories_count": 1,
                },
            )
            text = (repo / ".halo" / "baton.md").read_text(encoding="utf-8")
            self.assertIn("scores_trajectories_match: false", text)


if __name__ == "__main__":
    unittest.main()
