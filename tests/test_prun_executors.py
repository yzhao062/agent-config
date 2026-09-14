"""prun runs its units on Agy alone.

Routing units to Sonnet subagents billed the coordinating session's own Claude
account, and a wide fan-out consumed that quota quickly, so the skill dropped
every Claude-side worker. These checks keep a later edit from quietly putting
one back through the table, the dispatch step, or a surface that advertises the
skill.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "prun" / "SKILL.md"
POINTER = ROOT / ".claude" / "commands" / "prun.md"
OPENAI = ROOT / "skills" / "prun" / "agents" / "openai.yaml"


RELEASE_NOTE = re.compile(r"`v\d+\.\d+")


def current_prun_lines(path: Path) -> list[str]:
    """Lines naming prun that describe it now rather than narrate a past release."""
    return [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if "prun" in line and not RELEASE_NOTE.search(line)
    ]


def prun_card(index: str) -> str:
    """The prun card of the skills index, from its title to the next card."""
    rest = index[index.index("__`prun`__"):]
    end = rest.find("\n-   ")
    return rest if end == -1 else rest[:end]


def executors_table(text: str) -> list[list[str]]:
    """Rows of the table under the Executors heading, header and rule excluded."""
    section = text.split("\n## Executors\n", 1)[1].split("\n## ", 1)[0]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|") or set(line) <= {"|", "-", " "}:
            continue
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows[1:]


class PrunExecutorContractTests(unittest.TestCase):
    def test_agy_is_the_only_worker_in_the_executors_table(self) -> None:
        rows = executors_table(SKILL.read_text(encoding="utf-8"))
        names = [row[0] for row in rows]
        self.assertEqual(names, ["Agy (`agy`)", "Claude session (this session)"])
        # The coordinator's row stays, and it is never a unit.
        self.assertIn("Never a unit", rows[1][2])

    def test_no_surface_spawns_a_claude_subagent(self) -> None:
        for path in (SKILL, POINTER, OPENAI):
            with self.subTest(path.name):
                text = path.read_text(encoding="utf-8")
                self.assertIsNone(re.search(r"model:\s*[\"']?sonnet", text, re.I))

    def test_the_advertised_descriptions_name_agy_workers_only(self) -> None:
        # The pointer description is what the skill list shows every session,
        # and the OpenAI wrapper's short description is Codex's equivalent.
        pointer = POINTER.read_text(encoding="utf-8")
        description = re.search(r'^description:\s*"(.+)"$', pointer, re.M)
        self.assertIsNotNone(description)
        self.assertNotIn("Sonnet", description.group(1))
        self.assertIn("Agy", description.group(1))
        short = re.search(r'short_description:\s*"(.+)"', OPENAI.read_text(encoding="utf-8"))
        self.assertIsNotNone(short)
        self.assertNotIn("Sonnet", short.group(1))

    def test_the_prohibition_is_stated_where_units_are_assigned(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("**Never a Claude-side worker.**", text)
        self.assertIn("3. **Assign**: every unit goes to Agy.", text)

    def test_the_public_docs_do_not_route_units_to_sonnet(self) -> None:
        # anywhere-agents publishes a docs site whose prun page puts its own
        # summary above the included skill, so a stale summary contradicts the
        # skill on the same page. agent-config has no such site.
        page = ROOT / "docs" / "skills" / "prun.md"
        index = ROOT / "docs" / "skills" / "index.md"
        landing = ROOT / "docs" / "index.md"
        if not any(path.is_file() for path in (page, index, landing)):
            self.skipTest("this repository publishes no docs site")
        if page.is_file():
            self.assertNotIn("Sonnet", page.read_text(encoding="utf-8"))
        if index.is_file():
            # Every skill has a card on the index, so only the prun card is held to this.
            self.assertNotIn("Sonnet", prun_card(index.read_text(encoding="utf-8")))
        if landing.is_file():
            for line in current_prun_lines(landing):
                self.assertNotIn("Sonnet", line)

    def test_the_readmes_do_not_route_units_to_sonnet(self) -> None:
        # A README and its translation describe prun in a paragraph, a table row
        # or a tree comment. Their release-history paragraphs still name Sonnet
        # for the versions that used it, which remains true of those versions.
        readmes = [path for path in (ROOT / "README.md", ROOT / "README.zh-CN.md") if path.is_file()]
        self.assertTrue(readmes)
        for readme in readmes:
            lines = current_prun_lines(readme)
            self.assertTrue(lines, readme.name)
            for line in lines:
                with self.subTest(readme.name, line=line[:60]):
                    self.assertNotIn("Sonnet", line)


if __name__ == "__main__":
    unittest.main()
