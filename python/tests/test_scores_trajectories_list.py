#!/usr/bin/env python3
"""D113: halo scores trajectories list CLI prints count and latest id."""

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

from halo_scores import list_trajectories  # noqa: E402


class TestScoresTrajectoriesList(unittest.TestCase):
    def test_list_trajectories_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            out = list_trajectories(repo)
            self.assertEqual(out["count"], 0)
            self.assertIsNone(out["latest"])

    def test_list_trajectories_count_and_latest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            traj = repo / ".halo" / "trajectories"
            traj.mkdir(parents=True)
            (traj / "GT-001.json").write_text(
                json.dumps({"id": "GT-001", "feature_id": "D001"}) + "\n",
                encoding="utf-8",
            )
            (traj / "GT-003.json").write_text(
                json.dumps({"id": "GT-003", "feature_id": "D003"}) + "\n",
                encoding="utf-8",
            )
            (traj / "GT-002.json").write_text(
                json.dumps({"id": "GT-002", "feature_id": "D002"}) + "\n",
                encoding="utf-8",
            )
            (traj / "notes.txt").write_text("ignore\n", encoding="utf-8")
            (traj / "other.json").write_text("{}\n", encoding="utf-8")
            out = list_trajectories(repo)
            self.assertEqual(out["count"], 3)
            self.assertEqual(out["latest"], "GT-003")

    def test_cli_trajectories_exits_0_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            traj = repo / ".halo" / "trajectories"
            traj.mkdir(parents=True)
            (traj / "GT-001.json").write_text(
                json.dumps({"id": "GT-001"}) + "\n", encoding="utf-8"
            )
            (traj / "GT-002.json").write_text(
                json.dumps({"id": "GT-002"}) + "\n", encoding="utf-8"
            )
            r = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "halo_scores.py"),
                    "trajectories",
                    "--repo",
                    str(repo),
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertIn("count", data)
            self.assertIn("latest", data)
            self.assertEqual(data["count"], 2)
            self.assertEqual(data["latest"], "GT-002")


if __name__ == "__main__":
    unittest.main()
