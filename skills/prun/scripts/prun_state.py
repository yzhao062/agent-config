#!/usr/bin/env python3
"""Discover and recover output stranded in prun unit directories.

Two commands, one implementation. `report-state` reads and classifies.
`snapshot-tail` copies one tail into a durable labelled archive.

Neither queries process state. This module records no PID, sends no signal,
and reaches no conclusion about whether anything is running. THE ONLY SAFE
OPERATION HERE IS SNAPSHOTTING A TAIL: nothing in this output says that
deleting, overwriting, or promoting a unit is safe, because without the
process identity of anywhere-agents#29 Part B that cannot be established.

See anywhere-agents#29 Part A for the design and the four review rounds
that shaped it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import stat
import sys
import tempfile
import time
import zipfile

SCHEMA_VERSION = 1

# Exit codes are fixed and numeric so automation can branch on them.
EXIT_OK = 0
EXIT_PARTIAL = 1          # some units could not be inspected
EXIT_USAGE = 2
EXIT_COLLISION = 3        # destination already exists
EXIT_SOURCE = 4           # source could not be opened
EXIT_ARCHIVE = 5          # archive construction or validation failed
EXIT_PUBLISH = 6          # publication failed for a reason other than collision

UNIT_GLOB_PREFIX = "prun-task-"
TAIL_NAME = "tail"
RESULT_ENTRY = "result-file"
LEGACY_PID_ENTRY = "dispatch-pid"
# A result path and a PID are both short. The cap exists so a stale unit
# pointing at an endless source cannot consume the sweep.
MAX_ENTRY_BYTES = 1 << 16

# result_path_state: what happened to the `result-file` ENTRY.
# result: what was observed at the TARGET, when one was reached.
# The legal pairs are exhaustive; see _LEGAL_PAIRS.
_LEGAL_PAIRS = {
    "resolved": {"present", "empty", "missing", "unknown"},
    "absent-entry": {"unknown"},
    "invalid-entry": {"unknown"},
    "unreadable": {"unknown"},
}


class SnapshotError(Exception):
    """Carries the exit code the CLI should return."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


# --------------------------------------------------------------- discovery


def default_roots():
    return [tempfile.gettempdir()]


def iter_units(roots, problems=None):
    """Yield unit directories under each root, sorted for reproducibility.

    Discovery failures are appended to `problems` rather than skipped. A root
    that cannot be listed, and a root that does not exist, both used to yield
    nothing and leave the run looking clean, so an unreadable corpus and a
    mistyped path were indistinguishable from an empty one. For a command whose
    purpose is finding stranded output, that is the most costly silence
    available: it reads as "nothing here to recover".
    """
    if problems is None:
        problems = []
    seen = set()
    for root in roots:
        try:
            names = sorted(os.listdir(root))
        except OSError as exc:
            problems.append({"stage": "root", "root": root,
                             "error": exc.__class__.__name__})
            continue
        for name in names:
            if not name.startswith(UNIT_GLOB_PREFIX):
                continue
            path = os.path.join(root, name)
            key = os.path.normcase(os.path.abspath(path))
            if key in seen:
                continue
            seen.add(key)
            # os.stat directly, never os.path.isdir: CPython's genericpath
            # catches OSError inside isdir and returns False, so an except
            # clause around it is unreachable and a denied entry vanished from
            # the sweep with no error and exit 0. Measured, not assumed.
            try:
                info = os.stat(path)
            except OSError as exc:
                problems.append({"stage": "unit-entry", "unit": path,
                                 "error": exc.__class__.__name__})
                continue
            if stat.S_ISDIR(info.st_mode):
                yield path


