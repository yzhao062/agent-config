<!-- Round 1 -->
Intended file: `Review-Antigravity.md`

# Review: Omit absent Claude rate-limit windows

## Verification notes

All commands ran inside the disposable staged snapshot at `/private/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-ef72615a-round1-12580-433b1a9307e04ca0/staged-snapshot` using the project Python (`$HOME/miniforge3/envs/py312/bin/python`).

- `$HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_codex_usage.py -v`: exited 0; 61/61 tests passed (including all 5 new tests in `TestClaudeWindows`).
- `$HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_agent_quota_refresh.py tests/test_line_endings.py -v`: `test_agent_quota_refresh.py` passed 4/4; `test_line_endings.py` failed only because the disposable snapshot has no `.git` directory (`git ls-files` returned 0).
- Direct LF byte check on `scripts/agent-quota.py`, `scripts/statusline.py`, and `tests/test_codex_usage.py`: all three files have `CRLF=False`.
- `$HOME/miniforge3/envs/py312/bin/python -m unittest discover -s tests -v`: ran 1617 tests (173 skipped, 60 failures, all confined to snapshot-environment dependencies in `test_repo.py`, `test_line_endings.py`, `test_dispatch_gemini.py`, and `test_dispatch_task_agy.py`; zero failures in quota or statusline tests).
- Behavioral probe via Python against `scripts/statusline.py` and `scripts/agent-quota.py`:
  - `{"five_hour": {"used_percentage": 0}, "seven_day": {"used_percentage": 0}}` renders `cc 5h100% 7d100%`, `🤖 Opus 5.5 · 5h 100% · 7d 100%`, and `5h 100% left` / `7d 100% left`.
  - `{"five_hour": {"used_percentage": None, "resets_at": None}, "seven_day": {"used_percentage": 7}}` renders `cc 5h— 7d93%`, `🤖 Opus 5.5 · 5h — · 7d 93%`, and `5h —                     7d 93% left`.
  - `{"five_hour": {"used_percentage": None}, "seven_day": {"used_percentage": None}}` renders `cc 5h— 7d—` and `5h —                     7d —` instead of `cc —` and `(no windows)`.
- Old-code and mutation verification via Python against `TestClaudeWindows`:
  - Against the pre-diff `claude_segment` and `claude_row`: `test_absent_five_hour_is_left_out`, `test_absent_seven_day_is_left_out`, and `test_no_window_still_renders_a_placeholder` FAIL; `test_both_windows_keep_their_order_and_row_layout` and `test_zero_usage_keeps_its_meter` PASS.
  - Against a mutated `claude_segment` containing a falsy-zero filter bug (`if (rl.get(key) or {}).get(CLAUDE_PCT_FIELD)`): all 5 tests in `TestClaudeWindows` PASS, including `test_zero_usage_keeps_its_meter`.
- Web search verification: confirmed that Claude Code's `statusLine` stdin `rate_limits` schema carries `five_hour` and `seven_day` objects with `used_percentage` and `resets_at`, and that Anthropic removed the 5-hour session cap for verified Ultra accounts (leaving `five_hour` null or omitted, or its `used_percentage` null in unpopulated shapes).

Verification status: VERIFIED

## Scope and lens

- **Files changed (staged diff):** `scripts/agent-quota.py`, `scripts/statusline.py`, `tests/test_codex_usage.py`.
- **Review lens:** Code and documentation correctness, edge cases, behavior change for existing inputs, test effectiveness (failing on old code and catching regressions in new code), consistency across both scripts and neighboring code/docs, maintainability, and scope challenge.

## Findings

### New

#### High

1. **`test_zero_usage_keeps_its_meter` tests `1%` used instead of `0%` used and misses falsy-zero bugs** (`tests/test_codex_usage.py:1073-1083`)
   - The method is named `test_zero_usage_keeps_its_meter` and its docstring states `"A window at 0% used is present, so it must not be mistaken for an absent one."`, yet the input passes `{"used_percentage": 1}` and asserts `99%`.
   - Because `1` is truthy, this test fails to guard the exact boundary condition it describes. Verified empirically: mutating the new filter to `if (rl.get(key) or {}).get(CLAUDE_PCT_FIELD)` drops `0%`-used windows, and all 5 tests in `TestClaudeWindows` still pass.
   - Confirmed that the current production code renders `100%` for `{"used_percentage": 0}` in both readouts, so fixing the test makes it pass today while actually catching falsy-zero regressions.

   Exact rewrite (`tests/test_codex_usage.py:1073-1083`):
   ```python
       def test_zero_usage_keeps_its_meter(self):
           """A window at 0% used is present, so it must not be mistaken for an
           absent one."""
           rate_limits = {"five_hour": {"used_percentage": 0},
                          "seven_day": {"used_percentage": 0}}
           compact, full = self._segments(rate_limits)
           row = self._row(rate_limits)
           self.assertEqual(compact, "cc 5h100% 7d100%")
           self.assertEqual(full, "🤖 Opus 5.5 · 5h 100% · 7d 100%")
           self.assertIn("5h 100% left", row)
           self.assertIn("7d 100% left", row)
   ```

