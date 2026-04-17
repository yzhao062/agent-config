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

import json
import os
import platform
import subprocess
import sys
import time


VERSION_CACHE_TTL_SECONDS = 86400  # 24 hours


def update_version_cache() -> None:
    """Refresh ~/.claude/hooks/version-cache.json with the latest Claude Code and
    Codex versions from the npm registry. Used by the session-start banner to
    show current vs latest. 24-hour TTL keeps the common path to a file read.
    Silent on any failure — the banner tolerates a missing cache by omitting
    the "→ latest" half instead of blocking.
    """
    cache_path = os.path.join(
        os.path.expanduser("~"), ".claude", "hooks", "version-cache.json"
    )
    cache: dict = {}
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    now = time.time()
    if cache.get("checked_at", 0) + VERSION_CACHE_TTL_SECONDS > now:
        return  # still fresh

    new_cache: dict = {
        "checked_at": now,
        "claude_latest": cache.get("claude_latest", ""),
        "codex_latest": cache.get("codex_latest", ""),
    }

    import urllib.request

    for key, url in (
        (
            "claude_latest",
            "https://registry.npmjs.org/@anthropic-ai%2Fclaude-code/latest",
        ),
        ("codex_latest", "https://registry.npmjs.org/@openai%2Fcodex/latest"),
    ):
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
                v = data.get("version", "")
                if v:
                    new_cache[key] = v
        except Exception:
            pass  # preserve previous value

    # Only persist the cache (advancing checked_at) if at least one version is
    # known. First-ever run where both fetches fail leaves the cache absent so
    # the next session retries instead of waiting out the 24h TTL with empty
    # values.
    if new_cache.get("claude_latest") or new_cache.get("codex_latest"):
        try:
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(new_cache, f)
        except Exception:
            pass


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

    # Refresh the version cache only when this is a participating repo, so the
    # hook stays silent (and network-free) in unrelated Claude Code sessions.
    update_version_cache()

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