def _read_entry(unit, name):
    """Read one entry file. Returns (text, problem).

    `problem` is "absent" only for FileNotFoundError. Every other OSError
    keeps its class name, because a denied or failing read is a gap in the
    observation rather than evidence that the entry was never written. The
    earlier `os.path.exists` pre-check could not tell those apart and also
    raced the open.
    """
    path = os.path.join(unit, name)
    try:
        info = os.stat(path)
    except FileNotFoundError:
        return None, "absent"
    except OSError as exc:
        return None, exc.__class__.__name__
    if not stat.S_ISREG(info.st_mode):
        # Same boundary the tail already enforces. A FIFO here blocked the
        # whole sweep on open, and a link to an endless device would have read
        # until memory ran out; both from one stale unit directory.
        return None, "NotARegularFile"
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        return None, "absent"
    except OSError as exc:
        return None, exc.__class__.__name__
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            return None, "NotARegularFile"
        # Read one byte past the cap, in a loop because os.read may return
        # short. Stopping silently at the cap turned a truncated entry into an
        # affirmative result: a long entry whose first MAX_ENTRY_BYTES happened
        # to strip down to a real path was reported as resolved/present with no
        # error. Over-length is a failed observation, so it is named as one.
        chunks = []
        budget = MAX_ENTRY_BYTES + 1
        while budget > 0:
            chunk = os.read(fd, budget)
            if not chunk:
                break
            chunks.append(chunk)
            budget -= len(chunk)
    except OSError as exc:
        return None, exc.__class__.__name__
    finally:
        os.close(fd)
    raw = b"".join(chunks)
    if len(raw) > MAX_ENTRY_BYTES:
        return None, "EntryTooLarge"
    return raw.decode("utf-8", "replace").strip(), None


def classify_result(unit):
    """Return (result_path_state, result, resolved_path, problem).

    An absolute entry pointing anywhere is `resolved`. Measuring the real
    corpus before implementing showed all 217 legacy entries are absolute and
    outside their unit, pointing into other sessions' scratch directories, so
    treating that as an anomaly would classify every unit as unknown. The
    reporter only stats the target and never opens it.

    A failed observation is never reported as an outcome. Only
    FileNotFoundError proves a target is gone. A denial, an I/O error, or an
    unsupported operation yields `resolved/unknown` and an error entry, so a
    reader is never told a result is missing when the command merely could not
    look at it. Catching every OSError as `missing` made the one claim this
    command exists to avoid.
    """
    raw, problem = _read_entry(unit, RESULT_ENTRY)
    if problem == "absent":
        return "absent-entry", "unknown", None, None
    if problem is not None:
        return ("unreadable", "unknown", None,
                {"stage": "result-entry", "error": problem})
    if not raw:
        return "invalid-entry", "unknown", None, None
    if not os.path.isabs(raw):
        # A relative entry may only name something beneath its own unit.
        target = os.path.normpath(os.path.join(unit, raw))
        if not os.path.normcase(target).startswith(
                os.path.normcase(os.path.abspath(unit)) + os.sep):
            return "invalid-entry", "unknown", None, None
    else:
        target = raw
    try:
        info = os.stat(target)
    except FileNotFoundError:
        return "resolved", "missing", target, None
    except OSError as exc:
        return ("resolved", "unknown", target,
                {"stage": "result-target", "error": exc.__class__.__name__})
    if not stat.S_ISREG(info.st_mode):
        # `present` and `empty` are defined over a file and its bytes. A
        # directory has an st_size too, so getsize alone reported one as
        # `empty` here and could report it as `present` on other filesystems.
        return ("resolved", "unknown", target,
                {"stage": "result-target", "error": "NotARegularFile"})
    return ("resolved", ("empty" if info.st_size == 0 else "present"),
            target, None)


def inspect_unit(unit, include_legacy_pid=False):
    """One unit's evidence. Never raises; failures become `errors` entries."""
    record = {"unit": unit, "errors": []}
    try:
        path_state, result, target, problem = classify_result(unit)
    except Exception as exc:  # defensive: one unit must not end the sweep
        path_state, result, target = "unreadable", "unknown", None
        problem = {"stage": "result", "error": exc.__class__.__name__}
    # Every documented field is set on every path. The old early return here
    # omitted result_target, so the one record a reader most needs to inspect
    # was the one missing a key.
    record["result_path_state"] = path_state
    record["result"] = result
    record["result_target"] = target
    if problem:
        record["errors"].append(problem)

    tail = os.path.join(unit, TAIL_NAME)
    try:
        info = os.stat(tail)
    except FileNotFoundError:
        record["tail_bytes"] = 0
    except OSError as exc:
        record["tail_bytes"] = None
        record["errors"].append({"stage": "tail", "error": exc.__class__.__name__})
    else:
        if stat.S_ISREG(info.st_mode):
            record["tail_bytes"] = info.st_size
        else:
            record["tail_bytes"] = None
            record["errors"].append({"stage": "tail", "error": "NotARegularFile"})

    if include_legacy_pid:
        raw, problem = _read_entry(unit, LEGACY_PID_ENTRY)
        # Named to make misuse obvious. A recorded PID is stale, possibly
        # reused, and says nothing about liveness. It never sorts or classifies.
        record["legacy_pid_unverified"] = raw if problem is None else None
        # A denied read is not the same as no entry, and this caller used to
        # flatten both to None with no error, so the sweep reported itself
        # complete while one observation had failed. Absence stays silent.
        if problem is not None and problem != "absent":
            record["errors"].append({"stage": "legacy-pid", "error": problem})

    assert record["result"] in _LEGAL_PAIRS[record["result_path_state"]], (
        f"illegal pair {record['result_path_state']}/{record['result']}")
    return record


