# Changelog

All notable changes to the shared agent configuration are documented here.
Consuming projects pull the latest on every bootstrap run; this log helps
track what changed between runs.

## 2026-04-29

### Changed
- Updated recommended Codex defaults from `gpt-5.4` to `gpt-5.5` to match the maintainer's shipped configuration.
- Added `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=80` to shared user settings so bootstrapped Claude Code sessions compact later while retaining a context buffer.

## 2026-04-11

### Changed
- Guard hook now shows randomized, attention-grabbing approval messages for destructive git/gh commands (e.g., "WHOA THERE COWBOY! git commit wants to run") to prevent accidental approvals.

## 2026-04-08

### Changed
- Removed MCP path from `implement-review` skill. Terminal copy-paste is now the default Codex channel on all platforms. Plugin path remains as an alternative.

## 2026-04-07

### Fixed
- Standardized all 6 command pointers to dual-path lookup format (`skills/` then `.agent-config/repo/skills/`) so they work in consuming repos.
- Added missing `ci-mockup-figure` to the routing table shared skills section.
- Removed duplicate `.agent-config/` entry from `.gitignore`.
- Fixed bootstrap `.gitignore` check to recognize both legacy `/.agent-config/` and current `.agent-config/` entries, preventing duplicate lines on upgrade.
- Removed `Bash(cat:*)` and `Bash(echo:*)` from shared settings allow list to align with AGENTS.md guidance (use Read/Write tools instead).

### Changed
- Moved `test_guard.py` from `scripts/` to `tests/` and converted from custom runner to unittest so CI discovers it.
- Expanded README Structure section to document all directories (`reference-skills/`, `figure-references/`, `scripts/`, `user/`, `tests/`, `docs/`).
- Moved `CodexReview.md` to `docs/` to reduce root-level clutter.

### Added
- Reference-skills validation tests (structural integrity, markdown link resolution, openai wrapper checks for all 12 reference skills).
- Bootstrap smoke tests now verify user-level files (`scripts/guard.py`, `user/settings.json`) exist in cloned repo.
- Strengthened sparse-checkout test assertion to check full `skills .claude scripts user`.
- Pointer validation test now verifies dual-path format and local-first ordering.

## 2026-04-06

### Added
- `ci-mockup-figure` skill: build interactive HTML mockups and abstract figures (TikZ, skia-canvas, Illustrator ExtendScript) for papers and proposals.
- Abstract figure toolchain section with tool comparison table, arrow routing guidance, and path-specific review criteria.

## 2026-04-05

### Added
- Overleaf merge conflict resolution rules in Submodule Workflow: never use `--theirs` on structurally changed files, inspect co-PI changes via merge-base diff, preserve co-PI content as priority.
- Pre-merge checklist for Overleaf-synced repos.
- Synced 12 reference-skills from NSF-Proposal-Template-Yue.

### Changed
- Polished implement-review skill based on real-session feedback (CodexReview.md root review sink, round history tracking, save instruction contract).

## 2026-04-04

### Added
- `my-router` skill: context-aware dispatcher that detects work type and routes to the right domain skill.
- Task Routing section in AGENTS.md with router integration rules.
- PreToolUse hook guard (`scripts/guard.py`): blocks compound cd commands, gates destructive git/gh operations.
- Bootstrap now deploys guard hook and merges user-level settings from `user/settings.json`.

## 2026-04-03

### Changed
- Split `claude-code-tips.md` into `docs/` directory with separate reference tables (`claude-code-reference.md`) and extras (`claude-code-extras.md`).

## 2026-04-02

### Added
- Shell Command Style rules: avoid compound `cd && cmd` chains, use `git -C` instead.
- Hardened submodule safety: fetch-before-write checks, detached-HEAD awareness, `.gitignore` internal-only file warnings.

### Changed
- Session start check now covers OS detection, Claude Code model/effort preference, and Codex config validation.

## 2026-04-01

### Added
- `implement-review` skill: multi-round review loop with Codex via MCP, terminal, or plugin paths. Content-aware lens selection (code, paper, proposal).
- Review lenses grounded in Google eng-practices, NeurIPS/ICLR/ACL guidelines, NSF Merit Review, and NIH Simplified Peer Review.
- 12 reference-skills for proposals, paper reviews, presentations, CV, and reimbursement.
- Recommended Codex defaults: `gpt-5.4`, `xhigh` effort, `fast` inference tier.

### Fixed
- Windows MCP registration: use bash-compatible path without `.cmd` extension.

## 2026-03-31

### Changed
- Tightened formatting rules: sentence-length limits, dash usage restrictions, varied sentence structure guidance.
- Fixed override-path conflict between `AGENTS.md` and `AGENTS.local.md`.

## 2026-03-26 -- 2026-03-28

### Added
- Submodule Workflow section: safety rules for shared repos, push/pull procedures, `.gitignore` internal-only file handling.
- Claude Code native installer note in Environment Notes.

### Fixed
- Disabled `core.autocrlf` globally in bootstrap to silence CRLF warnings on Windows.

## 2026-03-24

### Added
- Git Safety rule: never run `git commit` or `git push` without explicit user approval.
- Claude Code tips and tricks reference doc.

## 2026-03-22

### Added
- Deep merge for shared Claude settings: arrays of objects are replaced, arrays of strings are deduplicated, project-only keys are preserved.
- Broad shared permissions (web, pip, conda, file operations) in bootstrap.

## 2026-03-21

### Added
- `bibref-filler` skill: safe external citation filling with verification, `working.bib` separation, and visible TODOs.
- `figure-prompt-builder` skill: copy-ready prompts for explanatory figures with bundled reference bank.
- `dual-pass-workflow` skill generalized to support any domain skill as the inner executor.

## 2026-03-20

### Added
- Initial repo: `AGENTS.md` with user profile, writing defaults, formatting rules.
- Bootstrap scripts for PowerShell and bash.
- `dual-pass-workflow` skill (first version).
- CI validation tests on Ubuntu and Windows.
