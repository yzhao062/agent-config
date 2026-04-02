#!/usr/bin/env python3
"""
Instantiate a working proposal folder from the long-lived template.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from configure_aim_files import (
    AIM_SLOTS,
    ENTRYPOINT_NAME,
    choose_unit_builder,
    rewrite_entrypoint,
    write_unit_file,
)

SOLICITATION_TEXT_PLACEHOLDER = """[Replace this placeholder with the raw solicitation text before parsing.]

Paste or extract the full solicitation text into this file.
Keep solicitation.pdf in the same folder for cross-checking.
Delete this placeholder block once the real text is in place.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--template-dir",
        default="template",
        help="Source template directory. Defaults to template.",
    )
    parser.add_argument(
        "--dest",
        default="proposals",
        help="Destination working proposal directory. Defaults to proposals.",
    )
    parser.add_argument(
        "--family",
        choices=("methodology-driven", "ecosystem-building"),
        help="Optional family to immediately scaffold after copying the template.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=4,
        choices=(1, 2, 3, 4),
        help="Number of active aim/thrust files to enable when --family is used.",
    )
    parser.add_argument(
        "--tasks-per-unit",
        type=int,
        default=2,
        choices=(2, 3),
        help="How many subtasks/tasks to scaffold in each active unit.",
    )
    parser.add_argument(
        "--unit-label",
        help="Optional override for the family-specific unit label.",
    )
    parser.add_argument(
        "--keep-example-aims",
        action="store_true",
        help="Leave example aim inputs enabled in the copied project description.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow copying into an existing destination directory.",
    )
    return parser.parse_args()


def ensure_copyable(dest: Path, overwrite: bool) -> None:
    if not dest.exists():
        return
    if not overwrite:
        raise FileExistsError(
            f"{dest} already exists; rerun with --overwrite to reuse it."
        )


def instantiate_template(template_dir: Path, dest: Path, overwrite: bool) -> None:
    ensure_copyable(dest, overwrite)
    shutil.copytree(template_dir, dest, dirs_exist_ok=overwrite)


def ensure_working_layout(dest: Path) -> None:
    required_dirs = [
        dest / "out",
        dest / "guardrail",
        dest / "context",
        dest / "context" / "solicitation",
        dest / "context" / "team",
        dest / "context" / "team" / "_template",
        dest / "context" / "notes",
    ]
    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)

    solicitation_text = dest / "context" / "solicitation" / "solicitation.txt"
    if not solicitation_text.exists():
        solicitation_text.write_text(
            SOLICITATION_TEXT_PLACEHOLDER,
            encoding="utf-8",
        )


def scaffold_family(
    dest: Path,
    family: str,
    count: int,
    tasks_per_unit: int,
    unit_label: str | None,
    keep_example_aims: bool,
) -> None:
    resolved_label = unit_label or ("Aim" if family == "methodology-driven" else "Thrust")
    builder = choose_unit_builder(family)
    for unit_index in range(1, count + 1):
        unit_path = dest / AIM_SLOTS[unit_index]
        content = builder(unit_index, tasks_per_unit, resolved_label)
        write_unit_file(unit_path, content, overwrite_existing=True)
    rewrite_entrypoint(dest / ENTRYPOINT_NAME, count, keep_example_aims)


def main() -> int:
    args = parse_args()
    template_dir = Path(args.template_dir)
    dest = Path(args.dest)

    if not template_dir.exists():
        print(f"Template directory not found: {template_dir}", file=sys.stderr)
        return 1

    try:
        instantiate_template(template_dir, dest, args.overwrite)
        ensure_working_layout(dest)
        if args.family:
            scaffold_family(
                dest=dest,
                family=args.family,
                count=args.count,
                tasks_per_unit=args.tasks_per_unit,
                unit_label=args.unit_label,
                keep_example_aims=args.keep_example_aims,
            )
    except FileExistsError as exc:
        print(exc, file=sys.stderr)
        return 1

    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
