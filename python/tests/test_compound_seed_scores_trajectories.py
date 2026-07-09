#!/usr/bin/env python3
"""D169: compound-seed.json records scores_count/trajectories_count/match on seed write."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_features import maybe_compound_seed  # noqa: E402


def _scaffold_all_pass(repo: Path) -> Path:
    """Compounding dogfood repo with all features passed (eligible for seed)."""
    halo = repo / ".halo"
    halo.mkdir(parents=True)
    (halo / "state.json").write_text(
        json.dumps(
            {
                "status": "ACTIVE",
                "phase": "build",
                "autonomous": True,
                "dogfood": True,
                "dogfood_mode": "compounding",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (halo / "feature-list.json").write_text(
        json.dumps(
            {
                "version": 1,
                "dogfood": True,
                "dogfood_mode": "compounding",
                "features": [
                    {
                        "id": "D001",
                        "description": "done fixture unique-d169-a",
                        "category": "dogfood",
                        "passes": True,
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return halo


class TestCompoundSeedScoresTrajectories(unittest.TestCase):
    def test_seed_meta_counts_and_match_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _scaffold_all_pass(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text(json.dumps({"id": "S001"}) + "\n")
            (scores / "S002.json").write_text(json.dumps({"id": "S002"}) + "\n")
            (traj / "GT-001.json").write_text(json.dumps({"id": "GT-001"}) + "\n")
            (traj / "GT-002.json").write_text(json.dumps({"id": "GT-002"}) + "\n")

            result = maybe_compound_seed(repo)
            self.assertTrue(result.get("seeded"), result)

            meta = json.loads((halo / "compound-seed.json").read_text(encoding="utf-8"))
            self.assertEqual(meta.get("scores_count"), 2)
            self.assertEqual(meta.get("trajectories_count"), 2)
            self.assertIs(meta.get("scores_trajectories_match"), True)
            self.assertEqual(meta.get("last_reason"), "seeded")

    def test_seed_meta_match_false_when_counts_diverge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _scaffold_all_pass(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text(json.dumps({"id": "S001"}) + "\n")
            (scores / "S002.json").write_text(json.dumps({"id": "S002"}) + "\n")
            (scores / "S003.json").write_text(json.dumps({"id": "S003"}) + "\n")
            (traj / "GT-001.json").write_text(json.dumps({"id": "GT-001"}) + "\n")

            result = maybe_compound_seed(repo)
            self.assertTrue(result.get("seeded"), result)

            meta = json.loads((halo / "compound-seed.json").read_text(encoding="utf-8"))
            self.assertEqual(meta.get("scores_count"), 3)
            self.assertEqual(meta.get("trajectories_count"), 1)
            self.assertIs(meta.get("scores_trajectories_match"), False)

    def test_seed_meta_zeros_and_match_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _scaffold_all_pass(repo)

            result = maybe_compound_seed(repo)
            self.assertTrue(result.get("seeded"), result)

            meta = json.loads((halo / "compound-seed.json").read_text(encoding="utf-8"))
            self.assertEqual(meta.get("scores_count"), 0)
            self.assertEqual(meta.get("trajectories_count"), 0)
            self.assertIs(meta.get("scores_trajectories_match"), True)


if __name__ == "__main__":
    unittest.main()
