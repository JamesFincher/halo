#!/usr/bin/env python3
"""features summary includes top-level scores_count (D109)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_features import summary  # noqa: E402


class TestSummaryScoresCount(unittest.TestCase):
    def test_scores_count_zero_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "feature-list.json").write_text(
                json.dumps(
                    {
                        "features": [
                            {
                                "id": "D001",
                                "description": "done",
                                "passes": True,
                                "steps": [],
                            }
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            sm = summary(repo, compound=False)
            self.assertIn("scores_count", sm)
            self.assertEqual(sm["scores_count"], 0)
            self.assertIsInstance(sm["scores_count"], int)

    def test_scores_count_matches_json_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            scores = halo / "scores"
            scores.mkdir(parents=True)
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            (scores / "S002.json").write_text("{}\n", encoding="utf-8")
            (scores / "notes.txt").write_text("ignore\n", encoding="utf-8")
            (halo / "feature-list.json").write_text(
                json.dumps(
                    {
                        "features": [
                            {
                                "id": "D001",
                                "description": "open",
                                "passes": False,
                                "requires_code": True,
                                "steps": ["a"],
                            }
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            sm = summary(repo, compound=False)
            self.assertEqual(sm["scores_count"], 2)
            self.assertTrue(sm["next"]["requires_code"])


if __name__ == "__main__":
    unittest.main()
