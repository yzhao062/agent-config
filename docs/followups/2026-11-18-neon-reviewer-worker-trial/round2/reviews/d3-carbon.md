<!-- Round 1 -->
Intended output file: `Review-Antigravity.md`

## Verification notes

All commands were executed from `/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-f09bbd5c-round1-12572-f7e766986df844f3/staged-snapshot` using `$HOME/miniforge3/envs/py312/bin/python`:

- `$HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_agent_models.py` -> exit `0` (`Ran 90 tests in 2.634s`, `OK (skipped=1)`).
- `$HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_dispatch_task_grok.py tests/test_dispatch_grok.py tests/test_prun_executors.py tests/test_style_audit.py tests/test_skill_md_contract.py tests/test_skill_size.py` -> exit `0` (`Ran 144 tests in 21.345s`, `OK (skipped=1)`).
- `$HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_check_parity.py tests/test_guard.py` -> exit `0` (`Ran 446 tests in 19.914s`, `OK`).
- `$HOME/miniforge3/envs/py312/bin/python scripts/agent_models.py scan skills/prun/references/grok-executor.md` -> exit `0` (no model or effort literals).
- `$HOME/miniforge3/envs/py312/bin/python -c '... subprocess.run([sys.executable, "scripts/guard.py"], ...) ...'` with a `Write` payload for `skills/prun/references/grok-executor.md` -> exit `0` (empty stdout and stderr; passes writing-style gate and advisory).
- `$HOME/miniforge3/envs/py312/bin/python -c 'import os, ntpath ... ntpath.expanduser("~/grok-home")'` -> exit `0` (`C:\Users\fake/grok-home`; confirms `USERPROFILE` takes precedence over `HOMEDRIVE`/`HOMEPATH` on Windows so the new test works cross-platform).

Verification status: VERIFIED

## Scope and review lens

- **Files reviewed (staged diff):** `scripts/agent_models.py`, `skills/prun/references/grok-executor.md`, `tests/test_agent_models.py` (cross-checked against `skills/prun/scripts/dispatch-task-grok.py`, `tests/test_dispatch_task_grok.py`, `skills/prun/SKILL.md`, and `skills/agent-models/SKILL.md`).
- **Lens:** Code and its documentation: correctness, edge cases, behavior change for existing inputs, test effectiveness (fails on old code and fails if new code breaks), consistency across the diff and neighboring code/docs, maintainability, and mandatory scope challenge.

## Findings

### New

1. **[High] `grok-executor.md` states that `GROK_DISPATCH_MODEL` alone waives a missing registry row, contradicting `dispatch-task-grok.py` and its tests** (`skills/prun/references/grok-executor.md:65`)
   - **Problem:** The updated paragraph adds: ``A missing registry row exits `70` and asks for the row, unless `GROK_DISPATCH_MODEL` is set, which waives it.`` In `skills/prun/scripts/dispatch-task-grok.py:899-903`, the dispatcher requires **both** `GROK_DISPATCH_MODEL` and `GROK_DISPATCH_EFFORT` to be non-empty before waiving a missing `grok` row (`both_overridden = bool(os.environ.get("GROK_DISPATCH_MODEL", "").strip()) and bool(os.environ.get("GROK_DISPATCH_EFFORT", "").strip())`), because lines `1015-1018` always pass `-m <model> --effort <effort>` to `grok`. `skills/prun/scripts/dispatch-task-grok.py:80` gives the same instruction (`or set both GROK_DISPATCH_MODEL and GROK_DISPATCH_EFFORT`), and `tests/test_dispatch_task_grok.py:663-672` explicitly verifies that setting `GROK_DISPATCH_MODEL` alone still exits `70`. Because `grok` is an optional family in `user/agent-models.json`, an operator or coordinator following this sentence on a checkout without `families.grok` will hit exit `70`.
   - **Exact rewrite (`skills/prun/references/grok-executor.md:65`):**
     ```markdown
     Because `XAI_API_KEY` matches `*KEY*`, it is scrubbed by default so `prun` units use the local OAuth login. To pass an API key intentionally to a worker, set `PRUN_KEEP_ENV=XAI_API_KEY`; `PRUN_KEEP_ENV` is a comma-separated, case-insensitive allowlist of any names, applied before the secret filter. Preflight checks the final child environment before launching `grok`. A non-empty `XAI_API_KEY` there skips the login file check; otherwise the login is `GROK_AUTH_PATH` when it is set, or `<GROK_HOME or ~/.grok>/auth.json`. A missing binary exits `127`. A missing registry row exits `70` and asks for the row, unless both `GROK_DISPATCH_MODEL` and `GROK_DISPATCH_EFFORT` are set, which waives it. A missing login exits `70` after `STATE-DIR`, writes `FALLBACK`, and tells the user to run `grok login` or pass `PRUN_KEEP_ENV=XAI_API_KEY`. An authentication or quota error during the run fails without retry or fallback to another backend.
     ```

