#!/usr/bin/env python3
"""D091: progress unit events include dirty_count (0 when clean)."""

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

from halo_progress import append, tail  # noqa: E402


def _git_init(repo: Path) -> None:
    subprocess.check_call(["git", "init"], cwd=repo, stdout=subprocess.DEVNULL)
    subprocess.check_call(
        ["git", "config", "user.email", "t@t.com"], cwd=repo, stdout=subprocess.DEVNULL
    )
    subprocess.check_call(
        ["git", "config", "user.name", "t"], cwd=repo, stdout=subprocess.DEVNULL
    )
    (repo / "README").write_text("x\n", encoding="utf-8")
    subprocess.check_call(["git", "add", "README"], cwd=repo, stdout=subprocess.DEVNULL)
    subprocess.check_call(
        ["git", "commit", "-m", "i"], cwd=repo, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


class TestProgressDirtyCount(unittest.TestCase):
    def test_unit_dirty_count_zero_when_clean(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            append(repo, "unit", {"note": "clean check"})
            rows = tail(repo, n=1)
            self.assertEqual(len(rows), 1)
            self.assertIn("dirty_count", rows[0])
            self.assertEqual(rows[0]["dirty_count"], 0)

    def test_unit_dirty_count_nonzero_when_dirty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            (repo / "extra.py").write_text("print(1)\n", encoding="utf-8")
            append(repo, "unit", {"note": "dirty check"})
            rows = tail(repo, n=1)
            self.assertGreaterEqual(rows[0].get("dirty_count"), 1)
            # .halo-only noise should not inflate if we only wrote progress under .halo
            # (extra.py is factory dirty)

    def test_non_unit_event_no_forced_dirty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            append(repo, "note", {"note": "not a unit"})
            rows = tail(repo, n=1)
            self.assertNotIn("dirty_count", rows[0])


if __name__ == "__main__":
    unittest.main()
