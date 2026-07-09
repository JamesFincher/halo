#!/usr/bin/env python3
"""features summary includes top-level scores_trajectories_match bool (D123)."""

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


def _write_features(halo: Path) -> None:
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


class TestSummaryScoresTrajectoriesMatch(unittest.TestCase):
    def test_match_true_when_both_zero(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            _write_features(halo)
            sm = summary(repo, compound=False)
            self.assertIn("scores_trajectories_match", sm)
            self.assertIsInstance(sm["scores_trajectories_match"], bool)
            self.assertEqual(sm["scores_count"], 0)
            self.assertEqual(sm["trajectories_count"], 0)
            self.assertTrue(sm["scores_trajectories_match"])

    def test_match_true_when_counts_equal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir(parents=True)
            traj.mkdir(parents=True)
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            (scores / "S002.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-002.json").write_text("{}\n", encoding="utf-8")
            _write_features(halo)
            sm = summary(repo, compound=False)
            self.assertEqual(sm["scores_count"], 2)
            self.assertEqual(sm["trajectories_count"], 2)
            self.assertTrue(sm["scores_trajectories_match"])

    def test_match_false_when_counts_diverge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir(parents=True)
            traj.mkdir(parents=True)
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            (scores / "S002.json").write_text("{}\n", encoding="utf-8")
            (scores / "S003.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            _write_features(halo)
            sm = summary(repo, compound=False)
            self.assertEqual(sm["scores_count"], 3)
            self.assertEqual(sm["trajectories_count"], 1)
            self.assertFalse(sm["scores_trajectories_match"])


if __name__ == "__main__":
    unittest.main()
