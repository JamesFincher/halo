#!/usr/bin/env python3
"""D128: progress unit events auto-record scores_count and trajectories_count."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_progress import append, tail  # noqa: E402


def _git_init(repo: Path) -> None:
    subprocess.check_call(["git", "init"], cwd=repo, stdout=subprocess.DEVNULL)
    subprocess.check_call(
        ["git", "config", "user.email", "t@t.com"], cwd=repo, stdout=subprocess.DEVNULL
    )
    subprocess.check_call(
        ["git", "config", "user.name", "t"], cwd=repo, stdout=subprocess.DEVNULL
    )
    (repo / "README").write_text("x\n", encoding="utf-8")
    subprocess.check_call(["git", "add", "README"], cwd=repo, stdout=subprocess.DEVNULL)
    subprocess.check_call(
        ["git", "commit", "-m", "i"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class TestProgressScoresTrajectoriesCount(unittest.TestCase):
    def test_unit_counts_zero_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            append(repo, "unit", {"note": "no scores/traj dirs"})
            rows = tail(repo, n=1)
            self.assertEqual(len(rows), 1)
            self.assertIn("scores_count", rows[0])
            self.assertIn("trajectories_count", rows[0])
            self.assertIsInstance(rows[0]["scores_count"], int)
            self.assertIsInstance(rows[0]["trajectories_count"], int)
            self.assertEqual(rows[0]["scores_count"], 0)
            self.assertEqual(rows[0]["trajectories_count"], 0)

    def test_unit_counts_zero_when_dirs_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            halo = repo / ".halo"
            (halo / "scores").mkdir(parents=True)
            (halo / "trajectories").mkdir(parents=True)
            append(repo, "unit", {"note": "empty dirs"})
            rows = tail(repo, n=1)
            self.assertEqual(rows[0]["scores_count"], 0)
            self.assertEqual(rows[0]["trajectories_count"], 0)

    def test_unit_counts_match_json_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            halo = repo / ".halo"
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir(parents=True)
            traj.mkdir(parents=True)
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            (scores / "S002.json").write_text("{}\n", encoding="utf-8")
            (scores / "notes.txt").write_text("ignore\n", encoding="utf-8")
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-002.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-003.json").write_text("{}\n", encoding="utf-8")
            (traj / "other.json").write_text("{}\n", encoding="utf-8")
            append(repo, "unit", {"note": "counted"})
            rows = tail(repo, n=1)
            self.assertEqual(rows[0]["scores_count"], 2)
            self.assertEqual(rows[0]["trajectories_count"], 3)

    def test_explicit_counts_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            halo = repo / ".halo"
            scores = halo / "scores"
            scores.mkdir(parents=True)
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            append(
                repo,
                "unit",
                {"note": "override", "scores_count": 99, "trajectories_count": 88},
            )
            rows = tail(repo, n=1)
            self.assertEqual(rows[0]["scores_count"], 99)
            self.assertEqual(rows[0]["trajectories_count"], 88)

    def test_non_unit_event_no_forced_counts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            append(repo, "note", {"note": "not a unit"})
            rows = tail(repo, n=1)
            self.assertNotIn("scores_count", rows[0])
            self.assertNotIn("trajectories_count", rows[0])


if __name__ == "__main__":
    unittest.main()
