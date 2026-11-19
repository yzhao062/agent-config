<!-- Round 1 -->
Intended output file: `Review-Antigravity.md`

## Verification notes

All repository commands were executed in `/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-7f911768-round1-12574-fea53ed1d3fe4e75/staged-snapshot` using `$HOME/miniforge3/envs/py312/bin/python`.

1. `$HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_codex_usage.py tests/test_agent_quota_refresh.py -v` -> Exit 0 (`Ran 65 tests in 0.419s`, `OK`, including all 5 new tests in `TestClaudeWindows`).
2. `$HOME/miniforge3/envs/py312/bin/python -m unittest discover -s tests -v` -> Exit 1 (`Ran 1617 tests in 161.086s`, `failures=60, skipped=173`). Inspected every failure via `grep "^FAIL:\|^ERROR:"`: all 60 failures occur in `test_dispatch_gemini`, `test_dispatch_task_agy`, `test_line_endings`, and `test_repo` solely because the disposable staged snapshot omits `.git` (`fatal: not a git repository`). Every non-git test across the repository passed.
3. `$HOME/miniforge3/envs/py312/bin/python -c '... claude_segment ...'` on `{"used_percentage": 0}` and `{"used_percentage": 100}` -> Exit 0; confirmed runtime outputs `cc 5h100% 7d0%` (compact) and `🤖 Opus 5.5 · 5h 100% · 7d 100%` (full).
4. `$HOME/miniforge3/envs/py312/bin/python -c '... persist_claude ...'` writing `{"seven_day": {"used_percentage": 7}}` followed by `{"five_hour": None, "seven_day": None}` -> Exit 0; reproduced `persist_claude` overwriting `CLAUDE_RL_CACHE` so `agent_quota.claude_row()` changed from `Claude   Opus 5.5      7d 93% left              [just now]` to `Claude   Opus 5.5      (no windows)  [just now]`.
5. `$HOME/miniforge3/envs/py312/bin/python -c '...'` multi-row visual check across `claude_row()`, `codex_row()`, and `agy_row()` with a `seven_day`-only Claude cache -> Exit 0; confirmed column alignment between single-window Claude (`7d 93% left (resets 3d11h)  [just now]`) and single-window Codex (`7d 87% left (resets 4d15h)  [2m ago]`).
6. `$HOME/miniforge3/envs/py312/bin/python -c '...'` binary check on `scripts/agent-quota.py`, `scripts/statusline.py`, and `tests/test_codex_usage.py` -> Exit 0; confirmed LF line endings and a single trailing newline in all three files, and `grep -rn "5h—\|7d—\|5h —\|7d —" .` found no remaining references expecting the old dash layout.
7. External verification via web search: confirmed that Anthropic renamed the $200/month Max 20x tier to Claude Ultra and removed the 5-hour session cap for verified Ultra accounts while keeping the weekly (`seven_day`) cap; confirmed Claude Code `statusLine` stdin injects `rate_limits` (`five_hour`, `seven_day` with `used_percentage` and `resets_at`) after the first API response on subscription plans and drops expired windows once `resets_at` passes.

Verification status: VERIFIED

## Scope and lens

- **Files changed:** `scripts/agent-quota.py`, `scripts/statusline.py`, `tests/test_codex_usage.py`
- **Lens:** Code and documentation correctness, edge cases, behavior change for existing inputs, test effectiveness (whether new tests fail on old code and catch regressions in new code), internal and neighboring consistency, maintainability, and scope challenge.

## Findings

### New

1. **[Medium] `test_zero_usage_keeps_its_meter` passes `used_percentage: 1` instead of `0`, leaving the `0%`-used boundary untested** (`tests/test_codex_usage.py:1073-1084`)
   The method name and docstring state that a window at `0%` used must remain visible, yet lines 1076-1077 supply `{"used_percentage": 1}` (`99%` remaining). Because `1` is truthy in Python while `0` is falsy, this test passes even if window filtering regresses to a truthiness check on `used_percentage` (for example, `if (rl.get(key) or {}).get(CLAUDE_PCT_FIELD):`), which would silently drop a `0%`-used meter. Testing `0` on one window and `100` (`0%` remaining) on the other pins both falsy-zero boundaries at once.

   Suggested update (`tests/test_codex_usage.py:1073-1084`):
   ```python
       def test_zero_usage_keeps_its_meter(self):
           """A window at 0% used (or 0% left) is present, so it must not be
           mistaken for an absent one."""
           rate_limits = {"five_hour": {"used_percentage": 0},
                          "seven_day": {"used_percentage": 100}}
           compact, full = self._segments(rate_limits)
           row = self._row(rate_limits)
           self.assertEqual(compact, "cc 5h100% 7d0%")
           self.assertEqual(full, "🤖 Opus 5.5 · 5h 100% · 7d 0%")
           self.assertIn("5h 100% left", row)
           self.assertIn("7d 0% left", row)
   ```

