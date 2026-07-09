#!/usr/bin/env python3
"""compound seed --force refuses when open backlog (D090)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_features import maybe_compound_seed  # noqa: E402


class TestSeedForceBacklog(unittest.TestCase):
    def test_force_does_not_seed_over_pending(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "state.json").write_text(
                json.dumps(
                    {
                        "dogfood": True,
                        "dogfood_mode": "compounding",
                        "status": "ACTIVE",
                        "phase": "build",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (halo / "feature-list.json").write_text(
                json.dumps(
                    {
                        "dogfood": True,
                        "features": [
                            {
                                "id": "D001",
                                "description": "open unit",
                                "passes": False,
                                "requires_code": True,
                                "steps": ["a"],
                            }
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            r = maybe_compound_seed(repo, force=True)
            self.assertFalse(r.get("seeded"))
            self.assertEqual(r.get("reason"), "not_all_pass")


if __name__ == "__main__":
    unittest.main()
