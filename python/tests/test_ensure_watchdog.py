#!/usr/bin/env python3
"""ensure_watchdog does not double-start when pidfile alive (D081)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_go import ensure_watchdog  # noqa: E402


class TestEnsureWatchdog(unittest.TestCase):
    def test_already_running(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            logs = repo / ".halo" / "logs"
            logs.mkdir(parents=True)
            (logs / "watchdog.pid").write_text(f"{os.getpid()}\n", encoding="utf-8")
            with mock.patch("halo_go._pid_alive", return_value=True):
                r = ensure_watchdog(repo)
            self.assertFalse(r.get("started"))
            self.assertEqual(r.get("reason"), "already_running")
            self.assertEqual(r.get("pid"), os.getpid())


if __name__ == "__main__":
    unittest.main()
