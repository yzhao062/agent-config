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
SCRIPT = ROOT / "skills" / "bibref-filler" / "scripts" / "check_cite_keys.py"


class BibrefFillerScriptTests(unittest.TestCase):
    def run_script(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_resolves_keys_from_bib_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tex = root / "draft.tex"
            bib_dir = root / "bibs"
            bib_dir.mkdir()
            tex.write_text("Prior work \\cite{smith2024}.\n", encoding="utf-8")
            (bib_dir / "main.bib").write_text(
                "@article{smith2024,\n"
                "  title={Exact Metadata},\n"
                "  author={Smith, Ada},\n"
                "  year={2024}\n"
                "}\n",
                encoding="utf-8",
            )

            result = self.run_script(root, "--bib-root", "bibs", "draft.tex")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Checked 1 citation uses across 1 file(s)", result.stdout)
            self.assertIn("All cite keys resolved", result.stdout)

    def test_reports_unresolved_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tex = root / "draft.tex"
            bib_dir = root / "bibs"
            bib_dir.mkdir()
            tex.write_text("Prior work \\cite{missing2024}.\n", encoding="utf-8")
            (bib_dir / "main.bib").write_text(
                "@article{present2024,\n"
                "  title={Present Entry},\n"
                "  author={Smith, Ada},\n"
                "  year={2024}\n"
                "}\n",
                encoding="utf-8",
            )

            result = self.run_script(root, "--bib-root", "bibs", "draft.tex")

            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("Unresolved cite keys:", result.stdout)
            self.assertIn("draft.tex:1 -> missing2024", result.stdout)

    def test_handles_empty_source_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            tex = root / "draft.tex"
            bib_dir = root / "bibs"
            bib_dir.mkdir()
            tex.write_text("", encoding="utf-8")

            result = self.run_script(root, "--bib-root", "bibs", "draft.tex")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Checked 0 citation uses across 1 file(s)", result.stdout)
            self.assertIn("All cite keys resolved", result.stdout)


if __name__ == "__main__":
    unittest.main()
