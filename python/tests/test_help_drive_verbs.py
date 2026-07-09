#!/usr/bin/env python3
"""scripts/halo help lists continuous-drive verbs (D089 + D168)."""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

HALO = Path(__file__).resolve().parents[2]
CLI = HALO / "scripts" / "halo"

# D168: continuous-drive surface that help + doctor must list
DRIVE_VERBS = ("plan", "watchdog", "cycle-smoke", "reinstantiate")


class TestHelpDriveVerbs(unittest.TestCase):
    def test_help_lists_verbs(self) -> None:
        """D089: help output mentions each continuous-drive verb."""
        r = subprocess.run(
            ["bash", str(CLI), "help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout + r.stderr
        for verb in DRIVE_VERBS:
            self.assertIn(verb, out, f"missing {verb}")

    def test_help_lists_drive_command_lines(self) -> None:
        """D168: each verb appears as a dedicated help command line."""
        r = subprocess.run(
            ["bash", str(CLI), "help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        for verb in DRIVE_VERBS:
            # e.g. "  plan [path]" or "  plan "
            pat = re.compile(rf"(?m)^\s+{re.escape(verb)}(?:\s|\[)")
            self.assertIsNotNone(
                pat.search(out),
                f"help missing dedicated command line for {verb!r}",
            )

    def test_doctor_required_cli_includes_drive_verbs(self) -> None:
        """D168: doctor REQUIRED_CLI lists continuous-drive verbs (integrity gate)."""
        import halo_doctor

        required = set(halo_doctor.REQUIRED_CLI)
        for verb in DRIVE_VERBS:
            self.assertIn(
                verb,
                required,
                f"REQUIRED_CLI missing continuous-drive verb {verb!r}",
            )


if __name__ == "__main__":
    unittest.main()
