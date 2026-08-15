"""Contract tests for prun's state-directory-keyed orphan reapers."""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path

from test_dispatch_task import (
    BASH,
    DISPATCH_PS1,
    DISPATCH_SH,
    PS_SHELL,
    _temp_dir,
    _write_mock_codex,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "skills" / "prun" / "scripts"
REAP_SH = SCRIPTS_DIR / "reap-orphans.sh"
REAP_PS1 = SCRIPTS_DIR / "reap-orphans.ps1"
WINDOWS_POWERSHELL = shutil.which("powershell.exe")


def _pid_alive(pid: int) -> bool:
    if sys.platform.startswith("win"):
        import ctypes
        from ctypes import wintypes

        process_query_limited_information = 0x1000
        still_active = 259
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_limited_information, False, pid
        )
        if not handle:
            return False
        try:
            exit_code = wintypes.DWORD()
            if not ctypes.windll.kernel32.GetExitCodeProcess(
                handle, ctypes.byref(exit_code)
            ):
                return False
            return exit_code.value == still_active
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)

    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    proc_stat = Path(f"/proc/{pid}/stat")
    if proc_stat.exists():
        try:
            if proc_stat.read_text(encoding="utf-8").split()[2] == "Z":
                return False
        except (OSError, IndexError):
            pass
    return True


def _wait_for(predicate, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.1)
    return predicate()


def _windows_process_start_ticks(process: subprocess.Popen[str]) -> int:
    import ctypes
    from ctypes import wintypes

    creation = wintypes.FILETIME()
    exit_time = wintypes.FILETIME()
    kernel_time = wintypes.FILETIME()
    user_time = wintypes.FILETIME()
    handle = wintypes.HANDLE(int(process._handle))
    if not ctypes.windll.kernel32.GetProcessTimes(
        handle,
        ctypes.byref(creation),
        ctypes.byref(exit_time),
        ctypes.byref(kernel_time),
        ctypes.byref(user_time),
    ):
        raise ctypes.WinError()
    filetime = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
    return filetime + 504_911_232_000_000_000


def _windows_deny_process_terminate(process: subprocess.Popen[str]) -> None:
    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    convert = advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW
    convert.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPVOID),
        ctypes.POINTER(wintypes.DWORD),
    ]
    convert.restype = wintypes.BOOL
    set_security = advapi32.SetKernelObjectSecurity
    set_security.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID]
    set_security.restype = wintypes.BOOL

    descriptor = wintypes.LPVOID()
    try:
        # Deny new terminate handles while preserving query and wait access.
        sddl = "D:(D;;0x00000001;;;WD)(A;;0x00121400;;;WD)"
        if not convert(sddl, 1, ctypes.byref(descriptor), None):
            raise ctypes.WinError(ctypes.get_last_error())
        if not set_security(int(process._handle), 0x4, descriptor):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        if descriptor:
            kernel32.LocalFree(descriptor)


def _stop_popen(process: subprocess.Popen[str] | None) -> None:
    if process is None:
        return
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
    if process.stdout is not None:
        process.stdout.close()
    if process.stderr is not None:
        process.stderr.close()


