# Routing Table — Quick Reference

## Shared Skills (available in all projects via bootstrap)

| Skill | Triggers on | What it does |
|---|---|---|
| `bibref-filler` | citation/bibliography work | Add verified citations to `working.bib`, keep curated bib files stable |
| `ci-mockup-figure` | HTML mockups, TikZ/skia-canvas figures, dashboards, Gantt charts | Build space-efficient figures via HTML capture or abstract figure toolchain |
| `figure-prompt-builder` | figure/diagram requests | Build copy-ready prompts for explanatory figures |
| `implement-review` | staged changes + review request | Multi-round review loop with Codex, content-aware lenses |
| `dual-pass-workflow` | multi-step build-then-audit tasks | First pass builds, second pass audits and reconciles |
| `my-router` | any task (this skill) | Detects context and dispatches to the right skill |
| `readme-polish` | README audit / rewrite / modernize | Apply modern 2025-2026 GitHub README patterns (centered header, badges, hero image, callouts, emoji feature bullets, collapsibles, Mermaid, tables) |

**Local-first rule:** If a project has a more specific local skill (e.g., `nsf-bibref-filler` alongside shared `bibref-filler`), always prefer the local version. Local skills are more customized for the project context.

## Reference Skills (project-local, must be copied from agent-config)

### Proposal Writing

| Skill | Triggers on | What it does |
|---|---|---|
| `nsf-proposal-composer` | NSF proposal drafting | Section blueprints, aim file configuration, edit boundaries |
| `nsf-thrust-refiner` | NSF thrust/aim polishing | Technical depth patterns, figure patterns, quality checklist |
| `nsf-proposal-guardrail` | NSF compliance checking | Solicitation parsing, template mapping, output schema |
| `nsf-figure-builder` | NSF-specific figures | Figure archetypes and tool selection for proposals |

### Paper and Review

| Skill | Triggers on | What it does |
|---|---|---|
| `cs-paper-review` | Peer review of CS papers | Venue-specific review criteria (NeurIPS, ICML, ACL, etc.) |
| `cs-meta-review` | Area chair decisions | Meta-review criteria across venues |

### Presentations

| Skill | Triggers on | What it does |
|---|---|---|
| `paper-to-beamer` | Converting paper to slides | Presenter mapping, engagement dynamics |
| `deck-assembler` | Building slide decks | Assembly patterns, continuity checks |
| `profile-intro-slides` | Intro/profile presentations | Slide recipes, quality checks, source selection |

### Administrative

| Skill | Triggers on | What it does |
|---|---|---|
| `condense-cv` | CV preparation | Selection guide for condensing academic CV |
| `usc-reimbursement` | Travel/expense claims | Process map, intake fields, policy gaps |

## Lens Selection for implement-review

When the router dispatches to `implement-review`, it also selects the review lens:

| Context | Lens | Criteria source |
|---|---|---|
| `.py`, `.js`, code files | Code | Google eng-practices, Microsoft Engineering Fundamentals |
| `.tex`/`.bib` in paper directory | Paper | NeurIPS, ICLR, ICML, ACL review guidelines |
| `.tex`/`.bib` in proposal directory | Proposal | Ask user which agency lens (NSF, NIH, etc.) |
| `.tex`/`.bib` in NIH-related directory | Proposal | NIH Simplified Peer Review Framework |
| Mixed or unclear | General | Completeness, correctness, consistency, clarity |
