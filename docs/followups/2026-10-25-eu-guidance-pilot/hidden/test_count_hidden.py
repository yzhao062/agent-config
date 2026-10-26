import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "count_lines.py"


def run(cwd, *names):
    return subprocess.run([sys.executable, str(SCRIPT), *names], cwd=cwd,
                          capture_output=True, text=True, timeout=30)


def test_one_line_per_file(tmp_path):
    (tmp_path / "a.txt").write_text("one\ntwo\nthree\n")
    (tmp_path / "b.txt").write_text("solo\n")
    proc = run(tmp_path, "a.txt", "b.txt")
    assert proc.returncode == 0
    assert [ln.strip() for ln in proc.stdout.strip().splitlines()] == ["3 a.txt", "1 b.txt"]


def test_empty_file(tmp_path):
    (tmp_path / "e.txt").write_text("")
    assert run(tmp_path, "e.txt").stdout.strip() == "0 e.txt"
