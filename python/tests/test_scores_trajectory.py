#!/usr/bin/env python3
"""D103–D105: scores, golden trajectory, loop last_head on pass."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_scores import (  # noqa: E402
    on_feature_pass,
    refresh_loop_last_head,
    write_cycle_score,
    write_golden_trajectory,
)


class TestScoresTrajectory(unittest.TestCase):
    def test_score_has_dimensions_and_warm_start(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            with mock.patch("halo_scores._git_head", return_value="abc"):
                path = write_cycle_score(repo, feature_id="D103")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(data["id"].startswith("S"))
            self.assertIn("tool_selection", data)
            self.assertIn("warm_start_directive", data)
            self.assertEqual(data["feature_id"], "D103")

    def test_trajectory_has_steps_and_head(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            with mock.patch("halo_scores._git_head", return_value="deadbeef"):
                path = write_golden_trajectory(repo, feature_id="D104")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(data["id"].startswith("GT-"))
            self.assertIsInstance(data["steps"], list)
            self.assertEqual(data["git_head"], "deadbeef")
            self.assertEqual(data["feature_id"], "D104")

    def test_refresh_last_head(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "loop.json").write_text(
                json.dumps({"active": True, "iteration": 1, "last_head": "old"})
                + "\n",
                encoding="utf-8",
            )
            with mock.patch("halo_scores._git_head", return_value="newhead"):
                r = refresh_loop_last_head(repo)
            self.assertTrue(r.get("ok"))
            loop = json.loads((halo / "loop.json").read_text())
            self.assertEqual(loop["last_head"], "newhead")

    def test_on_feature_pass_writes_all(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "loop.json").write_text(
                json.dumps({"active": True}) + "\n", encoding="utf-8"
            )
            with mock.patch("halo_scores._git_head", return_value="h1"):
                out = on_feature_pass(repo, "D105")
            self.assertIn("score", out)
            self.assertIn("trajectory", out)
            self.assertTrue(out.get("loop", {}).get("ok"))
            self.assertTrue(list((halo / "scores").glob("S*.json")))
            self.assertTrue(list((halo / "trajectories").glob("GT-*.json")))


if __name__ == "__main__":
    unittest.main()
