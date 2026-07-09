#!/usr/bin/env python3
"""features summary includes top-level latest_score_id (D115)."""

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


class TestSummaryLatestScoreId(unittest.TestCase):
    def test_latest_score_id_null_when_missing(self) -> None:
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
            self.assertIn("latest_score_id", sm)
            self.assertIsNone(sm["latest_score_id"])

    def test_latest_score_id_is_max_s_numeric(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            scores = halo / "scores"
            scores.mkdir(parents=True)
            (scores / "S001.json").write_text(
                json.dumps({"id": "S001"}) + "\n", encoding="utf-8"
            )
            (scores / "S003.json").write_text(
                json.dumps({"id": "S003"}) + "\n", encoding="utf-8"
            )
            (scores / "S002.json").write_text(
                json.dumps({"id": "S002"}) + "\n", encoding="utf-8"
            )
            (scores / "notes.txt").write_text("ignore\n", encoding="utf-8")
            (scores / "other.json").write_text("{}\n", encoding="utf-8")
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
            self.assertEqual(sm["latest_score_id"], "S003")
            self.assertIsInstance(sm["latest_score_id"], str)

    def test_latest_score_id_null_when_scores_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            (halo / "scores").mkdir(parents=True)
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
            self.assertIsNone(sm["latest_score_id"])


if __name__ == "__main__":
    unittest.main()
