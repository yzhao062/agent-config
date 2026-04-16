# agent-config

Personal shared configuration for Codex and Claude Code. Not intended for general use.

## Relationship with `anywhere-agents` (long-term co-maintenance)

This repo is the **private canonical source** of shared agent configuration. Its **sanitized public downstream** lives at [`yzhao062/anywhere-agents`](https://github.com/yzhao062/anywhere-agents) and ships the subset safe for general audiences — no USC content, no `reference-skills/`, no personal identifiers.

> The two repos co-evolve. Most meaningful changes to shared components (bootstrap, `implement-review`, `my-router`, guard hook, writing defaults, Git safety rules, session checks) should land here first, then be **backported** into `anywhere-agents` on the next public release cut. Skipping the backport lets the public release drift — users stop getting improvements that the author is already using daily.

Read before touching either repo:

- [`docs/anywhere-agents.md`](docs/anywhere-agents.md) — canonical source rule, "what gets copied" table, 11-step release workflow, package/asset ownership.
- [`docs/specs/open-source-framework.md`](docs/specs/open-source-framework.md) — the historical release plan plus the dated post-v1.0 update (npm/PyPI CLI policy).
- [`yzhao062/anywhere-agents/RELEASING.md`](https://github.com/yzhao062/anywhere-agents/blob/main/RELEASING.md) — the public-facing release steps (tag → build → publish to PyPI + npm → verify). Use this after the backport is staged.

**Every release of `anywhere-agents` is paired with a doc update here.** If you change the two-repo policy (what gets copied, canonical-source rule, release workflow), update `docs/anywhere-agents.md` in the same commit.

## What This Repo Does

Other project repos bootstrap from this repo to get shared agent defaults and skills. The bootstrap script (defined in `AGENTS.md`) fetches:

- **`AGENTS.md`** — user profile, writing/formatting defaults, environment notes, skill-sharing rules
- **`skills/`** — shared skills (e.g., `dual-pass-workflow`, `bibref-filler`)
- **`.claude/commands/`** — Claude Code pointer commands for shared skills
- **`.claude/settings.json`** — shared Claude project defaults (permissions, attribution, etc.)
- **`user/settings.json`** — shared user-level Claude defaults (permissions, hook wiring, `CLAUDE_CODE_EFFORT_LEVEL=max` env entry that pins effort to max)

## Adding to a Project

Paste the bootstrap block from `AGENTS.md` into the top of your project's `AGENTS.md`. The script will:

1. Download the latest `AGENTS.md` into `.agent-config/`.
2. Sparse-clone `skills/` and the shared `.claude/` files into `.agent-config/repo/`.
3. Copy shared commands into the project's `.claude/commands/` (non-destructive).
4. Merge shared keys into the project's `.claude/settings.json` on every run; project-only keys are preserved.
5. Auto-add `.agent-config/` to the project's `.gitignore`.

The copied block downloads the latest shared `bootstrap.ps1` or `bootstrap.sh`
at runtime. Those scripts refresh the consuming repo's root `AGENTS.md` to
match the shared copy. If a project later needs local overrides, put them in
`AGENTS.local.md`.

## Quick Start Prompt

After pasting the bootstrap block into the project's `AGENTS.md`, tell the agent:

```
阅读 AGENTS.md 并执行其中的 bootstrap 脚本。
```

## Validation

This repo includes zero-dependency validation tests for the bootstrap contract, skill layout, Claude/Codex wrappers, and temp-project smoke tests for the bootstrap flow.

Use any Python 3.12 interpreter to run them locally:

```bash
python -B -m unittest discover -s tests -p "test_*.py" -v
```

GitHub Actions runs the same test suite on Ubuntu and Windows for every push and pull request.

## Override Rules

- Project-local `AGENTS.md` rules override shared defaults.
- Project-local `skills/<name>/SKILL.md` overrides the shared copy of the same skill.

## Codex MCP Integration

Codex can be used from within Claude Code as an MCP server. See [AGENTS.md — Codex MCP Integration](AGENTS.md#codex-mcp-integration) for full setup instructions (registration, Windows path, approval policy, Bitdefender workarounds).

## Shared Skills

| Skill | Description |
|-------|-------------|
| `dual-pass-workflow` | Outer shell for two-pass tasks: first pass builds the artifact, optional second pass audits and reconciles. Works with any domain skill (paper review, bug fix, writing, frontend edit, etc.). |
| `bibref-filler` | Add new external verified citations while keeping curated bibliography files stable, placing machine-added entries in a separate `working.bib`, and leaving visible unresolved notes instead of guessing. |
| `figure-prompt-builder` | Build copy-ready prompts for explanatory figures such as overviews, workflows, mechanisms, timelines, and conceptual illustrations, using a small bundled reference bank when helpful. |
| `implement-review` | Review loop for staged changes. Detects content type, sends to Codex (terminal or plugin) for review using established frameworks (Google/Microsoft for code, NeurIPS/ACL for papers, NSF/NIH for proposals), categorizes feedback, revises, and iterates. |
| `ci-mockup-figure` | Build interactive HTML mockups of systems, methodological flowcharts, dashboards, and timelines, then capture as space-efficient figures for papers and proposals. |
| `my-router` | Context-aware dispatcher that detects work type (papers, proposals, code, figures, citations, admin) and routes to the right domain skill. Works as the inner decision loop within superpowers' execution phase. |
| `readme-polish` | Audit and rewrite a GitHub README using modern 2025-2026 patterns — centered header, badges, hero image, GitHub alert callouts, emoji feature bullets, collapsibles, Mermaid diagrams, tables over dense prose. Produces a README that survives a 10-second skim and a deep dive. |

## Skill Usage

After bootstrap, mention the skill name directly in the prompt. In Claude Code, the matching pointer command under `.claude/commands/` provides the same entry point. Each skill's `SKILL.md` contains full usage instructions and examples.

## Structure

```
AGENTS.md                          # Shared agent config (entry point)
bootstrap/
  bootstrap.ps1                    # Windows bootstrap logic
  bootstrap.sh                     # Unix bootstrap logic
skills/                            # Shared skills (bootstrapped to all projects)
  bibref-filler/
    SKILL.md                       # Skill definition
    agents/openai.yaml             # Codex wrapper
    assets/working.bib             # Starter template for machine-added entries
    references/citation-rules.md   # Density, placement, and storage guidance
    scripts/check_cite_keys.py     # Local cite-key validation helper
  ci-mockup-figure/
    SKILL.md                       # Skill definition
    agents/openai.yaml             # Codex wrapper
  dual-pass-workflow/
    SKILL.md                       # Skill definition (single source of truth)
    agents/openai.yaml             # Codex wrapper
    references/                    # contracts.md, task-mappings.md
    assets/                        # workflow.yaml, handoff.md, audit.md, reconcile.md
  figure-prompt-builder/
    SKILL.md                       # Skill definition
    agents/openai.yaml             # Codex wrapper
    assets/reference-bank/         # Portable donor figures bundled with the skill
    references/                    # figure-archetypes, reference-bank, prompt-design, tool-selection, external-handoff
    scripts/init_figure_spec.py    # Figure brief scaffold helper
  implement-review/
    SKILL.md                       # Skill definition
    agents/openai.yaml             # Codex wrapper
    references/review-lenses.md    # Framework-grounded review criteria (Google, NeurIPS, NSF, NIH)
  my-router/
    SKILL.md                       # Context-aware dispatcher for academic tasks
    agents/openai.yaml             # Codex wrapper
    references/routing-table.md    # Quick-reference routing table and lens selection
  readme-polish/
    SKILL.md                       # Audit + rewrite a GitHub README with modern patterns
    agents/openai.yaml             # Codex wrapper
    references/patterns.md         # Copyable snippets for every modern pattern
    references/checklist.md        # Pre-publish audit grid
reference-skills/                  # Domain skills (copied manually into project repos)
  condense-cv/                     # CV preparation
  cs-meta-review/                  # Area chair meta-review
  cs-paper-review/                 # Peer review of CS papers
  deck-assembler/                  # Slide deck assembly
  nsf-bibref-filler/               # NSF-specific citation filling
  nsf-figure-builder/              # NSF-specific figure building
  nsf-proposal-composer/           # NSF proposal section drafting
  nsf-proposal-guardrail/          # NSF compliance checking
  nsf-thrust-refiner/              # NSF thrust polishing
  paper-to-beamer/                 # Paper to Beamer slides
  profile-intro-slides/            # Intro/profile presentations
  usc-reimbursement/               # Travel/expense claims
figure-references/                 # Reusable reference figures organized by visual job
  index.md                         # Annotated index with role, density, and trait labels
scripts/
  guard.py                         # PreToolUse hook: blocks compound cd, gates destructive git/gh
user/
  settings.json                    # User-level Claude Code settings (permissions, hooks)
tests/                             # Validation tests (run in CI on Ubuntu and Windows)
  test_repo.py                     # Bootstrap contract, skill layout, smoke tests
  test_bibref_filler.py            # Cite-key validation script tests
  test_figure_prompt_builder.py    # Figure spec scaffold script tests
  test_guard.py                    # Guard hook tests
docs/
  claude-code-tips.md              # Workflows and best practices
  claude-code-reference.md         # Keyboard shortcuts, slash commands, vim mode
  claude-code-extras.md            # Buddy/companion, plugins
.claude/commands/                  # Claude Code pointer commands for shared skills
  bibref-filler.md
  ci-mockup-figure.md
  dual-pass-workflow.md
  figure-prompt-builder.md
  implement-review.md
  my-router.md
  readme-polish.md
.claude/settings.json              # Shared Claude project defaults (permissions, attribution, etc.)
user/settings.json                 # Shared user-level defaults (permissions, hooks, CLAUDE_CODE_EFFORT_LEVEL=max env entry)
```
