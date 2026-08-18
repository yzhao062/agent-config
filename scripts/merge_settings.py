"""Merge a shared settings.json into a target settings.json, in place.

Both bootstrap entry points call this, so the merge semantics and the on-disk
format have one implementation instead of two. The PowerShell entry point used
`ConvertTo-Json`, whose indentation differs between Windows PowerShell 5.1 and
PowerShell 7 and matches neither `json.dumps`, so the same file was reformatted
by whichever machine touched it last. See anywhere-agents#36.

Usage:
    merge_settings.py <target.json> <shared.json>

Exit codes:
    0  merged, or nothing to do
    1  a file could not be read or parsed
    2  bad usage
"""
from __future__ import annotations

import json
import pathlib
import sys


def deep_merge(base: dict, over: dict) -> None:
    """Merge `over` into `base`.

    Kept byte-compatible with the inline program this replaced: a dict merges
    recursively; a list of objects replaces; a list of scalars appends with
    duplicates dropped and first-seen order kept; anything else overwrites.
    """
    for key, value in over.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            deep_merge(base[key], value)
        elif key in base and isinstance(base[key], list) and isinstance(value, list):
            if value and isinstance(value[0], dict):
                base[key] = value
            else:
                base[key] = list(dict.fromkeys(base[key] + value))
        else:
            base[key] = value


def read_json(path: pathlib.Path):
    """Read JSON as UTF-8 whatever the machine's locale says.

    Text mode picks the ANSI codepage on Windows, which is cp1252 on a default
    install, and these files carry non-ASCII. `utf-8-sig` also heals a copy
    left with a BOM by an earlier `Set-Content -Encoding UTF8`.
    """
    return json.loads(path.read_bytes().decode("utf-8-sig"))


def write_json(path: pathlib.Path, data) -> None:
    """Write the one canonical form: UTF-8, no BOM, LF, trailing newline."""
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_bytes(text.encode("utf-8"))


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        sys.stderr.write("usage: merge_settings.py <target.json> <shared.json>\n")
        return 2
    target = pathlib.Path(argv[1])
    shared = pathlib.Path(argv[2])
    try:
        shared_data = read_json(shared)
    except Exception as exc:
        sys.stderr.write("merge_settings: cannot read %s: %s\n" % (shared, exc))
        return 1
    try:
        target_data = read_json(target)
    except Exception as exc:
        sys.stderr.write("merge_settings: cannot read %s: %s\n" % (target, exc))
        return 1
    if not isinstance(target_data, dict) or not isinstance(shared_data, dict):
        sys.stderr.write("merge_settings: both files must hold a JSON object\n")
        return 1
    try:
        deep_merge(target_data, shared_data)
    except TypeError as exc:
        # An array holding a scalar first and an object later reaches
        # dict.fromkeys with an unhashable element. Reading only the first
        # element to choose the branch is deliberate parity with the inline
        # program this replaced, and the PowerShell fallback survives the same
        # input, so the two entry points disagree here. Report it and leave the
        # file alone rather than inventing a merge the other side would not
        # produce. Without this the run printed a traceback and the Bash entry
        # point, which does not read the exit code, carried on regardless.
        sys.stderr.write("merge_settings: cannot merge %s: %s\n" % (target, exc))
        return 1
    if not target_data:
        # A merge that produced nothing is a defect rather than a state worth
        # persisting; leaving the file alone keeps the old content readable.
        sys.stderr.write("merge_settings: refusing to write an empty object to %s\n" % target)
        return 1
    write_json(target, target_data)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
