#!/usr/bin/env python3
"""plugin.json version present and >= 0.8.1 after continuous-drive work (D088)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

HALO = Path(__file__).resolve().parents[2]
PLUGIN = HALO / ".grok-plugin" / "plugin.json"


class TestPluginVersion(unittest.TestCase):
    def test_version_bumped(self) -> None:
        self.assertTrue(PLUGIN.is_file(), PLUGIN)
        data = json.loads(PLUGIN.read_text(encoding="utf-8"))
        ver = str(data.get("version") or "")
        parts = [int(x) for x in ver.split(".")[:3]]
        self.assertGreaterEqual(tuple(parts + [0, 0, 0])[:3], (0, 8, 1), ver)
        desc = str(data.get("description") or "").lower()
        self.assertTrue("continuous" in desc or "drive" in desc or "headless" in desc)


if __name__ == "__main__":
    unittest.main()
