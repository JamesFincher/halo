#!/usr/bin/env python3
"""plan-latest includes latest_score_id alongside scores_count (D118)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_planner import study, write_plan  # noqa: E402


def _minimal_halo(repo: Path) -> Path:
    halo = repo / ".halo"
    halo.mkdir(parents=True, exist_ok=True)
    (halo / "state.json").write_text(
        json.dumps({"status": "ACTIVE", "phase": "build", "autonomous": True}) + "\n",
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
    return halo


class TestPlanLatestScoreId(unittest.TestCase):
    def test_null_when_scores_dir_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _minimal_halo(repo)
            plan = study(repo)
            self.assertIn("latest_score_id", plan)
            self.assertIsNone(plan["latest_score_id"])
            self.assertIn("scores_count", plan)
            self.assertEqual(plan["scores_count"], 0)

    def test_max_s_numeric_prefers_payload_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _minimal_halo(repo)
            scores = halo / "scores"
            scores.mkdir()
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
            plan = study(repo)
            self.assertEqual(plan["latest_score_id"], "S003")
            self.assertEqual(plan["scores_count"], 3)

    def test_write_plan_persists_latest_score_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _minimal_halo(repo)
            scores = halo / "scores"
            scores.mkdir()
            (scores / "S007.json").write_text(
                json.dumps({"id": "S007"}) + "\n", encoding="utf-8"
            )
            plan = study(repo)
            path = write_plan(repo, plan)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["latest_score_id"], "S007")
            self.assertIn("scores_count", loaded)


if __name__ == "__main__":
    unittest.main()
