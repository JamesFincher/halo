#!/usr/bin/env python3
"""feature summary next includes requires_code (D098)."""

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


class TestSummaryRequiresCode(unittest.TestCase):
    def test_next_carries_requires_code(self) -> None:
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
                            },
                            {
                                "id": "D002",
                                "description": "open code unit",
                                "passes": False,
                                "requires_code": True,
                                "steps": ["a"],
                            },
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (halo / "state.json").write_text(
                json.dumps({"status": "ACTIVE", "phase": "build"}) + "\n",
                encoding="utf-8",
            )
            sm = summary(repo, compound=False)
            self.assertIsNotNone(sm["next"])
            self.assertEqual(sm["next"]["id"], "D002")
            self.assertTrue(sm["next"]["requires_code"])
            self.assertIn("requires_code", sm["next"])

    def test_next_null_when_all_pass(self) -> None:
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
            self.assertTrue(sm["all_pass"])
            self.assertIsNone(sm["next"])


if __name__ == "__main__":
    unittest.main()
