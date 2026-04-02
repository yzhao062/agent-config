from __future__ import annotations

import argparse
from pathlib import Path


TEMPLATE = """# {title}

- Figure ID: `{name}`
- Archetype: `{archetype}`
- Target section/file: `{target}`

## Goal

Describe what this figure must help a reviewer understand.

## Reviewer Takeaway

One sentence stating what a reviewer should remember after seeing this figure.

## Required Elements

- element 1
- element 2
- element 3

## Required Arrows Or Relationships

- relationship 1
- relationship 2

## Suggested Layout

Describe left-to-right, top-to-bottom, layered, or other layout logic.

## In-Figure Text

List the short labels or box text that should appear in the figure.

## Caption Draft

Write a concise proposal-ready caption.

## Editable Source Plan

- Preferred source format:
- Source file under `figure-src/`:
- Final exported file under `figure/`:

## Outside-Tool Prompt Pack

If using Gemini/Sora/Nano Banana, place the final structured prompt here.

## TODO

- [ ] Finalize labels
- [ ] Build editable source
- [ ] Export PDF
"""


def main() -> None:
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
            if (candidate / "00-project-description.tex").exists() and (candidate / "figure-spec").exists():
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

    parser = argparse.ArgumentParser(
        description="Create a figure spec scaffold for the active proposal."
    )
    parser.add_argument(
        "--proposal-dir",
        help=(
            "Proposal workspace path such as `proposals/nsf-25-533-fairos`. "
            "If omitted, the script will try to infer the current workspace."
        ),
    )
    parser.add_argument("--name", required=True)
    parser.add_argument(
        "--archetype",
        default="overview-architecture",
        choices=[
            "overview-architecture",
            "thrust-mechanism",
            "workflow-or-method-pipeline",
            "timeline-or-work-plan",
            "ecosystem-or-adoption",
            "evidence-or-impact",
        ],
    )
    parser.add_argument("--title")
    parser.add_argument("--target", default="00-project-description.tex")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    current_dir = Path.cwd().resolve()
    repo_root = find_repo_root(current_dir)
    proposal_dir = (
        resolve_user_path(args.proposal_dir, current_dir, repo_root)
        if args.proposal_dir
        else detect_proposal_dir(repo_root, current_dir)
    )
    if proposal_dir is None:
        raise SystemExit(
            "Could not infer a proposal workspace. Pass --proposal-dir explicitly."
        )
    figure_spec_dir = proposal_dir / "figure-spec"
    figure_src_dir = proposal_dir / "figure-src"
    figure_spec_dir.mkdir(parents=True, exist_ok=True)
    figure_src_dir.mkdir(parents=True, exist_ok=True)

    spec_path = figure_spec_dir / f"{args.name}.md"
    if spec_path.exists() and not args.overwrite:
        raise SystemExit(f"{spec_path} already exists. Use --overwrite to replace it.")

    title = args.title or args.name.replace("-", " ").title()
    content = TEMPLATE.format(
        title=title,
        name=args.name,
        archetype=args.archetype,
        target=args.target,
    )
    spec_path.write_text(content, encoding="utf-8")
    print(spec_path)


if __name__ == "__main__":
    main()
