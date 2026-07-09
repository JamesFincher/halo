#!/usr/bin/env python3
"""D152: halo features fail JSON includes scores_count trajectories_count scores_trajectories_match."""

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


class TestFeaturesFailScoresTrajectories(unittest.TestCase):
    def _fail(self, repo: Path, feature_id: str = "F1") -> dict:
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "halo_features.py"),
                "fail",
                "--repo",
                str(repo),
                "--id",
                feature_id,
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            timeout=30,
        )
        self.assertEqual(r.returncode, 0, r.stderr or r.stdout)
        return json.loads(r.stdout)

    def _scaffold(self, repo: Path, *, passes: bool = True) -> Path:
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
                            "passes": passes,
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return halo

    def test_fail_json_has_counts_and_match_after_mark(self) -> None:
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
            data = self._fail(repo)
            self.assertIn("scores_count", data)
            self.assertIn("trajectories_count", data)
            self.assertIn("scores_trajectories_match", data)
            self.assertIsInstance(data["scores_count"], int)
            self.assertIsInstance(data["trajectories_count"], int)
            self.assertIsInstance(data["scores_trajectories_match"], bool)
            # fail does not call on_feature_pass — counts stay pre-mark
            self.assertEqual(data["scores_count"], 2)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertTrue(data["scores_trajectories_match"])
            self.assertIn("features", data)
            self.assertEqual(data["version"], 1)

    def test_fail_json_match_false_when_diverge(self) -> None:
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
            data = self._fail(repo)
            # pre 2/1 — fail leaves counts unchanged
            self.assertEqual(data["scores_count"], 2)
            self.assertEqual(data["trajectories_count"], 1)
            self.assertFalse(data["scores_trajectories_match"])

    def test_fail_json_zeros_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = self._fail(repo)
            self.assertEqual(data["scores_count"], 0)
            self.assertEqual(data["trajectories_count"], 0)
            self.assertTrue(data["scores_trajectories_match"])
            self.assertIn("features", data)


if __name__ == "__main__":
    unittest.main()
