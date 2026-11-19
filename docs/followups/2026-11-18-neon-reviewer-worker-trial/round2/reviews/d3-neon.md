<!-- Round 1 -->

Intended file: `Review-Antigravity.md`

## Verification notes

All commands ran from `/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-570018b0-round1-12573-b71c61002949434b/staged-snapshot` using `$HOME/miniforge3/envs/py312/bin/python`:

- `$HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_agent_models.py -v`: exited `0` (90 tests run, 1 skipped, all passing, including `test_grok_home_expands_a_leading_tilde_like_the_dispatchers`).
- `$HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_dispatch_task_grok.py tests/test_dispatch_grok.py tests/test_prun_executors.py tests/test_style_audit.py tests/test_skill_md_contract.py tests/test_skill_size.py`: exited `0` (144 tests run, 1 skipped, all passing).
- `$HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_dispatch_task_grok.py tests/test_dispatch_grok.py tests/test_prun_executors.py tests/test_style_audit.py tests/test_repo.py tests/test_skill_md_contract.py tests/test_skill_size.py tests/test_line_endings.py`: 186 tests run, 10 failures solely in `test_repo.py` and `test_line_endings.py` where `git ls-files` fails with exit `128` because the disposable snapshot has no `.git` directory.
- `$HOME/miniforge3/envs/py312/bin/python scripts/agent_models.py scan scripts/agent_models.py skills/prun/references/grok-executor.md tests/test_agent_models.py`: `skills/prun/references/grok-executor.md` had zero hits (existing fixture/comment hits in `scripts/agent_models.py` and `tests/test_agent_models.py` only).
- Writing-style and formatting check via `scripts.guard.check_writing_style` and `scripts.guard.advise_writing_style` plus direct scan of `skills/prun/references/grok-executor.md`: exited `0`, no banned words, no `agent_style` findings, no em/en dashes, no `U+202F`, no CRLF, no contractions.
- Line-by-line cross-check of every claim in `skills/prun/references/grok-executor.md` against `skills/prun/scripts/dispatch-task-grok.py`, `scripts/agent_models.py`, and `tests/test_dispatch_task_grok.py`.

Verification status: VERIFIED

## Scope and Lens

- **Files changed**: `scripts/agent_models.py`, `skills/prun/references/grok-executor.md`, `tests/test_agent_models.py`.
- **Review lens**: Code and its documentation (correctness, edge cases, behavior change for existing inputs, test strength, internal and neighboring consistency, maintainability) plus mandatory scope challenge.

## Scope-challenge

- **(a) Why this exact scope**: The staged change pairs two outputs from a Grok `prun` verification pass: a one-line bug fix in `scripts/agent_models.py` (`grok_home_path()` expanding a leading `~`, plus test) that prevents false `MODEL-UNVERIFIED` reports under `GROK_HOME=~/.grok`, and a reconciliation of `skills/prun/references/grok-executor.md` against `skills/prun/scripts/dispatch-task-grok.py` and `scripts/agent_models.py`. A smaller scope would split a tiny fix and its doc cleanup into two review cycles for no benefit. A marginally larger scope inside `scripts/agent_models.py` itself is worth considering: five sibling env-var path lookups in the same file (`registry_path` / `AGENT_MODELS_FILE`, `codex_config_path` / `CODEX_HOME`, `agy_settings_path` / `ANTIGRAVITY_SETTINGS_FILE`, `claude_settings_path` / `CLAUDE_CONFIG_DIR`, and `claude_actual` / `CLAUDE_CONFIG_DIR`) still pass unexpanded values to `Path(...)` (while `scripts/merge_codex_hooks.py` already expands `CODEX_HOME`). Expanding `~` across all env-var path helpers in `scripts/agent_models.py` is roughly five lines plus one test and eliminates the same bug class across every family in that file at negligible risk (`os.path.expanduser` is a no-op when no leading `~` is present).
- **(b) Deferrals vs. process tax**: Keeping other repositories' docs and separate scripts (such as `scripts/render_banner.py`) out of this commit is reasonable. By contrast, leaving the sibling path helpers inside `scripts/agent_models.py` unexpanded is not worth a separate future bug report and review cycle when `scripts/agent_models.py` and `tests/test_agent_models.py` are already staged here.
- **(c) Simplest path**: Expanding `~` in `grok_home_path()` and updating `grok-executor.md` in place is the simplest shape. The code change and its test are clean and well-targeted (the test fails against the pre-change code and fails if either `expanduser` or `.strip()` regresses). However, the doc reconciliation introduced one direct factual error (High finding below) that contradicts both `dispatch-task-grok.py` and its unit test.

## Findings

### New

#### High

