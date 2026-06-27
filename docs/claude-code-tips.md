# Claude Code Tips & Tricks (Claude Max)

Compiled from official docs, blogs, and community sources. Tailored for a Claude Max subscriber using PyCharm terminal across Windows/macOS/Linux.

> Source: https://code.claude.com/docs/en/interactive-mode
> Full docs index: https://code.claude.com/docs/llms.txt

**Related files:**
- [claude-code-reference.md](claude-code-reference.md) — keyboard shortcuts, slash commands, vim mode, command history
- [claude-code-extras.md](claude-code-extras.md) — buddy/companion, plugins

---

## 0. Platform Notes (Windows vs macOS vs Linux)

| Action | Windows | macOS | Linux |
|--------|---------|-------|-------|
| Alt/Option key shortcuts | `Alt` works directly | `Option` key (requires terminal config) | `Alt` works directly |
| Paste image from clipboard | `Alt+V` | `Ctrl+V` (or `Cmd+V` in iTerm2) | `Ctrl+V` |
| Multiline (native) | `\` + `Enter` | `Option+Enter` default; `Shift+Enter` in iTerm2/WezTerm/Ghostty/Kitty | `\` + `Enter` |
| Open in browser | `Ctrl+click` | `Cmd+click` | `Ctrl+click` |

**macOS terminal setup for Option/Alt shortcuts:**
- **iTerm2**: Settings → Profiles → Keys → set Left/Right Option key to "Esc+"
- **Terminal.app**: Settings → Profiles → Keyboard → check "Use Option as Meta Key"

**PyCharm terminal notes:**
- `\` + `Enter` is the most reliable multiline method
- Image clipboard paste may not work; use file path instead (e.g., `@screenshot.png`)
- Run `/terminal-setup` to install `Shift+Enter` binding

## 1. Keyboard Shortcuts (Summary)

| Shortcut | What it does |
|----------|-------------|
| `Escape` | Stop Claude mid-action |
| `Esc` + `Esc` | Rewind to checkpoint |
| `Shift+Tab` / `Alt+M` | Cycle permission modes |
| `Ctrl+G` / `Ctrl+X Ctrl+E` | Edit prompt in system editor |
| `Alt+T` | Toggle thinking mode |
| `Alt+P` | Switch model |
| `Ctrl+O` | Toggle verbose output |
| `Ctrl+R` | Reverse search history |
| `Ctrl+B` | Background a running command |
| `/` | Open command/skill menu |
| `!` | Bash mode |
| `@` | File path autocomplete |

Full tables: [claude-code-reference.md](claude-code-reference.md#keyboard-shortcuts)

## 2. Context Management (Critical)

- **`/context`** — check token usage periodically. You have ~200k tokens.
- **`/clear`** — reset between unrelated tasks. Context fills fast and performance decays.
- **`/compact Focus on X`** — summarize conversation while preserving key context.
- **`/resume` or `--resume`** — pick up from a previous session.
- **`/fork`** — duplicate a session to branch off independently.
- **`/rename`** — name sessions descriptively (e.g., "oauth-migration").
- **Esc+Esc → "Summarise from here"** — compress failed attempts into dense summaries.
- **Delegate research to subagents** — they explore in separate context windows and report back, keeping your main context clean.
- Write **handoff documents** before clearing state.

## 3. CLAUDE.md — Project Memory

The single most important configuration tool. Claude reads it automatically at conversation start.

**Include (< 200 lines):**
- Build/test/deploy commands Claude cannot guess
- Code style rules that differ from language defaults
- Architectural decisions, project structure overview
- Common gotchas, required env vars
- Branch naming, PR conventions

**Exclude:**
- Anything Claude can figure out by reading code
- Standard language conventions
- Long explanations or tutorials

**Best practices:**
- Start small — document what Claude gets wrong, not everything
- Use emphasis (`IMPORTANT`, `YOU MUST`) for critical rules
- Use `@path/to/file` imports to modularize instructions
- Multiple CLAUDE.md files: `~/.claude/CLAUDE.md` (global), `./CLAUDE.md` (project), subdirectories (contextual)

## 4. Workflow: Research → Plan → Execute → Review

1. **Explore** — Shift+Tab into Plan Mode, read files, understand the codebase
2. **Plan** — ask Claude for an implementation plan, refine it, use Ctrl+G to edit in your editor
3. **Implement** — switch to Normal Mode, let Claude code, run tests
4. **Commit & PR** — ask Claude to commit and create PR

Skip planning for one-line diffs (typos, log lines, renames).

## 5. Verification — Highest-Leverage Tip

Give Claude a way to check its own work:
- Write failing tests first, then implement
- Run tests after every change
- Paste screenshots for UI verification
- Include linter/type-checker commands in CLAUDE.md
- Use hooks to auto-run checks after edits

## 6. Configuration & Customization

**Hooks** (deterministic automation in `.claude/settings.json`):
- Run eslint after every file edit
- Block writes to protected directories
- Validate state before commits

**Skills** (`.claude/skills/` or `skills/`):
- Domain-specific knowledge and reusable workflows
- Load on-demand without bloating every conversation
- Invoke with `/skill-name`

**Custom commands** (`.claude/commands/*.md`):
- Reusable prompt templates as Markdown files
- Share with team via git

**Subagents** (`.claude/agents/*.md`):
- Specialized agents with own context and tool permissions

## 7. Image & Rich Input

| Platform | Image paste shortcut | Notes |
|----------|---------------------|-------|
| Windows  | `Alt+V`             | Not `Ctrl+V` |
| macOS    | `Ctrl+V`            | Not `Cmd+V`; or `Cmd+V` in iTerm2 |
| Linux    | `Ctrl+V`            | Standard |

PyCharm terminal: clipboard image paste may not work. Use file path instead (`@screenshot.png`).

Other input methods: `@file` (reference files), `! command` (bash mode), `cat file | claude` (pipe), `/copy` (clean extraction), `--output-format json` (structured output).

## 8. Parallel Work & Multi-Agent

- Run multiple Claude sessions in separate terminal tabs/panes
- **`--worktree`** — isolated git worktrees preventing agent interference
- **Writer/Reviewer pattern** — Session A implements, Session B reviews, Session A refines
- **Batch fan-out** — loop through file lists with `claude -p` for large migrations

## 9. Non-Interactive / CI Mode

```bash
claude -p "prompt"                                  # one-shot
claude -p "prompt" --output-format json              # structured output
claude -p "prompt" --permission-mode auto             # autonomous
claude -p "prompt" --max-turns 10 --max-budget-usd 5  # safety limits
```

## 10. Effort Level

| Level | Use case |
|-------|----------|
| Low | File renames, simple greps, quick questions |
| Medium | General coding, small refactors |
| High | Complex debugging, multi-file refactors |
| Xhigh | Heavy multi-file or design work below Max (persists to settings) |
| Max | System design, deeply nested bugs (Opus only, resets on session end) |

Set via: `/effort low|medium|high|xhigh` (persists to user settings), `/effort max` (session only, because `max` is not a valid persisted value), `claude --effort <level>` at launch (session only), `"effortLevel": "low|medium|high"` in `settings.json` for persisted low/medium/high, or the `CLAUDE_CODE_EFFORT_LEVEL` env var, which is the only way to persist `max` (for example, `"env": {"CLAUDE_CODE_EFFORT_LEVEL": "max"}` in `~/.claude/settings.json`). The env var outranks CLI and slash-command overrides. Left/right arrows in the `/model` picker also change the level.

## 11. Cost & Performance

- **Alt+T to disable thinking** on simple tasks — faster and cheaper
- **Use effort levels** — Low for boilerplate, Max for hardest problems
- **Batch similar requests** to minimize API overhead
- **Use subagents** for research instead of doing it in the main context
- **`/compact`** proactively to avoid auto-compaction

## 12. Git Workflow

- Allow `git pull` automatically, review `git push` manually
- Use `gh` CLI for issues, PRs, comments — Claude knows it well
- Draft PRs for low-risk iteration
- `--from-pr` to resume the session that created a PR

## 13. Voice Dictation

- **Enable**: `/voice` to toggle on/off
- **Use**: hold `Space` to record, release to stop. Speak, release, type, hold Space again — all in one message.
- **Zero cost**: transcription tokens are free
- **20+ languages**: set via `/config` or `"language": "japanese"` in settings
- **Requires**: Claude.ai account, microphone access. On Windows needs WSL2 with WSLg.

## 14. Status Line

A customizable bar at the bottom showing context usage, model, git branch, costs, etc.

- **Quick setup**: `/statusline show model name and context percentage with a progress bar`
- **Manual**: create `~/.claude/statusline.sh`, add to settings:
  ```json
  { "statusLine": { "type": "command", "command": "~/.claude/statusline.sh" } }
  ```
- **Available data**: model name, context % used, cost in USD, session duration, git branch, rate limit usage, vim mode, agent name

## 15. Side Questions with /btw

Ask quick questions without polluting conversation history:
```
/btw what was the name of that config file again?
```
- Full visibility into current conversation context, no tool access
- Works while Claude is processing (non-blocking), single response only
- Appears in dismissible overlay, never stored in history
- `/btw` is the inverse of a subagent: sees your full conversation but has no tools. A subagent has full tools but starts with empty context.

## 16. Model Switching

- **In session**: `/model` or `Alt+P`
- **CLI**: `claude --model opus`
- **Available**: `default`, `sonnet`, `opus`, `haiku`, `sonnet[1m]`, `opus[1m]` (1M context)

## 17. Background Tasks

Run bash commands in the background while continuing to work. Either prompt Claude to run a command in the background, or press `Ctrl+B` to move a running command to the background (press twice in tmux). Background tasks have unique IDs, output is buffered for retrieval, and tasks are cleaned up on exit.

## 18. Bash Mode with `!` Prefix

Run bash commands directly without Claude interpreting them: `! npm test`, `! git status`. Output goes into conversation context. Supports `Ctrl+B` backgrounding and Tab autocomplete from previous `!` commands.

## 19. Prompt Suggestions

After Claude responds, a grayed-out follow-up suggestion appears based on your conversation. Press **Tab** to accept or start typing to dismiss. Suggestions reuse the prompt cache so cost is minimal. Disable with `export CLAUDE_CODE_ENABLE_PROMPT_SUGGESTION=false`.

## 20. Task List

Press `Ctrl+T` to toggle the task list view showing pending/in-progress/complete tasks. Tasks persist across context compactions. Share across sessions with `CLAUDE_CODE_TASK_LIST_ID=my-project claude`.

## 21. PR Review Status

On branches with open PRs, a clickable PR link appears in the footer with colored underline: green (approved), yellow (pending), red (changes requested), gray (draft), purple (merged). Updates every 60 seconds. Requires `gh` CLI.

---

## See Also

- [claude-code-reference.md](claude-code-reference.md) — keyboard shortcuts, slash commands, vim mode
- [claude-code-extras.md](claude-code-extras.md) — buddy/companion, plugins
- Skills: https://code.claude.com/docs/en/skills
- Checkpointing: https://code.claude.com/docs/en/checkpointing
- CLI reference: https://code.claude.com/docs/en/cli-reference
- Settings: https://code.claude.com/docs/en/settings
- Memory management: https://code.claude.com/docs/en/memory

---

**Sources:** [Official Interactive Mode](https://code.claude.com/docs/en/interactive-mode), [Official Best Practices](https://code.claude.com/docs/en/best-practices), [Builder.io](https://www.builder.io/blog/claude-code), [Eesel](https://www.eesel.ai/blog/claude-code-best-practices), [YK 32 Tips](https://agenticcoding.substack.com/p/32-claude-code-tips-from-basics-to), [Trigger.dev](https://trigger.dev/blog/10-claude-code-tips-you-did-not-know), [ykdojo/claude-code-tips](https://github.com/ykdojo/claude-code-tips), [Ran the Builder](https://ranthebuilder.cloud/blog/claude-code-best-practices-lessons-from-real-projects/), [Sshh Blog](https://blog.sshh.io/p/how-i-use-every-claude-code-feature), [Official Workflows](https://code.claude.com/docs/en/common-workflows), [F22 Labs](https://www.f22labs.com/blogs/10-claude-code-productivity-tips-for-every-developer/)
