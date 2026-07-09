#!/usr/bin/env python3
"""drive status includes watchdog_pid + heartbeat_age_sec."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_drive import _watchdog_status  # noqa: E402


class TestWatchdogStatus(unittest.TestCase):
    def test_missing_heartbeat_age_null(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo" / "logs").mkdir(parents=True)
            st = _watchdog_status(repo)
            self.assertIsNone(st["watchdog_pid"])
            self.assertFalse(st["watchdog_alive"])
            self.assertIsNone(st["heartbeat_age_sec"])

    def test_pid_and_age(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            logs = repo / ".halo" / "logs"
            logs.mkdir(parents=True)
            (logs / "watchdog.pid").write_text("1\n", encoding="utf-8")
            past = (datetime.now(timezone.utc) - timedelta(seconds=12)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            (logs / "watchdog-heartbeat.json").write_text(
                json.dumps({"at": past, "pid": 1, "ok": True}) + "\n",
                encoding="utf-8",
            )
            with mock.patch("halo_drive._pid_alive", return_value=True):
                st = _watchdog_status(repo)
            self.assertEqual(st["watchdog_pid"], 1)
            self.assertTrue(st["watchdog_alive"])
            self.assertIsNotNone(st["heartbeat_age_sec"])
            self.assertGreaterEqual(st["heartbeat_age_sec"], 10)


if __name__ == "__main__":
    unittest.main()