#### Medium

2. **Non-empty window dicts with `used_percentage: None` still render the broken dash (`5h—` / `5h —`)** (`scripts/statusline.py:253-257`, `scripts/agent-quota.py:585-589`)
   - Both scripts filter windows with `if rl.get(key)`. A non-empty dict such as `{"used_percentage": None, "resets_at": None}` or `{"used_percentage": None}` is truthy, so it passes the filter and enters `_fmt` / `fmt_window` / `fmt_window_compact`.
   - All three formatters immediately return `"—"` whenever `window.get(pct_field) is None` (ignoring `resets_at`), so that payload reproduces `cc 5h— 7d93%` and `5h —` (and `cc 5h— 7d—` instead of `cc —` / `(no windows)` if both windows have null percentages).
   - Tightening the predicate in both scripts to require a dict with a non-null percentage closes this shape without dropping `0%` used:
     - `scripts/statusline.py:253-257`:
       ```python
           windows = [
               (label, formatter(w, CLAUDE_PCT_FIELD))
               for label, key in CLAUDE_WINDOWS
               for w in (rl.get(key),)
               if isinstance(w, dict) and w.get(CLAUDE_PCT_FIELD) is not None
           ]
       ```
     - `scripts/agent-quota.py:585-589`:
       ```python
           segs = [
               f"{label} {_fmt(w, CLAUDE_PCT_FIELD):<20}"
               for label, key in CLAUDE_WINDOWS
               for w in (rl.get(key),)
               if isinstance(w, dict) and w.get(CLAUDE_PCT_FIELD) is not None
           ]
       ```
   - Pair this with a `{"five_hour": {"used_percentage": None, "resets_at": None}, "seven_day": self.WEEK}` case in `test_absent_five_hour_is_left_out` and a `{"five_hour": {"used_percentage": None}, "seven_day": {"used_percentage": None}}` case in `test_no_window_still_renders_a_placeholder`.

#### Low

3. **Docstring tier list stops at `Pro/Max` two lines before discussing `Ultra`** (`scripts/statusline.py:4-8`)
   - Line 5 reads `Pro/Max subscribers.` while line 7 adds `a verified Ultra account has no 5h limit`. Updating line 5 to `Pro/Max/Ultra subscribers.` keeps the opening paragraph consistent.

### Previously raised

None.

## Behavior-change and consistency notes

- **Existing two-window inputs:** Output is unchanged in both `statusline.py` (compact and full) and `agent-quota.py` (including the `:<20` column padding).
- **No-window inputs (API-key sessions / before first API response):** Compact statusLine changes from `cc 5h— 7d—` to `cc —`, full statusLine changes from `🤖 <model> · 5h — · 7d —` to `🤖 <model> · —`, and `agent-quota.py` changes from `5h —  7d —` to `(no windows)`. No repo caller parses the old dash string, and `(no windows)` matches `codex_row()` cleanly.
- **Cross-repo parity reminder:** All three changed files are listed in `scripts/check-parity.sh` as STRICT byte-identical mirrors with `anywhere-agents`; ensure the sync step mirrors all three once finalized.

## Scope-challenge focus

- **(a) Why this scope:** The change targets a concrete user pain on verified Ultra accounts, where an absent `five_hour` window rendered as `5h—` on every statusLine refresh and `agent-quota` run. A smaller scope (patching only `statusline.py`) would leave `agent-quota.py` displaying `5h —` from the same `~/.claude/rate-limits-cache.json` file. A marginally larger scope within these exact same lines (tightening the window predicate to reject `used_percentage: None`, Finding 2) closes the remaining unpopulated-window JSON shape for essentially zero extra cost. Extending the change to Agy (`agy_segment`/`agy_row`) is not warranted because Agy pools always provide both `5h` and `weekly` buckets.
- **(b) Out-of-scope / deferred items:** Nothing beyond the three changed files is deferred, and leaving shared-module extraction out of scope is the right call: `statusline.py` and `agent-quota.py` are deployed as standalone files to `~/.claude/` by `bootstrap.{sh,ps1}`, so extracting a shared helper would require installer and parity changes for no user benefit.
- **(c) Simplest path:** Yes. Iterating over `CLAUDE_WINDOWS` and filtering present windows matches `codex_segment`/`codex_row`, requires no cache schema changes, and automatically displays `5h` again if a plan restores it.

Commit verdict: BLOCK (fix Finding 1 in `tests/test_codex_usage.py:1073-1083` so the zero-usage test actually tests `0%`; strongly recommend folding in Finding 2 in the same pass).
