#!/usr/bin/env python3
"""Weekly growth watch: measure fixed roots, compare with the previous capture, flag growth.

Read-only on every inspected tree. With --save, the only write is a dated
capture in the state directory, published atomically, after which captures
beyond the newest --keep are pruned. Prints the report as JSON on stdout.
"""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

sys.dont_write_bytecode = True  # importing the sibling collector writes nothing
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scan_storage import scan, timestamp  # noqa: E402

GB = 1e9
CAPTURE_RE = re.compile(r"^capture-\d{8}T\d{6}\.json$")
METHOD = {"tool": "du -k -d 0", "unit": "KiB", "follow_symlinks": False, "schema": 1}
# Budgets for stores whose growth Track 1 of the steady-state plan owns.
BUDGETS = {"agy-dispatch": 30.0, "pack-cache-one": 0.25, "pack-cache-total": 2.0}
GROWTH_FLAG_GB = 5.0
NEW_ROOT_FLAG_GB = 5.0


def named_stores(home):
    return {
        "agy-shared": home / ".gemini" / "antigravity-cli",
        "agy-dispatch": home / ".cache" / "anywhere-agents" / "dispatch-stores" / "agy",
        "grok-sessions": home / ".grok" / "sessions",
        "codex-sessions": home / ".codex" / "sessions",
        "claude-projects": home / ".claude" / "projects",
        "hf-hub": home / ".cache" / "huggingface" / "hub",
        "pip-cache": home / "Library" / "Caches" / "pip",
    }


def pack_caches(projects):
    """Distinct consumer cache roots, skipping symlinked repositories.

    Returns (caches, errors). A missing retired-repositories folder is not an
    error; a base that exists but cannot be listed is.
    """
    found, seen, errors = [], set(), []
    for base in (projects, projects / ".retired-repositories"):
        try:
            names = sorted(os.listdir(base))
        except FileNotFoundError:
            if base == projects:
                errors.append(f"{base}: not found")
            continue
        except OSError as exc:
            errors.append(f"{base}: {exc}")
            continue
        for name in names:
            repo = base / name
            cache = repo / ".agent-config" / "cache"
            try:
                if repo.is_symlink() or not repo.is_dir():
                    continue
                if cache.is_symlink() or not cache.is_dir():
                    continue
                real = os.path.realpath(cache)
            except OSError as exc:
                errors.append(f"{repo}: {exc}")
                continue
            if real not in seen:
                seen.add(real)
                found.append(cache)
    return found, errors


def measure(path, timeout):
    """One du total for a path: status and KiB (None when du gave no total).

    A partial scan still reports the KiB it could read, a lower bound.
    """
    result = scan(str(path), 0, timeout)
    kib = None
    for row in result["rows"]:
        if row["path"] == str(path):
            kib = row["allocated_kib"]
    return {"path": str(path), "status": result["status"], "kib": kib,
            "error_count": len(result["errors"])}


SPLIT_DEPTH = 2


def kind_of(path):
    """'dir', 'link', 'other', 'missing', or 'error' when the path cannot be inspected.

    Never raises, so one denied path cannot stop the rest of the run.
    """
    try:
        st = os.lstat(path)
    except (FileNotFoundError, NotADirectoryError):
        return "missing"
    except OSError:
        return "error"
    if stat.S_ISLNK(st.st_mode):
        return "link"
    return "dir" if stat.S_ISDIR(st.st_mode) else "other"


def measure_tree(path, kind, depth_left, timeout, rows, skip=None):
    """Measure a path; when its scan is partial, measure its children the same way.

    Readable siblings then keep comparable totals when their parent is
    partial (macOS privacy controls deny parts of ~/Library). ``skip`` is a
    subtree never measured on its own (the capture directory). Returns the
    path's own row.
    """
    state = kind_of(path)
    if state == "error":
        row = {"path": str(path), "status": "failed", "kib": None, "error_count": 1}
    else:
        row = measure(path, timeout)
    row["kind"] = kind
    rows.append(row)
    if row["status"] != "ok" and depth_left > 0 and state == "dir":
        children, listed = list_entries(path)
        row["children_listed"] = listed
        for child in children:
            c = path / child
            if kind_of(c) == "link" or (skip is not None and (c == skip or skip in c.parents)):
                continue
            measure_tree(c, "child", depth_left - 1, timeout, rows, skip)
    return row


def list_entries(path):
    try:
        return sorted(p.name for p in path.iterdir()), True
    except OSError:
        return [], False


