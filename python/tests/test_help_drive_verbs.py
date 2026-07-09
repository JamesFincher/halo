#!/usr/bin/env python3
"""scripts/halo help lists the simplified public lifecycle commands."""

from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

HALO = Path(__file__).resolve().parents[2]
CLI = HALO / "scripts" / "halo"

LIFECYCLE_VERBS = (
    "init", "status", "specs", "lock", "unlock", "ready",
    "scaffold", "build", "go", "stop", "resume", "continue",
    "handoff", "doctor", "help",
)


class TestHelpLifecycleVerbs(unittest.TestCase):
    def test_help_lists_verbs(self) -> None:
        r = subprocess.run(
            ["bash", str(CLI), "help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout + r.stderr
        for verb in LIFECYCLE_VERBS:
            self.assertIn(verb, out, f"missing {verb}")

    def test_help_lists_command_lines(self) -> None:
        r = subprocess.run(
            ["bash", str(CLI), "help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(r.returncode, 0, r.stderr)
        out = r.stdout
        for verb in LIFECYCLE_VERBS:
            pat = re.compile(rf"(?m)^\s+{re.escape(verb)}(?:\s|\[)")
            self.assertIsNotNone(
                pat.search(out),
                f"help missing dedicated command line for {verb!r}",
            )

    def test_doctor_required_cli_includes_verbs(self) -> None:
        import halo_doctor

        required = set(halo_doctor.REQUIRED_CLI)
        for verb in LIFECYCLE_VERBS:
            self.assertIn(
                verb,
                required,
                f"REQUIRED_CLI missing {verb!r}",
            )


if __name__ == "__main__":
    unittest.main()
