# agent-config

Personal shared configuration for Codex and Claude Code. Not intended for general use.

## What This Repo Does

Other project repos bootstrap from this repo to get shared agent defaults and skills. The bootstrap script (defined in `AGENTS.md`) fetches:

- **`AGENTS.md`** — user profile, writing/formatting defaults, environment notes, skill-sharing rules
- **`skills/`** — shared skills (e.g., `dual-pass-workflow`)
- **`.claude/commands/`** — Claude Code pointer commands for shared skills

## Adding to a Project

Paste the bootstrap block from `AGENTS.md` into the top of your project's `AGENTS.md`. The script will:

1. Download the latest `AGENTS.md` into `.agent-config/`.
2. Sparse-clone `skills/` and `.claude/commands/` into `.agent-config/repo/`.
3. Copy shared commands into the project's `.claude/commands/` (non-destructive).
4. Auto-add `.agent-config/` to the project's `.gitignore`.

## Quick Start Prompt

After pasting the bootstrap block into the project's `AGENTS.md`, tell the agent:

```
阅读 AGENTS.md 并执行其中的 bootstrap 脚本。
```

## Override Rules

- Project-local `AGENTS.md` rules override shared defaults.
- Project-local `skills/<name>/SKILL.md` overrides the shared copy of the same skill.

## Shared Skills

| Skill | Description |
|-------|-------------|
| `dual-pass-workflow` | Outer shell for two-pass tasks: first pass builds the artifact, optional second pass audits and reconciles. Works with any domain skill (paper review, bug fix, writing, frontend edit, etc.). |

## Structure

```
AGENTS.md                          # Shared agent config (entry point)
skills/
  dual-pass-workflow/
    SKILL.md                       # Skill definition (single source of truth)
    agents/openai.yaml             # Codex wrapper
    references/
      contracts.md                 # Task packet and handoff/audit contracts
      task-mappings.md             # Audit emphasis per task type
    assets/
      workflow.yaml                # Task packet template
      handoff.md, audit.md, reconcile.md  # Workflow note templates
.claude/commands/
  dual-pass-workflow.md            # Claude Code pointer to SKILL.md
```
