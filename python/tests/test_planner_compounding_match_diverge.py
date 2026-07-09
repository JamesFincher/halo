#!/usr/bin/env python3
"""D163: planner recommendation warns when scores_trajectories_match is false under compounding."""

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
    compounding: bool = True,
    dogfood: bool | None = None,
    n_scores: int = 0,
    n_traj: int = 0,
    junk: bool = False,
) -> Path:
    halo = repo / ".halo"
    halo.mkdir(parents=True, exist_ok=True)
    state: dict = {
        "status": "ACTIVE",
        "phase": "build",
        "autonomous": True,
    }
    if compounding:
        state["dogfood_mode"] = "compounding"
    if dogfood is True:
        state["dogfood"] = True
    elif dogfood is False:
        state["dogfood"] = False
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
    if junk:
        (scores / "notes.txt").write_text("ignore\n", encoding="utf-8")
        (scores / "extra.json").write_text("{}\n", encoding="utf-8")
        (traj / "orphan.json").write_text("{}\n", encoding="utf-8")
    return halo


class TestPlannerCompoundingMatchDiverge(unittest.TestCase):
    """D163: compounding-mode path + culture counts + match flag."""

    def test_recommend_diverge_under_compounding_mode_only(self) -> None:
        """dogfood_mode=compounding without dogfood key still warns."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            rec = _recommend(
                repo,
                {"dogfood_mode": "compounding", "status": "ACTIVE"},
                {"all_pass": True, "next": None},
                [],
                scores_count=4,
                trajectories_count=1,
            )
            self.assertIn("scores_trajectories_diverge", rec)
            self.assertIn("4", rec)
            self.assertIn("1", rec)

    def test_skip_when_match_true_under_compounding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            rec = _recommend(
                repo,
                {"dogfood_mode": "compounding", "status": "ACTIVE"},
                {"all_pass": True, "next": None},
                [],
                scores_count=2,
                trajectories_count=2,
                scores_trajectories_match=True,
            )
            self.assertNotIn("scores_trajectories_diverge", rec)

    def test_skip_when_not_compounding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            rec = _recommend(
                repo,
                {"dogfood": False, "dogfood_mode": "off", "status": "ACTIVE"},
                {"all_pass": True, "next": None},
                [],
                scores_count=9,
                trajectories_count=1,
                scores_trajectories_match=False,
            )
            self.assertNotIn("scores_trajectories_diverge", rec)

    def test_explicit_match_false_triggers_without_counts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            rec = _recommend(
                repo,
                {"dogfood_mode": "compounding", "status": "ACTIVE"},
                {"all_pass": True, "next": None},
                [],
                scores_trajectories_match=False,
            )
            self.assertIn("scores_trajectories_diverge", rec)

    def test_study_recommendation_when_diverge_compounding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _halo_all_pass(repo, compounding=True, n_scores=3, n_traj=1)
            plan = study(repo)
            self.assertFalse(plan["scores_trajectories_match"])
            self.assertEqual(plan["scores_count"], 3)
            self.assertEqual(plan["trajectories_count"], 1)
            self.assertIn("scores_trajectories_diverge", plan["recommendation"])

    def test_study_culture_ignores_junk_files(self) -> None:
        """list_scores/list_trajectories culture: only S*.json / GT-*.json count."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            # equal real counts + junk that would break naive glob of *.json
            _halo_all_pass(repo, compounding=True, n_scores=2, n_traj=1, junk=True)
            plan = study(repo)
            self.assertEqual(plan["scores_count"], 2)
            self.assertEqual(plan["trajectories_count"], 1)
            self.assertFalse(plan["scores_trajectories_match"])
            self.assertIn("scores_trajectories_diverge", plan["recommendation"])


if __name__ == "__main__":
    unittest.main()
