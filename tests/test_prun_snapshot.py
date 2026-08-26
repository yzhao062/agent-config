"""Snapshot contract for skills/prun/scripts/prun_state.py.

Three properties carry this command, and each was established by a plan-review
round rather than by choice:

- The read is bounded and best-effort. `bytes_copied == n` does NOT prove the
  source was unchanged, because bytes can come from different generations and
  still total n, so nothing is inferred from equality.
- Publication is atomic AND never replaces. Those are not one portable
  operation: os.replace replaces, os.rename differs by platform, and checking
  first races. Only os.link gives both, with the kernel deciding refusal.
- Only FileExistsError is a collision. Every other link failure is an
  unsupported or failed publication and never falls back.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import stat
import sys
import tempfile
import threading
import unittest
import unittest.mock
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _quiet_spawn  # noqa: E402,F401

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "skills" / "prun" / "scripts" / "prun_state.py"


def load():
    spec = importlib.util.spec_from_file_location("_prun_snap", MODULE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_unit(root, name, tail=b""):
    unit = Path(root) / f"prun-task-{name}"
    unit.mkdir(parents=True)
    (unit / "tail").write_bytes(tail)
    return unit


def run(mod, argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = mod.main(argv)
    return code, buf.getvalue()


class LauncherContractTests(unittest.TestCase):
    """Both launcher families must agree on the exit code.

    Round 2 review, New 2: the PowerShell launchers called Write-Error under
    $ErrorActionPreference = 'Stop', so an unusable explicit interpreter raised
    a terminating error and the script exited 1 without ever reaching its own
    exit 2. The bash launchers returned 2 for the same input. A caller
    branching on the documented code got a different answer per platform.
    """

    SCRIPTS = ROOT / "skills" / "prun" / "scripts"

    def _run(self, launcher, args, interpreter):
        env = dict(os.environ, PRUN_PYTHON=interpreter)
        if launcher.endswith(".ps1"):
            shell = shutil.which("pwsh") or shutil.which("powershell")
            if not shell:
                self.skipTest("no PowerShell available")
            cmd = [shell, "-NoProfile", "-File", str(self.SCRIPTS / launcher)]
        else:
            shell = shutil.which("bash")
            if not shell:
                self.skipTest("no bash available")
            cmd = [shell, str(self.SCRIPTS / launcher)]
        return subprocess.run(cmd + args, capture_output=True, text=True, env=env)

    def test_an_unusable_explicit_interpreter_exits_2_on_every_launcher(self):
        bogus = os.path.join(os.sep, "definitely", "not", "python")
        with tempfile.TemporaryDirectory() as tmp:
            for launcher, args in (
                ("report-state.sh", ["--root", tmp]),
                ("report-state.ps1", ["--root", tmp]),
                ("snapshot-tail.sh", ["--unit", tmp]),
                ("snapshot-tail.ps1", ["--unit", tmp]),
            ):
                if not (self.SCRIPTS / launcher).is_file():
                    continue
                with self.subTest(launcher=launcher):
                    proc = self._run(launcher, args, bogus)
                    self.assertEqual(
                        proc.returncode, 2,
                        f"{launcher} returned {proc.returncode}; "
                        f"stderr={proc.stderr!r}")
                    self.assertIn("not usable", proc.stderr)

class ByteContractTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = os.path.join(self.tmp.name, "dest")

    def _members(self, path):
        with zipfile.ZipFile(path) as zf:
            return json.loads(zf.read("manifest.json")), zf.read("tail.bin")

    def test_exact_bytes_are_preserved(self):
        payload = bytes(range(256)) * 40  # includes \r\n and NUL
        unit = make_unit(self.tmp.name, "bin", payload)
        code, out = run(self.mod, ["snapshot-tail", "--unit", str(unit),
                                   "--dest", self.dest, "--json"])
        self.assertEqual(code, 0)
        manifest, blob = self._members(json.loads(out)["published"])
        self.assertEqual(blob, payload, "no decoding, no newline conversion")
        self.assertEqual(manifest["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(manifest["capture_outcome"], "complete_bounded_read")

    def test_a_source_growing_during_the_copy_yields_exactly_n(self):
        """The bound is taken from fstat on the open handle, so later appends
        cannot enlarge the capture."""
        unit = make_unit(self.tmp.name, "grow", b"a" * 1000)
        source = unit / "tail"
        real_fstat = os.fstat

        def fstat_then_grow(fd):
            # The growth must land AFTER n is taken, or the test proves
            # nothing. An earlier version appended before fstat ran and saw
            # 6000, which is the mock testing itself rather than the bound.
            st = real_fstat(fd)
            with open(source, "ab") as appender:
                appender.write(b"b" * 5000)
            return st

        with unittest.mock.patch.object(os, "fstat", side_effect=fstat_then_grow):
            data, n = self.mod.bounded_read(str(source))
        self.assertEqual(n, 1000)
        self.assertEqual(len(data), 1000)
        self.assertEqual(data, b"a" * 1000)

    def test_a_short_read_is_recorded_as_short_read(self):
        unit = make_unit(self.tmp.name, "short", b"a" * 100)
        with unittest.mock.patch.object(self.mod, "bounded_read",
                                        return_value=(b"a" * 40, 100)):
            code, out = run(self.mod, ["snapshot-tail", "--unit", str(unit),
                                       "--dest", self.dest, "--json"])
        self.assertEqual(code, 0)
        manifest = json.loads(out)["manifest"]
        self.assertEqual(manifest["capture_outcome"], "short_read")
        self.assertEqual((manifest["bytes_copied"], manifest["source_size_at_open"]),
                         (40, 100))

    def test_equality_is_not_claimed_as_consistency(self):
        """The manifest must not assert the source was unchanged. Round 3
        corrected a plan that stated this as fact."""
        unit = make_unit(self.tmp.name, "note", b"x" * 10)
        _, out = run(self.mod, ["snapshot-tail", "--unit", str(unit),
                                "--dest", self.dest, "--json"])
        manifest = json.loads(out)["manifest"]
        self.assertTrue(manifest["source_may_be_live"])
        self.assertIn("do not prove", manifest["note"])

    def test_an_unopenable_source_publishes_nothing(self):
        unit = make_unit(self.tmp.name, "gone", b"x")
        os.remove(unit / "tail")
        code, _ = run(self.mod, ["snapshot-tail", "--unit", str(unit),
                                 "--dest", self.dest])
        self.assertEqual(code, self.mod.EXIT_SOURCE)
        self.assertEqual(os.listdir(self.dest) if os.path.isdir(self.dest) else [],
                         [])


class RegularSourceTests(unittest.TestCase):
    """Round 4 review: the snapshot read path had no type check at all.

    The reporter gained S_ISREG in Round 3 and this path did not, so a device
    such as /dev/null reported st_size 0 and published an empty archive as a
    `complete_bounded_read` with exit 0, and a FIFO with no writer blocked the
    open forever. A snapshot command that hangs is worse than one that refuses.

    The mode-injection case runs everywhere so the contract is guarded on
    Windows too; the FIFO and device cases need a real POSIX filesystem.
    """

    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_a_source_reporting_a_non_regular_mode_is_refused(self):
        unit = make_unit(self.tmp.name, "fake", b"")
        source = unit / "tail"
        dest = os.path.join(self.tmp.name, "dest")
        real = os.stat

        class FifoMode:
            def __init__(self, wrapped):
                self._wrapped = wrapped

            def __getattr__(self, name):
                return getattr(self._wrapped, name)

            @property
            def st_mode(self):
                base = self._wrapped.st_mode & ~stat.S_IFMT(self._wrapped.st_mode)
                return base | stat.S_IFIFO

        def fake(path, *args, **kwargs):
            info = real(path, *args, **kwargs)
            return FifoMode(info) if str(path) == str(source) else info

        with unittest.mock.patch.object(os, "stat", side_effect=fake):
            code, _ = run(self.mod, ["snapshot-tail", "--unit", str(unit),
                                     "--dest", dest])
        self.assertEqual(code, self.mod.EXIT_SOURCE)
        self.assertEqual(os.listdir(dest) if os.path.isdir(dest) else [], [],
                         "a non-regular source must publish nothing")

    def test_a_swap_to_a_non_regular_type_after_open_is_rejected(self):
        """The second check exists for the window between stat and open.

        Round 5 asked for this on every platform rather than only where a real
        FIFO can be made, since the swap window is the reason the check is
        doubled at all."""
        unit = make_unit(self.tmp.name, "swap", b"payload")
        source = str(unit / "tail")
        dest = os.path.join(self.tmp.name, "dest")
        real_fstat = os.fstat

        class FifoMode:
            def __init__(self, wrapped):
                self._wrapped = wrapped

            def __getattr__(self, name):
                return getattr(self._wrapped, name)

            @property
            def st_mode(self):
                base = self._wrapped.st_mode & ~stat.S_IFMT(self._wrapped.st_mode)
                return base | stat.S_IFIFO

        seen = []

        def swapped(fd):
            info = real_fstat(fd)
            seen.append(fd)
            return FifoMode(info)

        with unittest.mock.patch.object(os, "fstat", side_effect=swapped):
            with self.assertRaises(self.mod.SnapshotError) as ctx:
                self.mod.bounded_read(source)
        self.assertEqual(ctx.exception.code, self.mod.EXIT_SOURCE)
        self.assertTrue(seen, "the post-open check must actually run")
        with self.assertRaises(OSError):
            real_fstat(seen[0])  # the descriptor was closed on rejection
        self.assertEqual(os.listdir(dest) if os.path.isdir(dest) else [], [])

    def test_a_failure_wrapping_the_descriptor_closes_it_and_maps_the_exit(self):
        """Round 5 review, New 2: os.fdopen sat outside the cleanup block, so a
        failure there left an owner-less descriptor open, and a raw OSError
        escaped main instead of becoming the documented exit 4."""
        unit = make_unit(self.tmp.name, "wrap", b"payload")
        source = str(unit / "tail")
        captured = []
        real_open = os.open

        def track(path, *args, **kwargs):
            fd = real_open(path, *args, **kwargs)
            captured.append(fd)
            return fd

        with unittest.mock.patch.object(os, "open", side_effect=track):
            with unittest.mock.patch.object(
                    os, "fdopen", side_effect=OSError(24, "too many files")):
                with self.assertRaises(self.mod.SnapshotError) as ctx:
                    self.mod.bounded_read(source)
        self.assertEqual(ctx.exception.code, self.mod.EXIT_SOURCE)
        self.assertTrue(captured)
        with self.assertRaises(OSError):
            os.fstat(captured[0])  # closed, not leaked

    def test_a_corrupt_archived_manifest_is_rejected(self):
        """Round 5 review, New 3: validation listed manifest.json and read only
        tail.bin, so an archive whose recovery metadata was unreadable passed
        and got published as good."""
        path = os.path.join(self.tmp.name, "badmanifest.zip")
        payload = b"actual bytes"
        manifest = {"bytes_copied": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest()}
        with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("tail.bin", payload)
            zf.writestr("manifest.json", "{not json at all")
        with self.assertRaises(self.mod.SnapshotError) as ctx:
            self.mod.validate_archive(path, manifest)
        self.assertEqual(ctx.exception.code, self.mod.EXIT_ARCHIVE)

    def test_an_archived_manifest_that_disagrees_is_rejected(self):
        path = os.path.join(self.tmp.name, "mismatch.zip")
        payload = b"actual bytes"
        manifest = {"bytes_copied": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest()}
        with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("tail.bin", payload)
            zf.writestr("manifest.json", json.dumps(dict(manifest, sha256="0" * 64)))
        with self.assertRaises(self.mod.SnapshotError) as ctx:
            self.mod.validate_archive(path, manifest)
        self.assertEqual(ctx.exception.code, self.mod.EXIT_ARCHIVE)

    def test_a_regular_source_is_unaffected(self):
        payload = bytes(range(256)) * 8
        unit = make_unit(self.tmp.name, "regular", payload)
        dest = os.path.join(self.tmp.name, "dest")
        code, out = run(self.mod, ["snapshot-tail", "--unit", str(unit),
                                   "--dest", dest, "--json"])
        self.assertEqual(code, 0)
        manifest = json.loads(out)["manifest"]
        self.assertEqual(manifest["bytes_copied"], len(payload))
        self.assertEqual(manifest["capture_outcome"], "complete_bounded_read")

    @unittest.skipIf(os.name == "nt", "needs a real POSIX filesystem")
    def test_a_fifo_is_refused_rather_than_blocking(self):
        unit = Path(self.tmp.name) / "prun-task-fifo"
        unit.mkdir()
        os.mkfifo(str(unit / "tail"))
        dest = os.path.join(self.tmp.name, "dest")
        # Run out of process with a timeout: the pre-fix failure mode was a
        # hang, which an in-process assertion cannot survive to report.
        proc = subprocess.run(
            [sys.executable, "-B", str(MODULE), "snapshot-tail",
             "--unit", str(unit), "--dest", dest],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(proc.returncode, self.mod.EXIT_SOURCE, proc.stderr)
        self.assertIn("not a regular file", proc.stderr)

    @unittest.skipIf(os.name == "nt", "needs a real POSIX filesystem")
    def test_a_device_source_does_not_publish_an_empty_capture(self):
        unit = Path(self.tmp.name) / "prun-task-dev"
        unit.mkdir()
        os.symlink("/dev/null", str(unit / "tail"))
        dest = os.path.join(self.tmp.name, "dest")
        code, _ = run(self.mod, ["snapshot-tail", "--unit", str(unit),
                                 "--dest", dest])
        self.assertEqual(code, self.mod.EXIT_SOURCE)
        self.assertEqual(os.listdir(dest) if os.path.isdir(dest) else [], [])

    @unittest.skipIf(os.name == "nt", "needs a real POSIX filesystem")
    def test_a_symlink_to_a_regular_file_is_still_a_valid_source(self):
        """Both type checks follow links on purpose; rejecting them would break
        an ordinary and correct way to name a tail."""
        real_tail = Path(self.tmp.name) / "actual-tail"
        real_tail.write_bytes(b"linked payload")
        unit = Path(self.tmp.name) / "prun-task-link"
        unit.mkdir()
        os.symlink(str(real_tail), str(unit / "tail"))
        dest = os.path.join(self.tmp.name, "dest")
        code, out = run(self.mod, ["snapshot-tail", "--unit", str(unit),
                                   "--dest", dest, "--json"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["manifest"]["bytes_copied"],
                         len(b"linked payload"))


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dest = os.path.join(self.tmp.name, "dest")
        self.unit = make_unit(self.tmp.name, "pub", b"payload" * 100)

    def _snap(self, output):
        return run(self.mod, ["snapshot-tail", "--unit", str(self.unit),
                              "--output", output])

    def test_an_existing_destination_is_refused(self):
        out = os.path.join(self.dest, "fixed.zip")
        code, _ = self._snap(out)
        self.assertEqual(code, 0)
        before = Path(out).read_bytes()
        code, _ = self._snap(out)
        self.assertEqual(code, self.mod.EXIT_COLLISION)
        self.assertEqual(Path(out).read_bytes(), before,
                         "a refused publication must not alter the artifact")

    def test_concurrent_attempts_yield_exactly_one_success(self):
        """The destination must already exist so the six threads race on the
        link rather than on the mkdir.

        Establish that precondition through ensure_dest_dir, which is what a
        real first run would have used. A plain os.makedirs picks up the
        caller's umask: on a box with umask 002 it yields mode 0775, and
        ensure_dest_dir then rightly refuses a group-accessible state
        directory, so all six threads fail before reaching os.link. Windows
        hid this, because the mode check is a no-op there.
        """
        out = os.path.join(self.dest, "race.zip")
        self.mod.ensure_dest_dir(self.dest)
        results = []
        lock = threading.Lock()

        def attempt():
            code, _ = self._snap(out)
            with lock:
                results.append(code)

        threads = [threading.Thread(target=attempt) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(results.count(0), 1, f"expected one winner, got {results}")
        self.assertEqual(set(results) - {0}, {self.mod.EXIT_COLLISION})

    def test_a_link_failure_that_is_not_a_collision_never_falls_back(self):
        """Lack of hard-link support, an ACL denial, a filter driver, or an SMB
        server can surface as another OSError. None may downgrade."""
        out = os.path.join(self.dest, "unsupported.zip")
        with unittest.mock.patch.object(
                os, "link", side_effect=OSError(1, "not supported")):
            with unittest.mock.patch.object(os, "replace") as replace:
                with unittest.mock.patch.object(os, "rename") as rename:
                    code, _ = self._snap(out)
        self.assertEqual(code, self.mod.EXIT_PUBLISH)
        replace.assert_not_called()
        rename.assert_not_called()
        self.assertFalse(os.path.exists(out))

    def test_publication_succeeds_even_if_the_temp_unlink_fails(self):
        """After os.link returns, the artifact is visible and valid. Reporting
        failure there would be wrong.

        Asserting only exit 0 and the artifact was too weak: deleting the whole
        unlink-and-warn block from publish left both facts unchanged, so a
        build that retained every .snap-*.part and warned about none would have
        passed. The mock call, the warning text, and the surviving temporary
        file are what pin the behaviour.
        """
        out = os.path.join(self.dest, "keep.zip")
        with unittest.mock.patch.object(
                os, "unlink", side_effect=OSError("locked")) as unlink:
            code, output = run(self.mod, ["snapshot-tail", "--unit", str(self.unit),
                                          "--output", out, "--json"])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(out))
        self.assertEqual(unlink.call_count, 1, "the cleanup must be attempted")
        warning = json.loads(output)["warning"]
        self.assertIsNotNone(warning, "a retained temporary file must be reported")
        self.assertIn(".snap-", warning)
        leftovers = [f for f in os.listdir(self.dest) if f.startswith(".snap-")]
        self.assertEqual(len(leftovers), 1,
                         "the temporary file really did survive")

    def test_an_unexpected_exception_leaves_no_temporary_file(self):
        """Round 1 review, High 2: the handler caught only SnapshotError, so any
        other exception left the .part behind and exited by traceback, outside
        the documented 0/3/4/5/6 contract."""
        out = os.path.join(self.dest, "boom.zip")
        with unittest.mock.patch.object(self.mod, "build_archive",
                                        side_effect=MemoryError("not a SnapshotError")):
            with self.assertRaises(MemoryError):
                self._snap(out)
        leftovers = [f for f in os.listdir(self.dest) if f.startswith(".snap-")]
        self.assertEqual(leftovers, [],
                         "cleanup must not depend on the exception type")
        self.assertFalse(os.path.exists(out))

    @unittest.skipIf(os.name == "nt", "chmod is a no-op on nt")
    def test_a_chmod_failure_leaves_no_temporary_file(self):
        """chmod ran outside the cleanup block, so a denial there leaked the
        .part. Windows could never surface this, because chmod is skipped."""
        out = os.path.join(self.dest, "perm.zip")
        with unittest.mock.patch.object(os, "chmod",
                                        side_effect=PermissionError(1, "denied")):
            with self.assertRaises(PermissionError):
                self._snap(out)
        leftovers = [f for f in os.listdir(self.dest) if f.startswith(".snap-")]
        self.assertEqual(leftovers, [], "the .part must not survive")

    def test_an_archive_failure_leaves_no_final_name(self):
        out = os.path.join(self.dest, "bad.zip")
        with unittest.mock.patch.object(
                self.mod, "validate_archive",
                side_effect=self.mod.SnapshotError(self.mod.EXIT_ARCHIVE, "nope")):
            code, _ = self._snap(out)
        self.assertEqual(code, self.mod.EXIT_ARCHIVE)
        self.assertFalse(os.path.exists(out))
        leftovers = [f for f in os.listdir(self.dest) if f.startswith(".snap-")]
        self.assertEqual(leftovers, [], "the temporary file must be cleaned up")


class ArchiveValidationTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_members_are_stored_not_deflated(self):
        unit = make_unit(self.tmp.name, "stored", b"z" * 4096)
        dest = os.path.join(self.tmp.name, "d")
        _, out = run(self.mod, ["snapshot-tail", "--unit", str(unit),
                                "--dest", dest, "--json"])
        with zipfile.ZipFile(json.loads(out)["published"]) as zf:
            for info in zf.infolist():
                self.assertEqual(info.compress_type, zipfile.ZIP_STORED)

    def test_a_compressed_member_is_rejected(self):
        """The positive test only proves the writer stores. Disabling the
        validator's stored-only condition left every case here green, so the
        documented branch could vanish without a failure."""
        path = os.path.join(self.tmp.name, "deflated.zip")
        payload = b"z" * 4096
        manifest = {"bytes_copied": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest()}
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("tail.bin", payload)
            zf.writestr("manifest.json", json.dumps(manifest))
        with self.assertRaises(self.mod.SnapshotError) as ctx:
            self.mod.validate_archive(path, manifest)
        self.assertEqual(ctx.exception.code, self.mod.EXIT_ARCHIVE)
        self.assertIn("not stored", str(ctx.exception))

    def test_an_extra_member_is_rejected(self):
        """ZIP permits duplicate and extra names, so validation checks the
        member multiset rather than trusting construction."""
        path = os.path.join(self.tmp.name, "tampered.zip")
        manifest = {"bytes_copied": 1, "sha256": hashlib.sha256(b"x").hexdigest()}
        with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("tail.bin", b"x")
            # A matching manifest, so the member-set branch is what fails.
            # Writing `{}` here let the later comparison raise the same code,
            # and the test stayed green with the member check deleted.
            zf.writestr("manifest.json", json.dumps(manifest))
            zf.writestr("extra.txt", "surprise")
        with self.assertRaises(self.mod.SnapshotError) as ctx:
            self.mod.validate_archive(path, manifest)
        self.assertEqual(ctx.exception.code, self.mod.EXIT_ARCHIVE)
        self.assertIn("unexpected archive members", str(ctx.exception))

    def test_a_digest_mismatch_is_rejected(self):
        """Round 6 review: this wrote `{}` as the archived manifest, so the new
        manifest comparison rejected it first and the digest check was never
        reached. The test would have stayed green with that check deleted."""
        path = os.path.join(self.tmp.name, "wrong.zip")
        manifest = {"bytes_copied": 6, "sha256": hashlib.sha256(b"other").hexdigest()}
        with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("tail.bin", b"actual")
            zf.writestr("manifest.json", json.dumps(manifest))
        with self.assertRaises(self.mod.SnapshotError) as ctx:
            self.mod.validate_archive(path, manifest)
        self.assertEqual(ctx.exception.code, self.mod.EXIT_ARCHIVE)
        self.assertIn("digest", str(ctx.exception))

    def test_a_length_mismatch_is_rejected_on_its_own(self):
        """The length branch needs a matching manifest too, or it is shadowed
        the same way the digest branch was."""
        path = os.path.join(self.tmp.name, "shortlen.zip")
        payload = b"actual"
        manifest = {"bytes_copied": 99, "sha256": hashlib.sha256(payload).hexdigest()}
        with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
            zf.writestr("tail.bin", payload)
            zf.writestr("manifest.json", json.dumps(manifest))
        with self.assertRaises(self.mod.SnapshotError) as ctx:
            self.mod.validate_archive(path, manifest)
        self.assertIn("length", str(ctx.exception))


@unittest.skipIf(os.name == "nt", "POSIX permission semantics")
class PosixPermissionTests(unittest.TestCase):
    def setUp(self):
        self.mod = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_a_created_state_dir_is_owner_only(self):
        dest = os.path.join(self.tmp.name, "state")
        self.mod.ensure_dest_dir(dest)
        mode = stat.S_IMODE(os.stat(dest).st_mode)
        self.assertEqual(mode & (stat.S_IRWXG | stat.S_IRWXO), 0)

    def test_a_broad_pre_existing_state_dir_is_refused(self):
        """Creation mode says nothing about a directory that already existed."""
        dest = os.path.join(self.tmp.name, "loose")
        os.makedirs(dest, mode=0o777)
        os.chmod(dest, 0o777)
        with self.assertRaises(self.mod.SnapshotError):
            self.mod.ensure_dest_dir(dest)

    def test_the_artifact_is_owner_only(self):
        unit = make_unit(self.tmp.name, "perm", b"secret")
        dest = os.path.join(self.tmp.name, "d")
        _, out = run(self.mod, ["snapshot-tail", "--unit", str(unit),
                                "--dest", dest, "--json"])
        published = json.loads(out)["published"]
        mode = stat.S_IMODE(os.stat(published).st_mode)
        self.assertEqual(mode & (stat.S_IRWXG | stat.S_IRWXO), 0,
                         "a snapshot extends the lifetime of prompts and tool "
                         "output; it must not be group or world readable")


if __name__ == "__main__":
    unittest.main()
