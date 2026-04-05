"""Tests for guard.py hook. Portable — finds guard.py relative to this file."""
import json
import os
import subprocess
import sys

PYTHON = sys.executable
GUARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guard.py")


def run_guard(command):
    """Run guard.py with a simulated hook input and return the decision."""
    payload = json.dumps({"tool_input": {"command": command}})
    result = subprocess.run(
        [PYTHON, GUARD],
        input=payload,
        capture_output=True,
        text=True,
    )
    stdout = result.stdout.strip()
    if not stdout:
        return "PASSED"
    try:
        data = json.loads(stdout)
        return data["hookSpecificOutput"]["permissionDecision"].upper()
    except (json.JSONDecodeError, KeyError):
        return f"ERROR: {stdout}"


def test(label, command, expected):
    actual = run_guard(command)
    status = "OK" if actual == expected else "FAIL"
    print(f"  [{status}] {label:55s} expected={expected:10s} got={actual}")
    return status == "OK"


def main():
    passed = 0
    failed = 0
    total = 0

    def run(label, cmd, exp):
        nonlocal passed, failed, total
        total += 1
        if test(label, cmd, exp):
            passed += 1
        else:
            failed += 1

    # =========================================================
    # COMPOUND CD (should DENY)
    # =========================================================
    print("\n=== Compound cd commands (should DENY) ===")
    run("cd && pdflatex",             "cd papers/foo && pdflatex main.tex",       "DENY")
    run("cd ; rm",                    "cd /tmp; rm -rf /",                        "DENY")
    run("cd && bibtex",               "cd papers/foo && bibtex main",             "DENY")
    run("cd with leading space",      "  cd /tmp && ls",                          "DENY")
    # R5 regression: set prefixes
    run("set -e; cd && make",         "set -e; cd repo && make",                  "DENY")
    run("set -ex; cd && cmd",         "set -ex; cd repo && make",                 "DENY")
    run("set -e && cd && make",       "set -e && cd repo && make",                "DENY")
    run("cd path ; cmd (semicolon)",  "cd /tmp; ls -la",                          "DENY")
    run("cd || exit then &&",         "cd repo || exit 1",                        "DENY")

    # =========================================================
    # DESTRUCTIVE GIT — direct forms (should ASK)
    # =========================================================
    print("\n=== Destructive git — direct (should ASK) ===")
    run("git push",                   "git push origin main",                     "ASK")
    run("git push (bare)",            "git push",                                 "ASK")
    run("git commit",                 'git commit -m "fix bug"',                  "ASK")
    run("git merge",                  "git merge origin/main",                    "ASK")
    run("git rebase",                 "git rebase main",                          "ASK")
    run("git reset --hard",           "git reset --hard HEAD~1",                  "ASK")
    run("git clean",                  "git clean -fd",                            "ASK")
    run("git branch -D",              "git branch -D feature",                    "ASK")
    run("git branch -d",              "git branch -d feature",                    "ASK")
    run("git branch --delete",        "git branch --delete feature",              "ASK")
    run("git tag -d",                 "git tag -d v1.0",                          "ASK")
    run("git tag --delete",           "git tag --delete v1.0",                    "ASK")
    run("git stash drop",             "git stash drop stash@{0}",                 "ASK")
    run("git stash clear",            "git stash clear",                          "ASK")
    run("git checkout -- file",       "git checkout -- src/main.py",              "ASK")

    # =========================================================
    # DESTRUCTIVE GIT — flag variants (should ASK)
    # =========================================================
    print("\n=== Destructive git — flag variants (should ASK) ===")
    run("git -C push",               "git -C papers/repo push origin main",      "ASK")
    run("git -C commit",             'git -C papers/repo commit -m "msg"',        "ASK")
    run("git -C merge",              "git -C papers/repo merge origin/main",      "ASK")
    run("git -C branch -D",          "git -C papers/repo branch -D feature",      "ASK")
    run("git -C checkout -- file",   "git -C papers/repo checkout -- file.py",    "ASK")
    run("git -C tag -d",             "git -C papers/repo tag -d v1.0",            "ASK")
    run("git -c config push",        "git -c color.ui=always push origin main",   "ASK")
    # R5 regressions: quoted -C, --exec-path
    run("git -C quoted path push",   'git -C "repo with space" push origin main', "ASK")
    run("git --exec-path push",      "git --exec-path /tmp push origin main",     "ASK")
    run("git --git-dir push",        "git --git-dir /tmp/.git push origin main",  "ASK")
    run("git --work-tree push",      "git --work-tree /tmp push origin main",     "ASK")

    # =========================================================
    # DESTRUCTIVE GIT — wrapper prefixes (should ASK)
    # =========================================================
    print("\n=== Destructive git — wrapper prefixes (should ASK) ===")
    run("env FOO=1 git push",        "env FOO=1 git push origin main",           "ASK")
    run("FOO=1 git push",            "FOO=1 git push origin main",               "ASK")
    run("env -u VAR git commit",     "env -u VAR git commit -m msg",             "ASK")
    run("A=1 B=2 git push",          "A=1 B=2 git push origin main",             "ASK")

    # =========================================================
    # DESTRUCTIVE GH (should ASK)
    # =========================================================
    print("\n=== Destructive gh commands (should ASK) ===")
    run("gh pr create",              'gh pr create --title "fix"',                "ASK")
    run("gh pr merge",               "gh pr merge 42",                           "ASK")
    run("gh pr close",               "gh pr close 42",                           "ASK")
    run("gh repo delete",            "gh repo delete owner/repo",                "ASK")
    run("gh -R pr create",           "gh -R owner/repo pr create",               "ASK")
    run("gh -R pr merge",            "gh -R owner/repo pr merge 42",             "ASK")
    run("gh --repo pr create",       "gh --repo owner/repo pr create",           "ASK")
    # R5 regressions: -R after group token
    run("gh pr -R create",           "gh pr -R owner/repo create --title x",     "ASK")
    run("gh repo -R delete",         "gh repo -R owner/repo delete",             "ASK")

    # =========================================================
    # R3 BYPASS REGRESSION (branch name containing safe substring)
    # =========================================================
    print("\n=== R3 bypass regression (should ASK) ===")
    run("git merge feature/merge-base-fix",
        "git merge feature/merge-base-fix",                                       "ASK")
    run("git rebase topic/commit-graph",
        "git rebase topic/commit-graph-cleanup",                                  "ASK")

    # =========================================================
    # SAFE COMMANDS (should PASS)
    # =========================================================
    print("\n=== Safe commands (should PASS) ===")
    # General
    run("pdflatex",                   "pdflatex main.tex",                        "PASSED")
    run("bibtex",                     "bibtex main",                              "PASSED")
    run("latexmk",                    "latexmk -pdf main.tex",                    "PASSED")
    run("echo with cd text",          'echo "cd repo && make"',                   "PASSED")
    run("grep",                       "grep -r pattern src/",                     "PASSED")
    run("ls",                         "ls -la",                                   "PASSED")
    run("python",                     "python script.py",                         "PASSED")
    # Safe git
    run("git status",                 "git status",                               "PASSED")
    run("git log",                    "git log --oneline -5",                     "PASSED")
    run("git diff",                   "git diff HEAD",                            "PASSED")
    run("git branch (list)",          "git branch",                               "PASSED")
    run("git branch -v",              "git branch -v",                            "PASSED")
    run("git tag --list",             "git tag --list",                           "PASSED")
    run("git stash list",             "git stash list",                           "PASSED")
    run("git show",                   "git show HEAD",                            "PASSED")
    run("git fetch",                  "git fetch origin",                         "PASSED")
    run("git pull",                   "git pull origin main",                     "PASSED")
    run("git merge-base",             "git merge-base HEAD origin/main",          "PASSED")
    run("git show-branch -d",         "git show-branch -d",                       "PASSED")
    run("git commit-tree",            "git commit-tree abc123",                   "PASSED")
    run("git commit-graph",           "git commit-graph write",                   "PASSED")
    run("git reset (soft)",           "git reset --soft HEAD~1",                  "PASSED")
    run("git checkout branch",        "git checkout feature",                     "PASSED")
    run("git tag (create)",           "git tag v1.0",                             "PASSED")
    run("git -C status",              "git -C papers/repo status",                "PASSED")
    run("git -C log",                 "git -C papers/repo log --oneline",         "PASSED")
    run("git -C diff",                "git -C papers/repo diff",                  "PASSED")
    run("git -C fetch",               "git -C papers/repo fetch origin",          "PASSED")
    run("git notes add",              'git notes add -m "commit docs"',           "PASSED")
    # Safe gh
    run("gh pr list",                 "gh pr list",                               "PASSED")
    run("gh pr view",                 "gh pr view 42",                            "PASSED")
    run("gh pr status",               "gh pr status",                             "PASSED")
    run("gh issue list",              "gh issue list",                            "PASSED")
    # Edge cases
    run("empty command",              "",                                         "PASSED")
    run("cd alone (no chaining)",     "cd /tmp",                                  "PASSED")

    # =========================================================
    print(f"\n{'='*65}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed:
        print("SOME TESTS FAILED")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()