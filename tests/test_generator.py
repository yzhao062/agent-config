"""Tests for scripts/generate_agent_configs.py."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# tests/ is on sys.path under `unittest discover -s tests` but not under
# `python -m unittest tests.<module>`, which validate.yml uses for the
# Sentinel redaction smoke. Put it there before the sibling import.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _quiet_spawn  # noqa: E402,F401  installs a windowless spawn default on Windows

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_agent_configs.py"
AGENTS_MD = ROOT / "AGENTS.md"
CLAUDE_MD = ROOT / "CLAUDE.md"
CODEX_MD = ROOT / "agents" / "codex.md"

GENERATED_MARKER = "GENERATED FILE"


def run_generator(root: Path, extra: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    args = [sys.executable, str(GENERATOR), "--root", str(root)]
    if extra:
        args.extend(extra)
    return subprocess.run(args, text=True, capture_output=True, check=False)


class GeneratorTests(unittest.TestCase):
    def test_generator_script_exists(self) -> None:
        self.assertTrue(GENERATOR.exists(), f"Generator not found at {GENERATOR}")

    def test_claude_md_exists_and_has_marker(self) -> None:
        self.assertTrue(CLAUDE_MD.exists(), "CLAUDE.md should be committed at repo root")
        text = CLAUDE_MD.read_text(encoding="utf-8")
        self.assertIn(GENERATED_MARKER, text, "CLAUDE.md must carry the GENERATED marker")

    def test_codex_md_exists_and_has_marker(self) -> None:
        self.assertTrue(CODEX_MD.exists(), "agents/codex.md should be committed at repo root")
        text = CODEX_MD.read_text(encoding="utf-8")
        self.assertIn(GENERATED_MARKER, text, "agents/codex.md must carry the GENERATED marker")

    def test_agent_tags_route_blocks_on_synthetic_fixture(self) -> None:
        """Tagged blocks reach only their agent's file; untagged text reaches both.

        The committed AGENTS.md carries no tagged block since the 2026-09
        rewrite, so the routing is exercised on a synthetic fixture rather
        than pinned to a heading in the real file.
        """
        fixture = "\n".join(
            [
                "# Rules",
                "",
                "Shared line for every agent.",
                "",
                "<!-- agent:claude -->",
                "## Claude-only section",
                "",
                "Only Claude Code reads this.",
                "<!-- /agent:claude -->",
                "",
                "<!-- agent:codex -->",
                "## Codex-only section",
                "",
                "Only Codex reads this.",
                "<!-- /agent:codex -->",
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "AGENTS.md").write_text(fixture, encoding="utf-8")
            result = run_generator(root, ["--quiet"])
            self.assertEqual(result.returncode, 0, f"generator failed: {result.stderr}")
            claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
            codex = (root / "agents" / "codex.md").read_text(encoding="utf-8")
        for text in (claude, codex):
            self.assertIn("Shared line for every agent.", text)
            self.assertNotIn("<!-- agent:", text, "tag markers must not survive generation")
        self.assertIn("Claude-only section", claude)
        self.assertNotIn("Codex-only section", claude,
                         "Codex-tagged content must be stripped from CLAUDE.md")
        self.assertIn("Codex-only section", codex)
        self.assertNotIn("Claude-only section", codex,
                         "Claude-tagged content must be stripped from agents/codex.md")

    def test_committed_agents_md_has_no_tagged_blocks(self) -> None:
        """The shared baseline is byte-identical in agent-config and
        anywhere-agents and carries nothing agent-specific to tag. A new tagged
        block needs a reason recorded in docs/agents-md.md."""
        text = AGENTS_MD.read_text(encoding="utf-8")
        self.assertNotIn("<!-- agent:claude -->", text)
        self.assertNotIn("<!-- agent:codex -->", text)

    def test_claude_md_keeps_shared_content(self) -> None:
        text = CLAUDE_MD.read_text(encoding="utf-8")
        self.assertIn("Writing Defaults", text)
        self.assertIn("Git Safety", text)

    def test_codex_md_keeps_shared_content(self) -> None:
        text = CODEX_MD.read_text(encoding="utf-8")
        self.assertIn("Writing Defaults", text)
        self.assertIn("Git Safety", text)

    def test_generated_files_carry_copy_paste_wrapping_clause(self) -> None:
        """The copy-paste bullet is shared, so both agents must inherit it.

        Guards against the Formatting Defaults section being moved inside an
        <!-- agent:claude --> / <!-- agent:codex --> block (anywhere-agents#27).
        """
        for path in (CLAUDE_MD, CODEX_MD):
            text = path.read_text(encoding="utf-8")
            self.assertIn("treat hard line breaks as semantic", text,
                          f"{path.name} lost the copy-paste wrapping clause")

    def test_generator_output_is_up_to_date(self) -> None:
        """Running the generator against the committed AGENTS.md produces the
        committed CLAUDE.md and agents/codex.md byte-for-byte."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            shutil.copy2(AGENTS_MD, root / "AGENTS.md")
            result = run_generator(root, ["--quiet"])
            self.assertEqual(result.returncode, 0,
                             f"generator failed: {result.stderr}")
            new_claude = (root / "CLAUDE.md").read_text(encoding="utf-8")
            new_codex = (root / "agents" / "codex.md").read_text(encoding="utf-8")
            committed_claude = CLAUDE_MD.read_text(encoding="utf-8")
            committed_codex = CODEX_MD.read_text(encoding="utf-8")
            self.assertEqual(new_claude, committed_claude,
                             "CLAUDE.md is stale. Run scripts/generate_agent_configs.py.")
            self.assertEqual(new_codex, committed_codex,
                             "agents/codex.md is stale. Run scripts/generate_agent_configs.py.")

    def test_generator_preserves_user_authored_file(self) -> None:
        """If an output file exists without the GENERATED marker, the
        generator preserves it and emits a warning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            shutil.copy2(AGENTS_MD, root / "AGENTS.md")
            user_content = "# My own rules\n\nDo not touch.\n"
            (root / "CLAUDE.md").write_text(user_content, encoding="utf-8")
            result = run_generator(root)
            self.assertEqual(result.returncode, 0)
            self.assertIn("WARNING", result.stderr, "generator must warn on preserve")
            self.assertEqual(
                (root / "CLAUDE.md").read_text(encoding="utf-8"),
                user_content,
                "hand-authored CLAUDE.md must be preserved",
            )
            self.assertTrue((root / "agents" / "codex.md").exists(),
                            "other agent files are still generated when one is preserved")

    def test_generator_nested_preserve_warning_uses_relative_path(self) -> None:
        """Warning for nested outputs (agents/codex.md) shows the full relative
        path, not just the filename, so the rename hint is actionable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            shutil.copy2(AGENTS_MD, root / "AGENTS.md")
            nested = root / "agents"
            nested.mkdir()
            (nested / "codex.md").write_text(
                "# hand-authored codex rules\n", encoding="utf-8"
            )
            result = run_generator(root)
            self.assertEqual(result.returncode, 0)
            self.assertIn("agents/codex.md", result.stderr,
                          "warning must include the full nested relative path")
            self.assertIn("agents/codex.local.md", result.stderr,
                          "warning must point at the nested .local.md path")
            self.assertNotIn("mv codex.md codex.local.md", result.stderr,
                             "warning must not drop the agents/ prefix")

    def test_generator_overwrites_its_own_output(self) -> None:
        """Files with the GENERATED marker are regenerated freely."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            shutil.copy2(AGENTS_MD, root / "AGENTS.md")
            # First generation.
            result1 = run_generator(root, ["--quiet"])
            self.assertEqual(result1.returncode, 0)
            # Mutate the file but keep the marker intact.
            claude_path = root / "CLAUDE.md"
            original = claude_path.read_text(encoding="utf-8")
            # Prepend a line under the header block; marker is inside the comment.
            claude_path.write_text(
                original + "\n<!-- mutated by test -->\n", encoding="utf-8"
            )
            # Second generation should overwrite cleanly.
            result2 = run_generator(root, ["--quiet"])
            self.assertEqual(result2.returncode, 0)
            self.assertEqual(
                claude_path.read_text(encoding="utf-8"),
                original,
                "regeneration should restore the managed file",
            )


if __name__ == "__main__":
    unittest.main()
