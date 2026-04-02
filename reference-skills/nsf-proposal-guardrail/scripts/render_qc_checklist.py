#!/usr/bin/env python3
"""
Render a parsed solicitation JSON file into a markdown quality-control checklist.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


COMMON_WORKSPACE_TARGETS = {
    "Project Summary": ["00-project-summary.tex"],
    "Project Description": ["00-project-description.tex"],
    "Data Management Plan": ["31-data-management.tex"],
    "Facilities, Equipment and Other Resources": [
        "34-facility.tex",
        "34-facility-standalone.tex",
    ],
    "Collaboration Plan": ["32-collaboration-plan.tex"],
    "Broadening Participation in Computing Plan": ["33-bpc.tex"],
    "Collaborators and Other Affiliations": ["30-collaborators.tex"],
    "Results from Prior NSF Support": [
        "21-prior-nsf-support.tex",
        "00-project-description.tex",
    ],
    "References Cited": ["00-project-description.tex"],
    "Letters of Collaboration": ["letters"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", required=True, help="Path to parsed solicitation JSON.")
    parser.add_argument(
        "--proposal-dir",
        help=(
            "Path to one proposal workspace such as `proposals/nsf-25-533-fairos`. "
            "If omitted, the script will try to infer the current workspace."
        ),
    )
    parser.add_argument(
        "--workspace",
        dest="proposal_dir_legacy",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--output", help="Write markdown output to this path instead of stdout.")
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "skills").exists() and (candidate / "template").exists():
            return candidate
    return start


def resolve_user_path(raw_path: str, current_dir: Path, repo_root: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    current_candidate = (current_dir / path).resolve()
    if current_candidate.exists():
        return current_candidate
    return (repo_root / path).resolve()


def detect_proposal_dir(repo_root: Path, current_dir: Path) -> Path | None:
    for candidate in (current_dir.resolve(), *current_dir.resolve().parents):
        if (candidate / "00-project-description.tex").exists() and (candidate / "context").exists():
            return candidate
        if candidate == repo_root:
            break
    legacy = repo_root / "proposals"
    if (legacy / "00-project-description.tex").exists():
        return legacy.resolve()
    workspaces = [
        path.resolve()
        for path in sorted(legacy.iterdir())
        if path.is_dir() and (path / "00-project-description.tex").exists()
    ] if legacy.exists() else []
    if len(workspaces) == 1:
        return workspaces[0]
    return None


def find_targets(repo_root: Path, proposal_dir: Path | None) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    template_dir = repo_root / "template"
    for document, rel_paths in COMMON_WORKSPACE_TARGETS.items():
        hits = []
        if proposal_dir is not None:
            for rel_path in rel_paths:
                candidate = proposal_dir / rel_path
                if candidate.exists():
                    hits.append(str(candidate))
        for rel_path in rel_paths:
            candidate = template_dir / rel_path
            if candidate.exists():
                hits.append(str(candidate))
        if hits:
            found[document] = hits
    return found


def format_metadata(data: dict) -> list[str]:
    metadata = data.get("metadata", {})
    lines = ["## Source Summary", ""]
    lines.append(f"- Source files: {', '.join(data.get('source_files', [])) or 'None'}")
    lines.append(
        f"- Primary solicitation number: {metadata.get('primary_solicitation_number') or 'None detected'}"
    )
    lines.append(
        f"- Solicitation numbers: {', '.join(metadata.get('solicitation_numbers', [])) or 'None detected'}"
    )
    lines.append(
        f"- Replaced solicitation numbers: {', '.join(metadata.get('replaced_solicitation_numbers', [])) or 'None detected'}"
    )
    lines.append(
        f"- Referenced solicitation numbers: {', '.join(metadata.get('referenced_solicitation_numbers', [])) or 'None detected'}"
    )
    lines.append(
        f"- Program title candidates: {', '.join(metadata.get('program_title_candidates', [])) or 'None detected'}"
    )
    lines.append(
        f"- Deadline candidates: {', '.join(metadata.get('deadline_candidates', [])) or 'None detected'}"
    )
    lines.append(
        f"- NSF unit candidates: {', '.join(metadata.get('nsf_unit_candidates', [])) or 'None detected'}"
    )
    lines.append("")
    return lines


def evidence_line(item: dict) -> str:
    source = item.get("source_file", "unknown source")
    heading = item.get("heading")
    heading_text = f" | heading: {heading}" if heading else ""
    return f"{source}{heading_text}"


def render_requirement_section(title: str, items: list[dict], target_map: dict[str, list[str]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.append("- None extracted")
        lines.append("")
        return lines

    for item in sorted(items, key=lambda value: (-value.get("confidence", 0), value.get("document") or "")):
        document = item.get("document") or "General rule"
        target_hits = target_map.get(document, [])
        template_status = f"template: {', '.join(target_hits)}" if target_hits else "template: no mapped file found"
        lines.append(
            f"- {document} | confidence {item.get('confidence', 0):.2f} | {template_status}"
        )
        lines.append(f"  Requirement: {item.get('requirement', '')}")
        lines.append(f"  Evidence: {evidence_line(item)}")
        lines.append(f"  Excerpt: {item.get('evidence_excerpt', '')}")
    lines.append("")
    return lines


def render_general_section(title: str, items: list[dict]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.append("- None extracted")
        lines.append("")
        return lines
    for item in sorted(items, key=lambda value: -value.get("confidence", 0)):
        lines.append(f"- Confidence {item.get('confidence', 0):.2f} | {item.get('requirement', '')}")
        lines.append(f"  Evidence: {evidence_line(item)}")
        lines.append(f"  Excerpt: {item.get('evidence_excerpt', '')}")
    lines.append("")
    return lines


def render_template_coverage(target_map: dict[str, list[str]]) -> list[str]:
    lines = ["## Template Coverage Map", ""]
    if not target_map:
        lines.append("- No proposal workspace mapping resolved")
        lines.append("")
        return lines
    for document, _hits in COMMON_WORKSPACE_TARGETS.items():
        present = target_map.get(document)
        if present:
            lines.append(f"- {document}: present at {', '.join(present)}")
        else:
            lines.append(f"- {document}: no mapped file found")
    lines.append("")
    return lines


def render_open_questions(data: dict) -> list[str]:
    questions = data.get("open_questions", [])
    notes = data.get("notes", [])
    lines = ["## Open Questions", ""]
    if not questions and not notes:
        lines.append("- None")
        lines.append("")
        return lines
    for question in questions:
        lines.append(f"- {question}")
    for note in notes:
        lines.append(f"- Note: {note}")
    lines.append("")
    return lines


def build_markdown(data: dict, repo_root: Path, proposal_dir: Path | None) -> str:
    requirements = data.get("requirements", {})
    target_map = find_targets(repo_root, proposal_dir)

    lines = ["# NSF Solicitation QC Checklist", ""]
    lines.extend(format_metadata(data))
    lines.extend(render_requirement_section("Required Proposal Components", requirements.get("required_documents", []), target_map))
    lines.extend(
        render_requirement_section("Conditional Components", requirements.get("conditional_documents", []), target_map)
    )
    lines.extend(
        render_general_section("Prohibited or Restricted Items", requirements.get("prohibited_or_restricted", []))
    )
    lines.extend(render_general_section("Page Limits", requirements.get("page_limits", [])))
    lines.extend(render_general_section("Review Criteria", requirements.get("review_criteria", [])))
    lines.extend(render_general_section("Eligibility and Proposal Limits", requirements.get("eligibility_and_limits", [])))
    lines.extend(render_general_section("Budget and Duration Rules", requirements.get("budget_and_duration", [])))
    lines.extend(
        render_general_section("Submission and Formatting Rules", requirements.get("submission_and_formatting", []))
    )
    lines.extend(
        render_general_section("Program-Specific Requirements", requirements.get("program_specific_requirements", []))
    )
    lines.extend(render_template_coverage(target_map))
    lines.extend(render_open_questions(data))
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    current_dir = Path.cwd().resolve()
    repo_root = find_repo_root(current_dir)
    data = load_json(resolve_user_path(args.requirements, current_dir, repo_root))
    raw_proposal_dir = args.proposal_dir or args.proposal_dir_legacy
    proposal_dir = (
        resolve_user_path(raw_proposal_dir, current_dir, repo_root)
        if raw_proposal_dir
        else detect_proposal_dir(repo_root, current_dir)
    )
    rendered = build_markdown(data, repo_root, proposal_dir)
    if args.output:
        output_path = resolve_user_path(args.output, current_dir, repo_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
