#!/usr/bin/env python3
"""Doctor warns on stale watchdog heartbeat when autonomous loop is active."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_doctor import STALE_HEARTBEAT_SEC, _stale_watchdog_issues, check_product  # noqa: E402


def _write_repo(tmp: Path, *, active: bool = True, age_sec: float | None = 10) -> Path:
    halo = tmp / ".halo"
    (halo / "logs").mkdir(parents=True)
    (halo / "state.json").write_text(
        json.dumps(
            {
                "autonomous": True,
                "phase": "build",
                "status": "ACTIVE",
                "spec_status": "draft",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (halo / "loop.json").write_text(
        json.dumps({"active": active, "iteration": 1}) + "\n", encoding="utf-8"
    )
    if age_sec is not None:
        past = (datetime.now(timezone.utc) - timedelta(seconds=age_sec)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        (halo / "logs" / "watchdog-heartbeat.json").write_text(
            json.dumps({"at": past, "ok": True, "pid": 1}) + "\n", encoding="utf-8"
        )
    return tmp


class TestDoctorHeartbeat(unittest.TestCase):
    def test_stale_warn(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), age_sec=STALE_HEARTBEAT_SEC + 30)
            issues = _stale_watchdog_issues(repo)
            codes = [i["code"] for i in issues]
            self.assertIn("watchdog_heartbeat_stale", codes)

    def test_fresh_ok(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), age_sec=5)
            self.assertEqual(_stale_watchdog_issues(repo), [])

    def test_check_product_includes_stale(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _write_repo(Path(td), age_sec=STALE_HEARTBEAT_SEC + 5)
            issues = check_product(repo)
            codes = [i["code"] for i in issues]
            self.assertIn("watchdog_heartbeat_stale", codes)


if __name__ == "__main__":
    unittest.main()