# ---------------------------------------------------------------- reporting


def run_report(args):
    # Absolute once, at the boundary. A relative --root propagated into
    # iter_units, and classify_result then compared a relative unit path
    # against abspath(unit), so a valid in-unit relative result entry was
    # misread as invalid-entry. It also made the documented-absolute
    # `roots` and `unit` fields relative.
    roots = [os.path.abspath(r) for r in (args.root or default_roots())]
    discovery = []
    records = [inspect_unit(u, args.include_legacy_pid)
               for u in iter_units(roots, discovery)]

    shown = [r for r in records
             if (r["tail_bytes"] or 0) >= args.min_tail_bytes]
    if args.sort == "tail-bytes-desc":
        shown.sort(key=lambda r: (-(r["tail_bytes"] or 0),
                                  os.path.normcase(r["unit"])))
    else:
        shown.sort(key=lambda r: os.path.normcase(r["unit"]))

    partial = bool(discovery) or any(r["errors"] for r in records)

    if args.json:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "roots": roots,
            "unit_count": len(records),
            "discovery_errors": discovery,
            "units": shown,
            "safety": "Snapshotting a tail is the only safe operation offered "
                      "here. This output does not establish that deleting, "
                      "overwriting, or promoting any unit is safe.",
        }
        if args.summary:
            payload["summary"] = _summarize(records)
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        _print_table(shown, args.include_legacy_pid)
        for problem in discovery:
            where = problem.get("root") or problem.get("unit")
            print(f"discovery failed: {where} ({problem['error']})",
                  file=sys.stderr)
        if args.summary:
            _print_summary(_summarize(records))
        print("\nSnapshotting a tail is the only safe operation offered here.")
        print("This output does not establish that deleting, overwriting, or")
        print("promoting any unit is safe.")
        if partial:
            print(chr(10) + "This sweep is incomplete; see the errors column "
                  "and any discovery failures above.", file=sys.stderr)

    return EXIT_PARTIAL if partial else EXIT_OK


def _summarize(records):
    """Two disjoint byte counters, because one would have to derive something.

    The first counter names the predicate it observed rather than an action
    it cannot authorize. `recoverable` was operational language a step from
    the rejected `salvageable`, and neither a missing target nor an empty one
    proves no other copy exists or that a live producer will not fill it.
    `missing_or_empty_result` covers units whose result path resolved to a
    file that is missing or empty. `unresolved` covers
    units whose result was never classified at all. Folding the second into
    the first would assert that an unclassified unit lost its output, which
    this slice declines to claim. Leaving it out entirely is worse: a run
    whose units all died before writing `result-file` would report
    a zero first counter while holding megabytes of tail, and a reader would take
    that as nothing to salvage.
    """
    summary = {"units": len(records), "by_result": {}, "by_path_state": {},
               "missing_or_empty_result_bytes": 0,
               "missing_or_empty_result_units": 0,
               "unresolved_bytes": 0, "unresolved_units": 0}
    for r in records:
        summary["by_result"][r["result"]] = summary["by_result"].get(r["result"], 0) + 1
        key = r["result_path_state"]
        summary["by_path_state"][key] = summary["by_path_state"].get(key, 0) + 1
        tail = r["tail_bytes"] or 0
        if tail <= 0:
            continue
        if r["result"] in ("missing", "empty"):
            summary["missing_or_empty_result_bytes"] += tail
            summary["missing_or_empty_result_units"] += 1
        elif r["result"] == "unknown":
            summary["unresolved_bytes"] += tail
            summary["unresolved_units"] += 1
    return summary


