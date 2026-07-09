#!/usr/bin/env python3
"""D139: cycle-smoke evidence includes latest_score_id and latest_trajectory_id.

Does NOT invoke full cycle-smoke (would recurse: smoke → unittest → smoke).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_cycle_smoke import build_evidence, write_evidence  # noqa: E402


class TestCycleSmokeLatestIds(unittest.TestCase):
    def _scaffold(self, repo: Path) -> Path:
        halo = repo / ".halo"
        halo.mkdir()
        (halo / "feature-list.json").write_text(
            json.dumps({"version": 1, "features": []}) + "\n",
            encoding="utf-8",
        )
        return halo

    def test_build_evidence_latest_ids_when_present(self) -> None:
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
            data = build_evidence(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertEqual(data["latest_score_id"], "S003")
            self.assertEqual(data["latest_trajectory_id"], "GT-010")
            # counts still present (parity with D138)
            self.assertEqual(data["scores_count"], 3)
            self.assertEqual(data["trajectories_count"], 2)

    def test_build_evidence_latest_ids_null_when_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            (halo / "scores").mkdir()
            (halo / "trajectories").mkdir()
            data = build_evidence(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertIsNone(data["latest_score_id"])
            self.assertIsNone(data["latest_trajectory_id"])

    def test_build_evidence_latest_ids_null_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = build_evidence(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertIsNone(data["latest_score_id"])
            self.assertIsNone(data["latest_trajectory_id"])

    def test_write_evidence_persists_latest_ids(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = self._scaffold(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S007.json").write_text(json.dumps({"id": "S007"}) + "\n")
            (traj / "GT-007.json").write_text(json.dumps({"id": "GT-007"}) + "\n")
            path = write_evidence(repo)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["latest_score_id"], "S007")
            self.assertEqual(data["latest_trajectory_id"], "GT-007")
            self.assertEqual(data["cert"], "GREEN_TEST")


if __name__ == "__main__":
    unittest.main()
