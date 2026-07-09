#!/usr/bin/env python3
"""should-drive respects backlog / dogfood (D093)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_drive import work_remains  # noqa: E402


def _write(repo: Path, *, pending: bool, dogfood: bool = False) -> None:
    halo = repo / ".halo"
    halo.mkdir(parents=True)
    (halo / "state.json").write_text(
        json.dumps(
            {
                "status": "ACTIVE",
                "phase": "build",
                "autonomous": True,
                "dogfood": dogfood,
                "dogfood_mode": "compounding" if dogfood else None,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (halo / "loop.json").write_text(
        json.dumps({"active": True}) + "\n", encoding="utf-8"
    )
    feats = [
        {
            "id": "D1",
            "description": "x",
            "passes": not pending,
            "steps": [],
        }
    ]
    (halo / "feature-list.json").write_text(
        json.dumps({"features": feats, "dogfood": dogfood}) + "\n", encoding="utf-8"
    )


class TestShouldDrive(unittest.TestCase):
    def test_open_backlog(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _write(repo, pending=True)
            self.assertTrue(work_remains(repo))

    def test_all_pass_product_stops(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _write(repo, pending=False, dogfood=False)
            self.assertFalse(work_remains(repo))

    def test_all_pass_dogfood_continues(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _write(repo, pending=False, dogfood=True)
            self.assertTrue(work_remains(repo))


if __name__ == "__main__":
    unittest.main()
