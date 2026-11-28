"""Private mac-storage-audit growth watch: flags, discovery, and capture rotation."""
import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

if os.name == "nt":
    # The collector stamps captures with ZoneInfo("America/Los_Angeles"), which
    # needs the tzdata package on Windows, and the audit runs only on a Mac.
    raise unittest.SkipTest("the Mac storage audit does not run on Windows")

SCRIPT = Path(__file__).resolve().parents[1] / "reference-skills" / "mac-storage-audit" / "scripts" / "growth_watch.py"
spec = importlib.util.spec_from_file_location("growth_watch", SCRIPT)
gw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gw)

KIB_PER_GB = 1e9 / 1024


def row(path, gb, kind="home", status="ok", store=None):
    r = {"path": path, "kind": kind, "status": status, "kib": int(gb * KIB_PER_GB), "error_count": 0}
    if store:
        r["store"] = store
    return r


def capture(when, rows=(), stores=(), caches=(), entries=None, complete=True):
    return {"schema_version": 1, "observed_at": when, "method": gw.METHOD,
            "home": "/h", "home_entries": sorted(entries if entries is not None else
                                                  [Path(r["path"]).name for r in rows if r["kind"] == "home"]),
            "home_listing_complete": complete,
            "rows": list(rows), "stores": list(stores), "pack_caches": list(caches)}


T0 = "2026-11-21T11:00:00-08:00"
T1 = "2026-11-28T11:00:00-08:00"


class EvaluateTest(unittest.TestCase):
    def kinds(self, flags):
        return sorted((f["kind"], f["path"]) for f in flags)

    def test_first_capture_applies_budgets_without_growth(self):
        cur = capture(T1, rows=[row("/h/a", 50)],
                      stores=[row("/h/.cache/x/agy", 31, kind="store", store="agy-dispatch")])
        flags, notes = gw.evaluate(cur, None)
        self.assertEqual(self.kinds(flags), [("budget", "/h/.cache/x/agy")])
        self.assertTrue(any("no previous capture" in n for n in notes))
        self.assertFalse(any("home listing failed" in n for n in notes))
        unlisted = capture(T1, stores=[row("/h/.codex/sessions", 1, kind="store", store="codex-sessions")],
                           complete=False)
        self.assertTrue(any("home listing failed" in n for n in gw.evaluate(unlisted, None)[1]))

    def test_growth_over_threshold_is_flagged_including_owned_stores(self):
        prev = capture(T0, rows=[row("/h/a", 10)],
                       stores=[row("/h/.grok/sessions", 1, kind="store", store="grok-sessions")])
        cur = capture(T1, rows=[row("/h/a", 12)],
                      stores=[row("/h/.grok/sessions", 7.5, kind="store", store="grok-sessions")])
        flags, _ = gw.evaluate(cur, prev)
        self.assertEqual(self.kinds(flags), [("growth", "/h/.grok/sessions")])

    def test_a_partial_scan_gives_no_growth_inference(self):
        prev = capture(T0, rows=[row("/h/Library", 100)])
        cur = capture(T1, rows=[row("/h/Library", 130, status="partial_or_failed")])
        flags, notes = gw.evaluate(cur, prev)
        self.assertEqual(flags, [])
        self.assertTrue(any("partial" in n for n in notes))

    def test_growth_shows_once_at_the_most_specific_path(self):
        lib, caches = str(Path("/h/Library")), str(Path("/h/Library/Caches"))
        prev = capture(T0, rows=[row(lib, 100, status="partial_or_failed"),
                                 row(caches, 10, kind="child")])
        cur = capture(T1, rows=[row(lib, 120, status="partial_or_failed"),
                                row(caches, 20, kind="child")])
        flags, _ = gw.evaluate(cur, prev)
        self.assertEqual(self.kinds(flags), [("growth", caches)])
        parent, child = str(Path("/h/P")), str(Path("/h/P/x"))
        prev2 = capture(T0, rows=[row(parent, 100), row(child, 10, kind="child")])
        cur2 = capture(T1, rows=[row(parent, 120), row(child, 20, kind="child")])
        self.assertEqual(self.kinds(gw.evaluate(cur2, prev2)[0]), [("growth", child)])

    def test_new_root_needs_a_complete_earlier_listing(self):
        prev = capture(T0, rows=[row("/h/a", 1)])
        cur = capture(T1, rows=[row("/h/a", 1), row("/h/big", 6)])
        self.assertEqual(self.kinds(gw.evaluate(cur, prev)[0]), [("new-root", "/h/big")])
        prev_incomplete = capture(T0, rows=[row("/h/a", 1)], complete=False)
        flags, notes = gw.evaluate(cur, prev_incomplete)
        self.assertEqual(flags, [])
        self.assertTrue(any("incomplete" in n for n in notes))

    def test_a_root_that_was_listed_but_unreadable_is_not_new(self):
        prev = capture(T0, rows=[row("/h/a", 1)], entries=["a", "big"])
        cur = capture(T1, rows=[row("/h/a", 1), row("/h/big", 6)])
        self.assertEqual(gw.evaluate(cur, prev)[0], [])

    def test_small_caches_can_exceed_the_total_budget(self):
        caches = [row(f"/h/P/r{i}/.agent-config/cache", 0.2, kind="pack-cache") for i in range(11)]
        flags, _ = gw.evaluate(capture(T1, caches=caches), None)
        self.assertEqual(self.kinds(flags), [("budget", "all pack caches")])

    def test_a_path_measured_twice_is_compared_once_under_its_store_name(self):
        pip = "/h/Library/Caches/pip"
        prev = capture(T0, rows=[row("/h/Library", 50, status="partial_or_failed"),
                                 row(pip, 1, kind="child")],
                       stores=[row(pip, 1, kind="store", store="pip-cache")])
        cur = capture(T1, rows=[row("/h/Library", 60, status="partial_or_failed"),
                                row(pip, 7, kind="child")],
                      stores=[row(pip, 7, kind="store", store="pip-cache")])
        flags, _ = gw.evaluate(cur, prev)
        self.assertEqual(len(flags), 1)
        self.assertEqual((flags[0]["kind"], flags[0]["path"], flags[0]["store"]),
                         ("growth", pip, "pip-cache"))

    def test_incomplete_cache_discovery_is_reported(self):
        cur = capture(T1, caches=[row("/h/P/r/.agent-config/cache", 0.1, kind="pack-cache")])
        cur["pack_cache_discovery_errors"] = ["/h/P: Permission denied"]
        flags, notes = gw.evaluate(cur, None)
        self.assertEqual(flags, [])
        self.assertTrue(any("discovery incomplete" in n for n in notes))
        self.assertTrue(any("covers only" in n for n in notes))

    def test_budgets_compare_exact_bytes(self):
        dispatch_limit = 29296875  # 30 GB in KiB, an exact boundary
        cache_limit = 244140  # the last KiB count within 0.25 GB
        for kind, store, limit in (("store", "agy-dispatch", dispatch_limit),
                                   ("pack-cache", None, cache_limit)):
            for kib, flagged in ((limit, False), (limit + 1, True)):
                r = row("/h/x", 0, kind=kind, store=store)
                r["kib"] = kib
                cur = capture(T1, stores=[r]) if store else capture(T1, caches=[r])
                self.assertEqual(bool(gw.evaluate(cur, None)[0]), flagged, (kind, kib))

    def test_one_cache_over_its_budget_is_flagged(self):
        caches = [row("/h/P/r/.agent-config/cache", 0.3, kind="pack-cache")]
        self.assertEqual(self.kinds(gw.evaluate(capture(T1, caches=caches), None)[0]),
                         [("budget", "/h/P/r/.agent-config/cache")])


class DiscoveryAndSaveTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name).resolve()

    def tearDown(self):
        self._tmp.cleanup()

    def test_pack_caches_skip_symlinked_repos_and_count_each_root_once(self):
        projects = self.base / "P"
        for name in ("a", ".retired-repositories/b"):
            (projects / name / ".agent-config" / "cache").mkdir(parents=True)
        try:
            os.symlink(projects / "a", projects / "alias", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("this filesystem or account cannot create a directory symlink")
        caches, errors = gw.pack_caches(projects)
        self.assertEqual(errors, [])
        found = [p.relative_to(projects).as_posix() for p in caches]
        self.assertEqual(sorted(found), [".retired-repositories/b/.agent-config/cache",
                                         "a/.agent-config/cache"])

    def test_a_partial_folder_is_split_until_readable_children_scan(self):
        lib = self.base / "Library"
        for rel in ("Caches/pip/http", "Caches/Protected/x", "Mail/x", "Fonts"):
            (lib / rel).mkdir(parents=True)
        partial = {str(lib), str(lib / "Caches"), str(lib / "Mail"), str(lib / "Caches" / "Protected")}

        def fake_measure(path, timeout):
            status = "partial_or_failed" if str(path) in partial else "ok"
            return {"path": str(path), "status": status, "kib": 1, "error_count": 0}

        rows = []
        original = gw.measure
        gw.measure = fake_measure
        try:
            gw.measure_tree(lib, "home", 2, 1, rows)
        finally:
            gw.measure = original
        measured = {Path(r["path"]).relative_to(self.base).as_posix(): r["status"] for r in rows}
        self.assertEqual(measured["Library/Caches/pip"], "ok")
        self.assertEqual(measured["Library/Fonts"], "ok")
        self.assertIn("Library/Caches/Protected", measured)
        self.assertNotIn("Library/Caches/Protected/x", measured)
        self.assertNotIn("Library/Caches/pip/http", measured)

    @unittest.skipIf(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                     "POSIX permissions as a normal user")
    def test_a_denied_project_base_is_reported_and_a_missing_retired_folder_is_not(self):
        projects = self.base / "P"
        (projects / "a" / ".agent-config" / "cache").mkdir(parents=True)
        caches, errors = gw.pack_caches(projects)
        self.assertEqual((len(caches), errors), (1, []))
        os.chmod(projects, 0o000)
        try:
            caches, errors = gw.pack_caches(projects)
        finally:
            os.chmod(projects, 0o700)
        self.assertEqual(caches, [])
        self.assertTrue(errors)
        self.assertIn(str(projects), errors[0])

    def test_the_capture_subtree_is_never_measured_on_its_own(self):
        local = self.base / ".local"
        state = local / "state" / "mac-storage-audit"
        state.mkdir(parents=True)
        (local / "share").mkdir()

        def fake_measure(path, timeout):
            status = "ok" if path not in (local, local / "state") else "partial_or_failed"
            return {"path": str(path), "status": status, "kib": 1, "error_count": 0}

        rows = []
        original = gw.measure
        gw.measure = fake_measure
        try:
            gw.measure_tree(local, "home", 3, 1, rows, skip=state)
        finally:
            gw.measure = original
        measured = {Path(r["path"]).relative_to(self.base).as_posix() for r in rows}
        self.assertIn(".local/share", measured)
        self.assertIn(".local/state", measured)
        self.assertNotIn(".local/state/mac-storage-audit", measured)

    def test_a_failed_publish_keeps_the_earlier_captures(self):
        state = self.base / "state"
        for day in (1, 2):
            gw.save(state, capture(f"2026-11-0{day}T11:00:00-08:00"), keep=2)
        before = {p.name: p.read_bytes() for p in state.iterdir()}
        original = gw.os.replace

        def fail(*_args, **_kwargs):
            raise OSError("disk full")

        gw.os.replace = fail
        try:
            with self.assertRaises(OSError):
                gw.save(state, capture("2026-11-03T11:00:00-08:00"), keep=2)
        finally:
            gw.os.replace = original
        after = {p.name: p.read_bytes() for p in state.iterdir()}
        self.assertEqual(after, before)

    def _fake_measure(self, sizes):
        def fake(path, timeout):
            kib = sizes.get(Path(path).relative_to(self.base).as_posix(), 1)
            return {"path": str(path), "status": "ok", "kib": kib, "error_count": 0}
        return fake

    def test_collect_subtracts_the_capture_bytes_from_their_ancestor(self):
        home = self.base
        state = home / ".local" / "state" / "mac-storage-audit"
        state.mkdir(parents=True)
        original = gw.measure
        gw.measure = self._fake_measure({".local": 100, ".local/state/mac-storage-audit": 30})
        try:
            cur = gw.collect(home, home / "P", state, 1)
        finally:
            gw.measure = original
        local = next(r for r in cur["rows"] if r["path"] == str(home / ".local"))
        self.assertEqual((local["kib"], local["excluded_capture_kib"]), (70, 30))
        self.assertEqual(cur["pack_cache_discovery_errors"], [f"{home / 'P'}: not found"])

    def _run_main(self, state):
        """Run the entry point read-only against the fixture home; return stdout."""
        argv, original = sys.argv, gw.measure
        sys.argv = ["growth_watch.py", "--state-dir", str(state), "--projects", str(self.base / "P")]
        gw.measure = self._fake_measure({})
        out = io.StringIO()
        try:
            with mock.patch.object(gw.Path, "home", return_value=self.base), \
                    contextlib.redirect_stdout(out):
                self.assertEqual(gw.main(), 0)
        finally:
            sys.argv, gw.measure = argv, original
        return out.getvalue()

    def test_main_without_save_writes_nothing(self):
        state = self.base / "state"
        out = self._run_main(state)
        self.assertFalse(state.exists())
        self.assertNotIn("saved", json.loads(out))

    def test_a_malformed_previous_capture_is_noted_not_fatal(self):
        bad = self.base / "capture-20261121T110000.json"
        bad_row = capture(T0, rows=[row("/h/a", 1)])
        bad_row["rows"][0]["kib"] = "12"
        naive = capture("2026-11-21T11:00:00")
        rows_object = dict(capture(T0), rows={})
        entries_string = dict(capture(T0), home_entries="abc")
        payloads = ("[]", "{}", "{not json", json.dumps({"observed_at": "x", "rows": []}),
                    json.dumps(bad_row), json.dumps(naive), json.dumps(rows_object),
                    json.dumps(entries_string))
        for payload in payloads:
            bad.write_text(payload)
            prev, note = gw.load_previous(bad)
            self.assertIsNone(prev)
            self.assertIn("unreadable", note)
        good = capture(T0)
        bad.write_text(json.dumps(good))
        self.assertEqual(gw.load_previous(bad), (good, None))

    def test_a_malformed_baseline_still_yields_a_report(self):
        for payload in (capture("2026-11-21T11:00:00"), dict(capture(T0), rows={})):
            with self.subTest(payload=payload):
                self._main_with_baseline(payload)

    def _main_with_baseline(self, payload):
        state = self.base / "state"
        state.mkdir(exist_ok=True)
        (state / "capture-20261121T110000.json").write_text(json.dumps(payload))
        out = self._run_main(state)
        report = json.loads(out)
        self.assertIn("unreadable", report["notes"][0])
        self.assertFalse(any(n.startswith("no previous capture") for n in report["notes"]))

    @unittest.skipIf(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                     "POSIX permissions as a normal user")
    def test_a_denied_consumer_does_not_hide_its_readable_siblings(self):
        projects = self.base / "P"
        for name in ("a", "b"):
            (projects / name / ".agent-config" / "cache").mkdir(parents=True)
        os.chmod(projects / "b", 0o000)
        try:
            caches, errors = gw.pack_caches(projects)
        finally:
            os.chmod(projects / "b", 0o700)
        self.assertEqual([p.relative_to(projects).as_posix() for p in caches], ["a/.agent-config/cache"])
        self.assertEqual(len(errors), 1)
        self.assertIn(str(projects / "b"), errors[0])

    @unittest.skipIf(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                     "POSIX permissions as a normal user")
    def test_a_denied_store_does_not_hide_its_readable_siblings(self):
        home = self.base
        (home / ".gemini" / "antigravity-cli").mkdir(parents=True)
        (home / ".codex" / "sessions").mkdir(parents=True)
        os.chmod(home / ".gemini", 0o000)
        original = gw.measure
        gw.measure = self._fake_measure({".codex/sessions": 40})
        try:
            cur = gw.collect(home, home / "P", home / "state", 1)
            flags, notes = gw.evaluate(cur, None)
        finally:
            gw.measure = original
            os.chmod(home / ".gemini", 0o700)
        stores = {r["store"]: r for r in cur["stores"]}
        self.assertEqual((stores["agy-shared"]["status"], stores["agy-shared"]["kib"]), ("failed", None))
        self.assertEqual((stores["codex-sessions"]["status"], stores["codex-sessions"]["kib"]), ("ok", 40))
        self.assertIn(str(home / ".gemini" / "antigravity-cli"), gw.partial_paths(cur))
        self.assertTrue(any("partial or failed" in n for n in notes))

    @unittest.skipIf(os.name == "nt" or (hasattr(os, "geteuid") and os.geteuid() == 0),
                     "POSIX permissions as a normal user")
    def test_an_unlistable_history_is_reported_not_taken_as_empty(self):
        state = self.base / "state"
        state.mkdir()
        (state / "capture-20261121T110000.json").write_text(json.dumps(capture(T0)))
        os.chmod(state, 0o311)
        try:
            report = json.loads(self._run_main(state))
            saved, note = gw.save(state, capture(T1), keep=2)
        finally:
            os.chmod(state, 0o700)
        self.assertIn("cannot be listed", report["notes"][0])
        self.assertFalse(any(n.startswith("no previous capture") for n in report["notes"]))
        self.assertTrue(saved.exists())
        self.assertIn("not pruned", note)
        self.assertEqual(gw.captures(self.base / "absent"), [])

    def test_save_publishes_atomically_and_keeps_the_newest(self):
        state = self.base / "state"
        for day in range(1, 5):
            gw.save(state, capture(f"2026-11-0{day}T11:00:00-08:00"), keep=2)
        names = sorted(p.name for p in state.iterdir())
        self.assertEqual(names, ["capture-20261103T110000.json", "capture-20261104T110000.json"])
        self.assertEqual(json.loads((state / names[-1]).read_text())["observed_at"],
                         "2026-11-04T11:00:00-08:00")


if __name__ == "__main__":
    unittest.main()
