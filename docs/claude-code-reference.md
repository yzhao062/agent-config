# Claude Code Reference Tables

Lookup tables for keyboard shortcuts, slash commands, vim mode, and command history. See [claude-code-tips.md](claude-code-tips.md) for workflows and best practices.

---

## Keyboard Shortcuts

**Core:**

| Shortcut | What it does |
|----------|-------------|
| `Escape` | Stop Claude mid-action (context preserved) |
| `Esc` + `Esc` | Rewind/restore code and conversation to a checkpoint |
| `Shift+Tab` or `Alt+M` | Cycle permission modes (default → acceptEdits → plan → ...) |
| `Ctrl+C` | Cancel current input or generation |
| `Ctrl+D` | Exit Claude Code session |
| `Up/Down arrows` | Navigate command history (recall previous inputs) |
| `?` | Show available shortcuts for your environment |

**Editing & Navigation:**

| Shortcut | What it does |
|----------|-------------|
| `Ctrl+G` or `Ctrl+X Ctrl+E` | Open prompt in your system editor for complex multi-line |
| `Ctrl+K` | Delete to end of line (stored for paste) |
| `Ctrl+U` | Delete to start of line (stored for paste; repeated use clears across lines in multiline input) |
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
| `Ctrl+O` | Toggle verbose output (shows detailed tool usage; also expands MCP read/search calls that collapse to a single line like "Queried slack" by default) |
| `Ctrl+T` | Toggle task list display |
| `Ctrl+L` | Redraw terminal screen (keeps conversation) |
| `Ctrl+R` | Reverse search through input history |
| `Ctrl+B` | Background a running command (press twice in tmux) |
| `Ctrl+X Ctrl+K` | Kill all background agents (press twice within 3s to confirm) |
| `Left/Right arrows` | Cycle through tabs in permission dialogs |

**Theme/display (inside `/theme` picker only):**

| Shortcut | What it does |
|----------|-------------|
| `Ctrl+T` | Toggle syntax highlighting for code blocks (only in `/theme` picker menu; only available in native build) |

**Quick commands:**

| Shortcut | What it does |
|----------|-------------|
| `/` at start | Open command/skill menu |
| `!` at start | Bash mode — run commands directly, output goes into context |
| `@` | Trigger file path autocomplete |

**Custom keybindings:** edit `~/.claude/keybindings.json` or run `/keybindings`. Supports chord bindings (e.g., `ctrl+k ctrl+s`). Cannot rebind `Ctrl+C` and `Ctrl+D`.

---

## Slash Commands

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
| `/effort`            | Set effort level (low/medium/high/xhigh/max)              |
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
| `/privacy-settings`  | View/update privacy settings (Pro and Max)                |

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
| `/plugin`            | Open plugin manager                                       |
| `/reload-plugins`    | Apply plugin changes without restarting                   |

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

## Vim Mode

Enable vim-style editing with `/vim` command or configure permanently via `/config`.

**Mode switching:**

| Command | Action | From mode |
|---------|--------|-----------|
| `Esc` | Enter NORMAL mode | INSERT |
| `i` | Insert before cursor | NORMAL |
| `I` | Insert at beginning of line | NORMAL |
| `a` | Insert after cursor | NORMAL |
| `A` | Insert at end of line | NORMAL |
| `o` | Open line below | NORMAL |
| `O` | Open line above | NORMAL |

**Navigation (NORMAL mode):**

| Command | Action |
|---------|--------|
| `h`/`j`/`k`/`l` | Move left/down/up/right |
| `w` | Next word |
| `e` | End of word |
| `b` | Previous word |
| `0` | Beginning of line |
| `$` | End of line |
| `^` | First non-blank character |
| `gg` | Beginning of input |
| `G` | End of input |
| `f{char}` | Jump to next occurrence of character |
| `F{char}` | Jump to previous occurrence of character |
| `t{char}` | Jump to just before next occurrence of character |
| `T{char}` | Jump to just after previous occurrence of character |
| `;` | Repeat last f/F/t/T motion |
| `,` | Repeat last f/F/t/T motion in reverse |

In vim normal mode, if the cursor is at the beginning or end of input and cannot move further, the arrow keys navigate command history instead.

**Editing (NORMAL mode):**

| Command | Action |
|---------|--------|
| `x` | Delete character |
| `dd` | Delete line |
| `D` | Delete to end of line |
| `dw`/`de`/`db` | Delete word/to end/back |
| `cc` | Change line |
| `C` | Change to end of line |
| `cw`/`ce`/`cb` | Change word/to end/back |
| `yy`/`Y` | Yank (copy) line |
| `yw`/`ye`/`yb` | Yank word/to end/back |
| `p` | Paste after cursor |
| `P` | Paste before cursor |
| `>>` | Indent line |
| `<<` | Dedent line |
| `J` | Join lines |
| `.` | Repeat last change |

**Text objects (NORMAL mode):**

Text objects work with operators like `d`, `c`, and `y`:

| Command | Action |
|---------|--------|
| `iw`/`aw` | Inner/around word |
| `iW`/`aW` | Inner/around WORD (whitespace-delimited) |
| `i"`/`a"` | Inner/around double quotes |
| `i'`/`a'` | Inner/around single quotes |
| `i(`/`a(` | Inner/around parentheses |
| `i[`/`a[` | Inner/around brackets |
| `i{`/`a{` | Inner/around braces |

---

## Command History & Search

- Input history is stored per working directory
- Input history resets when you run `/clear`. The previous session's conversation is preserved and can be resumed.
- Use Up/Down arrows to navigate
- History expansion (`!`) is disabled by default

**Reverse search with Ctrl+R:**

1. **Start search**: press `Ctrl+R` to activate reverse history search
2. **Type query**: enter text to search for in previous commands. The search term is highlighted in matching results
3. **Navigate matches**: press `Ctrl+R` again to cycle through older matches
4. **Accept match**:
   - Press `Tab` or `Esc` to accept the current match and continue editing
   - Press `Enter` to accept and execute the command immediately
5. **Cancel search**:
   - Press `Ctrl+C` to cancel and restore your original input
   - Press `Backspace` on empty search to cancel
