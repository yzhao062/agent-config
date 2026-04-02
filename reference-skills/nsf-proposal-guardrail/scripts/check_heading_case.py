from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


IGNORE_FILENAMES = {"10-aim0-example1.tex", "10-aim0-example2.tex"}
SKIP_DIR_PARTS = {"context", "guardrail", "out", "figure", "figure-src", "figure-spec"}
HEADING_RE = re.compile(
    r"^\s*\\(?P<level>section|subsection|subsubsection)\*?"
    r"(?:\[[^\]]*\])?\{(?P<title>.+)\}\s*$",
    re.MULTILINE,
)
LATEX_COMMAND_WITH_ARG_RE = re.compile(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?\{([^{}]*)\}")
LATEX_COMMAND_RE = re.compile(r"\\[A-Za-z@]+\*?")
WORD_SPLIT_RE = re.compile(r"[-/]")
TRIM_CHARS = ".,:;!?()[]{}\"'`"
ALLOWED_LOWERCASE = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "into",
    "nor",
    "of",
    "on",
    "or",
    "per",
    "the",
    "to",
    "via",
    "vs",
    "with",
}


@dataclass
class HeadingIssue:
    file: str
    line: int
    level: str
    title: str
    offending_words: list[str]


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def normalize_title(title: str) -> str:
    value = title.replace("~", " ").replace("\\&", "&")
    previous = None
    while previous != value:
        previous = value
        value = LATEX_COMMAND_WITH_ARG_RE.sub(r"\1", value)
    value = LATEX_COMMAND_RE.sub("", value)
    value = value.replace("{", "").replace("}", "")
    return " ".join(value.split())


def word_needs_capitalization(word: str) -> bool:
    if not word:
        return False
    if not any(char.isalpha() for char in word):
        return False
    if any(char.isdigit() for char in word):
        return False
    if word.isupper():
        return False
    if word[0].isupper():
        return False
    if any(char.isupper() for char in word[1:]):
        return False
    return word.lower() not in ALLOWED_LOWERCASE


def find_offending_words(title: str) -> list[str]:
    cleaned = normalize_title(title)
    offending: list[str] = []
    for token in cleaned.split():
        for part in WORD_SPLIT_RE.split(token):
            word = part.strip(TRIM_CHARS)
            if word_needs_capitalization(word):
                offending.append(word)
    return offending


def iter_tex_files(proposal_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(proposal_dir.rglob("*.tex")):
        if path.name in IGNORE_FILENAMES:
            continue
        if any(part in SKIP_DIR_PARTS for part in path.parts):
            continue
        files.append(path)
    return files


def build_report(proposal_dir: Path) -> dict[str, object]:
    issues: list[HeadingIssue] = []
    for path in iter_tex_files(proposal_dir):
        text = path.read_text(encoding="utf-8")
        relative = str(path.relative_to(proposal_dir)).replace("\\", "/")
        for match in HEADING_RE.finditer(text):
            title = match.group("title").strip()
            offending = find_offending_words(title)
            if not offending:
                continue
            issues.append(
                HeadingIssue(
                    file=relative,
                    line=line_number(text, match.start()),
                    level=match.group("level"),
                    title=title,
                    offending_words=offending,
                )
            )
    return {
        "proposal_dir": str(proposal_dir),
        "heading_style": (
            "Title Case for sectioning commands; lowercase connector words are "
            "tolerated, but lowercase content words are flagged."
        ),
        "issues": [asdict(item) for item in issues],
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = ["# Heading Case Report", ""]
    lines.append(f"- Proposal dir: `{report['proposal_dir']}`")
    lines.append(f"- Expected style: {report['heading_style']}")
    lines.append("")
    lines.append("## Findings")
    issues = report["issues"]
    if issues:
        for item in issues:
            words = ", ".join(f"`{word}`" for word in item["offending_words"])
            lines.append(
                f"- {item['file']}:{item['line']} | `{item['level']}` | "
                f"`{item['title']}` | offending words: {words}"
            )
    else:
        lines.append("- None found.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check section, subsection, and subsubsection titles for Title Case."
    )
    parser.add_argument("--proposal-dir", required=True, help="Proposal workspace path.")
    parser.add_argument("--output-json", help="Optional JSON report path.")
    parser.add_argument("--output-md", help="Optional Markdown report path.")
    args = parser.parse_args()

    proposal_dir = Path(args.proposal_dir).resolve()
    report = build_report(proposal_dir)

    if args.output_json:
        output_json = Path(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.output_md:
        output_md = Path(args.output_md)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(render_markdown(report), encoding="utf-8")
    if not args.output_json and not args.output_md:
        print(render_markdown(report))


if __name__ == "__main__":
    main()
