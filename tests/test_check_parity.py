"""Smoke tests for scripts/check-parity.sh.

This script is a maintainer-only tool that runs against both ac and aa clones,
so full behavioral testing requires both to be present. These tests verify
script existence and shell-syntax validity; the real behavioral check is the
manual invocation from aa/RELEASING.md pre-release check 5.
"""

from __future__ import annotations

import pathlib
import platform
import shutil
import subprocess
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check-parity.sh"


def _find_bash() -> str | None:
    """Return a real bash executable path, avoiding the WSL relay on Windows.

    On Windows, the WSL relay at C:\\Windows\\System32\\bash.exe shows up on
    PATH first and errors with "execvpe(/bin/bash) failed" when invoked from
    Python subprocess. Prefer Git Bash explicitly.
    """
    if platform.system() == "Windows":
        candidates = [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
        ]
        for path in candidates:
            if pathlib.Path(path).is_file():
                return path
        return None
    return shutil.which("bash")


BASH = _find_bash()


class CheckParityScriptExists(unittest.TestCase):
    def test_script_present(self):
        self.assertTrue(
            SCRIPT.is_file(),
            f"expected {SCRIPT} to exist",
        )

    def test_script_has_shebang(self):
        first_line = SCRIPT.read_text(encoding="utf-8").splitlines()[0]
        self.assertTrue(
            first_line.startswith("#!"),
            f"expected shebang on first line, got {first_line!r}",
        )

    @unittest.skipUnless(
        BASH, "bash not found (Git Bash on Windows, /bin/bash on Unix)"
    )
    def test_script_shell_syntax_clean(self):
        # bash -n parses without executing; catches syntax errors locally.
        result = subprocess.run(
            [BASH, "-n", str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"bash -n failed: stdout={result.stdout!r}, stderr={result.stderr!r}",
        )


if __name__ == "__main__":
    unittest.main()
