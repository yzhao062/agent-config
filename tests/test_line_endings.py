"""No tracked text file may carry CRLF in the working tree.

`.gitattributes` (`* text=auto eol=lf`) already guarantees that what gets
*committed* is LF, so this is not about the repository's history. It is
about the working tree, because two gates compare working-tree bytes
rather than committed bytes:

- ``scripts/check-parity.sh`` runs ``diff -q`` between the agent-config and
  anywhere-agents trees, and between the aa source and its wheel-bundled
  mirror.
- ``scripts/vendor-packs.py check`` compares the vendored package against a
  text rewrite of ``scripts/packs/*``.

A file rewritten by a helper script that opened it in Python's text mode on
Windows comes back with CRLF. Git will normalize it on the next commit, so
the diff looks clean, but until then both gates above see a byte difference
on every line and report drift that has nothing to do with content. The
usual cause is ``pathlib.Path.write_text(...)`` without ``newline=""``;
``write_bytes`` and ``newline=""`` both write exactly what they are given.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys
import unittest

# tests/ is on sys.path under `unittest discover -s tests` but not under
# `python -m unittest tests.<module>`, which validate.yml uses for the
# Sentinel redaction smoke. Put it there before the sibling import.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _quiet_spawn  # noqa: E402,F401  installs a windowless spawn default on Windows

ROOT = pathlib.Path(__file__).resolve().parents[1]

# Extensions whose content is binary even though git may track them.
_BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".whl",
    ".woff", ".woff2", ".ttf", ".otf", ".xlsx", ".docx", ".pptx",
}


def _tracked_files() -> list[pathlib.Path]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        return []
    return [
        ROOT / name
        for name in result.stdout.split("\0")
        if name
    ]


class TestNoCRLFInTrackedFiles(unittest.TestCase):
    def test_tracked_text_files_use_lf(self) -> None:
        tracked = _tracked_files()
        self.assertGreater(
            len(tracked), 100,
            "git ls-files returned almost nothing; the check would pass "
            "vacuously",
        )

        offenders: list[str] = []
        scanned = 0
        for path in tracked:
            if path.suffix.lower() in _BINARY_SUFFIXES:
                continue
            try:
                data = path.read_bytes()
            except OSError:
                continue
            # A NUL byte means binary regardless of extension.
            if b"\0" in data:
                continue
            scanned += 1
            crlf = data.count(b"\r\n")
            if crlf:
                rel = path.relative_to(ROOT).as_posix()
                offenders.append(f"{rel} ({crlf} CRLF line(s))")

        self.assertGreater(
            scanned, 100,
            "too few text files scanned; the check would pass vacuously",
        )
        self.assertEqual(
            offenders, [],
            "tracked text files carry CRLF in the working tree, which makes "
            "check-parity and vendor-packs report byte drift on every line:\n  "
            + "\n  ".join(offenders)
            + "\nRewrite them as LF. When a script produces them, pass "
            'newline="" to write_text (or use write_bytes).',
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
