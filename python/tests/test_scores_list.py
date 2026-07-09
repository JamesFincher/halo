#!/usr/bin/env python3
"""D110: halo scores list CLI prints count and latest id."""

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

from halo_scores import list_scores  # noqa: E402


class TestScoresList(unittest.TestCase):
    def test_list_scores_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            out = list_scores(repo)
            self.assertEqual(out["count"], 0)
            self.assertIsNone(out["latest"])

    def test_list_scores_count_and_latest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            scores = repo / ".halo" / "scores"
            scores.mkdir(parents=True)
            (scores / "S001.json").write_text(
                json.dumps({"id": "S001", "feature_id": "D001"}) + "\n",
                encoding="utf-8",
            )
            (scores / "S003.json").write_text(
                json.dumps({"id": "S003", "feature_id": "D003"}) + "\n",
                encoding="utf-8",
            )
            (scores / "S002.json").write_text(
                json.dumps({"id": "S002", "feature_id": "D002"}) + "\n",
                encoding="utf-8",
            )
            (scores / "notes.txt").write_text("ignore\n", encoding="utf-8")
            out = list_scores(repo)
            self.assertEqual(out["count"], 3)
            self.assertEqual(out["latest"], "S003")

    def test_cli_list_exits_0_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            scores = repo / ".halo" / "scores"
            scores.mkdir(parents=True)
            (scores / "S001.json").write_text(
                json.dumps({"id": "S001"}) + "\n", encoding="utf-8"
            )
            (scores / "S002.json").write_text(
                json.dumps({"id": "S002"}) + "\n", encoding="utf-8"
            )
            r = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "halo_scores.py"),
                    "list",
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
            self.assertEqual(data["latest"], "S002")


if __name__ == "__main__":
    unittest.main()
