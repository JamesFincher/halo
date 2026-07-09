#!/usr/bin/env python3
"""features summary includes top-level trajectories_count (D112)."""

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


class TestSummaryTrajectoriesCount(unittest.TestCase):
    def test_trajectories_count_zero_when_missing(self) -> None:
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
            self.assertIn("trajectories_count", sm)
            self.assertEqual(sm["trajectories_count"], 0)
            self.assertIsInstance(sm["trajectories_count"], int)
            self.assertIn("scores_count", sm)

    def test_trajectories_count_matches_gt_json_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            traj = halo / "trajectories"
            traj.mkdir(parents=True)
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-002.json").write_text("{}\n", encoding="utf-8")
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
            self.assertEqual(sm["trajectories_count"], 2)
            self.assertEqual(sm["scores_count"], 0)
            self.assertTrue(sm["next"]["requires_code"])


if __name__ == "__main__":
    unittest.main()
