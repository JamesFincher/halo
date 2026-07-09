#!/usr/bin/env python3
"""D167: set_pass requires factory FILE_DIFF when requires_code true (unless --force)."""

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

from halo_features import _factory_diff_paths, set_pass  # noqa: E402


def _git_init(repo: Path) -> None:
    subprocess.check_call(["git", "init"], cwd=repo, stdout=subprocess.DEVNULL)
    subprocess.check_call(
        ["git", "config", "user.email", "t@t.com"], cwd=repo, stdout=subprocess.DEVNULL
    )
    subprocess.check_call(
        ["git", "config", "user.name", "t"], cwd=repo, stdout=subprocess.DEVNULL
    )
    (repo / "README").write_text("base\n", encoding="utf-8")
    subprocess.check_call(["git", "add", "README"], cwd=repo, stdout=subprocess.DEVNULL)
    subprocess.check_call(
        ["git", "commit", "-m", "i"],
        cwd=repo,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _scaffold(
    repo: Path,
    *,
    feature_id: str = "D167",
    requires_code: bool | None = True,
) -> Path:
    halo = repo / ".halo"
    halo.mkdir(parents=True, exist_ok=True)
    (halo / "state.json").write_text(
        json.dumps(
            {
                "status": "ACTIVE",
                "phase": "build",
                "autonomous": True,
                "dogfood": True,
                "dogfood_mode": "compounding",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    feat: dict = {
        "id": feature_id,
        "description": "fixture D167",
        "category": "dogfood",
        "passes": False,
    }
    if requires_code is not None:
        feat["requires_code"] = requires_code
    (halo / "feature-list.json").write_text(
        json.dumps({"version": 1, "features": [feat]}) + "\n",
        encoding="utf-8",
    )
    ev = halo / "evidence"
    ev.mkdir(exist_ok=True)
    (ev / f"{feature_id}-green.json").write_text(
        json.dumps(
            {
                "id": feature_id,
                "status": "GREEN",
                "exit_code": 0,
                "note": "fixture green evidence",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return halo


class TestFeaturesPassFactoryDiff(unittest.TestCase):
    def test_refuse_requires_code_empty_factory_diff(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            _scaffold(repo, requires_code=True)
            # clean tree + only .halo noise later — no factory paths
            self.assertEqual(_factory_diff_paths(repo), [])
            with self.assertRaises(SystemExit) as ctx:
                set_pass(repo, "D167", True, evidence=str(repo / ".halo/evidence/D167-green.json"))
            msg = str(ctx.exception)
            self.assertIn("FILE_DIFF", msg)
            self.assertIn("requires_code", msg)

    def test_force_bypasses_empty_factory_diff(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            _scaffold(repo, requires_code=True)
            data = set_pass(
                repo,
                "D167",
                True,
                force=True,
                note="human override",
            )
            feats = {f["id"]: f for f in data["features"]}
            self.assertTrue(feats["D167"]["passes"])

    def test_pass_with_factory_file_diff(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            _scaffold(repo, requires_code=True)
            (repo / "python_stub.py").write_text("x = 1\n", encoding="utf-8")
            diffs = _factory_diff_paths(repo)
            self.assertIn("python_stub.py", diffs)
            data = set_pass(
                repo,
                "D167",
                True,
                evidence=str(repo / ".halo/evidence/D167-green.json"),
            )
            feats = {f["id"]: f for f in data["features"]}
            self.assertTrue(feats["D167"]["passes"])
            self.assertIn("factory_diff", feats["D167"])
            self.assertIn("python_stub.py", feats["D167"]["factory_diff"])

    def test_requires_code_false_allows_empty_factory_diff(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            _scaffold(repo, requires_code=False)
            self.assertEqual(_factory_diff_paths(repo), [])
            data = set_pass(
                repo,
                "D167",
                True,
                evidence=str(repo / ".halo/evidence/D167-green.json"),
            )
            feats = {f["id"]: f for f in data["features"]}
            self.assertTrue(feats["D167"]["passes"])
            self.assertNotIn("factory_diff", feats["D167"])

    def test_halo_only_dirty_not_factory_diff(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            _git_init(repo)
            _scaffold(repo, requires_code=True)
            # extra .halo noise must not satisfy FILE_DIFF
            (repo / ".halo" / "noise.txt").write_text("noise\n", encoding="utf-8")
            self.assertEqual(_factory_diff_paths(repo), [])
            with self.assertRaises(SystemExit) as ctx:
                set_pass(repo, "D167", True, evidence=str(repo / ".halo/evidence/D167-green.json"))
            self.assertIn("FILE_DIFF", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
