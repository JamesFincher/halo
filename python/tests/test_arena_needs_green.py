#!/usr/bin/env python3
"""Arena refuses APPROVED without GREEN evidence (D086)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_arena import verify  # noqa: E402


class TestArenaNeedsGreen(unittest.TestCase):
    def test_missing_green_not_approved(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "feature-list.json").write_text(
                json.dumps(
                    {
                        "features": [
                            {
                                "id": "D999",
                                "description": "x",
                                "passes": False,
                                "steps": ["a"],
                            }
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (halo / "evidence").mkdir()
            report = verify(repo, "D999")
            self.assertNotEqual(report.get("verdict"), "APPROVED")
            self.assertIn(report.get("verdict"), ("REJECTED", "NEEDS_REVISION"))


if __name__ == "__main__":
    unittest.main()
