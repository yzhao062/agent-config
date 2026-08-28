"""Contract tests for prun's dispatch-task.{sh,ps1}.

Validates the dispatch contract documented in skills/prun/SKILL.md. Mirrors
tests/test_dispatch_codex.py: the real codex binary is replaced with a mock
Python stub (via the CODEX_BIN override that dispatch-task honors) that logs
args + stdin + cwd, so the dispatch wiring is verified without invoking codex.

prun-specific contract vs dispatch-codex:
  - args are --prompt-file / --result-file / --unit-id (no --round).
  - state-dir is named prun-task-<8hex>-<unit-id>-<pid>-<16hex>.
  - codex runs from a per-unit SCRATCH cwd (<state-dir>/work) so accidental
    relative writes stay out of the user's repo.
  - the same `exec --sandbox <mode> [--ignore-user-config -c <reasoning>] -`
    shape and stdin delivery as dispatch-codex.

The bash class and the powershell class share a mixin and each skips when its
shell is not on PATH, so the same file runs on Ubuntu (bash) and Windows (both).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

# tests/ is on sys.path under `unittest discover -s tests` but not under
# `python -m unittest tests.<module>`, which validate.yml uses for the
# Sentinel redaction smoke. Put it there before the sibling import.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _quiet_spawn  # noqa: E402,F401  installs a windowless spawn default on Windows


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "skills" / "prun" / "scripts"
DISPATCH_SH = SCRIPTS_DIR / "dispatch-task.sh"
DISPATCH_PS1 = SCRIPTS_DIR / "dispatch-task.ps1"
REAP_WATCH_PS1 = SCRIPTS_DIR / "reap-watch.ps1"


def _temp_dir():
    if sys.version_info >= (3, 10):
        return tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    return tempfile.TemporaryDirectory()


MOCK_CODEX_PY = r'''"""Mock codex stub for dispatch-task tests."""
import json
import os
import sys
import time

log_dir = os.environ.get("MOCK_CODEX_LOG", os.getcwd())
os.makedirs(log_dir, exist_ok=True)

with open(os.path.join(log_dir, "args"), "w", encoding="utf-8") as f:
    f.write(json.dumps(sys.argv[1:]))

stdin_data = sys.stdin.read()
with open(os.path.join(log_dir, "stdin"), "w", encoding="utf-8", newline="") as f:
    f.write(stdin_data)

with open(os.path.join(log_dir, "cwd"), "w", encoding="utf-8") as f:
    f.write(os.getcwd())

result_target = os.environ.get("MOCK_CODEX_WRITE_RESULT")
if result_target:
    with open(result_target, "w", encoding="utf-8") as f:
        f.write(os.environ.get("MOCK_CODEX_RESULT_CONTENT", "# worker result\nreal worker content\n"))

sys.stdout.write(os.environ.get("MOCK_CODEX_STDOUT", "mock-codex: stdout\n"))
sys.stderr.write(os.environ.get("MOCK_CODEX_STDERR", "mock-codex: stderr\n"))
sys.stdout.flush()
sys.stderr.flush()

sleep_seconds = os.environ.get("MOCK_CODEX_SLEEP")
if sleep_seconds:
    time.sleep(float(sleep_seconds))

sys.exit(int(os.environ.get("MOCK_CODEX_EXIT", "0")))
'''


BASH = shutil.which("bash")
PS_SHELL = shutil.which("pwsh") or shutil.which("powershell")


def _git_bash() -> str | None:
    """Return a Git Bash executable on Windows, or None if there is none.

    ``shutil.which("bash")`` answers with the WSL launcher in System32 first,
    which fails with "execvpe(/bin/bash)" when no distro is installed. The file
    handle DispatchTaskReleasesDeployedPath is about belongs to Git Bash, so
    that is the binary to find. Off Windows the plain PATH answer is right.
    """
    if not sys.platform.startswith("win"):
        return BASH
    roots = [
        os.environ.get("ProgramFiles", "C:/Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    for root in roots:
        if not root:
            continue
        for parts in (("Git", "bin", "bash.exe"),
                      ("Programs", "Git", "bin", "bash.exe")):
            candidate = Path(root).joinpath(*parts)
            if candidate.is_file():
                return str(candidate)
    return None


GIT_BASH = _git_bash()


def _write_mock_codex(tmpdir: Path, want_powershell_shim: bool) -> Path:
    py_path = tmpdir / "mock_codex.py"
    py_path.write_text(MOCK_CODEX_PY, encoding="utf-8")
    if want_powershell_shim:
        shim = tmpdir / "codex-mock.cmd"
        shim.write_text(
            "@echo off\r\n" f'"{sys.executable}" "{py_path}" %*\r\n',
            encoding="utf-8",
        )
    else:
        shim = tmpdir / "codex-mock.sh"
        shim.write_text(
            "#!/usr/bin/env bash\n" f'exec "{sys.executable}" "{py_path}" "$@"\n',
            encoding="utf-8",
        )
        mode = shim.stat().st_mode
        shim.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return shim


def _parse_state_dir(stdout: str) -> Path:
    if not stdout:
        raise AssertionError("dispatch stdout is empty (expected STATE-DIR line)")
    first_line = stdout.splitlines()[0]
    match = re.match(r"^STATE-DIR (.+)$", first_line)
    if not match:
        raise AssertionError(
            f"first stdout line is not 'STATE-DIR <path>': {first_line!r}"
        )
    return Path(match.group(1).strip())


class _DispatchTaskContractMixin:
    SHELL_KIND: str = ""  # "bash" or "powershell"

    def _build_cmd(
        self, prompt_file: Path, result_file: str, unit_id: str
    ) -> list[str]:
        if self.SHELL_KIND == "bash":
            return [
                BASH, str(DISPATCH_SH),
                "--prompt-file", str(prompt_file),
                "--result-file", result_file,
                "--unit-id", unit_id,
            ]
        if self.SHELL_KIND == "powershell":
            return [
                PS_SHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(DISPATCH_PS1),
                "--prompt-file", str(prompt_file),
                "--result-file", result_file,
                "--unit-id", unit_id,
            ]
        raise AssertionError(f"unknown SHELL_KIND: {self.SHELL_KIND!r}")

    def _run_dispatch(
        self, cwd: Path, prompt_file: Path, result_file: str, unit_id: str,
        codex_bin: Path, log_dir: Path, exit_code: int = 0, timeout: float = 60.0,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["CODEX_BIN"] = str(codex_bin)
        env["MOCK_CODEX_LOG"] = str(log_dir)
        env["MOCK_CODEX_EXIT"] = str(exit_code)
        env["TMPDIR"] = str(cwd)
        env["TEMP"] = str(cwd)
        env["TMP"] = str(cwd)
        env.pop("PRUN_SCRATCH_CWD", None)
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            self._build_cmd(prompt_file, result_file, unit_id),
            cwd=str(cwd), env=env, capture_output=True, text=True,
            check=False, timeout=timeout,
        )

    def _fresh_fixture(self, tmpdir: Path) -> tuple[Path, Path, Path]:
        log_dir = tmpdir / "mock-log"
        log_dir.mkdir()
        codex_bin = _write_mock_codex(
            tmpdir, want_powershell_shim=(self.SHELL_KIND == "powershell")
        )
        prompt = tmpdir / "prompt.txt"
        prompt.write_text(
            "TASK PROMPT body\nLine 2 content\nLine 3 content\n", encoding="utf-8"
        )
        return codex_bin, prompt, log_dir

    # --- contract assertions ---------------------------------------------

    def test_state_dir_first_line(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result = self._run_dispatch(
                tmpdir, prompt, str(tmpdir / "result.md"), "unit_a", codex, log_dir
            )
            self.assertEqual(result.returncode, 0,
                             f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
            state_dir = _parse_state_dir(result.stdout)
            self.assertTrue(state_dir.is_absolute(), state_dir)
            self.assertTrue(state_dir.exists(), state_dir)

    def test_state_dir_naming(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result = self._run_dispatch(
                tmpdir, prompt, str(tmpdir / "r.md"), "survey_7", codex, log_dir
            )
            state_dir = _parse_state_dir(result.stdout)
            self.assertRegex(
                state_dir.name,
                r"^prun-task-[0-9a-f]{8}-survey_7-\d+-[0-9a-f]{16}$",
                f"state-dir name pattern: {state_dir.name}",
            )

    def test_state_dir_files(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result_file = tmpdir / "result.md"
            result_file.write_text("old result\n", encoding="utf-8")
            old_mtime = int(result_file.stat().st_mtime)
            result = self._run_dispatch(
                tmpdir, prompt, str(result_file), "u", codex, log_dir
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            state_dir = _parse_state_dir(result.stdout)

            pre_mtime = (state_dir / "pre-mtime").read_text(encoding="utf-8").strip()
            self.assertTrue(pre_mtime.isdigit(), pre_mtime)
            self.assertLess(int(pre_mtime), 10**12,
                            "pre-mtime must be Unix epoch seconds, not FILETIME")
            self.assertAlmostEqual(int(pre_mtime), old_mtime, delta=2)

            ts = (state_dir / "timestamp").read_text(encoding="utf-8").strip()
            self.assertTrue(ts.isdigit(), ts)
            self.assertLess(int(ts), 10**12)
            self.assertAlmostEqual(int(ts), int(time.time()), delta=60)

            recorded = (state_dir / "result-file").read_text(encoding="utf-8").strip()
            self.assertEqual(recorded, str(result_file),
                             "state-dir must record the result-file path")

            tail = (state_dir / "tail").read_text(encoding="utf-8")
            self.assertIn("mock-codex: stdout", tail)
            self.assertIn("mock-codex: stderr", tail)

    def test_pre_mtime_zero_when_result_missing(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result = self._run_dispatch(
                tmpdir, prompt, str(tmpdir / "absent.md"), "u", codex, log_dir
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            state_dir = _parse_state_dir(result.stdout)
            pre = (state_dir / "pre-mtime").read_text(encoding="utf-8").strip()
            self.assertEqual(pre, "0")

    def test_fallback_salvages_tail_when_result_unwritten(self) -> None:
        """If the worker exits without writing its result file, dispatch-task
        salvages the captured tail into the result file (FALLBACK header) so the
        unit is never silently missing when gather polls."""
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result_file = tmpdir / "result.md"  # the mock never writes this
            res = self._run_dispatch(
                tmpdir, prompt, str(result_file), "u_fb", codex, log_dir,
                extra_env={"MOCK_CODEX_STDOUT": "WORKER-OUTPUT-MARKER\n"},
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertTrue(result_file.exists(),
                            "fallback must create the result file when the worker did not")
            body = result_file.read_text(encoding="utf-8")
            self.assertIn("FALLBACK", body, "salvaged result must be marked FALLBACK")
            self.assertIn("u_fb", body, "fallback header must name the unit")
            self.assertIn("WORKER-OUTPUT-MARKER", body,
                          "fallback must salvage the worker's captured stdout from the tail")

    def test_idle_watchdog_reaps_worker_and_fallback_salvages_tail(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result_file = tmpdir / "result.md"
            res = self._run_dispatch(
                tmpdir, prompt, str(result_file), "u_idle", codex, log_dir,
                timeout=20.0,
                extra_env={
                    "MOCK_CODEX_STDOUT": "IDLE-REAP-MARKER\n",
                    "MOCK_CODEX_SLEEP": "30",
                    "PRUN_STALL_THRESHOLD": "1",
                    "CODEX_DISPATCH_TIMEOUT": "0",
                },
            )
            self.assertEqual(res.returncode, 124,
                             f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
            self.assertTrue(result_file.exists(),
                            "fallback must create the result file after idle reap")
            body = result_file.read_text(encoding="utf-8")
            self.assertIn("FALLBACK", body)
            self.assertIn("IDLE-REAP-MARKER", body)
            self.assertIn("idle-stall", body)
            self.assertIn("exit code 124", body)

    def test_hard_timeout_reaps_worker_and_fallback_names_trigger(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result_file = tmpdir / "result.md"
            res = self._run_dispatch(
                tmpdir, prompt, str(result_file), "u_hard", codex, log_dir,
                timeout=20.0,
                extra_env={
                    "MOCK_CODEX_STDOUT": "HARD-TIMEOUT-MARKER\n",
                    "MOCK_CODEX_SLEEP": "30",
                    "PRUN_STALL_THRESHOLD": "60",
                    "CODEX_DISPATCH_TIMEOUT": "1",
                },
            )
            self.assertEqual(res.returncode, 124,
                             f"STDOUT:\n{res.stdout}\nSTDERR:\n{res.stderr}")
            self.assertTrue(result_file.exists(),
                            "fallback must create the result file after hard timeout")
            body = result_file.read_text(encoding="utf-8")
            self.assertIn("FALLBACK", body)
            self.assertIn("HARD-TIMEOUT-MARKER", body)
            self.assertIn("hard-timeout", body)
            self.assertIn("exit code 124", body)

    def test_fallback_does_not_clobber_a_written_result(self) -> None:
        """When the worker DOES write a non-empty result file, dispatch-task must
        leave it untouched (no salvage clobber)."""
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result_file = tmpdir / "result.md"
            real = "# u_ok result\nConclusion: genuine worker result\n"
            res = self._run_dispatch(
                tmpdir, prompt, str(result_file), "u_ok", codex, log_dir,
                extra_env={
                    "MOCK_CODEX_WRITE_RESULT": str(result_file),
                    "MOCK_CODEX_RESULT_CONTENT": real,
                },
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            body = result_file.read_text(encoding="utf-8")
            self.assertEqual(body, real, "a worker-written result must survive untouched")
            self.assertNotIn("FALLBACK", body)

    def test_codex_runs_from_scratch_cwd(self) -> None:
        """The Round-3 Medium: codex runs from a per-unit scratch dir under the
        state-dir, so accidental relative writes stay out of the user's repo."""
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result = self._run_dispatch(
                tmpdir, prompt, str(tmpdir / "r.md"), "u", codex, log_dir
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            state_dir = _parse_state_dir(result.stdout)
            cwd_logged = Path((log_dir / "cwd").read_text(encoding="utf-8").strip())
            self.assertEqual(cwd_logged.name, "work",
                             f"codex cwd must be the scratch 'work' dir: {cwd_logged}")
            # And it must live under this dispatch's state-dir, not the repo.
            self.assertEqual(
                cwd_logged.parent.resolve(), state_dir.resolve(),
                f"scratch cwd must be under the state-dir: {cwd_logged}",
            )

    def test_prompt_sent_via_stdin(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result = self._run_dispatch(
                tmpdir, prompt, str(tmpdir / "r.md"), "u", codex, log_dir
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            stdin_log = (log_dir / "stdin").read_text(encoding="utf-8")
            for needle in ("TASK PROMPT body", "Line 2 content", "Line 3 content"):
                self.assertIn(needle, stdin_log)

    def test_codex_invoked_exec_dash_not_review(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result = self._run_dispatch(
                tmpdir, prompt, str(tmpdir / "r.md"), "u", codex, log_dir
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            args = json.loads((log_dir / "args").read_text(encoding="utf-8"))
            self.assertEqual(args[0], "exec", args)
            self.assertEqual(args[-1], "-", args)
            self.assertNotIn("review", args, args)
            # Scratch cwd is not a git repo, so codex needs this or it refuses
            # with "Not inside a trusted directory".
            self.assertIn("--skip-git-repo-check", args, args)

    def test_default_sandbox_flag(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result = self._run_dispatch(
                tmpdir, prompt, str(tmpdir / "r.md"), "u", codex, log_dir
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            args = json.loads((log_dir / "args").read_text(encoding="utf-8"))
            self.assertIn("--sandbox", args)
            self.assertEqual(args[args.index("--sandbox") + 1], "danger-full-access")

    def test_sandbox_override(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            old = os.environ.get("CODEX_DISPATCH_SANDBOX")
            os.environ["CODEX_DISPATCH_SANDBOX"] = "workspace-write"
            try:
                result = self._run_dispatch(
                    tmpdir, prompt, str(tmpdir / "r.md"), "u", codex, log_dir
                )
            finally:
                if old is None:
                    os.environ.pop("CODEX_DISPATCH_SANDBOX", None)
                else:
                    os.environ["CODEX_DISPATCH_SANDBOX"] = old
            self.assertEqual(result.returncode, 0, result.stderr)
            args = json.loads((log_dir / "args").read_text(encoding="utf-8"))
            self.assertEqual(args[args.index("--sandbox") + 1], "workspace-write")

    def test_mcp_isolation_default(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            old = os.environ.pop("CODEX_DISPATCH_ISOLATE_MCP", None)
            old_r = os.environ.pop("CODEX_DISPATCH_REASONING", None)
            try:
                result = self._run_dispatch(
                    tmpdir, prompt, str(tmpdir / "r.md"), "u", codex, log_dir
                )
            finally:
                if old is not None:
                    os.environ["CODEX_DISPATCH_ISOLATE_MCP"] = old
                if old_r is not None:
                    os.environ["CODEX_DISPATCH_REASONING"] = old_r
            self.assertEqual(result.returncode, 0, result.stderr)
            args = json.loads((log_dir / "args").read_text(encoding="utf-8"))
            self.assertIn("--ignore-user-config", args)
            self.assertIn(("-c", "model_reasoning_effort=xhigh"),
                          list(zip(args, args[1:])))
            self.assertEqual(args[-1], "-")

    def test_mcp_isolation_off(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            old = os.environ.get("CODEX_DISPATCH_ISOLATE_MCP")
            os.environ["CODEX_DISPATCH_ISOLATE_MCP"] = "off"
            try:
                result = self._run_dispatch(
                    tmpdir, prompt, str(tmpdir / "r.md"), "u", codex, log_dir
                )
            finally:
                if old is None:
                    os.environ.pop("CODEX_DISPATCH_ISOLATE_MCP", None)
                else:
                    os.environ["CODEX_DISPATCH_ISOLATE_MCP"] = old
            self.assertEqual(result.returncode, 0, result.stderr)
            args = json.loads((log_dir / "args").read_text(encoding="utf-8"))
            self.assertNotIn("--ignore-user-config", args)
            self.assertFalse(
                any(str(a).startswith("model_reasoning_effort=") for a in args), args
            )
            self.assertIn("--sandbox", args)
            self.assertEqual(args[-1], "-")

    def test_reasoning_override(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            old_iso = os.environ.pop("CODEX_DISPATCH_ISOLATE_MCP", None)
            old_r = os.environ.get("CODEX_DISPATCH_REASONING")
            os.environ["CODEX_DISPATCH_REASONING"] = "high"
            try:
                result = self._run_dispatch(
                    tmpdir, prompt, str(tmpdir / "r.md"), "u", codex, log_dir
                )
            finally:
                if old_iso is not None:
                    os.environ["CODEX_DISPATCH_ISOLATE_MCP"] = old_iso
                if old_r is None:
                    os.environ.pop("CODEX_DISPATCH_REASONING", None)
                else:
                    os.environ["CODEX_DISPATCH_REASONING"] = old_r
            self.assertEqual(result.returncode, 0, result.stderr)
            args = json.loads((log_dir / "args").read_text(encoding="utf-8"))
            self.assertIn("model_reasoning_effort=high", args)
            self.assertNotIn("model_reasoning_effort=xhigh", args)

    def test_exit_code_propagation(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result = self._run_dispatch(
                tmpdir, prompt, str(tmpdir / "r.md"), "u", codex, log_dir,
                exit_code=23,
            )
            self.assertEqual(result.returncode, 23, result.stderr)

    def test_unique_state_dirs(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            r1 = self._run_dispatch(
                tmpdir, prompt, str(tmpdir / "r.md"), "u", codex, log_dir
            )
            r2 = self._run_dispatch(
                tmpdir, prompt, str(tmpdir / "r.md"), "u", codex, log_dir
            )
            self.assertNotEqual(_parse_state_dir(r1.stdout),
                                _parse_state_dir(r2.stdout))

    def test_missing_prompt_file_exits_two(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, _, log_dir = self._fresh_fixture(tmpdir)
            result = self._run_dispatch(
                tmpdir, tmpdir / "nope.txt", str(tmpdir / "r.md"), "u",
                codex, log_dir,
            )
            self.assertEqual(result.returncode, 2, result.stderr)

    def test_bad_unit_id_exits_two(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            codex, prompt, log_dir = self._fresh_fixture(tmpdir)
            result = self._run_dispatch(
                tmpdir, prompt, str(tmpdir / "r.md"), "bad id!", codex, log_dir
            )
            self.assertEqual(result.returncode, 2,
                             f"non-alnum unit-id must exit 2\nSTDERR:\n{result.stderr}")

    def test_missing_required_arg_exits_two(self) -> None:
        if self.SHELL_KIND == "bash":
            cmd = [BASH, str(DISPATCH_SH), "--prompt-file", "x.txt"]
        else:
            cmd = [
                PS_SHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(DISPATCH_PS1), "--prompt-file", "x.txt",
            ]
        result = subprocess.run(cmd, capture_output=True, text=True,
                                check=False, timeout=30)
        self.assertEqual(result.returncode, 2, result.stderr)


@unittest.skipIf(
    sys.platform.startswith("win"),
    "bash skipped on Windows: Git Bash POSIX-translates env-var temp paths, "
    "which breaks path comparison from Python's Windows-path perspective. "
    "CI Linux + Spark cover this lane.",
)
@unittest.skipUnless(BASH, "bash not on PATH")
class DispatchTaskBashTests(_DispatchTaskContractMixin, unittest.TestCase):
    SHELL_KIND = "bash"


@unittest.skipUnless(
    PS_SHELL and sys.platform.startswith("win"),
    "PowerShell dispatch tests are Windows-only.",
)
class DispatchTaskPowerShellTests(_DispatchTaskContractMixin, unittest.TestCase):
    SHELL_KIND = "powershell"


class DispatchTaskScriptsTracked(unittest.TestCase):
    def test_sh_exists(self) -> None:
        self.assertTrue(DISPATCH_SH.exists(), f"missing: {DISPATCH_SH}")

    def test_ps1_exists(self) -> None:
        self.assertTrue(DISPATCH_PS1.exists(), f"missing: {DISPATCH_PS1}")

    def test_reap_watch_ps1_exists(self) -> None:
        # Windows watchdog lives in its own file (AMSI split); see reaper contract test.
        self.assertTrue(REAP_WATCH_PS1.exists(), f"missing: {REAP_WATCH_PS1}")


class DispatchTaskStaticContract(unittest.TestCase):
    """Freeze the safety wiring so a refactor that drops a flag fails here."""

    def _both(self):
        return [DISPATCH_SH.read_text(encoding="utf-8"),
                DISPATCH_PS1.read_text(encoding="utf-8")]

    def test_sandbox_flag_present(self) -> None:
        for text in self._both():
            self.assertIn("--sandbox", text)
            self.assertIn("CODEX_DISPATCH_SANDBOX", text)
            self.assertIn("danger-full-access", text)

    def test_mcp_isolation_present(self) -> None:
        for text in self._both():
            self.assertIn("CODEX_DISPATCH_ISOLATE_MCP", text)
            self.assertIn("--ignore-user-config", text)
            self.assertIn("model_reasoning_effort", text)

    def test_scratch_cwd_present(self) -> None:
        for text in self._both():
            self.assertIn("PRUN_SCRATCH_CWD", text)

    def test_skip_git_repo_check_present(self) -> None:
        # The scratch cwd is intentionally not a git repo; codex needs this.
        for text in self._both():
            self.assertIn("--skip-git-repo-check", text)

    def test_dispatch_reaper_contract_present(self) -> None:
        # The .sh enforces the idle-stall + hard-timeout watchdog inline. The .ps1 side
        # splits it out into reap-watch.ps1: a single .ps1 that launches a hidden worker
        # AND polls it AND force-kills its tree trips some Windows AV AMSI heuristics and
        # is blocked at parse, so dispatch-task.ps1 keeps the env contract + exit 124 and
        # delegates the watch/kill to reap-watch.ps1 (the dispatch-codex + stall-watch split).
        sh = DISPATCH_SH.read_text(encoding="utf-8")
        for token in ("PRUN_STALL_THRESHOLD", "CODEX_DISPATCH_TIMEOUT",
                      "idle-stall", "hard-timeout", "124"):
            self.assertIn(token, sh, f"dispatch-task.sh missing {token}")

        ps1 = DISPATCH_PS1.read_text(encoding="utf-8")
        for token in ("PRUN_STALL_THRESHOLD", "CODEX_DISPATCH_TIMEOUT", "124", "reap-watch"):
            self.assertIn(token, ps1, f"dispatch-task.ps1 missing {token}")

        reap = REAP_WATCH_PS1.read_text(encoding="utf-8")
        for token in ("PRUN_STALL_THRESHOLD", "CODEX_DISPATCH_TIMEOUT",
                      "idle-stall", "hard-timeout", "reap-reason", "taskkill"):
            self.assertIn(token, reap, f"reap-watch.ps1 missing {token}")

    def test_reexec_guard_present_in_sh_only(self) -> None:
        """The .sh releases its own deployed path before it starts the worker
        (anywhere-agents#43). The .ps1 deliberately does not: PowerShell
        releases a parsed script file, and re-executing it would force a
        source-directory handoff for its reap-watch.ps1 lookup, which is risk
        with no measured lock behind it."""
        sh = DISPATCH_SH.read_text(encoding="utf-8")
        for token in ("PRUN_DISPATCH_REEXEC", "prun-dispatch-task-reexec-",
                      'cp -- "$0"', "unset PRUN_DISPATCH_REEXEC"):
            self.assertIn(token, sh, f"dispatch-task.sh missing {token}")

        ps1 = DISPATCH_PS1.read_text(encoding="utf-8")
        self.assertNotIn(
            "PRUN_DISPATCH_REEXEC", ps1,
            "the PowerShell dispatcher does not need the re-exec guard",
        )


@unittest.skipUnless(
    sys.platform.startswith("win") and GIT_BASH,
    "the deployed-path release is a Windows file-sharing property; needs Git Bash",
)
class DispatchTaskReleasesDeployedPath(unittest.TestCase):
    """A live fan-out must not block a redeploy of its own dispatcher.

    Windows refuses a rename over a file another process holds open without
    FILE_SHARE_DELETE, and a shell holds a script open for as long as it is
    executing it. The composer deploys skill files by rename, so before the
    re-exec guard a running worker aborted the whole compose transaction at
    this one file (anywhere-agents#43).

    Both tests run the real script from a copied "deployed" path against a mock
    codex that sleeps, then attempt the rename the composer would attempt. The
    second is a control: it pre-sets the sentinel so the guard is skipped, and
    asserts the rename is still refused. If that control ever stops failing,
    Git Bash has changed its sharing mode and the guard's premise is worth
    rechecking rather than trusting.

    This class does not extend the bash contract mixin, which skips on Windows
    because Git Bash POSIX-translates env-var temp paths and that breaks its
    path comparisons. Nothing here compares a path the shell produced.
    """

    WORKER_SLEEP_SECONDS = "8"
    REPLACEMENT_BODY = "#!/usr/bin/env bash\nexit 0\n"

    def _fixture(self, tmpdir: Path):
        deployed_dir = tmpdir / "deployed"
        deployed_dir.mkdir()
        deployed = deployed_dir / "dispatch-task.sh"
        shutil.copyfile(DISPATCH_SH, deployed)
        log_dir = tmpdir / "mock-log"
        log_dir.mkdir()
        codex = _write_mock_codex(tmpdir, want_powershell_shim=False)
        prompt = tmpdir / "prompt.txt"
        prompt.write_text("TASK PROMPT body\n", encoding="utf-8")
        return deployed, codex, prompt, log_dir

    def _spawn(self, tmpdir: Path, deployed: Path, codex: Path, prompt: Path,
               log_dir: Path, extra_env: dict[str, str] | None = None):
        env = os.environ.copy()
        env["CODEX_BIN"] = str(codex)
        env["MOCK_CODEX_LOG"] = str(log_dir)
        env["MOCK_CODEX_EXIT"] = "0"
        env["MOCK_CODEX_SLEEP"] = self.WORKER_SLEEP_SECONDS
        # Git Bash reads these as shell strings, where a Windows backslash
        # is an escape character. Hand it the forward-slash spelling so the
        # state directory it creates is a path Python can find again.
        posix_tmp = str(tmpdir).replace(chr(92), "/")
        env["TMPDIR"] = posix_tmp
        env["TEMP"] = posix_tmp
        env["TMP"] = posix_tmp
        env.pop("PRUN_SCRATCH_CWD", None)
        if extra_env:
            env.update(extra_env)
        return subprocess.Popen(
            [GIT_BASH, str(deployed),
             "--prompt-file", str(prompt),
             "--result-file", str(tmpdir / "result.md"),
             "--unit-id", "u_lock"],
            cwd=str(tmpdir), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )

    def _wait_for_worker(self, log_dir: Path, proc, timeout: float = 30.0) -> None:
        """Block until the mock worker has started and is inside its sleep."""
        args_file = log_dir / "args"
        deadline = time.time() + timeout
        while time.time() < deadline:
            if args_file.exists():
                return
            if proc.poll() is not None:
                out, err = proc.communicate()
                raise AssertionError(
                    "dispatch exited before the worker started "
                    "(rc=%s)\nSTDOUT:\n%s\nSTDERR:\n%s"
                    % (proc.returncode, out, err)
                )
            time.sleep(0.1)
        proc.kill()
        raise AssertionError("mock worker never started")

    def _replacement(self, tmpdir: Path) -> Path:
        path = tmpdir / "replacement.sh"
        path.write_text(self.REPLACEMENT_BODY, encoding="utf-8")
        return path

    def test_deployed_path_is_replaceable_while_a_worker_runs(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            deployed, codex, prompt, log_dir = self._fixture(tmpdir)
            proc = self._spawn(tmpdir, deployed, codex, prompt, log_dir)
            try:
                self._wait_for_worker(log_dir, proc)
                # The composer's own operation, at the moment it used to fail.
                os.replace(self._replacement(tmpdir), deployed)
                self.assertEqual(
                    deployed.read_text(encoding="utf-8"),
                    self.REPLACEMENT_BODY,
                    "the replacement did not land at the deployed path",
                )
            finally:
                stdout, stderr = proc.communicate(timeout=90)
            self.assertEqual(
                proc.returncode, 0,
                "STDOUT:\n%s\nSTDERR:\n%s" % (stdout, stderr),
            )
            self.assertTrue(stdout.startswith("STATE-DIR "),
                            "first stdout line: %s" % (stdout.splitlines()[:1],))
            leftovers = list(tmpdir.glob("prun-dispatch-task-reexec-*"))
            self.assertEqual(leftovers, [],
                             "re-exec dir was not cleaned up: %s" % (leftovers,))

    def test_without_the_guard_the_rename_is_refused(self) -> None:
        """Control. Pre-setting the sentinel makes the dispatcher run from the
        deployed path, which is what it did before the guard existed."""
        with _temp_dir() as td:
            tmpdir = Path(td)
            deployed, codex, prompt, log_dir = self._fixture(tmpdir)
            proc = self._spawn(tmpdir, deployed, codex, prompt, log_dir,
                               extra_env={"PRUN_DISPATCH_REEXEC": "1"})
            try:
                self._wait_for_worker(log_dir, proc)
                with self.assertRaises(PermissionError):
                    os.replace(self._replacement(tmpdir), deployed)
            finally:
                proc.communicate(timeout=90)


@unittest.skipUnless(
    sys.platform.startswith("win") and GIT_BASH,
    "the deployed-path release is a Windows file-sharing property; needs Git Bash",
)
class PrunLongRunningScriptsReleaseDeployedPath(unittest.TestCase):
    """monitor.sh and gather.sh are the other two long-lived Bash holders.

    Each can run for an hour, and skill files are staged in sorted path order
    while the transaction stops at its first failure, so dispatch-task.sh sat in
    front of both and hid them. They carry the same private-copy guard, and this
    is the same live-replacement proof without a codex mock: both scripts poll on
    their own and announce themselves on the first stdout line.
    """

    RUN_SECONDS = "6"
    REPLACEMENT_BODY = "#!/usr/bin/env bash\nexit 0\n"

    def _spawn(self, tmpdir, script_name, args, env_extra):
        deployed_dir = tmpdir / "deployed"
        deployed_dir.mkdir(exist_ok=True)
        deployed = deployed_dir / script_name
        shutil.copyfile(SCRIPTS_DIR / script_name, deployed)
        env = os.environ.copy()
        # Git Bash reads these as shell strings, where a Windows backslash
        # is an escape character. Hand it the forward-slash spelling so the
        # state directory it creates is a path Python can find again.
        posix_tmp = str(tmpdir).replace(chr(92), "/")
        env["TMPDIR"] = posix_tmp
        env["TEMP"] = posix_tmp
        env["TMP"] = posix_tmp
        env.update(env_extra)
        proc = subprocess.Popen(
            [GIT_BASH, str(deployed)] + args,
            cwd=str(tmpdir), env=env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        return deployed, proc

    def _replace_while_running(self, tmpdir, deployed, proc, expected_first_token):
        """Wait for the script to announce itself, perform the rename the
        composer would perform, then let it finish on its own."""
        first = proc.stdout.readline()
        self.assertTrue(
            first.startswith(expected_first_token),
            "first stdout line was %r, expected it to start with %r"
            % (first, expected_first_token),
        )
        replacement = tmpdir / "replacement.sh"
        replacement.write_text(self.REPLACEMENT_BODY, encoding="utf-8")
        os.replace(replacement, deployed)
        self.assertEqual(deployed.read_text(encoding="utf-8"), self.REPLACEMENT_BODY)
        proc.communicate(timeout=60)

    def test_monitor_releases_its_deployed_path(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            state_dir = tmpdir / "unit-state"
            state_dir.mkdir()
            (state_dir / "tail").write_text("", encoding="utf-8")
            (state_dir / "result-file").write_text(
                str(tmpdir / "never.md"), encoding="utf-8")
            deployed, proc = self._spawn(
                tmpdir, "monitor.sh", [str(state_dir)],
                {"PRUN_MONITOR_TIMEOUT": self.RUN_SECONDS, "PRUN_MONITOR_POLL": "1"},
            )
            self._replace_while_running(tmpdir, deployed, proc, "MONITOR-START")
            self.assertEqual(list(tmpdir.glob("prun-monitor-reexec-*")), [])

    def test_gather_releases_its_deployed_path(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            deployed, proc = self._spawn(
                tmpdir, "gather.sh", [str(tmpdir / "never.md")],
                {"AGENT_CONFIG_GATHER_TIMEOUT": self.RUN_SECONDS,
                 "PRUN_GATHER_POLL": "1"},
            )
            self._replace_while_running(tmpdir, deployed, proc, "GATHER-START")
            self.assertEqual(list(tmpdir.glob("prun-gather-reexec-*")), [])


@unittest.skipUnless(
    sys.platform.startswith("win") and GIT_BASH,
    "the Bash contract mixin skips on Windows; these pin the wrapper contract",
)
class DispatchTaskWrapperProcessContract(unittest.TestCase):
    """The private-copy hand-off puts a command-string parent above the real
    dispatcher, so the contract the caller sees has to survive one more process.

    The Bash contract mixin skips on Windows, which is the only platform where
    the wrapper exists for a reason, so these four assertions would otherwise
    have no permanent home: exit-status propagation, both reaper exits, and what
    dispatch-pid now names.
    """

    def _fixture(self, tmpdir):
        log_dir = tmpdir / "mock-log"
        log_dir.mkdir()
        codex = _write_mock_codex(tmpdir, want_powershell_shim=False)
        prompt = tmpdir / "prompt.txt"
        prompt.write_text("TASK PROMPT body\n", encoding="utf-8")
        env = os.environ.copy()
        env["CODEX_BIN"] = str(codex)
        env["MOCK_CODEX_LOG"] = str(log_dir)
        # Git Bash reads these as shell strings, where a Windows backslash
        # is an escape character. Hand it the forward-slash spelling so the
        # state directory it creates is a path Python can find again.
        posix_tmp = str(tmpdir).replace(chr(92), "/")
        env["TMPDIR"] = posix_tmp
        env["TEMP"] = posix_tmp
        env["TMP"] = posix_tmp
        env.pop("PRUN_SCRATCH_CWD", None)
        return prompt, env

    def _cmd(self, tmpdir, prompt, unit_id):
        return [GIT_BASH, str(DISPATCH_SH),
                "--prompt-file", str(prompt),
                "--result-file", str(tmpdir / "result.md"),
                "--unit-id", unit_id]

    def _run(self, tmpdir, env_extra=None, timeout=120.0):
        prompt, env = self._fixture(tmpdir)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            self._cmd(tmpdir, prompt, "u_wrap"),
            cwd=str(tmpdir), env=env, capture_output=True, text=True,
            check=False, timeout=timeout,
        )

    def test_worker_exit_status_propagates_through_the_wrapper(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            result = self._run(tmpdir, {"MOCK_CODEX_EXIT": "23"})
            self.assertEqual(result.returncode, 23, result.stderr)

    def test_idle_stall_reap_still_exits_124(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            result = self._run(tmpdir, {"MOCK_CODEX_SLEEP": "30",
                                        "PRUN_STALL_THRESHOLD": "3"})
            self.assertEqual(result.returncode, 124, result.stderr)
            self.assertIn("idle-stall", result.stderr)

    def test_hard_timeout_reap_still_exits_124(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            result = self._run(tmpdir, {"MOCK_CODEX_SLEEP": "30",
                                        "CODEX_DISPATCH_TIMEOUT": "3"})
            self.assertEqual(result.returncode, 124, result.stderr)
            self.assertIn("hard-timeout", result.stderr)

    def test_dispatch_pid_names_the_private_copy_and_reads_as_live(self) -> None:
        """dispatch-pid is the private copy PID, not the PID of the process the
        caller launched. monitor.sh tests that value for liveness, so the wrapper
        must not make a running unit look dead."""
        with _temp_dir() as td:
            tmpdir = Path(td)
            prompt, env = self._fixture(tmpdir)
            env["MOCK_CODEX_SLEEP"] = "12"
            proc = subprocess.Popen(
                self._cmd(tmpdir, prompt, "u_pid"),
                cwd=str(tmpdir), env=env,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            )
            try:
                # Find the state dir by glob rather than by parsing the live
                # stdout pipe. Reading the STATE-DIR line and using that path
                # was measured not to resolve here, which is the same class of
                # Windows path mismatch that makes the shared Bash contract
                # mixin skip on this platform. A glob under the test's own
                # temp dir does not depend on the spelling the shell emits.
                deadline = time.time() + 30
                pid_file = None
                while time.time() < deadline:
                    found = list(tmpdir.glob("prun-task-*-u_pid-*/dispatch-pid"))
                    if found:
                        pid_file = found[0]
                        break
                    time.sleep(0.1)
                self.assertIsNotNone(
                    pid_file,
                    "no prun-task-*-u_pid-*/dispatch-pid appeared under %s; "
                    "tmpdir held %s" % (tmpdir, sorted(p.name for p in tmpdir.iterdir())),
                )
                state_dir = pid_file.parent
                recorded = int(pid_file.read_text(encoding="utf-8").strip())
                self.assertGreater(recorded, 0)
                self.assertNotEqual(
                    recorded, proc.pid,
                    "dispatch-pid must name the private copy, not the wrapper",
                )
                monitor_env = dict(env)
                monitor_env["PRUN_MONITOR_TIMEOUT"] = "3"
                monitor_env["PRUN_MONITOR_POLL"] = "1"
                # monitor.sh reads dispatch-pid only once a unit has been quiet
                # for the stall threshold. At the default 600 seconds it reports
                # the unit as growing and never looks at the PID, so asserting
                # only the absence of failed(dispatch-dead) would pass without
                # testing anything. Drop the threshold so the branch is entered,
                # and assert the reached state positively before the negative.
                monitor_env["PRUN_STALL_THRESHOLD"] = "1"
                monitor = subprocess.run(
                    [GIT_BASH, str(SCRIPTS_DIR / "monitor.sh"), str(state_dir)],
                    cwd=str(tmpdir), env=monitor_env,
                    capture_output=True, text=True, check=False, timeout=60,
                )
                self.assertEqual(monitor.returncode, 3,
                                 monitor.stdout + monitor.stderr)
                self.assertIn(
                    "stalled(", monitor.stdout,
                    "monitor never reached its liveness branch: " + monitor.stdout,
                )
                self.assertNotIn(
                    "failed(dispatch-dead)", monitor.stdout,
                    "monitor read a live unit as dead: " + monitor.stdout,
                )
            finally:
                proc.communicate(timeout=120)


if __name__ == "__main__":
    unittest.main()
