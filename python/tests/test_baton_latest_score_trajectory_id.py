#!/usr/bin/env python3
"""baton.md records latest_score_id and latest_trajectory_id after planner run (D121)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_planner import write_plan  # noqa: E402


class TestBatonLatestScoreTrajectoryId(unittest.TestCase):
    def test_baton_includes_latest_score_and_trajectory_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo").mkdir()
            plan = {
                "at": "2026-01-01T00:00:00Z",
                "recommendation": "ONE unit: D121",
                "features": {
                    "all_pass": False,
                    "next": {"id": "D121", "description": "baton latest ids"},
                },
                "factory_dirty_count": 0,
                "scores_count": 3,
                "trajectories_count": 2,
                "latest_score_id": "S003",
                "latest_trajectory_id": "GT-002",
            }
            write_plan(repo, plan)
            text = (repo / ".halo" / "baton.md").read_text(encoding="utf-8")
            self.assertIn("latest_score_id: S003", text)
            self.assertIn("latest_trajectory_id: GT-002", text)

    def test_baton_dash_when_latest_ids_null_or_missing(self) -> None:
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
                    "latest_score_id": None,
                    "latest_trajectory_id": None,
                },
            )
            text = (repo / ".halo" / "baton.md").read_text(encoding="utf-8")
            self.assertIn("latest_score_id: -", text)
            self.assertIn("latest_trajectory_id: -", text)

    def test_baton_defaults_missing_latest_ids_to_dash(self) -> None:
        """Plan without latest_* keys still emits dash lines."""
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
            self.assertIn("latest_score_id: -", text)
            self.assertIn("latest_trajectory_id: -", text)


if __name__ == "__main__":
    unittest.main()
