"""The reviewer-I/O classifier against its hand-labeled fixture.

The classifier lives beside the audit note it serves
(docs/followups/2026-09-18-skills-bloat-audit/) rather than under skills/,
because it measures the review loop and is not part of it. The fixture holds
one synthetic Codex rollout and one synthetic Antigravity tail whose every
event was labeled by hand; expected.json records those labels and the totals
the classifier produced once the labels agreed. A change to the label rules
must update both, which is the point.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "followups" / "2026-09-18-skills-bloat-audit"
SCRIPT = AUDIT / "classify_reviewer_io.py"
FIXTURE = AUDIT / "fixture"

INPUTS = {
    "codex": ("codex.jsonl", "codex.round.json"),
    "antigravity": ("tail", "tail.round.json"),
}


def _load():
    spec = importlib.util.spec_from_file_location("classify_reviewer_io", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ClassifierFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load()
        cls.expected = json.loads((FIXTURE / "expected.json").read_text(encoding="utf-8"))

    def test_fixture_files_exist(self) -> None:
        for name in ("codex.jsonl", "codex.round.json", "tail", "tail.round.json",
                     "prompt-relay", "expected.json"):
            self.assertTrue((FIXTURE / name).is_file(), name)

    def test_every_hand_label_matches(self) -> None:
        for backend, (inp, rnd) in INPUTS.items():
            with self.subTest(backend):
                report = self.module.classify(FIXTURE / inp, FIXTURE / rnd)
                self.assertEqual(report["backend"], backend)
                got = {r["event_id"]: {"class": r["class"], "label": r["label"]}
                       for r in report["events"]}
                self.assertEqual(got, self.expected[backend]["events"])

    def test_totals_match_and_never_fold_unresolved(self) -> None:
        for backend, (inp, rnd) in INPUTS.items():
            with self.subTest(backend):
                report = self.module.classify(FIXTURE / inp, FIXTURE / rnd)
                self.assertEqual(report["totals"], self.expected[backend]["totals"])
                labels = report["totals"]["by_label"]
                self.assertEqual(
                    labels["required"] + labels["avoidable"] + labels["unresolved"],
                    report["totals"]["tool_output_total"])
                self.assertGreater(labels["unresolved"], 0,
                                   "the fixture carries an unresolved case on purpose")

    def test_prompt_bytes_stay_out_of_the_tool_totals(self) -> None:
        codex = self.module.classify(FIXTURE / "codex.jsonl", FIXTURE / "codex.round.json")
        self.assertEqual(codex["injected_bytes"], self.expected["codex"]["injected_bytes"])
        self.assertEqual(codex["prompt_bytes"], self.expected["codex"]["prompt_bytes"])
        self.assertNotIn("injected_bytes", codex["totals"]["by_class"])
        self.assertEqual(codex["totals"]["tool_output_total"],
                         sum(r["output_bytes"] for r in codex["events"]))
        agy = self.module.classify(FIXTURE / "tail", FIXTURE / "tail.round.json")
        for key in ("preamble_bytes", "request_bytes", "diff_bytes_prompt"):
            self.assertEqual(agy[key], self.expected["antigravity"][key], key)

    def test_the_eight_specified_cases_by_name(self) -> None:
        """The plan names eight cases; pin each to its event so a fixture edit
        cannot quietly drop one."""
        codex = self.expected["codex"]["events"]
        self.assertEqual(codex["c1"], {"class": "rules", "label": "required"})              # AGENTS.local.md not supplied
        self.assertEqual(codex["c2"], {"class": "coordinator_skill", "label": "required"})  # skill under review
        self.assertEqual(codex["c3"]["label"], "required")                                  # two ranges of one file
        self.assertEqual(codex["c4"]["label"], "required")
        self.assertEqual(codex["c5"], {"class": "coordinator_skill", "label": "required"})  # verification reason
        self.assertEqual(codex["c6"], {"class": "diff", "label": "avoidable"})              # second diff obtain
        self.assertEqual(codex["c7"], {"class": "rules", "label": "avoidable"})             # supplied AGENTS.md re-read
        self.assertEqual(codex["c8"], {"class": "coordinator_skill", "label": "avoidable"}) # example review, no reason
        self.assertEqual(codex["c9"], {"class": "coordinator_skill", "label": "unresolved"})  # range read, no reason
        self.assertEqual(codex["c11"], {"class": "source", "label": "avoidable"})           # same range again
        # Round-2 additions (execution review): argv payloads, executed scripts,
        # range identity for instruction files, and a mixed event.
        self.assertEqual(codex["c12"], {"class": "source", "label": "required"})            # first of two files under the wrapper
        self.assertEqual(codex["c13"], {"class": "source", "label": "required"})            # second file, not a repeat of the first
        self.assertEqual(codex["c14"], {"class": "tests_builds", "label": "required"})      # coordinator script executed, not read
        self.assertEqual(codex["c15"], {"class": "rules", "label": "required"})             # AGENTS.local.md lines 1-20
        self.assertEqual(codex["c16"], {"class": "rules", "label": "required"})             # lines 21-40 are a different read
        self.assertEqual(codex["c17"], {"class": "rules", "label": "unresolved"})           # supplied AGENTS.md + in-scope file in one output
        self.assertEqual(codex["c18"], {"class": "other", "label": "required"})             # a body only stored, nothing run: inert data
        self.assertEqual(codex["c19"], {"class": "tests_builds", "label": "required"})      # quoted interpreter path
        self.assertEqual(codex["c20"], {"class": "tests_builds", "label": "required"})      # pwsh -File operand
        self.assertEqual(codex["c21"], {"class": "rules", "label": "avoidable"})            # supplied rule read again
        self.assertEqual(codex["c22"], {"class": "rules", "label": "unresolved"})           # mixed event judged before the repeat rule
        self.assertEqual(codex["c23"], {"class": "rules", "label": "avoidable"})            # identical mixed command repeated
        self.assertEqual(codex["c24"], {"class": "source", "label": "required"})            # search keyed by pattern
        self.assertEqual(codex["c25"], {"class": "source", "label": "required"})            # different pattern, same file
        self.assertEqual(codex["c26"], {"class": "source", "label": "avoidable"})           # same search again
        self.assertEqual(codex["c27"], {"class": "source", "label": "required"})            # $n -ge/-le filter is a range
        self.assertEqual(codex["c28"], {"class": "tests_builds", "label": "unresolved"})    # executed body reads a supplied rule
        self.assertEqual(codex["c29"], {"class": "tests_builds", "label": "unresolved"})    # bash heredoc executed body
        self.assertEqual(codex["c30"]["label"], "required")                                 # 'bootstrap|router'
        self.assertEqual(codex["c31"]["label"], "required")                                 # 'bootstrap|verification' is a different search
        self.assertEqual(codex["c32"]["label"], "required")                                 # Select-String -Pattern 'bootstrap'
        self.assertEqual(codex["c33"]["label"], "required")                                 # -Pattern 'verification'
        self.assertEqual(codex["c34"]["label"], "required")
        self.assertEqual(codex["c35"]["label"], "required")                                 # -C 20 adds context
        self.assertEqual(codex["c36"], {"class": "coordinator_skill", "label": "avoidable"})  # exact repeat
        self.assertEqual(codex["c37"], {"class": "tests_builds", "label": "unresolved"})    # stored then run in one event
        self.assertEqual(codex["c38"], {"class": "tests_builds", "label": "unresolved"})    # assigned then piped
        self.assertEqual(codex["c39"]["label"], "required")                                 # '^  - item'
        self.assertEqual(codex["c40"]["label"], "required")                                 # '^ - item' differs by one space
        self.assertEqual(codex["c41"], {"class": "source", "label": "avoidable"})           # identical command
        self.assertEqual(codex["c42"], {"class": "other", "label": "unresolved"})           # stored then run directly
        self.assertEqual(codex["c43"], {"class": "other", "label": "unresolved"})           # Invoke-Expression consumer
        self.assertEqual(codex["c44"], {"class": "other", "label": "required"})             # assignment only is storage
        self.assertEqual(codex["c45"], {"class": "other", "label": "unresolved"})           # expandable here-string
        self.assertEqual(codex["c46"], {"class": "other", "label": "unresolved"})           # expanded before storage (-PassThru)
        self.assertEqual(codex["c47"], {"class": "other", "label": "unresolved"})           # unquoted heredoc delimiter
        self.assertEqual(codex["c48"], {"class": "other", "label": "required"})             # quoted heredoc stored: data
        self.assertEqual(codex["c49"], {"class": "other", "label": "unresolved"})           # bare literal here-string is not storage
        self.assertEqual(codex["c50"], {"class": "tests_builds", "label": "unresolved"})    # inline -c source reads a supplied rule
        self.assertEqual(codex["c51"], {"class": "tests_builds", "label": "unresolved"})    # inline -c source reads the coordinator skill
        self.assertEqual(codex["c52"], {"class": "tests_builds", "label": "required"})      # benign inline code
        self.assertEqual(codex["c53"], {"class": "other", "label": "required"})             # <<"EOF" is literal in bash
        agy = self.expected["antigravity"]["events"]
        self.assertEqual(agy["a0"], {"class": "diff", "label": "avoidable"})                # embedded transport
        self.assertEqual(agy["a7"], {"class": "rules", "label": "avoidable"})               # repeated rule read
        self.assertEqual(agy["a9"], {"class": "coordinator_skill", "label": "unresolved"})
        self.assertEqual(agy["a13"], {"class": "rules", "label": "required"})
        self.assertEqual(agy["a14"], {"class": "rules", "label": "required"})
        self.assertEqual(agy["a15"], {"class": "tests_builds", "label": "required"})

    def test_cli_prints_the_totals(self) -> None:
        for backend, (inp, rnd) in INPUTS.items():
            with self.subTest(backend):
                proc = subprocess.run(
                    [sys.executable, str(SCRIPT), "--input", str(FIXTURE / inp),
                     "--round", str(FIXTURE / rnd)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    cwd=str(ROOT),
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("Totals by label (tool-output bytes):", proc.stdout)
                self.assertIn("tool_output_total", proc.stdout)
                self.assertIn("Unresolved events", proc.stdout)

    def test_cli_usage_error_exits_two(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "--input", str(FIXTURE / "missing"),
             "--round", str(FIXTURE / "codex.round.json")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 2)


MEASURE = AUDIT / "measure_acceptance.py"
CORPUS_MANIFEST = AUDIT / "corpus-manifest.json"


class CorpusManifestTests(unittest.TestCase):
    """The manifest states the acceptance cohort; these guard that statement.

    The published record is only evidence if it can be recomputed, and it used
    to select its before cohort by globbing a session scratchpad and dropping
    whatever classified to zero. The scratchpad is temporary, the two dates
    involved hold 108 sessions, with 90 outside both cohorts. A missing input
    produced an empty table and exit 0.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(CORPUS_MANIFEST.read_text(encoding="utf-8"))

    def test_cohort_sizes_match_the_published_tables(self) -> None:
        before = self.manifest["before"]
        counted = [e for e in before if e["included"]]
        self.assertEqual(len(before), 14, "the audit sampled 14 before rollouts")
        self.assertEqual(
            len(counted), 11,
            "the published before table totals 11 rounds; the other three are "
            "the zero-output setup probes")
        self.assertEqual(len(self.manifest["after"]), 4)

    def test_every_entry_is_identifiable_and_hashed(self) -> None:
        seen = set()
        for cohort in ("before", "after"):
            for entry in self.manifest[cohort]:
                stem = entry["stem"]
                with self.subTest(cohort=cohort, stem=stem):
                    self.assertNotIn(stem, seen, "a stem appears twice")
                    seen.add(stem)
                    self.assertRegex(entry["sha256"], r"\A[0-9a-f]{64}\Z")
                    self.assertIn(entry["scope"], ("paper", "trading"))

    def test_every_exclusion_gives_its_reason(self) -> None:
        for entry in self.manifest["before"]:
            if not entry["included"]:
                with self.subTest(stem=entry["stem"]):
                    self.assertTrue(
                        entry.get("excluded_because", "").strip(),
                        "an excluded round has to say why, or the cohort is "
                        "again something a reader has to infer")

    def test_every_stem_is_a_full_session_name(self) -> None:
        """A truncated stem is the prefix matching this change set out to remove.

        Resolution globs `<stem>*.jsonl`. A timestamp-only prefix resolves to one
        file today and the hash would catch a wrong one, but a second session
        starting in the same second makes the entry ambiguous, and ambiguity is a
        refusal. A full stem carries the session uuid and cannot collide.
        """
        for cohort in ("before", "after"):
            for entry in self.manifest[cohort]:
                with self.subTest(cohort=cohort, stem=entry["stem"]):
                    self.assertRegex(
                        entry["stem"],
                        r"\Arollout-\d{4}-\d{2}-\d{2}T[\d-]+-[0-9a-f]{8}-[0-9a-f-]+\Z")


