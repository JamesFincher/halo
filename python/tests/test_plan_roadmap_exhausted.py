#!/usr/bin/env python3
"""plan-latest roadmap_exhausted flag (D084)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_planner import study  # noqa: E402


class TestRoadmapExhausted(unittest.TestCase):
    def test_flag_true_when_no_new_roadmap(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "state.json").write_text(
                json.dumps(
                    {
                        "status": "ACTIVE",
                        "phase": "build",
                        "autonomous": True,
                        "dogfood": True,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (halo / "loop.json").write_text(
                json.dumps({"active": True, "iteration": 1}) + "\n", encoding="utf-8"
            )
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
            (halo / "compound-seed.json").write_text(
                json.dumps({"last_reason": "no_new_roadmap", "batch": 9}) + "\n",
                encoding="utf-8",
            )
            plan = study(repo)
            self.assertTrue(plan.get("roadmap_exhausted"))

    def test_flag_false_otherwise(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "state.json").write_text(
                json.dumps({"status": "ACTIVE", "phase": "build"}) + "\n", encoding="utf-8"
            )
            (halo / "loop.json").write_text("{}\n", encoding="utf-8")
            (halo / "feature-list.json").write_text(
                json.dumps({"features": []}) + "\n", encoding="utf-8"
            )
            (halo / "compound-seed.json").write_text(
                json.dumps({"last_reason": "seeded"}) + "\n", encoding="utf-8"
            )
            plan = study(repo)
            self.assertFalse(plan.get("roadmap_exhausted"))


if __name__ == "__main__":
    unittest.main()
