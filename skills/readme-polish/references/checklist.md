# README Audit Checklist

Run this grid against a candidate README before editing. Mark each row `✓` (present and correct), `✗` (absent or broken), or `N/A` (does not apply to this project).

## First-paint (above the fold)

| Item | Notes |
|------|-------|
| Centered project name in `<div align="center">` | Modern OSS convention; left-align is the old style. |
| One-line tagline directly under the name | Under 15 words. Survives without context. |
| Badge row (4-6 badges) | PyPI, npm, license, CI status, stars. Not more. |
| Dot-separated nav links | Optional but helpful on READMEs over 100 lines. |
| Hero image, diagram, or screenshot | At least one visual above the elevator pitch. |
| Maintainer credibility as `> [!NOTE]` callout, not paragraph | Keep to 2-3 sentences, verifiable claims only. |
| Elevator pitch paragraph (1-3 sentences) | What the project is, who it is for. |

## Install section

| Item | Notes |
|------|-------|
| Primary install command visible without scrolling | The single most important line. |
| Platform-specific variants collapsed in `<details>` | Do not show all three OSes above the fold. |
| Prerequisites listed (or explicitly none) | Reader should know if they need Python, Node, Docker, etc. |
| Example invocation right after install | "Run this to verify it works." |
| Direct-from-agent phrasing (if applicable) | `> [!TIP]` callout: "tell your agent to install it." |

## What you get / Features

| Item | Notes |
|------|-------|
| 5-8 emoji-prefixed one-liner bullets | Each bullet = emoji + bold name + em-dash + takeaway. |
| No multi-sentence prose bullets | If a feature needs more than one sentence, link to a follow-up section or collapsible. |
| No overlap between feature bullets and hero image content | If the hero image already shows the 6 features, either cut the bullets or make them much shorter. |

## Reference material (should be collapsed)

| Item | Should be in `<details>`? |
|------|----------------------------|
| Platform-specific install variants | Yes |
| Repo layout / file tree | Yes |
| Related projects / alternatives | Yes |
| Limitations and caveats | Yes |
| Maintenance policy | Yes |
| "What this is not" | Yes |
| FAQ | Yes |
| Detailed configuration options | Depends — if only a power-user concern, collapse. |
| Quickstart | No, never collapse. |
| What you get / features | No, never collapse. |

## Callout discipline

| Item | Notes |
|------|-------|
| `> [!NOTE]` used for maintainer callout only | One per major section max. |
| `> [!TIP]` used only for "agent-install" or "pro tip" moments | Optional. |
| `> [!WARNING]` / `[!CAUTION]` reserved for genuine hazards | Breaking changes, destructive operations. Not decorative. |
| First source line is exactly `> [!TYPE]` (one `>`, one tag, alone) | Any extra prefix or missing `>` breaks the callout. |

## Anchor and link hygiene

| Item | Notes |
|------|-------|
| Every dot-nav link resolves to a real heading | GitHub autogenerates anchors from headings. Verify manually. |
| No markdown links to files that do not exist | `[CONTRIBUTING](CONTRIBUTING.md)` requires the file. |
| External links use HTTPS | Mixed-content issues on HTTPS pages otherwise. |
| Image alt text is descriptive | Not just "hero" or "logo". |
| Badge URLs use correct registry / package names | Shield.io is case-sensitive for package names. |

## Render verification

| Item | Notes |
|------|-------|
| Pushed to a branch and viewed on GitHub | PyCharm / VS Code previews miss `> [!NOTE]` and Mermaid. |
| `> [!NOTE]` renders as a colored box (not a plain blockquote) | If it looks like a quote, the syntax is wrong. |
| Mermaid diagrams render (not as raw text) | If raw text, the fence language is wrong or renderer disabled. |
| Hero image loads (not a broken-image icon) | Relative path must be correct from repo root. |
| Badges show live data (not "image not found") | Shield.io URL must be well-formed. |
| Collapsibles expand cleanly | No content leaks outside the `<details>` tag. |

## Hygiene

| Item | Notes |
|------|-------|
| `git diff --cached --check` passes | No trailing whitespace. |
| Tables are GitHub-flavored (pipes, not grid format) | Grid format does not render. |
| Code blocks have language hints (` ```bash `, ` ```python `) | Syntax highlighting only fires with hints. |
| Line lengths reasonable (under ~120 chars for prose) | Long lines are fine in code blocks. |

## Content accuracy (cannot be linted)

| Item | Notes |
|------|-------|
| Every version number mentioned matches the current release | Package version, minimum versions, release-date claims. |
| Every feature claim matches what the code actually does | A README promising X must correspond to shipped X. |
| Every install command has been tested on a clean machine | Fresh-machine test before shipping. |
| No personal identifiers leaked in public README | Usernames, paths, institutional affiliations that should not be public. |

## When to stop

A modern README does not need to check every box above. Focus on:

1. First-paint (above-the-fold) correctness — non-negotiable.
2. Install path clarity — non-negotiable.
3. Feature scannability — at least emoji-prefixed bullets or a table.
4. At least one collapsible for reference material.
5. Verified rendering on GitHub.

Everything else is polish. Stop polishing when the reader's first-minute experience is strong.
