#!/usr/bin/env python3
"""D097: halo budget show prints spend and max_iterations together."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestBudgetShow(unittest.TestCase):
    def test_show_has_spend_and_max_iterations(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "state.json").write_text("{}", encoding="utf-8")
            (halo / "loop.json").write_text(
                json.dumps({"active": True, "iteration": 2, "max_iterations": 50}) + "\n",
                encoding="utf-8",
            )
            (halo / "spend.json").write_text(
                json.dumps({"day": "2026-07-09", "day_cycles": 1, "total_cycles": 1}) + "\n",
                encoding="utf-8",
            )
            r = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "halo_budget.py"),
                    "--repo",
                    str(repo),
                    "show",
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertIn("spend", data)
            self.assertIsInstance(data["spend"], dict)
            self.assertIn("budget", data)
            self.assertIn("max_iterations", data["budget"])
            # top-level convenience field (D097)
            self.assertEqual(data.get("max_iterations"), data["budget"]["max_iterations"])


if __name__ == "__main__":
    unittest.main()
