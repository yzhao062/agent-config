#!/usr/bin/env python3
"""
Heuristically parse NSF solicitation raw text into a structured requirement bundle.

The output is intentionally conservative: it captures candidate requirements plus
supporting evidence so an agent can review and verify them before use.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable


DOCUMENT_PATTERNS = {
    "Project Summary": [r"\bproject summary\b"],
    "Project Description": [r"\bproject description\b"],
    "References Cited": [r"\breferences cited\b"],
    "Data Management Plan": [r"\bdata management plan\b"],
    "Postdoctoral Mentoring Plan": [r"\bpostdoctoral mentoring plan\b"],
    "Facilities, Equipment and Other Resources": [
        r"\bfacilities, equipment and other resources\b",
        r"\bfacilities, equipment\b",
    ],
    "Supplementary Documents": [r"\bsupplementary documents?\b"],
    "Biographical Sketch": [r"\bbiographical sketch(?:es)?\b", r"\bbiosketch(?:es)?\b"],
    "Current and Pending Support": [
        r"\bcurrent and pending(?: \(?:other\) support)?\b",
        r"\bcurrent and pending support\b",
    ],
    "Collaborators and Other Affiliations": [
        r"\bcollaborators and other affiliations\b",
        r"\bcoa\b",
    ],
    "Letters of Collaboration": [r"\bletters? of collaboration\b"],
    "Letters of Support": [r"\bletters? of support\b"],
    "Mentoring Plan": [r"\bmentoring plan\b"],
    "Broadening Participation in Computing Plan": [
        r"\bbroadening participation in computing\b",
        r"\bbpc plan\b",
    ],
    "Collaboration Plan": [r"\bcollaboration plan\b"],
    "Results from Prior NSF Support": [r"\bresults from prior nsf support\b"],
}

SAFE_REQUIRED_DOCUMENTS = {
    "Project Summary",
    "Project Description",
    "References Cited",
    "Data Management Plan",
    "Postdoctoral Mentoring Plan",
    "Facilities, Equipment and Other Resources",
    "Supplementary Documents",
    "Biographical Sketch",
    "Current and Pending Support",
    "Collaborators and Other Affiliations",
    "Letters of Collaboration",
    "Letters of Support",
    "Mentoring Plan",
    "Broadening Participation in Computing Plan",
    "Collaboration Plan",
    "Results from Prior NSF Support",
}

CATEGORY_PATTERNS = {
    "review_criteria": [
        r"\breview criteria\b",
        r"\bintellectual merit\b",
        r"\bbroader impacts\b",
        r"\badditional review criteria\b",
    ],
    "eligibility_and_limits": [
        r"\bwho may submit proposals\b",
        r"\beligibility\b",
        r"\blimit on number of proposals\b",
        r"\bpi limit\b",
        r"\bone proposal per\b",
        r"\bno more than\b",
    ],
    "budget_and_duration": [
        r"\bbudget\b",
        r"\baward amount\b",
        r"\baward size\b",
        r"\baward duration\b",
        r"\bduration\b",
        r"\bup to \$",
    ],
    "submission_and_formatting": [
        r"\bresearch\.gov\b",
        r"\bfastlane\b",
        r"\bpage limit\b",
        r"\bmargins?\b",
        r"\bfont\b",
        r"\bsingle[- ]spaced\b",
        r"\bline spacing\b",
        r"\bsupplementary documents?\b",
    ],
    "program_specific_requirements": [
        r"\bspecial instructions\b",
        r"\bprogram-specific\b",
        r"\btrack\b",
        r"\btheme\b",
        r"\bpitch\b",
        r"\bplanning proposal\b",
    ],
}

REQUIRED_PATTERNS = [
    r"\bmust\b",
    r"\brequired\b",
    r"\bshall\b",
    r"\bneeds? to\b",
    r"\bis to\b",
    r"\binclude\b",
    r"\bsubmit\b",
]

CONDITIONAL_PATTERNS = [
    r"\bif\b",
    r"\bwhen applicable\b",
    r"\bwhere applicable\b",
    r"\bfor collaborative proposals?\b",
    r"\bfor proposals? that\b",
    r"\bif proposing\b",
    r"\bpostdoctoral\b",
    r"\bplanning proposal\b",
]

PROHIBITED_PATTERNS = [
    r"\bmust not\b",
    r"\bmay not\b",
    r"\bnot allowed\b",
    r"\bshould not\b",
    r"\bwill not be accepted\b",
    r"\bno letters? of support\b",
    r"\bdo not include\b",
]

PAGE_LIMIT_PATTERN = re.compile(r"\b\d+\s*(?:-\s*)?(?:page|pages)\b", re.IGNORECASE)
DATE_PATTERN = re.compile(
    r"\b(?:deadline|due date|full proposal deadline|target date|submission window)\b.{0,80}",
    re.IGNORECASE,
)
SOLICITATION_ID_PATTERN = re.compile(r"\bNSF\s+\d{2,}-\d{2,4}\b")
PRIMARY_SOLICITATION_PATTERN = re.compile(r"^(NSF\s+\d{2,}-\d{2,4}):\s+(.+)$")
DIRECTORATE_PATTERN = re.compile(
    r"\b(?:directorate|division|office) for [A-Z][A-Za-z& ,/-]+\b", re.IGNORECASE
)
MONTH_DATE_PATTERN = re.compile(
    r"^(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}$"
)
SECTION_START_PATTERN = re.compile(r"^Summary Of Program Requirements$", re.IGNORECASE)
TOC_PATTERN = re.compile(r"^Table Of Contents$", re.IGNORECASE)
NAVIGATION_PATTERNS = [
    r"^Skip to main content",
    r"^An official website of the United States government$",
    r"^Here's how you know$",
    r"^NSF - U\.S\. National Science Foundation - Home$",
    r"^Search NSF$",
    r"^search$",
    r"^Find Funding$",
    r"^How to Apply$",
    r"^Manage Your Award$",
    r"^Focus Areas$",
    r"^News & Events$",
    r"^About$",
    r"^Printthis Page$",
    r"^Active funding opportunity$",
    r"^This document is the current version\.$",
    r"^Create a PDF$",
    r"^To save a PDF of this solicitation",
    r"^View the program page$",
    r"^NSF Logo$",
    r"^U\.S\. National Science Foundation$",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", action="append", required=True, help="Raw text file to parse.")
    parser.add_argument("--output", help="Write JSON output to this path instead of stdout.")
    return parser.parse_args()


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Could not decode {path}")


def normalize_line(line: str) -> str:
    line = line.replace("\t", " ")
    line = re.sub(r"\s+", " ", line).strip()
    if re.fullmatch(r"\d+", line):
        return ""
    return line


def should_skip_line(line: str) -> bool:
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in NAVIGATION_PATTERNS)


def preprocess_lines(text: str) -> list[str]:
    normalized_lines = [normalize_line(raw_line) for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    normalized_lines = [line for line in normalized_lines if not should_skip_line(line)]

    started = False
    skipping_toc = False
    processed: list[str] = []

    for line in normalized_lines:
        if TOC_PATTERN.match(line):
            skipping_toc = True
            continue
        if SECTION_START_PATTERN.match(line):
            started = True
            skipping_toc = False
            processed.append(line)
            continue
        if not started:
            continue
        if skipping_toc:
            continue
        processed.append(line)

    fallback = [line for line in normalized_lines if line]
    return processed if processed else fallback


def paragraph_blocks(lines: list[str]) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line:
            if current:
                blocks.append(" ".join(current).strip())
                current = []
            continue
        if is_heading(line):
            if current:
                blocks.append(" ".join(current).strip())
                current = []
            blocks.append(line)
            continue
        current.append(line)
    if current:
        blocks.append(" ".join(current).strip())
    return blocks


def is_heading(block: str) -> bool:
    words = block.split()
    if not words or len(words) > 18 or len(block) > 140:
        return False
    if block.endswith("."):
        return False
    if re.match(r"^(?:[A-Z0-9][A-Za-z0-9()./&,-]*\s*)+$", block):
        return True
    if re.match(r"^\d+(?:\.\d+)*\s+[A-Z]", block):
        return True
    if re.match(r"^[A-Z][A-Za-z0-9 /,&()-]+:$", block):
        return True
    return False


def classify_requirement(text: str) -> str:
    lowered = text.lower()
    if any(re.search(pattern, lowered) for pattern in PROHIBITED_PATTERNS):
        return "prohibited"
    if any(re.search(pattern, lowered) for pattern in CONDITIONAL_PATTERNS):
        return "conditional"
    if any(re.search(pattern, lowered) for pattern in REQUIRED_PATTERNS):
        return "required"
    return "informational"


def confidence_score(text: str, document: str | None, category_hits: int) -> float:
    score = 0.45
    if document:
        score += 0.20
    if PAGE_LIMIT_PATTERN.search(text):
        score += 0.15
    if any(re.search(pattern, text.lower()) for pattern in PROHIBITED_PATTERNS):
        score += 0.20
    elif any(re.search(pattern, text.lower()) for pattern in REQUIRED_PATTERNS):
        score += 0.15
    elif any(re.search(pattern, text.lower()) for pattern in CONDITIONAL_PATTERNS):
        score += 0.10
    score += min(0.15, category_hits * 0.05)
    return round(min(score, 0.99), 2)


def normalize_excerpt(text: str, max_len: int = 320) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def make_item(
    *,
    requirement: str,
    source_file: str,
    heading: str | None,
    document: str | None,
    category: str,
    classification: str,
    evidence: str,
    signals: list[str],
) -> dict:
    return {
        "requirement": requirement,
        "source_file": source_file,
        "heading": heading,
        "document": document,
        "classification": classification,
        "confidence": confidence_score(requirement, document, len(signals)),
        "signals": sorted(set(signals)),
        "evidence_excerpt": normalize_excerpt(evidence),
        "category": category,
    }


def add_unique(bucket: list[dict], item: dict, seen: set[tuple[str, str, str]]) -> None:
    key = (
        item["category"],
        (item.get("document") or "").lower(),
        re.sub(r"\s+", " ", item["requirement"].lower()),
    )
    if key not in seen:
        bucket.append(item)
        seen.add(key)


def extract_items_from_block(block: str, heading: str | None, source_file: str) -> list[tuple[str, dict]]:
    items: list[tuple[str, dict]] = []
    lowered = block.lower()
    classification = classify_requirement(block)

    matched_documents = []
    for document, patterns in DOCUMENT_PATTERNS.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            matched_documents.append(document)

    category_hits: list[str] = []
    for category, patterns in CATEGORY_PATTERNS.items():
        if any(re.search(pattern, lowered) for pattern in patterns):
            category_hits.append(category)

    for document in matched_documents:
        if document in SAFE_REQUIRED_DOCUMENTS and (
            classification in {"required", "conditional", "prohibited"} or PAGE_LIMIT_PATTERN.search(block)
        ):
            if classification == "conditional":
                bucket = "conditional_documents"
            elif classification == "prohibited":
                bucket = "prohibited_or_restricted"
            else:
                bucket = "required_documents"
        elif classification == "required":
            bucket = "required_documents"
        elif classification == "conditional":
            bucket = "conditional_documents"
        elif classification == "prohibited":
            bucket = "prohibited_or_restricted"
        else:
            bucket = "program_specific_requirements"
        item = make_item(
            requirement=block,
            source_file=source_file,
            heading=heading,
            document=document,
            category=bucket,
            classification=classification,
            evidence=block,
            signals=[document] + category_hits,
        )
        items.append((bucket, item))

    if PAGE_LIMIT_PATTERN.search(block):
        page_item = make_item(
            requirement=block,
            source_file=source_file,
            heading=heading,
            document=matched_documents[0] if matched_documents else None,
            category="page_limits",
            classification=classification,
            evidence=block,
            signals=["page_limit"] + category_hits,
        )
        items.append(("page_limits", page_item))

    for category in category_hits:
        item = make_item(
            requirement=block,
            source_file=source_file,
            heading=heading,
            document=matched_documents[0] if matched_documents else None,
            category=category,
            classification=classification,
            evidence=block,
            signals=category_hits,
        )
        items.append((category, item))

    if classification == "prohibited" and not matched_documents:
        item = make_item(
            requirement=block,
            source_file=source_file,
            heading=heading,
            document=None,
            category="prohibited_or_restricted",
            classification=classification,
            evidence=block,
            signals=["prohibited"],
        )
        items.append(("prohibited_or_restricted", item))

    return items


def unique_list(values: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def parse_inputs(paths: list[Path]) -> dict:
    output = {
        "source_files": [str(path) for path in paths],
        "metadata": {
            "primary_solicitation_number": None,
            "program_title_candidates": [],
            "solicitation_numbers": [],
            "replaced_solicitation_numbers": [],
            "referenced_solicitation_numbers": [],
            "deadline_candidates": [],
            "nsf_unit_candidates": [],
        },
        "requirements": {
            "required_documents": [],
            "conditional_documents": [],
            "prohibited_or_restricted": [],
            "page_limits": [],
            "review_criteria": [],
            "eligibility_and_limits": [],
            "budget_and_duration": [],
            "submission_and_formatting": [],
            "program_specific_requirements": [],
        },
        "open_questions": [],
        "notes": [],
    }

    seen_by_bucket: dict[str, set[tuple[str, str, str]]] = defaultdict(set)

    for path in paths:
        text = read_text(path)
        full_lines = [normalize_line(raw_line) for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
        for line in full_lines:
            title_match = PRIMARY_SOLICITATION_PATTERN.match(line)
            if title_match:
                solicitation_number = title_match.group(1)
                if not output["metadata"]["primary_solicitation_number"]:
                    output["metadata"]["primary_solicitation_number"] = solicitation_number
                output["metadata"]["solicitation_numbers"].append(solicitation_number)
                output["metadata"]["program_title_candidates"].append(line)
                continue
            if line.lower().startswith("replaces:"):
                output["metadata"]["replaced_solicitation_numbers"].extend(SOLICITATION_ID_PATTERN.findall(line))
                continue
            output["metadata"]["referenced_solicitation_numbers"].extend(SOLICITATION_ID_PATTERN.findall(line))
            if MONTH_DATE_PATTERN.match(line) or "Annually Thereafter" in line:
                output["metadata"]["deadline_candidates"].append(line)
            output["metadata"]["nsf_unit_candidates"].extend(
                normalize_excerpt(match.group(0), 120) for match in DIRECTORATE_PATTERN.finditer(line)
            )

        blocks = paragraph_blocks(preprocess_lines(text))
        current_heading: str | None = None

        for index, block in enumerate(blocks):
            if is_heading(block):
                current_heading = block.rstrip(":")
                for bucket, item in extract_items_from_block(block, current_heading, str(path)):
                    add_unique(output["requirements"][bucket], item, seen_by_bucket[bucket])
                continue

            for bucket, item in extract_items_from_block(block, current_heading, str(path)):
                add_unique(output["requirements"][bucket], item, seen_by_bucket[bucket])

    output["metadata"]["program_title_candidates"] = unique_list(output["metadata"]["program_title_candidates"])[:10]
    output["metadata"]["solicitation_numbers"] = unique_list(output["metadata"]["solicitation_numbers"])
    output["metadata"]["replaced_solicitation_numbers"] = unique_list(
        output["metadata"]["replaced_solicitation_numbers"]
    )
    output["metadata"]["referenced_solicitation_numbers"] = unique_list(
        output["metadata"]["referenced_solicitation_numbers"]
    )
    output["metadata"]["deadline_candidates"] = unique_list(output["metadata"]["deadline_candidates"])[:12]
    output["metadata"]["nsf_unit_candidates"] = unique_list(output["metadata"]["nsf_unit_candidates"])[:12]

    if not output["requirements"]["review_criteria"]:
        output["open_questions"].append(
            "Review criteria were not clearly detected. Verify whether the solicitation adds criteria beyond Intellectual Merit and Broader Impacts."
        )
    if not output["requirements"]["page_limits"]:
        output["open_questions"].append(
            "No explicit page-limit language was detected. Check the solicitation PDF and governing PAPPG text for document-specific page limits."
        )
    if not output["requirements"]["required_documents"]:
        output["open_questions"].append(
            "Required proposal components were not confidently extracted. Manual review is needed before using this as a compliance checklist."
        )

    output["notes"].append(
        "This file is heuristic output. Keep low-confidence items visible until a human or agent verifies them against the source PDF/text."
    )
    return output


def main() -> None:
    args = parse_args()
    input_paths = [Path(item) for item in args.input]
    data = parse_inputs(input_paths)
    rendered = json.dumps(data, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
