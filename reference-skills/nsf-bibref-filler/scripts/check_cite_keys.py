from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ENTRY_RE = re.compile(
    r"@(?P<kind>\w+)\s*\{\s*(?P<key>[^,]+),(?P<body>.*?)(?=^@\w+\s*\{|\Z)",
    re.S | re.M,
)
CITE_RE = re.compile(
    r"\\[A-Za-z]*cite[A-Za-z]*\*?(?:\[[^\]]*\]){0,2}\{(?P<keys>[^}]*)\}",
    re.S,
)
SUPPORT_ROOTS = ("template", "examples/proposals")


@dataclass
class CitationUse:
    key: str
    path: Path
    line: int


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


def detect_workspace_from_file(path: Path, repo_root: Path) -> Path | None:
    start = path if path.is_dir() else path.parent
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "00-project-description.tex").exists() and (candidate / "bibs").exists():
            return candidate
        if candidate == repo_root:
            break
    return None


def load_bib_index(repo_root: Path, proposal_dirs: list[Path]) -> dict[str, list[Path]]:
    index: dict[str, list[Path]] = {}
    seen_paths: set[Path] = set()

    for proposal_dir in proposal_dirs:
        if not proposal_dir.exists():
            continue
        for bib_path in proposal_dir.rglob("*.bib"):
            if bib_path in seen_paths:
                continue
            seen_paths.add(bib_path)
            text = bib_path.read_text(encoding="utf-8", errors="ignore")
            for match in ENTRY_RE.finditer(text):
                key = match.group("key").strip()
                index.setdefault(key, []).append(bib_path)

    for root in SUPPORT_ROOTS:
        base = repo_root / root
        if not base.exists():
            continue
        for bib_path in base.rglob("*.bib"):
            if bib_path in seen_paths:
                continue
            seen_paths.add(bib_path)
            text = bib_path.read_text(encoding="utf-8", errors="ignore")
            for match in ENTRY_RE.finditer(text):
                key = match.group("key").strip()
                index.setdefault(key, []).append(bib_path)
    return index


def extract_citations(path: Path) -> list[CitationUse]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    hits: list[CitationUse] = []
    for match in CITE_RE.finditer(text):
        keys = [part.strip() for part in match.group("keys").split(",")]
        line = text.count("\n", 0, match.start()) + 1
        for key in keys:
            if not key or key == "*":
                continue
            hits.append(CitationUse(key=key, path=path, line=line))
    return hits


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check that cite keys used in .tex files exist in local .bib files."
    )
    parser.add_argument(
        "--proposal-dir",
        help=(
            "Optional proposal workspace path such as "
            "`proposals/nsf-25-533-fairos`. If omitted, the script will try to "
            "infer the workspace from the target files."
        ),
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="One or more .tex files to inspect.",
    )
    args = parser.parse_args()

    current_dir = Path.cwd().resolve()
    repo_root = find_repo_root(current_dir)
    all_hits: list[CitationUse] = []
    resolved_files: list[Path] = []
    for raw_path in args.files:
        path = resolve_user_path(raw_path, current_dir, repo_root)
        if not path.exists():
            print(f"Missing file: {raw_path}", file=sys.stderr)
            sys.exit(2)
        resolved_files.append(path)
        all_hits.extend(extract_citations(path))

    proposal_dirs: list[Path] = []
    if args.proposal_dir:
        proposal_candidate = resolve_user_path(args.proposal_dir, current_dir, repo_root)
        proposal_dirs = list_proposal_workspaces(proposal_candidate) or [proposal_candidate]
    else:
        for path in resolved_files:
            workspace = detect_workspace_from_file(path, repo_root)
            if workspace and workspace not in proposal_dirs:
                proposal_dirs.append(workspace)
        if not proposal_dirs:
            legacy = repo_root / "proposals"
            if (legacy / "00-project-description.tex").exists():
                proposal_dirs = [legacy.resolve()]
            else:
                proposal_dirs = list_proposal_workspaces(legacy)

    bib_index = load_bib_index(repo_root, proposal_dirs)
    unresolved = [hit for hit in all_hits if hit.key not in bib_index]
    print(
        f"Checked {len(all_hits)} citation uses across {len(args.files)} file(s)."
    )
    if not unresolved:
        print("All cite keys resolved in local bibliography files.")
        return

    print("Unresolved cite keys:")
    for hit in unresolved:
        rel = hit.path.relative_to(repo_root).as_posix()
        print(f"- {rel}:{hit.line} -> {hit.key}")
    sys.exit(1)


if __name__ == "__main__":
    main()