1. **`skills/prun/references/grok-executor.md:65` — Incorrect claim that `GROK_DISPATCH_MODEL` alone waives a missing registry row**
   - The edited paragraph states: *"A missing registry row exits `70` and asks for the row, unless `GROK_DISPATCH_MODEL` is set, which waives it."*
   - In `skills/prun/scripts/dispatch-task-grok.py:899-903`, waiving a missing registry row requires **both** `GROK_DISPATCH_MODEL` and `GROK_DISPATCH_EFFORT` to be set (non-empty):
     ```python
     both_overridden = bool(os.environ.get("GROK_DISPATCH_MODEL", "").strip()) and bool(
         os.environ.get("GROK_DISPATCH_EFFORT", "").strip()
     )
     if worker_row is None and not both_overridden:
         return fail(row_error, 70)
     ```
   - `skills/prun/scripts/dispatch-task-grok.py:80` gives the same instruction in its error message (`or set both GROK_DISPATCH_MODEL and GROK_DISPATCH_EFFORT`), and `tests/test_dispatch_task_grok.py:663-684` explicitly asserts that setting only `GROK_DISPATCH_MODEL` still exits `70` while setting both succeeds. An operator following the new doc sentence will still hit exit `70`.
   - Exact rewrite for `skills/prun/references/grok-executor.md:65`:
     ```markdown
     Because `XAI_API_KEY` matches `*KEY*`, it is scrubbed by default so `prun` units use the local OAuth login. To pass an API key intentionally to a worker, set `PRUN_KEEP_ENV=XAI_API_KEY`; `PRUN_KEEP_ENV` is a comma-separated, case-insensitive allowlist of any names, applied before the secret filter. Preflight checks the final child environment before launching `grok`. A non-empty `XAI_API_KEY` there skips the login file check; otherwise the login is `GROK_AUTH_PATH` when it is set, or `<GROK_HOME or ~/.grok>/auth.json`. A missing binary exits `127`. A missing registry row exits `70` and asks for the row, unless both `GROK_DISPATCH_MODEL` and `GROK_DISPATCH_EFFORT` are set, which waives it. A missing login exits `70` after `STATE-DIR`, writes `FALLBACK`, and tells the user to run `grok login` or pass `PRUN_KEEP_ENV=XAI_API_KEY`. An authentication or quota error during the run fails without retry or fallback to another backend.
     ```

#### Medium

2. **`skills/prun/references/grok-executor.md:48` — Exit-code summary omits the `124` reaper override**
   - Line 48 states: *"The dispatcher then exits `70`, or with Grok's own status when `grok` itself exited non-zero."*
   - In `skills/prun/scripts/dispatch-task-grok.py:1116-1118`, when the idle reaper or wall-clock limit kills `grok` (`timed_out_reason`), `grok` exits non-zero from the termination signal, yet the dispatcher overrides `exit_code` to `124` rather than returning `70` or Grok's own status.
   - Clarify line 48 (for example: *"The dispatcher then exits `124` on a stall or wall-clock kill, `70` when `grok` exited `0`, or with Grok's own status when `grok` itself exited non-zero."*) so line 48 agrees with lines 71–72.

#### Low

3. **`scripts/agent_models.py:81-83,249-263,760-761` — Sibling env-var path helpers do not expand leading `~`**
   - `grok_home_path()` now calls `os.path.expanduser(home)`, whereas `registry_path()` (`AGENT_MODELS_FILE`), `codex_config_path()` (`CODEX_HOME`), `agy_settings_path()` (`ANTIGRAVITY_SETTINGS_FILE`), `claude_settings_path()` (`CLAUDE_CONFIG_DIR`), and `claude_actual()` (`CLAUDE_CONFIG_DIR`) still construct `Path(...)` directly without `os.path.expanduser`.
   - Expanding `~` uniformly via a small helper in `scripts/agent_models.py` would keep all four families consistent with `grok_home_path()` and `scripts/merge_codex_hooks.py:158`.

4. **`skills/prun/references/grok-executor.md:69` — Minor notation inconsistency on `<GROK_HOME>/bin/grok`**
   - Line 69 writes `when it is unset, the lookup tries PATH and then <GROK_HOME>/bin/grok`, whereas lines 44, 65, and 78 write `<GROK_HOME or ~/.grok>` (and `resolve_binary()` in `dispatch-task-grok.py:204-209` uses `grok_home(source) / "bin"`, falling back to `~/.grok/bin/grok`, or `grok.exe` first on Windows, when `GROK_BIN` is unset or empty). Using `<GROK_HOME or ~/.grok>/bin/grok` keeps the document self-consistent.

### Previously raised

None.

## Verdict

Commit verdict: BLOCK (fix High finding #1 in `skills/prun/references/grok-executor.md:65` before committing).
