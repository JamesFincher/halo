#!/usr/bin/env python3
"""D114: doctor warns when dogfood autonomous and trajectories directory empty."""

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
    with_traj: bool = False,
    empty_traj_dir: bool = False,
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
    # Non-empty scores so scores_empty does not fire
    scores = halo / "scores"
    scores.mkdir(parents=True)
    (scores / "S001.json").write_text(json.dumps({"id": "S001"}) + "\n", encoding="utf-8")
    if with_traj:
        traj = halo / "trajectories"
        traj.mkdir(parents=True)
        (traj / "GT-001.json").write_text(
            json.dumps({"id": "GT-001"}) + "\n", encoding="utf-8"
        )
    elif empty_traj_dir:
        (halo / "trajectories").mkdir(parents=True)
    return tmp


class TestDoctorTrajectoriesEmpty(unittest.TestCase):
    def test_warn_when_missing_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), with_traj=False)
            issues = check_product(repo)
            codes = [i["code"] for i in issues]
            self.assertIn("trajectories_empty", codes)
            warn = next(i for i in issues if i["code"] == "trajectories_empty")
            self.assertEqual(warn["level"], "warn")

    def test_warn_when_empty_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), empty_traj_dir=True)
            issues = check_product(repo)
            self.assertIn("trajectories_empty", [i["code"] for i in issues])

    def test_no_warn_when_has_gt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), with_traj=True)
            issues = check_product(repo)
            self.assertNotIn("trajectories_empty", [i["code"] for i in issues])

    def test_no_warn_when_not_dogfood(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), dogfood=False, with_traj=False)
            issues = check_product(repo)
            self.assertNotIn("trajectories_empty", [i["code"] for i in issues])

    def test_not_error_level(self) -> None:
        """Warn must not make doctor report fail (strict keys on errors only)."""
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), with_traj=False)
            issues = check_product(repo)
            te = [i for i in issues if i["code"] == "trajectories_empty"]
            self.assertTrue(te)
            self.assertEqual(te[0]["level"], "warn")
            self.assertNotEqual(te[0]["level"], "error")


if __name__ == "__main__":
    unittest.main()
