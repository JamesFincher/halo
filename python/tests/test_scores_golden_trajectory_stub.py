#!/usr/bin/env python3
"""D158: Compounding approved cycle records golden trajectory GT stub."""

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
    GOLDEN_TRAJECTORY_SIGNATURE,
    GOLDEN_TRAJECTORY_STEPS,
    write_golden_trajectory,
)


class TestScoresGoldenTrajectoryStub(unittest.TestCase):
    def test_trajectory_has_steps_git_head_and_feature_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            with mock.patch("halo_scores._git_head", return_value="abc123"):
                path = write_golden_trajectory(repo, feature_id="D158")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIsInstance(data["steps"], list)
            self.assertGreaterEqual(len(data["steps"]), 1)
            self.assertEqual(data["git_head"], "abc123")
            self.assertEqual(data["feature_id"], "D158")
            self.assertTrue(path.name.startswith("GT-"))
            self.assertTrue(path.name.endswith(".json"))

    def test_trajectory_id_sequential_gt_matches_path_stem(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            with mock.patch("halo_scores._git_head", return_value="deadbeef"):
                p1 = write_golden_trajectory(repo, feature_id="D158")
                p2 = write_golden_trajectory(repo, feature_id="D158")
            d1 = json.loads(p1.read_text(encoding="utf-8"))
            d2 = json.loads(p2.read_text(encoding="utf-8"))
            self.assertEqual(d1["id"], p1.stem)
            self.assertEqual(d2["id"], p2.stem)
            self.assertRegex(d1["id"], r"^GT-\d{3}$")
            self.assertRegex(d2["id"], r"^GT-\d{3}$")
            self.assertEqual(d1["id"], "GT-001")
            self.assertEqual(d2["id"], "GT-002")
            self.assertEqual(d1["feature_id"], "D158")

    def test_default_steps_and_schema_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            with mock.patch("halo_scores._git_head", return_value="h"):
                path = write_golden_trajectory(repo, feature_id="D158")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(GOLDEN_TRAJECTORY_STEPS), 5)
            self.assertEqual(data["steps"], list(GOLDEN_TRAJECTORY_STEPS))
            for step in data["steps"]:
                self.assertIsInstance(step, str)
                self.assertTrue(step.strip())
            self.assertEqual(data.get("schema_version"), 1)
            self.assertEqual(data.get("signature"), GOLDEN_TRAJECTORY_SIGNATURE)
            # Custom steps override defaults
            with mock.patch("halo_scores._git_head", return_value="h2"):
                custom = write_golden_trajectory(
                    repo, feature_id="D158", steps=["a", "b"]
                )
            cdata = json.loads(custom.read_text(encoding="utf-8"))
            self.assertEqual(cdata["steps"], ["a", "b"])
            self.assertEqual(cdata.get("schema_version"), 1)


if __name__ == "__main__":
    unittest.main()
