#!/usr/bin/env python3
"""
Scaffold NSF aim/thrust files and synchronize the main project-description entrypoint.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


AIM_SLOTS = {
    1: "11-aim1.tex",
    2: "12-aim2.tex",
    3: "13-aim3.tex",
    4: "14-aim4.tex",
}

ENTRYPOINT_NAME = "00-project-description.tex"
EXAMPLE_AIMS = ("10-aim0-example1", "10-aim0-example2")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--family",
        required=True,
        choices=("methodology-driven", "ecosystem-building"),
        help="Dominant proposal family used to choose the scaffold shape.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=4,
        choices=(1, 2, 3, 4),
        help="Number of active aim/thrust files to enable. Defaults to 4.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory containing the template aim files and main project description.",
    )
    parser.add_argument(
        "--tasks-per-unit",
        type=int,
        default=2,
        choices=(2, 3),
        help="How many subtasks/tasks to scaffold inside each active unit.",
    )
    parser.add_argument(
        "--unit-label",
        help="Override the unit label. Defaults to 'Aim' or 'Thrust' based on family.",
    )
    parser.add_argument(
        "--entrypoint",
        help="Optional explicit path to the project description entrypoint to rewrite.",
    )
    parser.add_argument(
        "--keep-example-aims",
        action="store_true",
        help="Leave 10-aim0-example inputs enabled in the entrypoint.",
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Allow overwriting non-empty existing aim files.",
    )
    return parser.parse_args()


def methodology_unit(unit_index: int, tasks_per_unit: int, unit_label: str) -> str:
    lines = [
        "% composer:sync-start",
        f"\\subsection{{{unit_label} {unit_index}: [Template Title]}}",
        f"\\label{{subsec:aim{unit_index}}}",
        "\\vspace{-0.1in}",
        "",
        "\\textbf{Objective and Motivation.}",
        "\\todo{State the scientific or technical problem this aim addresses, why it matters, and what this aim contributes to the overall proposal.}",
        "",
        "\\textbf{Limitations of Prior Approaches.}",
        "\\todo{Summarize the main gaps in prior work and why existing approaches are insufficient for this proposal.}",
        "",
        "\\textbf{Proposed Research Direction.}",
        "\\todo{Describe the high-level strategy, expected technical contributions, and how this aim connects to the other aims.}",
        "",
        "% composer:sync-end",
        "% refiner:body-start",
    ]
    for task_index in range(1, tasks_per_unit + 1):
        lines.extend(
            [
                f"\\subsubsection{{Subtask {unit_index}.{task_index}: [Subtask Title]}}",
                "\\textbf{Problem.}",
                "\\todo{State the concrete technical challenge addressed in this subtask and why it matters for the full aim.}",
                "",
                "\\textbf{Technical approach.}",
                "\\todo{Describe the method design, model or system formulation, and what is technically new in this subtask.}",
                "",
                "\\textbf{Integration handling.}",
                "\\todo{Explain how this subtask feeds later aims, interacts with other components, or stabilizes downstream behavior.}",
                "",
            ]
        )
    lines.extend(
        [
            "\\textbf{Evaluation and success criteria.}",
            "\\todo{State the local evaluation hook, measurable outcomes, and what counts as success for this aim.}",
            "",
            "\\textbf{Risks and fallback plan.}",
            "\\todo{Describe the main technical risk and the fallback or mitigation strategy.}",
            "% refiner:body-end",
            "\\vspace{-0.05in}",
            "",
        ]
    )
    return "\n".join(lines)


def ecosystem_unit(unit_index: int, tasks_per_unit: int, unit_label: str) -> str:
    lines = [
        "% composer:sync-start",
        f"\\subsection{{{unit_label} {unit_index}: [Template Title]}}",
        f"\\label{{subsec:aim{unit_index}}}",
        "\\vspace{-0.1in}",
        "",
        "\\textbf{Motivation and Background.}",
        "\\todo{State the ecosystem or infrastructure gap, who is blocked today, and why this thrust is necessary.}",
        "",
        "\\textbf{Overview.}",
        "\\todo{Describe the concrete platform, workflow, open resource, or coordination capability delivered by this thrust and how it fits the full ecosystem.}",
        "",
        "% composer:sync-end",
        "% refiner:body-start",
    ]
    for task_index in range(1, tasks_per_unit + 1):
        lines.extend(
            [
                f"\\subsubsection{{Task {unit_index}.{task_index}: [Task Title]}}",
                "\\textbf{Problem.}",
                "\\todo{State the concrete bottleneck this task removes for the ecosystem, user community, or deployment pathway.}",
                "",
                "\\textbf{Method.}",
                "\\todo{Describe the technical, organizational, governance, or interoperability work performed in this task and how it integrates with the broader ecosystem.}",
                "",
            ]
        )
    lines.extend(
        [
            "\\textbf{Milestones and measurable outcomes.}",
            "\\todo{State the deliverables, adoption evidence, and measurable outcomes expected from this thrust.}",
            "",
            "\\textbf{Dependencies and sustainability path.}",
            "\\todo{Explain dependencies on other thrusts and how this capability will be sustained or handed off after the project.}",
            "% refiner:body-end",
            "\\vspace{-0.05in}",
            "",
        ]
    )
    return "\n".join(lines)


def choose_unit_builder(family: str):
    if family == "methodology-driven":
        return methodology_unit
    return ecosystem_unit


def write_unit_file(path: Path, content: str, overwrite_existing: bool) -> None:
    if path.exists():
        existing = path.read_text(encoding="utf-8").strip()
        if existing and not overwrite_existing:
            raise FileExistsError(
                f"{path} already contains content; rerun with --overwrite-existing to replace it."
            )
    path.write_text(content, encoding="utf-8")


def rewrite_entrypoint(
    entrypoint: Path,
    active_count: int,
    keep_example_aims: bool,
) -> None:
    if not entrypoint.exists():
        return

    pattern = re.compile(r"^(\s*)%?\s*\\input\{([^}]+)\}\s*$")
    rewritten: list[str] = []
    for line in entrypoint.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if not match:
            rewritten.append(line)
            continue
        indent, name = match.groups()
        if name in EXAMPLE_AIMS:
            rewritten.append(f"{indent}\\input{{{name}}}" if keep_example_aims else f"{indent}%\\input{{{name}}}")
            continue
        if name in {slot_name.removesuffix('.tex') for slot_name in AIM_SLOTS.values()}:
            unit_index = next(index for index, slot_name in AIM_SLOTS.items() if slot_name == f"{name}.tex")
            rewritten.append(f"{indent}\\input{{{name}}}" if unit_index <= active_count else f"{indent}%\\input{{{name}}}")
            continue
        rewritten.append(line)
    entrypoint.write_text("\n".join(rewritten) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    entrypoint = Path(args.entrypoint) if args.entrypoint else output_dir / ENTRYPOINT_NAME

    unit_label = args.unit_label
    if not unit_label:
        unit_label = "Aim" if args.family == "methodology-driven" else "Thrust"

    builder = choose_unit_builder(args.family)
    try:
        for unit_index in range(1, args.count + 1):
            path = output_dir / AIM_SLOTS[unit_index]
            content = builder(unit_index, args.tasks_per_unit, unit_label)
            write_unit_file(path, content, args.overwrite_existing)
    except FileExistsError as exc:
        print(exc, file=sys.stderr)
        return 1

    rewrite_entrypoint(entrypoint, args.count, args.keep_example_aims)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
