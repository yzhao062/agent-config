"""Reporter contract for skills/prun/scripts/prun_state.py.

The reporter emits orthogonal evidence and derives nothing. Plan review round 3
established why: an exclusive class name like `salvageable` reads as "safe to
act on", which this slice cannot support without the process identity that
anywhere-agents#29 Part B would add.
"""
from __future__ import annotations

import hashlib
import io
import contextlib
import importlib.util
import json
import pathlib
import os
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _quiet_spawn  # noqa: E402,F401  installs a windowless spawn default on Windows

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "skills" / "prun" / "scripts" / "prun_state.py"


def load():
    spec = importlib.util.spec_from_file_location("_prun_state", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_unit(root, name, result_entry=None, result_body=None, tail=b""):
    """Build one unit directory. `result_entry` is the literal entry content."""
    unit = Path(root) / f"prun-task-{name}"
    unit.mkdir(parents=True)
    if tail is not None:
        (unit / "tail").write_bytes(tail)
    if result_entry is not None:
        (unit / "result-file").write_text(result_entry, encoding="utf-8")
    if result_body is not None:
        target = Path(result_entry)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(result_body, encoding="utf-8")
    return unit


def run(mod, argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = mod.main(argv)
    return code, buf.getvalue()


def tree_hash(root):
    """Recursive content hash, for proving the reporter wrote nothing.

    Directories are hashed as well as files. Hashing only file paths and
    contents let a mutant create an empty directory inside an inspected unit
    and survive the whole reporter suite, which is weaker than the claim the
    documentation makes.
    """
    h = hashlib.sha256()
    for base, dirs, files in os.walk(root):
        dirs.sort()
        for name in dirs:
            rel = os.path.relpath(os.path.join(base, name), root)
            h.update(b"dir:" + rel.encode("utf-8", "replace"))
        for name in sorted(files):
            path = os.path.join(base, name)
            h.update(b"file:")
            h.update(os.path.relpath(path, root).encode("utf-8", "replace"))
            h.update(Path(path).read_bytes())
    return h.hexdigest()


class EvidencePairTests(unittest.TestCase):
    """Every legal pair, and proof that no other pair can be emitted."""

    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name

    def _units(self):
        code, out = run(self.mod, ["report-state", "--root", self.root, "--json"])
        return code, {os.path.basename(u["unit"]): u
                      for u in json.loads(out)["units"]}

    def test_resolved_present(self):
        target = os.path.join(self.root, "out", "r.md")
        make_unit(self.root, "present", target, "body", b"tail")
        _, units = self._units()
        u = units["prun-task-present"]
        self.assertEqual((u["result_path_state"], u["result"]),
                         ("resolved", "present"))

    def test_resolved_empty(self):
        target = os.path.join(self.root, "out", "e.md")
        make_unit(self.root, "empty", target, "", b"tail")
        _, units = self._units()
        u = units["prun-task-empty"]
        self.assertEqual((u["result_path_state"], u["result"]),
                         ("resolved", "empty"))

    def test_resolved_missing(self):
        make_unit(self.root, "missing",
                  os.path.join(self.root, "out", "gone.md"), None, b"tail")
        _, units = self._units()
        u = units["prun-task-missing"]
        self.assertEqual((u["result_path_state"], u["result"]),
                         ("resolved", "missing"))

    def test_absent_entry(self):
        make_unit(self.root, "noentry", None, None, b"tail")
        _, units = self._units()
        u = units["prun-task-noentry"]
        self.assertEqual((u["result_path_state"], u["result"]),
                         ("absent-entry", "unknown"))

    def test_empty_entry_is_invalid(self):
        make_unit(self.root, "blank", "", None, b"tail")
        _, units = self._units()
        u = units["prun-task-blank"]
        self.assertEqual((u["result_path_state"], u["result"]),
                         ("invalid-entry", "unknown"))

    def test_relative_entry_escaping_its_unit_is_invalid(self):
        """The only traversal shape with no safe reading."""
        make_unit(self.root, "escape", os.path.join("..", "..", "etc", "passwd"),
                  None, b"tail")
        _, units = self._units()
        u = units["prun-task-escape"]
        self.assertEqual((u["result_path_state"], u["result"]),
                         ("invalid-entry", "unknown"))

    def test_an_absolute_entry_elsewhere_is_resolved(self):
        """Measured before implementing: all 217 real legacy entries are
        absolute and outside their unit, pointing into other sessions' scratch
        directories. Treating that as an anomaly would classify every real unit
        as unknown and report nothing."""
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        target = os.path.join(outside.name, "far.md")
        make_unit(self.root, "far", target, "body", b"tail")
        _, units = self._units()
        u = units["prun-task-far"]
        self.assertEqual((u["result_path_state"], u["result"]),
                         ("resolved", "present"))

    def test_no_illegal_pair_can_be_emitted(self):
        for name, entry, body in [
            ("a", os.path.join(self.root, "o", "a.md"), "x"),
            ("b", "", None),
            ("c", None, None),
            ("d", os.path.join("..", "x"), None),
        ]:
            make_unit(self.root, name, entry, body, b"t")
        _, units = self._units()
        for u in units.values():
            self.assertIn(u["result"],
                          self.mod._LEGAL_PAIRS[u["result_path_state"]],
                          f"illegal pair for {u['unit']}")


class SummaryTests(unittest.TestCase):
    """The two byte counters are disjoint and neither absorbs the other."""

    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name

    def _summary(self):
        _, out = run(self.mod, ["report-state", "--root", self.root, "--json",
                                "--summary"])
        return json.loads(out)["summary"]

    def test_a_unit_with_a_tail_and_no_entry_is_reported_as_unresolved(self):
        """Measured on the live corpus: 3 units and 0.40 MiB sat in this state
        while the first counter read 24.30 MiB. Reporting only the
        headline invites a reader to conclude there is nothing else to save."""
        make_unit(self.root, "noentry", None, None, b"x" * 700)
        summary = self._summary()
        self.assertEqual((summary["unresolved_units"], summary["unresolved_bytes"]),
                         (1, 700))
        self.assertEqual(summary["missing_or_empty_result_units"], 0,
                         "an unclassified unit must not be counted as a missing result")

    def test_the_counters_never_double_count(self):
        target = os.path.join(self.root, "out", "gone.md")
        make_unit(self.root, "missing", target, None, b"a" * 100)
        make_unit(self.root, "noentry", None, None, b"b" * 200)
        make_unit(self.root, "present", os.path.join(self.root, "out", "p.md"),
                  "body", b"c" * 400)
        summary = self._summary()
        self.assertEqual(summary["missing_or_empty_result_bytes"], 100)
        self.assertEqual(summary["unresolved_bytes"], 200)

    def test_an_empty_tail_counts_toward_neither(self):
        make_unit(self.root, "hollow", None, None, b"")
        summary = self._summary()
        self.assertEqual((summary["unresolved_units"], summary["missing_or_empty_result_units"]),
                         (0, 0))


class ObservationFailureTests(unittest.TestCase):
    """A failed look is never reported as a finding.

    Round 1 review, High 1: classify_result caught every OSError from getsize
    as `missing`, so a permission denial on a result file that existed with
    content was emitted as affirmative evidence that it was gone, with an empty
    errors list and exit 0, and it entered the recoverable counter. That is the
    single claim this command exists to avoid making.
    """

    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name

    def _report(self, extra=()):
        assert "--root" not in extra, (
            "_report already passes --root; a duplicate makes the sweep visit "
            "the same root twice and the seen-set dedup masks the branch")
        code, out = run(self.mod, ["report-state", "--root", self.root, "--json",
                                   "--summary", *extra])
        return code, json.loads(out)

    def test_a_denied_stat_on_a_live_target_is_not_reported_as_missing(self):
        target = os.path.join(self.root, "out", "present.md")
        make_unit(self.root, "denied", target, "THE RESULT IS RIGHT HERE", b"x" * 700)
        real = os.stat

        def denied(path, *args, **kwargs):
            # Pinned to os.stat because that is what classify_result calls. An
            # earlier version patched os.path.getsize; when the implementation
            # moved to os.stat for the regular-file check the mock stopped
            # intercepting and the test passed while proving nothing.
            if str(path) == target:
                raise PermissionError(13, "Access is denied")
            return real(path, *args, **kwargs)

        with unittest.mock.patch.object(os, "stat", side_effect=denied):
            code, payload = self._report()
        unit = payload["units"][0]
        self.assertEqual((unit["result_path_state"], unit["result"]),
                         ("resolved", "unknown"))
        self.assertEqual(unit["result_target"], target,
                         "the resolved path survives a failed observation")
        self.assertEqual([e["stage"] for e in unit["errors"]], ["result-target"])
        self.assertEqual(code, self.mod.EXIT_PARTIAL,
                         "a gap in the sweep must not exit 0")
        self.assertEqual(payload["summary"]["missing_or_empty_result_units"], 0,
                         "an unobserved target must never be counted as gone")

    def test_only_a_real_absence_is_reported_as_missing(self):
        make_unit(self.root, "gone", os.path.join(self.root, "out", "gone.md"),
                  None, b"x" * 700)
        code, payload = self._report()
        unit = payload["units"][0]
        self.assertEqual((unit["result_path_state"], unit["result"]),
                         ("resolved", "missing"))
        self.assertEqual(unit["errors"], [])
        self.assertEqual(code, self.mod.EXIT_OK)
        self.assertEqual(payload["summary"]["missing_or_empty_result_units"], 1)

    def test_a_denied_entry_read_is_unreadable_not_absent(self):
        """os.path.exists cannot separate "never written" from "cannot look",
        and it raced the open besides."""
        unit = make_unit(self.root, "entrydenied", None, None, b"x" * 10)
        (unit / "result-file").write_text("whatever", encoding="utf-8")
        real_open = os.open

        def denied(path, *a, **k):
            # Pinned to os.open, which is what _read_entry calls since the
            # metadata path gained its regular-file gate. A builtins.open patch
            # stopped intercepting and the test passed while proving nothing.
            if str(path).endswith("result-file"):
                raise PermissionError(13, "Access is denied")
            return real_open(path, *a, **k)

        with unittest.mock.patch.object(os, "open", side_effect=denied):
            code, payload = self._report()
        u = payload["units"][0]
        self.assertEqual((u["result_path_state"], u["result"]),
                         ("unreadable", "unknown"))
        self.assertEqual([e["stage"] for e in u["errors"]], ["result-entry"])
        self.assertEqual(code, self.mod.EXIT_PARTIAL)

    def test_a_denied_legacy_pid_read_is_recorded_not_swallowed(self):
        """Round 2 review, New 1: this caller flattened every problem to None
        with no error, so a denied read was indistinguishable from no entry and
        the sweep still exited 0 while one observation had failed."""
        unit = make_unit(self.root, "pid", None, None, b"x" * 100)
        (unit / "dispatch-pid").write_text("4242", encoding="utf-8")
        real_open = os.open

        def denied(path, *a, **k):
            if str(path).endswith("dispatch-pid"):
                raise PermissionError(13, "Access is denied")
            return real_open(path, *a, **k)

        with unittest.mock.patch.object(os, "open", side_effect=denied):
            code, payload = self._report(["--include-legacy-pid"])
        unit_record = payload["units"][0]
        self.assertIsNone(unit_record["legacy_pid_unverified"])
        self.assertEqual([e["stage"] for e in unit_record["errors"]], ["legacy-pid"])
        self.assertEqual(unit_record["errors"][0]["error"], "PermissionError")
        self.assertEqual(code, self.mod.EXIT_PARTIAL)

    def test_an_absent_legacy_pid_stays_silent(self):
        """Absence of an optional entry is not a failure and must not exit 1."""
        make_unit(self.root, "nopid", None, None, b"x" * 100)
        code, payload = self._report(["--include-legacy-pid"])
        self.assertIsNone(payload["units"][0]["legacy_pid_unverified"])
        self.assertEqual(payload["units"][0]["errors"], [])
        self.assertEqual(code, self.mod.EXIT_OK)

    def test_a_matching_entry_that_cannot_be_stated_is_reported(self):
        """Round 5 review: this branch existed but was unreachable.

        It guarded os.path.isdir with `except OSError`, and CPython's
        genericpath catches OSError inside isdir and returns False. The denied
        entry therefore vanished from the sweep with no error and exit 0, and
        the `# pragma: no cover - defensive` comment hid that it was dead."""
        make_unit(self.root, "readable", None, None, b"x")
        denied_unit = os.path.join(self.root, "prun-task-denied")
        os.makedirs(denied_unit)
        real = os.stat

        def denied(path, *args, **kwargs):
            if os.path.normcase(str(path)) == os.path.normcase(denied_unit):
                raise PermissionError(13, "Access is denied")
            return real(path, *args, **kwargs)

        # No extra --root here: _report already passes it, and a duplicate made
        # the sweep visit the same root twice. The `seen` set then skipped the
        # denied entry on the second pass and reached the readable unit anyway,
        # which masked a continue-to-break mutation entirely.
        with unittest.mock.patch.object(os, "stat", side_effect=denied):
            code, payload = self._report()
        self.assertEqual(payload["unit_count"], 1, "the readable unit still ran")
        self.assertEqual([e["stage"] for e in payload["discovery_errors"]],
                         ["unit-entry"])
        self.assertEqual(payload["discovery_errors"][0]["error"],
                         "PermissionError")
        self.assertEqual(code, self.mod.EXIT_PARTIAL)

    def test_a_non_regular_metadata_entry_is_not_read(self):
        """Round 5 review: `_read_entry` opened with built-in open and read
        unbounded, so a FIFO here blocked the whole sweep and a link to an
        endless device would read until memory ran out."""
        unit = make_unit(self.root, "dirent", None, None, b"x" * 10)
        os.makedirs(os.path.join(str(unit), "result-file"))
        code, payload = self._report()
        record = payload["units"][0]
        self.assertEqual((record["result_path_state"], record["result"]),
                         ("unreadable", "unknown"))
        self.assertEqual([e["error"] for e in record["errors"]],
                         ["NotARegularFile"])
        self.assertEqual(code, self.mod.EXIT_PARTIAL)

    def test_an_oversized_metadata_entry_is_reported_not_truncated(self):
        """Round 6 review: the cap stopped the read but said nothing about it,
        and the first version of this test asserted `problem is None`, which
        codified the defect. Silently returning a prefix is the same class of
        error as reporting a denied stat as `missing`."""
        unit = make_unit(self.root, "huge", None, None, b"x")
        (unit / "result-file").write_bytes(b"a" * (self.mod.MAX_ENTRY_BYTES * 2))
        raw, problem = self.mod._read_entry(str(unit), "result-file")
        self.assertIsNone(raw)
        self.assertEqual(problem, "EntryTooLarge")

    def test_an_entry_exactly_at_the_cap_is_still_valid(self):
        """The boundary must not move: the cap is inclusive."""
        unit = make_unit(self.root, "exact", None, None, b"x")
        target = os.path.join(self.root, "out", "at-cap.md")
        padded = target.encode() + b" " * (self.mod.MAX_ENTRY_BYTES - len(target))
        (unit / "result-file").write_bytes(padded)
        raw, problem = self.mod._read_entry(str(unit), "result-file")
        self.assertIsNone(problem)
        self.assertEqual(raw, target)

    def test_a_truncated_entry_cannot_masquerade_as_a_valid_path(self):
        """The concrete attack shape: a real path padded to the cap with an
        ignored suffix. The truncated prefix stripped down to that path and was
        emitted as resolved/present with no error and exit 0."""
        target = os.path.join(self.root, "innocent.md")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as handle:
            handle.write("a real result")
        unit = make_unit(self.root, "masq", None, None, b"x" * 10)
        payload = (target.encode()
                   + b" " * (self.mod.MAX_ENTRY_BYTES - len(target))
                   + b"AND-THEN-SOMETHING-ELSE.md")
        (unit / "result-file").write_bytes(payload)
        code, payload_json = self._report()
        record = next(u for u in payload_json["units"]
                      if u["unit"].endswith("masq"))
        self.assertEqual((record["result_path_state"], record["result"]),
                         ("unreadable", "unknown"))
        self.assertEqual([e["error"] for e in record["errors"]],
                         ["EntryTooLarge"])
        self.assertEqual(code, self.mod.EXIT_PARTIAL)

    def test_an_oversized_legacy_pid_is_recorded_under_its_own_stage(self):
        unit = make_unit(self.root, "bigpid", None, None, b"x")
        (unit / "dispatch-pid").write_bytes(b"9" * (self.mod.MAX_ENTRY_BYTES + 10))
        code, payload = self._report(["--include-legacy-pid"])
        record = payload["units"][0]
        self.assertIsNone(record["legacy_pid_unverified"])
        self.assertEqual([(e["stage"], e["error"]) for e in record["errors"]],
                         [("legacy-pid", "EntryTooLarge")])
        self.assertEqual(code, self.mod.EXIT_PARTIAL)

    def test_every_documented_field_survives_the_defensive_path(self):
        """The early return there omitted result_target, so the one record a
        reader most needs to inspect was the one missing a key."""
        make_unit(self.root, "boom", None, None, b"t")
        with unittest.mock.patch.object(self.mod, "classify_result",
                                        side_effect=OSError("injected")):
            code, payload = self._report()
        unit = payload["units"][0]
        for key in ("unit", "errors", "result_path_state", "result",
                    "result_target", "tail_bytes"):
            self.assertIn(key, unit, key)
        self.assertEqual(unit["tail_bytes"], 1,
                         "the sweep continues past a classification failure")
        self.assertEqual(code, self.mod.EXIT_PARTIAL)


class RootNormalizationTests(unittest.TestCase):
    """Round 1 review, Medium 4: a relative --root reached classify_result,
    which compared a relative unit path against abspath(unit), so a valid
    in-unit relative result entry was misread as invalid-entry."""

    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_a_relative_root_classifies_an_in_unit_entry_correctly(self):
        root = pathlib.Path(self.tmp.name) / "corpus"
        unit = root / "prun-task-rel"
        unit.mkdir(parents=True)
        (unit / "tail").write_bytes(b"x" * 40)
        (unit / "result.txt").write_text("body", encoding="utf-8")
        (unit / "result-file").write_text("result.txt", encoding="utf-8")
        previous = os.getcwd()
        os.chdir(self.tmp.name)
        try:
            code, out = run(self.mod, ["report-state", "--root", "corpus",
                                       "--json"])
        finally:
            os.chdir(previous)
        payload = json.loads(out)
        record = payload["units"][0]
        self.assertEqual((record["result_path_state"], record["result"]),
                         ("resolved", "present"))
        self.assertEqual(code, self.mod.EXIT_OK)
        self.assertTrue(os.path.isabs(payload["roots"][0]),
                        "roots is documented as absolute")
        self.assertTrue(os.path.isabs(record["unit"]),
                        "unit is documented as absolute")


class DiscoveryFailureTests(unittest.TestCase):
    """Round 3 review, New 1: an unreadable corpus read as an empty one.

    iter_units swallowed every OSError from listdir, and `partial` was computed
    only from records that survived discovery. A denied root, and a mistyped
    one, both returned zero units and exit 0. For a command whose whole purpose
    is finding stranded output, that is the most expensive silence available.
    """

    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name

    def _report(self, argv):
        code, out = run(self.mod, ["report-state", "--json", *argv])
        return code, json.loads(out)

    def test_a_root_that_cannot_be_listed_is_reported(self):
        make_unit(self.root, "real", None, None, b"x" * 9000)
        with unittest.mock.patch.object(
                os, "listdir", side_effect=PermissionError(13, "denied")):
            code, payload = self._report(["--root", self.root])
        self.assertEqual(code, self.mod.EXIT_PARTIAL)
        self.assertEqual([e["error"] for e in payload["discovery_errors"]],
                         ["PermissionError"])
        self.assertEqual(payload["discovery_errors"][0]["stage"], "root")

    def test_a_missing_root_is_not_an_empty_corpus(self):
        missing = os.path.join(self.root, "nope", "still-nope")
        code, payload = self._report(["--root", missing])
        self.assertEqual(code, self.mod.EXIT_PARTIAL,
                         "a typo must not read as nothing to recover")
        self.assertEqual(payload["unit_count"], 0)
        self.assertEqual([e["error"] for e in payload["discovery_errors"]],
                         ["FileNotFoundError"])

    def test_a_readable_root_beside_an_unreadable_one_is_still_inspected(self):
        good = os.path.join(self.root, "good")
        os.makedirs(good)
        make_unit(good, "fine", None, None, b"x" * 10)
        bad = os.path.join(self.root, "gone")
        # The unreadable root goes FIRST. With the readable one first, changing
        # `continue` to `break` in iter_units still satisfied every assertion,
        # so the fixture did not prove that the sweep continues.
        code, payload = self._report(["--root", bad, "--root", good])
        self.assertEqual(payload["unit_count"], 1, "the readable root still ran")
        self.assertEqual(len(payload["discovery_errors"]), 1)
        self.assertEqual(code, self.mod.EXIT_PARTIAL)

    def test_a_clean_sweep_reports_no_discovery_errors(self):
        make_unit(self.root, "ok", None, None, b"x")
        code, payload = self._report(["--root", self.root])
        self.assertEqual(payload["discovery_errors"], [])
        self.assertEqual(code, self.mod.EXIT_OK)


class NonRegularFileTests(unittest.TestCase):
    """Round 3 review, New 2: `present` and `empty` are defined over a file and
    its bytes, but os.path.getsize answers for a directory too. A directory
    named as the result target was emitted as resolved/empty on Windows, and
    could read as resolved/present elsewhere."""

    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name

    def test_a_directory_target_is_unknown_not_empty(self):
        target = os.path.join(self.root, "a-directory")
        os.makedirs(target)
        make_unit(self.root, "dirtarget", target, None, b"x" * 50)
        code, out = run(self.mod, ["report-state", "--root", self.root,
                                   "--json", "--summary"])
        payload = json.loads(out)
        record = next(u for u in payload["units"]
                      if u["unit"].endswith("dirtarget"))
        self.assertEqual((record["result_path_state"], record["result"]),
                         ("resolved", "unknown"))
        self.assertIn("NotARegularFile",
                      [e["error"] for e in record["errors"]])
        self.assertEqual(code, self.mod.EXIT_PARTIAL)
        self.assertEqual(payload["summary"]["missing_or_empty_result_units"], 0,
                         "a malformed unit must not enter the summary as clean")

    def test_a_directory_tail_is_null_not_zero(self):
        unit = make_unit(self.root, "dirtail", None, None, None)
        os.makedirs(os.path.join(str(unit), "tail"))
        code, out = run(self.mod, ["report-state", "--root", self.root, "--json"])
        record = json.loads(out)["units"][0]
        self.assertIsNone(record["tail_bytes"],
                          "a directory has an st_size; it is not a tail size")
        self.assertIn("tail", [e["stage"] for e in record["errors"]])
        self.assertEqual(code, self.mod.EXIT_PARTIAL)


class ReadOnlyTests(unittest.TestCase):
    def test_report_writes_nothing(self):
        mod = load()
        with tempfile.TemporaryDirectory() as tmp:
            make_unit(tmp, "one", os.path.join(tmp, "o", "r.md"), "x", b"tail")
            make_unit(tmp, "two", None, None, b"")
            before = tree_hash(tmp)
            run(mod, ["report-state", "--root", tmp, "--json"])
            run(mod, ["report-state", "--root", tmp, "--summary"])
            self.assertEqual(tree_hash(tmp), before,
                             "report-state must not modify anything")


class OutputContractTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name

    def test_legacy_pid_is_absent_by_default(self):
        """Round 3: labelling a PID advisory does not stop a reader treating it
        as a liveness hint, which is the inference this slice disclaims."""
        unit = make_unit(self.root, "pid", None, None, b"tail")
        (unit / "dispatch-pid").write_text("4242", encoding="utf-8")
        _, out = run(self.mod, ["report-state", "--root", self.root, "--json"])
        self.assertNotIn("legacy_pid_unverified", out)
        self.assertNotIn("4242", out)

        _, out = run(self.mod, ["report-state", "--root", self.root, "--json",
                                "--include-legacy-pid"])
        payload = json.loads(out)["units"][0]
        self.assertEqual(payload["legacy_pid_unverified"], "4242")

    def test_min_tail_bytes_filters_display_only(self):
        make_unit(self.root, "small", None, None, b"x" * 10)
        make_unit(self.root, "big", None, None, b"x" * 5000)
        _, out = run(self.mod, ["report-state", "--root", self.root, "--json",
                                "--min-tail-bytes", "1000"])
        payload = json.loads(out)
        self.assertEqual(len(payload["units"]), 1)
        # Naming the survivor is the point. Asserting only the count let a
        # mutant that inverted the comparison keep the 10-byte unit and pass.
        self.assertTrue(payload["units"][0]["unit"].endswith("prun-task-big"))
        self.assertEqual(payload["units"][0]["tail_bytes"], 5000)
        self.assertEqual(payload["unit_count"], 2,
                         "the filter is display-only; both units were inspected")

    def test_ordering_is_stable_by_default(self):
        for name in ("c", "a", "b"):
            make_unit(self.root, name, None, None, b"x")
        runs = [json.loads(run(self.mod, ["report-state", "--root", self.root,
                                          "--json"])[1])["units"]
                for _ in range(2)]
        self.assertEqual([u["unit"] for u in runs[0]],
                         [u["unit"] for u in runs[1]])

    def test_tail_bytes_desc_sort(self):
        """Names chosen so path order and size order disagree.

        With `big` and `small`, path order already put the large unit first, so
        disabling the tail-bytes-desc branch produced the same list and passed.
        """
        make_unit(self.root, "a-small", None, None, b"x" * 10)
        make_unit(self.root, "z-big", None, None, b"x" * 5000)
        _, out = run(self.mod, ["report-state", "--root", self.root, "--json",
                                "--sort", "tail-bytes-desc"])
        units = json.loads(out)["units"]
        self.assertEqual([os.path.basename(u["unit"]) for u in units],
                         ["prun-task-z-big", "prun-task-a-small"])
        self.assertEqual([u["tail_bytes"] for u in units], [5000, 10])

    def test_json_is_complete_even_when_a_unit_fails(self):
        make_unit(self.root, "ok", None, None, b"tail")
        bad = make_unit(self.root, "bad", None, None, b"tail")
        original = self.mod.classify_result

        def boom(unit):
            if os.path.basename(unit) == os.path.basename(str(bad)):
                raise OSError("injected")
            return original(unit)

        self.mod.classify_result = boom
        code, out = run(self.mod, ["report-state", "--root", self.root, "--json"])
        payload = json.loads(out)  # must still parse
        self.assertEqual(code, self.mod.EXIT_PARTIAL)
        self.assertEqual(len(payload["units"]), 2)
        errored = [u for u in payload["units"] if u["errors"]]
        self.assertEqual(len(errored), 1)

    def test_the_safety_sentence_is_always_present(self):
        make_unit(self.root, "x", None, None, b"t")
        _, out = run(self.mod, ["report-state", "--root", self.root, "--json"])
        self.assertIn("only safe operation", json.loads(out)["safety"])
        _, text = run(self.mod, ["report-state", "--root", self.root])
        self.assertIn("only safe operation", text)


if __name__ == "__main__":
    unittest.main()
