#!/usr/bin/env python3
"""D117: doctor warns when dogfood autonomous and scores_count != trajectories_count."""

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


def _write_repo(
    tmp: Path,
    *,
    dogfood: bool = True,
    autonomous: bool = True,
    loop_active: bool = True,
    n_scores: int = 0,
    n_traj: int = 0,
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
    traj = halo / "trajectories"
    traj.mkdir(parents=True)
    for i in range(1, n_traj + 1):
        tid = f"GT-{i:03d}"
        (traj / f"{tid}.json").write_text(
            json.dumps({"id": tid}) + "\n", encoding="utf-8"
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

    def test_warn_when_traj_ahead(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), n_scores=1, n_traj=3)
            issues = check_product(repo)
            self.assertIn(
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


if __name__ == "__main__":
    unittest.main()
