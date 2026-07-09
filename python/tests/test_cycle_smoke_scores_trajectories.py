#!/usr/bin/env python3
"""D138: cycle-smoke evidence includes scores_count trajectories_count match.

Does NOT invoke full cycle-smoke (would recurse: smoke → unittest → smoke).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HALO = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_cycle_smoke import build_evidence, write_evidence  # noqa: E402

SCRIPT = HALO / "scripts" / "halo-cycle-smoke.sh"


class TestCycleSmokeScoresTrajectories(unittest.TestCase):
    def _scaffold(self, repo: Path) -> Path:
        halo = repo / ".halo"
        halo.mkdir()
        (halo / "feature-list.json").write_text(
            json.dumps({"version": 1, "features": []}) + "\n",
            encoding="utf-8",
        )
        return halo

    def test_build_evidence_equal_counts_match_true(self) -> None:
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
            data = build_evidence(repo)
            self.assertEqual(data.get("cert"), "GREEN_TEST")
            self.assertEqual(data.get("exit_code"), 0)
            self.assertIn("scores_count", data)
            self.assertIn("trajectories_count", data)
            self.assertIn("scores_trajectories_match", data)
            self.assertIsInstance(data["scores_count"], int)
            self.assertIsInstance(data["trajectories_count"], int)
            self.assertIsInstance(data["scores_trajectories_match"], bool)
            self.assertEqual(data["scores_count"], 2)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertTrue(data["scores_trajectories_match"])

    def test_build_evidence_diverge_match_false(self) -> None:
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
            data = build_evidence(repo)
            self.assertEqual(data["scores_count"], 3)
            self.assertEqual(data["trajectories_count"], 1)
            self.assertFalse(data["scores_trajectories_match"])

    def test_build_evidence_zero_counts_match_true(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = build_evidence(repo)
            self.assertEqual(data["scores_count"], 0)
            self.assertEqual(data["trajectories_count"], 0)
            self.assertTrue(data["scores_trajectories_match"])

    def test_write_evidence_persists_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            path = write_evidence(repo)
            self.assertTrue(path.is_file())
            self.assertEqual(path.name, "D-cycle-smoke-latest.json")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["scores_count"], 0)
            self.assertEqual(data["trajectories_count"], 0)
            self.assertTrue(data["scores_trajectories_match"])
            self.assertEqual(data["cert"], "GREEN_TEST")

    def test_shell_invokes_write_evidence(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("halo_cycle_smoke.py", text)
        self.assertIn("write-evidence", text)


if __name__ == "__main__":
    unittest.main()