class CorpusRejectionTests(unittest.TestCase):
    """What the resolver refuses, measured against a cohort small enough to hold.

    The first version of these tests withheld all but one of the eighteen real
    inputs, so every run failed on the seventeen absent ones whatever the case
    under test did. Turning the hash and ambiguity errors into warnings left
    them all green: they proved the branch ran, not that it rejected. Each test
    here starts from a synthetic cohort that passes, then changes exactly one
    thing, which is what makes the exit code attributable.
    """

    BUSY = FIXTURE / "codex.jsonl"          # classifies to 10,691 bytes
    QUIET = b'{"type":"event_msg","payload":{}}\n'   # no CommandExecution: zero

    def _cohort(self, root: Path, *, quiet_included: bool = False,
                busy_excluded: bool = False) -> Path:
        """Write a three-rollout corpus and the manifest that describes it."""
        corpus = root / "corpus"
        corpus.mkdir()
        busy = self.BUSY.read_bytes()
        files = {
            "rollout-2026-01-01T00-00-00-aaaaaaaa-0000-0000-0000-000000000001": busy,
            "rollout-2026-01-01T00-00-01-bbbbbbbb-0000-0000-0000-000000000002": self.QUIET,
            "rollout-2026-01-01T00-00-02-cccccccc-0000-0000-0000-000000000003": busy,
        }
        for stem, data in files.items():
            (corpus / f"{stem}.jsonl").write_bytes(data)

        def entry(stem, included, **extra):
            digest = hashlib.sha256(files[stem]).hexdigest()
            out = {"stem": stem, "sha256": digest, "scope": "paper",
                   "included": included}
            out.update(extra)
            return out

        stems = list(files)
        manifest = {
            "schema": 1,
            "record": "synthetic",
            "why": "synthetic",
            "acquisition": "synthetic; set ACCEPTANCE_CORPUS_DIR or pass --corpus-dir",
            "corpus_root_default": str(corpus),
            "before": [
                entry(stems[0], not busy_excluded),
                entry(stems[1], quiet_included, excluded_because="synthetic probe"),
            ],
            "after": [dict(entry(stems[2], True), label="synthetic after")],
        }
        path = root / "manifest.json"
        path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return path

    def _run(self, manifest: Path, corpus: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(MEASURE), "--manifest", str(manifest),
             "--corpus-dir", str(corpus)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )

    def _assert_refused(self, proc, code: int, needle: str, why: str) -> None:
        self.assertEqual(proc.returncode, code, f"{why}; stderr={proc.stderr!r}")
        self.assertIn(needle, proc.stderr)
        self.assertNotIn(
            "before total", proc.stdout,
            "a refused corpus must print no table at all, or a reader can take "
            "a partial one for the record")

    def test_the_synthetic_cohort_passes_before_anything_is_changed(self) -> None:
        """Without this, every case below could be passing for the wrong reason."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._cohort(root)
            proc = self._run(manifest, root / "corpus")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("before total (1)", proc.stdout)
        self.assertIn("after total (1)", proc.stdout)

    def test_a_custom_cohort_says_so_instead_of_wearing_the_published_labels(self) -> None:
        """A synthetic run must not print output that reads as the record.

        The headings name one specific pair of cohorts and the paper rounds they
        came from. Above someone else's totals they describe nothing, and the
        output can be copied as though it were the published measurement.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._cohort(root)
            proc = self._run(manifest, root / "corpus")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Custom cohort from", proc.stdout)
        self.assertIn(str(manifest), proc.stdout,
                      "the notice has to name which manifest produced this")
        self.assertIn("not the published Milestone A measurement", proc.stdout)
        self.assertNotIn(
            "rounds 7-9", proc.stdout,
            "the historical heading claims a cohort this run does not have")
        self.assertNotIn("old contract", proc.stdout)
        self.assertNotIn("new contract", proc.stdout)

    def test_one_missing_input_refuses_the_whole_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._cohort(root)
            victim = sorted((root / "corpus").glob("*.jsonl"))[0]
            victim.unlink()
            proc = self._run(manifest, root / "corpus")
        self._assert_refused(
            proc, 2, "no file under",
            "the earlier script printed `missing:` and carried on with exit 0")
        self.assertIn("ACCEPTANCE_CORPUS_DIR", proc.stderr,
                      "the failure has to say how to supply the corpus")

    def test_one_tampered_input_refuses_on_its_hash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._cohort(root)
            victim = sorted((root / "corpus").glob("*.jsonl"))[0]
            with victim.open("ab") as fh:
                fh.write(b'{"type":"event_msg","payload":{}}\n')
            proc = self._run(manifest, root / "corpus")
        self._assert_refused(proc, 2, "does not match the recorded",
                             "an edited input must not reach the table")

    def test_one_ambiguous_stem_refuses_rather_than_taking_the_first(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._cohort(root)
            corpus = root / "corpus"
            twin = corpus / "twin"
            twin.mkdir()
            victim = sorted(corpus.glob("*.jsonl"))[0]
            (twin / victim.name).write_bytes(victim.read_bytes())
            proc = self._run(manifest, corpus)
        self._assert_refused(proc, 2, "2 matches",
                             "the earlier script took hits[0]")

    def _swap(self, root: Path, manifest: Path, cohort: str, index: int,
              payload: bytes) -> subprocess.CompletedProcess:
        """Replace one rollout's bytes and keep its recorded hash honest.

        The hash has to follow, or the run stops at resolution and never reaches
        the membership check the test is about.
        """
        corpus = root / "corpus"
        order = sorted(corpus.glob("*.jsonl"))
        position = index if cohort == "before" else 2
        victim = order[position]
        victim.write_bytes(payload)
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data[cohort][index]["sha256"] = hashlib.sha256(payload).hexdigest()
        manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return self._run(manifest, corpus)

    def test_an_excluded_round_that_starts_producing_output_refuses(self) -> None:
        """Drift direction one: a probe the classifier no longer sees as silent."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = self._cohort(root)
            proc = self._swap(root, manifest, "before", 1, self.BUSY.read_bytes())
        self._assert_refused(proc, 3, "before/", "an excluded probe now produces output")
        self.assertIn("included=False", proc.stderr)

    def test_a_counted_round_that_falls_silent_refuses(self) -> None:
        """Drift direction two, in both cohorts.

        The after cohort is the half an earlier version skipped entirely: its
        loop appended every entry without checking membership, so a silent
        after round printed a row of zeros and exited 0 while the README
        promised exit 3.
        """
        for cohort, index in (("before", 0), ("after", 0)):
            with self.subTest(cohort=cohort):
                with tempfile.TemporaryDirectory() as td:
                    root = Path(td)
                    manifest = self._cohort(root)
                    proc = self._swap(root, manifest, cohort, index, self.QUIET)
                self._assert_refused(
                    proc, 3, f"{cohort}/",
                    f"a counted {cohort} round that produces nothing changes the total")
                self.assertIn("included=True", proc.stderr)

    def test_a_flag_with_no_value_is_a_usage_error(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(MEASURE), "--corpus-dir"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("needs a path", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_the_measurement_names_no_session_scratchpad(self) -> None:
        """The defect itself: a committed script pointing at a temp directory."""
        text = MEASURE.read_text(encoding="utf-8")
        for needle in ("AppData/Local/Temp", "AppData\\\\Local\\\\Temp", "/scratchpad"):
            self.assertNotIn(
                needle, text,
                f"measure_acceptance.py still refers to {needle}; a session "
                "scratchpad does not outlive the session that made it")


if __name__ == "__main__":
    unittest.main()
