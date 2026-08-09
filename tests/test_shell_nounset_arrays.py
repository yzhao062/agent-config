"""Static safety checks for Bash array expansion under ``set -u``."""
from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"

NOUNSET_RE = re.compile(
    r"^\s*set\s+(?:-[A-Za-z]*u[A-Za-z]*|-o\s+nounset)\b",
    re.MULTILINE,
)
GUARDED_ARRAY_RE = re.compile(
    r'\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\[@\]\+"'
    r'\$\{(?P=name)\[@\]\}"\}'
)
BARE_ARRAY_RE = re.compile(
    r'"\$\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\[@\]\}"'
)


class ShellNounsetArraySafety(unittest.TestCase):
    def test_set_u_scripts_guard_empty_array_expansions(self) -> None:
        failures: list[str] = []
        for script in sorted(SKILLS_DIR.rglob("*.sh")):
            body = script.read_text(encoding="utf-8")
            if not NOUNSET_RE.search(body):
                continue
            scrubbed = GUARDED_ARRAY_RE.sub("", body)
            for match in BARE_ARRAY_RE.finditer(scrubbed):
                line_number = scrubbed.count("\n", 0, match.start()) + 1
                line = scrubbed.splitlines()[line_number - 1]
                if line.lstrip().startswith("#"):
                    continue
                failures.append(
                    f"{script.relative_to(ROOT)}:{line_number}:"
                    f"{match.group('name')}"
                )

        self.assertEqual(
            failures,
            [],
            "unguarded empty-array expansion under set -u; use "
            "${name[@]+\"${name[@]}\"}: " + ", ".join(failures),
        )


if __name__ == "__main__":
    unittest.main()
