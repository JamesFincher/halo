#!/usr/bin/env python3
"""RED→GREEN: Arena dual-lens + optional --spawn-check second-pass stub (D045)."""

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

from halo_arena import spawn_check_note, verify  # noqa: E402


def _repo_with_feature(tmp: Path, feature_id: str = "S001") -> Path:
    halo = tmp / ".halo"
    ev = halo / "evidence"
    plans = halo / "plans"
    ev.mkdir(parents=True)
    plans.mkdir(parents=True)
    (ev / f"{feature_id}-green.json").write_text(
        json.dumps(
            {
                "cert": "GREEN_TEST",
                "kind": "green-test",
                "feature_id": feature_id,
                "exit_code": 0,
                "ok": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (plans / f"{feature_id}-plan.md").write_text("# plan\n", encoding="utf-8")
    fl = {
        "version": 1,
        "features": [
            {
                "id": feature_id,
                "description": "test feature",
                "passes": False,
                "steps": ["step a", "step b"],
            }
        ],
    }
    (halo / "feature-list.json").write_text(json.dumps(fl, indent=2) + "\n", encoding="utf-8")
    return tmp


class TestArenaSpawnCheck(unittest.TestCase):
    def test_spawn_check_note_writes_cert(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / ".halo" / "evidence").mkdir(parents=True)
            report = {"verdict": "APPROVED", "feature_id": "S001"}
            out = spawn_check_note(repo, "S001", report)
            self.assertEqual(out["cert"], "ARENA_SPAWN_CHECK")
            self.assertEqual(out["feature_id"], "S001")
            self.assertEqual(out["mode"], "stub-second-pass")
            self.assertEqual(out["base_verdict"], "APPROVED")
            self.assertIn("dual-lens", out["note"].lower())
            path = Path(out["path"])
            self.assertTrue(path.is_file())
            self.assertEqual(path.name, "arena-spawn-check-S001.json")
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["cert"], "ARENA_SPAWN_CHECK")
            self.assertEqual(loaded["mode"], "stub-second-pass")

    def test_verify_dual_lens_keys(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _repo_with_feature(Path(td), "S002")
            rep = verify(repo, "S002")
            self.assertIn("A", rep)
            self.assertIn("B", rep)
            self.assertEqual(rep["A"]["lens"], "A_adversarial")
            self.assertEqual(rep["B"]["lens"], "B_constructive")
            self.assertIn(rep["verdict"], ("APPROVED", "NEEDS_REVISION", "REJECTED"))
            self.assertTrue((repo / ".halo" / "arena" / "S002.json").is_file())
            self.assertTrue((repo / ".halo" / "evidence" / "verdict-S002.json").is_file())

    def test_cli_spawn_check_flag(self) -> None:
        """CLI: verify --spawn-check embeds spawn_check in JSON output."""
        with tempfile.TemporaryDirectory() as td:
            repo = _repo_with_feature(Path(td), "S003")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "halo_arena.py"),
                    "--repo",
                    str(repo),
                    "verify",
                    "--id",
                    "S003",
                    "--spawn-check",
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr + proc.stdout)
            data = json.loads(proc.stdout)
            self.assertIn("spawn_check", data)
            self.assertEqual(data["spawn_check"]["cert"], "ARENA_SPAWN_CHECK")
            cert = repo / ".halo" / "evidence" / "arena-spawn-check-S003.json"
            self.assertTrue(cert.is_file())

    def test_cli_without_spawn_check_has_no_spawn_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _repo_with_feature(Path(td), "S004")
            proc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "halo_arena.py"),
                    "--repo",
                    str(repo),
                    "verify",
                    "--id",
                    "S004",
                ],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr + proc.stdout)
            data = json.loads(proc.stdout)
            self.assertNotIn("spawn_check", data)
            cert = repo / ".halo" / "evidence" / "arena-spawn-check-S004.json"
            self.assertFalse(cert.exists())


if __name__ == "__main__":
    unittest.main()
