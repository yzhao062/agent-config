# Codex-primary symmetry implementation plan

**Status**: Draft plan for review.
**Driver**: make the role flip operational for two cases: Claude service outage or regional block, and deliberate reversal testing so the workflow does not depend on one agent.
**Scope**: implement the next three practical symmetry steps from the fungibility plan: a Codex-primary runbook, an `AGENTS.md` section for Codex-primary mode, and bootstrap support for `--primary codex`.
**Non-goals**: no pack handler split, no portable memory bridge, no rewrite of the pack composer, and no change to the default Claude-primary workflow.

## Current state

The shared principle already exists in `AGENTS.md` under `Agent Fungibility`. The review side is no longer theoretical: `dispatch-claude.{ps1,sh}` can run headless Claude Code as a reviewer, and `dispatch-copilot.{ps1,sh}` gives a third-agent fallback when Claude is absent. The remaining problem is the Codex-primary outer workflow. Today the pieces exist, but a Codex session does not get a first-class entry point that says what to read, what to run, what degrades, and how to hand work to Claude or Copilot for review.

This plan closes that gap without trying to make every Claude surface exist in Codex.

## Desired user flow

When Claude is down, restricted, or intentionally not primary, the maintainer can start Codex in a repo and use one fixed instruction:

```text
Run Codex-primary implement-review mode: read AGENTS.md, read skills/implement-review/SKILL.md using the 3-path lookup order, implement the requested change, then request reviewer feedback from Claude via dispatch-claude. If Claude is unavailable, use dispatch-copilot. Save reviewer output to Review-Claude-Code.md or Review-GitHub-Copilot.md, verify factual findings before applying, and iterate until no High findings remain.
```

The exact words can be shortened later, but the workflow must be documented enough that a fresh Codex session can follow it without Claude being available to explain the missing pieces.

## Phase 1 - Codex-primary runbook command

### Goal

Create a compact repo-local runbook that Codex can load directly when it is the primary agent.

### Files

- `docs/codex-primary.md` in `agent-config`
- mirrored public version in `anywhere-agents/docs/codex-primary.md`
- optional pointer from `README.md` or `docs/skills/index.md` in `anywhere-agents`, if the docs already have a natural place for it

### Implementation

1. Add `docs/codex-primary.md` with a single-page workflow:
   - prerequisites: Codex CLI configured, repo bootstrapped, `claude` optional for Claude reviewer, `copilot` or `gh copilot` optional for third-agent reviewer
   - skill lookup: `skills/<name>/SKILL.md`, then `.claude/skills/<name>/SKILL.md`, then `.agent-config/repo/skills/<name>/SKILL.md`
   - implementation loop: read task, inspect repo, make scoped edits, run tests, stage intended review target when review is requested
   - reviewer selection: Claude reviewer first when available; Copilot reviewer if Claude is absent; manual second pass if neither reviewer exists
   - review intake: read `Review-Claude-Code.md` or `Review-GitHub-Copilot.md`, categorize findings, verify factual findings before editing, then iterate
   - degradation list: no Claude slash command, no Claude SessionStart banner, no Claude PreToolUse hook mediation inside Codex
2. Include one copy-pasteable starter prompt for Codex-primary mode. Keep it under 25 lines.
3. Add a short "manual fallback" section for the worst case where no reviewer CLI is available: Codex writes `Review-Codex-Self-Audit.md` only as a labeled self-audit, not as an independent gatekeeper review.

### Tests and checks

- Add a doc test or grep-style unit test if the repo already has a docs assertion pattern; otherwise add `tests/test_codex_primary_docs.py`.
- Assert the runbook names the 3-path skill lookup order, both reviewer files, and the degradation list.
- In `anywhere-agents`, ensure the docs build still passes if documentation tests exist.

### Done when

A fresh Codex session can be told to read `docs/codex-primary.md` and complete an implement-review loop without relying on Claude slash-command context.

## Phase 2 - AGENTS.md Codex-primary section

### Goal

Put the mode switch in the always-loaded instructions, so every agent sees the same contract.

### Files

- `AGENTS.md`
- regenerated `CLAUDE.md`
- regenerated `agents/codex.md`
- mirrored and sanitized copies in `anywhere-agents`

### Implementation

1. Add a subsection after `Agent Fungibility` titled `When Codex Is Primary`.
2. Keep it short, about 20 to 30 lines.
3. Specify three modes:
   - normal mode: Claude implements, Codex reviews
   - reversal mode: Codex implements, Claude reviews through `dispatch-claude`
   - Codex-only mode: Codex implements, Copilot reviews if available; otherwise use a clearly labeled self-audit only as a temporary substitute
