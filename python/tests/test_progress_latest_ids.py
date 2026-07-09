#!/usr/bin/env python3
"""D134: progress unit events auto-record latest_score_id and latest_trajectory_id."""

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


class TestProgressLatestIds(unittest.TestCase):
    def test_null_when_dirs_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            append(repo, "unit", {"note": "no dirs"})
            rows = tail(repo, n=1)
            self.assertIn("latest_score_id", rows[0])
            self.assertIn("latest_trajectory_id", rows[0])
            self.assertIsNone(rows[0]["latest_score_id"])
            self.assertIsNone(rows[0]["latest_trajectory_id"])

    def test_null_when_dirs_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            halo = repo / ".halo"
            (halo / "scores").mkdir(parents=True)
            (halo / "trajectories").mkdir(parents=True)
            append(repo, "unit", {"note": "empty"})
            rows = tail(repo, n=1)
            self.assertIsNone(rows[0]["latest_score_id"])
            self.assertIsNone(rows[0]["latest_trajectory_id"])

    def test_max_numeric_ids_from_filenames(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            scores = repo / ".halo" / "scores"
            traj = repo / ".halo" / "trajectories"
            scores.mkdir(parents=True)
            traj.mkdir(parents=True)
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            (scores / "S003.json").write_text("{}\n", encoding="utf-8")
            (scores / "S002.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-002.json").write_text("{}\n", encoding="utf-8")
            (traj / "other.json").write_text("{}\n", encoding="utf-8")
            append(repo, "unit", {"note": "max ids"})
            rows = tail(repo, n=1)
            self.assertEqual(rows[0]["latest_score_id"], "S003")
            self.assertEqual(rows[0]["latest_trajectory_id"], "GT-002")

    def test_prefers_payload_id_when_well_formed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            scores = repo / ".halo" / "scores"
            traj = repo / ".halo" / "trajectories"
            scores.mkdir(parents=True)
            traj.mkdir(parents=True)
            (scores / "S010.json").write_text(
                json.dumps({"id": "S010"}) + "\n", encoding="utf-8"
            )
            (traj / "GT-007.json").write_text(
                json.dumps({"id": "GT-007"}) + "\n", encoding="utf-8"
            )
            append(repo, "unit", {"note": "payload ids"})
            rows = tail(repo, n=1)
            self.assertEqual(rows[0]["latest_score_id"], "S010")
            self.assertEqual(rows[0]["latest_trajectory_id"], "GT-007")

    def test_explicit_ids_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            scores = repo / ".halo" / "scores"
            scores.mkdir(parents=True)
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            append(
                repo,
                "unit",
                {
                    "note": "override",
                    "latest_score_id": "S999",
                    "latest_trajectory_id": "GT-999",
                },
            )
            rows = tail(repo, n=1)
            self.assertEqual(rows[0]["latest_score_id"], "S999")
            self.assertEqual(rows[0]["latest_trajectory_id"], "GT-999")

    def test_non_unit_event_no_forced_ids(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            append(repo, "note", {"note": "not a unit"})
            rows = tail(repo, n=1)
            self.assertNotIn("latest_score_id", rows[0])
            self.assertNotIn("latest_trajectory_id", rows[0])


if __name__ == "__main__":
    unittest.main()
