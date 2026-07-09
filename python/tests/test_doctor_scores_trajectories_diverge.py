#!/usr/bin/env python3
"""D162/D117: doctor warns when compounding self-instance scores_count != trajectories_count.

Uses list_scores / list_trajectories culture (S*.json / GT-*.json only) so doctor
and scores/trajectories CLI agree; junk files do not change diverge detection.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_doctor import check_product  # noqa: E402
from halo_scores import list_scores, list_trajectories  # noqa: E402


def _write_repo(
    tmp: Path,
    *,
    dogfood: bool = True,
    autonomous: bool = True,
    loop_active: bool = True,
    n_scores: int = 0,
    n_traj: int = 0,
    junk_scores: bool = False,
    junk_traj: bool = False,
) -> Path:
    halo = tmp / ".halo"
    (halo / "logs").mkdir(parents=True)
    state: dict = {
        "autonomous": autonomous,
        "phase": "build",
        "status": "ACTIVE",
        "spec_status": "draft",
    }
    if dogfood:
        state["dogfood_mode"] = "compounding"
        state["dogfood"] = True
    (halo / "state.json").write_text(json.dumps(state) + "\n", encoding="utf-8")
    (halo / "loop.json").write_text(
        json.dumps({"active": loop_active, "iteration": 1}) + "\n", encoding="utf-8"
    )
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (halo / "logs" / "watchdog-heartbeat.json").write_text(
        json.dumps({"at": now, "ok": True, "pid": 1}) + "\n", encoding="utf-8"
    )
    scores = halo / "scores"
    scores.mkdir(parents=True)
    for i in range(1, n_scores + 1):
        sid = f"S{i:03d}"
        (scores / f"{sid}.json").write_text(
            json.dumps({"id": sid}) + "\n", encoding="utf-8"
        )
    if junk_scores:
        (scores / "readme.json").write_text(
            json.dumps({"note": "junk"}) + "\n", encoding="utf-8"
        )
        (scores / "score-1.json").write_text(
            json.dumps({"id": "nope"}) + "\n", encoding="utf-8"
        )
    traj = halo / "trajectories"
    traj.mkdir(parents=True)
    for i in range(1, n_traj + 1):
        tid = f"GT-{i:03d}"
        (traj / f"{tid}.json").write_text(
            json.dumps({"id": tid}) + "\n", encoding="utf-8"
        )
    if junk_traj:
        (traj / "readme.json").write_text(
            json.dumps({"note": "junk"}) + "\n", encoding="utf-8"
        )
        (traj / "trajectory-1.json").write_text(
            json.dumps({"id": "nope"}) + "\n", encoding="utf-8"
        )
    return tmp


class TestDoctorScoresTrajectoriesDiverge(unittest.TestCase):
    def test_warn_when_counts_unequal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), n_scores=2, n_traj=1)
            issues = check_product(repo)
            codes = [i["code"] for i in issues]
            self.assertIn("scores_trajectories_diverge", codes)
            warn = next(i for i in issues if i["code"] == "scores_trajectories_diverge")
            self.assertEqual(warn["level"], "warn")
            # D162 culture attribution
            self.assertIn("list_scores", warn["item"])
            self.assertIn("list_trajectories", warn["item"])
            self.assertIn("scores_count=2", warn["item"])
            self.assertIn("trajectories_count=1", warn["item"])

    def test_warn_when_traj_ahead(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), n_scores=1, n_traj=3)
            issues = check_product(repo)
            self.assertIn(
                "scores_trajectories_diverge", [i["code"] for i in issues]
            )
            warn = next(i for i in issues if i["code"] == "scores_trajectories_diverge")
            self.assertIn("scores_count=1", warn["item"])
            self.assertIn("trajectories_count=3", warn["item"])

    def test_culture_junk_does_not_mask_diverge(self) -> None:
        """D162: non-S* / non-GT-* junk must not equalize counts or suppress diverge."""
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(
                Path(td),
                n_scores=1,
                n_traj=2,
                junk_scores=True,
                junk_traj=True,
            )
            self.assertEqual(list_scores(repo).get("count"), 1)
            self.assertEqual(list_trajectories(repo).get("count"), 2)
            issues = check_product(repo)
            codes = [i["code"] for i in issues]
            self.assertIn("scores_trajectories_diverge", codes)
            warn = next(i for i in issues if i["code"] == "scores_trajectories_diverge")
            self.assertEqual(warn["level"], "warn")
            self.assertIn("scores_count=1", warn["item"])
            self.assertIn("trajectories_count=2", warn["item"])

    def test_culture_junk_does_not_create_false_diverge(self) -> None:
        """Equal culture counts stay equal even with junk files present."""
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(
                Path(td),
                n_scores=2,
                n_traj=2,
                junk_scores=True,
                junk_traj=True,
            )
            self.assertEqual(list_scores(repo).get("count"), 2)
            self.assertEqual(list_trajectories(repo).get("count"), 2)
            issues = check_product(repo)
            self.assertNotIn(
                "scores_trajectories_diverge", [i["code"] for i in issues]
            )

    def test_skip_when_both_zero(self) -> None:
        """Both empty: empty warns fire; diverge must not."""
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), n_scores=0, n_traj=0)
            issues = check_product(repo)
            self.assertNotIn(
                "scores_trajectories_diverge", [i["code"] for i in issues]
            )
            codes = [i["code"] for i in issues]
            self.assertIn("scores_empty", codes)
            self.assertIn("trajectories_empty", codes)

    def test_no_warn_when_equal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), n_scores=2, n_traj=2)
            issues = check_product(repo)
            self.assertNotIn(
                "scores_trajectories_diverge", [i["code"] for i in issues]
            )

    def test_no_warn_when_not_dogfood(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), dogfood=False, n_scores=2, n_traj=1)
            issues = check_product(repo)
            self.assertNotIn(
                "scores_trajectories_diverge", [i["code"] for i in issues]
            )

    def test_not_error_level(self) -> None:
        """Warn must not make doctor report fail (strict keys on errors only)."""
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), n_scores=2, n_traj=1)
            issues = check_product(repo)
            d = [i for i in issues if i["code"] == "scores_trajectories_diverge"]
            self.assertTrue(d)
            self.assertEqual(d[0]["level"], "warn")
            self.assertNotEqual(d[0]["level"], "error")
            errors = [i for i in issues if i.get("level") == "error"]
            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
