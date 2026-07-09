#!/usr/bin/env python3
"""D157: Compounding approved cycle writes .halo/scores/SNNN.json six-dimension stub."""

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

from halo_scores import SIX_DIMENSIONS, write_cycle_score  # noqa: E402


class TestScoresSixDimensionStub(unittest.TestCase):
    def test_score_has_tool_selection_and_warm_start(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            with mock.patch("halo_scores._git_head", return_value="abc123"):
                path = write_cycle_score(
                    repo, feature_id="D157", note="compound stub note"
                )
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("tool_selection", data)
            self.assertIn("warm_start_directive", data)
            self.assertEqual(data["warm_start_directive"], "compound stub note")
            self.assertIsInstance(data["tool_selection"], (int, float))

    def test_score_id_sequential_s_matches_path_stem(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            with mock.patch("halo_scores._git_head", return_value="deadbeef"):
                p1 = write_cycle_score(repo, feature_id="D157")
                p2 = write_cycle_score(repo, feature_id="D157")
            d1 = json.loads(p1.read_text(encoding="utf-8"))
            d2 = json.loads(p2.read_text(encoding="utf-8"))
            self.assertEqual(d1["id"], p1.stem)
            self.assertEqual(d2["id"], p2.stem)
            self.assertRegex(d1["id"], r"^S\d{3}$")
            self.assertRegex(d2["id"], r"^S\d{3}$")
            self.assertEqual(d1["id"], "S001")
            self.assertEqual(d2["id"], "S002")
            self.assertEqual(d1["feature_id"], "D157")

    def test_all_six_dimensions_present_as_unit_interval_floats(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            with mock.patch("halo_scores._git_head", return_value="h"):
                path = write_cycle_score(repo, feature_id="D157")
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(len(SIX_DIMENSIONS), 6)
            for dim in SIX_DIMENSIONS:
                self.assertIn(dim, data, dim)
                val = float(data[dim])
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 1.0)
            # Nested dimensions map mirrors top-level contract (D157)
            dims = data.get("dimensions")
            self.assertIsInstance(dims, dict)
            for dim in SIX_DIMENSIONS:
                self.assertIn(dim, dims)
                self.assertEqual(float(dims[dim]), float(data[dim]))
            self.assertEqual(data.get("schema_version"), 1)


if __name__ == "__main__":
    unittest.main()
