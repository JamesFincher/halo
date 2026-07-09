#!/usr/bin/env python3
"""D122: halo status prints latest_score_id and latest_trajectory_id when present."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HALO = ROOT / "scripts" / "halo"


class TestHaloStatusLatestIds(unittest.TestCase):
    def _run_status(self, repo: Path) -> subprocess.CompletedProcess[str]:
        env = {
            **os.environ,
            "HALO_SYSTEM": str(ROOT),
            "PYTHONPATH": str(ROOT / "python"),
        }
        return subprocess.run(
            ["bash", str(HALO), "status", str(repo)],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

    def test_status_prints_latest_score_and_trajectory_id(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            scores = halo / "scores"
            traj = halo / "trajectories"
            scores.mkdir(parents=True)
            traj.mkdir(parents=True)
            (halo / "state.json").write_text(
                json.dumps(
                    {
                        "product_name": "T",
                        "status": "ACTIVE",
                        "phase": "build",
                        "autonomous": True,
                        "spec_status": "locked",
                        "dogfood_mode": "compounding",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (halo / "feature-list.json").write_text(
                json.dumps({"version": 1, "features": []}) + "\n", encoding="utf-8"
            )
            (scores / "S001.json").write_text(
                json.dumps({"id": "S001"}) + "\n", encoding="utf-8"
            )
            (scores / "S007.json").write_text(
                json.dumps({"id": "S007"}) + "\n", encoding="utf-8"
            )
            (traj / "GT-002.json").write_text(
                json.dumps({"id": "GT-002"}) + "\n", encoding="utf-8"
            )
            (traj / "GT-004.json").write_text(
                json.dumps({"id": "GT-004"}) + "\n", encoding="utf-8"
            )
            r = self._run_status(repo)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            out = r.stdout
            self.assertIn("latest_score_id: S007", out)
            self.assertIn("latest_trajectory_id: GT-004", out)

    def test_status_omits_or_dashes_when_ids_absent(self) -> None:
        """When no scores/trajectories, do not invent ids (dash or omit ok)."""
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            (halo / "state.json").write_text(
                json.dumps(
                    {
                        "product_name": "T",
                        "status": "ACTIVE",
                        "phase": "build",
                        "autonomous": False,
                        "spec_status": "locked",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (halo / "feature-list.json").write_text(
                json.dumps({"version": 1, "features": []}) + "\n", encoding="utf-8"
            )
            r = self._run_status(repo)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            out = r.stdout
            # Must not invent a real id
            self.assertNotRegex(out, r"latest_score_id:\s+S\d+")
            self.assertNotRegex(out, r"latest_trajectory_id:\s+GT-\d+")

    def test_status_prints_score_id_even_if_trajectory_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            scores = halo / "scores"
            scores.mkdir(parents=True)
            (halo / "state.json").write_text(
                json.dumps(
                    {
                        "product_name": "T",
                        "status": "ACTIVE",
                        "phase": "build",
                        "spec_status": "locked",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (halo / "feature-list.json").write_text(
                json.dumps({"version": 1, "features": []}) + "\n", encoding="utf-8"
            )
            (scores / "S003.json").write_text(
                json.dumps({"id": "S003"}) + "\n", encoding="utf-8"
            )
            r = self._run_status(repo)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            out = r.stdout
            self.assertIn("latest_score_id: S003", out)
            self.assertNotRegex(out, r"latest_trajectory_id:\s+GT-\d+")


if __name__ == "__main__":
    unittest.main()
