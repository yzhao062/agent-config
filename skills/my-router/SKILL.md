---
name: my-router
description: Context-aware router that detects work type (papers, proposals, code, figures, admin) and dispatches to the right domain skill. Works within superpowers' execution phase as the inner decision loop.
---

# My Router

## Overview

A routing layer that sits between superpowers (outer workflow) and domain skills (inner execution). It reads the working directory, file types, and prompt to decide which skill to invoke. The user does not need to remember skill names; the router selects automatically.

## When to Use Superpowers vs. Direct Dispatch

The router decides this. Not all tasks need superpowers' full ceremony.

| Task shape | Route | Why |
|---|---|---|
| Clear, scoped task with an obvious skill match (e.g., "add citations", "review staged changes", "make a figure") | **Direct dispatch** — router picks the domain skill and runs it immediately | Brainstorming and planning add no value when the task is already well-defined |
| Open-ended, multi-step, or ambiguous task (e.g., "improve the proposal", "build a new feature", "restructure the related work") | **Superpowers first** — brainstorm → plan → execute (router dispatches during execute) → verify | These benefit from thinking before doing |
| Quick edit or fix (e.g., "fix the typo on line 42", "rename this variable") | **Neither** — just do it directly | No routing or workflow needed |

| Effort signal words in prompt (e.g., "extensively", "extensive", "deep", "thorough", "in-depth", "carefully", "comprehensive") | **Superpowers + extended thinking** — enable extended thinking (`Alt+T`) and route through superpowers regardless of task shape | The user is explicitly asking for more deliberation |

The rule: **if the domain skill is obvious and the scope is clear, skip superpowers and dispatch directly. If the task needs exploration or planning, let superpowers run the outer loop and the router dispatches during execution. If the user signals they want deep effort, always use superpowers with extended thinking enabled.**

## Integration with Superpowers

When superpowers is active, it handles workflow phases: brainstorm → plan → execute → verify. The router activates during the **execute** phase and dispatches to the right domain skill.

When superpowers is not active (direct dispatch or quick task), the router works standalone.

## How Routing Works

At dispatch time, the router checks three signals in order (keywords, file types, project structure). In a consuming repo, before applying the table below, it first merges any consumer-local routing extensions: a `routing-table.local.md` at the repo root, or a `## Routing` section in `AGENTS.local.md`. Those two files survive bootstrap, so they are where a consuming repo registers project-local skills that bootstrap would otherwise overwrite; on a keyword or file-type conflict, the local row wins.

### 1. Prompt keywords (highest priority)

The user's prompt often contains the clearest signal. Match keywords to skills:

| Keywords in prompt | Skill | Source |
|---|---|---|
| "cite", "citation", "bibliography", "bib", "references" | `bibref-filler` (or local variant like `nsf-bibref-filler` if available) | `skills/` (shared), check local first |
| "figure", "diagram", "illustration", "schematic", "overview figure" | `figure-prompt-builder` | `skills/` (shared) |
| "mockup", "HTML figure", "HTML mockup", "interactive figure", "dashboard mockup", "Gantt", "screenshotable figure", "capture mode", "skia-canvas", "TikZ figure", "arrow routing" | `ci-mockup-figure` | `skills/` (shared) |
| "review staged", "review changes", "review the diff" | `implement-review` | `skills/` (shared) |
| "two-pass", "first pass", "second pass", "audit" | `dual-pass-workflow` | `skills/` (shared) |
| "polish README", "modernize README", "README audit", "README rewrite", "README badges", "README hero", "GitHub README patterns" | `readme-polish` | `skills/` (shared) |
| "proposal", "nsf", "nih", "grant", "solicitation", "aim", "thrust" | Proposal skills (check for local `nsf-*`, `nih-*` skills first) | `reference-skills/` (project-local) |
| "review paper", "peer review", "reviewer comments" | `cs-paper-review` | `reference-skills/` (project-local) |
| "meta-review", "area chair", "AC decision" | `cs-meta-review` | `reference-skills/` (project-local) |
| "slides", "presentation", "beamer" | `paper-to-beamer` or `deck-assembler` | `reference-skills/` (project-local) |
| "cv", "curriculum vitae", "resume" | `condense-cv` | `reference-skills/` (project-local) |
| "reimbursement", "travel claim", "expense" | `usc-reimbursement` | `reference-skills/` (project-local) |

### 2. File types in working directory

If prompt keywords are ambiguous, inspect the files being worked on:

| Files present | Likely context | Default skill |
|---|---|---|
| `.tex` + `.bib` in a `paper/` or manuscript directory | Paper writing | `bibref-filler` for citations, `implement-review` (paper lens) for review |
| `.tex` + `.bib` in a `proposal/` or `nsf/` or `grant/` directory | Proposal writing | Proposal skills (check for local `nsf-*` or `nih-*` skills first), `implement-review` (ask user which agency lens) for review |
| `.py`, `.js`, `.ts`, or other code files | Code | Superpowers handles directly (brainstorm → plan → execute → verify) |
| `.md` slides or presentation files | Presentations | `paper-to-beamer` or `deck-assembler` |
| HTML mockups for system/dashboard figures | System figures | `ci-mockup-figure` |
| HTML mockups for general frontend/demos | Frontend | `frontend-design` plugin |
| `.md` in a proposal or grant directory | Proposal (Markdown-based) | Proposal skills (check for local skills first) |
| Staged git changes | Review needed | `implement-review` |

