#!/usr/bin/env python3
"""D166: halo commit-unit JSON includes scores_count trajectories_count scores_trajectories_match."""

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


class TestCommitUnitScoresTrajectories(unittest.TestCase):
    def _commit_dry(self, repo: Path, feature_id: str = "D166") -> dict:
        r = subprocess.run(
            [
                sys.executable,
                str(ROOT / "halo_commit.py"),
                "--repo",
                str(repo),
                "--id",
                feature_id,
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env={**os.environ, "PYTHONPATH": str(ROOT)},
            timeout=30,
        )
        self.assertTrue(r.stdout.strip(), r.stderr or "no stdout")
        return json.loads(r.stdout)

    def _git_init(self, repo: Path) -> None:
        subprocess.run(
            ["git", "init"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "test"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        (repo / "README.md").write_text("hello\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
        (repo / "README.md").write_text("hello dirty\n", encoding="utf-8")

    def _scaffold_halo(self, repo: Path) -> Path:
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

    def test_commit_unit_json_has_counts_and_match_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._git_init(repo)
            halo = self._scaffold_halo(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text(json.dumps({"id": "S001"}) + "\n")
            (scores / "S002.json").write_text(json.dumps({"id": "S002"}) + "\n")
            (traj / "GT-001.json").write_text(json.dumps({"id": "GT-001"}) + "\n")
            (traj / "GT-002.json").write_text(json.dumps({"id": "GT-002"}) + "\n")
            data = self._commit_dry(repo)
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
            self.assertTrue(data.get("dry_run"))

    def test_commit_unit_json_match_false_when_counts_diverge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._git_init(repo)
            halo = self._scaffold_halo(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text(json.dumps({"id": "S001"}) + "\n")
            (traj / "GT-001.json").write_text(json.dumps({"id": "GT-001"}) + "\n")
            (traj / "GT-002.json").write_text(json.dumps({"id": "GT-002"}) + "\n")
            data = self._commit_dry(repo)
            self.assertEqual(data["scores_count"], 1)
            self.assertEqual(data["trajectories_count"], 2)
            self.assertIs(data["scores_trajectories_match"], False)

    def test_commit_unit_json_zeros_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._git_init(repo)
            self._scaffold_halo(repo)
            data = self._commit_dry(repo)
            self.assertEqual(data["scores_count"], 0)
            self.assertEqual(data["trajectories_count"], 0)
            self.assertIs(data["scores_trajectories_match"], True)


if __name__ == "__main__":
    unittest.main()
