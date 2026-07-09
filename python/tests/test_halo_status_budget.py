#!/usr/bin/env python3
"""D085: halo status human output includes budget verdict + watchdog age."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HALO = ROOT / "scripts" / "halo"


class TestHaloStatusBudget(unittest.TestCase):
    def test_status_prints_budget_and_watchdog_age(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            (halo / "logs").mkdir(parents=True)
            (halo / "state.json").write_text(
                json.dumps(
                    {
                        "product_name": "T",
                        "status": "ACTIVE",
                        "phase": "build",
                        "autonomous": True,
                        "spec_status": "locked",
                        "dogfood_mode": "compounding",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (halo / "loop.json").write_text(
                json.dumps({"active": True, "iteration": 1, "max_iterations": 10}) + "\n",
                encoding="utf-8",
            )
            (halo / "feature-list.json").write_text(
                json.dumps({"version": 1, "features": []}) + "\n", encoding="utf-8"
            )
            (halo / "logs" / "watchdog.pid").write_text(f"{os.getpid()}\n", encoding="utf-8")
            (halo / "logs" / "watchdog-heartbeat.json").write_text(
                json.dumps(
                    {
                        "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "ok": True,
                        "pid": os.getpid(),
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            env = {
                **os.environ,
                "HALO_SYSTEM": str(ROOT),
                "PYTHONPATH": str(ROOT / "python"),
            }
            r = subprocess.run(
                ["bash", str(HALO), "status", str(repo)],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            out = r.stdout
            # human line: budget:   verdict=ALLOW|PAUSE|…  (or bare ALLOW)
            self.assertRegex(out, r"budget:\s+.*(ALLOW|PAUSE|DEGRADE|HALT)")
            self.assertIn("watchdog:", out)
            self.assertRegex(out, r"heartbeat_age(_sec)?=")


if __name__ == "__main__":
    unittest.main()
