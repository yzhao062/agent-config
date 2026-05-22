# Copilot Auto Reviewer Probe

Local test session: 2026-05-21, Windows PowerShell.

Purpose: record the probe results that informed the GitHub Copilot CLI reviewer
path for `implement-review`. **Status: implemented (2026-05-21)** -- the recommended
backend now ships as `dispatch-copilot.{ps1,sh}`, `tests/test_dispatch_copilot.py`,
and SKILL.md > "Auto-terminal Copilot backend". This file is retained as the design
and probe record, not as a description of pending work.

## Target Use Case

When Claude Code is unavailable, Codex can act as the main terminal worker while
GitHub Copilot CLI acts as the reviewer in an auto mode. The useful contract is
not "Codex only"; it is:

- main agent prepares the existing `implement-review` prompt;
- reviewer runs non-interactively;
- reviewer writes `Review-<AgentName>.md` at the repo root;
- existing watcher, intake, health check, and categorization logic process that
  file.

For Copilot, the stable review file name should be
`Review-GitHub-Copilot.md`.

## Observed Local Tools

- `gh --version`: GitHub CLI 2.88.1.
- `gh auth status`: logged into `github.com` as `yzhao062`.
- `gh copilot --help`: built-in Copilot CLI entry is available through `gh`.
- `copilot --help`: standalone Copilot CLI is available.
- `copilot version`: GitHub Copilot CLI 1.0.51, reported as latest.
- `where.exe copilot`: resolved to the WinGet-installed `copilot.exe`.

Both entry points worked:

```powershell
copilot -p "Return exactly: COPILOT_SMOKE_OK" --allow-all-tools --no-ask-user --silent --stream off --no-color
gh copilot -p "Return exactly: GH_COPILOT_SMOKE_OK" --allow-all-tools --no-ask-user --silent --stream off --no-color
```

Both returned the requested smoke token without an interactive prompt.

## Key CLI Behavior

Useful non-interactive flags:

- `-p` / `--prompt <text>` runs one prompt and exits.
- `--no-ask-user` prevents Copilot from asking the user questions.
- `--silent` keeps output script-friendly.
- `--stream off` makes output less noisy.
- `--no-color` avoids ANSI output in captured tails.
- `--allow-tool=write` allows file writes.
- `--allow-tool=read` allows file reads.
- `--allow-tool='shell(git:*)'` allows git commands.
- `--add-dir <repo>` grants file access to the target repo.
- `-C <repo>` changes the working directory before the run.

Important prompt-file result:

- `--attachment <prompt.md>` does not work for text or Markdown prompts. Copilot
  rejected a `.md` attachment with: `--attachment file type not supported`.
- `-p "@<prompt-file>"` does work. Copilot treated the referenced text file as
  the prompt content and followed it.

This means a Copilot dispatch script should keep the current prompt-file model,
but invoke Copilot with `-p "@<prompt-file>"` rather than trying to pass the full
prompt as one long command-line string.

## Probe Results

### Real repo read-only review (random/access-hpc)

Follow-up live probe: 2026-05-22, `C:\Users\yuezh\PycharmProjects\random`,
staged `access-hpc` resource-selection docs and helper script changes.

Two review modes were tried:

1. **Embedded diff only.** This is safer, but weak. The reviewer sees hunks but
   cannot inspect adjacent source files. It is useful as a fallback when tools
   are blocked, but it is not the preferred Copilot path.
2. **Read-only repo inspection.** This produced a more useful review. Copilot
   was allowed to run read-only git commands and denied write/edit tools:

   ```powershell
   copilot -p $prompt --silent --no-ask-user `
     --allow-tool='shell(git diff:*)' `
     --allow-tool='shell(git status:*)' `
     --allow-tool='shell(git show:*)' `
     --allow-tool='shell(git grep:*)' `
     --allow-tool='shell(git ls-files:*)' `
     --allow-tool='shell(git log:*)' `
     --allow-tool='shell(git check-ignore:*)' `
     --deny-tool=write `
     --deny-tool=edit
   ```

Result: Copilot produced a substantive review in about 275 seconds. It found a
real low-severity issue that pure diff review would likely miss:
`hpc_status.py` hardcoded `yzhao13` while neighboring `psc.py` already exposed
`psc.USER`. The fix was to use `psc.USER` in both the visible queue label and
the `squeue -u` command. This is a good example of a context-dependent review
finding that needs read access to nearby files.

The run also showed a pager issue: Copilot first reported that the staged diff
was truncated by the pager, then recovered by reading files directly. A dispatch
adapter should avoid this by forcing no-pager behavior, for example with
`git --no-pager diff --cached` in the prompt and/or `GIT_PAGER=cat` in the
subprocess environment.

Important command-length observation: passing a long embedded diff through a
single `-p "<prompt>"` argument failed quickly with exit code 1 and no useful
output. A small `copilot -p "Say ok"` prompt worked. This reinforces the earlier
finding: real dispatch should use `-p "@<prompt-file>"`, not a large literal
prompt argument.

Safer write contract option: Copilot does not need write permission to be useful
as a reviewer. The caller can deny write/edit tools, capture stdout, and save it
to `Review-GitHub-Copilot.md` itself. This avoids granting the reviewer file
write access while still letting Phase 2 ingest the normal review file. If the
existing watcher path is reused directly, write access may still be needed, but
stdout-capture is the safer adapter design.

### File write contract

In a temp directory, Copilot was asked to create `Review-GitHub-Copilot.md` with
the first line `<!-- Round 1 -->`. It wrote the file successfully.

### Staged-diff review

In a temp git repo, the staged file was:

```python
def add(a, b):
    return a - b
