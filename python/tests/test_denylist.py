#!/usr/bin/env python3
"""RED→GREEN: tracked denylist for cycle-smoke (D044)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_denylist import (  # noqa: E402
    find_tracked_violations,
    is_denylist_path,
)


class TestDenylistPath(unittest.TestCase):
    def test_dogfood_control_plane(self) -> None:
        self.assertTrue(is_denylist_path(".halo/state.json"))
        self.assertTrue(is_denylist_path(".halo-archive/old/state.json"))
        self.assertTrue(is_denylist_path(".halo"))

    def test_secret_env_files(self) -> None:
        self.assertTrue(is_denylist_path(".env"))
        self.assertTrue(is_denylist_path("apps/web/.env"))
        self.assertTrue(is_denylist_path(".env.local"))
        self.assertTrue(is_denylist_path(".env.production"))
        self.assertTrue(is_denylist_path(".env.prod"))
        self.assertTrue(is_denylist_path(".env.development"))
        self.assertTrue(is_denylist_path(".env.staging"))

    def test_allow_env_templates(self) -> None:
        self.assertFalse(is_denylist_path(".env.example"))
        self.assertFalse(is_denylist_path(".env.sample"))
        self.assertFalse(is_denylist_path(".env.template"))
        self.assertFalse(is_denylist_path("packages/app/.env.example"))

    def test_credentials_and_keys(self) -> None:
        self.assertTrue(is_denylist_path("id_rsa"))
        self.assertTrue(is_denylist_path("keys/id_rsa"))
        self.assertTrue(is_denylist_path("credentials.json"))
        self.assertTrue(is_denylist_path("config/credentials.json"))
        self.assertTrue(is_denylist_path("secrets/api.key"))
        self.assertTrue(is_denylist_path("app/secrets/token"))

    def test_safe_source_paths(self) -> None:
        self.assertFalse(is_denylist_path("python/halo_state.py"))
        self.assertFalse(is_denylist_path("scripts/halo-cycle-smoke.sh"))
        self.assertFalse(is_denylist_path("README.md"))
        self.assertFalse(is_denylist_path("docs/secrets-policy.md"))  # docs name only

    def test_find_tracked_violations_filters(self) -> None:
        paths = [
            "python/halo_state.py",
            ".env.example",
            ".env",
            ".halo/state.json",
            "credentials.json",
            "README.md",
        ]
        bad = find_tracked_violations(paths)
        self.assertEqual(
            sorted(bad),
            sorted([".env", ".halo/state.json", "credentials.json"]),
        )

    def test_check_repo_ls_files_clean_on_temp_git(self) -> None:
        """Integration-ish: empty tracked set → no violations."""
        from halo_denylist import check_tracked_in_repo

        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            # no .git → soft skip, returns ok
            result = check_tracked_in_repo(repo)
            self.assertTrue(result["ok"])
            self.assertEqual(result["violations"], [])


if __name__ == "__main__":
    unittest.main()
