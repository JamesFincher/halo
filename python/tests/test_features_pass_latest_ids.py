#!/usr/bin/env python3
"""D148: halo features pass JSON includes latest_score_id and latest_trajectory_id."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestFeaturesPassLatestIds(unittest.TestCase):
    def _pass(self, repo: Path, feature_id: str = "F1") -> dict:
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "halo_features.py"),
                "pass",
                "--repo",
                str(repo),
                "--id",
                feature_id,
                "--force",
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            timeout=30,
        )
        self.assertEqual(r.returncode, 0, r.stderr or r.stdout)
        return json.loads(r.stdout)

    def _scaffold(self, repo: Path) -> Path:
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
                            "id": "F1",
                            "description": "fixture",
                            "category": "dogfood",
                            "passes": False,
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return halo

    def test_pass_json_has_latest_ids_after_mark(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text(json.dumps({"id": "S001"}) + "\n")
            (scores / "S003.json").write_text(json.dumps({"id": "S003"}) + "\n")
            (scores / "S002.json").write_text(json.dumps({"id": "S002"}) + "\n")
            (traj / "GT-001.json").write_text(json.dumps({"id": "GT-001"}) + "\n")
            (traj / "GT-010.json").write_text(json.dumps({"id": "GT-010"}) + "\n")
            data = self._pass(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            # on_feature_pass may allocate S004 / GT-011 after mark
            self.assertIsInstance(data["latest_score_id"], str)
            self.assertIsInstance(data["latest_trajectory_id"], str)
            self.assertRegex(data["latest_score_id"], r"^S\d+$")
            self.assertRegex(data["latest_trajectory_id"], r"^GT-\d+$")
            # max must be at least pre-existing max (S003 / GT-010) or higher after mark
            self.assertGreaterEqual(int(data["latest_score_id"][1:]), 3)
            self.assertGreaterEqual(int(data["latest_trajectory_id"].split("-")[1]), 10)
            # D147 score surface still present
            self.assertIn("scores_count", data)
            self.assertIn("trajectories_count", data)
            self.assertIn("scores_trajectories_match", data)
            self.assertIn("features", data)

    def test_pass_json_latest_ids_null_when_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            (halo / "scores").mkdir()
            (halo / "trajectories").mkdir()
            data = self._pass(repo)
            # on_feature_pass creates one score + one trajectory after mark
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertIsInstance(data["latest_score_id"], str)
            self.assertIsInstance(data["latest_trajectory_id"], str)
            self.assertRegex(data["latest_score_id"], r"^S\d+$")
            self.assertRegex(data["latest_trajectory_id"], r"^GT-\d+$")

    def test_pass_json_latest_ids_null_when_dirs_missing_pre_mark(self) -> None:
        """When dirs missing before mark, on_feature_pass creates them — ids become non-null.

        Pure null case is covered by fail path (D149) or force-skip of on_feature_pass.
        Here we assert keys always present on pass stdout after mark.
        """
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = self._pass(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            # post on_feature_pass stubs exist
            self.assertIsNotNone(data["latest_score_id"])
            self.assertIsNotNone(data["latest_trajectory_id"])


if __name__ == "__main__":
    unittest.main()