### 3. Project structure hints

Some projects declare their type in `AGENTS.local.md` or directory naming:

- Directory named `proposals/`, `nsf-*`, `nih-*` → proposal context
- Directory named `papers/`, `manuscript/`, `draft/` → paper context
- Submodule linked to Overleaf → shared paper/proposal, apply extra caution per submodule safety rules

## Dispatch Rules

1. **Local-first override** → before dispatching, scan `skills/` for any local skill that is a more specific variant of the matched skill (e.g., `nsf-bibref-filler` over shared `bibref-filler`, or `nsf-figure-builder` over shared `figure-prompt-builder`). If a local variant exists, use it instead.
2. **If a prompt keyword matches** → invoke that skill (after applying rule 1).
3. **If file context matches but prompt is vague** (e.g., "help me with this") → state the detected context and proposed skill, ask the user to confirm before proceeding.
4. **If multiple skills could apply** (e.g., "review this proposal" matches both `implement-review` and local proposal skills) → use `implement-review` as the outer loop and ask the user which agency lens to apply (NSF, NIH, etc.). Load any local proposal skills as supplementary criteria.
5. **If nothing matches** → fall through to superpowers or general Claude behavior. Do not force a skill where none fits.

## Skill Lookup Order

In consuming project repos, skills can be project-local, pack-deployed, or bootstrapped from shared config. When dispatching, look for each skill in this order:

1. `skills/<name>/SKILL.md`: project-local (highest priority). Projects may have their own custom skills here that are not in the shared config. The router should scan `skills/` for any available SKILL.md files, not just the ones listed in the routing table below.
2. `.claude/skills/<name>/SKILL.md`: pack-deployed by `anywhere-agents pack install`. The `.claude/` prefix is a historical Claude Code convention; the SKILL.md contents are agent-agnostic.
3. `.agent-config/repo/skills/<name>/SKILL.md`: bootstrapped from shared config.
4. **Installed plugins**: Claude Code plugins (e.g., `frontend-design`, `superpowers`, `pyright-lsp`) provide their own skills and capabilities. Check `/skills` output for plugin-provided skills alongside the three locations above. Plugin skills may overlap with custom skills; prefer the more specific one (e.g., a project-local `nsf-proposal-composer` over a generic plugin writing skill).

If a project-local skill matches the task better than a pack-deployed or bootstrapped skill, prefer the project-local one. The router itself follows this same lookup order: in the `agent-config` repo it lives at `skills/my-router/`; in other projects it lives at `.claude/skills/my-router/` or `.agent-config/repo/skills/my-router/`.

## Skill Availability

Skills come from three sources with different availability:

| Source | Available where | How |
|---|---|---|
| `skills/` (shared) | All projects | Copied by bootstrap into `.agent-config/repo/skills/` |
| Pack-deployed (third-party packs) | Projects that install the pack | `anywhere-agents pack install` writes into `.claude/skills/<name>/` |
| `reference-skills/` (domain) | Only projects that have them locally | Copied manually into `skills/` in the project repo |

Before invoking a reference skill, check that its `SKILL.md` exists in the current project (in `skills/`, `.claude/skills/`, or `.agent-config/repo/skills/`). If it does not exist, inform the user: "This task would use [skill name], but it is not available in this project. You can copy it from https://github.com/yzhao062/agent-config/tree/main/reference-skills/."

## Combining with Dual-Pass Workflow

For tasks that benefit from build-then-audit:

- **First pass**: router dispatches to the domain skill (e.g., `bibref-filler` adds citations)
- **Second pass**: router dispatches to `implement-review` or the domain skill's audit mode

The user can say "two-pass this" and the router will wrap the domain skill in `dual-pass-workflow` automatically.

## Combining with Implement-Review

When review is needed after domain skill execution:

1. Domain skill runs (e.g., proposal writing, citation filling)
2. Changes are staged
3. Router dispatches to `implement-review` with the appropriate lens (paper, proposal, or code)
4. Codex reviews using the lens-specific criteria

## Examples

**User says:** "Add citations to the related work section"
→ Router detects: keyword "citations" → checks for local variant (e.g., `nsf-bibref-filler`) → if found, uses it; otherwise falls back to shared `bibref-filler`

**User says:** "Review this"
→ Router detects: staged changes exist, `.tex` files in a proposal directory → `implement-review`, asks user which agency lens (NSF, NIH, etc.)

**User says:** "Make an overview figure for the proposal"
→ Router detects: keyword "figure" + "proposal" → checks for local `nsf-figure-builder` → if found, uses it; otherwise falls back to shared `figure-prompt-builder`

**User says:** "Help me improve this section"
→ Router detects: `.tex` in proposal directory, no specific keyword → asks user: "This looks like proposal work. Should I use local proposal skills, or is this general editing?"

**User says:** "Build the feature and review it"
→ Router detects: code context → superpowers handles the build, then router dispatches to `implement-review` with code lens
