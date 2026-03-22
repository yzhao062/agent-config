import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "figure-prompt-builder" / "scripts" / "init_figure_spec.py"


class FigurePromptBuilderScriptTests(unittest.TestCase):
    def run_script(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_help_lists_current_archetypes(self) -> None:
        result = self.run_script(ROOT, "--help")

        self.assertEqual(result.returncode, 0, result.stderr)
        for archetype in (
            "overview-architecture",
            "local-mechanism-or-subsystem",
            "workflow-or-method-pipeline",
            "method-composite",
            "concept-illustration",
            "timeline-or-work-plan",
        ):
            self.assertIn(archetype, result.stdout)
        self.assertNotIn("ecosystem-or-adoption", result.stdout)
        self.assertNotIn("evidence-or-impact", result.stdout)
        self.assertNotIn("thrust-mechanism", result.stdout)

    def test_creates_spec_with_current_archetype(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "demo-workspace"
            workspace.mkdir()

            result = self.run_script(
                ROOT,
                "--workspace-dir",
                str(workspace),
                "--name",
                "demo-figure",
                "--archetype",
                "method-composite",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            spec_path = workspace / "figure-spec" / "demo-figure.md"
            self.assertTrue(spec_path.exists())
            self.assertIn("Archetype: `method-composite`", spec_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
