#!/usr/bin/env python3
"""D127: NEXT_PROMPT includes scores_count, trajectories_count, scores_trajectories_match."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_next_prompt import build_prompt  # noqa: E402

HALO_SYS = Path(__file__).resolve().parents[2]


def _base_repo(repo: Path) -> Path:
    halo = repo / ".halo"
    halo.mkdir(parents=True)
    (halo / "state.json").write_text(
        json.dumps(
            {
                "product_name": "T",
                "status": "ACTIVE",
                "phase": "build",
                "autonomous": True,
                "spec_status": "locked",
                "dogfood_mode": "compounding",
                "dogfood": True,
            }
        )
        + "\n",
        encoding="utf-8",
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


class TestNextPromptScoresTrajectories(unittest.TestCase):
    def test_prompt_includes_counts_and_match_true_when_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _base_repo(repo)
            text = build_prompt(repo, HALO_SYS)
            self.assertIn("scores_count: 0", text)
            self.assertIn("trajectories_count: 0", text)
            self.assertIn("scores_trajectories_match: true", text)

    def test_prompt_includes_counts_and_match_true_when_equal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _base_repo(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            (scores / "S002.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-002.json").write_text("{}\n", encoding="utf-8")
            text = build_prompt(repo, HALO_SYS)
            self.assertIn("scores_count: 2", text)
            self.assertIn("trajectories_count: 2", text)
            self.assertIn("scores_trajectories_match: true", text)

    def test_prompt_match_false_when_counts_diverge(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _base_repo(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            (scores / "S002.json").write_text("{}\n", encoding="utf-8")
            (scores / "S003.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            text = build_prompt(repo, HALO_SYS)
            self.assertIn("scores_count: 3", text)
            self.assertIn("trajectories_count: 1", text)
            self.assertIn("scores_trajectories_match: false", text)


if __name__ == "__main__":
    unittest.main()
