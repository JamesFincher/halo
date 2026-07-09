#!/usr/bin/env python3
"""D129: planner recommendation warns when scores_trajectories_match is false under dogfood."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_planner import _recommend, study  # noqa: E402


def _halo_all_pass(
    repo: Path,
    *,
    dogfood: bool = True,
    n_scores: int = 0,
    n_traj: int = 0,
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
    scores = halo / "scores"
    scores.mkdir(parents=True, exist_ok=True)
    for i in range(1, n_scores + 1):
        (scores / f"S{i:03d}.json").write_text("{}\n", encoding="utf-8")
    traj = halo / "trajectories"
    traj.mkdir(parents=True, exist_ok=True)
    for i in range(1, n_traj + 1):
        (traj / f"GT-{i:03d}.json").write_text("{}\n", encoding="utf-8")
    return halo


class TestPlannerScoresTrajectoriesDiverge(unittest.TestCase):
    def test_recommend_mentions_diverge_when_unequal_dogfood(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            rec = _recommend(
                repo,
                {"dogfood": True, "dogfood_mode": "compounding", "status": "ACTIVE"},
                {"all_pass": True, "next": None},
                [],
                scores_count=3,
                trajectories_count=1,
            )
            self.assertIn("scores_trajectories_diverge", rec)

    def test_skip_when_match_true(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            rec = _recommend(
                repo,
                {"dogfood": True, "status": "ACTIVE"},
                {"all_pass": True, "next": None},
                [],
                scores_count=2,
                trajectories_count=2,
            )
            self.assertNotIn("scores_trajectories_diverge", rec)

    def test_skip_when_not_dogfood(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            rec = _recommend(
                repo,
                {"dogfood": False, "status": "ACTIVE"},
                {"all_pass": True, "next": None},
                [],
                scores_count=5,
                trajectories_count=1,
            )
            self.assertNotIn("scores_trajectories_diverge", rec)

    def test_study_recommendation_when_diverge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _halo_all_pass(repo, dogfood=True, n_scores=3, n_traj=1)
            plan = study(repo)
            self.assertFalse(plan["scores_trajectories_match"])
            self.assertIn("scores_trajectories_diverge", plan["recommendation"])


if __name__ == "__main__":
    unittest.main()