def collect(home, projects, state_dir, timeout):
    entries, complete = list_entries(home)
    rows = []
    for name in entries:
        p = home / name
        if kind_of(p) not in ("link", "missing"):
            measure_tree(p, "home", SPLIT_DEPTH, timeout, rows, state_dir)
    stores = []
    for key, p in named_stores(home).items():
        if kind_of(p) not in ("link", "missing"):
            extra = []
            row = measure_tree(p, "store", SPLIT_DEPTH, timeout, extra, state_dir)
            row["store"] = key
            stores.append(row)
            rows.extend(r for r in extra if r is not row)
    caches = []
    cache_roots, discovery_errors = pack_caches(projects)
    for p in cache_roots:
        extra = []
        row = measure_tree(p, "pack-cache", SPLIT_DEPTH, timeout, extra, state_dir)
        caches.append(row)
        rows.extend(r for r in extra if r is not row)
    own = measure(state_dir, timeout) if kind_of(state_dir) == "dir" else None
    if own and own["kib"]:
        for row in rows:
            if row["kind"] in ("home", "child") and row["kib"] is not None and \
                    str(state_dir).startswith(row["path"] + os.sep):
                row["kib"] = max(0, row["kib"] - own["kib"])
                row["excluded_capture_kib"] = own["kib"]
    return {"schema_version": 1, "observed_at": timestamp(), "method": METHOD,
            "home": str(home), "home_entries": entries, "home_listing_complete": complete,
            "rows": rows, "stores": stores, "pack_caches": caches,
            "pack_cache_discovery_errors": discovery_errors}


def gb(kib):
    """KiB as decimal GB rounded for display; thresholds use ``over``."""
    return round(kib * 1024 / GB, 3) if kib is not None else None


def over(kib, limit_gb):
    """Whether a KiB count exceeds a decimal-GB limit, compared in bytes."""
    return kib * 1024 > limit_gb * GB


def partial_paths(cur):
    return sorted(path for path, r in by_path(cur).items() if r["status"] != "ok")


def evaluate(cur, prev):
    """Flags and notes for the current capture against the previous one (or None)."""
    flags, notes = [], []
    partial = partial_paths(cur)
    if partial:
        notes.append(f"{len(partial)} scans were partial or failed (listed under 'partial'); "
                     "their growth is not compared")
    dispatch = [r for r in cur["stores"] if r.get("store") == "agy-dispatch"]
    for r in dispatch:
        if r["kib"] is not None and over(r["kib"], BUDGETS["agy-dispatch"]):
            flags.append({"kind": "budget", "path": r["path"], "gb": gb(r["kib"]),
                          "budget_gb": BUDGETS["agy-dispatch"]})
    total = 0
    complete = not cur.get("pack_cache_discovery_errors")
    for err in cur.get("pack_cache_discovery_errors", []):
        notes.append(f"pack cache discovery incomplete: {err}")
    for r in cur["pack_caches"]:
        if r["kib"] is None or r["status"] != "ok":
            complete = False
        if r["kib"] is not None:
            total += r["kib"]
            if over(r["kib"], BUDGETS["pack-cache-one"]):
                flags.append({"kind": "budget", "path": r["path"], "gb": gb(r["kib"]),
                              "budget_gb": BUDGETS["pack-cache-one"]})
    if over(total, BUDGETS["pack-cache-total"]):
        flags.append({"kind": "budget", "path": "all pack caches", "gb": gb(total),
                      "budget_gb": BUDGETS["pack-cache-total"], "complete": complete})
    elif not complete:
        notes.append(f"pack cache total {gb(total)} GB covers only the caches that scanned")
    if prev is None:
        notes.append("no previous capture: baseline only, no growth comparison")
        if not cur.get("home_listing_complete"):
            notes.append("the home listing failed, so no home entry was measured")
        return flags, notes
    if prev.get("method") != cur["method"]:
        notes.append("previous capture used another method: no growth comparison")
        return flags, notes
    hours = (datetime.fromisoformat(cur["observed_at"]) -
             datetime.fromisoformat(prev["observed_at"])).total_seconds() / 3600
    notes.append(f"compared with the capture of {prev['observed_at']} ({hours:.0f} hours earlier)")
    before = by_path(prev)
    for r in by_path(cur).values():
        old = before.get(r["path"])
        if old is None or r["status"] != "ok" or old.get("status") != "ok":
            continue
        if r["kib"] is None or old.get("kib") is None:
            continue
        delta = gb(r["kib"] - old["kib"])
        if over(r["kib"] - old["kib"], GROWTH_FLAG_GB):
            flags.append({"kind": "growth", "path": r["path"], "delta_gb": delta,
                          "gb": gb(r["kib"]), "store": r.get("store")})
        if r.get("store") == "agy-shared" and r["kib"] > old["kib"]:
            notes.append(f"shared Agy store grew {delta} GB")
    if prev.get("home_listing_complete") and cur.get("home_listing_complete"):
        earlier = set(prev.get("home_entries", []))
        for r in cur["rows"]:
            name = Path(r["path"]).name
            if r["kind"] == "home" and name not in earlier and r["kib"] is not None \
                    and over(r["kib"], NEW_ROOT_FLAG_GB):
                flags.append({"kind": "new-root", "path": r["path"], "gb": gb(r["kib"])})
    else:
        notes.append("a home listing was incomplete: no new-root comparison")
    return most_specific(flags), notes


