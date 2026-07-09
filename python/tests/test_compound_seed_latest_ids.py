#!/usr/bin/env python3
"""D155: compound-seed.json records latest_score_id and latest_trajectory_id on seed write."""

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
                        "description": "done fixture unique-d155-a",
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


class TestCompoundSeedLatestIds(unittest.TestCase):
    def test_seed_meta_has_latest_ids_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _scaffold_all_pass(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text(json.dumps({"id": "S001"}) + "\n")
            (scores / "S003.json").write_text(json.dumps({"id": "S003"}) + "\n")
            (scores / "S002.json").write_text(json.dumps({"id": "S002"}) + "\n")
            (traj / "GT-001.json").write_text(json.dumps({"id": "GT-001"}) + "\n")
            (traj / "GT-010.json").write_text(json.dumps({"id": "GT-010"}) + "\n")

            result = maybe_compound_seed(repo)
            self.assertTrue(result.get("seeded"), result)

            meta_path = halo / "compound-seed.json"
            self.assertTrue(meta_path.is_file(), "compound-seed.json must exist after seed")
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            self.assertIn("latest_score_id", meta)
            self.assertIn("latest_trajectory_id", meta)
            self.assertEqual(meta["latest_score_id"], "S003")
            self.assertEqual(meta["latest_trajectory_id"], "GT-010")
            self.assertEqual(meta.get("last_reason"), "seeded")

    def test_seed_meta_latest_ids_null_when_dirs_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _scaffold_all_pass(repo)
            (halo / "scores").mkdir()
            (halo / "trajectories").mkdir()

            result = maybe_compound_seed(repo)
            self.assertTrue(result.get("seeded"), result)

            meta = json.loads((halo / "compound-seed.json").read_text(encoding="utf-8"))
            self.assertIn("latest_score_id", meta)
            self.assertIn("latest_trajectory_id", meta)
            self.assertIsNone(meta["latest_score_id"])
            self.assertIsNone(meta["latest_trajectory_id"])

    def test_seed_meta_latest_ids_null_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _scaffold_all_pass(repo)

            result = maybe_compound_seed(repo)
            self.assertTrue(result.get("seeded"), result)

            meta = json.loads((halo / "compound-seed.json").read_text(encoding="utf-8"))
            self.assertIn("latest_score_id", meta)
            self.assertIn("latest_trajectory_id", meta)
            self.assertIsNone(meta["latest_score_id"])
            self.assertIsNone(meta["latest_trajectory_id"])


if __name__ == "__main__":
    unittest.main()
