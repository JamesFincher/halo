#!/usr/bin/env python3
"""D171: halo evidence check JSON includes latest_score_id and latest_trajectory_id."""

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


class TestEvidenceCheckLatestIds(unittest.TestCase):
    def _check(self, repo: Path, evidence: Path) -> dict:
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "halo_evidence.py"),
                "--repo",
                str(repo),
                "--check",
                str(evidence),
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            timeout=30,
        )
        self.assertTrue(r.stdout.strip(), r.stderr or "no stdout")
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
        ev = halo / "evidence"
        ev.mkdir()
        good = ev / "D171-green.json"
        good.write_text(
            json.dumps({"cert": "GREEN_TEST", "ok": True, "exit_code": 0}) + "\n",
            encoding="utf-8",
        )
        return halo

    def test_check_json_has_latest_ids_when_present(self) -> None:
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
            evidence = halo / "evidence" / "D171-green.json"
            data = self._check(repo, evidence)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertEqual(data["latest_score_id"], "S003")
            self.assertEqual(data["latest_trajectory_id"], "GT-010")
            self.assertTrue(data.get("ok"))

    def test_check_json_latest_ids_null_when_dirs_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            (halo / "scores").mkdir()
            (halo / "trajectories").mkdir()
            evidence = halo / "evidence" / "D171-green.json"
            data = self._check(repo, evidence)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertIsNone(data["latest_score_id"])
            self.assertIsNone(data["latest_trajectory_id"])

    def test_check_json_latest_ids_null_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            evidence = halo / "evidence" / "D171-green.json"
            data = self._check(repo, evidence)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertIsNone(data["latest_score_id"])
            self.assertIsNone(data["latest_trajectory_id"])


if __name__ == "__main__":
    unittest.main()
