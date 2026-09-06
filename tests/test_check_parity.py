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
import sys
import tempfile
import unittest

# tests/ is on sys.path under `unittest discover -s tests` but not under
# `python -m unittest tests.<module>`, which validate.yml uses for the
# Sentinel redaction smoke. Put it there before the sibling import.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _quiet_spawn  # noqa: E402,F401  installs a windowless spawn default on Windows


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check-parity.sh"


def _strict_test_files() -> tuple[str, ...]:
    """Read the gated test list out of the script instead of restating it.

    The fixture has to seed every path the script gates, so a hand-copied list
    here turns any addition to the script into two failures in tests that have
    nothing to do with the change. That is drift of exactly the kind the gated
    list exists to prevent, one level up.
    """
    text = SCRIPT.read_text(encoding="utf-8")
    _, _, after = text.partition("strict_test_files=(")
    body, closed, _ = after.partition("\n)")
    assert closed, "check-parity.sh: unterminated strict_test_files array"
    files = []
    for raw in body.splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            files.append(line)
    assert "tests/test_health_check.py" in files, (
        f"parsed strict_test_files looks wrong: {files}")
    return tuple(files)


# Reading the list out of the script keeps the fixture from drifting, but it
# also lets the file under test define its own oracle: delete a row and the
# fixture simply seeds one fewer file while every parity test stays green.
# These names govern code both repositories run from the same bytes, so their
# membership is asserted here instead of inferred.
STRICT_MEMBERSHIP_FLOOR = (
    "tests/_quiet_spawn.py",
    "tests/test_dispatch_codex.py",
    "tests/test_dispatch_copilot.py",
    "tests/test_dispatch_claude.py",
    "tests/test_dispatch_task.py",
    "tests/test_health_check.py",
    "tests/test_guard.py",
    "tests/test_session_bootstrap.py",
    "tests/test_pointer_files.py",
    "tests/test_prompt_byte_parity.py",
    "tests/test_bootstrap_preflight.py",
    "tests/test_dispatch_path_resolution.py",
    "tests/test_codex_usage.py",
    "tests/test_line_endings.py",
    "tests/test_skill_md_contract.py",
    "tests/test_await_review.py",
    "tests/test_auto_watch.py",
    "tests/test_stall_watch.py",
    "tests/test_prun_report.py",
    "tests/test_prun_snapshot.py",
    "tests/test_style_audit.py",
)


