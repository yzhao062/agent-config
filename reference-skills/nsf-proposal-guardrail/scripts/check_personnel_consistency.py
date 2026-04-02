from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


IGNORE_FILENAMES = {"10-aim0-example1.tex", "10-aim0-example2.tex"}
COLLABORATOR_RE = re.compile(
    r"\\item\s+(?P<name>[^;]+);\s+(?P<institution>[^;]+);\s+(?P<role>PI|Co-PI)"
)
BOLD_ROLE_RE = re.compile(r"\\textbf\{(?P<role>PI|Co-PI)\s+(?P<name>[^}]+)\}")
PLAIN_ROLE_RE = re.compile(
    r"(?<![A-Za-z-])(?P<role>PI|Co-PI)\s+"
    r"(?P<name>[A-Z][A-Za-z.'-]+(?:\s+[A-Z][A-Za-z.'-]+){1,4})"
)
PROFILE_HEADING_RE = re.compile(r"^#\s+(?P<name>.+?)\s*$", re.MULTILINE)


@dataclass
class CanonicalPerson:
    name: str
    role: str
    institution: str


@dataclass
class Mention:
    file: str
    line: int
    role: str
    name: str
    source: str


@dataclass
class TeamProfile:
    file: str
    name: str


def normalize_space(text: str) -> str:
    return " ".join(text.split())


def normalize_name(text: str) -> str:
    return normalize_space(text).rstrip(":,.;")


def normalize_institution(text: str) -> str:
    return normalize_space(text.split(",")[0])


def slugify_name(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize_name(text).lower()).strip("-")


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def load_canonical_roster(proposal_dir: Path) -> dict[str, CanonicalPerson]:
    collaborators = proposal_dir / "30-collaborators.tex"
    roster: dict[str, CanonicalPerson] = {}
    if collaborators.exists():
        text = collaborators.read_text(encoding="utf-8")
        for match in COLLABORATOR_RE.finditer(text):
            name = normalize_name(match.group("name"))
            roster[name] = CanonicalPerson(
                name=name,
                role=match.group("role"),
                institution=normalize_space(match.group("institution")),
            )
    if roster:
        return roster

    team_file = proposal_dir / "03-team-qualification.tex"
    if team_file.exists():
        text = team_file.read_text(encoding="utf-8")
        for match in BOLD_ROLE_RE.finditer(text):
            name = normalize_name(match.group("name"))
            roster[name] = CanonicalPerson(name=name, role=match.group("role"), institution="")
    return roster


def collect_mentions(proposal_dir: Path) -> list[Mention]:
    mentions: list[Mention] = []
    seen: set[tuple[str, int, str, str]] = set()
    for path in sorted(proposal_dir.rglob("*.tex")):
        if path.name in IGNORE_FILENAMES:
            continue
        if "context" in path.parts or "guardrail" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        relative = str(path.relative_to(proposal_dir)).replace("\\", "/")
        for pattern, source in ((BOLD_ROLE_RE, "bold"), (PLAIN_ROLE_RE, "plain")):
            for match in pattern.finditer(text):
                item = (
                    relative,
                    line_number(text, match.start()),
                    match.group("role"),
                    normalize_name(match.group("name")),
                )
                if item in seen:
                    continue
                seen.add(item)
                mentions.append(
                    Mention(
                        file=item[0],
                        line=item[1],
                        role=item[2],
                        name=item[3],
                        source=source,
                    )
                )
    return mentions


def collect_team_profiles(
    proposal_dir: Path,
) -> tuple[dict[str, TeamProfile], list[dict[str, str]]]:
    team_dir = proposal_dir / "context" / "team"
    profiles: dict[str, TeamProfile] = {}
    issues: list[dict[str, str]] = []

    if not team_dir.exists():
        return profiles, issues

    for path in sorted(team_dir.glob("*/profile.md")):
        if path.parent.name == "_template":
            continue
        text = path.read_text(encoding="utf-8")
        relative = str(path.relative_to(proposal_dir)).replace("\\", "/")
        match = PROFILE_HEADING_RE.search(text)
        if not match:
            issues.append(
                {
                    "file": relative,
                    "issue": "missing top-level `# Name` heading",
                }
            )
            continue
        name = normalize_name(match.group("name"))
        if not name or name == "Name":
            issues.append(
                {
                    "file": relative,
                    "issue": "placeholder or empty profile name",
                }
            )
            continue
        if name in profiles:
            issues.append(
                {
                    "file": relative,
                    "issue": f"duplicate cleaned profile for `{name}`",
                }
            )
            continue
        profiles[name] = TeamProfile(file=relative, name=name)

    return profiles, issues


def check_institutions(
    proposal_dir: Path, roster: dict[str, CanonicalPerson]
) -> list[dict[str, str | int]]:
    findings: list[dict[str, str | int]] = []
    team_file = proposal_dir / "03-team-qualification.tex"
    if not team_file.exists():
        return findings

    text = team_file.read_text(encoding="utf-8")
    starts = list(BOLD_ROLE_RE.finditer(text))
    for index, match in enumerate(starts):
        name = normalize_name(match.group("name"))
        canonical = roster.get(name)
        if not canonical or not canonical.institution:
            continue
        block_start = match.end()
        block_end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[block_start:block_end]
        if normalize_institution(canonical.institution) not in normalize_space(block):
            findings.append(
                {
                    "file": "03-team-qualification.tex",
                    "line": line_number(text, match.start()),
                    "name": name,
                    "expected_institution": canonical.institution,
                }
            )
    return findings