def _stop_worker_tree(pid: int | None) -> None:
    if pid is None or not _pid_alive(pid):
        return
    if sys.platform.startswith("win"):
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=10,
        )
        return
    try:
        if os.getpgid(pid) == pid:
            os.killpg(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _start_bash_term_tree(
    tmpdir: Path,
) -> tuple[subprocess.Popen[str], str, int, str, int, int]:
    identity_path = tmpdir / "bash-tree-identity"
    fixture = tmpdir / "bash-term-tree.sh"
    fixture.write_text(
        "#!/usr/bin/env bash\n"
        "identity_path=$1\n"
        "trap 'exit 0' TERM\n"
        "bash -c 'trap \"\" TERM; while :; do sleep 1; done' &\n"
        "child_pid=$!\n"
        "if [ -r /proc/$$/stat ]; then\n"
        "  IFS= read -r root_line < /proc/$$/stat\n"
        "  root_rest=${root_line##*)}\n"
        "  set -- $root_rest\n"
        "  root_start=${20}\n"
        "  root_pgid=$3\n"
        "else\n"
        "  root_start=$(ps -o lstart= -p $$ | sed -e 's/^[[:space:]]*//' "
        "-e 's/[[:space:]]*$//')\n"
        "  root_pgid=$(ps -o pgid= -p $$ | tr -d '[:space:]')\n"
        "fi\n"
        "case $(uname -s) in\n"
        "  MINGW*|MSYS*|CYGWIN*)\n"
        "    scheme=msys\n"
        "    IFS= read -r host_child_pid < /proc/$child_pid/winpid\n"
        "    ;;\n"
        "  *) scheme=posix; host_child_pid=$child_pid ;;\n"
        "esac\n"
        "printf '%s\\t%s\\t%s\\t%s\\t%s\\n' \"$scheme\" \"$$\" "
        "\"$root_start\" \"$root_pgid\" \"$host_child_pid\" > \"$identity_path\"\n"
        "while :; do sleep 1; done\n",
        encoding="utf-8",
    )
    popen_args: dict[str, object] = {}
    if not sys.platform.startswith("win"):
        popen_args["start_new_session"] = True
    root = subprocess.Popen(
        [BASH, fixture.as_posix(), identity_path.as_posix()],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        **popen_args,
    )
    if not _wait_for(lambda: identity_path.exists() and identity_path.stat().st_size > 0):
        stderr = root.stderr.read() if root.stderr else ""
        _stop_popen(root)
        raise AssertionError(f"bash tree did not record its identity: {stderr}")
    scheme, root_pid, root_start, root_pgid, host_child_pid = (
        identity_path.read_text(encoding="utf-8").strip().split("\t")
    )
    return root, scheme, int(root_pid), root_start, int(root_pgid), int(host_child_pid)


class _ReapOrphansContractMixin:
    DISPATCH_KIND: str = ""
    REAPER_KIND: str = ""

    def _state_dir_from_output(self, raw_path: str) -> Path:
        if not (sys.platform.startswith("win") and self.DISPATCH_KIND == "bash"):
            return Path(raw_path)
        converted = subprocess.run(
            [BASH, "-lc", 'cygpath -w -- "$1"', "convert", raw_path],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        if converted.returncode != 0 or not converted.stdout.strip():
            raise unittest.SkipTest(
                "Git Bash cygpath could not map the shared /tmp state directory "
                "to its Windows path."
            )
        return Path(converted.stdout.strip())

    def _identity_parts(self, state_dir: Path, name: str = "worker-roots") -> list[str]:
        return (state_dir / name).read_text(encoding="utf-8").splitlines()[0].split("\t")

    def _host_worker_pid(self, state_dir: Path) -> int:
        parts = self._identity_parts(state_dir)
        if parts[0] == "msys":
            return int(parts[3])
        return int(parts[1])

    def _reported_worker_pid(self, state_dir: Path) -> int:
        parts = self._identity_parts(state_dir)
        if parts[0] == "msys" and self.REAPER_KIND == "powershell":
            return int(parts[3])
        return int(parts[1])

    def _dispatch_background(
        self, tmpdir: Path, unit_id: str = "orphan"
    ) -> tuple[subprocess.Popen[str], Path, int]:
        log_dir = tmpdir / f"mock-log-{unit_id}"
        log_dir.mkdir()
        codex_bin = _write_mock_codex(
            tmpdir, want_powershell_shim=(self.DISPATCH_KIND == "powershell")
        )
        prompt = tmpdir / f"prompt-{unit_id}.txt"
        prompt.write_text("orphan reaper fixture\n", encoding="utf-8")
        result_file = tmpdir / f"result-{unit_id}.md"

        if self.DISPATCH_KIND == "bash":
            cmd = [
                BASH, str(DISPATCH_SH),
                "--prompt-file", str(prompt),
                "--result-file", str(result_file),
                "--unit-id", unit_id,
            ]
        elif self.DISPATCH_KIND == "powershell":
            cmd = [
                PS_SHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(DISPATCH_PS1),
                "--prompt-file", str(prompt),
                "--result-file", str(result_file),
                "--unit-id", unit_id,
            ]
        else:
            raise AssertionError(f"unknown dispatch kind: {self.DISPATCH_KIND}")

        env = os.environ.copy()
        env.update({
            "CODEX_BIN": str(codex_bin),
            "MOCK_CODEX_LOG": str(log_dir),
            "MOCK_CODEX_SLEEP": "60",
            "PRUN_STALL_THRESHOLD": "300",
            "CODEX_DISPATCH_TIMEOUT": "0",
            "TMPDIR": str(tmpdir),
            "TEMP": str(tmpdir),
            "TMP": str(tmpdir),
        })
        env.pop("PRUN_SCRATCH_CWD", None)
        dispatcher = subprocess.Popen(
            cmd,
            cwd=str(tmpdir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if dispatcher.stdout is None:
            _stop_popen(dispatcher)
            raise AssertionError("dispatcher stdout pipe was not created")
        first_line = dispatcher.stdout.readline().strip()
        if not first_line.startswith("STATE-DIR "):
            stderr = dispatcher.stderr.read() if dispatcher.stderr else ""
            _stop_popen(dispatcher)
            raise AssertionError(
                f"missing STATE-DIR line: {first_line!r}\nSTDERR:\n{stderr}"
            )
        state_dir = self._state_dir_from_output(first_line.removeprefix("STATE-DIR "))
        worker_roots = state_dir / "worker-roots"
        if not _wait_for(
            lambda: worker_roots.exists() and worker_roots.stat().st_size > 0
        ):
            _stop_popen(dispatcher)
            raise AssertionError(f"worker-roots was not recorded: {state_dir}")
        worker_pid = self._host_worker_pid(state_dir)
        return dispatcher, state_dir, worker_pid

    def _run_reaper(
        self, tmpdir: Path, *, dry_run: bool = False,
        state_dirs: tuple[Path, ...] = (),
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if self.REAPER_KIND == "bash":
            cmd = [BASH, str(REAP_SH)]
        elif self.REAPER_KIND == "powershell":
            cmd = [
                PS_SHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(REAP_PS1),
            ]
        else:
            raise AssertionError(f"unknown reaper kind: {self.REAPER_KIND}")
        if dry_run:
            cmd.append("-DryRun" if self.REAPER_KIND == "powershell" else "--dry-run")
        for state_dir in state_dirs:
            cmd.extend(["--state-dir", str(state_dir)])
        env = os.environ.copy()
        env.update({"TMPDIR": str(tmpdir), "TEMP": str(tmpdir), "TMP": str(tmpdir)})
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            cmd,
            cwd=str(tmpdir),
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )

    def _make_orphan(
        self, tmpdir: Path, unit_id: str = "orphan"
    ) -> tuple[subprocess.Popen[str], Path, int]:
        dispatcher, state_dir, worker_pid = self._dispatch_background(tmpdir, unit_id)
        _stop_popen(dispatcher)
        self.assertFalse(_pid_alive(dispatcher.pid), "dispatcher must be gone")
        self.assertTrue(_pid_alive(worker_pid), "worker must survive its dispatcher")
        return dispatcher, state_dir, worker_pid

    def _dead_pid(self) -> int:
        process = subprocess.Popen([sys.executable, "-c", "pass"])
        process.wait(timeout=10)
        self.assertTrue(_wait_for(lambda: not _pid_alive(process.pid)))
        return process.pid

    def _write_windows_orphan_state(
        self, tmpdir: Path, worker: subprocess.Popen[str], unit_id: str
    ) -> Path:
        state_dir = tmpdir / f"prun-task-manual-{unit_id}"
        state_dir.mkdir()
        dispatch_pid = self._dead_pid()
        worker_start = _windows_process_start_ticks(worker)
        (state_dir / "dispatch-pid").write_text(
            f"{dispatch_pid}\n", encoding="utf-8"
        )
        (state_dir / "dispatch-roots").write_text(
            f"win\t{dispatch_pid}\t1\n", encoding="utf-8"
        )
        (state_dir / "worker-roots").write_text(
            f"win\t{worker.pid}\t{worker_start}\n", encoding="utf-8"
        )
        return state_dir

    def test_orphan_worker_is_reaped(self) -> None:
        dispatcher = None
        worker_pid = None
        with _temp_dir() as td:
            tmpdir = Path(td)
            try:
                dispatcher, state_dir, worker_pid = self._make_orphan(tmpdir)
                result = self._run_reaper(tmpdir)
                reported_pid = self._reported_worker_pid(state_dir)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"REAPED {state_dir.name} pid={reported_pid}", result.stdout)
                self.assertTrue(
                    _wait_for(lambda: not _pid_alive(worker_pid)),
                    f"worker PID {worker_pid} survived reap",
                )
            finally:
                _stop_popen(dispatcher)
                _stop_worker_tree(worker_pid)

    def test_live_dispatcher_leaves_worker_alone(self) -> None:
        dispatcher = None
        worker_pid = None
        with _temp_dir() as td:
            tmpdir = Path(td)
            try:
                dispatcher, state_dir, worker_pid = self._dispatch_background(tmpdir, "live")
                result = self._run_reaper(tmpdir)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"LEFT {state_dir.name} dispatcher-alive", result.stdout)
                self.assertTrue(_pid_alive(worker_pid))
            finally:
                _stop_popen(dispatcher)
                _stop_worker_tree(worker_pid)

    def test_unreferenced_process_is_never_touched(self) -> None:
        dispatcher = None
        worker_pid = None
        decoy = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        with _temp_dir() as td:
            tmpdir = Path(td)
            try:
                dispatcher, state_dir, worker_pid = self._make_orphan(tmpdir, "owned")
                result = self._run_reaper(tmpdir)
                reported_pid = self._reported_worker_pid(state_dir)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"REAPED {state_dir.name} pid={reported_pid}", result.stdout)
                self.assertTrue(_wait_for(lambda: not _pid_alive(worker_pid)))
                self.assertIsNone(decoy.poll(), "unreferenced process was terminated")
                self.assertNotIn(str(decoy.pid), result.stdout)
            finally:
                _stop_popen(dispatcher)
                _stop_worker_tree(worker_pid)
                _stop_popen(decoy)

    def test_identity_mismatch_is_not_reaped(self) -> None:
        dispatcher = None
        worker_pid = None
        with _temp_dir() as td:
            tmpdir = Path(td)
            try:
                dispatcher, state_dir, worker_pid = self._make_orphan(
                    tmpdir, "identity"
                )
                parts = self._identity_parts(state_dir)
                token_index = 4 if parts[0] == "msys" and self.REAPER_KIND == "powershell" else 2
                parts[token_index] = "1"
                (state_dir / "worker-roots").write_text(
                    "\t".join(parts) + "\n", encoding="utf-8"
                )
                result = self._run_reaper(tmpdir)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"LEFT {state_dir.name} identity-mismatch", result.stdout)
                self.assertTrue(_pid_alive(worker_pid))
            finally:
                _stop_popen(dispatcher)
                _stop_worker_tree(worker_pid)

    def test_legacy_two_field_record_is_unverifiable(self) -> None:
        decoy = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        with _temp_dir() as td:
            tmpdir = Path(td)
            try:
                state_dir = tmpdir / "prun-task-manual-legacy"
                state_dir.mkdir()
                (state_dir / "dispatch-pid").write_text(
                    f"{self._dead_pid()}\n", encoding="utf-8"
                )
                (state_dir / "worker-roots").write_text(
                    f"{decoy.pid}\t12345\n", encoding="utf-8"
                )
                result = self._run_reaper(tmpdir)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"LEFT {state_dir.name} unknown-identity", result.stdout)
                self.assertIsNone(decoy.poll())
            finally:
                _stop_popen(decoy)

    def test_foreign_scheme_is_not_reaped(self) -> None:
        decoy = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        with _temp_dir() as td:
            tmpdir = Path(td)
            try:
                state_dir = tmpdir / "prun-task-manual-foreign"
                state_dir.mkdir()
                (state_dir / "dispatch-pid").write_text(
                    f"{self._dead_pid()}\n", encoding="utf-8"
                )
                foreign = "posix" if self.REAPER_KIND == "powershell" else "win"
                (state_dir / "worker-roots").write_text(
                    f"{foreign}\t{decoy.pid}\t12345\n", encoding="utf-8"
                )
                result = self._run_reaper(tmpdir)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"LEFT {state_dir.name} foreign-scheme", result.stdout)
                self.assertIsNone(decoy.poll())
            finally:
                _stop_popen(decoy)

    def test_missing_worker_record_is_reported(self) -> None:
        with _temp_dir() as td:
            tmpdir = Path(td)
            state_dir = tmpdir / "prun-task-manual-missing"
            state_dir.mkdir()
            (state_dir / "dispatch-pid").write_text(
                f"{self._dead_pid()}\n", encoding="utf-8"
            )
            result = self._run_reaper(tmpdir)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"LEFT {state_dir.name} no-worker-record", result.stdout)
            self.assertIn("REAP-DONE reaped=0 left=1", result.stdout)

    def test_dry_run_kills_nothing(self) -> None:
        dispatcher = None
        worker_pid = None
        with _temp_dir() as td:
            tmpdir = Path(td)
            try:
                dispatcher, state_dir, worker_pid = self._make_orphan(tmpdir, "dry")
                result = self._run_reaper(tmpdir, dry_run=True)
                reported_pid = self._reported_worker_pid(state_dir)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"WOULD-REAP {state_dir.name} pid={reported_pid}", result.stdout)
                self.assertTrue(_pid_alive(worker_pid))
            finally:
                _stop_popen(dispatcher)
                _stop_worker_tree(worker_pid)

    def test_state_dir_survives_a_reap(self) -> None:
        dispatcher = None
        worker_pid = None
        with _temp_dir() as td:
            tmpdir = Path(td)
            try:
                dispatcher, state_dir, worker_pid = self._make_orphan(tmpdir, "preserve")
                result = self._run_reaper(tmpdir)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(_wait_for(lambda: not _pid_alive(worker_pid)))
                self.assertTrue(state_dir.is_dir())
                self.assertTrue((state_dir / "tail").is_file())
            finally:
                _stop_popen(dispatcher)
                _stop_worker_tree(worker_pid)