4. State the exact review file contract:
   - Claude reviewer writes `Review-Claude-Code.md`
   - Copilot reviewer writes `Review-GitHub-Copilot.md`
   - Codex self-audit, when unavoidable, writes `Review-Codex-Self-Audit.md` and must not be treated as an independent reviewer
5. Link to `docs/codex-primary.md` for full steps.
6. Regenerate agent files with the existing generator.

### Tests and checks

- Extend prompt byte parity tests if they cover generated files.
- Add assertions that generated `CLAUDE.md` and `agents/codex.md` contain the new heading.
- Run `scripts/check-parity.sh` after mirroring to `anywhere-agents`.

### Done when

Every bootstrapped consumer has enough always-loaded guidance to choose Codex-primary mode and knows which review backend to use.

## Phase 3 - Bootstrap `--primary codex`

### Goal

Make bootstrap heal Codex configuration as a first-class setup path while keeping the Claude-primary default unchanged.

### Files

- `bootstrap/bootstrap.sh`
- `bootstrap/bootstrap.ps1`
- tests for both scripts
- `docs/migrations.md` or equivalent install docs if they already document bootstrap flags
- `ONBOARDING.md` only if the maintainer workflow changes enough to need a pointer

### CLI contract

```bash
bash bootstrap.sh --primary codex
bash bootstrap.sh --primary codex --skip-claude-user-setup
```

PowerShell accepts the same logical flags:

```powershell
.\bootstrap.ps1 -Primary codex
.\bootstrap.ps1 -Primary codex -SkipClaudeUserSetup
```

### Semantics

- Default remains Claude-primary. Running bootstrap with no flags must produce the same Claude setup as before.
- `--primary codex` heals `~/.codex/config.toml` or `%USERPROFILE%\.codex\config.toml`:
  - `model = "gpt-5.5"`
  - `model_reasoning_effort = "xhigh"`
  - `service_tier = "fast"`
  - `[features] fast_mode = true`
- `--primary codex` does not skip Claude setup by itself. This supports reversal mode where Codex implements and Claude reviews.
- `--skip-claude-user-setup` is valid only with `--primary codex`.
- `--skip-claude-user-setup` with Claude-primary mode exits non-zero with a clear message.
- Bootstrap prints one line naming the active primary mode and any degraded features.

### Implementation

1. Add argument parsing in both bootstrap scripts without changing existing default behavior.
2. Add a small Codex config healer:
   - preserve unrelated keys in `config.toml`
   - update only the expected keys
   - create parent directory if missing
   - avoid rewriting the file when content is already current
3. Keep the existing Claude user setup path unchanged unless `--skip-claude-user-setup` is explicitly set in Codex-primary mode.
4. Add tests for:
   - default mode output equivalence against current Claude setup fixture
   - `--primary codex` writes or updates Codex config and still performs Claude setup
   - `--primary codex --skip-claude-user-setup` writes Codex config and leaves `~/.claude/` untouched
   - invalid skip flag combinations exit non-zero
   - existing Codex config with unrelated keys is preserved

### Done when

A new machine can be prepared for Codex-primary work with one bootstrap flag, and reversal mode still leaves Claude configured as a reviewer.

## Integrated validation

After Phases 1 to 3, run one end-to-end smoke in a scratch repo:

1. Bootstrap with Codex primary.
2. Start a Codex session and use the starter prompt from `docs/codex-primary.md`.
3. Make a one-line code or Markdown change.
4. Run the relevant local check.
5. Ask Claude reviewer through `dispatch-claude`; if unavailable, use `dispatch-copilot`.
6. Confirm the reviewer writes the expected `Review-*.md` file.
7. Confirm Codex reads the review, verifies factual findings, and applies one requested fix.
8. Confirm final status has no unintended files except expected review artifacts.

## Release sequence

1. Implement Phase 1 in `agent-config`, mirror public docs to `anywhere-agents`, and review.
2. Implement Phase 2, regenerate agent files, mirror, and run parity checks.
3. Implement Phase 3 in both bootstrap scripts with tests.
4. Run full local tests in both repos.
5. Run `scripts/check-parity.sh`.
6. Run the scratch Codex-primary smoke.
7. Update this followup with completion notes.

## Open questions for review

1. Should `docs/codex-primary.md` live under `docs/` or inside `skills/implement-review/references/`? I recommend `docs/` because this is an agent-mode runbook, not a review lens.
2. Should Codex-primary bootstrap update existing `approval_policy`? I recommend no. The user's Codex approval policy can be personal and environment-specific; this plan should only heal model, reasoning, tier, and fast mode.
3. Should self-audit output use `Review-Codex-Self-Audit.md` or no review file at all? I recommend the file, because it preserves the intake format while making the lack of independent review explicit.
