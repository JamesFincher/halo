#!/usr/bin/env python3
"""D130: NEXT_PROMPT includes latest_score_id and latest_trajectory_id."""

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


class TestNextPromptLatestIds(unittest.TestCase):
    def test_prompt_dash_when_scores_and_trajectories_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _base_repo(repo)
            text = build_prompt(repo, HALO_SYS)
            self.assertIn("latest_score_id: -", text)
            self.assertIn("latest_trajectory_id: -", text)

    def test_prompt_includes_latest_ids_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _base_repo(repo)
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir()
            traj.mkdir()
            (scores / "S001.json").write_text("{}\n", encoding="utf-8")
            (scores / "S003.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-001.json").write_text("{}\n", encoding="utf-8")
            (traj / "GT-002.json").write_text("{}\n", encoding="utf-8")
            text = build_prompt(repo, HALO_SYS)
            self.assertIn("latest_score_id: S003", text)
            self.assertIn("latest_trajectory_id: GT-002", text)

    def test_prompt_dash_when_dirs_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = _base_repo(repo)
            (halo / "scores").mkdir()
            (halo / "trajectories").mkdir()
            text = build_prompt(repo, HALO_SYS)
            self.assertIn("latest_score_id: -", text)
            self.assertIn("latest_trajectory_id: -", text)


if __name__ == "__main__":
    unittest.main()
