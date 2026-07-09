#!/usr/bin/env python3
"""halo probe rejects empty --url (D099)."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "halo_probe.py"


class TestProbeEmptyUrl(unittest.TestCase):
    def test_empty_url_nonzero(self) -> None:
        r = subprocess.run(
            [sys.executable, str(PROBE), "--url", ""],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("empty", (r.stdout + r.stderr).lower())

    def test_whitespace_url_nonzero(self) -> None:
        r = subprocess.run(
            [sys.executable, str(PROBE), "--url", "   "],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(r.returncode, 0)

    def test_help_lists_url(self) -> None:
        r = subprocess.run(
            [sys.executable, str(PROBE), "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0)
        self.assertIn("--url", r.stdout)


if __name__ == "__main__":
    unittest.main()
