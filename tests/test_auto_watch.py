"""Tests for the auto-watch stream-death branch, in both shell variants.

`STREAM-DEAD` is not a diagnostic. SKILL.md turns it into an Auto-terminal
runtime failure, which downgrades the round and sticks that downgrade to the
rest of the session. `stall-watch` writes `stream-death` before it reaps and
`stream-reap-complete` after, so the first marker on its own only says a
terminal suffix was seen, not that the worker tree is gone. Emitting on it
lets a consequence that heavy rest on a half-finished handshake.

Waiting for the second marker has its own failure: both stall watchers swallow
a failed completion write and never retry it, so a round could wait out the
full hour for proof that is not coming. `REAP-UNKNOWN` is the exit from that,
and it is a checkpoint rather than a verdict.

Nothing covered this path before: no test in either repository referenced
`STREAM-DEAD`, so the emission could have been deleted outright and every
suite stayed green.

The watcher takes its state directory by handoff here, through
`IMPLEMENT_REVIEW_STATE_DIR`, which is what an orchestrator that already read
the dispatcher's `STATE-DIR` line does. That keeps these cases off the
30-second discovery window, so a slow process launch cannot decide the result.
One case per shell still drives discovery, since production falls back to it.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _quiet_spawn  # noqa: E402,F401  installs a windowless spawn default on Windows

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "skills" / "implement-review" / "scripts"
WATCH_SH = SCRIPTS_DIR / "auto-watch.sh"
WATCH_PS1 = SCRIPTS_DIR / "auto-watch.ps1"

# Only the cases that assert a wait pay this; the rest end on the first poll.
WATCH_TIMEOUT_SECONDS = "6"
WATCH_POLL_SECONDS = "1"
# The watchers' handoff grace. A marker older than this is past waiting for.
REAP_GRACE_SECONDS = 30
SUBPROCESS_TIMEOUT = int(os.environ.get("AGENT_CONFIG_TEST_TIMEOUT", "90"))


def _find_bash() -> str | None:
    """Git Bash on Windows; the WSL relay on PATH cannot run these scripts."""
    if platform.system() == "Windows":
        for candidate in (r"C:\Program Files\Git\bin\bash.exe",
                          r"C:\Program Files\Git\usr\bin\bash.exe"):
            if Path(candidate).is_file():
                return candidate
        return None
    return shutil.which("bash")


BASH = _find_bash()
PS_SHELL = shutil.which("pwsh") or shutil.which("powershell")


class _WatchCase(unittest.TestCase):
    """One fake repository plus one state directory the watcher will adopt."""

    def setUp(self) -> None:
        # The watcher re-execs itself from a private copy and can still hold the
        # working directory when the parent returns, which makes a strict
        # TemporaryDirectory cleanup raise WinError 32 on Windows. The fixture
        # is disposable; a leftover directory under %TEMP% is not a test result.
        base = Path(tempfile.mkdtemp(prefix="auto-watch-"))
        self.addCleanup(shutil.rmtree, base, True)
        self.repo = base / "repo"
        self.repo.mkdir()
        self.tmpdir = base / "tmp"
        self.tmpdir.mkdir()

    def env(self, state_dir: Path | None = None) -> dict:
        env = dict(os.environ)
        env["TMPDIR"] = str(self.tmpdir)
        env["AGENT_CONFIG_AUTO_WATCH_TIMEOUT"] = WATCH_TIMEOUT_SECONDS
        env["AGENT_CONFIG_AUTO_WATCH_POLL"] = WATCH_POLL_SECONDS
        env.pop("IMPLEMENT_REVIEW_STATE_DIR", None)
        if state_dir is not None:
            env["IMPLEMENT_REVIEW_STATE_DIR"] = str(state_dir)
        return env

    def make_state_dir(self, name: str = "handed-over",
                       age_seconds: int = 0) -> Path:
        """A dispatch that has died mid-stream, `age_seconds` ago."""
        state = self.tmpdir / name
        state.mkdir()
        stamped = int(time.time()) - age_seconds
        (state / "timestamp").write_text(str(stamped), encoding="utf-8")
        (state / "pre-mtime").write_text("0", encoding="utf-8")
        (state / "tail").write_text("output\n", encoding="utf-8")
        death = state / "stream-death"
        death.write_text(
            "STREAM-DEATH 2026-08-21T00:00:00Z codex-response-stream-disconnected\n",
            encoding="utf-8")
        if age_seconds:
            os.utime(death, (stamped, stamped))
        return state

    def complete_the_reap(self, state: Path) -> None:
        (state / "stream-reap-complete").write_text(
            "STREAM-REAP-COMPLETE 2026-08-21T00:00:00Z\n", encoding="utf-8")

    # --- shared assertions, run once per shell -------------------------------

    def assert_waits_without_the_completion_marker(self):
        state = self.make_state_dir()
        rc, out = self.run_watch(self.env(state))
        self.assertNotIn("STREAM-DEAD", out)
        self.assertNotIn("REAP-UNKNOWN", out)
        self.assertIn("TIMEOUT", out)
        self.assertEqual(rc, 2, out)

    def assert_emits_once_the_reap_completes(self):
        state = self.make_state_dir()
        self.complete_the_reap(state)
        rc, out = self.run_watch(self.env(state))
        self.assertIn("STREAM-DEAD", out)
        self.assertEqual(rc, 3, out)

    def assert_a_lost_completion_marker_becomes_a_checkpoint(self):
        state = self.make_state_dir(age_seconds=REAP_GRACE_SECONDS * 2)
        rc, out = self.run_watch(self.env(state))
        self.assertIn(f"REAP-UNKNOWN {state}", out)
        self.assertNotIn("STREAM-DEAD", out)
        # Exit 2 is the watcher's checkpoint code, the same one TIMEOUT uses.
        # Exit 3 would make this a runtime failure and a sticky downgrade.
        self.assertEqual(rc, 2, out)

    def assert_the_handoff_adopts_what_discovery_would_reject(self):
        # Wrong repo hash, wrong round, and a timestamp an hour outside the
        # discovery window. Only the handoff can reach this directory.
        state = self.make_state_dir(
            name="implement-review-codex-00000000-round99-1-abc",
            age_seconds=3600)
        self.complete_the_reap(state)
        rc, out = self.run_watch(self.env(state))
        self.assertIn("STREAM-DEAD", out)
        self.assertEqual(rc, 3, out)

    def assert_discovery_still_adopts_a_fresh_directory(self):
        state = self.make_state_dir(
            name=f"implement-review-codex-{self.repo_hash()}-round1-1-abc")
        self.complete_the_reap(state)
        rc, out = self.run_watch(self.env())
        self.assertIn("STREAM-DEAD", out)
        self.assertEqual(rc, 3, out)


@unittest.skipIf(BASH is None, "bash not available")
class BashWatcherTests(_WatchCase):
    def repo_hash(self) -> str:
        proc = subprocess.run(
            [BASH, "-c", "pwd | sha256sum | cut -c1-8"],
            cwd=str(self.repo), capture_output=True, text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        return proc.stdout.strip()

    def run_watch(self, env: dict) -> tuple[int, str]:
        proc = subprocess.run(
            [BASH, str(WATCH_SH), "Review-Codex.md", "1", "Codex"],
            cwd=str(self.repo), env=env, capture_output=True, text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        return proc.returncode, proc.stdout

    def test_stream_death_alone_does_not_emit(self):
        self.assert_waits_without_the_completion_marker()

    def test_stream_death_with_a_completed_reap_emits(self):
        self.assert_emits_once_the_reap_completes()

    def test_a_lost_completion_marker_becomes_a_checkpoint(self):
        self.assert_a_lost_completion_marker_becomes_a_checkpoint()

    def test_the_handoff_adopts_what_discovery_would_reject(self):
        self.assert_the_handoff_adopts_what_discovery_would_reject()

    def test_discovery_still_adopts_a_fresh_directory(self):
        self.assert_discovery_still_adopts_a_fresh_directory()


@unittest.skipIf(PS_SHELL is None, "no PowerShell on PATH")
class PowerShellWatcherTests(_WatchCase):
    def repo_hash(self) -> str:
        expr = (
            "$b=[System.Text.Encoding]::UTF8.GetBytes((Get-Location).Path);"
            "$s=[System.Security.Cryptography.SHA256]::Create();"
            "([System.BitConverter]::ToString($s.ComputeHash($b)))"
            ".Replace('-','').Substring(0,8).ToLower()"
        )
        proc = subprocess.run(
            [PS_SHELL, "-NoProfile", "-NonInteractive", "-Command", expr],
            cwd=str(self.repo), capture_output=True, text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        return proc.stdout.strip()

    def run_watch(self, env: dict) -> tuple[int, str]:
        proc = subprocess.run(
            [PS_SHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
             "Bypass", "-File", str(WATCH_PS1), "Review-Codex.md", "1", "Codex"],
            cwd=str(self.repo), env=env, capture_output=True, text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        return proc.returncode, proc.stdout

    def test_stream_death_alone_does_not_emit(self):
        self.assert_waits_without_the_completion_marker()

    def test_stream_death_with_a_completed_reap_emits(self):
        self.assert_emits_once_the_reap_completes()

    def test_a_lost_completion_marker_becomes_a_checkpoint(self):
        self.assert_a_lost_completion_marker_becomes_a_checkpoint()

    def test_the_handoff_adopts_what_discovery_would_reject(self):
        self.assert_the_handoff_adopts_what_discovery_would_reject()

    def test_discovery_still_adopts_a_fresh_directory(self):
        self.assert_discovery_still_adopts_a_fresh_directory()


if __name__ == "__main__":
    unittest.main()
