# Claude Code Tips & Tricks (Claude Max)

Compiled from official docs, blogs, and community sources. Tailored for a Claude Max subscriber using PyCharm terminal across Windows/macOS/Linux.

---

## 0. Platform Notes (Windows vs macOS vs Linux)

Most shortcuts use `Ctrl` and `Alt` on all platforms. Key differences:

| Action | Windows | macOS | Linux |
|--------|---------|-------|-------|
| Alt/Option key shortcuts (`Alt+T`, `Alt+P`, `Alt+B`, etc.) | `Alt` works directly | `Option` key, but **requires terminal config** (see below) | `Alt` works directly |
| Paste image from clipboard | `Alt+V` | `Ctrl+V` (or `Cmd+V` in iTerm2) | `Ctrl+V` |
| Multiline (native) | `\` + `Enter` everywhere | `Option+Enter` default; `Shift+Enter` in iTerm2/WezTerm/Ghostty/Kitty | `\` + `Enter` everywhere |
| Voice dictation | Needs WSL2 + WSLg (Win 11 only) | Works natively | Works natively |
| Open in browser (`Cmd+click`) | `Ctrl+click` | `Cmd+click` | `Ctrl+click` |

**macOS terminal setup for Option/Alt shortcuts:**
- **iTerm2**: Settings → Profiles → Keys → set Left/Right Option key to "Esc+"
- **Terminal.app**: Settings → Profiles → Keyboard → check "Use Option as Meta Key"
- **VS Code terminal**: same as iTerm2 setting
- Without this, `Option+T`, `Option+P`, `Option+B`, `Option+F`, etc. will not work

**PyCharm terminal notes:**
- `\` + `Enter` is the most reliable multiline method
- Image clipboard paste may not work; use file path instead (e.g., `@screenshot.png`)
- Run `/terminal-setup` to install `Shift+Enter` binding
- On macOS PyCharm, Alt/Option shortcuts may need additional configuration in PyCharm preferences

## 1. Keyboard Shortcuts

**Core:**

| Shortcut | What it does |
|----------|-------------|
| `Escape` | Stop Claude mid-action (context preserved) |
| `Esc` + `Esc` | Rewind/restore code and conversation to a checkpoint |
| `Shift+Tab` (twice) | Cycle permission modes (default → acceptEdits → plan → ...) |
| `Ctrl+C` | Cancel current input or generation |
| `Ctrl+D` | Exit Claude Code session |
| `?` | Show available shortcuts for your environment |

**Editing & Navigation:**

| Shortcut | What it does |
|----------|-------------|
| `Ctrl+G` | Open prompt in your system editor for complex multi-line |
| `Ctrl+K` | Delete to end of line (stored for paste) |
| `Ctrl+U` | Delete entire line (stored for paste) |
| `Ctrl+Y` | Paste deleted text |
| `Alt+Y` (after Ctrl+Y) | Cycle through paste history |
| `Alt+B` / `Alt+F` | Move cursor back/forward one word (macOS: `Option+B`/`Option+F`, needs Meta key configured) |
| `\` + `Enter` | Multiline input (works everywhere including PyCharm) |
| `Shift+Enter` | Multiline (native in iTerm2, WezTerm, Ghostty, Kitty; run `/terminal-setup` for others) |
| `Ctrl+J` | Line feed for multiline input |

**Toggles & Switching:**

| Shortcut | What it does |
|----------|-------------|
| `Alt+T` (macOS: `Option+T`) | Toggle extended thinking mode |
| `Alt+P` (macOS: `Option+P`) | Switch model without clearing prompt |
| `Ctrl+O` | Toggle verbose output (shows detailed tool usage) |
| `Ctrl+T` | Toggle task list display |
| `Ctrl+L` | Clear terminal screen (keeps conversation) |
| `Ctrl+R` | Reverse search through input history |
| `Ctrl+B` | Background a running command (press twice in tmux) |
| `Ctrl+F` | Kill all background agents (press twice within 3s to confirm) |
| `Left/Right arrows` | Cycle through tabs in permission dialogs |

**Custom keybindings:** edit `~/.claude/keybindings.json` or run `/keybindings`. Supports chord bindings (e.g., `ctrl+k ctrl+s`). Cannot rebind `Ctrl+C` and `Ctrl+D`.

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
- File-by-file descriptions

**Best practices:**
- Start small — document what Claude gets wrong, not everything
- Use emphasis (`IMPORTANT`, `YOU MUST`) for critical rules
- Use `@path/to/file` imports to modularize instructions
- Multiple CLAUDE.md files: `~/.claude/CLAUDE.md` (global), `./CLAUDE.md` (project), subdirectories (contextual)
- Treat it like code — review, prune, iterate

## 4. Workflow: Research → Plan → Execute → Review

1. **Explore** — Shift+Tab into Plan Mode, read files, understand the codebase
2. **Plan** — ask Claude for an implementation plan, refine it, use Ctrl+G to edit in your editor
3. **Implement** — switch to Normal Mode, let Claude code, run tests
4. **Commit & PR** — ask Claude to commit and create PR

**Skip planning** for one-line diffs (typos, log lines, renames).

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
- Great for security review, code review, research

## 7. Image & Rich Input

**Pasting images/screenshots into the terminal prompt:**

| Platform | Shortcut | Notes |
|----------|----------|-------|
| Windows  | `Alt+V`  | Not `Ctrl+V` |
| macOS    | `Ctrl+V` | Not `Cmd+V`; or `Cmd+V` in iTerm2 |
| Linux    | `Ctrl+V` | Standard |

- Supports PNG, JPG, and other common formats from clipboard
- You can also paste a file path to an image
- **PyCharm terminal**: clipboard image paste may not work. Use file path instead (`@screenshot.png` or absolute path)

**Other input methods:**
- **`@file`** — reference files directly instead of describing them
- **`! command`** — run bash commands directly, output goes into context
- **`cat file | claude`** — pipe data into Claude
- **`/copy`** — clean extraction of output
- **`--output-format json`** — structured output for automation

## 8. Parallel Work & Multi-Agent

- Run multiple Claude sessions in separate terminal tabs/panes
- **`--worktree`** — isolated git worktrees preventing agent interference
- **Writer/Reviewer pattern** — Session A implements, Session B reviews, Session A refines
- **Batch fan-out** — loop through file lists with `claude -p` for large migrations

## 9. Non-Interactive / CI Mode

```bash
claude -p "prompt"                              # one-shot
claude -p "prompt" --output-format json          # structured output
claude -p "prompt" --permission-mode auto         # autonomous
claude -p "prompt" --max-turns 10 --max-budget-usd 5.00  # safety limits
```

## 10. Effort Level

Controls how much reasoning Claude uses per response. Higher = more thorough but slower/costlier.

| Level | Use case | Persists? |
|-------|----------|-----------|
| Low | File renames, simple greps, quick questions | Yes |
| Medium | General coding, small refactors, reviewing files | Yes |
| High | Complex debugging, multi-file refactors, code review | Yes |
| Max | System design, deeply nested bugs, complex algorithms (Opus only) | No (resets on session end) |

**How to set:**
- **In session**: `/effort low` (or medium/high/max/auto)
- **CLI flag**: `claude --effort low`
- **Env var**: `export CLAUDE_CODE_EFFORT_LEVEL=low`
- **Settings**: `"effortLevel": "high"` in `settings.json`
- **In `/model` picker**: use left/right arrows to adjust the slider

Current indicator shows next to the spinner (e.g., "with low effort").

## 11. Cost & Performance Optimization

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
- **Use**: hold `Space` to record, release to stop
- **Mix input**: speak, release, type, hold Space again — all in one message
- **Zero cost**: transcription tokens are free and do not count against rate limits
- **20+ languages**: English, Chinese, Japanese, Korean, French, German, Spanish, etc.
- **Set language**: `/config` or `"language": "japanese"` in settings
- **Requires**: Claude.ai account (not API key), microphone access. On Windows needs WSL2 with WSLg (not available on Windows 10/WSL1)
- **Rebind key**: edit `~/.claude/keybindings.json`

## 14. Status Line

A customizable bar at the bottom showing context usage, model, git branch, costs, etc.

- **Quick setup**: `/statusline show model name and context percentage with a progress bar` — Claude generates the script
- **Manual**: create `~/.claude/statusline.sh`, add to settings:
  ```json
  { "statusLine": { "type": "command", "command": "~/.claude/statusline.sh" } }
  ```
- **Available data**: model name, context % used, cost in USD, session duration, git branch, rate limit usage, vim mode, agent name, and more
- **Supports**: ANSI colors, multi-line output, clickable OSC 8 links

## 15. Side Questions with /btw

Ask quick questions without polluting conversation history:
```
/btw what was the name of that config file again?
```
- Has full visibility into current conversation context
- Works while Claude is processing (non-blocking)
- No tool access — answers only from existing context
- Appears in dismissible overlay, never stored in history
- Dismiss with Space, Enter, or Escape

## 16. Model Switching

- **In session**: `/model` to open picker
- **Quick switch**: `Alt+P` (Windows/Linux) or `Option+P` (macOS) — no prompt clearing
- **CLI**: `claude --model opus`
- **Settings**: `"model": "opus"` in settings.json
- **Available**: `default`, `sonnet`, `opus`, `haiku`, `sonnet[1m]`, `opus[1m]` (1M context)

## 17. Quick Reference: All Slash Commands

**Session & Context:**

| Command              | Purpose                                                   |
|----------------------|-----------------------------------------------------------|
| `/context`           | Check token usage                                         |
| `/clear`             | Reset conversation                                        |
| `/compact`           | Summarize and free context                                |
| `/resume`            | Resume previous session                                   |
| `/fork`              | Branch a session                                          |
| `/rename`            | Name a session                                            |
| `/export [file]`     | Export conversation as plain text                         |
| `/cost`              | Show token usage statistics                               |
| `/stats`             | Visualize daily usage, session history, streaks           |
| `/usage`             | Show plan usage limits and rate limit status              |

**Configuration & Setup:**

| Command              | Purpose                                                   |
|----------------------|-----------------------------------------------------------|
| `/model`             | Switch model                                              |
| `/effort`            | Set effort level (low/medium/high/max/auto)               |
| `/fast [on/off]`     | Toggle fast mode                                          |
| `/vim`               | Enable vim keybindings                                    |
| `/theme`             | Change syntax highlighting theme                          |
| `/color [color]`     | Set prompt bar color for current session                  |
| `/config`            | Open general config                                       |
| `/permissions`       | Allowlist trusted commands                                |
| `/keybindings`       | Edit custom keybindings                                   |
| `/hooks`             | Browse configured hooks                                   |
| `/terminal-setup`    | Install Shift+Enter binding for your terminal             |
| `/statusline`        | Configure status line display                             |
| `/sandbox`           | Toggle OS-level sandbox mode                              |
| `/memory`            | Edit CLAUDE.md files, toggle auto-memory                  |
| `/privacy-settings`  | View/update privacy settings (Max only)                   |

**Tools & Integrations:**

| Command              | Purpose                                                   |
|----------------------|-----------------------------------------------------------|
| `/btw question`      | Side question without polluting context                   |
| `/diff`              | Open interactive diff viewer for uncommitted changes      |
| `/pr-comments [PR]`  | Fetch and display comments from a GitHub PR               |
| `/add-dir <path>`    | Add a working directory to the session                    |
| `/voice`             | Toggle voice dictation                                    |
| `/mcp`               | Manage MCP server connections                             |
| `/skills`            | List available skills                                     |
| `/agents`            | Manage agent configurations                               |
| `/tasks`             | List and manage background tasks                          |
| `/ide`               | Manage IDE integrations                                   |

**Account & Info:**

| Command              | Purpose                                                   |
|----------------------|-----------------------------------------------------------|
| `/login` / `/logout` | Sign in/out of Anthropic account                          |
| `/status`            | Show version, model, account, connectivity                |
| `/doctor`            | Diagnose issues with your setup                           |
| `/release-notes`     | View full changelog                                       |
| `/extra-usage`       | Configure extra usage when rate limits hit                 |
| `/upgrade`           | Open upgrade page                                         |
| `/help`              | Show help and available commands                          |

---

**Sources:** [Official Best Practices](https://code.claude.com/docs/en/best-practices), [Builder.io](https://www.builder.io/blog/claude-code), [Eesel](https://www.eesel.ai/blog/claude-code-best-practices), [YK 32 Tips](https://agenticcoding.substack.com/p/32-claude-code-tips-from-basics-to), [Trigger.dev](https://trigger.dev/blog/10-claude-code-tips-you-did-not-know), [ykdojo/claude-code-tips](https://github.com/ykdojo/claude-code-tips), [Ran the Builder](https://ranthebuilder.cloud/blog/claude-code-best-practices-lessons-from-real-projects/), [Sshh Blog](https://blog.sshh.io/p/how-i-use-every-claude-code-feature), [Official Workflows](https://code.claude.com/docs/en/common-workflows), [F22 Labs](https://www.f22labs.com/blogs/10-claude-code-productivity-tips-for-every-developer/)
