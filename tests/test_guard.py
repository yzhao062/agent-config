"""Tests for guard.py hook. Discovers guard.py relative to the repo root."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "scripts" / "guard.py"


def run_guard(command: str) -> str:
    """Run guard.py with a simulated hook input and return the decision."""
    payload = json.dumps({"tool_input": {"command": command}})
    result = subprocess.run(
        [sys.executable, str(GUARD)],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"guard.py crashed (exit {result.returncode}): {result.stderr.strip()}"
        )
    stdout = result.stdout.strip()
    if not stdout:
        return "PASSED"
    data = json.loads(stdout)
    return data["hookSpecificOutput"]["permissionDecision"].upper()


def run_guard_full(command: str) -> dict | None:
    """Run guard.py and return the full parsed JSON payload, or None if no output."""
    payload = json.dumps({"tool_input": {"command": command}})
    result = subprocess.run(
        [sys.executable, str(GUARD)],
        input=payload,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"guard.py crashed (exit {result.returncode}): {result.stderr.strip()}"
        )
    stdout = result.stdout.strip()
    if not stdout:
        return None
    return json.loads(stdout)


class CompoundCdTests(unittest.TestCase):
    """Compound cd commands should be denied."""

    def test_cd_and_pdflatex(self) -> None:
        self.assertEqual(run_guard("cd papers/foo && pdflatex main.tex"), "DENY")

    def test_cd_semicolon_rm(self) -> None:
        self.assertEqual(run_guard("cd /tmp; rm -rf /"), "DENY")

    def test_cd_and_bibtex(self) -> None:
        self.assertEqual(run_guard("cd papers/foo && bibtex main"), "DENY")

    def test_cd_with_leading_space(self) -> None:
        self.assertEqual(run_guard("  cd /tmp && ls"), "DENY")

    def test_set_e_semicolon_cd(self) -> None:
        self.assertEqual(run_guard("set -e; cd repo && make"), "DENY")

    def test_set_ex_semicolon_cd(self) -> None:
        self.assertEqual(run_guard("set -ex; cd repo && make"), "DENY")

    def test_set_e_and_cd(self) -> None:
        self.assertEqual(run_guard("set -e && cd repo && make"), "DENY")

    def test_cd_semicolon_ls(self) -> None:
        self.assertEqual(run_guard("cd /tmp; ls -la"), "DENY")

    def test_cd_or_exit(self) -> None:
        self.assertEqual(run_guard("cd repo || exit 1"), "DENY")


class DestructiveGitDirectTests(unittest.TestCase):
    """Destructive git commands in direct form should ask."""

    def test_push(self) -> None:
        self.assertEqual(run_guard("git push origin main"), "ASK")

    def test_push_bare(self) -> None:
        self.assertEqual(run_guard("git push"), "ASK")

    def test_commit(self) -> None:
        self.assertEqual(run_guard('git commit -m "fix bug"'), "ASK")

    def test_merge(self) -> None:
        self.assertEqual(run_guard("git merge origin/main"), "ASK")

    def test_rebase(self) -> None:
        self.assertEqual(run_guard("git rebase main"), "ASK")

    def test_reset_hard(self) -> None:
        self.assertEqual(run_guard("git reset --hard HEAD~1"), "ASK")

    def test_clean(self) -> None:
        self.assertEqual(run_guard("git clean -fd"), "ASK")

    def test_branch_D(self) -> None:
        self.assertEqual(run_guard("git branch -D feature"), "ASK")

    def test_branch_d(self) -> None:
        self.assertEqual(run_guard("git branch -d feature"), "ASK")

    def test_branch_delete(self) -> None:
        self.assertEqual(run_guard("git branch --delete feature"), "ASK")

    def test_tag_d(self) -> None:
        self.assertEqual(run_guard("git tag -d v1.0"), "ASK")

    def test_tag_delete(self) -> None:
        self.assertEqual(run_guard("git tag --delete v1.0"), "ASK")

    def test_stash_drop(self) -> None:
        self.assertEqual(run_guard("git stash drop stash@{0}"), "ASK")

    def test_stash_clear(self) -> None:
        self.assertEqual(run_guard("git stash clear"), "ASK")

    def test_checkout_dash_dash_file(self) -> None:
        self.assertEqual(run_guard("git checkout -- src/main.py"), "ASK")


class DestructiveGitFlagVariantTests(unittest.TestCase):
    """Destructive git commands with global flags should still ask."""

    def test_C_push(self) -> None:
        self.assertEqual(run_guard("git -C papers/repo push origin main"), "ASK")

    def test_C_commit(self) -> None:
        self.assertEqual(run_guard('git -C papers/repo commit -m "msg"'), "ASK")

    def test_C_merge(self) -> None:
        self.assertEqual(run_guard("git -C papers/repo merge origin/main"), "ASK")

    def test_C_branch_D(self) -> None:
        self.assertEqual(run_guard("git -C papers/repo branch -D feature"), "ASK")

    def test_C_checkout_dash_dash(self) -> None:
        self.assertEqual(run_guard("git -C papers/repo checkout -- file.py"), "ASK")

    def test_C_tag_d(self) -> None:
        self.assertEqual(run_guard("git -C papers/repo tag -d v1.0"), "ASK")

    def test_c_config_push(self) -> None:
        self.assertEqual(run_guard("git -c color.ui=always push origin main"), "ASK")

    def test_C_quoted_path_push(self) -> None:
        self.assertEqual(run_guard('git -C "repo with space" push origin main'), "ASK")

    def test_exec_path_push(self) -> None:
        self.assertEqual(run_guard("git --exec-path /tmp push origin main"), "ASK")

    def test_git_dir_push(self) -> None:
        self.assertEqual(run_guard("git --git-dir /tmp/.git push origin main"), "ASK")

    def test_work_tree_push(self) -> None:
        self.assertEqual(run_guard("git --work-tree /tmp push origin main"), "ASK")


class DestructiveGitWrapperTests(unittest.TestCase):
    """Destructive git commands with env/var wrappers should still ask."""

    def test_env_var_push(self) -> None:
        self.assertEqual(run_guard("env FOO=1 git push origin main"), "ASK")

    def test_inline_var_push(self) -> None:
        self.assertEqual(run_guard("FOO=1 git push origin main"), "ASK")

    def test_env_unset_commit(self) -> None:
        self.assertEqual(run_guard("env -u VAR git commit -m msg"), "ASK")

    def test_multi_var_push(self) -> None:
        self.assertEqual(run_guard("A=1 B=2 git push origin main"), "ASK")


class DestructiveGhTests(unittest.TestCase):
    """Destructive gh commands should ask."""

    def test_pr_create(self) -> None:
        self.assertEqual(run_guard('gh pr create --title "fix"'), "ASK")

    def test_pr_merge(self) -> None:
        self.assertEqual(run_guard("gh pr merge 42"), "ASK")

    def test_pr_close(self) -> None:
        self.assertEqual(run_guard("gh pr close 42"), "ASK")

    def test_repo_delete(self) -> None:
        self.assertEqual(run_guard("gh repo delete owner/repo"), "ASK")

    def test_R_pr_create(self) -> None:
        self.assertEqual(run_guard("gh -R owner/repo pr create"), "ASK")

    def test_R_pr_merge(self) -> None:
        self.assertEqual(run_guard("gh -R owner/repo pr merge 42"), "ASK")

    def test_repo_pr_create(self) -> None:
        self.assertEqual(run_guard("gh --repo owner/repo pr create"), "ASK")

    def test_pr_R_create(self) -> None:
        self.assertEqual(run_guard("gh pr -R owner/repo create --title x"), "ASK")

    def test_repo_R_delete(self) -> None:
        self.assertEqual(run_guard("gh repo -R owner/repo delete"), "ASK")


class BypassRegressionTests(unittest.TestCase):
    """Branch names containing safe-looking substrings should still ask."""

    def test_merge_feature_merge_base_fix(self) -> None:
        self.assertEqual(run_guard("git merge feature/merge-base-fix"), "ASK")

    def test_rebase_topic_commit_graph(self) -> None:
        self.assertEqual(run_guard("git rebase topic/commit-graph-cleanup"), "ASK")


class SafeCommandTests(unittest.TestCase):
    """Safe commands should pass through without intervention."""

    def test_pdflatex(self) -> None:
        self.assertEqual(run_guard("pdflatex main.tex"), "PASSED")

    def test_bibtex(self) -> None:
        self.assertEqual(run_guard("bibtex main"), "PASSED")

    def test_latexmk(self) -> None:
        self.assertEqual(run_guard("latexmk -pdf main.tex"), "PASSED")

    def test_echo_with_cd_text(self) -> None:
        self.assertEqual(run_guard('echo "cd repo && make"'), "PASSED")

    def test_grep(self) -> None:
        self.assertEqual(run_guard("grep -r pattern src/"), "PASSED")

    def test_ls(self) -> None:
        self.assertEqual(run_guard("ls -la"), "PASSED")

    def test_python(self) -> None:
        self.assertEqual(run_guard("python script.py"), "PASSED")

    def test_git_status(self) -> None:
        self.assertEqual(run_guard("git status"), "PASSED")

    def test_git_log(self) -> None:
        self.assertEqual(run_guard("git log --oneline -5"), "PASSED")

    def test_git_diff(self) -> None:
        self.assertEqual(run_guard("git diff HEAD"), "PASSED")

    def test_git_branch_list(self) -> None:
        self.assertEqual(run_guard("git branch"), "PASSED")

    def test_git_branch_v(self) -> None:
        self.assertEqual(run_guard("git branch -v"), "PASSED")

    def test_git_tag_list(self) -> None:
        self.assertEqual(run_guard("git tag --list"), "PASSED")

    def test_git_stash_list(self) -> None:
        self.assertEqual(run_guard("git stash list"), "PASSED")

    def test_git_show(self) -> None:
        self.assertEqual(run_guard("git show HEAD"), "PASSED")

    def test_git_fetch(self) -> None:
        self.assertEqual(run_guard("git fetch origin"), "PASSED")

    def test_git_pull(self) -> None:
        self.assertEqual(run_guard("git pull origin main"), "PASSED")

    def test_git_merge_base(self) -> None:
        self.assertEqual(run_guard("git merge-base HEAD origin/main"), "PASSED")

    def test_git_show_branch_d(self) -> None:
        self.assertEqual(run_guard("git show-branch -d"), "PASSED")

    def test_git_commit_tree(self) -> None:
        self.assertEqual(run_guard("git commit-tree abc123"), "PASSED")

    def test_git_commit_graph(self) -> None:
        self.assertEqual(run_guard("git commit-graph write"), "PASSED")

    def test_git_reset_soft(self) -> None:
        self.assertEqual(run_guard("git reset --soft HEAD~1"), "PASSED")

    def test_git_checkout_branch(self) -> None:
        self.assertEqual(run_guard("git checkout feature"), "PASSED")

    def test_git_tag_create(self) -> None:
        self.assertEqual(run_guard("git tag v1.0"), "PASSED")

    def test_git_C_status(self) -> None:
        self.assertEqual(run_guard("git -C papers/repo status"), "PASSED")

    def test_git_C_log(self) -> None:
        self.assertEqual(run_guard("git -C papers/repo log --oneline"), "PASSED")

    def test_git_C_diff(self) -> None:
        self.assertEqual(run_guard("git -C papers/repo diff"), "PASSED")

    def test_git_C_fetch(self) -> None:
        self.assertEqual(run_guard("git -C papers/repo fetch origin"), "PASSED")

    def test_git_notes_add(self) -> None:
        self.assertEqual(run_guard('git notes add -m "commit docs"'), "PASSED")

    def test_gh_pr_list(self) -> None:
        self.assertEqual(run_guard("gh pr list"), "PASSED")

    def test_gh_pr_view(self) -> None:
        self.assertEqual(run_guard("gh pr view 42"), "PASSED")

    def test_gh_pr_status(self) -> None:
        self.assertEqual(run_guard("gh pr status"), "PASSED")

    def test_gh_issue_list(self) -> None:
        self.assertEqual(run_guard("gh issue list"), "PASSED")

    def test_empty_command(self) -> None:
        self.assertEqual(run_guard(""), "PASSED")

    def test_cd_alone(self) -> None:
        self.assertEqual(run_guard("cd /tmp"), "PASSED")


class JsonPayloadTests(unittest.TestCase):
    """Verify the full JSON output structure, not just the decision string."""

    def _assert_valid_payload(self, command: str, expected_decision: str) -> None:
        data = run_guard_full(command)
        self.assertIsNotNone(data, f"Expected output for: {command}")
        self.assertIn("hookSpecificOutput", data)
        hook = data["hookSpecificOutput"]
        self.assertEqual(hook["hookEventName"], "PreToolUse")
        self.assertEqual(hook["permissionDecision"], expected_decision)
        self.assertIsInstance(hook["permissionDecisionReason"], str)
        self.assertTrue(len(hook["permissionDecisionReason"]) > 0)

    def test_git_commit_payload(self) -> None:
        self._assert_valid_payload('git commit -m "msg"', "ask")

    def test_git_push_payload(self) -> None:
        self._assert_valid_payload("git push origin main", "ask")

    def test_gh_pr_create_payload(self) -> None:
        self._assert_valid_payload("gh pr create --title t", "ask")

    def test_compound_cd_payload(self) -> None:
        self._assert_valid_payload("cd /tmp && ls", "deny")

    def test_safe_command_no_output(self) -> None:
        data = run_guard_full("git status")
        self.assertIsNone(data)


if __name__ == "__main__":
    unittest.main()