```

Prompt: inspect only the staged diff and write `Review-GitHub-Copilot.md`.

Result: Copilot wrote a review file, cited `sample.py` line 2, and correctly
identified that `add()` subtracts instead of adding.

### Prompt-file review

In a second temp git repo, the prompt was saved to a text file and invoked with
`-p "@<prompt-file>"`. The staged file was:

```python
def multiply(a, b):
    return a + b
```

Result: Copilot wrote `Review-GitHub-Copilot.md`, started with
`<!-- Round 1 -->`, included `Verification notes`, cited `calc.py` line 2, and
correctly identified that `multiply()` adds instead of multiplying.

### Watcher compatibility

Existing watcher command shape worked with the Copilot review name:

```powershell
.\skills\implement-review\scripts\auto-watch.ps1 <temp>\Review-*.md 1 GitHub-Copilot
```

It emitted:

```text
WATCH-START round=1 reviewers=GitHub-Copilot timeout=25s
DONE <temp>\Review-GitHub-Copilot.md
```

### Health-check compatibility

Existing `health-check.ps1` accepted a Copilot review file when passed through
`--review-file`:

```powershell
.\skills\implement-review\scripts\health-check.ps1 --state-dir <state> --round 1 --review-file <temp>\Review-GitHub-Copilot.md --lens code
```

Observed passes:

- review file exists;
- freshness;
- round marker;
- size;
- `Verification notes`;
- suspicious phrases;
- dispatch tail markers;
- stall warning absence;
- substance checks for non-plan-review code lens.

## Recommended Minimal Implementation

Add a Copilot-specific dispatch adapter, not a rewrite of the review loop:

- `skills/implement-review/scripts/dispatch-copilot.ps1`
- `skills/implement-review/scripts/dispatch-copilot.sh`

The adapter should mirror the `dispatch-codex` contract where possible:

- accepts `--prompt-file`, `--round`, and `--expected-review-file`;
- creates a state dir under temp;
- records `pre-mtime`, `timestamp`, and `tail`;
- prints `STATE-DIR <abs-path>` as the first machine-readable stdout line;
- runs Copilot non-interactively;
- returns Copilot exit code;
- writes stdout and stderr to `tail`;
- expects `Review-GitHub-Copilot.md`.

Suggested PowerShell command shape:

```powershell
copilot -C <repo> -p "@<prompt-file>" `
  --add-dir <repo> `
  --allow-tool='shell(git:*)' `
  --allow-tool=read `
  --allow-tool=write `
  --no-ask-user `
  --silent `
  --stream off `
  --no-color
```

Fallback if `copilot` is not on PATH:

```powershell
gh copilot -C <repo> -p "@<prompt-file>" <same flags>
```

Test both entry points because this machine has both.

## Skill Routing Suggestion

Keep current Codex behavior intact. Add explicit Copilot triggers, for example:

- `/implement-review auto copilot`
- `/implement-review copilot auto`
- `use copilot as reviewer`
- role reversal wording where Codex is the implementer and Copilot is the
  reviewer

Do not change plain `/implement-review auto` until the user explicitly wants
Copilot to become the default reviewer. Today, `auto` maps to Codex auto-terminal.

## Test Suggestions

Add tests parallel to `tests/test_dispatch_codex.py`, but with a mock Copilot
stub:

- script presence for `.ps1` and `.sh`;
- argument validation;
- prompt-file missing;
- round validation;
- state dir naming, likely `implement-review-copilot-...`;
- `pre-mtime`, `timestamp`, and `tail` creation;
- stdout first line is `STATE-DIR`;
- `copilot` receives `-p @<prompt-file>`;
- no long prompt is passed as a literal command-line argument;
- expected review file can be `Review-GitHub-Copilot.md`;
- non-zero Copilot exit is propagated;
- fallback to `gh copilot` when standalone `copilot` is missing.

Existing tests for `auto-watch` and `health-check` may only need small coverage
for the `GitHub-Copilot` reviewer name, because both scripts already worked in
manual probes.

## Risk Notes

- `--allow-all-tools` works, but a narrower allow list is safer and sufficient
  for review: `read`, `write`, and `shell(git:*)`.
- Copilot can modify files. The prompt must say review-only and name
  `Review-GitHub-Copilot.md` as the only allowed write target.
- Copilot may emit tables or symbols in terminal output. Capturing with
  `--no-color --silent --stream off` kept output usable in tests.
- The text attachment path is a trap. Use `-p "@<prompt-file>"`.
