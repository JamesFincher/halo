#!/usr/bin/env python3
"""cycle-smoke evidence cert is GREEN_TEST (D101).

Does NOT invoke cycle-smoke (would recurse: smoke → unittest → smoke).
Asserts the script emits the required cert shape.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

HALO = Path(__file__).resolve().parents[2]
SCRIPT = HALO / "scripts" / "halo-cycle-smoke.sh"


class TestCycleSmokeCert(unittest.TestCase):
    def test_script_writes_green_test_cert(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("D-cycle-smoke-latest.json", text)
        self.assertIn('"cert":"GREEN_TEST"', text.replace(" ", ""))
        self.assertIn('"exit_code":0', text.replace(" ", ""))
        # cert field present in JSON body
        self.assertRegex(text, r'"cert"\s*:\s*"GREEN_TEST"')

    def test_existing_evidence_if_present(self) -> None:
        ev = HALO / ".halo" / "evidence" / "D-cycle-smoke-latest.json"
        if not ev.is_file():
            self.skipTest("no prior cycle-smoke evidence")
        import json

        data = json.loads(ev.read_text(encoding="utf-8"))
        self.assertEqual(data.get("cert"), "GREEN_TEST")
        self.assertEqual(data.get("exit_code"), 0)


if __name__ == "__main__":
    unittest.main()
