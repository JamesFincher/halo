#!/usr/bin/env python3
"""D151: halo arena JSON includes latest_score_id and latest_trajectory_id."""

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


class TestArenaLatestIds(unittest.TestCase):
    def _scaffold(self, repo: Path, feature_id: str = "D151") -> Path:
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

    def test_arena_json_has_latest_ids_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text(json.dumps({"id": "S001"}) + "\n")
            (scores / "S003.json").write_text(json.dumps({"id": "S003"}) + "\n")
            (traj / "GT-001.json").write_text(json.dumps({"id": "GT-001"}) + "\n")
            (traj / "GT-002.json").write_text(json.dumps({"id": "GT-002"}) + "\n")
            data = verify(repo, "D151")
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertEqual(data["latest_score_id"], "S003")
            self.assertEqual(data["latest_trajectory_id"], "GT-002")
            # D150 fields still present
            self.assertEqual(data["scores_count"], 2)
            self.assertEqual(data["trajectories_count"], 2)
            # persisted arena cert also has top-level fields
            cert_path = halo / "arena" / "D151.json"
            self.assertTrue(cert_path.is_file(), "arena cert should be written")
            cert = json.loads(cert_path.read_text(encoding="utf-8"))
            self.assertEqual(cert["latest_score_id"], "S003")
            self.assertEqual(cert["latest_trajectory_id"], "GT-002")

    def test_arena_json_latest_ids_null_when_dirs_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            (halo / "scores").mkdir()
            (halo / "trajectories").mkdir()
            data = verify(repo, "D151")
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertIsNone(data["latest_score_id"])
            self.assertIsNone(data["latest_trajectory_id"])

    def test_arena_json_latest_ids_null_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = verify(repo, "D151")
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertIsNone(data["latest_score_id"])
            self.assertIsNone(data["latest_trajectory_id"])


if __name__ == "__main__":
    unittest.main()
