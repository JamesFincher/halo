#!/usr/bin/env python3
"""D176: halo progress tail JSON envelope includes scores_count/trajectories_count/match."""

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


class TestProgressTailScoresTrajectories(unittest.TestCase):
    def _tail(self, repo: Path, n: int = 15) -> dict:
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "halo_progress.py"),
                "tail",
                "--repo",
                str(repo),
                "-n",
                str(n),
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            timeout=30,
        )
        self.assertEqual(r.returncode, 0, r.stderr or r.stdout)
        self.assertTrue(r.stdout.strip(), r.stderr or "no stdout")
        data = json.loads(r.stdout)
        self.assertIsInstance(data, dict, "tail stdout must be JSON object envelope")
        return data

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
        return halo

    def test_tail_envelope_has_events_counts_and_match(self) -> None:
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
            # seed one progress row so events is non-empty
            (halo / "progress.jsonl").write_text(
                json.dumps({"at": "2026-01-01T00:00:00Z", "event": "unit", "note": "seed"})
                + "\n",
                encoding="utf-8",
            )
            data = self._tail(repo)
            self.assertIn("events", data)
            self.assertIsInstance(data["events"], list)
            self.assertEqual(len(data["events"]), 1)
            self.assertIn("scores_count", data)
            self.assertIn("trajectories_count", data)
            self.assertIn("scores_trajectories_match", data)
            self.assertIsInstance(data["scores_count"], int)
            self.assertIsInstance(data["trajectories_count"], int)
            self.assertIsInstance(data["scores_trajectories_match"], bool)
            self.assertEqual(data["scores_count"], 2)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertIs(data["scores_trajectories_match"], True)

    def test_tail_envelope_match_false_when_diverge(self) -> None:
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
            data = self._tail(repo)
            self.assertEqual(data["scores_count"], 1)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertIs(data["scores_trajectories_match"], False)
            self.assertIsInstance(data["events"], list)

    def test_tail_envelope_zero_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._scaffold(repo)
            data = self._tail(repo)
            self.assertEqual(data["scores_count"], 0)
            self.assertEqual(data["trajectories_count"], 0)
            self.assertIs(data["scores_trajectories_match"], True)
            self.assertIsInstance(data["events"], list)
            self.assertEqual(data["events"], [])


if __name__ == "__main__":
    unittest.main()