2. **[Low] Sibling environment-variable path helpers in `scripts/agent_models.py` still omit `expanduser`** (`scripts/agent_models.py:81-83,249-263,758-761,798-802`)
   - **Problem:** `grok_home_path()` now expands a leading `~` in `GROK_HOME`, whereas the other four env-override path helpers in the same file (`registry_path()` for `AGENT_MODELS_FILE`, `codex_config_path()` for `CODEX_HOME`, `agy_settings_path()` for `ANTIGRAVITY_SETTINGS_FILE`, `claude_settings_path()` and `claude_actual()` for `CLAUDE_CONFIG_DIR`) still pass the raw stripped value directly to `Path(...)`. In this repository, environment overrides are commonly placed inside JSON `"env"` blocks (such as `~/.claude/settings.json`) where no shell expands `~`, which is how `GROK_HOME=~/.grok` reached `agent_models.py` unexpanded. Applying `os.path.expanduser` uniformly across those helpers in `scripts/agent_models.py` would prevent the identical literal-`~`-directory failure mode for the other three families.

3. **[Low] Minor residual precision gaps in `skills/prun/references/grok-executor.md` (`:23`, `:48`, `:69`, `:74`)**
   - `skills/prun/references/grok-executor.md:23`: says `An empty, unreadable, or malformed id exits 2`, omitting the case where neither `session-id` nor `conversation-id` exists in `<prev-state-dir>` (common when the prior unit failed before emitting a stream `sessionId`), which also exits `2` (`dispatch-task-grok.py:887-888`). Writing `A missing, empty, unreadable, or malformed id exits 2` covers all four pre-launch failures.
   - `skills/prun/references/grok-executor.md:48`: says `The dispatcher then exits 70, or with Grok's own status when grok itself exited non-zero.` When the stall or timeout reaper kills `grok`, `grok` exits non-zero from the signal while the dispatcher forces exit `124` (`dispatch-task-grok.py:1116-1118`); also, `dispatch-task-grok.py:1119-1122` fails the run on any `error` event even if a later `end_turn` event and exit `0` occur, so adding `no error event appears` to the first sentence makes the success rule self-contained.
   - `skills/prun/references/grok-executor.md:69,74`: line `69` writes `<GROK_HOME>/bin/grok` whereas lines `44`, `65`, and `78` write `<GROK_HOME or ~/.grok>/...` (`resolve_binary` uses `grok_home(source) / "bin"`, plus `grok.exe` on Windows, and treats whitespace-only `GROK_BIN` as unset); line `74` notes pre-launch exit `2` for invalid threshold or timeout values without mentioning that `GROK_KILL_GRACE_SECONDS` is validated in the same block (`dispatch-task-grok.py:934-938`) and exits `2` when non-positive or non-numeric.

4. **[Low] New tilde test exercises `grok_home_path()` directly without locking `grok_actual()`'s caller path** (`tests/test_agent_models.py:659-665`)
   - **Assessment:** `test_grok_home_expands_a_leading_tilde_like_the_dispatchers` fails on the old code (`Path("~/grok-home") != Path(tmp) / "grok-home"`) and fails if `os.path.expanduser` is removed from `grok_home_path()`. Adding one assertion in `test_grok_actual_reads_end_event_and_session_files_in_grok_home` with `HOME=tmp`, `USERPROFILE=tmp`, and `GROK_HOME="~/grok-home"` is optional, and would also catch a future edit in `grok_actual()` that reads `GROK_HOME` directly instead of calling `grok_home_path()`.

### Previously raised

None (Round 1).

## Scope challenge

- **(a) Why this scope, smaller vs. marginally larger:** Pairing the `grok_home_path()` tilde fix with the `grok-executor.md` corrections makes practical sense because both came out of exercising the Grok `prun` path and auditing its contract. A smaller scope (splitting a two-line bugfix and a doc correction into two separate review/CI/parity cycles) would only add process overhead. Conversely, a **marginally larger scope inside `scripts/agent_models.py` itself** would close the entire class of unexpanded-tilde bugs at near-zero cost: `registry_path()`, `codex_config_path()`, `agy_settings_path()`, `claude_settings_path()`, and `claude_actual()` live in the same already-staged file and suffer from the exact same `Path(os.environ.get(...))` defect whenever users configure paths with `~` in JSON `"env"` settings. Expanding `~` in those sibling helpers (plus one parametrized test in `tests/test_agent_models.py`) adds roughly 10 lines inside the two code files already touched and avoids repeating this bug per agent family.
- **(b) Deferred / out-of-scope items vs. process tax:** Nothing is explicitly marked deferred to vNext in the diff, and leaving `skills/prun/scripts/dispatch-task-grok.py` untouched is right because its `grok_home()`, `GROK_BIN`, and `GROK_AUTH_PATH` readers already call `os.path.expanduser`. Leaving the four sibling env-path helpers in `scripts/agent_models.py` unfixed is not worth a separate future plan, review, CI, and two-repo parity sync cycle compared to folding those four one-line `os.path.expanduser` calls in while touching `scripts/agent_models.py` and `tests/test_agent_models.py` anyway (or consciously keeping this diff strictly Grok-scoped if maintainer policy prefers).
- **(c) Simplest path:** Yes. Using `os.path.expanduser(home)` in `grok_home_path()` matches `dispatch-task-grok.py:182` verbatim without introducing a shared helper module across standalone scripts, and updating `grok-executor.md` in place keeps the reference concise (growing by only 6 net lines while fixing 20 discrepant claims, once Finding 1 is corrected).

Commit verdict: BLOCK
