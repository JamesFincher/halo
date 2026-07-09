#!/usr/bin/env python3
"""D159: halo plan surfaces scores_missing warn when scores dir empty under compounding."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_planner import _recommend, study, write_plan  # noqa: E402


def _halo_all_pass(
    repo: Path,
    *,
    dogfood: bool = True,
    n_scores: int = 0,
    create_scores_dir: bool = True,
) -> Path:
    halo = repo / ".halo"
    halo.mkdir(parents=True, exist_ok=True)
    state: dict = {
        "status": "ACTIVE",
        "phase": "build",
        "autonomous": True,
    }
    if dogfood:
        state["dogfood"] = True
        state["dogfood_mode"] = "compounding"
    (halo / "state.json").write_text(json.dumps(state) + "\n", encoding="utf-8")
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
    if create_scores_dir or n_scores > 0:
        scores = halo / "scores"
        scores.mkdir(parents=True, exist_ok=True)
        for i in range(1, n_scores + 1):
            (scores / f"S{i:03d}.json").write_text("{}\n", encoding="utf-8")
    return halo


class TestPlannerScoresMissing(unittest.TestCase):
    def test_study_scores_count_int_and_missing_when_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _halo_all_pass(repo, dogfood=True, n_scores=0)
            plan = study(repo)
            self.assertIn("scores_count", plan)
            self.assertIsInstance(plan["scores_count"], int)
            self.assertEqual(plan["scores_count"], 0)
            self.assertIn("scores_missing", plan)
            self.assertIsInstance(plan["scores_missing"], bool)
            self.assertTrue(plan["scores_missing"])

    def test_recommend_mentions_scores_when_empty_compounding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            rec = _recommend(
                repo,
                {"dogfood": True, "dogfood_mode": "compounding", "status": "ACTIVE"},
                {"all_pass": True, "next": None},
                [],
                scores_count=0,
                trajectories_count=0,
            )
            self.assertIn("scores", rec.lower())
            self.assertIn("scores_missing", rec)

    def test_study_recommendation_when_empty_compounding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _halo_all_pass(repo, dogfood=True, n_scores=0)
            plan = study(repo)
            self.assertTrue(plan["scores_missing"])
            self.assertIn("scores_missing", plan["recommendation"])
            self.assertIn("scores", plan["recommendation"].lower())

    def test_skip_when_not_dogfood(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            rec = _recommend(
                repo,
                {"dogfood": False, "status": "ACTIVE"},
                {"all_pass": True, "next": None},
                [],
                scores_count=0,
                trajectories_count=0,
            )
            self.assertNotIn("scores_missing", rec)

    def test_false_when_scores_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _halo_all_pass(repo, dogfood=True, n_scores=2)
            plan = study(repo)
            self.assertEqual(plan["scores_count"], 2)
            self.assertFalse(plan["scores_missing"])
            self.assertNotIn("scores_missing", plan["recommendation"])

    def test_write_plan_persists_scores_missing_and_baton(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _halo_all_pass(repo, dogfood=True, n_scores=0, create_scores_dir=False)
            plan = study(repo)
            path = write_plan(repo, plan)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("scores_count", loaded)
            self.assertIsInstance(loaded["scores_count"], int)
            self.assertEqual(loaded["scores_count"], 0)
            self.assertTrue(loaded.get("scores_missing"))
            baton = (repo / ".halo" / "baton.md").read_text(encoding="utf-8")
            self.assertRegex(baton, r"(?m)^- scores_missing:\s*true\s*$")


if __name__ == "__main__":
    unittest.main()
