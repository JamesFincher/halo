#!/usr/bin/env python3
"""Verify halo_spec_write.py generates an intentionally verbose spec pack."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from halo_spec_write import write_specs


class TestSpecWrite(unittest.TestCase):
    def test_writes_all_excessive_docs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            halo = repo / ".halo"
            halo.mkdir()
            state = {
                "product_name": "TestProduct",
                "intake": {
                    "product_name": "TestProduct",
                    "purpose": "A test product for verifying spec generation.",
                    "features": [
                        {"title": "Sign up", "one_liner": "User creates an account"},
                        {"title": "Create thing", "one_liner": "User creates a thing"},
                    ],
                    "out_of_scope": ["Payments"],
                    "users": {"primary": "End user"},
                    "success_metric": "10 users",
                    "stack": {"language": "python", "framework": "fastapi"},
                    "data_model": {
                        "entities": [
                            {
                                "name": "User",
                                "fields": [
                                    {"name": "id", "type": "uuid"},
                                    {"name": "email", "type": "string"},
                                ],
                            }
                        ]
                    },
                    "milestones": [
                        {"n": 1, "name": "Foundation", "slug": "foundation", "scope": "Core app"},
                        {"n": 2, "name": "Value", "slug": "value", "scope": "Main feature"},
                    ],
                },
            }
            (halo / "state.json").write_text(json.dumps(state), encoding="utf-8")

            written = write_specs(repo)
            basenames = {Path(p).name for p in written}

            expected_core = {
                "PRD.md",
                "STACK.md",
                "DATA-MODEL.md",
                "DESIGN.md",
                "ARCHITECTURE.md",
                "INTEGRATIONS.md",
                "STORIES.md",
                "MILESTONES.md",
                "READINESS.md",
            }
            expected_extras = {
                "API.md",
                "USER-FLOWS.md",
                "ARCHITECTURE-DECISIONS.md",
                "SEQUENCE.md",
                "STATE.md",
                "SECURITY.md",
                "TEST-PLAN.md",
                "FRONTEND.md",
                "BACKEND.md",
                "MOBILE.md",
                "DEPLOYMENT.md",
                "RUNBOOK.md",
                "METRICS.md",
                "PROMPTS.md",
                "GLOSSARY.md",
                "RISKS.md",
                "PERSONAS.md",
                "SEED.md",
                "CHANGELOG.md",
                "CONTRIBUTING.md",
            }
            self.assertTrue(expected_core.issubset(basenames))
            self.assertTrue(expected_extras.issubset(basenames))

            # Verify verbose content: PRD has sections and stories have detailed acceptance.
            prd = (repo / ".halo" / "spec" / "PRD.md").read_text(encoding="utf-8")
            self.assertIn("## 1. Product overview", prd)
            self.assertIn("### User personas", prd)

            stories = (repo / ".halo" / "spec" / "STORIES.md").read_text(encoding="utf-8")
            self.assertIn("### S001", stories)
            self.assertIn("#### Acceptance criteria", stories)

            api = (repo / ".halo" / "spec" / "API.md").read_text(encoding="utf-8")
            self.assertIn("## Endpoints", api)


if __name__ == "__main__":
    unittest.main()
