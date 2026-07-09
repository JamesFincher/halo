#!/usr/bin/env python3
"""D145: halo doctor JSON report includes scores_count trajectories_count scores_trajectories_match."""

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


class TestDoctorScoresTrajectories(unittest.TestCase):
    def _doctor_json(self, repo: Path) -> dict:
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "halo_doctor.py"),
                "--repo",
                str(repo),
                "--halo-system",
                str(ROOT.parent),
                "--json",
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            timeout=60,
        )
        # doctor may exit 0 or 1 depending on product issues; JSON must still parse
        self.assertIn(r.returncode, (0, 1, 2), r.stderr or r.stdout)
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
            json.dumps({"version": 1, "features": []}) + "\n", encoding="utf-8"
        )
        return halo

    def test_doctor_json_has_counts_and_match_when_present(self) -> None:
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
            data = self._doctor_json(repo)
            self.assertIn("scores_count", data)
            self.assertIn("trajectories_count", data)
            self.assertIn("scores_trajectories_match", data)
            self.assertEqual(data["scores_count"], 2)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertIs(data["scores_trajectories_match"], True)
            # baseline doctor fields still present
            self.assertIn("ok", data)
            self.assertIn("issues", data)

    def test_doctor_json_match_false_when_counts_diverge(self) -> None:
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
            data = self._doctor_json(repo)
            self.assertEqual(data["scores_count"], 1)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertIs(data["scores_trajectories_match"], False)

    def test_doctor_json_zeros_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = self._doctor_json(repo)
            self.assertEqual(data["scores_count"], 0)
            self.assertEqual(data["trajectories_count"], 0)
            self.assertIs(data["scores_trajectories_match"], True)


if __name__ == "__main__":
    unittest.main()
