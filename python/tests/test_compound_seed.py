#!/usr/bin/env python3
"""RED→GREEN: dogfood compounding auto-seed (D030)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_features import (  # noqa: E402
    load_list,
    maybe_seed_compounding_batch,
    save_list,
    summary,
)


def _utc_day(ts: str | None = None) -> str:
    if ts:
        return ts[:10]
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _repo_with_features(
    tmp: Path,
    *,
    features: list[dict],
    dogfood_mode: str = "compounding",
    state_dogfood: bool = True,
) -> Path:
    halo = tmp / ".halo"
    halo.mkdir(parents=True)
    fl = {
        "version": 1,
        "dogfood": True,
        "dogfood_mode": dogfood_mode,
        "features": features,
    }
    (halo / "feature-list.json").write_text(json.dumps(fl, indent=2) + "\n", encoding="utf-8")
    state = {
        "dogfood": state_dogfood,
        "dogfood_mode": dogfood_mode,
        "phase": "build",
        "status": "ACTIVE",
        "autonomous": True,
    }
    (halo / "state.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return tmp


class TestCompoundSeed(unittest.TestCase):
    def test_seeds_three_when_all_pass_compounding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _repo_with_features(
                Path(td),
                features=[
                    {
                        "id": "D001",
                        "description": "done",
                        "category": "dogfood",
                        "passes": True,
                        "steps": ["ok"],
                    }
                ],
            )
            result = maybe_seed_compounding_batch(repo)
            self.assertTrue(result.get("seeded"), result)
            self.assertEqual(len(result.get("added") or []), 3)
            data = load_list(repo)
            self.assertEqual(len(data["features"]), 4)
            self.assertEqual(data.get("last_compound_seed_date"), _utc_day())
            sm = summary(repo, compound=False)
            self.assertFalse(sm["all_pass"])
            self.assertEqual(sm["remaining"], 3)
            for fid in result["added"]:
                self.assertTrue(str(fid).startswith("D"))

    def test_noop_when_pending_remain(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _repo_with_features(
                Path(td),
                features=[
                    {
                        "id": "D001",
                        "description": "done",
                        "passes": True,
                        "steps": ["ok"],
                    },
                    {
                        "id": "D002",
                        "description": "open",
                        "passes": False,
                        "steps": ["todo"],
                    },
                ],
            )
            result = maybe_seed_compounding_batch(repo)
            self.assertFalse(result.get("seeded"))
            self.assertEqual(result.get("reason"), "not all_pass")
            self.assertEqual(len(load_list(repo)["features"]), 2)

    def test_once_per_utc_day(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _repo_with_features(
                Path(td),
                features=[
                    {
                        "id": "D010",
                        "description": "done",
                        "passes": True,
                        "steps": ["ok"],
                    }
                ],
            )
            r1 = maybe_seed_compounding_batch(repo)
            self.assertTrue(r1.get("seeded"), r1)
            # mark all new ones pass so all_pass again
            data = load_list(repo)
            for f in data["features"]:
                f["passes"] = True
            save_list(repo, data)
            r2 = maybe_seed_compounding_batch(repo)
            self.assertFalse(r2.get("seeded"), r2)
            self.assertEqual(r2.get("reason"), "already seeded today")
            # force allows same-day reseed
            r3 = maybe_seed_compounding_batch(repo, force=True)
            self.assertTrue(r3.get("seeded"), r3)
            self.assertEqual(len(r3.get("added") or []), 3)

    def test_noop_when_not_compounding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _repo_with_features(
                Path(td),
                dogfood_mode="once",
                state_dogfood=False,
                features=[
                    {
                        "id": "S001",
                        "description": "done",
                        "passes": True,
                        "steps": ["ok"],
                    }
                ],
            )
            # clear dogfood flags on list
            data = load_list(repo)
            data["dogfood"] = False
            data["dogfood_mode"] = "once"
            save_list(repo, data)
            sp = repo / ".halo" / "state.json"
            st = json.loads(sp.read_text(encoding="utf-8"))
            st["dogfood"] = False
            st["dogfood_mode"] = "once"
            sp.write_text(json.dumps(st) + "\n", encoding="utf-8")
            result = maybe_seed_compounding_batch(repo)
            self.assertFalse(result.get("seeded"))
            self.assertIn(result.get("reason"), ("not compounding", "not dogfood compounding"))


if __name__ == "__main__":
    unittest.main()
