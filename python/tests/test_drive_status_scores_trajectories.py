#!/usr/bin/env python3
"""D135: drive status JSON features include scores/trajectories counts + match."""

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


class TestDriveStatusScoresTrajectories(unittest.TestCase):
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

    def test_features_has_counts_and_match_true_when_equal(self) -> None:
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
            data = self._status(repo)
            feats = data["features"]
            self.assertIn("scores_count", feats)
            self.assertIn("trajectories_count", feats)
            self.assertIn("scores_trajectories_match", feats)
            self.assertIsInstance(feats["scores_count"], int)
            self.assertIsInstance(feats["trajectories_count"], int)
            self.assertIsInstance(feats["scores_trajectories_match"], bool)
            self.assertEqual(feats["scores_count"], 2)
            self.assertEqual(feats["trajectories_count"], 2)
            self.assertTrue(feats["scores_trajectories_match"])

    def test_features_match_false_when_diverge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text(json.dumps({"id": "S001"}) + "\n")
            (scores / "S002.json").write_text(json.dumps({"id": "S002"}) + "\n")
            (scores / "S003.json").write_text(json.dumps({"id": "S003"}) + "\n")
            (traj / "GT-001.json").write_text(json.dumps({"id": "GT-001"}) + "\n")
            data = self._status(repo)
            feats = data["features"]
            self.assertEqual(feats["scores_count"], 3)
            self.assertEqual(feats["trajectories_count"], 1)
            self.assertFalse(feats["scores_trajectories_match"])

    def test_features_zero_counts_match_true(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = self._status(repo)
            feats = data["features"]
            self.assertEqual(feats["scores_count"], 0)
            self.assertEqual(feats["trajectories_count"], 0)
            self.assertTrue(feats["scores_trajectories_match"])


if __name__ == "__main__":
    unittest.main()
