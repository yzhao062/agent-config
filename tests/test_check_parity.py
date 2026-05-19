"""Smoke + behavioral tests for scripts/check-parity.sh.

The script is a maintainer-only tool that runs against both ac and aa clones,
so full fidelity requires both to be present. The behavioral tests build a
minimal fake ac+aa tree in a tempdir and invoke the script via its `AA_ROOT`
argument, which lets us cover each exit-code contract without depending on
the real sibling clone.
"""

from __future__ import annotations

import pathlib
import platform
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check-parity.sh"


def _find_bash() -> str | None:
    """Return a real bash executable path, avoiding the WSL relay on Windows.

    On Windows, the WSL relay at C:\\Windows\\System32\\bash.exe shows up on
    PATH first and errors with "execvpe(/bin/bash) failed" when invoked from
    Python subprocess. Prefer Git Bash explicitly.
    """
    if platform.system() == "Windows":
        candidates = [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
        ]
        for path in candidates:
            if pathlib.Path(path).is_file():
                return path
        return None
    return shutil.which("bash")


BASH = _find_bash()


def _build_fake_tree(base: pathlib.Path):
    """Build a minimal ac+aa pair the script judges clean.

    Populates every file in the script's STRICT and BY-DESIGN lists.
    STRICT files get identical content on both sides; BY-DESIGN files get
    different content. The real check-parity.sh is copied into
    ``ac/scripts/`` so the script's AC_ROOT resolution lands on the fake
    tree rather than the real repo, and into ``aa/scripts/`` so the
    STRICT byte-equality check (which includes the script itself) passes.
    """
    ac = base / "ac"
    aa = base / "aa"
    for repo in (ac, aa):
        (repo / "scripts").mkdir(parents=True)
        (repo / ".claude" / "commands").mkdir(parents=True)
        (repo / ".githooks").mkdir(parents=True)
        (repo / "bootstrap").mkdir(parents=True)
        (repo / "skills").mkdir(parents=True)
        (repo / "user").mkdir(parents=True)
        (repo / ".github" / "workflows").mkdir(parents=True)

    strict_files = {
        "scripts/_python": "#!/usr/bin/env bash\nexec python3 \"$@\"\n",
        "scripts/guard.py": "# guard stub\n",
        "scripts/session_bootstrap.py": "# session bootstrap stub\n",
        "scripts/statusline.py": "# statusline stub\n",
        "scripts/generate_agent_configs.py": "# generator stub\n",
        "scripts/pre-push-smoke.sh": "#!/bin/bash\nexit 0\n",
        "scripts/remote-smoke.sh": "#!/bin/bash\nexit 0\n",
        ".claude/settings.json": "{}\n",
        ".githooks/pre-push": "#!/bin/bash\nexit 0\n",
        ".github/workflows/real-agent-smoke.yml": "name: smoke\non: push\n",
        ".github/workflows/validate.yml": "name: validate\non: push\njobs:\n  repo-validation: {}\n",
        "bootstrap/bootstrap.sh": "# bootstrap stub\n",
        "bootstrap/bootstrap.ps1": "# bootstrap ps1 stub\n",
    }
    for rel, content in strict_files.items():
        (ac / rel).write_text(content)
        (aa / rel).write_text(content)

    # Shared-contract test files added to STRICT in 2026-05-16 (closes
    # the tests/ drift that broke aa CI on every shared-skill change).
    strict_test_files = (
        "tests/test_dispatch_codex.py",
        "tests/test_health_check.py",
        "tests/test_guard.py",
        "tests/test_prompt_byte_parity.py",
    )
    for repo in (ac, aa):
        (repo / "tests").mkdir(exist_ok=True)
    for rel in strict_test_files:
        content = f"# stub: {rel}\n"
        (ac / rel).write_text(content)
        (aa / rel).write_text(content)

    for skill in ("implement-review", "my-router", "ci-mockup-figure", "readme-polish"):
        rel = f".claude/commands/{skill}.md"
        content = f"# pointer: {skill}\n"
        (ac / rel).write_text(content)
        (aa / rel).write_text(content)

    for skill in ("implement-review", "ci-mockup-figure", "readme-polish"):
        (ac / f"skills/{skill}").mkdir()
        (aa / f"skills/{skill}").mkdir()
        (ac / f"skills/{skill}/SKILL.md").write_text(f"# {skill}\n")
        (aa / f"skills/{skill}/SKILL.md").write_text(f"# {skill}\n")

    by_design = {
        "AGENTS.md": ("# ac AGENTS (USC section)\n", "# aa AGENTS\n"),
        "user/settings.json": ("{\"additionalDirectories\": []}\n", "{}\n"),
    }
    for rel, (ac_content, aa_content) in by_design.items():
        (ac / rel).write_text(ac_content)
        (aa / rel).write_text(aa_content)

    (ac / "skills/my-router").mkdir()
    (aa / "skills/my-router").mkdir()
    (ac / "skills/my-router/SKILL.md").write_text("# ac router (NSF flavor)\n")
    (aa / "skills/my-router/SKILL.md").write_text("# aa router (generic)\n")

    script_text = SCRIPT.read_text(encoding="utf-8")
    (ac / "scripts/check-parity.sh").write_text(script_text)
    (aa / "scripts/check-parity.sh").write_text(script_text)
    return ac, aa


