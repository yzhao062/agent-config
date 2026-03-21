import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
GITIGNORE = ROOT / ".gitignore"
GITATTRIBUTES = ROOT / ".gitattributes"
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"
SKILLS_DIR = ROOT / "skills"
POINTER_DIR = ROOT / ".claude" / "commands"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def skill_dirs() -> list[Path]:
    return sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())


def extract_fenced_block(text: str, language: str) -> str:
    match = re.search(rf"```{language}\n(.*?)\n```", text, re.DOTALL)
    if not match:
        raise AssertionError(f"Missing ```{language} code block in AGENTS.md")
    return match.group(1)


def run_command(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


class RepoValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.agents_text = read_text(AGENTS)
        cls.readme_text = read_text(README)
        cls.gitignore_text = read_text(GITIGNORE)
        cls.gitattributes_text = read_text(GITATTRIBUTES)
        cls.workflow_text = read_text(WORKFLOW)
        cls.skills = skill_dirs()
        cls.powershell_bootstrap = extract_fenced_block(cls.agents_text, "powershell")
        cls.bash_bootstrap = extract_fenced_block(cls.agents_text, "bash")

    def assert_command_ok(
        self, result: subprocess.CompletedProcess[str], context: str
    ) -> None:
        if result.returncode != 0:
            self.fail(
                f"{context} failed with exit code {result.returncode}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

    def tracked_files(self) -> set[str]:
        result = run_command(["git", "ls-files"], ROOT)
        self.assert_command_ok(result, "git ls-files")
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}

    def create_remote_repo_snapshot(self, base_dir: Path) -> Path:
        remote_dir = base_dir / "remote-src"
        remote_dir.mkdir()
        shutil.copy2(AGENTS, remote_dir / "AGENTS.md")
        shutil.copytree(SKILLS_DIR, remote_dir / "skills")
        shutil.copytree(POINTER_DIR, remote_dir / ".claude" / "commands")

        init = run_command(["git", "init"], remote_dir)
        self.assert_command_ok(init, "git init in remote snapshot")

        branch = run_command(["git", "checkout", "-b", "main"], remote_dir)
        self.assert_command_ok(branch, "git checkout -b main in remote snapshot")

        email = run_command(
            ["git", "config", "user.email", "repo-validation@example.com"], remote_dir
        )
        self.assert_command_ok(email, "git config user.email in remote snapshot")

        name = run_command(
            ["git", "config", "user.name", "Repo Validation"], remote_dir
        )
        self.assert_command_ok(name, "git config user.name in remote snapshot")

        add = run_command(["git", "add", "."], remote_dir)
        self.assert_command_ok(add, "git add in remote snapshot")

        commit = run_command(["git", "commit", "-m", "snapshot"], remote_dir)
        self.assert_command_ok(commit, "git commit in remote snapshot")
        return remote_dir

    def prepare_project_dir(self, base_dir: Path) -> Path:
        project_dir = base_dir / "project"
        commands_dir = project_dir / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        (commands_dir / "local-only.md").write_text("local-only\n", encoding="utf-8")
        (commands_dir / "dual-pass-workflow.md").write_text(
            "stale-pointer\n", encoding="utf-8"
        )
        (project_dir / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
        return project_dir

    def verify_bootstrap_result(self, project_dir: Path) -> None:
        fetched_agents = project_dir / ".agent-config" / "AGENTS.md"
        cloned_skill = (
            project_dir
            / ".agent-config"
            / "repo"
            / "skills"
            / "dual-pass-workflow"
            / "SKILL.md"
        )
        cloned_pointer = (
            project_dir
            / ".agent-config"
            / "repo"
            / ".claude"
            / "commands"
            / "dual-pass-workflow.md"
        )
        project_pointer = project_dir / ".claude" / "commands" / "dual-pass-workflow.md"
        local_only_pointer = project_dir / ".claude" / "commands" / "local-only.md"

        self.assertTrue(fetched_agents.exists(), "Expected fetched AGENTS.md")
        self.assertIn("## User Profile", read_text(fetched_agents))
        self.assertTrue(cloned_skill.exists(), "Expected cloned skill definition")
        self.assertTrue(cloned_pointer.exists(), "Expected cloned Claude pointer")
        self.assertEqual(read_text(project_pointer), read_text(POINTER_DIR / "dual-pass-workflow.md"))
        self.assertEqual(read_text(local_only_pointer), "local-only\n")

        gitignore_lines = (project_dir / ".gitignore").read_text(
            encoding="utf-8"
        ).splitlines()
        self.assertEqual(gitignore_lines.count(".agent-config/"), 1)

    def render_powershell_smoke_script(self, remote_dir: Path) -> str:
        agents_copy = str((remote_dir / "AGENTS.md")).replace("'", "''")
        script = self.powershell_bootstrap.replace(
            "Invoke-WebRequest -UseBasicParsing -Uri https://raw.githubusercontent.com/yzhao062/agent-config/main/AGENTS.md -OutFile .agent-config/AGENTS.md",
            f"Copy-Item -LiteralPath '{agents_copy}' -Destination .agent-config/AGENTS.md",
        )
        return script.replace(
            "https://github.com/yzhao062/agent-config.git", remote_dir.as_uri()
        )

    def render_bash_smoke_script(self, remote_dir: Path) -> str:
        agents_copy = shlex.quote((remote_dir / "AGENTS.md").as_posix())
        script = self.bash_bootstrap.replace(
            "curl -sfL https://raw.githubusercontent.com/yzhao062/agent-config/main/AGENTS.md -o .agent-config/AGENTS.md",
            f"cp {agents_copy} .agent-config/AGENTS.md",
        )
        return script.replace(
            "https://github.com/yzhao062/agent-config.git", remote_dir.as_uri()
        )

    def test_repo_has_at_least_one_skill(self) -> None:
        self.assertTrue(self.skills, "Expected at least one shared skill in skills/.")

    def test_agents_has_fetched_copy_guard(self) -> None:
        self.assertIn(
            "If this file was fetched into `.agent-config/AGENTS.md`",
            self.agents_text,
        )
        self.assertIn(
            "read and follow the shared rules starting at `## User Profile`",
            self.agents_text,
        )

    def test_agents_bootstrap_covers_windows_and_unix_shells(self) -> None:
        required_fragments = [
            "PowerShell (Windows):",
            "```powershell",
            "Invoke-WebRequest -UseBasicParsing -Uri https://raw.githubusercontent.com/yzhao062/agent-config/main/AGENTS.md -OutFile .agent-config/AGENTS.md",
            "Copy-Item .agent-config/repo/.claude/commands/*.md .claude/commands/ -Force",
            "Add-Content -Path .gitignore -Value \"`n.agent-config/\"",
            "Bash (macOS/Linux):",
            "```bash",
            "curl -sfL https://raw.githubusercontent.com/yzhao062/agent-config/main/AGENTS.md -o .agent-config/AGENTS.md",
            "cp -f .agent-config/repo/.claude/commands/*.md .claude/commands/",
            "echo '.agent-config/' >> .gitignore",
            "git -C .agent-config/repo sparse-checkout set skills .claude/commands",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, self.agents_text)

    def test_agents_declares_non_destructive_claude_sync(self) -> None:
        self.assertIn(
            "does not delete unrelated project-local commands",
            self.agents_text,
        )
        self.assertIn(
            "should not delete unrelated project-local commands",
            self.agents_text,
        )

    def test_gitignore_excludes_local_state(self) -> None:
        for entry in (
            "/.agent-config/",
            "/.claude/settings.local.json",
            "/.idea/",
            "__pycache__/",
        ):
            self.assertIn(entry, self.gitignore_text)

    def test_gitattributes_enforces_lf_for_text_files(self) -> None:
        self.assertIn("* text=auto eol=lf", self.gitattributes_text)

    def test_tracked_files_exclude_local_state_paths(self) -> None:
        tracked = self.tracked_files()
        self.assertNotIn(".claude/settings.local.json", tracked)
        self.assertFalse(any(path.startswith(".idea/") for path in tracked))

    def test_readme_describes_bootstrap_and_validation_targets(self) -> None:
        expected = [
            "**`AGENTS.md`**",
            "**`skills/`**",
            "**`.claude/commands/`**",
            "Auto-add `.agent-config/` to the project's `.gitignore`.",
            "阅读 AGENTS.md 并执行其中的 bootstrap 脚本。",
            "Use any Python 3.12 interpreter to run them locally:",
            "temp-project smoke tests for the bootstrap flow",
            'python -B -m unittest discover -s tests -p "test_*.py" -v',
        ]
        for fragment in expected:
            self.assertIn(fragment, self.readme_text)

    def test_readme_lists_every_skill(self) -> None:
        for skill_dir in self.skills:
            self.assertIn(f"`{skill_dir.name}`", self.readme_text)

    def test_each_skill_has_core_files(self) -> None:
        for skill_dir in self.skills:
            skill_name = skill_dir.name
            self.assertTrue((skill_dir / "SKILL.md").exists(), skill_name)
            self.assertTrue((skill_dir / "agents" / "openai.yaml").exists(), skill_name)
            self.assertTrue((POINTER_DIR / f"{skill_name}.md").exists(), skill_name)

    def test_pointer_files_match_skill_directories(self) -> None:
        skill_names = {path.name for path in self.skills}
        pointer_names = {path.stem for path in POINTER_DIR.glob("*.md")}
        self.assertEqual(skill_names, pointer_names)

    def test_pointer_files_reference_matching_skill(self) -> None:
        for pointer_file in POINTER_DIR.glob("*.md"):
            skill_name = pointer_file.stem
            pointer_text = read_text(pointer_file)
            self.assertIn(
                f"skills/{skill_name}/SKILL.md",
                pointer_text,
                pointer_file.name,
            )

    def test_openai_wrappers_reference_matching_skill(self) -> None:
        for skill_dir in self.skills:
            wrapper_text = read_text(skill_dir / "agents" / "openai.yaml")
            self.assertIn("display_name:", wrapper_text, skill_dir.name)
            self.assertIn(f"${skill_dir.name}", wrapper_text, skill_dir.name)

    def test_skill_markdown_links_resolve(self) -> None:
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")
        for skill_dir in self.skills:
            text = read_text(skill_dir / "SKILL.md")
            for raw_target in link_pattern.findall(text):
                if "://" in raw_target or raw_target.startswith("#"):
                    continue
                linked_path = (skill_dir / raw_target).resolve()
                self.assertTrue(
                    linked_path.exists(),
                    f"{skill_dir.name} links to missing file: {raw_target}",
                )

    def test_github_actions_runs_validation_on_windows_and_ubuntu(self) -> None:
        required_fragments = [
            "name: Validate",
            "pull_request:",
            "ubuntu-latest",
            "windows-latest",
            "actions/checkout@v4",
            "actions/setup-python@v5",
            "python -B -m unittest discover -s tests -p \"test_*.py\" -v",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, self.workflow_text)

    @unittest.skipUnless(sys.platform.startswith("win"), "Windows-only PowerShell smoke test")
    def test_powershell_bootstrap_smoke_test(self) -> None:
        shell = shutil.which("powershell") or shutil.which("pwsh")
        if not shell:
            self.skipTest("PowerShell is not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            remote_dir = self.create_remote_repo_snapshot(base_dir)
            project_dir = self.prepare_project_dir(base_dir)
            script = self.render_powershell_smoke_script(remote_dir)

            first_run = run_command(
                [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                project_dir,
            )
            self.assert_command_ok(first_run, "first PowerShell bootstrap run")

            second_run = run_command(
                [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                project_dir,
            )
            self.assert_command_ok(second_run, "second PowerShell bootstrap run")

            self.verify_bootstrap_result(project_dir)

    @unittest.skipIf(sys.platform.startswith("win"), "Unix-only bash smoke test")
    def test_bash_bootstrap_smoke_test(self) -> None:
        shell = shutil.which("bash")
        if not shell:
            self.skipTest("bash is not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            remote_dir = self.create_remote_repo_snapshot(base_dir)
            project_dir = self.prepare_project_dir(base_dir)
            script = self.render_bash_smoke_script(remote_dir)

            first_run = run_command([shell, "-lc", script], project_dir)
            self.assert_command_ok(first_run, "first bash bootstrap run")

            second_run = run_command([shell, "-lc", script], project_dir)
            self.assert_command_ok(second_run, "second bash bootstrap run")

            self.verify_bootstrap_result(project_dir)


if __name__ == "__main__":
    unittest.main()
