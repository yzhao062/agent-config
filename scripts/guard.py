"""
Claude Code PreToolUse hook guard.
Parses the Bash tool input JSON, extracts the command, and checks for:
1. Compound cd commands (cd path && cmd, cd path; cmd) → deny
2. Destructive git subcommands (push, commit, merge, etc.) → ask
3. Destructive gh subcommands (pr create, pr merge, etc.) → ask
"""
import json
import re
import shlex
import sys


def make_response(decision, reason):
    return json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    })


def check_cd_compound(cmd):
    """Check if command contains a cd that chains into another command."""
    # Split on shell operators, preserving order
    segments = re.split(r"&&|;|\|\|", cmd)
    for i, seg in enumerate(segments):
        seg = seg.strip()
        if seg.startswith("cd ") and i < len(segments) - 1:
            return True
    return False


def strip_wrappers(parts):
    """Skip env, inline VAR=VALUE, and other wrapper prefixes."""
    # env flags that consume the next token
    _env_value_flags = {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"}
    i = 0
    while i < len(parts):
        if parts[i] == "env":
            i += 1
            # Skip env flags and their values
            while i < len(parts) and parts[i].startswith("-"):
                if parts[i] in _env_value_flags and i + 1 < len(parts):
                    i += 2
                else:
                    i += 1
            # Skip VAR=VALUE pairs
            while i < len(parts) and "=" in parts[i] and not parts[i].startswith("-"):
                i += 1
        elif (
            "=" in parts[i]
            and not parts[i].startswith("-")
            and len(parts[i]) > 0
            and parts[i][0].isalpha()
        ):
            # Inline VAR=VALUE before command
            i += 1
        else:
            break
    return parts[i:]


# Git global options that consume the next token as a value.
# Options with = form (--git-dir=<path>) are handled by the "=" check.
_GIT_VALUE_FLAGS = {
    "-C", "-c",
    "--exec-path", "--git-dir", "--work-tree", "--namespace",
    "--super-prefix", "--config-env", "--attr-source", "--list-cmds",
}


def extract_git_subcommand(parts):
    """Skip git global flags and their values, return (index, subcommand)."""
    i = 1  # skip "git"
    while i < len(parts):
        if parts[i] in _GIT_VALUE_FLAGS and i + 1 < len(parts):
            i += 2
        elif parts[i].startswith("-"):
            if "=" in parts[i]:
                i += 1  # --flag=value consumed as one token
            else:
                i += 1  # boolean flag
        else:
            break
    return (i, parts[i]) if i < len(parts) else (i, "")


# gh inherited flags that consume the next token.
_GH_VALUE_FLAGS = {"-R", "--repo", "--hostname"}


def extract_gh_subcommand(parts):
    """Skip gh flags (before and after group), return (group, action)."""
    i = 1  # skip "gh"
    # Skip flags before group
    while i < len(parts):
        if parts[i] in _GH_VALUE_FLAGS and i + 1 < len(parts):
            i += 2
        elif parts[i].startswith("-"):
            i += 1
        else:
            break
    group = parts[i] if i < len(parts) else ""
    i += 1
    # Skip flags between group and action (inherited flags like -R can appear here)
    while i < len(parts):
        if parts[i] in _GH_VALUE_FLAGS and i + 1 < len(parts):
            i += 2
        elif parts[i].startswith("-"):
            i += 1
        else:
            break
    action = parts[i] if i < len(parts) else ""
    return group, action


def check_git_destructive(parts):
    """Check if a git command is destructive."""
    idx, sub = extract_git_subcommand(parts)
    if not sub:
        return False
    rest = parts[idx:]

    if sub in ("push", "commit", "merge", "rebase", "clean"):
        return True
    if sub == "reset":
        return "--hard" in rest
    if sub == "checkout":
        return "--" in rest
    if sub == "branch":
        return any(f in rest for f in ("-D", "-d", "--delete"))
    if sub == "tag":
        return any(f in rest for f in ("-d", "--delete"))
    if sub == "stash":
        return len(rest) > 1 and rest[1] in ("drop", "clear")
    return False


def check_gh_destructive(parts):
    """Check if a gh command is destructive."""
    group, action = extract_gh_subcommand(parts)
    destructive = {
        ("pr", "create"), ("pr", "merge"),
        ("pr", "close"), ("repo", "delete"),
    }
    return (group, action) in destructive


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    cmd = data.get("tool_input", {}).get("command", "").strip()
    if not cmd:
        return

    # Check 1: compound cd (on raw string, before shlex parsing)
    if check_cd_compound(cmd):
        print(make_response(
            "deny",
            "Compound cd command blocked. Use separate tool calls or path arguments."
        ))
        return

    # Parse into tokens with proper quote handling
    try:
        parts = shlex.split(cmd)
    except ValueError:
        parts = cmd.split()  # fallback for malformed quoting

    if not parts:
        return

    # Strip wrapper prefixes (env, VAR=VALUE)
    parts = strip_wrappers(parts)
    if not parts:
        return

    # Check 2: destructive git
    if parts[0] == "git" and check_git_destructive(parts):
        print(make_response(
            "ask",
            "Destructive git command detected. Confirm before proceeding."
        ))
        return

    # Check 3: destructive gh
    if parts[0] == "gh" and check_gh_destructive(parts):
        print(make_response(
            "ask",
            "Destructive gh command detected. Confirm before proceeding."
        ))
        return


if __name__ == "__main__":
    main()