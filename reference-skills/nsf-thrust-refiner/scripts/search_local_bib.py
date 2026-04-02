from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ENTRY_RE = re.compile(
    r"@(?P<kind>\w+)\s*\{\s*(?P<key>[^,]+),(?P<body>.*?)(?=^@\w+\s*\{|\Z)",
    re.S | re.M,
)
FIELD_RE = re.compile(
    r"(?P<field>\w+)\s*=\s*[\{\"](?P<value>.*?)[\}\"],?\s*(?=\w+\s*=|\Z)",
    re.S,
)
SUPPORT_ROOTS = ("template", "examples/proposals")


@dataclass
class BibHit:
    key: str
    title: str
    authors: str
    path: Path
    score: int


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


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


def list_proposal_workspaces(container: Path) -> list[Path]:
    if not container.exists():
        return []
    if (container / "00-project-description.tex").exists():
        return [container.resolve()]
    workspaces = []
    for path in sorted(container.iterdir()):
        if path.is_dir() and (path / "00-project-description.tex").exists():
            workspaces.append(path.resolve())
    return workspaces


def detect_proposal_dirs(repo_root: Path, current_dir: Path) -> list[Path]:
    for candidate in (current_dir.resolve(), *current_dir.resolve().parents):
        if (candidate / "00-project-description.tex").exists() and (candidate / "bibs").exists():
            return [candidate]
        if candidate == repo_root:
            break

    legacy = repo_root / "proposals"
    if (legacy / "00-project-description.tex").exists():
        return [legacy.resolve()]
    return list_proposal_workspaces(legacy)


def extract_entries(path: Path) -> list[BibHit]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    hits: list[BibHit] = []
    for match in ENTRY_RE.finditer(text):
        fields = {
            m.group("field").lower(): " ".join(m.group("value").split())
            for m in FIELD_RE.finditer(match.group("body"))
        }
        hits.append(
            BibHit(
                key=match.group("key").strip(),
                title=fields.get("title", ""),
                authors=fields.get("author", ""),
                path=path,
                score=0,
            )
        )
    return hits


def iter_bibs(repo_root: Path, proposal_dirs: list[Path]) -> list[BibHit]:
    results: list[BibHit] = []
    seen_paths: set[Path] = set()

    for proposal_dir in proposal_dirs:
        if not proposal_dir.exists():
            continue
        for path in proposal_dir.rglob("*.bib"):
            if path in seen_paths:
                continue
            seen_paths.add(path)
            results.extend(extract_entries(path))

    for root in SUPPORT_ROOTS:
        base = repo_root / root
        if not base.exists():
            continue
        for path in base.rglob("*.bib"):
            if path in seen_paths:
                continue
            seen_paths.add(path)
            results.extend(extract_entries(path))
    return results


def score_hit(hit: BibHit, terms: list[str]) -> int:
    haystack = normalize(" ".join([hit.title, hit.authors, hit.key]))
    return sum(term in haystack for term in terms)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search local .bib files for candidate citations."
    )
    parser.add_argument(
        "--proposal-dir",
        help=(
            "Optional proposal workspace path such as "
            "`proposals/nsf-25-533-fairos`. Strongly recommended when the repo "
            "contains multiple proposal workspaces."
        ),
    )
    parser.add_argument(
        "terms",
        nargs="+",
        help="Keyword terms to match against local bibliography entries.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=12,
        help="Maximum number of hits to print.",
    )
    args = parser.parse_args()

    current_dir = Path.cwd().resolve()
    repo_root = find_repo_root(current_dir)
    if args.proposal_dir:
        proposal_dirs = list_proposal_workspaces(
            resolve_user_path(args.proposal_dir, current_dir, repo_root)
        )
        if not proposal_dirs:
            proposal_candidate = resolve_user_path(
                args.proposal_dir, current_dir, repo_root
            )
            if proposal_candidate.exists():
                proposal_dirs = [proposal_candidate]
    else:
        proposal_dirs = detect_proposal_dirs(repo_root, current_dir)
    terms = [normalize(term) for term in args.terms]
    hits = iter_bibs(repo_root, proposal_dirs)
    scored = []
    for hit in hits:
        score = score_hit(hit, terms)
        if score > 0:
            hit.score = score
            scored.append(hit)

    scored.sort(key=lambda item: (-item.score, item.path.as_posix(), item.key))
    for hit in scored[: args.limit]:
        rel = hit.path.relative_to(repo_root).as_posix()
        print(f"[{hit.score}] {hit.key} | {hit.title} | {hit.authors} | {rel}")


if __name__ == "__main__":
    main()
