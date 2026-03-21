import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
GITIGNORE = ROOT / ".gitignore"
WORKFLOW = ROOT / ".github" / "workflows" / "validate.yml"
SKILLS_DIR = ROOT / "skills"
POINTER_DIR = ROOT / ".claude" / "commands"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def skill_dirs() -> list[Path]:
    return sorted(path for path in SKILLS_DIR.iterdir() if path.is_dir())


class RepoValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.agents_text = read_text(AGENTS)
        cls.readme_text = read_text(README)
        cls.gitignore_text = read_text(GITIGNORE)
        cls.workflow_text = read_text(WORKFLOW)
        cls.skills = skill_dirs()

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
        for entry in ("/.agent-config/", "/.claude/settings.local.json", "/.idea/"):
            self.assertIn(entry, self.gitignore_text)

    def test_readme_describes_bootstrap_and_validation_targets(self) -> None:
        expected = [
            "**`AGENTS.md`**",
            "**`skills/`**",
            "**`.claude/commands/`**",
            "Auto-add `.agent-config/` to the project's `.gitignore`.",
            "阅读 AGENTS.md 并执行其中的 bootstrap 脚本。",
            "Use any Python 3.12 interpreter to run them locally:",
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
            "python -m unittest discover -s tests -p \"test_*.py\" -v",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, self.workflow_text)


if __name__ == "__main__":
    unittest.main()
