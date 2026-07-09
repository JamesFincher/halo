#!/usr/bin/env python3
"""D144: halo budget check JSON includes latest_score_id and latest_trajectory_id."""

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


class TestBudgetCheckLatestIds(unittest.TestCase):
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

    def test_check_has_latest_ids_when_present(self) -> None:
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
            data = self._check(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertEqual(data["latest_score_id"], "S003")
            self.assertEqual(data["latest_trajectory_id"], "GT-010")
            # budget gate + D143 score surface still present
            self.assertIn("verdict", data)
            self.assertEqual(data["verdict"], "ALLOW")
            self.assertIn("scores_count", data)
            self.assertIn("scores_trajectories_match", data)

    def test_check_latest_ids_null_when_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            (halo / "scores").mkdir()
            (halo / "trajectories").mkdir()
            data = self._check(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertIsNone(data["latest_score_id"])
            self.assertIsNone(data["latest_trajectory_id"])
            self.assertEqual(data["verdict"], "ALLOW")

    def test_check_latest_ids_null_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = self._check(repo)
            self.assertIsNone(data["latest_score_id"])
            self.assertIsNone(data["latest_trajectory_id"])
            self.assertEqual(data["verdict"], "ALLOW")


if __name__ == "__main__":
    unittest.main()