def _print_table(records, include_legacy_pid):
    header = f"{'unit':<52} {'result':<9} {'path':<13} {'tail bytes':>11}"
    if include_legacy_pid:
        header += "  legacy_pid_unverified"
    print(header)
    print("-" * len(header))
    for r in records:
        tail = "?" if r["tail_bytes"] is None else f"{r['tail_bytes']:,}"
        line = (f"{os.path.basename(r['unit'])[:52]:<52} {r['result']:<9} "
                f"{r['result_path_state']:<13} {tail:>11}")
        if include_legacy_pid:
            line += f"  {r.get('legacy_pid_unverified') or '-'}"
        print(line)
        for err in r["errors"]:
            print(f"    error [{err['stage']}]: {err['error']}")


def _print_summary(summary):
    print(f"\nunits {summary['units']}   "
          f"missing-or-empty result {summary['missing_or_empty_result_units']} units, "
          f"{summary['missing_or_empty_result_bytes'] / 1048576:.1f} MiB")
    print(f"  unresolved    : {summary['unresolved_units']} units, "
          f"{summary['unresolved_bytes'] / 1048576:.1f} MiB "
          f"(tail present, result never classified)")
    print(f"  by result     : {summary['by_result']}")
    print(f"  by path state : {summary['by_path_state']}")


# ----------------------------------------------------------------- snapshot


