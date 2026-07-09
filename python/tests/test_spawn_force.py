#!/usr/bin/env python3
"""spawn --force reaps dead lock (D087)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_drive import drive_lock_path, spawn_headless  # noqa: E402


class TestSpawnForce(unittest.TestCase):
    def test_force_reaps_dead_lock(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            logs = halo / "logs"
            logs.mkdir(parents=True)
            (halo / "loop.json").write_text(
                json.dumps({"active": True, "iteration": 1}) + "\n", encoding="utf-8"
            )
            (halo / "state.json").write_text(
                json.dumps({"status": "ACTIVE", "phase": "build", "autonomous": True})
                + "\n",
                encoding="utf-8",
            )
            (halo / "feature-list.json").write_text(
                json.dumps(
                    {
                        "features": [
                            {"id": "D1", "description": "x", "passes": False, "steps": []}
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (halo / "NEXT_PROMPT.md").write_text("# prompt\n" + ("x" * 80), encoding="utf-8")
            lp = drive_lock_path(repo)
            lp.write_text(
                json.dumps(
                    {
                        "pid": 999999,
                        "expires_at": 9999999999,
                        "mode": "headless",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            class FakeProc:
                pid = 4242

            with mock.patch("halo_drive._pid_alive", return_value=False), mock.patch(
                "halo_drive.shutil.which", return_value="/usr/bin/grok"
            ), mock.patch("halo_drive.subprocess.Popen", return_value=FakeProc()):
                r = spawn_headless(repo, force=True)
            self.assertTrue(r.get("ok"), r)
            self.assertEqual(r.get("pid"), 4242)


if __name__ == "__main__":
    unittest.main()