2. **[Medium] `persist_claude` and window filtering check dict truthiness rather than usable `used_percentage`, allowing all-null `rate_limits` to clobber the disk cache** (`scripts/statusline.py:234-236`, `scripts/statusline.py:253-257`, `scripts/agent-quota.py:585-589`)
   `TestClaudeWindows.test_no_window_still_renders_a_placeholder` (`tests/test_codex_usage.py:1096`) treats `{"five_hour": None, "seven_day": None}` as an expected no-window payload alongside `{}` and `None`. In `claude_segment`, all three render `cc —`. In `persist_claude` (`scripts/statusline.py:234-236`), however, `if not rl: return` skips `{}` and `None` (preserving the last valid cached quota on disk) while treating `{"five_hour": None, "seven_day": None}` as truthy and overwriting `~/.claude/rate-limits-cache.json` with a windowless entry, turning `agent_quota.claude_row()` from `7d 93% left` into `(no windows)`. For the same reason, gating windows on `if rl.get(key)` still renders `cc 5h— 7d93%` and `5h —` whenever a window arrives as a non-empty dict with a null percentage (`{"used_percentage": None, "resets_at": None}`). Checking `isinstance(w, dict) and w.get(CLAUDE_PCT_FIELD) is not None` in both scripts and requiring at least one present window in `persist_claude` keeps cache persistence and both renderers aligned.

   Suggested update (`scripts/statusline.py:234-262` and matching filter in `scripts/agent-quota.py:585-589`):
   ```python
   def _has_claude_window(window):
       return isinstance(window, dict) and window.get(CLAUDE_PCT_FIELD) is not None
   ```
   Then in `persist_claude`:
   ```python
       rl = data.get("rate_limits")
       if not isinstance(rl, dict) or not any(
           _has_claude_window(rl.get(key)) for _, key in CLAUDE_WINDOWS
       ):
           return
   ```
   And in `claude_segment` / `claude_row`, replace `if rl.get(key)` with `if _has_claude_window(rl.get(key))`.

### Previously raised

None.

## Behavior and test assessment

- **Existing dual-window inputs:** Output is unchanged across `statusline.claude_segment` (compact and full) and `agent_quota.claude_row` (including the 20-character column width and two-space join).
- **Absent single window (`five_hour` or `seven_day` missing, `None`, or `{}`):** Omitted cleanly in both readouts (`cc 7d93%`, `🤖 Opus 5.5 · 7d 93%`, `Claude   Opus 5.5      7d 93% left ...`). If `five_hour` reappears (such as an unverified account or plan change), `CLAUDE_WINDOWS` restores it in `5h` then `7d` order without code changes.
- **No windows present:** Changed intentionally from `cc 5h— 7d—` / `5h — ... 7d —` to `cc —` / `🤖 <model> · —` / `(no windows)` (matching `codex_row()`'s `(no windows)` wording at `scripts/agent-quota.py:616`). No tests or callers in the repository depended on the old double-dash strings.
- **Test sensitivity:** Three of the five new test methods (`test_absent_five_hour_is_left_out`, `test_absent_seven_day_is_left_out`, `test_no_window_still_renders_a_placeholder`) fail on the pre-diff code in both `statusline.py` and `agent-quota.py`, and every test asserts both scripts so single-script drift cannot slip past. The remaining two methods guard existing dual-window behavior, subject to Finding 1 on the `0%` literal.

## Scope challenge

- **(a) Why this exact scope (smaller vs. marginally larger):** Verified Claude Ultra accounts have no 5-hour cap, and expired windows drop out after `resets_at`, so rendering `5h—` misreports healthy quota as a broken meter in both the interactive Claude status bar and the cross-agent `agent-quota` readout run at `/vet` start. A smaller scope touching only one of the two scripts would split one shared display contract across commits for no savings. A marginally larger scope should go only as far as the 3-line `persist_claude` guard noted in Finding 2 inside `scripts/statusline.py`. Dynamic window omission should **not** be extended to `agy_segment` / `agy_row`: Antigravity's Ultra plan still meters both `5h` and `weekly` buckets, and `skills/prun/scripts/dispatch-task-agy.py` (`REQUIRED_WINDOWS = frozenset({"5h", "weekly"})`) treats a missing Agy bucket as an incomplete snapshot, so a dash on Agy accurately flags missing bucket data rather than an absent plan limit.
- **(b) Out-of-scope / deferred items vs. process tax:** Nothing is deferred to vNext. All three modified files (`scripts/agent-quota.py`, `scripts/statusline.py`, `tests/test_codex_usage.py`) are listed under `strict_files` / `strict_test_files` in `scripts/check-parity.sh`, so mirroring them to `anywhere-agents` is part of the normal parity step rather than a separate cycle. Keeping the open follow-up in `docs/followups/README.md` (`statusline-rollout-walk-junction-guard`, scoped to `_codex_rollouts` / `codex_rollouts`) out of this diff is also the right call, because this change does not touch rollout filesystem discovery.
- **(c) Simplest path:** Yes. Iterating over `CLAUDE_WINDOWS = (("5h", "five_hour"), ("7d", "seven_day"))` with an explicit empty-list placeholder removes duplicated `five` / `week` formatting branches, avoids fragile plan-name heuristics, and preserves standalone deployment of `statusline.py` and `agent-quota.py` into `~/.claude/` without introducing cross-file imports.

Commit verdict: PASS