def state_root():
    """Durable, per-user. Not the temp directory the tails already live in."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    else:
        # Resolved from $HOME explicitly. A tilde produced by shell parameter
        # expansion is not reliably expanded, so the docs never show one.
        base = os.environ.get("XDG_STATE_HOME") or ""
        if not base:
            base = os.path.join(os.path.expanduser("~"), ".local", "state")
    return os.path.join(base, "anywhere-agents", "prun", "snapshots")


def ensure_dest_dir(path):
    """Create owner-only, and refuse a pre-existing directory that is broader.

    Creation mode says nothing about a directory that already existed, so an
    existing one is checked rather than assumed.
    """
    if os.path.isdir(path):
        if os.name != "nt":
            mode = stat.S_IMODE(os.stat(path).st_mode)
            if mode & (stat.S_IRWXG | stat.S_IRWXO):
                raise SnapshotError(
                    EXIT_PUBLISH,
                    f"{path} is group- or world-accessible (mode {mode:04o}); "
                    f"refusing to write snapshots there. "
                    f"Fix with: chmod 700 {path}")
        return
    try:
        os.makedirs(path, mode=0o700, exist_ok=True)
    except OSError as exc:
        raise SnapshotError(EXIT_PUBLISH, f"cannot create {path}: {exc}")


def _open_regular_source(source):
    """Open `source` for reading, refusing anything that is not a regular file.

    The type is checked twice on purpose. The pre-open stat rejects the common
    cases cheaply; the post-open fstat closes the window in which the path is
    swapped between the two calls. Both follow symlinks, which is intended: a
    link to a regular file is a valid source, and a link to a FIFO is not.

    On POSIX the open is non-blocking, because opening a reader on a FIFO with
    no writer blocks forever. A snapshot command that hangs is worse than one
    that refuses, and the reporter already rejects these types.
    """
    try:
        info = os.stat(source)
    except OSError as exc:
        raise SnapshotError(EXIT_SOURCE, f"cannot open {source}: {exc}")
    if not stat.S_ISREG(info.st_mode):
        raise SnapshotError(
            EXIT_SOURCE,
            f"{source} is not a regular file; refusing to snapshot it")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(source, flags)
    except OSError as exc:
        raise SnapshotError(EXIT_SOURCE, f"cannot open {source}: {exc}")
    handle = None
    try:
        opened = os.fstat(fd)
        if not stat.S_ISREG(opened.st_mode):
            raise SnapshotError(
                EXIT_SOURCE,
                f"{source} is not a regular file; refusing to snapshot it")
        # fdopen belongs inside the cleanup. Outside it, a failure here left
        # the descriptor open with no owner. Ownership transfers only once
        # fdopen has returned, which is what `handle is None` tracks.
        handle = os.fdopen(fd, "rb")
    except SnapshotError:
        os.close(fd)
        raise
    except OSError as exc:
        os.close(fd)
        raise SnapshotError(EXIT_SOURCE, f"cannot open {source}: {exc}")
    except BaseException:
        os.close(fd)
        raise
    return handle, opened


def bounded_read(source):
    """Copy at most the size observed on the open handle.

    A bounded best-effort read, NOT a coherent filesystem snapshot. If the
    producer truncates or rewrites while this runs, bytes can come from
    different generations and still total n, so nothing is inferred from
    bytes_copied == n.

    The source must be a regular file. Without that check a device such as
    /dev/null reported st_size 0 and published an empty archive as a complete
    capture, and a FIFO blocked the open indefinitely.
    """
    handle, opened = _open_regular_source(source)
    with handle:
        n = opened.st_size
        chunks = []
        remaining = n
        while remaining > 0:
            chunk = handle.read(min(1 << 20, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
    data = b"".join(chunks)
    return data, n


def build_archive(tmp_path, data, n, source):
    outcome = "complete_bounded_read" if len(data) == n else "short_read"
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_path": source,
        "source_size_at_open": n,
        "bytes_copied": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "source_may_be_live": True,
        "capture_outcome": outcome,
        "note": "A bounded best-effort read. Equal byte counts do not prove "
                "the source was unchanged during the copy.",
    }
    try:
        with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_STORED,
                             allowZip64=True) as zf:
            info = zipfile.ZipInfo("tail.bin")
            info.compress_type = zipfile.ZIP_STORED
            # force_zip64 so a member over the classic limit cannot fail only
            # while it is being finalized.
            with zf.open(info, "w", force_zip64=True) as member:
                member.write(data)
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
    except (OSError, zipfile.BadZipFile) as exc:
        raise SnapshotError(EXIT_ARCHIVE, f"cannot build archive: {exc}")
    return manifest


def validate_archive(path, manifest):
    """Reject anything that is not exactly the two expected stored members."""
    try:
        with zipfile.ZipFile(path) as zf:
            names = [i.filename for i in zf.infolist()]
            if sorted(names) != ["manifest.json", "tail.bin"]:
                raise SnapshotError(
                    EXIT_ARCHIVE,
                    f"unexpected archive members: {names}")
            for info in zf.infolist():
                if info.compress_type != zipfile.ZIP_STORED:
                    raise SnapshotError(EXIT_ARCHIVE,
                                        f"{info.filename} is not stored")
            payload = zf.read("tail.bin")
            # Read the manifest back too. Listing it proved only that the name
            # was present, so an archive whose recovery metadata was corrupt
            # passed validation and got published as good.
            stored = json.loads(zf.read("manifest.json").decode("utf-8"))
    except SnapshotError:
        raise
    except (OSError, zipfile.BadZipFile, KeyError, ValueError,
            UnicodeDecodeError) as exc:
        raise SnapshotError(EXIT_ARCHIVE, f"archive did not validate: {exc}")
    if stored != manifest:
        raise SnapshotError(EXIT_ARCHIVE,
                            "manifest.json disagrees with the manifest written")
    if len(payload) != manifest["bytes_copied"]:
        raise SnapshotError(EXIT_ARCHIVE, "tail.bin length disagrees with manifest")
    if hashlib.sha256(payload).hexdigest() != manifest["sha256"]:
        raise SnapshotError(EXIT_ARCHIVE, "tail.bin digest disagrees with manifest")


def publish(tmp_path, final_path):
    """Atomic, and never replaces.

    Publication succeeds the moment os.link returns. A later failure to unlink
    the temporary name is a cleanup warning, not a failed snapshot, and a crash
    in that interval leaves two names for one inode rather than a corrupt
    artifact.

    Only FileExistsError is a collision. Lack of hard-link support, an ACL
    denial, a filter driver, or an SMB server can surface as another OSError,
    and none of those may fall back to a replacing operation.
    """
    try:
        os.link(tmp_path, final_path)
    except FileExistsError:
        raise SnapshotError(EXIT_COLLISION,
                            f"{final_path} already exists; refusing to replace")
    except OSError as exc:
        raise SnapshotError(
            EXIT_PUBLISH,
            f"cannot publish by hard link ({exc.__class__.__name__}: {exc}); "
            f"not falling back to a replacing operation")
    warning = None
    try:
        os.unlink(tmp_path)
    except OSError as exc:
        warning = f"published, but the temporary file {tmp_path} remains: {exc}"
    return warning


def run_snapshot(args):
    unit = os.path.abspath(args.unit)
    if not os.path.isdir(unit):
        raise SnapshotError(EXIT_USAGE, f"{unit} is not a directory")
    # The tail path is derived, never taken from unit-controlled content, so
    # there is no traversal surface here.
    source = os.path.join(unit, TAIL_NAME)

    if args.output:
        final_path = os.path.abspath(args.output)
        dest_dir = os.path.dirname(final_path)
        if os.path.basename(final_path) != os.path.basename(args.output).strip():
            raise SnapshotError(EXIT_USAGE, "output name may not traverse")
        ensure_dest_dir(dest_dir)
    else:
        dest_dir = os.path.abspath(args.dest) if args.dest else state_root()
        ensure_dest_dir(dest_dir)
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        final_path = os.path.join(
            dest_dir, f"snapshot-{stamp}-{secrets.token_hex(4)}.zip")

    data, n = bounded_read(source)

    fd, tmp_path = tempfile.mkstemp(prefix=".snap-", suffix=".part",
                                    dir=dest_dir)
    # Everything after mkstemp runs under one cleanup. chmod used to sit
    # outside it, so a denial there left the .part behind and escaped the
    # documented exit codes by traceback. The handler also caught only
    # SnapshotError, so any other exception leaked the file on every platform.
    fd_open = True
    published = False
    try:
        os.close(fd)
        fd_open = False
        if os.name != "nt":
            os.chmod(tmp_path, 0o600)
        manifest = build_archive(tmp_path, data, n, source)
        validate_archive(tmp_path, manifest)
        warning = publish(tmp_path, final_path)
        # publish returns normally when the link succeeded, including when its
        # own unlink failed and produced a warning. That run keeps the artifact
        # and stays exit 0, so it must not be treated as unpublished here.
        published = True
    finally:
        if fd_open:
            try:
                os.close(fd)
            except OSError:
                pass
        if not published:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    if args.json:
        json.dump({"published": final_path, "manifest": manifest,
                   "warning": warning}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print(f"published {final_path}")
        print(f"  {manifest['bytes_copied']:,} of {manifest['source_size_at_open']:,} "
              f"bytes  {manifest['capture_outcome']}")
        print(f"  sha256 {manifest['sha256']}")
        print("  This is a bounded best-effort copy of a possibly live file.")
        print("  It is not a result and does not mean the unit is finished.")
    if warning:
        print(warning, file=sys.stderr)
    return EXIT_OK


# --------------------------------------------------------------------- CLI


def build_parser():
    parser = argparse.ArgumentParser(
        prog="prun_state",
        description="Discover and recover output stranded in prun units. "
                    "Reads and copies only; never signals a process.")
    sub = parser.add_subparsers(dest="command", required=True)

    rep = sub.add_parser("report-state", help="read-only classification")
    rep.add_argument("--root", action="append",
                     help="directory holding unit dirs; repeatable")
    rep.add_argument("--json", action="store_true")
    rep.add_argument("--min-tail-bytes", type=int, default=0,
                     help="display filter only; not a classification boundary")
    rep.add_argument("--sort", choices=["path", "tail-bytes-desc"],
                     default="path")
    rep.add_argument("--include-legacy-pid", action="store_true",
                     help="show the recorded PID; it is unverified, may be "
                          "stale or reused, and must not drive any decision")
    rep.add_argument("--summary", action="store_true")
    rep.set_defaults(func=run_report)

    snap = sub.add_parser("snapshot-tail", help="copy one tail, durably")
    snap.add_argument("--unit", required=True)
    group = snap.add_mutually_exclusive_group()
    group.add_argument("--dest", help="destination directory")
    group.add_argument("--output", help="exact destination file")
    snap.add_argument("--json", action="store_true")
    snap.set_defaults(func=run_snapshot)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return exc.code


if __name__ == "__main__":
    sys.exit(main())
