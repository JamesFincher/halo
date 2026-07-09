#!/usr/bin/env python3
"""D132: halo handoff writes scores_count, trajectories_count, scores_trajectories_match."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HALO = ROOT / "scripts" / "halo"


class TestHandoffScoresTrajectories(unittest.TestCase):
    def _run_handoff(self, repo: Path) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            "HALO_SYSTEM": str(ROOT),
            "PYTHONPATH": str(ROOT / "python"),
        }
        return subprocess.run(
            ["bash", str(HALO), "handoff", str(repo)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

    def _state(self, **extra: object) -> str:
        base = {
            "product_name": "T",
            "status": "ACTIVE",
            "phase": "build",
            "autonomous": True,
            "spec_status": "locked",
            "dogfood_mode": "compounding",
        }
        base.update(extra)
        return json.dumps(base) + "\n"

    def test_handoff_writes_counts_and_match_true(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir(parents=True)
            traj.mkdir(parents=True)
            (halo / "state.json").write_text(self._state(), encoding="utf-8")
            (halo / "feature-list.json").write_text(
                json.dumps({"version": 1, "features": []}) + "\n", encoding="utf-8"
            )
            (scores / "S001.json").write_text(
                json.dumps({"id": "S001"}) + "\n", encoding="utf-8"
            )
            (scores / "S002.json").write_text(
                json.dumps({"id": "S002"}) + "\n", encoding="utf-8"
            )
            (traj / "GT-001.json").write_text(
                json.dumps({"id": "GT-001"}) + "\n", encoding="utf-8"
            )
            (traj / "GT-002.json").write_text(
                json.dumps({"id": "GT-002"}) + "\n", encoding="utf-8"
            )
            r = self._run_handoff(repo)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            text = (halo / "handoff.md").read_text(encoding="utf-8")
            self.assertIn("scores_count: 2", text)
            self.assertIn("trajectories_count: 2", text)
            self.assertIn("scores_trajectories_match: true", text)

    def test_handoff_writes_match_false_when_diverge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir(parents=True)
            traj.mkdir(parents=True)
            (halo / "state.json").write_text(self._state(), encoding="utf-8")
            (halo / "feature-list.json").write_text(
                json.dumps({"version": 1, "features": []}) + "\n", encoding="utf-8"
            )
            (scores / "S001.json").write_text(
                json.dumps({"id": "S001"}) + "\n", encoding="utf-8"
            )
            (scores / "S002.json").write_text(
                json.dumps({"id": "S002"}) + "\n", encoding="utf-8"
            )
            (scores / "S003.json").write_text(
                json.dumps({"id": "S003"}) + "\n", encoding="utf-8"
            )
            (traj / "GT-001.json").write_text(
                json.dumps({"id": "GT-001"}) + "\n", encoding="utf-8"
            )
            r = self._run_handoff(repo)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            text = (halo / "handoff.md").read_text(encoding="utf-8")
            self.assertIn("scores_count: 3", text)
            self.assertIn("trajectories_count: 1", text)
            self.assertIn("scores_trajectories_match: false", text)

    def test_handoff_writes_zero_counts_and_match_true(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "state.json").write_text(self._state(), encoding="utf-8")
            (halo / "feature-list.json").write_text(
                json.dumps({"version": 1, "features": []}) + "\n", encoding="utf-8"
            )
            r = self._run_handoff(repo)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            text = (halo / "handoff.md").read_text(encoding="utf-8")
            self.assertIn("scores_count: 0", text)
            self.assertIn("trajectories_count: 0", text)
            self.assertIn("scores_trajectories_match: true", text)


if __name__ == "__main__":
    unittest.main()
