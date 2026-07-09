#!/usr/bin/env python3
"""plan-latest includes scores_trajectories_match bool (D124)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_planner import study, write_plan  # noqa: E402


def _minimal_halo(repo: Path) -> Path:
    halo = repo / ".halo"
    halo.mkdir(parents=True, exist_ok=True)
    (halo / "state.json").write_text(
        json.dumps({"status": "ACTIVE", "phase": "build", "autonomous": True}) + "\n",
        encoding="utf-8",
    )
    (halo / "loop.json").write_text(
        json.dumps({"active": True, "iteration": 1}) + "\n", encoding="utf-8"
    )
    (halo / "feature-list.json").write_text(
        json.dumps(
            {
                "features": [
                    {
                        "id": "D001",
                        "description": "done",
                        "passes": True,
                        "steps": [],
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return halo


class TestPlanScoresTrajectoriesMatch(unittest.TestCase):
    def test_true_when_both_zero(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _minimal_halo(repo)
            plan = study(repo)
            self.assertIn("scores_trajectories_match", plan)
            self.assertIsInstance(plan["scores_trajectories_match"], bool)
            self.assertEqual(plan["scores_count"], 0)
            self.assertEqual(plan["trajectories_count"], 0)
            self.assertTrue(plan["scores_trajectories_match"])

    def test_true_when_counts_equal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _minimal_halo(repo)
            scores = halo / "scores"
            scores.mkdir()
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            (scores / "S002.json").write_text("{}\n", encoding="utf-8")
            traj = halo / "trajectories"
            traj.mkdir()
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-002.json").write_text("{}\n", encoding="utf-8")
            plan = study(repo)
            self.assertEqual(plan["scores_count"], 2)
            self.assertEqual(plan["trajectories_count"], 2)
            self.assertTrue(plan["scores_trajectories_match"])

    def test_false_when_counts_diverge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _minimal_halo(repo)
            scores = halo / "scores"
            scores.mkdir()
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            (scores / "S002.json").write_text("{}\n", encoding="utf-8")
            (scores / "S003.json").write_text("{}\n", encoding="utf-8")
            traj = halo / "trajectories"
            traj.mkdir()
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            plan = study(repo)
            self.assertEqual(plan["scores_count"], 3)
            self.assertEqual(plan["trajectories_count"], 1)
            self.assertFalse(plan["scores_trajectories_match"])

    def test_write_plan_persists_match_bool(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _minimal_halo(repo)
            scores = halo / "scores"
            scores.mkdir()
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            plan = study(repo)
            path = write_plan(repo, plan)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("scores_trajectories_match", loaded)
            self.assertFalse(loaded["scores_trajectories_match"])


if __name__ == "__main__":
    unittest.main()
