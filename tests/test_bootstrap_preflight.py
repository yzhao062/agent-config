"""Tests for bootstrap preflight and run-ledger behavior.

The preflight runs before any sparse-clone command in either bootstrap path
(fresh-clone OR existing-repo refresh) and fails closed only on confirmed
too-old git. Parse failures default-pass with a stderr warning so unexpected
`git --version` strings (alpha builds, distro suffixes like `2.30.1.windows.1`
or `(Apple Git-141)`) do not block already-modern systems.

These tests stub git via a per-test temp dir prepended to PATH, run the
bootstrap script with AGENT_CONFIG_PREFLIGHT_TEST=1 so the script exits
right after preflight, and assert exit code + stderr shape per case. The ledger
contract is tested at the same boundary because every bootstrap run emits it
before checking git.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SH = ROOT / "bootstrap" / "bootstrap.sh"
BOOTSTRAP_PS1 = ROOT / "bootstrap" / "bootstrap.ps1"


def _resolve_bash() -> str | None:
    """Find a real bash binary, avoiding the Windows WSL launcher stub.

    On Windows, plain `bash` on PATH often resolves to the WSL launcher
    (`C:\\Windows\\System32\\bash.exe` or the WindowsApps shim), which
    requires a WSL distro to be installed and works through a syscall
    broker that breaks PATH stubbing. Prefer the Git for Windows bash.
    """
    # Honor an explicit override first (CI may need this).
    override = os.environ.get("AGENT_PREFLIGHT_BASH")
    if override and os.path.isfile(override):
        return override
    if os.name == "nt":
        candidates = [
            r"C:\Program Files\Git\usr\bin\bash.exe",
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files (x86)\Git\usr\bin\bash.exe",
        ]
        for c in candidates:
            if os.path.isfile(c):
                return c
        # shutil.which may surface the WSL stub on Windows; only trust it
        # if the resolved path is NOT under System32 / WindowsApps.
        found = shutil.which("bash")
        if found:
            low = found.lower()
            if "system32" not in low and "windowsapps" not in low:
                return found
        return None
    return shutil.which("bash")


BASH = _resolve_bash()
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


_POSIX_SANDBOX_TOOLS = (
    "sed", "uname", "printf", "tr", "grep", "cat", "mkdir", "echo", "rm",
    "dirname", "basename", "test", "ls", "head", "tail", "sh", "mv", "cp",
    "chmod", "mktemp", "sleep",
)


def _build_posix_sandbox(parent: Path) -> Path:
    """Create a sandbox bin dir with symlinks to shell utilities, no `git`.

    The default POSIX PATH (`/usr/bin`, `/bin`, `/usr/local/bin`,
    `/opt/homebrew/bin`) ships real git on macOS / Linux CI runners, so
    "missing-git" tests that only strip a stub_dir fail-open. The sandbox
    contains symlinks to a curated set of shell utilities (sed, uname, ...)
    but deliberately does NOT include `git`. Tests prepend the stub_dir
    (if any) and use the sandbox as the rest of PATH.
    """
    sandbox = parent / "sandbox_bin"
    sandbox.mkdir(parents=True, exist_ok=True)
    for tool in _POSIX_SANDBOX_TOOLS:
        src = shutil.which(tool)
        if src:
            link = sandbox / tool
            if not link.exists():
                try:
                    os.symlink(src, link)
                except (OSError, NotImplementedError):
                    # Filesystem cannot symlink; copy instead.
                    shutil.copy2(src, link)
    return sandbox


def _stripped_env(stub_dir: Path | None) -> dict[str, str]:
    """Build an env where PATH includes ONLY directories needed for bash
    builtins (sed, printf, sh) and the test stub_dir (if any).

    On Windows the Git Bash bash needs `Git\\usr\\bin` for sed/printf; we
    intentionally exclude `Git\\bin`, `Git\\cmd`, and `Git\\mingw64\\bin`
    because those contain the real `git` binary and would defeat the
    missing-git / stubbed-version scenarios.

    On POSIX we build a per-call sandbox bin dir containing symlinks to a
    curated set of shell utilities, and use ONLY that dir (plus the
    optional stub_dir) as PATH. This excludes real git from `/usr/bin`,
    `/usr/local/bin`, `/opt/homebrew/bin`, and any other default location.
    """
    env = os.environ.copy()
    keep_path: list[str] = []
    if os.name == "nt":
        # Always include the bash binary's sibling `usr/bin` so sed/printf
        # are reachable even on hosts where Git for Windows did not put it
        # on PATH directly (e.g., only `Git\cmd` is on PATH). Without this,
        # preflight parser silently default-passes because `sed` is missing
        # and "git 2.24" is treated as unparseable.
        if BASH:
            bash_dir = Path(BASH).resolve().parent
            if bash_dir.name.lower() == "bin" and bash_dir.parent.name.lower() == "usr":
                git_usr_bin = bash_dir
            else:
                git_usr_bin = bash_dir.parent / "usr" / "bin"
            if (git_usr_bin / "sed.exe").is_file():
                keep_path.append(str(git_usr_bin))
        for src in (os.environ.get("PATH") or "").split(os.pathsep):
            src_low = src.lower().rstrip("\\/")
            # Reject every dir that ships a real `git` binary.
            if any(bad in src_low for bad in (
                "system32",
                "windowsapps",
                "git\\cmd",
                "git\\bin",
                "git\\mingw64\\bin",
                "scoop\\apps\\git",
                "github\\bin",
            )):
                continue
            # Keep dirs that ship bash builtins (sed, printf, etc.).
            if any(needle in src_low for needle in (
                "git\\usr\\bin",
                "msys2",
                "msys64",
            )):
                keep_path.append(src)
    else:
        # POSIX: build a sandbox bin dir with no git. Anchor it under the
        # stub_dir's parent so the same temp lifecycle cleans it up; fall
        # back to a fresh tempdir if no stub_dir is provided.
        if stub_dir is not None:
            sandbox = _build_posix_sandbox(stub_dir.parent)
        else:
            sandbox = _build_posix_sandbox(Path(tempfile.mkdtemp(prefix="aa-preflight-sandbox-")))
        keep_path = [str(sandbox)]
    if stub_dir is not None:
        keep_path.insert(0, str(stub_dir))
    env["PATH"] = os.pathsep.join(keep_path)
    # Avoid leaking the developer's persisted upstream / cached repo state.
    env.pop("AGENT_CONFIG_UPSTREAM", None)
    env.pop("AGENT_CONFIG_SKIP_GIT_PREFLIGHT", None)
    env.pop("AGENT_CONFIG_PREFLIGHT_TEST", None)
    return env


def _make_stub_git(stub_dir: Path, version_line: str | None) -> None:
    """Create a stub `git` on PATH that prints `version_line` for `git --version`.

    When `version_line` is None, no stub is created (PATH has no git).
    """
    if version_line is None:
        return
    stub_dir.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        # Windows: ship both a .cmd shim (for cmd-style lookups) and a
        # bash-targeted shell script (for `command -v git` inside Git Bash).
        # Git Bash's command -v walks PATH for executables by name without
        # extension preference, so a bare-name file with #!/bin/sh suffices.
        cmd_path = stub_dir / "git.cmd"
        cmd_path.write_text(
            f"@echo off\r\nif \"%1\"==\"--version\" (\r\n  echo {version_line}\r\n  exit /b 0\r\n)\r\nexit /b 0\r\n",
            encoding="ascii",
        )
        # Bash-style stub for the bootstrap.sh path on Windows (Git Bash).
        sh_path = stub_dir / "git"
        sh_path.write_text(
            f"#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then\n  printf '%s\\n' '{version_line}'\n  exit 0\nfi\nexit 0\n",
            encoding="ascii",
        )
        sh_path.chmod(sh_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    else:
        sh_path = stub_dir / "git"
        sh_path.write_text(
            f"#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then\n  printf '%s\\n' '{version_line}'\n  exit 0\nfi\nexit 0\n",
            encoding="ascii",
        )
        sh_path.chmod(sh_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _run_bootstrap_sh(version_line: str | None, *, scenario: str = "fresh") -> subprocess.CompletedProcess:
    """Run bootstrap.sh with a stubbed git on PATH; capture exit + stderr.

    scenario:
      'fresh': no existing .agent-config/repo/.git
      'existing': pre-create .agent-config/repo/.git so the existing-repo
                  refresh branch would fire first if preflight did NOT gate.
    """
    if not BASH:
        raise unittest.SkipTest("bash not available (Git Bash on Windows or system bash on POSIX)")
    tmp = Path(tempfile.mkdtemp(prefix="aa-preflight-"))
    try:
        stub_dir = tmp / "stub_path"
        _make_stub_git(stub_dir, version_line)
        work = tmp / "work"
        work.mkdir()
        if scenario == "existing":
            (work / ".agent-config" / "repo" / ".git").mkdir(parents=True)
            (work / ".agent-config" / "repo" / ".git" / "config").write_text(
                "[remote \"origin\"]\n  url = https://github.com/example/example.git\n"
            )
        env = _stripped_env(stub_dir if version_line is not None else None)
        env["AGENT_CONFIG_PREFLIGHT_TEST"] = "1"
        # On Windows the env passed to bash needs forward-slash-friendly PATH;
        # subprocess.Popen handles the translation when the program is bash.exe.
        result = subprocess.run(
            [BASH, str(BOOTSTRAP_SH)],
            cwd=str(work),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run_bootstrap_sh_with_ledger(
    version_line: str | None,
    *,
    scenario: str = "fresh",
    upstream: str | None = None,
) -> tuple[subprocess.CompletedProcess, dict | None]:
    """Run bootstrap.sh through preflight and return its parsed ledger."""
    if not BASH:
        raise unittest.SkipTest("bash not available (Git Bash on Windows or system bash on POSIX)")
    tmp = Path(tempfile.mkdtemp(prefix="aa-preflight-ledger-"))
    try:
        stub_dir = tmp / "stub_path"
        _make_stub_git(stub_dir, version_line)
        work = tmp / "work"
        work.mkdir()
        if scenario == "existing":
            (work / ".agent-config" / "repo" / ".git").mkdir(parents=True)
            (work / ".agent-config" / "repo" / ".git" / "config").write_text(
                "[remote \"origin\"]\n  url = https://github.com/example/example.git\n"
            )
        elif scenario == "unwritable":
            (work / ".agent-config").write_text("regular file\n", encoding="utf-8")
        elif scenario != "fresh":
            raise ValueError(f"unknown scenario: {scenario}")
        env = _stripped_env(stub_dir if version_line is not None else None)
        env["AGENT_CONFIG_PREFLIGHT_TEST"] = "1"
        command = [BASH, str(BOOTSTRAP_SH)]
        if upstream is not None:
            if os.name == "nt":
                # Git Bash rewrites quotes in Windows argv. The environment
                # path reaches the same upstream cascade without that rewrite.
                env["AGENT_CONFIG_UPSTREAM"] = upstream
            else:
                command.append(upstream)
        result = subprocess.run(
            command,
            cwd=str(work),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        ledger_path = work / ".agent-config" / "last-run.json"
        ledger = (
            json.loads(ledger_path.read_text(encoding="utf-8"))
            if ledger_path.is_file()
            else None
        )
        return result, ledger
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run_bootstrap_ps1_with_ledger(
    version_line: str | None,
    *,
    scenario: str = "fresh",
    upstream: str | None = None,
) -> tuple[subprocess.CompletedProcess, dict | None]:
    """Run bootstrap.ps1 through preflight and return its parsed ledger."""
    if not POWERSHELL:
        raise unittest.SkipTest("pwsh/powershell not available")
    tmp = Path(tempfile.mkdtemp(prefix="aa-preflight-ledger-ps1-"))
    try:
        stub_dir = tmp / "stub_path"
        _make_stub_git(stub_dir, version_line)
        work = tmp / "work"
        work.mkdir()
        if scenario == "existing":
            (work / ".agent-config" / "repo" / ".git").mkdir(parents=True)
            (work / ".agent-config" / "repo" / ".git" / "config").write_text(
                "[remote \"origin\"]\n  url = https://github.com/example/example.git\n"
            )
        elif scenario == "unwritable":
            (work / ".agent-config").write_text("regular file\n", encoding="utf-8")
        elif scenario != "fresh":
            raise ValueError(f"unknown scenario: {scenario}")
        env = os.environ.copy()
        env["PATH"] = os.pathsep.join((str(stub_dir), env.get("PATH", "")))
        env.pop("AGENT_CONFIG_UPSTREAM", None)
        env.pop("AGENT_CONFIG_SKIP_GIT_PREFLIGHT", None)
        env["AGENT_CONFIG_PREFLIGHT_TEST"] = "1"
        if upstream is not None:
            env["AGENT_CONFIG_UPSTREAM"] = upstream
        result = subprocess.run(
            [POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(BOOTSTRAP_PS1)],
            cwd=str(work),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        ledger_path = work / ".agent-config" / "last-run.json"
        ledger = (
            json.loads(ledger_path.read_text(encoding="utf-8-sig"))
            if ledger_path.is_file()
            else None
        )
        return result, ledger
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _write_executable(path: Path, content: str) -> None:
    # open(newline=) rather than Path.write_text(newline=): the latter kwarg is
    # Python 3.10+, and the CI matrix still covers 3.9. These files are shell
    # stubs handed to a POSIX shell, so the LF ending is load-bearing on
    # Windows checkouts and cannot be left to the platform default.
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _prepare_full_bootstrap_fixture(
    tmp: Path,
    *,
    composer_rc: int | None,
    generator_rc: int | None,
    yaml_available: bool = True,
) -> tuple[Path, Path, Path]:
    work = tmp / "work"
    scripts = work / ".agent-config" / "repo" / "scripts"
    (work / ".agent-config" / "repo" / ".git").mkdir(parents=True)
    scripts.mkdir(parents=True)
    (work / ".agent-config" / "AGENTS.md").write_text("fetched rules\n", encoding="utf-8")
    if composer_rc is not None:
        (scripts / "compose_packs.py").write_text(
            "from pathlib import Path\n"
            "Path('AGENTS.md').write_text('composed rules\\n', encoding='utf-8')\n"
            f"raise SystemExit({composer_rc})\n",
            encoding="utf-8",
        )
    if generator_rc is not None:
        (scripts / "generate_agent_configs.py").write_text(
            "from pathlib import Path\n"
            f"rc = {generator_rc}\n"
            "if rc == 0:\n"
            "    agents = Path('AGENTS.md').read_text(encoding='utf-8')\n"
            "    Path('CLAUDE.md').write_text('generated claude\\n' + agents, encoding='utf-8')\n"
            "    Path('agents').mkdir(exist_ok=True)\n"
            "    Path('agents/codex.md').write_text('generated codex\\n' + agents, encoding='utf-8')\n"
            "raise SystemExit(rc)\n",
            encoding="utf-8",
        )
    python_path = tmp / "python_path"
    python_path.mkdir()
    yaml_stub = "# test PyYAML stand-in\n" if yaml_available else "raise ImportError('PyYAML blocked by test')\n"
    (python_path / "yaml.py").write_text(yaml_stub, encoding="utf-8")
    if not yaml_available:
        (python_path / "pip.py").write_text("raise SystemExit(1)\n", encoding="utf-8")
    home = tmp / "home"
    home.mkdir()
    return work, python_path, home


def _run_full_bootstrap_with_ledger(
    entrypoint: str,
    *,
    composer_rc: int | None = 0,
    generator_rc: int | None = 0,
    yaml_available: bool = True,
) -> tuple[subprocess.CompletedProcess, dict, dict[str, bytes]]:
    if entrypoint == "bash" and not BASH:
        raise unittest.SkipTest("bash not available (Git Bash on Windows or system bash on POSIX)")
    if entrypoint == "powershell" and not POWERSHELL:
        raise unittest.SkipTest("pwsh/powershell not available")
    tmp = Path(tempfile.mkdtemp(prefix=f"aa-generate-ledger-{entrypoint}-"))
    try:
        work, python_path, home = _prepare_full_bootstrap_fixture(
            tmp,
            composer_rc=composer_rc,
            generator_rc=generator_rc,
            yaml_available=yaml_available,
        )
        stub_dir = tmp / "stub_path"
        _make_stub_git(stub_dir, "git version 2.50.0")
        _write_executable(stub_dir / "curl", "#!/bin/sh\nexit 0\n")
        if entrypoint == "bash":
            env = _stripped_env(stub_dir)
            python_command = str(Path(sys.executable)).replace("\\", "/")
            command = [BASH, str(BOOTSTRAP_SH)]
        else:
            env = os.environ.copy()
            env["PATH"] = os.pathsep.join((str(stub_dir), env.get("PATH", "")))
            python_command = sys.executable
            wrapper = tmp / "invoke-bootstrap.ps1"
            bootstrap_literal = str(BOOTSTRAP_PS1).replace("'", "''")
            wrapper.write_text(
                "function Invoke-WebRequest { param([switch]$UseBasicParsing, [string]$Uri, [string]$OutFile) }\n"
                f"& '{bootstrap_literal}'\n"
                "if (-not $?) { exit $LASTEXITCODE }\n"
                "exit 0\n",
                encoding="utf-8",
            )
            command = [POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(wrapper)]
        env.pop("AGENT_CONFIG_PREFLIGHT_TEST", None)
        env["AGENT_CONFIG_UPSTREAM"] = "example/repo"
        env["ANYWHERE_AGENTS_PYTHON"] = python_command
        env["ANYWHERE_AGENTS_CODEX_AUTO_UPDATE"] = "off"
        env["PYTHONPATH"] = str(python_path)
        if not yaml_available:
            env["PIP_NO_INDEX"] = "1"
            env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        result = subprocess.run(
            command,
            cwd=str(work),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        ledger_path = work / ".agent-config" / "last-run.json"
        if not ledger_path.is_file():
            raise AssertionError(
                f"{entrypoint} did not emit a ledger; rc={result.returncode}; stderr={result.stderr!r}"
            )
        ledger = json.loads(ledger_path.read_text(encoding="utf-8-sig"))
        artifacts = {
            relative: (work / relative).read_bytes()
            for relative in ("AGENTS.md", "CLAUDE.md", "agents/codex.md")
            if (work / relative).is_file()
        }
        return result, ledger, artifacts
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run_no_python_bootstrap_with_ledger(
    entrypoint: str,
    *,
    config_text: str | None = None,
    local_config_text: str | None = None,
) -> tuple[subprocess.CompletedProcess, dict, str, bytes, bytes]:
    """Run a full bootstrap where every discoverable Python wrapper is broken."""
    if entrypoint == "bash" and not BASH:
        raise unittest.SkipTest("bash not available (Git Bash on Windows or system bash on POSIX)")
    if entrypoint == "powershell" and not POWERSHELL:
        raise unittest.SkipTest("pwsh/powershell not available")
    tmp = Path(tempfile.mkdtemp(prefix=f"aa-no-python-ledger-{entrypoint}-"))
    try:
        work, _, home = _prepare_full_bootstrap_fixture(
            tmp,
            composer_rc=0,
            generator_rc=0,
        )
        if config_text is not None:
            (work / "agent-config.yaml").write_text(config_text, encoding="utf-8")
        if local_config_text is not None:
            (work / "agent-config.local.yaml").write_text(local_config_text, encoding="utf-8")
        broken_wrapper = "#!/bin/sh\nexit 127\n"
        hooks = home / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        _write_executable(hooks / "_python", broken_wrapper)
        _write_executable(work / ".agent-config" / "repo" / "scripts" / "_python", broken_wrapper)

        stub_dir = tmp / "stub_path"
        _make_stub_git(stub_dir, "git version 2.50.0")
        path_wrapper = stub_dir / "python"
        _write_executable(path_wrapper, broken_wrapper)
        if os.name == "nt":
            (stub_dir / "python.cmd").write_text("@echo off\r\nexit /b 127\r\n", encoding="ascii")
        _write_executable(stub_dir / "curl", "#!/bin/sh\nexit 0\n")

        if entrypoint == "bash":
            env = _stripped_env(stub_dir)
            override = str(path_wrapper).replace("\\", "/")
            command = [BASH, str(BOOTSTRAP_SH)]
        else:
            env = os.environ.copy()
            env["PATH"] = str(stub_dir)
            override = str(path_wrapper)
            wrapper = tmp / "invoke-bootstrap.ps1"
            bootstrap_literal = str(BOOTSTRAP_PS1).replace("'", "''")
            wrapper.write_text(
                "function Invoke-WebRequest { param([switch]$UseBasicParsing, [string]$Uri, [string]$OutFile) }\n"
                f"& '{bootstrap_literal}'\n"
                "if (-not $?) { exit $LASTEXITCODE }\n"
                "exit 0\n",
                encoding="utf-8",
            )
            command = [POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(wrapper)]

        env.pop("AGENT_CONFIG_PREFLIGHT_TEST", None)
        env.pop("CONDA_PREFIX", None)
        env.pop("CONDA_ROOT", None)
        env["AGENT_CONFIG_UPSTREAM"] = "example/repo"
        env["ANYWHERE_AGENTS_PYTHON"] = override
        env["ANYWHERE_AGENTS_CODEX_AUTO_UPDATE"] = "off"
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        result = subprocess.run(
            command,
            cwd=str(work),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        ledger_path = work / ".agent-config" / "last-run.json"
        if not ledger_path.is_file():
            raise AssertionError(
                f"{entrypoint} did not emit a ledger; rc={result.returncode}; stderr={result.stderr!r}"
            )
        raw_ledger = ledger_path.read_text(encoding="utf-8-sig")
        agents_bytes = (work / "AGENTS.md").read_bytes()
        upstream_bytes = (work / ".agent-config" / "AGENTS.md").read_bytes()
        return result, json.loads(raw_ledger), raw_ledger, agents_bytes, upstream_bytes
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run_atomic_helper_deployment(
    entrypoint: str,
) -> tuple[subprocess.CompletedProcess, bytes, bytes, bytes, bool]:
    """Pause a real helper copy mid-write and read the live destination."""
    if entrypoint == "bash" and not BASH:
        raise unittest.SkipTest("bash not available (Git Bash on Windows or system bash on POSIX)")
    if entrypoint == "powershell" and not POWERSHELL:
        raise unittest.SkipTest("pwsh/powershell not available")
    tmp = Path(tempfile.mkdtemp(prefix=f"aa-atomic-helper-{entrypoint}-"))
    try:
        work, python_path, home = _prepare_full_bootstrap_fixture(
            tmp,
            composer_rc=0,
            generator_rc=None,
        )
        source = work / ".agent-config" / "repo" / "scripts" / "_python"
        old_content = b"#!/usr/bin/env bash\n# old helper\nexit 0\n"
        new_content = b"#!/usr/bin/env bash\n# new helper\nexit 0\n"
        source.write_bytes(new_content)
        hooks = home / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        target = hooks / "_python"
        _write_executable(target, old_content.decode("ascii"))
        signal = tmp / "copy-started"

        stub_dir = tmp / "stub_path"
        _make_stub_git(stub_dir, "git version 2.50.0")
        _write_executable(stub_dir / "curl", "#!/bin/sh\nexit 0\n")
        if entrypoint == "bash":
            real_cp = shutil.which("cp")
            if not real_cp and os.name == "nt" and BASH:
                bash_path = Path(BASH).resolve()
                candidates = (
                    bash_path.parent / "cp.exe",
                    bash_path.parent.parent / "usr" / "bin" / "cp.exe",
                )
                real_cp = next((str(path) for path in candidates if path.is_file()), None)
            if not real_cp:
                raise unittest.SkipTest("cp not available for atomic-deployment probe")
            _write_executable(
                stub_dir / "cp",
                "#!/bin/sh\n"
                "source_path=''\n"
                "destination=''\n"
                "for argument in \"$@\"; do\n"
                "  case \"$argument\" in\n"
                "    -*) ;;\n"
                "    *) if [ -z \"$source_path\" ]; then source_path=$argument; else destination=$argument; fi ;;\n"
                "  esac\n"
                "done\n"
                "case \"$source_path\" in\n"
                "  */_python)\n"
                "    printf '%s' partial > \"$destination\"\n"
                "    printf '%s' ready > \"$ATOMIC_COPY_SIGNAL\"\n"
                "    sleep 1\n"
                "    \"$REAL_CP\" -f \"$source_path\" \"$destination\"\n"
                "    ;;\n"
                "  *) exec \"$REAL_CP\" \"$@\" ;;\n"
                "esac\n",
            )
            env = _stripped_env(stub_dir)
            env["REAL_CP"] = str(Path(real_cp).resolve()).replace("\\", "/")
            env["ATOMIC_COPY_SIGNAL"] = str(signal).replace("\\", "/")
            command = [BASH, str(BOOTSTRAP_SH)]
        else:
            env = os.environ.copy()
            env["PATH"] = os.pathsep.join((str(stub_dir), env.get("PATH", "")))
            env["ATOMIC_COPY_SIGNAL"] = str(signal)
            bootstrap_literal = str(BOOTSTRAP_PS1).replace("'", "''")
            wrapper = tmp / "invoke-bootstrap.ps1"
            wrapper.write_text(
                "function Invoke-WebRequest { param([switch]$UseBasicParsing, [string]$Uri, [string]$OutFile) }\n"
                "function Copy-Item {\n"
                "  [CmdletBinding()] param(\n"
                "    [Parameter(Position=0)][string[]]$Path,\n"
                "    [string[]]$LiteralPath,\n"
                "    [Parameter(Position=1)][string]$Destination,\n"
                "    [switch]$Force\n"
                "  )\n"
                "  $sourcePath = if ($LiteralPath) { [string]$LiteralPath[0] } else { [string]$Path[0] }\n"
                "  if ($sourcePath -like '*_python') {\n"
                "    [System.IO.File]::WriteAllText($Destination, 'partial')\n"
                "    [System.IO.File]::WriteAllText($env:ATOMIC_COPY_SIGNAL, 'ready')\n"
                "    Start-Sleep -Seconds 1\n"
                "  }\n"
                "  if ($LiteralPath) {\n"
                "    Microsoft.PowerShell.Management\\Copy-Item -LiteralPath $LiteralPath -Destination $Destination -Force\n"
                "  } else {\n"
                "    Microsoft.PowerShell.Management\\Copy-Item -Path $Path -Destination $Destination -Force\n"
                "  }\n"
                "}\n"
                f"& '{bootstrap_literal}'\n"
                "if (-not $?) { exit $LASTEXITCODE }\n"
                "exit 0\n",
                encoding="utf-8",
            )
            command = [POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(wrapper)]

        env.pop("AGENT_CONFIG_PREFLIGHT_TEST", None)
        env["AGENT_CONFIG_UPSTREAM"] = "example/repo"
        env["ANYWHERE_AGENTS_PYTHON"] = str(Path(sys.executable)).replace("\\", "/") if entrypoint == "bash" else sys.executable
        env["ANYWHERE_AGENTS_CODEX_AUTO_UPDATE"] = "off"
        env["PYTHONPATH"] = str(python_path)
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        process = subprocess.Popen(
            command,
            cwd=str(work),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        deadline = time.monotonic() + 20
        while not signal.is_file() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.005)
        running_when_observed = signal.is_file() and process.poll() is None
        observed = target.read_bytes()
        stdout, stderr = process.communicate(timeout=30)
        result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
        return result, observed, target.read_bytes(), new_content, running_when_observed
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _run_bash_self_update() -> tuple[subprocess.CompletedProcess, bytes, bytes, bytes, dict]:
    """Run bootstrap through its deployed path while it installs a shorter successor."""
    if not BASH:
        raise unittest.SkipTest("bash not available (Git Bash on Windows or system bash on POSIX)")
    tmp = Path(tempfile.mkdtemp(prefix="aa-self-update-bash-"))
    try:
        work, python_path, home = _prepare_full_bootstrap_fixture(
            tmp,
            composer_rc=0,
            generator_rc=None,
        )
        deployed = work / ".agent-config" / "bootstrap.sh"
        original = BOOTSTRAP_SH.read_bytes()
        deployed.write_bytes(original)
        deployed.chmod(deployed.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        replacement = b"#!/bin/sh\n# shorter self-update fixture\nexit 0\n"
        upstream = work / ".agent-config" / "repo" / "bootstrap" / "bootstrap.sh"
        upstream.parent.mkdir(parents=True)
        upstream.write_bytes(replacement)
        upstream.chmod(upstream.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        stub_dir = tmp / "stub_path"
        _make_stub_git(stub_dir, "git version 2.50.0")
        _write_executable(stub_dir / "curl", "#!/bin/sh\nexit 0\n")
        env = _stripped_env(stub_dir)
        env["AGENT_CONFIG_UPSTREAM"] = "example/repo"
        env["ANYWHERE_AGENTS_PYTHON"] = str(Path(sys.executable)).replace("\\", "/")
        env["ANYWHERE_AGENTS_CODEX_AUTO_UPDATE"] = "off"
        env["PYTHONPATH"] = str(python_path)
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        result = subprocess.run(
            [BASH, str(deployed)],
            cwd=str(work),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        ledger = json.loads(
            (work / ".agent-config" / "last-run.json").read_text(encoding="utf-8-sig")
        )
        return result, deployed.read_bytes(), replacement, original, ledger
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class GitPreflightBashTests(unittest.TestCase):

    def test_missing_git_binary_fails(self):
        result = _run_bootstrap_sh(None)
        self.assertNotEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("git is not installed or not on PATH", result.stderr)
        self.assertIn("install:", result.stderr)

    def test_too_old_2_24_fails(self):
        result = _run_bootstrap_sh("git version 2.24.0")
        self.assertNotEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("git 2.24 is too old", result.stderr)
        self.assertIn("install:", result.stderr)

    def test_too_old_1_9_fails(self):
        # Major < 2 must also fail (covers ancient git installs).
        result = _run_bootstrap_sh("git version 1.9.5")
        self.assertNotEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("git 1.9 is too old", result.stderr)

    def test_boundary_2_25_0_passes(self):
        result = _run_bootstrap_sh("git version 2.25.0")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("too old", result.stderr)
        self.assertNotIn("not installed", result.stderr)

    def test_modern_2_50_passes(self):
        result = _run_bootstrap_sh("git version 2.50.0")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_windows_suffix_passes(self):
        # Real format from Git for Windows: `git version 2.30.1.windows.1`.
        result = _run_bootstrap_sh("git version 2.30.1.windows.1")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_apple_suffix_passes(self):
        # Real format from macOS Xcode-bundled git: `git version 2.34.1 (Apple Git-141)`.
        result = _run_bootstrap_sh("git version 2.34.1 (Apple Git-141)")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_release_candidate_passes(self):
        result = _run_bootstrap_sh("git version 2.50.0.rc1")
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_unparseable_version_default_passes(self):
        # Default-pass with stderr warning so unexpected formats don't break modern systems.
        result = _run_bootstrap_sh("git version foo.bar")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("could not parse git version", result.stderr)
        self.assertIn("assuming OK", result.stderr)

    def test_empty_version_default_passes(self):
        # Stub prints nothing for --version; preflight should default-pass.
        if not BASH:
            raise unittest.SkipTest("bash not available")
        tmp = Path(tempfile.mkdtemp(prefix="aa-preflight-"))
        try:
            stub_dir = tmp / "stub_path"
            stub_dir.mkdir(parents=True)
            sh_path = stub_dir / "git"
            sh_path.write_text("#!/bin/sh\nexit 0\n", encoding="ascii")
            sh_path.chmod(sh_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            if os.name == "nt":
                (stub_dir / "git.cmd").write_text("@echo off\r\nexit /b 0\r\n", encoding="ascii")
            work = tmp / "work"
            work.mkdir()
            env = _stripped_env(stub_dir)
            env["AGENT_CONFIG_PREFLIGHT_TEST"] = "1"
            result = subprocess.run(
                [BASH, str(BOOTSTRAP_SH)],
                cwd=str(work),
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("could not parse git version", result.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_existing_repo_path_still_gated(self):
        # If preflight only fired on the fresh-clone branch, an existing
        # .agent-config/repo/.git would slip past with old git. Verify the
        # gate runs first regardless.
        result = _run_bootstrap_sh("git version 2.24.0", scenario="existing")
        self.assertNotEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("git 2.24 is too old", result.stderr)

    def test_skip_env_bypasses_preflight(self):
        # AGENT_CONFIG_SKIP_GIT_PREFLIGHT=1 lets the check pass even on
        # too-old git (an escape hatch for unusual installs).
        if not BASH:
            raise unittest.SkipTest("bash not available")
        tmp = Path(tempfile.mkdtemp(prefix="aa-preflight-"))
        try:
            stub_dir = tmp / "stub_path"
            _make_stub_git(stub_dir, "git version 2.10.0")
            work = tmp / "work"
            work.mkdir()
            env = _stripped_env(stub_dir)
            env["AGENT_CONFIG_PREFLIGHT_TEST"] = "1"
            env["AGENT_CONFIG_SKIP_GIT_PREFLIGHT"] = "1"
            result = subprocess.run(
                [BASH, str(BOOTSTRAP_SH)],
                cwd=str(work),
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertNotIn("too old", result.stderr)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_platform_install_hint_matches_uname(self):
        # The platform-specific install line should match `uname -s` shape.
        result = _run_bootstrap_sh("git version 2.20.0")
        self.assertNotEqual(result.returncode, 0, msg=result.stderr)
        # Cross-platform: at least one of the known platform lines must appear.
        platform_hints = (
            "brew install git",
            "apt update && sudo apt install -y git",
            "https://git-scm.com/download/win",
            "https://git-scm.com/downloads",
        )
        self.assertTrue(
            any(h in result.stderr for h in platform_hints),
            msg=f"no platform install hint in stderr: {result.stderr!r}",
        )


class _BootstrapLedgerContract:
    entrypoint = ""
    emitted_by = ""

    def _run_preflight_ledger(
        self,
        version_line: str | None,
        *,
        scenario: str = "fresh",
        upstream: str | None = None,
    ) -> tuple[subprocess.CompletedProcess, dict | None]:
        if self.entrypoint == "bash":
            return _run_bootstrap_sh_with_ledger(
                version_line,
                scenario=scenario,
                upstream=upstream,
            )
        return _run_bootstrap_ps1_with_ledger(
            version_line,
            scenario=scenario,
            upstream=upstream,
        )

    @staticmethod
    def _phase(ledger: dict, phase: str) -> dict:
        matches = [step for step in ledger["steps"] if step["phase"] == phase]
        if len(matches) != 1:
            raise AssertionError(f"expected one {phase!r} step, got {matches!r}")
        return matches[0]

    def test_ledger_written_at_preflight_boundary(self):
        result, ledger = self._run_preflight_ledger("git version 2.50.0")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIsNotNone(ledger)
        self.assertEqual(ledger["schema"], 1)
        self.assertEqual(ledger["emitted_by"], self.emitted_by)
        self.assertIs(ledger["completed"], False)
        self.assertEqual(ledger["last_phase"], "start")
        self.assertEqual(ledger["steps"], [])
        self.assertIsInstance(ledger["run_id"], str)
        self.assertTrue(ledger["run_id"])
        self.assertIsInstance(ledger["started_at"], str)
        self.assertTrue(ledger["started_at"])

    def test_ledger_records_incomplete_run_on_preflight_failure(self):
        result, ledger = self._run_preflight_ledger("git version 2.24.0")
        self.assertNotEqual(result.returncode, 0, msg=result.stderr)
        self.assertIsNotNone(ledger)
        self.assertIs(ledger["completed"], False)
        self.assertEqual(ledger["last_phase"], "start")

    def test_ledger_round_trips_hostile_upstream(self):
        upstreams = (
            'evil"x/re\\po',
            "evil\nrepo",
            "evil\rrepo",
            "evil\trepo",
            "evil\brepo",
            "evil\frepo",
            "evil\x01repo",
        )
        for upstream in upstreams:
            with self.subTest(upstream=repr(upstream)):
                result, ledger = self._run_preflight_ledger(
                    "git version 2.50.0",
                    upstream=upstream,
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr)
                self.assertIsNotNone(ledger)
                self.assertEqual(ledger["upstream"], upstream)

    def test_ledger_never_aborts_run_when_unwritable(self):
        result, ledger = self._run_preflight_ledger(
            "git version 2.50.0",
            scenario="unwritable",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIsNone(ledger)

    def test_generate_ok(self):
        result, ledger, _ = _run_full_bootstrap_with_ledger(
            self.entrypoint,
            generator_rc=0,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        step = self._phase(ledger, "generate")
        self.assertEqual(step["status"], "ok")
        self.assertIsNone(step["rc"])
        self.assertEqual(step["targets"], ["CLAUDE.md", "agents/codex.md"])

    def test_generate_failed(self):
        result, ledger, _ = _run_full_bootstrap_with_ledger(
            self.entrypoint,
            generator_rc=7,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        step = self._phase(ledger, "generate")
        self.assertEqual(step["status"], "failed")
        self.assertEqual(step["rc"], 7)
        self.assertEqual(step["targets"], [])

    def test_generate_skipped(self):
        result, ledger, _ = _run_full_bootstrap_with_ledger(
            self.entrypoint,
            generator_rc=None,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        step = self._phase(ledger, "generate")
        self.assertEqual(step["status"], "skipped")
        self.assertIsNone(step["rc"])
        self.assertEqual(step["targets"], [])

    def test_generate_recorded_before_composer_failure_exit(self):
        result, ledger, _ = _run_full_bootstrap_with_ledger(
            self.entrypoint,
            composer_rc=23,
            generator_rc=9,
        )
        self.assertEqual(result.returncode, 23, msg=result.stderr)
        compose = self._phase(ledger, "compose")
        self.assertEqual(compose["status"], "failed")
        self.assertEqual(compose["rc"], 23)
        generate = self._phase(ledger, "generate")
        self.assertEqual(generate["status"], "failed")
        self.assertEqual(generate["rc"], 9)

    def test_no_python_fallback_is_marked_and_incomplete_for_passive_pack(self):
        result, ledger, _, agents_bytes, upstream_bytes = _run_no_python_bootstrap_with_ledger(
            self.entrypoint,
            config_text="rule_packs:\n  - name: agent-style\n",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        reason = "no Python 3 interpreter found"
        marker = f"<!-- rule-pack composition skipped: {reason}; run anywhere-agents to compose -->\n".encode()
        self.assertNotEqual(agents_bytes, upstream_bytes)
        self.assertTrue(agents_bytes.startswith(marker), msg=agents_bytes[:200])
        self.assertEqual(agents_bytes[len(marker):], upstream_bytes)
        compose = self._phase(ledger, "compose")
        self.assertEqual(compose["status"], "skipped")
        self.assertEqual(compose["reason"], reason)
        self.assertIs(ledger["completed"], False)

    def test_local_empty_opt_out_overrides_tracked_selection(self):
        # The layers are ordered, not merged. Probing packs.config directly
        # returns [] for tracked [agent-style] plus local [], so this is a
        # deliberate opt-out and must not be marked as an incomplete run.
        # The predicate previously treated either layer's non-emptiness as
        # sufficient and reported completed:false here.
        result, ledger, _, agents_bytes, upstream_bytes = _run_no_python_bootstrap_with_ledger(
            self.entrypoint,
            config_text="rule_packs:\n  - name: agent-style\n",
            local_config_text="rule_packs: []\n",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(agents_bytes, upstream_bytes)
        self.assertNotIn(b"rule-pack composition skipped", agents_bytes)
        self.assertIs(ledger["completed"], True)

    def test_local_nonempty_selection_still_counts_as_configured(self):
        # The mirror of the case above: a non-empty local layer is a real
        # selection, so an omitted composition is still an incomplete run.
        # Without this the fix could pass by always returning false.
        result, ledger, _, agents_bytes, upstream_bytes = _run_no_python_bootstrap_with_ledger(
            self.entrypoint,
            config_text="rule_packs: []\n",
            local_config_text="rule_packs:\n  - name: agent-style\n",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotEqual(agents_bytes, upstream_bytes)
        self.assertIn(b"rule-pack composition skipped", agents_bytes)
        self.assertIs(ledger["completed"], False)

    def test_skip_reasons_distinguish_missing_yaml_and_missing_composer(self):
        yaml_result, yaml_ledger, yaml_artifacts = _run_full_bootstrap_with_ledger(
            self.entrypoint,
            yaml_available=False,
        )
        self.assertEqual(yaml_result.returncode, 0, msg=yaml_result.stderr)
        self.assertEqual(
            self._phase(yaml_ledger, "compose")["reason"],
            "Python 3 interpreter has no PyYAML after install attempt",
        )
        yaml_marker = b"<!-- rule-pack composition skipped: Python 3 interpreter has no PyYAML after install attempt; run anywhere-agents to compose -->"
        for relative in ("AGENTS.md", "CLAUDE.md", "agents/codex.md"):
            self.assertIn(yaml_marker, yaml_artifacts[relative])
        composer_result, composer_ledger, _ = _run_full_bootstrap_with_ledger(
            self.entrypoint,
            composer_rc=None,
        )
        self.assertEqual(composer_result.returncode, 0, msg=composer_result.stderr)
        self.assertEqual(
            self._phase(composer_ledger, "compose")["reason"],
            "no composer script in sparse clone",
        )

    def test_helper_deployment_never_exposes_staged_partial_file(self):
        result, observed, final, expected, running = _run_atomic_helper_deployment(self.entrypoint)
        self.assertTrue(running, msg="copy pause was not observed while bootstrap was running")
        self.assertEqual(observed, b"#!/usr/bin/env bash\n# old helper\nexit 0\n")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(final, expected)


class BootstrapLedgerBashTests(_BootstrapLedgerContract, unittest.TestCase):
    entrypoint = "bash"
    emitted_by = "bootstrap.sh"

    def test_self_update_replaces_inode_without_skipping_running_tail(self):
        result, deployed, replacement, original, ledger = _run_bash_self_update()
        self.assertNotEqual(len(replacement), len(original))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(deployed, replacement)
        self.assertEqual(ledger["last_phase"], "finalize")
        self.assertIs(ledger["completed"], True)


class BootstrapLedgerPowerShellTests(_BootstrapLedgerContract, unittest.TestCase):
    entrypoint = "powershell"
    emitted_by = "bootstrap.ps1"


class BootstrapLedgerParityTests(unittest.TestCase):

    def test_no_python_generate_steps_match(self):
        bash_result, bash_ledger, bash_raw, _, _ = _run_no_python_bootstrap_with_ledger("bash")
        ps_result, ps_ledger, ps_raw, _, _ = _run_no_python_bootstrap_with_ledger("powershell")
        self.assertEqual(bash_result.returncode, 0, msg=bash_result.stderr)
        self.assertEqual(ps_result.returncode, 0, msg=ps_result.stderr)
        bash_generate = next(step for step in bash_ledger["steps"] if step["phase"] == "generate")
        ps_generate = next(step for step in ps_ledger["steps"] if step["phase"] == "generate")
        expected = {
            "phase": "generate",
            "scope": "repo",
            "status": "skipped",
            "rc": None,
            "targets": [],
        }
        self.assertEqual(bash_generate, expected)
        self.assertEqual(ps_generate, expected)
        self.assertIs(type(bash_generate["rc"]), type(ps_generate["rc"]))
        self.assertEqual(json.loads(bash_raw), bash_ledger)
        self.assertEqual(json.loads(ps_raw), ps_ledger)
        self.assertIn("ANYWHERE_AGENTS_PYTHON did not execute Python 3 successfully", bash_result.stderr)
        self.assertIn("ANYWHERE_AGENTS_PYTHON did not execute Python 3 successfully", ps_result.stderr)


if __name__ == "__main__":
    unittest.main()
