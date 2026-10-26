#!/usr/bin/env python3
"""Collect macOS du measurements without writing to the inspected filesystem."""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
from zoneinfo import ZoneInfo


def timestamp():
    return datetime.now(ZoneInfo("America/Los_Angeles")).isoformat(timespec="seconds")


def scan(root, depth, timeout):
    result = {"root": root, "started_at": timestamp(), "rows": [], "errors": []}
    if os.path.islink(root):
        result["status"] = "symlink_skipped"
    else:
        try:
            proc = subprocess.run(
                ["du", "-k", "-d", str(depth), root],
                capture_output=True, text=True, timeout=timeout,
            )
            result["exit_code"] = proc.returncode
            result["status"] = "ok" if proc.returncode == 0 else "partial_or_failed"
            result["errors"] = proc.stderr.splitlines()
            for line in proc.stdout.splitlines():
                count, separator, path = line.partition("\t")
                if not separator or not count.isdigit():
                    result["errors"].append("Unparsed du output: " + line)
                    result["status"] = "partial_or_failed"
                    continue
                kib = int(count)
                result["rows"].append({"path": path, "allocated_kib": kib,
                                       "allocated_gb": round(kib * 1024 / 1e9, 6)})
            result["rows"].sort(key=lambda row: row["allocated_kib"], reverse=True)
        except subprocess.TimeoutExpired:
            result["status"] = "timeout"
            result["errors"] = [f"du exceeded {timeout} seconds; no complete total available"]
        except OSError as exc:
            result["status"] = "failed"
            result["errors"] = [str(exc)]
    result["finished_at"] = timestamp()
    return result


def compare(report, baseline):
    if baseline.get("schema_version") != 1 or baseline.get("method") != report["method"]:
        raise ValueError("Baseline schema or measurement method does not match")
    report["baseline_observed_at"] = baseline.get("observed_at")
    earlier = {entry["root"]: entry for entry in baseline["roots"]}
    for current in report["roots"]:
        old = earlier.get(current["root"])
        if not old:
            current["comparison"] = "unavailable: no matching baseline root"
            continue
        old_rows = {row["path"]: row for row in old["rows"]}
        current_paths = {row["path"] for row in current["rows"]}
        current["baseline_only_rows"] = [row for row in old["rows"]
                                         if row["path"] not in current_paths]
        current["current_only_paths"] = sorted(current_paths - old_rows.keys())
        complete = current["status"] == "ok" and old["status"] == "ok"
        current["comparison"] = (
            "matched paths only; absent rows are not zero or proof of deletion"
            if complete else
            "partial pair: before/after observations only, no growth inference; rescan accessible children as roots"
        )
        for row in current["rows"]:
            previous = old_rows.get(row["path"])
            if previous is not None:
                row["baseline_allocated_kib"] = previous["allocated_kib"]
                if complete:
                    row["delta_kib"] = row["allocated_kib"] - previous["allocated_kib"]
                    row["delta_gb"] = round(row["delta_kib"] * 1024 / 1e9, 6)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", help="Root to inspect; repeatable")
    parser.add_argument("--depth", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=300, help="Seconds per du invocation")
    parser.add_argument("--baseline", type=Path, help="Prior collector JSON to read")
    args = parser.parse_args()
    if args.depth < 0 or args.timeout <= 0:
        parser.error("depth must be nonnegative and timeout must be positive")
    roots = args.root or [str(Path.home()), "/private/tmp", "/private/var/folders",
                          "/Applications", "/Library"]
    roots = list(dict.fromkeys(os.path.abspath(os.path.expanduser(p)) for p in roots))
    report = {"schema_version": 1, "observed_at": timestamp(),
              "method": {"tool": "du -k -d", "depth": args.depth,
                         "unit": "KiB", "follow_symlinks": False},
              "note": "Nested roots and child rows overlap. Allocated blocks are not guaranteed reclaimable bytes. Hardlink attribution can shift child deltas without new allocation.",
              "roots": [scan(root, args.depth, args.timeout) for root in roots]}
    if args.baseline:
        try:
            compare(report, json.loads(args.baseline.read_text()))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            parser.error(f"Cannot compare baseline: {exc}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(root["status"] == "ok" for root in report["roots"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
