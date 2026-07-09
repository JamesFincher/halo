#!/usr/bin/env python3
"""D143: halo budget check JSON includes scores_count trajectories_count scores_trajectories_match."""

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


class TestBudgetCheckScoresTrajectories(unittest.TestCase):
    def _check(self, repo: Path) -> dict:
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "halo_budget.py"),
                "--repo",
                str(repo),
                "check",
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            timeout=30,
        )
        self.assertIn(r.returncode, (0, 2), r.stderr or r.stdout)
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
            json.dumps({"active": True, "iteration": 2, "max_iterations": 50}) + "\n",
            encoding="utf-8",
        )
        (halo / "spend.json").write_text(
            json.dumps({"day": "2026-07-09", "day_cycles": 1, "total_cycles": 1})
            + "\n",
            encoding="utf-8",
        )
        (halo / "feature-list.json").write_text(
            json.dumps({"version": 1, "features": []}) + "\n", encoding="utf-8"
        )
        return halo

    def test_check_has_counts_and_match_true_when_equal(self) -> None:
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
            data = self._check(repo)
            self.assertIn("scores_count", data)
            self.assertIn("trajectories_count", data)
            self.assertIn("scores_trajectories_match", data)
            self.assertIsInstance(data["scores_count"], int)
            self.assertIsInstance(data["trajectories_count"], int)
            self.assertIsInstance(data["scores_trajectories_match"], bool)
            self.assertEqual(data["scores_count"], 2)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertTrue(data["scores_trajectories_match"])
            # budget gate fields still present
            self.assertIn("verdict", data)
            self.assertEqual(data["verdict"], "ALLOW")

    def test_check_match_false_when_diverge(self) -> None:
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
            data = self._check(repo)
            self.assertEqual(data["scores_count"], 3)
            self.assertEqual(data["trajectories_count"], 1)
            self.assertFalse(data["scores_trajectories_match"])
            self.assertEqual(data["verdict"], "ALLOW")

    def test_check_zero_counts_match_true(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = self._check(repo)
            self.assertEqual(data["scores_count"], 0)
            self.assertEqual(data["trajectories_count"], 0)
            self.assertTrue(data["scores_trajectories_match"])
            self.assertEqual(data["verdict"], "ALLOW")


if __name__ == "__main__":
    unittest.main()
