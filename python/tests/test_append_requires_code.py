#!/usr/bin/env python3
"""append_features must preserve requires_code for dogfood FILE_DIFF gate."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_features import append_features, load_list  # noqa: E402


class TestAppendRequiresCode(unittest.TestCase):
    def test_preserves_requires_code(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "feature-list.json").write_text(
                json.dumps({"version": 1, "features": []}) + "\n", encoding="utf-8"
            )
            append_features(
                repo,
                [
                    {
                        "id": "D999",
                        "description": "unit",
                        "category": "dogfood",
                        "requires_code": True,
                        "steps": ["a"],
                        "milestone": "M-test",
                    }
                ],
            )
            data = load_list(repo)
            row = data["features"][0]
            self.assertEqual(row["id"], "D999")
            self.assertTrue(row.get("requires_code"))


if __name__ == "__main__":
    unittest.main()
