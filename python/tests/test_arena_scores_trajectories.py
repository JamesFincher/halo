#!/usr/bin/env python3
"""D150: halo arena JSON includes scores_count trajectories_count scores_trajectories_match."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_arena import verify  # noqa: E402


class TestArenaScoresTrajectories(unittest.TestCase):
    def _scaffold(self, repo: Path, feature_id: str = "D150") -> Path:
        halo = repo / ".halo"
        halo.mkdir()
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
                    "features": [
                        {
                            "id": feature_id,
                            "description": "fixture",
                            "category": "dogfood",
                            "passes": False,
                            "steps": ["a"],
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (halo / "evidence").mkdir()
        # GREEN evidence so arena can complete dual-lens without hard reject noise
        (halo / "evidence" / f"{feature_id}-green.json").write_text(
            json.dumps(
                {
                    "cert": "GREEN",
                    "feature_id": feature_id,
                    "exit_code": 0,
                    "ok": True,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return halo

    def test_arena_json_has_counts_and_match_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text(json.dumps({"id": "S001"}) + "\n")
            (scores / "S002.json").write_text(json.dumps({"id": "S002"}) + "\n")
            (traj / "GT-001.json").write_text(json.dumps({"id": "GT-001"}) + "\n")
            (traj / "GT-002.json").write_text(json.dumps({"id": "GT-002"}) + "\n")
            data = verify(repo, "D150")
            self.assertIn("scores_count", data)
            self.assertIn("trajectories_count", data)
            self.assertIn("scores_trajectories_match", data)
            self.assertIsInstance(data["scores_count"], int)
            self.assertIsInstance(data["trajectories_count"], int)
            self.assertIsInstance(data["scores_trajectories_match"], bool)
            self.assertEqual(data["scores_count"], 2)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertIs(data["scores_trajectories_match"], True)
            # arena cert shape still present
            self.assertIn("verdict", data)
            self.assertIn("feature_id", data)
            # persisted arena cert also has top-level fields
            cert_path = halo / "arena" / "D150.json"
            self.assertTrue(cert_path.is_file(), "arena cert should be written")
            cert = json.loads(cert_path.read_text(encoding="utf-8"))
            self.assertEqual(cert["scores_count"], 2)
            self.assertEqual(cert["trajectories_count"], 2)
            self.assertIs(cert["scores_trajectories_match"], True)

    def test_arena_json_match_false_when_counts_diverge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text(json.dumps({"id": "S001"}) + "\n")
            (traj / "GT-001.json").write_text(json.dumps({"id": "GT-001"}) + "\n")
            (traj / "GT-002.json").write_text(json.dumps({"id": "GT-002"}) + "\n")
            data = verify(repo, "D150")
            self.assertEqual(data["scores_count"], 1)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertIs(data["scores_trajectories_match"], False)

    def test_arena_json_zeros_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = verify(repo, "D150")
            self.assertEqual(data["scores_count"], 0)
            self.assertEqual(data["trajectories_count"], 0)
            self.assertIs(data["scores_trajectories_match"], True)


if __name__ == "__main__":
    unittest.main()
