#!/usr/bin/env python3
"""D165: halo commit-unit JSON includes latest_score_id and latest_trajectory_id."""

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


class TestCommitUnitLatestIds(unittest.TestCase):
    def _commit_dry(self, repo: Path, feature_id: str = "D165") -> dict:
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
        # dry-run may be ok=false if nothing to commit — still parse JSON
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
        # one tracked factory file so dry-run has safe paths after touch dirty
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

    def test_commit_unit_json_has_latest_ids_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._git_init(repo)
            halo = self._scaffold_halo(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text(json.dumps({"id": "S001"}) + "\n")
            (scores / "S003.json").write_text(json.dumps({"id": "S003"}) + "\n")
            (scores / "S002.json").write_text(json.dumps({"id": "S002"}) + "\n")
            (traj / "GT-001.json").write_text(json.dumps({"id": "GT-001"}) + "\n")
            (traj / "GT-010.json").write_text(json.dumps({"id": "GT-010"}) + "\n")
            data = self._commit_dry(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertEqual(data["latest_score_id"], "S003")
            self.assertEqual(data["latest_trajectory_id"], "GT-010")
            self.assertTrue(data.get("ok"))
            self.assertTrue(data.get("dry_run"))

    def test_commit_unit_json_latest_ids_null_when_dirs_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._git_init(repo)
            halo = self._scaffold_halo(repo)
            (halo / "scores").mkdir()
            (halo / "trajectories").mkdir()
            data = self._commit_dry(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertIsNone(data["latest_score_id"])
            self.assertIsNone(data["latest_trajectory_id"])

    def test_commit_unit_json_latest_ids_null_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._git_init(repo)
            self._scaffold_halo(repo)
            data = self._commit_dry(repo)
            self.assertIn("latest_score_id", data)
            self.assertIn("latest_trajectory_id", data)
            self.assertIsNone(data["latest_score_id"])
            self.assertIsNone(data["latest_trajectory_id"])


if __name__ == "__main__":
    unittest.main()