def build_report(proposal_dir: Path) -> dict[str, object]:
    roster = load_canonical_roster(proposal_dir)
    mentions = collect_mentions(proposal_dir)
    team_profiles, profile_issues = collect_team_profiles(proposal_dir)

    role_mismatches = []
    unknown_mentions = []
    for mention in mentions:
        canonical = roster.get(mention.name)
        if canonical is None:
            unknown_mentions.append(asdict(mention))
            continue
        if canonical.role != mention.role:
            role_mismatches.append(
                {
                    **asdict(mention),
                    "expected_role": canonical.role,
                }
            )

    missing_team_profiles = []
    for canonical in roster.values():
        if canonical.name not in team_profiles:
            missing_team_profiles.append(
                {
                    "name": canonical.name,
                    "role": canonical.role,
                    "expected_profile_hint": (
                        f"context/team/{slugify_name(canonical.name)}/profile.md"
                    ),
                }
            )

    orphan_team_profiles = []
    for profile in team_profiles.values():
        if roster and profile.name not in roster:
            orphan_team_profiles.append(asdict(profile))

    return {
        "proposal_dir": str(proposal_dir),
        "canonical_roster": [asdict(person) for person in roster.values()],
        "role_mismatches": role_mismatches,
        "unknown_mentions": unknown_mentions,
        "missing_institutions_in_team_qualification": check_institutions(
            proposal_dir, roster
        ),
        "missing_team_profiles": missing_team_profiles,
        "orphan_team_profiles": orphan_team_profiles,
        "team_profile_issues": profile_issues,
    }


def render_markdown(report: dict[str, object]) -> str:
    lines = ["# Personnel Consistency Report", ""]

    roster = report["canonical_roster"]
    lines.append("## Canonical Roster")
    if roster:
        for person in roster:
            institution = f" | {person['institution']}" if person["institution"] else ""
            lines.append(f"- {person['name']} | {person['role']}{institution}")
    else:
        lines.append("- No canonical roster found.")
    lines.append("")

    role_mismatches = report["role_mismatches"]
    lines.append("## Role Mismatches")
    if role_mismatches:
        for item in role_mismatches:
            lines.append(
                f"- {item['file']}:{item['line']} | {item['name']} is labeled "
                f"`{item['role']}` but canonical role is `{item['expected_role']}`."
            )
    else:
        lines.append("- None found.")
    lines.append("")

    unknown_mentions = report["unknown_mentions"]
    lines.append("## Unknown Personnel Mentions")
    if unknown_mentions:
        for item in unknown_mentions:
            lines.append(
                f"- {item['file']}:{item['line']} | {item['name']} appears as "
                f"`{item['role']}` but is not in `30-collaborators.tex`."
            )
    else:
        lines.append("- None found.")
    lines.append("")

    missing_institutions = report["missing_institutions_in_team_qualification"]
    lines.append("## Team Qualification Institution Checks")
    if missing_institutions:
        for item in missing_institutions:
            lines.append(
                f"- {item['file']}:{item['line']} | {item['name']} does not mention the "
                f"expected institution `{item['expected_institution']}` nearby."
            )
    else:
        lines.append("- None found.")
    lines.append("")

    missing_profiles = report["missing_team_profiles"]
    lines.append("## Cleaned Team Profile Coverage")
    if missing_profiles:
        for item in missing_profiles:
            lines.append(
                f"- Missing cleaned profile for {item['name']} ({item['role']}); "
                f"expected something like `{item['expected_profile_hint']}`."
            )
    else:
        lines.append("- None missing from the canonical roster.")
    lines.append("")

    orphan_profiles = report["orphan_team_profiles"]
    lines.append("## Orphan Team Profiles")
    if orphan_profiles:
        for item in orphan_profiles:
            lines.append(
                f"- {item['file']} declares `{item['name']}` but that name is not in "
                f"`30-collaborators.tex`."
            )
    else:
        lines.append("- None found.")
    lines.append("")

    profile_issues = report["team_profile_issues"]
    lines.append("## Team Profile Format Issues")
    if profile_issues:
        for item in profile_issues:
            lines.append(f"- {item['file']} | {item['issue']}.")
    else:
        lines.append("- None found.")
    lines.append("")
    return "\n".join(lines)


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

    parser = argparse.ArgumentParser(
        description=(
            "Check PI/co-PI names, roles, and cleaned team-profile coverage for "
            "cross-file consistency."
        )
    )
    parser.add_argument(
        "--proposal-dir",
        help=(
            "Path to one proposal workspace. If omitted, the script will try to "
            "infer the current workspace."
        ),
    )
    parser.add_argument("--output-json", help="Optional path for JSON report output.")
    parser.add_argument("--output-md", help="Optional path for Markdown report output.")
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
    report = build_report(proposal_dir)

    if args.output_json:
        output_json = resolve_user_path(args.output_json, current_dir, repo_root)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    markdown = render_markdown(report)
    if args.output_md:
        output_md = resolve_user_path(args.output_md, current_dir, repo_root)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(markdown + "\n", encoding="utf-8")
    else:
        print(markdown)


if __name__ == "__main__":
    main()
