#!/usr/bin/env python3
"""plan-latest includes trajectories_count alongside scores_count (D111)."""

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


class TestPlanTrajectoriesCount(unittest.TestCase):
    def test_zero_when_trajectories_dir_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _minimal_halo(repo)
            plan = study(repo)
            self.assertIn("trajectories_count", plan)
            self.assertIn("scores_count", plan)
            self.assertEqual(plan["trajectories_count"], 0)
            self.assertIsInstance(plan["trajectories_count"], int)
            self.assertEqual(plan["scores_count"], 0)

    def test_counts_gt_json_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _minimal_halo(repo)
            traj = halo / "trajectories"
            traj.mkdir()
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-002.json").write_text("{}\n", encoding="utf-8")
            (traj / "notes.txt").write_text("ignore\n", encoding="utf-8")
            scores = halo / "scores"
            scores.mkdir()
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            plan = study(repo)
            self.assertEqual(plan["trajectories_count"], 2)
            self.assertEqual(plan["scores_count"], 1)

    def test_write_plan_persists_trajectories_count(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _minimal_halo(repo)
            traj = halo / "trajectories"
            traj.mkdir()
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            plan = study(repo)
            path = write_plan(repo, plan)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["trajectories_count"], 1)
            self.assertIn("scores_count", loaded)


if __name__ == "__main__":
    unittest.main()
