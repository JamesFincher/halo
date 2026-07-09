#!/usr/bin/env python3
"""D160: doctor warns when compounding self-instance and scores directory empty."""

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
    with_score: bool = False,
    empty_scores_dir: bool = False,
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
    # Fresh heartbeat so D078 does not dominate fixtures
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    (halo / "logs" / "watchdog-heartbeat.json").write_text(
        json.dumps({"at": now, "ok": True, "pid": 1}) + "\n", encoding="utf-8"
    )
    if with_score:
        scores = halo / "scores"
        scores.mkdir(parents=True)
        (scores / "S001.json").write_text(
            json.dumps({"id": "S001"}) + "\n", encoding="utf-8"
        )
    elif empty_scores_dir:
        (halo / "scores").mkdir(parents=True)
    # Non-empty trajectories so trajectories_empty does not fire when scores present
    if with_score:
        traj = halo / "trajectories"
        traj.mkdir(parents=True)
        (traj / "GT-001.json").write_text(
            json.dumps({"id": "GT-001"}) + "\n", encoding="utf-8"
        )
    return tmp


class TestDoctorScoresEmpty(unittest.TestCase):
    def test_warn_when_missing_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), with_score=False)
            issues = check_product(repo)
            codes = [i["code"] for i in issues]
            self.assertIn("scores_empty", codes)
            warn = next(i for i in issues if i["code"] == "scores_empty")
            self.assertEqual(warn["level"], "warn")

    def test_warn_when_empty_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), empty_scores_dir=True)
            issues = check_product(repo)
            self.assertIn("scores_empty", [i["code"] for i in issues])

    def test_no_warn_when_has_score(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), with_score=True)
            issues = check_product(repo)
            self.assertNotIn("scores_empty", [i["code"] for i in issues])

    def test_no_warn_when_not_dogfood(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), dogfood=False, with_score=False)
            issues = check_product(repo)
            self.assertNotIn("scores_empty", [i["code"] for i in issues])

    def test_not_error_level(self) -> None:
        """Warn must not make doctor report fail (strict keys on errors only)."""
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), with_score=False)
            issues = check_product(repo)
            se = [i for i in issues if i["code"] == "scores_empty"]
            self.assertTrue(se)
            self.assertEqual(se[0]["level"], "warn")
            self.assertNotEqual(se[0]["level"], "error")


if __name__ == "__main__":
    unittest.main()
