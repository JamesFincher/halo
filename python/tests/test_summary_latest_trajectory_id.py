#!/usr/bin/env python3
"""features summary includes top-level latest_trajectory_id (D116)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_features import summary  # noqa: E402


class TestSummaryLatestTrajectoryId(unittest.TestCase):
    def test_latest_trajectory_id_null_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
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
            sm = summary(repo, compound=False)
            self.assertIn("latest_trajectory_id", sm)
            self.assertIsNone(sm["latest_trajectory_id"])

    def test_latest_trajectory_id_is_max_gt_numeric(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            traj = halo / "trajectories"
            traj.mkdir(parents=True)
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
            (traj / "other.json").write_text("{}\n", encoding="utf-8")
            (halo / "feature-list.json").write_text(
                json.dumps(
                    {
                        "features": [
                            {
                                "id": "D001",
                                "description": "open",
                                "passes": False,
                                "requires_code": True,
                                "steps": ["a"],
                            }
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            sm = summary(repo, compound=False)
            self.assertEqual(sm["latest_trajectory_id"], "GT-003")
            self.assertIsInstance(sm["latest_trajectory_id"], str)

    def test_latest_trajectory_id_null_when_trajectories_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            (halo / "trajectories").mkdir(parents=True)
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
            sm = summary(repo, compound=False)
            self.assertIsNone(sm["latest_trajectory_id"])


if __name__ == "__main__":
    unittest.main()