@unittest.skipIf(
    sys.platform.startswith("win"),
    "bash reaper tests are skipped on Windows because Git Bash cannot provide "
    "the native process identity and tree semantics used by the POSIX reaper.",
)
@unittest.skipUnless(BASH, "bash not on PATH")
class ReapOrphansBashTests(_ReapOrphansContractMixin, unittest.TestCase):
    DISPATCH_KIND = "bash"
    REAPER_KIND = "bash"

    def test_failed_termination_is_left(self) -> None:
        dispatcher = None
        worker_pid = None
        with _temp_dir() as td:
            tmpdir = Path(td)
            try:
                dispatcher, state_dir, worker_pid = self._make_orphan(
                    tmpdir, "kill-failed"
                )
                bash_env = tmpdir / "deny-kill.bash"
                bash_env.write_text(
                    "kill() {\n"
                    "    if [ \"$1\" = \"-0\" ]; then command kill \"$@\"; "
                    "else return 1; fi\n"
                    "}\n",
                    encoding="utf-8",
                )
                result = self._run_reaper(
                    tmpdir,
                    state_dirs=(state_dir,),
                    extra_env={"BASH_ENV": str(bash_env)},
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"LEFT {state_dir.name} kill-failed", result.stdout)
                self.assertIn("REAP-DONE reaped=0 left=1", result.stdout)
                self.assertTrue(_pid_alive(worker_pid))
            finally:
                _stop_popen(dispatcher)
                _stop_worker_tree(worker_pid)