class StrictMembershipTests(unittest.TestCase):
    def test_every_current_member_stays_in_the_strict_list(self):
        """A snapshot, so dropping any row is a deliberate edit in two files."""
        listed = _strict_test_files()
        for name in STRICT_MEMBERSHIP_FLOOR:
            with self.subTest(name):
                self.assertIn(
                    name, listed,
                    f"{name} governs shared code and must stay gated by "
                    "scripts/check-parity.sh",
                )

    def test_new_members_are_added_to_the_floor(self):
        """The snapshot has to grow with the list, or it stops being one."""
        listed = set(_strict_test_files())
        missing = listed - set(STRICT_MEMBERSHIP_FLOOR)
        self.assertEqual(
            missing, set(),
            "scripts/check-parity.sh gained entries that STRICT_MEMBERSHIP_FLOOR "
            "does not name; add them here so a later deletion is caught",
        )


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
        "scripts/agent-quota.py": "# agent-quota stub\n",
        "scripts/generate_agent_configs.py": "# generator stub\n",
        "scripts/merge_settings.py": "# settings merge stub\n",
        "scripts/pre-push-smoke.sh": "#!/bin/bash\nexit 0\n",
        "scripts/remote-smoke.sh": "#!/bin/bash\nexit 0\n",
        ".claude/settings.json": "{}\n",
        ".githooks/pre-push": "#!/bin/bash\nexit 0\n",
        ".github/workflows/real-agent-smoke.yml": "name: smoke\non: push\n",
        ".github/workflows/validate.yml": "name: validate\non: push\njobs:\n  repo-validation: {}\n",
        "bootstrap/bootstrap.sh": "# bootstrap stub\n",
        "bootstrap/bootstrap.ps1": "# bootstrap ps1 stub\n",
        "bootstrap/todo-readme.md": "# todo drop-box stub\n",
    }
    for rel, content in strict_files.items():
        (ac / rel).write_text(content)
        (aa / rel).write_text(content)

    # Shared-contract test files added to STRICT in 2026-05-16 (closes
    # the tests/ drift that broke aa CI on every shared-skill change).
    # test_bootstrap_preflight.py joined the list in v0.7.0 alongside
    # bootstrap.sh/.ps1's git-preflight helper, which is shared STRICT.
    strict_test_files = _strict_test_files()
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

    for skill in (
        "implement-review",
        "ci-mockup-figure",
        "readme-polish",
        "prun",
        "editable-figure",
    ):
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
    def _tree_with_differing_caches(self, d):
        ac, aa = _build_fake_tree(pathlib.Path(d))
        for root, marker in ((ac, b"ac bytecode"), (aa, b"aa bytecode")):
            cache = root / "skills/prun/__pycache__"
            cache.mkdir(parents=True)
            (cache / "prun_state.cpython-312.pyc").write_bytes(marker)
        return ac, aa

    def test_bytecode_caches_do_not_count_as_drift(self):
        """Round 1 review, Low 7: every recursive diff gained
        --exclude=__pycache__, and nothing exercised it. Bytecode is
        environment-specific and appears whenever an agent or a test imports a
        helper out of a skill tree, which six shipped Python helpers under
        skills/ already allow."""
        with tempfile.TemporaryDirectory() as d:
            ac, aa = self._tree_with_differing_caches(d)
            rc, out = _run(ac, aa)
            self.assertEqual(rc, 0, out)
            self.assertNotIn("__pycache__", out)

    def test_a_real_skill_difference_beside_a_cache_still_fails(self):
        """The exclusion must not blind the gate to the drift it exists for."""
        with tempfile.TemporaryDirectory() as d:
            ac, aa = self._tree_with_differing_caches(d)
            (aa / "skills/prun/SKILL.md").write_text("# drifted" + chr(10))
            rc, out = _run(ac, aa)
            self.assertEqual(rc, 1, out)
            self.assertIn("skills/prun/", out)

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

    def test_shared_test_drift_exits_1(self):
        """The gated-test loop has to be exercised, not just populated.

        Every other case here drifts a file from a different list. With no case
        that drifts a gated test, a one-line edit emptying that loop leaves the
        membership assertions parsing happily and the whole suite green while
        the gate stops comparing anything.
        """
        with tempfile.TemporaryDirectory() as d:
            ac, aa = _build_fake_tree(pathlib.Path(d))
            (aa / "tests/test_dispatch_codex.py").write_text("drifted\n")
            rc, out = _run(ac, aa)
            self.assertEqual(rc, 1, f"expected 1, got {rc}; output:\n{out}")
            self.assertIn("tests/test_dispatch_codex.py", out)
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

    def test_both_roots_the_same_tree_exits_2(self):
        # The argument names the anywhere-agents clone. Handed the agent-config
        # one, both roots resolve to the same tree and every comparison passes
        # because nothing is being compared. Two runs during the v0.7.15 review
        # reported STRICT clean that way, one of them the reviewer's own
        # verification, so the vacuous pass has to be refused rather than
        # printed.
        with tempfile.TemporaryDirectory() as d:
            ac, _aa = _build_fake_tree(pathlib.Path(d))
            rc, out = _run(ac, ac)
            self.assertEqual(rc, 2, f"expected 2, got {rc}; output:\n{out}")
            self.assertIn("both roots resolve to", out)

    def test_the_aa_internal_flag_accepts_one_tree(self):
        # The wheel-mirror block needs one tree where every other block needs
        # two, and CI checks anywhere-agents out on its own. --aa-internal-only
        # is how that run says so; without it the run has to name the same tree
        # twice and gets refused, which is what took the release CI down.
        with tempfile.TemporaryDirectory() as d:
            _ac, aa = _build_fake_tree(pathlib.Path(d))
            result = subprocess.run(
                [BASH, str(aa / "scripts/check-parity.sh"),
                 "--aa-internal-only", str(aa)],
                capture_output=True,
                text=True,
            )
            out = result.stdout + result.stderr
            self.assertNotIn("both roots resolve to", out, out)
            self.assertEqual(result.returncode, 0, out)
            # The cross-repo headers must not appear: their answer would be
            # about one tree compared with itself.
            self.assertNotIn("strict byte-identical", out, out)
            self.assertNotIn("expected to differ by design", out, out)

    def test_a_symlink_to_the_same_tree_exits_2(self):
        # `pwd -P` rather than a string compare: two spellings of one directory
        # are the same self-comparison.
        with tempfile.TemporaryDirectory() as d:
            ac, _aa = _build_fake_tree(pathlib.Path(d))
            alias = pathlib.Path(d) / "alias"
            try:
                alias.symlink_to(ac, target_is_directory=True)
            except (OSError, NotImplementedError) as exc:
                self.skipTest(f"cannot create a directory symlink here: {exc}")
            rc, out = _run(ac, alias)
            self.assertEqual(rc, 2, f"expected 2, got {rc}; output:\n{out}")


if __name__ == "__main__":
    unittest.main()