def by_path(capture):
    """One row per path, preferring a complete reading and then the named store.

    The same folder can be measured twice (once inside a split parent, once
    as a named store); comparing both would report one change twice.
    """
    selected = {}
    for row in capture["rows"] + capture["pack_caches"] + capture["stores"]:
        old = selected.get(row["path"])
        if old is None or row["status"] == "ok":
            selected[row["path"]] = row
    return selected


def most_specific(flags):
    """Drop a growth flag whose path contains another growth flag's path."""
    grown = [f["path"] for f in flags if f["kind"] == "growth"]
    return [f for f in flags if f["kind"] != "growth" or not any(
        other.startswith(f["path"] + os.sep) for other in grown)]


def captures(state_dir):
    """Dated captures, oldest first; [] before the first save. Other errors raise."""
    try:
        entries = list(state_dir.iterdir())
    except FileNotFoundError:
        return []
    return sorted(p for p in entries if CAPTURE_RE.match(p.name))


def save(state_dir, capture, keep):
    """Publish a capture, then prune to ``keep``. Returns (path, note about a failed prune or None)."""
    state_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    stamp = datetime.fromisoformat(capture["observed_at"]).strftime("%Y%m%dT%H%M%S")
    target = state_dir / f"capture-{stamp}.json"
    fd, tmp = tempfile.mkstemp(prefix=".capture-", dir=state_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(capture, fh, ensure_ascii=False, indent=1)
        os.replace(tmp, target)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    try:
        for old in captures(state_dir)[:-keep]:
            old.unlink()
    except OSError as exc:
        return target, f"capture saved but older captures were not pruned ({exc})"
    return target, None


def check_capture(capture):
    """Raise ValueError unless a capture has every field the comparison reads."""
    if not isinstance(capture, dict):
        raise ValueError("not an object")
    when = datetime.fromisoformat(capture["observed_at"])
    if when.tzinfo is None:
        raise ValueError("observed_at has no time zone")
    if not isinstance(capture["home_listing_complete"], bool):
        raise ValueError("home_listing_complete is not a boolean")
    for key in ("home_entries", "rows", "stores", "pack_caches"):
        if not isinstance(capture[key], list):
            raise ValueError(f"{key} is not a list")
    if not all(isinstance(e, str) for e in capture["home_entries"]):
        raise ValueError("home_entries holds a non-string")
    for key in ("rows", "stores", "pack_caches"):
        for row in capture[key]:
            if not (isinstance(row, dict) and isinstance(row.get("path"), str)
                    and isinstance(row.get("status"), str)
                    and (row.get("kib") is None or type(row.get("kib")) is int)):
                raise ValueError(f"malformed {key} row")


def load_previous(path):
    """The previous capture, or (None, note) when it cannot be used."""
    try:
        prev = json.loads(path.read_text())
        check_capture(prev)
        return prev, None
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return None, f"previous capture {path.name} is unreadable ({exc}); no growth comparison"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    home = Path.home()
    absolute = lambda value: Path(os.path.abspath(os.path.expanduser(value)))  # noqa: E731
    parser.add_argument("--state-dir", type=absolute, default=home / ".local" / "state" / "mac-storage-audit")
    parser.add_argument("--projects", type=absolute, default=home / "PycharmProjects")
    parser.add_argument("--timeout", type=float, default=900, help="Seconds per du call")
    parser.add_argument("--keep", type=int, default=8)
    parser.add_argument("--save", action="store_true", help="Publish this capture and prune old ones")
    args = parser.parse_args()
    if args.keep < 2 or args.timeout <= 0:
        parser.error("keep must be at least 2 and timeout positive")
    try:
        previous, unreadable = captures(args.state_dir), None
    except OSError as exc:
        previous = []
        unreadable = f"capture history cannot be listed ({exc}); no growth comparison"
    prev, unreadable = load_previous(previous[-1]) if previous else (None, unreadable)
    cur = collect(home, args.projects, args.state_dir, args.timeout)
    flags, notes = evaluate(cur, prev)
    if unreadable:
        notes = [unreadable] + [n for n in notes if not n.startswith("no previous capture")]
    report = {"observed_at": cur["observed_at"], "flags": flags, "notes": notes,
              "stores": {r["store"]: gb(r["kib"]) for r in cur["stores"]},
              "pack_cache_gb": gb(sum(r["kib"] for r in cur["pack_caches"] if r["kib"] is not None)),
              "pack_cache_count": len(cur["pack_caches"]),
              "partial": partial_paths(cur)}
    if args.save:
        saved, prune_note = save(args.state_dir, cur, args.keep)
        report["saved"] = str(saved)
        if prune_note:
            notes.append(prune_note)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
