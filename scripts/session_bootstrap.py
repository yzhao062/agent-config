#!/usr/bin/env python3
"""SessionStart hook: run .agent-config bootstrap if present in the CWD.

Deployed to ~/.claude/hooks/session_bootstrap.py by bootstrap.sh / .ps1,
and wired into ~/.claude/settings.json under hooks.SessionStart.

When Claude Code opens a session, this hook runs before the agent sees any
user prompt. If the current working directory has .agent-config/bootstrap.sh
(Unix) or .agent-config/bootstrap.ps1 (Windows), this runs it. Otherwise it
exits silently, so projects that do not use anywhere-agents are unaffected.

Claude Code's SessionStart hook behavior: stdout from the hook is added as
context to the session. To avoid flooding Claude with git-pull noise or
generator messages on every session start/resume/clear, this script captures
the subprocess output and emits a single concise summary line on success.
Errors go to stderr with the last ~2KB of child output for debugging.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys


def main() -> int:
    cwd = os.getcwd()
    cmd: list[str] | None = None

    if platform.system() == "Windows":
        script = os.path.join(cwd, ".agent-config", "bootstrap.ps1")
        if os.path.isfile(script):
            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                script,
            ]
    else:
        script = os.path.join(cwd, ".agent-config", "bootstrap.sh")
        if os.path.isfile(script):
            cmd = ["bash", script]

    if cmd is None:
        return 0

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("anywhere-agents: bootstrap refreshed")
        return 0

    print(
        f"anywhere-agents: bootstrap failed (exit {result.returncode})",
        file=sys.stderr,
    )
    if result.stdout:
        print(result.stdout[-2000:], file=sys.stderr)
    if result.stderr:
        print(result.stderr[-2000:], file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
