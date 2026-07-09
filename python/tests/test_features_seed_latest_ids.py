#!/usr/bin/env python3
"""D153: halo features seed JSON includes latest_score_id and latest_trajectory_id."""

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


class TestFeaturesSeedLatestIds(unittest.TestCase):
    def _seed(self, repo: Path, *, force: bool = False) -> dict:
        cmd = [
            sys.executable,
            str(ROOT / "halo_features.py"),
            "seed",
            "--repo",
            str(repo),
        ]
        if force:
            cmd.append("--force")
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            timeout=30,
        )
        self.assertEqual(r.returncode, 0, r.stderr or r.stdout)
        return json.loads(r.stdout)

    def _scaffold(self, repo: Path, *, all_pass: bool = False) -> Path:
        """Default: open backlog so seed is noop (not_all_pass) — pure score surface."""
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
        features = [
            {
                "id": "D001",
                "description": "done fixture",
                "category": "dogfood",
                "passes": True,
            }
        ]
        if not all_pass:
            features.append(
                {
                    "id": "D002",
                    "description": "open fixture",
                    "category": "dogfood",
                    "passes": False,
                }
            )
        (halo / "feature-list.json").write_text(
            json.dumps(
                {
                    "version": 1,
                    "dogfood": True,
                    "dogfood_mode": "compounding",
                    "features": features,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return halo

    def test_seed_json_has_latest_ids_when_present(self) -> None:
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
            data = self._seed(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            # seed does not allocate scores — ids stay pre-existing max
            self.assertEqual(data["latest_score_id"], "S003")
            self.assertEqual(data["latest_trajectory_id"], "GT-010")
            self.assertIn("seeded", data)
            self.assertFalse(data["seeded"])
            # counts surface still present via pass_score_fields
            self.assertIn("scores_count", data)
            self.assertEqual(data["scores_count"], 3)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertFalse(data["scores_trajectories_match"])

    def test_seed_json_latest_ids_null_when_dirs_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            (halo / "scores").mkdir()
            (halo / "trajectories").mkdir()
            data = self._seed(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertIsNone(data["latest_score_id"])
            self.assertIsNone(data["latest_trajectory_id"])
            self.assertEqual(data["scores_count"], 0)
            self.assertEqual(data["trajectories_count"], 0)
            self.assertTrue(data["scores_trajectories_match"])

    def test_seed_json_latest_ids_null_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = self._seed(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertIsNone(data["latest_score_id"])
            self.assertIsNone(data["latest_trajectory_id"])


if __name__ == "__main__":
    unittest.main()
