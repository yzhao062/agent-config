"""The forced refresh path of the shared Agy quota readout.

`agent-quota.py` keeps a five-minute TTL on both the snapshot and the last
attempt, which is right for a statusline that renders on every turn. A prun
dispatcher whose run just died on a quota limit holds newer evidence than that
snapshot, so it asks for the refresh anyway. Without the force flag the call
returns having queried nothing, and the next unit of the batch routes on the
fraction that was already wrong (2026-09-11).
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUOTA = ROOT / "scripts" / "agent-quota.py"
PYTHON = Path(sys.executable).resolve()

USAGE_PAYLOAD = {
    "status": "SUCCESS",
    "command": {
        "name": "usage",
        "data": {
            "groups": [
                {
                    "name": "Gemini Models",
                    "buckets": [{"id": "gemini-5h", "remaining_fraction": 0.42}],
                },
                {
                    "name": "Claude and GPT models",
                    "buckets": [{"id": "3p-5h", "remaining_fraction": 0.0}],
                },
            ]
        },
    },
}

MOCK_AGY = (
    "import json, os, sys\n"
    "from pathlib import Path\n"
    "Path(os.environ['MOCK_AGY_CALLS']).open('a', encoding='utf-8')"
    ".write(' '.join(sys.argv[1:]) + '\\n')\n"
    f"print(json.dumps({USAGE_PAYLOAD!r}))\n"
)


def load_quota_module():
    spec = importlib.util.spec_from_file_location("agent_quota", QUOTA)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ForcedRefreshTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cache = self.root / "agy-quota-cache.json"
        self.calls = self.root / "agy-calls.txt"
        self.mock = self._write_mock()
        self._set_env("AGY_QUOTA_CACHE", str(self.cache))
        self._set_env("ANTIGRAVITY_BIN", str(self.mock))
        self._set_env("MOCK_AGY_CALLS", str(self.calls))
        # A snapshot young enough that the ordinary TTL declines to refresh.
        self.cache.write_text(
            json.dumps({"cached_at": 0, "usage": {"groups": []}}), encoding="utf-8"
        )
        self.module = load_quota_module()

    def _set_env(self, name: str, value: str) -> None:
        previous = os.environ.get(name)

        def restore() -> None:
            if previous is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = previous

        self.addCleanup(restore)
        os.environ[name] = value

    def _write_mock(self) -> Path:
        script = self.root / "mock_agy.py"
        script.write_text(MOCK_AGY, encoding="utf-8")
        if os.name == "nt":
            wrapper = self.root / "agy.cmd"
            wrapper.write_text(f'@"{PYTHON}" "{script}" %*\r\n', encoding="utf-8")
            return wrapper
        wrapper = self.root / "agy"
        wrapper.write_text(f'#!/bin/sh\nexec "{PYTHON}" "{script}" "$@"\n', encoding="utf-8")
        wrapper.chmod(0o755)
        return wrapper

    def _queries(self) -> int:
        if not self.calls.is_file():
            return 0
        return len(
            [line for line in self.calls.read_text(encoding="utf-8").splitlines() if line]
        )

    def test_a_fresh_snapshot_declines_an_ordinary_refresh(self) -> None:
        self.assertEqual(self.module._refresh_agy_cache(), 0)
        self.assertEqual(self._queries(), 0)

    def test_force_queries_past_the_snapshot_ttl(self) -> None:
        self.assertEqual(self.module._refresh_agy_cache(force=True), 0)
        self.assertEqual(self._queries(), 1)
        cached = json.loads(self.cache.read_text(encoding="utf-8"))
        groups = {g["name"]: g for g in cached["usage"]["groups"]}
        self.assertEqual(
            groups["Claude and GPT models"]["buckets"][0]["remaining_fraction"], 0.0
        )

    def test_force_also_passes_the_recent_attempt_marker(self) -> None:
        # The attempt marker is the second TTL, and a dispatcher that just hit
        # the limit has to get past both of them.
        Path(self.module.AGY_QUOTA_ATTEMPT).write_text(
            json.dumps({"ts": self.module.time.time()}), encoding="utf-8"
        )
        self.assertEqual(self.module._refresh_agy_cache(force=True), 0)
        self.assertEqual(self._queries(), 1)

    def test_the_command_line_accepts_the_force_flag(self) -> None:
        result = subprocess.run(
            [str(PYTHON), str(QUOTA), "--refresh-agy", "--force"],
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._queries(), 1)


if __name__ == "__main__":
    unittest.main()
