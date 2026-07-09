#!/usr/bin/env python3
"""Evidence cert schema: missing cert fails; GREEN_TEST accepted (D082)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_evidence import check_file, validate_cert_schema  # noqa: E402


class TestEvidenceCertSchema(unittest.TestCase):
    def test_missing_cert_fails(self) -> None:
        ok, msg = validate_cert_schema({"ok": True, "feature": "D001"})
        self.assertFalse(ok)
        self.assertIn("missing cert", msg)

    def test_green_test_ok(self) -> None:
        ok, msg = validate_cert_schema({"cert": "GREEN_TEST", "ok": True})
        self.assertTrue(ok, msg)

    def test_check_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "bad.json"
            bad.write_text(json.dumps({"ok": True}) + "\n", encoding="utf-8")
            r = check_file(bad)
            self.assertFalse(r["ok"])
            good = Path(td) / "good.json"
            good.write_text(
                json.dumps({"cert": "GREEN_TEST", "ok": True}) + "\n", encoding="utf-8"
            )
            r2 = check_file(good)
            self.assertTrue(r2["ok"], r2)


if __name__ == "__main__":
    unittest.main()
