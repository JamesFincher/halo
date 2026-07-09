#!/usr/bin/env python3
"""D073: Watchdog single-instance via pidfile."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WATCHDOG = ROOT / "scripts" / "halo-watchdog.sh"


def _repo(tmp: Path, *, autonomous: bool = False) -> Path:
    halo = tmp / ".halo"
    (halo / "logs").mkdir(parents=True)
    (halo / "state.json").write_text(
        json.dumps(
            {
                "status": "ACTIVE",
                "phase": "build",
                "autonomous": autonomous,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    # loop inactive so a winning start exits quickly after claim
    (halo / "loop.json").write_text(
        json.dumps({"active": False, "iteration": 0, "max_iterations": 100}) + "\n",
        encoding="utf-8",
    )
    return tmp


class TestWatchdogSingleInstance(unittest.TestCase):
    def test_refuse_when_pidfile_pid_alive(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _repo(Path(td))
            pidfile = repo / ".halo" / "logs" / "watchdog.pid"
            # current process is alive — second start must refuse
            pidfile.write_text(str(os.getpid()) + "\n", encoding="utf-8")
            before = pidfile.read_text(encoding="utf-8")
            r = subprocess.run(
                ["bash", str(WATCHDOG), str(repo), "1"],
                capture_output=True,
                text=True,
                env={**os.environ, "HALO_SYSTEM": str(ROOT)},
                timeout=15,
            )
            self.assertEqual(r.returncode, 3, r.stdout + r.stderr)
            self.assertIn("refuse", (r.stderr + r.stdout).lower())
            # loser must not overwrite winner's pidfile
            self.assertEqual(pidfile.read_text(encoding="utf-8"), before)

    def test_reclaim_stale_pidfile_dead_pid(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _repo(Path(td), autonomous=False)
            pidfile = repo / ".halo" / "logs" / "watchdog.pid"
            # very unlikely to be a live process
            pidfile.write_text("999999999\n", encoding="utf-8")
            r = subprocess.run(
                ["bash", str(WATCHDOG), str(repo), "1"],
                capture_output=True,
                text=True,
                env={**os.environ, "HALO_SYSTEM": str(ROOT)},
                timeout=15,
            )
            # inactive loop → exits 0 after writing own pid
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            claimed = pidfile.read_text(encoding="utf-8").strip()
            self.assertTrue(claimed.isdigit())
            self.assertNotEqual(claimed, "999999999")


if __name__ == "__main__":
    unittest.main()
