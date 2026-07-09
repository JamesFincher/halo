#!/usr/bin/env python3
"""cycle-smoke evidence cert is GREEN_TEST (D101).

Does NOT invoke cycle-smoke (would recurse: smoke → unittest → smoke).
Asserts the writer emits the required cert shape (D138 moved write to Python).
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HALO = Path(__file__).resolve().parents[2]
ROOT = HALO / "python"
SCRIPT = HALO / "scripts" / "halo-cycle-smoke.sh"
WRITER = ROOT / "halo_cycle_smoke.py"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_cycle_smoke import build_evidence, write_evidence  # noqa: E402


class TestCycleSmokeCert(unittest.TestCase):
    def test_script_invokes_writer(self) -> None:
        self.assertTrue(SCRIPT.is_file(), SCRIPT)
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("D-cycle-smoke-latest.json", text + WRITER.read_text(encoding="utf-8"))
        self.assertIn("halo_cycle_smoke.py", text)
        self.assertIn("write-evidence", text)

    def test_writer_emits_green_test_cert(self) -> None:
        self.assertTrue(WRITER.is_file(), WRITER)
        text = WRITER.read_text(encoding="utf-8")
        self.assertIn("GREEN_TEST", text)
        self.assertIn("D-cycle-smoke-latest.json", text)

    def test_build_evidence_cert_shape(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "feature-list.json").write_text(
                json.dumps({"version": 1, "features": []}) + "\n",
                encoding="utf-8",
            )
            data = build_evidence(repo)
            self.assertEqual(data.get("cert"), "GREEN_TEST")
            self.assertEqual(data.get("exit_code"), 0)
            self.assertTrue(data.get("ok"))

    def test_existing_evidence_if_present(self) -> None:
        ev = HALO / ".halo" / "evidence" / "D-cycle-smoke-latest.json"
        if not ev.is_file():
            self.skipTest("no prior cycle-smoke evidence")
        data = json.loads(ev.read_text(encoding="utf-8"))
        self.assertEqual(data.get("cert"), "GREEN_TEST")
        self.assertEqual(data.get("exit_code"), 0)


if __name__ == "__main__":
    unittest.main()
