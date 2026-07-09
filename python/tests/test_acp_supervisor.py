#!/usr/bin/env python3
"""Unit tests for halo_acp_supervisor using a fake grok binary."""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import halo_acp_supervisor  # noqa: E402


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


class TestACPSupervisor(unittest.TestCase):
    def _fake_grok_script(self, bin_dir: Path, updates: list[str] | None = None) -> Path:
        """Create a fake grok binary that implements the ACP protocol."""
        script = bin_dir / "grok"
        updates = updates or ["hello"]
        source = r"""#!/usr/bin/env python3
import json
import sys
import time

if "stdio" in sys.argv:
    for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except Exception:
                continue
            req_id = msg.get("id")
            method = msg.get("method")
            if method == "initialize":
                print(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {"authMethods": [{"id": "xai.api_key"}]}}), flush=True)
            elif method == "authenticate":
                print(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {}}), flush=True)
            elif method == "session/new":
                print(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {"sessionId": "s1"}}), flush=True)
            elif method == "session/prompt":
                for text in UPDATES:
                    print(json.dumps({"jsonrpc": "2.0", "method": "session/update", "params": {"update": {"sessionUpdate": "agent_message_chunk", "content": {"text": text}}}}), flush=True)
                    time.sleep(0.05)
                print(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": {"stopReason": "end_turn"}}), flush=True)
"""
        source = source.replace("UPDATES", repr(updates))
        script.write_text(source, encoding="utf-8")
        script.chmod(0o755)
        return script

    def _repo(self) -> Path:
        td = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, td, ignore_errors=True)
        repo = td / "repo"
        repo.mkdir()
        halo = repo / ".halo"
        halo.mkdir()
        _write_json(
            halo / "state.json",
            {
                "status": "ACTIVE",
                "phase": "build",
                "autonomous": True,
            },
        )
        _write_json(
            halo / "loop.json",
            {
                "active": True,
                "max_iterations": 1,
                "iteration": 0,
                "acp": True,
            },
        )
        return repo

    def test_acp_client_prompt(self) -> None:
        """ACPClient can drive a session with a fake grok."""
        td = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, td, ignore_errors=True)
        bin_dir = td / "bin"
        bin_dir.mkdir()
        self._fake_grok_script(bin_dir, updates=["unit ", "done"])

        repo = self._repo()
        client = halo_acp_supervisor.ACPClient(repo, grok=str(bin_dir / "grok"))
        client.start()
        os.environ["XAI_API_KEY"] = "xai-test"
        halo_acp_supervisor._authenticate(client)
        session_id = client.session_new(str(repo))
        result = client.prompt(session_id, "test prompt")
        client.close()
        self.assertEqual(result["text"], "unit done")
        self.assertEqual(result["stop_reason"], "end_turn")

    def test_run_supervisor_increments_iteration_and_stops(self) -> None:
        """Run supervisor for one turn, then stop because max_iterations=1."""
        td = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, td, ignore_errors=True)
        bin_dir = td / "bin"
        bin_dir.mkdir()
        self._fake_grok_script(bin_dir, updates=["turn ", "1"])
        repo = self._repo()

        # Avoid depending on full NEXT_PROMPT template generation.
        original = halo_acp_supervisor._write_next_prompt
        original_path = os.environ.get("PATH", "")
        original_xai = os.environ.get("XAI_API_KEY", "")

        def fake_write_next_prompt(r: Path, hs: Path | None) -> Path:
            path = r / ".halo" / "NEXT_PROMPT.md"
            path.write_text("execute one unit", encoding="utf-8")
            return path

        halo_acp_supervisor._write_next_prompt = fake_write_next_prompt
        try:
            os.environ["PATH"] = f"{bin_dir}:{original_path}"
            os.environ["XAI_API_KEY"] = "xai-test"
            # run_supervisor is blocking; run in a thread with a timeout.
            exit_code = {"value": -1}

            def run() -> None:
                exit_code["value"] = halo_acp_supervisor.run_supervisor(
                    repo, ROOT, max_iterations=1
                )

            t = threading.Thread(target=run)
            t.start()
            t.join(timeout=10.0)
            if t.is_alive():
                self.fail("supervisor did not stop in time")
            self.assertEqual(exit_code["value"], 0)
            loop = json.loads((repo / ".halo" / "loop.json").read_text(encoding="utf-8"))
            self.assertEqual(loop.get("iteration"), 1)
            self.assertFalse(loop.get("active"))
        finally:
            halo_acp_supervisor._write_next_prompt = original
            os.environ["PATH"] = original_path
            os.environ["XAI_API_KEY"] = original_xai

    def test_should_continue_respects_off(self) -> None:
        repo = self._repo()
        (repo / ".halo" / "OFF").write_text("x\n", encoding="utf-8")
        cont, reason = halo_acp_supervisor._should_continue(repo)
        self.assertFalse(cont)
        self.assertIn("OFF", reason)

    def test_should_continue_respects_max_iterations(self) -> None:
        repo = self._repo()
        _write_json(repo / ".halo" / "loop.json", {"active": True, "max_iterations": 0, "iteration": 0, "acp": True})
        cont, reason = halo_acp_supervisor._should_continue(repo)
        self.assertFalse(cont)
        self.assertIn("max_iterations", reason)


if __name__ == "__main__":
    unittest.main()
