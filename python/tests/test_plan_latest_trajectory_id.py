#!/usr/bin/env python3
"""plan-latest includes latest_trajectory_id alongside trajectories_count (D119)."""

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


class TestPlanLatestTrajectoryId(unittest.TestCase):
    def test_null_when_trajectories_dir_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _minimal_halo(repo)
            plan = study(repo)
            self.assertIn("latest_trajectory_id", plan)
            self.assertIsNone(plan["latest_trajectory_id"])
            self.assertIn("trajectories_count", plan)
            self.assertEqual(plan["trajectories_count"], 0)

    def test_max_gt_numeric_prefers_payload_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _minimal_halo(repo)
            traj = halo / "trajectories"
            traj.mkdir()
            (traj / "GT-001.json").write_text(
                json.dumps({"id": "GT-001"}) + "\n", encoding="utf-8"
            )
            (traj / "GT-003.json").write_text(
                json.dumps({"id": "GT-003"}) + "\n", encoding="utf-8"
            )
            (traj / "GT-002.json").write_text(
                json.dumps({"id": "GT-002"}) + "\n", encoding="utf-8"
            )
            (traj / "notes.txt").write_text("ignore\n", encoding="utf-8")
            (traj / "other.json").write_text(
                json.dumps({"id": "nope"}) + "\n", encoding="utf-8"
            )
            plan = study(repo)
            self.assertEqual(plan["latest_trajectory_id"], "GT-003")
            self.assertEqual(plan["trajectories_count"], 3)

    def test_write_plan_persists_latest_trajectory_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _minimal_halo(repo)
            traj = halo / "trajectories"
            traj.mkdir()
            (traj / "GT-007.json").write_text(
                json.dumps({"id": "GT-007"}) + "\n", encoding="utf-8"
            )
            plan = study(repo)
            path = write_plan(repo, plan)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["latest_trajectory_id"], "GT-007")
            self.assertIn("trajectories_count", loaded)


if __name__ == "__main__":
    unittest.main()
