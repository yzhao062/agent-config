"""Regression test: every committed .claude/commands/*.md pointer carries
.claude/skills/<name>/ in its lookup-order line. Guards against a future
pack shipping stale 2-path text (issue anywhere-agents#6).

A pointer normally resolves the skill its own filename names. An alias
pointer resolves a different one, and declares which through an `alias-of:`
key in its frontmatter. The lookup line is then checked against that target
rather than against the file stem, because the whole point of an alias is that
the two differ. `alias-of` must name a skill that exists, so a rename cannot
leave an alias resolving nothing.
"""
from __future__ import annotations

import pathlib
import re
import unittest


_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_COMMANDS_DIR = _REPO_ROOT / ".claude" / "commands"
_SKILLS_DIR = _REPO_ROOT / "skills"

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_ALIAS_RE = re.compile(r"^alias-of:[ \t]*(\S+)[ \t]*$", re.MULTILINE)


def _alias_target(text: str) -> str | None:
    """The `alias-of` value from the frontmatter block, or None.

    Only the leading `---` block counts. Scanning the whole file would let a
    body line that happens to begin with `alias-of:` reassign which skill a
    pointer resolves, which is the opposite of a declaration.
    """
    frontmatter = _FRONTMATTER_RE.match(text)
    if frontmatter is None:
        return None
    matches = _ALIAS_RE.findall(frontmatter.group(1))
    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError(f"duplicate alias-of keys: {matches}")
    return matches[0]


def _resolved_skill_name(pointer_path: pathlib.Path, text: str) -> str:
    """The skill this pointer resolves: its own stem, or its alias target."""
    target = _alias_target(text)
    return target if target is not None else pointer_path.stem


class PointerLookupOrderTests(unittest.TestCase):

    def test_every_pointer_names_three_paths_in_order(self):
        pointer_files = sorted(_COMMANDS_DIR.glob("*.md"))
        self.assertGreater(len(pointer_files), 0, "no .claude/commands/*.md files found")
        for pf in pointer_files:
            text = pf.read_text(encoding="utf-8")
            name = _resolved_skill_name(pf, text)
            # Find the lookup line (starts with "Read and follow the skill definition.")
            lookup_match = re.search(
                r"Read and follow the skill definition\.[^\n]*?\n",
                text,
            )
            self.assertIsNotNone(lookup_match,
                                 f"{pf.name}: lookup line not found")
            lookup_line = lookup_match.group(0)
            self.assertIn(f"skills/{name}/SKILL.md", lookup_line,
                          f"{pf.name}: missing project-local path")
            self.assertIn(f".claude/skills/{name}/SKILL.md", lookup_line,
                          f"{pf.name}: missing .claude/skills/ path")
            self.assertIn(f".agent-config/repo/skills/{name}/SKILL.md", lookup_line,
                          f"{pf.name}: missing .agent-config/repo/skills/ path")
            # Order: skills/ → .claude/skills/ → .agent-config/repo/skills/
            local_idx = lookup_line.index(f"skills/{name}/SKILL.md")
            claude_idx = lookup_line.index(f".claude/skills/{name}/SKILL.md")
            bootstrap_idx = lookup_line.index(f".agent-config/repo/skills/{name}/SKILL.md")
            self.assertLess(local_idx, claude_idx,
                            f"{pf.name}: skills/ must precede .claude/skills/")
            self.assertLess(claude_idx, bootstrap_idx,
                            f"{pf.name}: .claude/skills/ must precede .agent-config/repo/skills/")

    def test_every_pointer_resolves_a_skill_that_exists(self):
        """A pointer that resolves nothing is worse than no pointer.

        It looks healthy in the commands directory and fails only when someone
        invokes it. This covers canonical pointers and aliases alike, so a
        renamed or deleted skill cannot leave either kind dangling.
        """
        for pf in sorted(_COMMANDS_DIR.glob("*.md")):
            text = pf.read_text(encoding="utf-8")
            target = _resolved_skill_name(pf, text)
            with self.subTest(pointer=pf.name, target=target):
                self.assertTrue(
                    (_SKILLS_DIR / target / "SKILL.md").is_file(),
                    f"{pf.name}: resolves {target}, which has no "
                    f"skills/{target}/SKILL.md")

    def test_an_alias_may_not_name_its_own_stem(self):
        """`alias-of: <own name>` is a canonical pointer with extra words."""
        for pf in sorted(_COMMANDS_DIR.glob("*.md")):
            target = _alias_target(pf.read_text(encoding="utf-8"))
            if target is None:
                continue
            with self.subTest(pointer=pf.name):
                self.assertNotEqual(
                    target, pf.stem,
                    f"{pf.name}: alias-of names its own stem; drop the key")

    def test_a_body_line_cannot_declare_an_alias(self):
        """The key is a declaration in frontmatter, not a phrase in prose.

        Honouring it anywhere in the file would let a sentence silently
        reassign which skill a pointer resolves, and would excuse a plain
        pointer whose lookup line names the wrong skill.
        """
        smuggled = (
            "---\ndescription: ordinary\n---\n\n"
            "Read and follow the skill definition. Look for it at "
            "`skills/prun/SKILL.md` first.\n"
            "alias-of: prun\n"
        )
        self.assertIsNone(_alias_target(smuggled))
        self.assertEqual(
            _resolved_skill_name(pathlib.Path("ordinary.md"), smuggled),
            "ordinary")

    def test_duplicate_alias_keys_are_rejected(self):
        """Two declarations mean the file does not say what it resolves."""
        text = "---\nalias-of: prun\nalias-of: my-router\n---\n\nbody\n"
        with self.assertRaises(ValueError):
            _alias_target(text)

    def test_vet_resolves_implement_review(self):
        """The shipped alias, pinned by name.

        The rules above are generic, so all of them still pass if `vet` is
        quietly repointed at another skill with its lookup line changed to
        match. This is the assertion that notices.
        """
        pf = _COMMANDS_DIR / "vet.md"
        self.assertTrue(pf.is_file(), "the vet alias is missing")
        text = pf.read_text(encoding="utf-8")
        self.assertEqual(_alias_target(text), "implement-review")
        self.assertIn("implement-review", text)


if __name__ == "__main__":
    unittest.main()
