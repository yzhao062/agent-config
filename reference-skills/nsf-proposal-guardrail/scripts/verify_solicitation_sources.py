#!/usr/bin/env python3
"""
Extract text from a solicitation PDF and compare it against a companion raw-text copy.

This script is intentionally conservative. It verifies a fixed set of high-value
signals and surfaces source mismatches for manual review.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import fitz


PDF_NOISE_PATTERNS = [
    r"^\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}",
    r"^https?://",
    r"^Feedback$",
    r"^\d+$",
    r"^\d+\s*/\s*\d+$",
]

INTERESTING_KEYWORDS = [
    "deadline",
    "project summary",
    "project description",
    "letters of intent",
    "preliminary proposal",
    "cost sharing",
    "budget",
    "duration",
    "pi",
    "co-pi",
    "proposal",
    "review criteria",
    "open science impact",
    "leveraging cyberinfrastructure",
    "measurable outcomes",
    "letters of collaboration",
]

SIGNALS = [
    ("primary_solicitation", "Primary solicitation", r"NSF\s+\d{2,}-\d{2,4}:\s+.+"),
    ("deadline", "Deadline", r"Full Proposal Deadline\(s\).*?April \d{2}, \d{4}"),
    ("annual_deadline", "Annual deadline", r"Second Wednesday in April, Annually Thereafter"),
    ("track_selection", "Track selection", r"proposals must select one of two tracks"),
    ("standard_research_only", "Standard research only", r"Standard research proposals are the only type of proposal accepted"),
    ("collaborative_allowed", "Collaborative proposals allowed", r"Collaborative Research Proposals are allowable"),
    ("budget_limit", "Budget and duration limit", r"budget up to \$\s*600,?000.*?three-year duration"),
    ("pi_limit", "PI limit", r"Limit on Number of Proposals per PI or co-PI:\s*1"),
    ("letters_of_intent", "Letters of Intent", r"Letters of Intent:\s*Not required"),
    ("preliminary", "Preliminary proposal", r"Preliminary Proposal Submission:\s*Not required"),
    ("project_summary_limit", "Project Summary page limit", r"Project Summary\s*\(1-page limit\)"),
    ("project_description_limit", "Project Description page limit", r"Project Description\s*\(15-page limit\)"),
    ("broader_impacts_section", "Broader Impacts section", r"separate section labeled [\"“]?Broader Impacts"),
    ("cost_sharing", "Cost sharing prohibition", r"Inclusion of voluntary committed cost sharing is prohibited"),
    ("additional_review_criteria", "Additional review criteria", r"Additional Solicitation Specific Review Criteria"),
    ("open_science_impact", "Open Science Impact", r"Open Science Impact:"),
    ("leveraging_ci", "Leveraging Cyberinfrastructure", r"Leveraging Cyberinfrastructure:"),
    ("measurable_outcomes", "Measurable Outcomes", r"Measurable Outcomes:"),
    ("letters_of_collaboration", "Letters of collaboration", r"letters of collaboration"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, help="Path to solicitation PDF.")
    parser.add_argument("--txt", required=True, help="Path to companion raw text.")
    parser.add_argument("--pdf-text-output", help="Write extracted PDF text to this path.")
    parser.add_argument("--report-json", help="Write comparison JSON to this path.")
    parser.add_argument("--report-md", help="Write comparison markdown to this path.")
    parser.add_argument(
        "--tool",
        default="auto",
        choices=["auto", "pdftotext", "pymupdf"],
        help="PDF extraction backend.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Could not decode {path}")


def extract_with_pdftotext(pdf_path: Path) -> str:
    exe = shutil.which("pdftotext")
    if not exe:
        raise FileNotFoundError("pdftotext not found on PATH")
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "pdf.txt"
        subprocess.run(
            [exe, "-layout", "-enc", "UTF-8", str(pdf_path), str(out_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return read_text(out_path)


def extract_with_pymupdf(pdf_path: Path) -> str:
    document = fitz.open(str(pdf_path))
    parts: list[str] = []
    for page_number, page in enumerate(document, start=1):
        parts.append(f"=== PAGE {page_number} ===")
        parts.append(page.get_text("text"))
    return "\n\n".join(parts).strip() + "\n"


def extract_pdf_text(pdf_path: Path, tool: str) -> tuple[str, str]:
    if tool == "pdftotext":
        return extract_with_pdftotext(pdf_path), "pdftotext"
    if tool == "pymupdf":
        return extract_with_pymupdf(pdf_path), "pymupdf"
    try:
        return extract_with_pdftotext(pdf_path), "pdftotext"
    except Exception:
        return extract_with_pymupdf(pdf_path), "pymupdf"


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def clean_line(line: str) -> str:
    line = normalize_text(line)
    line = re.sub(r"\s+", " ", line).strip()
    return line


def should_skip_pdf_line(line: str) -> bool:
    if not line:
        return True
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in PDF_NOISE_PATTERNS)


def text_to_paragraphs(text: str, *, drop_pdf_noise: bool) -> list[str]:
    lines = []
    for raw_line in normalize_text(text).split("\n"):
        line = clean_line(raw_line)
        if drop_pdf_noise and should_skip_pdf_line(line):
            continue
        lines.append(line)

    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line:
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            continue
        if line.startswith("=== PAGE "):
            if current:
                paragraphs.append(" ".join(current).strip())
                current = []
            paragraphs.append(line)
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current).strip())
    return [paragraph for paragraph in paragraphs if paragraph]


def normalized_match_key(text: str) -> str:
    text = normalize_text(text).lower()
    text = re.sub(r"[^a-z0-9$ ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def find_signal(paragraphs: list[str], pattern: str) -> str | None:
    joined = "\n".join(paragraphs)
    match = re.search(pattern, joined, re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    excerpt = match.group(0)
    excerpt = re.sub(r"\s+", " ", excerpt).strip()
    return excerpt[:320] + ("..." if len(excerpt) > 320 else "")


def is_interesting_paragraph(paragraph: str) -> bool:
    lowered = paragraph.lower()
    if len(paragraph) < 25 or len(paragraph) > 900:
        return False
    return any(keyword in lowered for keyword in INTERESTING_KEYWORDS)


def text_to_candidate_lines(text: str, *, drop_pdf_noise: bool) -> list[str]:
    candidates: list[str] = []
    for raw_line in normalize_text(text).split("\n"):
        line = clean_line(raw_line)
        if drop_pdf_noise and should_skip_pdf_line(line):
            continue
        if not line or line.startswith("=== PAGE "):
            continue
        lowered = line.lower()
        if len(line) < 18 or len(line) > 260:
            continue
        if any(keyword in lowered for keyword in INTERESTING_KEYWORDS):
            candidates.append(line)
    return candidates


def unmatched_candidates(source_lines: list[str], target_lines: list[str], limit: int = 12) -> list[dict]:
    source_items = source_lines
    target_keys = [normalized_match_key(line) for line in target_lines]
    results: list[dict] = []
    for paragraph in source_items:
        source_key = normalized_match_key(paragraph)
        if not source_key:
            continue
        if source_key in target_keys:
            continue
        best_score = 0.0
        for target_key in target_keys:
            if not target_key:
                continue
            score = SequenceMatcher(None, source_key, target_key).ratio()
            if score > best_score:
                best_score = score
        if best_score < 0.72:
            results.append(
                {
                    "best_similarity": round(best_score, 2),
                    "text": paragraph[:500] + ("..." if len(paragraph) > 500 else ""),
                }
            )
        if len(results) >= limit:
            break
    return results


def compare_sources(pdf_text: str, txt_text: str, *, extraction_tool: str, pdf_path: Path, txt_path: Path) -> dict:
    pdf_paragraphs = text_to_paragraphs(pdf_text, drop_pdf_noise=True)
    txt_paragraphs = text_to_paragraphs(txt_text, drop_pdf_noise=False)
    pdf_lines = text_to_candidate_lines(pdf_text, drop_pdf_noise=True)
    txt_lines = text_to_candidate_lines(txt_text, drop_pdf_noise=False)

    signals = []
    missing_in_pdf = []
    missing_in_txt = []

    for signal_id, label, pattern in SIGNALS:
        txt_excerpt = find_signal(txt_paragraphs, pattern)
        pdf_excerpt = find_signal(pdf_paragraphs, pattern)
        status = "present_in_both"
        if txt_excerpt and not pdf_excerpt:
            status = "missing_in_pdf"
            missing_in_pdf.append(label)
        elif pdf_excerpt and not txt_excerpt:
            status = "missing_in_txt"
            missing_in_txt.append(label)
        elif not txt_excerpt and not pdf_excerpt:
            status = "missing_in_both"
        signals.append(
            {
                "id": signal_id,
                "label": label,
                "status": status,
                "txt_excerpt": txt_excerpt,
                "pdf_excerpt": pdf_excerpt,
            }
        )

    txt_only = unmatched_candidates(txt_lines, pdf_lines)
    pdf_only = unmatched_candidates(pdf_lines, txt_lines)

    report = {
        "pdf_path": str(pdf_path),
        "txt_path": str(txt_path),
        "extraction_tool": extraction_tool,
        "signals": signals,
        "missing_in_pdf": missing_in_pdf,
        "missing_in_txt": missing_in_txt,
        "txt_only_candidates": txt_only,
        "pdf_only_candidates": pdf_only,
        "summary": {
            "signals_present_in_both": sum(1 for signal in signals if signal["status"] == "present_in_both"),
            "signals_missing_in_pdf": len(missing_in_pdf),
            "signals_missing_in_txt": len(missing_in_txt),
            "txt_only_candidates": len(txt_only),
            "pdf_only_candidates": len(pdf_only),
        },
        "notes": [
            "Use solicitation.txt as the drafting-time source of truth, but confirm missing or conflicting high-value signals against the PDF.",
            "If a signal is missing in one source, inspect the PDF page manually before treating the text copy as complete.",
        ],
    }
    return report


def render_markdown(report: dict) -> str:
    lines = ["# Solicitation Source Cross-Check", ""]
    lines.append(f"- PDF: {report['pdf_path']}")
    lines.append(f"- TXT: {report['txt_path']}")
    lines.append(f"- Extraction tool: {report['extraction_tool']}")
    lines.append("")
    lines.append("## Signal Check")
    lines.append("")
    for signal in report["signals"]:
        lines.append(f"- {signal['label']}: {signal['status']}")
        if signal["txt_excerpt"]:
            lines.append(f"  TXT: {signal['txt_excerpt']}")
        if signal["pdf_excerpt"]:
            lines.append(f"  PDF: {signal['pdf_excerpt']}")
    lines.append("")

    lines.append("## High-Risk Differences")
    lines.append("")
    if not report["missing_in_pdf"] and not report["missing_in_txt"]:
        lines.append("- No key signals were missing in exactly one source")
    else:
        if report["missing_in_pdf"]:
            lines.append(f"- Missing in PDF extraction: {', '.join(report['missing_in_pdf'])}")
        if report["missing_in_txt"]:
            lines.append(f"- Missing in TXT copy: {', '.join(report['missing_in_txt'])}")
    lines.append("")

    lines.append("## TXT-Only Candidates")
    lines.append("")
    if not report["txt_only_candidates"]:
        lines.append("- None")
    else:
        for item in report["txt_only_candidates"]:
            lines.append(f"- Similarity {item['best_similarity']:.2f}: {item['text']}")
    lines.append("")

    lines.append("## PDF-Only Candidates")
    lines.append("")
    if not report["pdf_only_candidates"]:
        lines.append("- None")
    else:
        for item in report["pdf_only_candidates"]:
            lines.append(f"- Similarity {item['best_similarity']:.2f}: {item['text']}")
    lines.append("")

    lines.append("## Notes")
    lines.append("")
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def write_text(path: str | None, content: str) -> None:
    if not path:
        return
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def write_json(path: str | None, content: dict) -> None:
    if not path:
        return
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf)
    txt_path = Path(args.txt)

    pdf_text, extraction_tool = extract_pdf_text(pdf_path, args.tool)
    txt_text = read_text(txt_path)
    report = compare_sources(pdf_text, txt_text, extraction_tool=extraction_tool, pdf_path=pdf_path, txt_path=txt_path)

    write_text(args.pdf_text_output, pdf_text)
    write_json(args.report_json, report)
    markdown = render_markdown(report)
    write_text(args.report_md, markdown)

    if not args.report_json and not args.report_md:
        print(markdown)


if __name__ == "__main__":
    main()
