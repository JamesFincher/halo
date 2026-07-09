#!/usr/bin/env python3
"""drive status includes budget.verdict (D079)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestDriveBudgetStatus(unittest.TestCase):
    def test_status_has_budget_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "state.json").write_text(
                json.dumps({"status": "ACTIVE", "phase": "build", "autonomous": True})
                + "\n",
                encoding="utf-8",
            )
            (halo / "loop.json").write_text(
                json.dumps({"active": True, "iteration": 1, "max_iterations": 50})
                + "\n",
                encoding="utf-8",
            )
            (halo / "feature-list.json").write_text(
                json.dumps({"features": []}) + "\n", encoding="utf-8"
            )
            (halo / "spend.json").write_text("{}\n", encoding="utf-8")
            r = subprocess.run(
                [sys.executable, str(ROOT / "halo_drive.py"), "--repo", str(repo), "status"],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
                env={**dict(**__import__("os").environ), "PYTHONPATH": str(ROOT)},
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(r.stdout)
            self.assertIn("budget", data)
            self.assertIn(data["budget"].get("verdict"), ("ALLOW", "HALT", "DEGRADE", "PAUSE"))


if __name__ == "__main__":
    unittest.main()