def _run(ac_root: pathlib.Path, aa_root: pathlib.Path):
    result = subprocess.run(
        [BASH, str(ac_root / "scripts/check-parity.sh"), str(aa_root)],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr


class CheckParityScriptExists(unittest.TestCase):
    def test_script_present(self):
        self.assertTrue(SCRIPT.is_file(), f"expected {SCRIPT} to exist")

    def test_script_has_shebang(self):
        first_line = SCRIPT.read_text(encoding="utf-8").splitlines()[0]
        self.assertTrue(
            first_line.startswith("#!"),
            f"expected shebang on first line, got {first_line!r}",
        )

    @unittest.skipUnless(BASH, "bash not found")
    def test_script_shell_syntax_clean(self):
        result = subprocess.run(
            [BASH, "-n", str(SCRIPT)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"bash -n failed: stdout={result.stdout!r}, stderr={result.stderr!r}",
        )


@unittest.skipUnless(BASH, "bash not found")
class CheckParityBehavior(unittest.TestCase):
    def test_clean_run_exits_0(self):
        with tempfile.TemporaryDirectory() as d:
            ac, aa = _build_fake_tree(pathlib.Path(d))
            rc, out = _run(ac, aa)
            self.assertEqual(rc, 0, f"expected 0, got {rc}; output:\n{out}")
            self.assertIn("STRICT clean", out)

    def test_strict_drift_exits_1(self):
        with tempfile.TemporaryDirectory() as d:
            ac, aa = _build_fake_tree(pathlib.Path(d))
            (aa / "scripts/guard.py").write_text("drifted\n")
            rc, out = _run(ac, aa)
            self.assertEqual(rc, 1, f"expected 1, got {rc}; output:\n{out}")
            self.assertIn("scripts/guard.py", out)
            self.assertIn("DRIFT", out)

    def test_shipped_pointer_drift_ignored_after_v040(self):
        # Since aa v0.4.0 dropped the 4 shipped .claude/commands/*.md
        # pointers from STRICT (pack-emitted via kind: skill dispatch,
        # not aa-core source requiring byte-identical parity), drift in
        # these files must NOT fail the parity check. Guards against a
        # regression that re-adds them to STRICT. See
        # pack-architecture.md § "STRICT parity trajectory".
        with tempfile.TemporaryDirectory() as d:
            ac, aa = _build_fake_tree(pathlib.Path(d))
            (aa / ".claude/commands/my-router.md").write_text("drifted pointer\n")
            rc, out = _run(ac, aa)
            self.assertEqual(rc, 0, f"expected 0 (drift ignored), got {rc}; output:\n{out}")
            self.assertNotIn(".claude/commands/my-router.md", out)

    def test_strict_workflow_drift_exits_1(self):
        # Guards against drift in shared parts of validate.yml (action versions,
        # matrix changes, unittest command etc.) now that it is STRICT.
        with tempfile.TemporaryDirectory() as d:
            ac, aa = _build_fake_tree(pathlib.Path(d))
            (aa / ".github/workflows/validate.yml").write_text(
                "name: validate\non: push\njobs:\n  drifted: {}\n"
            )
            rc, out = _run(ac, aa)
            self.assertEqual(rc, 1)
            self.assertIn("validate.yml", out)

    def test_missing_by_design_file_exits_1(self):
        with tempfile.TemporaryDirectory() as d:
            ac, aa = _build_fake_tree(pathlib.Path(d))
            (aa / "AGENTS.md").unlink()
            rc, out = _run(ac, aa)
            self.assertEqual(rc, 1, f"expected 1, got {rc}; output:\n{out}")
            self.assertIn("AGENTS.md", out)

    def test_missing_my_router_dir_exits_1(self):
        with tempfile.TemporaryDirectory() as d:
            ac, aa = _build_fake_tree(pathlib.Path(d))
            shutil.rmtree(aa / "skills/my-router")
            rc, out = _run(ac, aa)
            self.assertEqual(rc, 1, f"expected 1, got {rc}; output:\n{out}")
            self.assertIn("my-router", out)

    def test_missing_aa_root_exits_2(self):
        with tempfile.TemporaryDirectory() as d:
            result = subprocess.run(
                [BASH, str(SCRIPT), str(pathlib.Path(d) / "nonexistent")],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
