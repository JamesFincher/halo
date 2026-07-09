#!/usr/bin/env python3
"""scripts/halo help lists continuous-drive verbs (D089)."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

HALO = Path(__file__).resolve().parents[2]
CLI = HALO / "scripts" / "halo"


class TestHelpDriveVerbs(unittest.TestCase):
    def test_help_lists_verbs(self) -> None:
        r = subprocess.run(
            ["bash", str(CLI), "help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        out = r.stdout + r.stderr
        for verb in ("plan", "watchdog", "cycle-smoke", "reinstantiate"):
            self.assertIn(verb, out, f"missing {verb}")


if __name__ == "__main__":
    unittest.main()
