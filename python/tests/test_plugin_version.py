#!/usr/bin/env python3
"""D088: plugin.json version matches TRUE-LOOP note after continuous-drive bumps."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / ".grok-plugin" / "plugin.json"
TRUE_LOOP = ROOT / "docs" / "TRUE-LOOP.md"


class TestPluginVersion(unittest.TestCase):
    def test_plugin_semver_and_true_loop_note(self) -> None:
        data = json.loads(PLUGIN.read_text(encoding="utf-8"))
        ver = str(data.get("version") or "")
        self.assertRegex(ver, r"^\d+\.\d+\.\d+$", f"plugin version not semver: {ver}")
        text = TRUE_LOOP.read_text(encoding="utf-8")
        # HTML comment: <!-- plugin X.Y.Z continuous-drive ... -->
        m = re.search(r"<!--\s*plugin\s+(\d+\.\d+\.\d+)\s+continuous-drive", text)
        self.assertIsNotNone(m, "TRUE-LOOP.md missing plugin continuous-drive version note")
        self.assertEqual(
            m.group(1),
            ver,
            f"plugin.json version {ver} != TRUE-LOOP note {m.group(1)}",
        )
        # continuous-drive surface mentioned (anti empty bump)
        self.assertIn("continuous-drive", text.lower())


if __name__ == "__main__":
    unittest.main()
