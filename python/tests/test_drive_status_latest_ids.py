#!/usr/bin/env python3
"""D136: drive status JSON features include latest_score_id and latest_trajectory_id."""

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


class TestDriveStatusLatestIds(unittest.TestCase):
    def _status(self, repo: Path) -> dict:
        r = subprocess.run(
            [sys.executable, str(ROOT / "halo_drive.py"), "--repo", str(repo), "status"],
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
            json.dumps({"status": "ACTIVE", "phase": "build", "autonomous": True})
            + "\n",
            encoding="utf-8",
        )
        (halo / "loop.json").write_text(
            json.dumps({"active": True, "iteration": 1, "max_iterations": 50}) + "\n",
            encoding="utf-8",
        )
        (halo / "feature-list.json").write_text(
            json.dumps({"version": 1, "features": []}) + "\n", encoding="utf-8"
        )
        return halo

    def test_features_has_latest_ids_when_present(self) -> None:
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
            data = self._status(repo)
            feats = data["features"]
            self.assertIn("latest_score_id", feats)
            self.assertIn("latest_trajectory_id", feats)
            self.assertEqual(feats["latest_score_id"], "S003")
            self.assertEqual(feats["latest_trajectory_id"], "GT-010")

    def test_features_latest_ids_null_when_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = self._status(repo)
            feats = data["features"]
            self.assertIn("latest_score_id", feats)
            self.assertIn("latest_trajectory_id", feats)
            self.assertIsNone(feats["latest_score_id"])
            self.assertIsNone(feats["latest_trajectory_id"])

    def test_features_latest_ids_null_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            # no scores/ or trajectories/ dirs
            data = self._status(repo)
            feats = data["features"]
            self.assertIsNone(feats["latest_score_id"])
            self.assertIsNone(feats["latest_trajectory_id"])
            self.assertTrue(halo.exists())


if __name__ == "__main__":
    unittest.main()
