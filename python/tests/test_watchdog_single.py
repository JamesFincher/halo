#!/usr/bin/env python3
"""Watchdog single-instance: refuse if pidfile PID still alive."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HALO = Path(__file__).resolve().parents[2]
SCRIPT = HALO / "scripts" / "halo-watchdog.sh"


class TestWatchdogSingle(unittest.TestCase):
    def test_refuse_second_instance(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            logs = repo / ".halo" / "logs"
            logs.mkdir(parents=True)
            # Fake an alive pid (this process)
            (logs / "watchdog.pid").write_text(f"{os.getpid()}\n", encoding="utf-8")
            # loop inactive so if it did start it would exit — but refuse is first
            (repo / ".halo" / "loop.json").write_text(
                '{"active": false}\n', encoding="utf-8"
            )
            (repo / ".halo" / "state.json").write_text(
                '{"autonomous": false}\n', encoding="utf-8"
            )
            r = subprocess.run(
                ["bash", str(SCRIPT), str(repo), "15"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(r.returncode, 3, r.stderr + r.stdout)
            self.assertIn("refuse", (r.stderr + r.stdout).lower())


if __name__ == "__main__":
    unittest.main()