@unittest.skipUnless(BASH, "bash not on PATH")
class ReapOrphansBashGroupTests(unittest.TestCase):
    def test_term_exited_root_does_not_hide_live_group_descendant(self) -> None:
        root = None
        root_pid = None
        host_child_pid = None
        with _temp_dir() as td:
            tmpdir = Path(td)
            try:
                (
                    root,
                    scheme,
                    root_pid,
                    root_start,
                    root_pgid,
                    host_child_pid,
                ) = _start_bash_term_tree(tmpdir)
                self.assertEqual(
                    root_pgid,
                    root_pid,
                    "fixture must be an isolated process-group leader",
                )

                state_dir = tmpdir / "prun-task-manual-term-descendant"
                state_dir.mkdir()
                dead_pid = 99_999_999
                (state_dir / "dispatch-pid").write_text(
                    f"{dead_pid}\n", encoding="utf-8"
                )
                if scheme == "msys":
                    dispatch_record = f"msys\t{dead_pid}\t1\t{dead_pid}\t1\n"
                    worker_record = (
                        f"msys\t{root_pid}\t{root_start}\t{root.pid}\t"
                        f"{_windows_process_start_ticks(root)}\n"
                    )
                else:
                    dispatch_record = f"posix\t{dead_pid}\t1\n"
                    worker_record = f"posix\t{root_pid}\t{root_start}\n"
                (state_dir / "dispatch-roots").write_text(
                    dispatch_record, encoding="utf-8"
                )
                (state_dir / "worker-roots").write_text(
                    worker_record, encoding="utf-8"
                )

                kill_marker = tmpdir / "group-kill-attempted"
                bash_env = tmpdir / "deny-group-kill.bash"
                bash_env.write_text(
                    "kill() {\n"
                    "    if [ \"$1\" = \"-KILL\" ]; then\n"
                    "        printf '%s\\n' attempted > \"$REAP_KILL_MARKER\"\n"
                    "        return 1\n"
                    "    fi\n"
                    "    command kill \"$@\"\n"
                    "}\n",
                    encoding="utf-8",
                )
                env = os.environ.copy()
                env.update({
                    "TMPDIR": tmpdir.as_posix(),
                    "TEMP": tmpdir.as_posix(),
                    "TMP": tmpdir.as_posix(),
                    "BASH_ENV": bash_env.as_posix(),
                    "REAP_KILL_MARKER": kill_marker.as_posix(),
                })
                result = subprocess.run(
                    [
                        BASH,
                        REAP_SH.as_posix(),
                        "--state-dir",
                        state_dir.as_posix(),
                    ],
                    cwd=str(tmpdir),
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertTrue(kill_marker.is_file(), result.stdout)
                self.assertIn(
                    f"LEFT {state_dir.name} kill-failed", result.stdout
                )
                self.assertNotIn(f"REAPED {state_dir.name}", result.stdout)
                self.assertTrue(_wait_for(lambda: root.poll() is not None))
                self.assertTrue(
                    _pid_alive(host_child_pid),
                    "the denied KILL must leave the TERM-ignoring descendant alive",
                )
            finally:
                if sys.platform.startswith("win"):
                    _stop_worker_tree(host_child_pid)
                    _stop_worker_tree(root.pid if root else None)
                elif root_pid is not None:
                    try:
                        os.killpg(root_pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                _stop_popen(root)


@unittest.skipUnless(
    PS_SHELL and sys.platform.startswith("win"),
    "PowerShell reaper tests are Windows-only.",
)
class ReapOrphansPowerShellTests(_ReapOrphansContractMixin, unittest.TestCase):
    DISPATCH_KIND = "powershell"
    REAPER_KIND = "powershell"

    def test_failed_termination_is_left(self) -> None:
        worker = None
        with _temp_dir() as td:
            tmpdir = Path(td)
            try:
                worker = subprocess.Popen(
                    [sys.executable, "-c", "import time; time.sleep(60)"]
                )
                state_dir = self._write_windows_orphan_state(
                    tmpdir, worker, "kill-failed"
                )
                _windows_deny_process_terminate(worker)
                result = self._run_reaper(
                    tmpdir,
                    state_dirs=(state_dir,),
                    extra_env={"ComSpec": str(tmpdir / "missing-cmd.exe")},
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"LEFT {state_dir.name} kill-failed", result.stdout)
                self.assertNotIn(f"REAPED {state_dir.name}", result.stdout)
                self.assertIn("REAP-DONE reaped=0 left=1", result.stdout)
                self.assertIsNone(worker.poll())
            finally:
                _stop_popen(worker)

    def test_target_exit_at_termination_boundary_is_worker_exited(self) -> None:
        worker = None
        with _temp_dir() as td:
            tmpdir = Path(td)
            state_dir = tmpdir / "prun-task-manual-boundary-exit"
            reason_path = state_dir / "reap-reason"
            try:
                worker = subprocess.Popen(
                    [
                        sys.executable,
                        "-c",
                        "import pathlib,sys,time\n"
                        "p=pathlib.Path(sys.argv[1])\n"
                        "while not p.exists(): time.sleep(0.001)\n",
                        str(reason_path),
                    ]
                )
                state_dir = self._write_windows_orphan_state(
                    tmpdir, worker, "boundary-exit"
                )
                _windows_deny_process_terminate(worker)
                result = self._run_reaper(
                    tmpdir, state_dirs=(state_dir,)
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"LEFT {state_dir.name} worker-exited", result.stdout)
                self.assertNotIn(f"REAPED {state_dir.name}", result.stdout)
                self.assertTrue(_wait_for(lambda: worker.poll() is not None))
            finally:
                _stop_popen(worker)

    @unittest.skipUnless(
        WINDOWS_POWERSHELL,
        "Windows PowerShell 5.1 is not on PATH.",
    )
    def test_windows_powershell_51_reaps_verified_worker_tree(self) -> None:
        worker = None
        child_pid = None
        with _temp_dir() as td:
            tmpdir = Path(td)
            child_pid_path = tmpdir / "child-pid"
            try:
                worker = subprocess.Popen(
                    [
                        sys.executable,
                        "-c",
                        "import pathlib,subprocess,sys,time\n"
                        "child=subprocess.Popen([sys.executable,'-c',"
                        "'import time; time.sleep(60)'])\n"
                        "pathlib.Path(sys.argv[1]).write_text(str(child.pid),"
                        "encoding='utf-8')\n"
                        "time.sleep(60)\n",
                        str(child_pid_path),
                    ]
                )
                self.assertTrue(
                    _wait_for(
                        lambda: child_pid_path.exists()
                        and child_pid_path.stat().st_size > 0
                    ),
                    "worker did not record its child PID",
                )
                child_pid = int(child_pid_path.read_text(encoding="utf-8"))
                self.assertTrue(_pid_alive(child_pid))
                state_dir = self._write_windows_orphan_state(
                    tmpdir, worker, "powershell-51-tree"
                )
                env = os.environ.copy()
                env.update({
                    "TMPDIR": str(tmpdir),
                    "TEMP": str(tmpdir),
                    "TMP": str(tmpdir),
                })
                result = subprocess.run(
                    [
                        WINDOWS_POWERSHELL,
                        "-NoProfile",
                        "-NonInteractive",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(REAP_PS1),
                        "--state-dir",
                        str(state_dir),
                    ],
                    cwd=str(tmpdir),
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=30,
                )

                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(
                    f"REAPED {state_dir.name} pid={worker.pid}", result.stdout
                )
                self.assertNotIn("kill-failed", result.stdout)
                self.assertTrue(_wait_for(lambda: worker.poll() is not None))
                self.assertTrue(_wait_for(lambda: not _pid_alive(child_pid)))
            finally:
                _stop_worker_tree(child_pid)
                _stop_worker_tree(worker.pid if worker else None)
                _stop_popen(worker)


@unittest.skipUnless(
    BASH and PS_SHELL and sys.platform.startswith("win"),
    "Git Bash dispatch to PowerShell reaper tests are Windows-only.",
)
class ReapOrphansGitBashPowerShellTests(_ReapOrphansContractMixin, unittest.TestCase):
    DISPATCH_KIND = "bash"
    REAPER_KIND = "powershell"

    def test_mismatched_msys_dispatch_pid_is_unknown_identity(self) -> None:
        dispatcher = None
        worker_pid = None
        with _temp_dir() as td:
            tmpdir = Path(td)
            try:
                dispatcher, state_dir, worker_pid = self._make_orphan(
                    tmpdir, "msys-mismatch"
                )
                parts = self._identity_parts(state_dir, "dispatch-roots")
                self.assertEqual(parts[0], "msys")
                parts[1] = str(int(parts[1]) + 1)
                (state_dir / "dispatch-roots").write_text(
                    "\t".join(parts) + "\n", encoding="utf-8"
                )
                result = self._run_reaper(tmpdir, state_dirs=(state_dir,))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"LEFT {state_dir.name} unknown-identity", result.stdout)
                self.assertTrue(_pid_alive(worker_pid))
            finally:
                _stop_popen(dispatcher)
                _stop_worker_tree(worker_pid)


class ReapOrphansStaticContract(unittest.TestCase):
    def _both(self) -> list[str]:
        return [
            REAP_SH.read_text(encoding="utf-8"),
            REAP_PS1.read_text(encoding="utf-8"),
        ]

    def test_both_reapers_exist(self) -> None:
        self.assertTrue(REAP_SH.is_file(), f"missing: {REAP_SH}")
        self.assertTrue(REAP_PS1.is_file(), f"missing: {REAP_PS1}")

    def test_reapers_never_enumerate_or_kill_by_name(self) -> None:
        forbidden = (
            "Get-Process -Name",
            "Stop-Process -Name",
            "pkill",
            "pgrep -f",
            "taskkill /IM",
            "/IM ",
        )
        for text in self._both():
            for token in forbidden:
                self.assertNotIn(token, text)

    def test_reapers_require_dispatch_and_worker_records(self) -> None:
        for text in self._both():
            self.assertIn("dispatch-pid", text)
            self.assertIn("dispatch-roots", text)
            self.assertIn("worker-roots", text)

    def test_windows_reaper_uses_retained_process_object(self) -> None:
        text = REAP_PS1.read_text(encoding="utf-8")
        self.assertEqual(text.count("Get-Process -Id $workerPid"), 1)
        self.assertIn("Get-Win32ProcessRows", text)
        self.assertIn("$entry.Process.Kill()", text)
        self.assertIn("Wait-RetainedProcessTree", text)
        self.assertNotIn(".Kill($true)", text)
        self.assertNotIn("taskkill", text.lower())

    def test_worker_records_are_scheme_tagged(self) -> None:
        dispatch_sh = DISPATCH_SH.read_text(encoding="utf-8")
        dispatch_ps1 = DISPATCH_PS1.read_text(encoding="utf-8")
        self.assertIn("printf 'msys\\t", dispatch_sh)
        self.assertIn("printf 'posix\\t", dispatch_sh)
        self.assertIn('"win`t$($worker.Id)`t$workerStartTicks', dispatch_ps1)


if __name__ == "__main__":
    unittest.main()
