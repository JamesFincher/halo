#!/usr/bin/env python3
"""D131: progress unit events auto-record scores_trajectories_match."""

from __future__ import annotations

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


class TestProgressScoresTrajectoriesMatch(unittest.TestCase):
    def test_match_true_when_both_zero_missing_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            append(repo, "unit", {"note": "no dirs"})
            rows = tail(repo, n=1)
            self.assertIn("scores_trajectories_match", rows[0])
            self.assertIsInstance(rows[0]["scores_trajectories_match"], bool)
            self.assertEqual(rows[0]["scores_count"], 0)
            self.assertEqual(rows[0]["trajectories_count"], 0)
            self.assertTrue(rows[0]["scores_trajectories_match"])

    def test_match_true_when_counts_equal(self) -> None:
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
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-002.json").write_text("{}\n", encoding="utf-8")
            append(repo, "unit", {"note": "equal"})
            rows = tail(repo, n=1)
            self.assertEqual(rows[0]["scores_count"], 2)
            self.assertEqual(rows[0]["trajectories_count"], 2)
            self.assertTrue(rows[0]["scores_trajectories_match"])

    def test_match_false_when_counts_unequal(self) -> None:
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
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            append(repo, "unit", {"note": "diverge"})
            rows = tail(repo, n=1)
            self.assertEqual(rows[0]["scores_count"], 2)
            self.assertEqual(rows[0]["trajectories_count"], 1)
            self.assertFalse(rows[0]["scores_trajectories_match"])

    def test_explicit_match_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            append(
                repo,
                "unit",
                {
                    "note": "override",
                    "scores_count": 1,
                    "trajectories_count": 1,
                    "scores_trajectories_match": False,
                },
            )
            rows = tail(repo, n=1)
            self.assertFalse(rows[0]["scores_trajectories_match"])

    def test_match_uses_final_counts_after_override(self) -> None:
        """When only counts overridden, match derives from those final values."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            append(
                repo,
                "unit",
                {"note": "count override", "scores_count": 5, "trajectories_count": 2},
            )
            rows = tail(repo, n=1)
            self.assertEqual(rows[0]["scores_count"], 5)
            self.assertEqual(rows[0]["trajectories_count"], 2)
            self.assertFalse(rows[0]["scores_trajectories_match"])

    def test_non_unit_event_no_forced_match(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            append(repo, "note", {"note": "not a unit"})
            rows = tail(repo, n=1)
            self.assertNotIn("scores_trajectories_match", rows[0])


if __name__ == "__main__":
    unittest.main()
