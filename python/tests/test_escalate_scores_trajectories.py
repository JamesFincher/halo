#!/usr/bin/env python3
"""D164: halo escalate JSON includes scores_count trajectories_count scores_trajectories_match."""

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


class TestEscalateScoresTrajectories(unittest.TestCase):
    def _escalate(self, repo: Path, reason: str = "test block") -> dict:
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "halo_escalate.py"),
                "--repo",
                str(repo),
                "--reason",
                reason,
            ],
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
            json.dumps({"version": 1, "features": []}) + "\n",
            encoding="utf-8",
        )
        (halo / "baton.md").write_text("# Baton\n- next: test\n", encoding="utf-8")
        return halo

    def test_escalate_json_has_counts_and_match_when_present(self) -> None:
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
            data = self._escalate(repo)
            self.assertIn("scores_count", data)
            self.assertIn("trajectories_count", data)
            self.assertIn("scores_trajectories_match", data)
            self.assertIsInstance(data["scores_count"], int)
            self.assertIsInstance(data["trajectories_count"], int)
            self.assertIsInstance(data["scores_trajectories_match"], bool)
            self.assertEqual(data["scores_count"], 2)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertIs(data["scores_trajectories_match"], True)
            self.assertTrue(data.get("ok"))
            self.assertEqual(data.get("status"), "ESCALATED")
            # packet JSON on disk also carries counts
            packet = data.get("packet")
            self.assertIsInstance(packet, str)
            packet_path = Path(packet)
            self.assertTrue(packet_path.is_file(), packet)
            body = json.loads(packet_path.read_text(encoding="utf-8"))
            self.assertEqual(body.get("scores_count"), 2)
            self.assertEqual(body.get("trajectories_count"), 2)
            self.assertIs(body.get("scores_trajectories_match"), True)
            # state.escalation carries fields too
            state = json.loads((halo / "state.json").read_text(encoding="utf-8"))
            esc = state.get("escalation") or {}
            self.assertEqual(esc.get("scores_count"), 2)
            self.assertEqual(esc.get("trajectories_count"), 2)
            self.assertIs(esc.get("scores_trajectories_match"), True)

    def test_escalate_json_match_false_when_counts_diverge(self) -> None:
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
            data = self._escalate(repo)
            self.assertEqual(data["scores_count"], 1)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertIs(data["scores_trajectories_match"], False)

    def test_escalate_json_zeros_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = self._escalate(repo)
            self.assertEqual(data["scores_count"], 0)
            self.assertEqual(data["trajectories_count"], 0)
            self.assertIs(data["scores_trajectories_match"], True)


if __name__ == "__main__":
    unittest.main()
