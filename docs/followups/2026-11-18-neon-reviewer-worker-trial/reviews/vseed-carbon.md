<!-- Round 1 -->

# Review (Review-Antigravity.md)

## Verification notes

- Ran `env -u ANTIGRAVITY_DISPATCH_MODEL -u ANTIGRAVITY_DISPATCH_EFFORT -u AGENT_MODELS_FILE $HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_health_check.py tests/test_dispatch_gemini.py` in the disposable snapshot: 174 tests ran in 29.28s, OK (3 skipped). Running without `env -u` first failed 26 integration tests in `tests/test_dispatch_gemini.py` with exit 70 because the parent review dispatcher exported `ANTIGRAVITY_DISPATCH_MODEL` into the environment.
- Ran `$HOME/miniforge3/envs/py312/bin/python` reproductions against `skills/implement-review/scripts/health-check.py` and `skills/implement-review/scripts/dispatch-gemini.py`: confirmed that `code_span_bounds` returns overlapping bounds `[(17, 35), (32, 69), (66, 85)]` on a review containing two triple-backtick blocks, causing `health-check.py` to exit 1 (`FAIL check-10 verdict=BLOCK verification=MISSING`) when `Verification status: VERIFIED` sits between two fenced blocks, and confirmed `strip_code_spans` reduces ``Found `foo` connection refused and `bar`.`` to `'Found .'`.
- Ran `$HOME/miniforge3/envs/py312/bin/python` benchmarks and old-versus-new comparisons: measured 0.0585s on a 1.9 MB synthetic JSONL tail (25,000 lines), confirmed Check 8 still scans `AGENTS.md`, `skills/implement-review/SKILL.md`, all `skills/implement-review/references/*.md`, and `skills/implement-review/scripts/dispatch-gemini.py` to `0-tool-failure-markers` with `index = partner + 1`, and checked each new test case against the prior two-regex implementation.

Verification status: VERIFIED

## Scope and review lens

- Intended output file: `Review-Antigravity.md`
- Files reviewed: `skills/implement-review/scripts/health-check.py`, `skills/implement-review/scripts/dispatch-gemini.py`, `tests/test_health_check.py`, `tests/test_dispatch_gemini.py`, `CHANGELOG.md`
- Lens: Code (correctness, Check 8 raw tail behavior, scan mechanics, `dispatch-gemini.py` newline-preserving mask and AST parity check, test coverage and mutation sensitivity, scope challenge)

## New

### 1. High: `code_span_bounds` sets `index = partner` instead of `index = partner + 1`, turning every closing run into the opener of a phantom span (`skills/implement-review/scripts/health-check.py:336`, `skills/implement-review/scripts/dispatch-gemini.py:740`)

When `opener = runs[index]` matches `runs[partner]`, `code_span_bounds` appends `(opener.start(), runs[partner].end())` and assigns `index = partner` with no increment before the next loop iteration. On the next pass of `while index < len(runs):`, `runs[partner]` (the closing delimiter of the span that just ended) is read again as a fresh opener and paired with `next_same[partner]` (the opening delimiter of the next span of the same width, whenever width is at least 3 or no newline sits between them). Every gap between consecutive same-width code spans is therefore emitted as an extra span overlapping its neighbors at both ends:

- **Check 10 false failures (`skills/implement-review/scripts/health-check.py:360-366`):** In `strip_code_spans`, the synthetic span `(close_0.start(), open_1.end())` has `start < keep_from`, which slices `text[keep_from:start]` to `""` and advances `keep_from` to `open_1.end()`. Any review that places a triple-backtick command block in `Verification notes` above `Verification status: VERIFIED` and a triple-backtick code block in `## New` below it loses `Verification status: VERIFIED` and fails Check 10 with `verdict=BLOCK verification=MISSING` (verified with exit code 1). Two inline single-backtick spans bracketing a verdict token on one line drop the verdict token for the same reason.
- **Check 8 false negatives on raw dispatch tails (`skills/implement-review/scripts/health-check.py:573`):** Raw `stream-json` and `codex exec` tails routinely carry many single-backtick spans on one JSON or reasoning line, and multiple triple-backtick blocks across a session tail. Any real failure marker (`connection refused`, `HTTP/1.1 429`, `ENOSPC`, `quota exceeded`) sitting between the first and last single-backtick span on the same line, or between two triple-backtick fences anywhere in the tail, is stripped before Check 8 scans.
- **Check 7 false negatives and recovery false rejections (`skills/implement-review/scripts/dispatch-gemini.py:765-773`):** Check 7 misses failure narration between consecutive fences or same-line inline spans, and `has_review_structure` replaces all prose lines between consecutive triple-backtick fences with blank lines, rejecting valid finished reviews during backend-error recovery.

Advance `index` past the closing run (`index = partner + 1`) in both copies so each backtick run belongs to at most one paired span and `bounds` is strictly disjoint and increasing.

Exact rewrite for `skills/implement-review/scripts/health-check.py:335-337`:

```python
        bounds.append((opener.start(), runs[partner].end()))
        index = partner + 1
    return bounds
```

Exact rewrite for `skills/implement-review/scripts/dispatch-gemini.py:739-741`:

```python
        bounds.append((opener.start(), runs[partner].end()))
        index = partner + 1
    return bounds
```

### 2. Medium: New tests miss prose between consecutive same-width spans, and two nested-delimiter assertions already pass on the old regexes (`tests/test_health_check.py:587-602`, `tests/test_health_check.py:1304-1365`, `tests/test_dispatch_gemini.py:449-466`)

Two test-design gaps show up when checking mutation sensitivity and old-code failure:

1. **No fixture places a checked token between two paired spans of the same width.** Every new case in `tests/test_health_check.py` and `tests/test_dispatch_gemini.py` uses either a single span of a given width (` ```` ```python ```` ` of width 4 followed by ` ```python ... ``` ` of width 3) or asserts `PASS` (marker hidden). In `"after three single backticks"` (`tests/test_health_check.py:597`), ``f"`example` then ` {marker}\n"`` placed `{marker}` after the third backtick while `" then "` between the second and third backticks was silently stripped. Adding cases where `{marker}`, `Verification status: VERIFIED`, and a Check 7 phrase sit *between* two single-backtick spans on one line (``"`first` connection refused `second`\n"``) and *between* two triple-backtick fences across lines pins `index = partner + 1` in Check 7, Check 8, Check 10, and `has_review_structure`.
2. **Two nested-delimiter subtests pass unchanged on the old two-regex implementation:**
   - In `tests/test_health_check.py:592-594`, `"double-backtick span holding a backtick"` uses ``f"Quoted ``a ` {marker}`` here.\n"``. On the old code, `re.sub(r"`[^`\n]*`", "", ...)` matched the opening ` `` ` as empty and then paired the inner `` ` `` with the first backtick of the closing ` `` `, hiding `{marker}` by coincidence. Moving `{marker}` before the inner backtick (``f"Quoted ``{marker} ` a`` here.\n"``, matching the Check 7 shape at line 1347) makes the old code leave `{marker}` exposed and fail.
   - In `tests/test_dispatch_gemini.py:459-466`, `template = f"{fence}text\nexample\n{fence}\n{whole}"` places `{whole}` after the inner three-backtick block inside `{long_fence}markdown\n{template}{long_fence}\n`. On the old code, `r"```.*?```"` paired the opening ` ```` ` with the first ` ``` ` and the second ` ``` ` with the closing ` ```` `, which still masked `{whole}` and returned `False`. Putting `{whole}` *inside* the inner three-backtick fence (`template = f"{fence}markdown\n{whole}{fence}\n"`) makes the old code close on ` ```markdown `, expose `{whole}`, and return `True`, so the assertion fails on the old code as intended.

## Assessment of remaining focus items

- **Check 8 tails (once `index = partner + 1` is fixed):** Compared against the old two-regex pass on single-line JSON tails with escaped `\\n` and multi-line `codex exec` tails, whole-run matching removes both false negatives (an inline four-backtick span quoting ` ``` ` or an unpaired ` ```` ` run ahead of a ` ``` ` block no longer swallows real failure markers between them, and a double-backtick span holding a single backtick on a long JSON line no longer pairs that inner backtick to the next single-backtick span across real error fields) and false positives (nested fences and double-backtick spans stay masked). Keeping the newline check on literal `"\n"` (`0x0A`) for widths 1 and 2 is also the right choice: matching two-character `\n` escapes would break backticked Windows paths such as `` `C:\new_dir\file` `` in raw `codex exec` tails, while triple-backtick fences inside one-line JSON strings still match across `\\n` because widths 3 and above may cross lines.
- **`dispatch-gemini.py` mask and AST parity check:** Once `bounds` is disjoint (`index = partner + 1`), replacing each span `[start, end)` with `"\n" * text.count("\n", start, end)` preserves exact line indices so `visible_lines[marker_index]` aligns with `normalize_review`'s cut point, and `test_code_span_bounds_matches_the_health_check_copy` compares the docstring-stripped ASTs of both `code_span_bounds` and `BACKTICK_RUN_RE`, catching logic, operator, and constant drift without pinning formatting or docstrings.

## Scope challenge

- **(a) Why this scope (smaller vs. larger):** The scope closes a real consumer `/vet` failure where a valid Antigravity review quoting `` ```` ```python ```` `` lost its `Verification status: VERIFIED` line and failed Check 10. A smaller scope touching only `health-check.py` would leave `dispatch-gemini.py`'s `has_review_structure` disagreeing with Check 10 on the very Antigravity review shape that triggered the bug, either rejecting valid finished reviews during backend-error recovery or recovering templates quoted inside four-backtick fences that Check 10 then fails. A larger scope pulling in `scripts/guard.py` (`_content_for_style_check` at `scripts/guard.py:601-606`) is unnecessary here: `guard.py` runs at `PreToolUse` time on authored prose files rather than multi-megabyte dispatch tails, handles tilde fences (`~~~`), and inserts a leading space to keep word boundaries apart, so forcing one helper across both would couple the global `PreToolUse` hook to `/vet` scanner semantics for little gain.
- **(b) Out-of-scope / deferral process tax:** Leaving the other Check 7, 8, and 10 regex patterns out of this patch incurs zero extra release-cycle tax because no concrete defect is queued for them, and mixing pattern-vocabulary edits into a lexer fix would blur regression attribution against the Check 8 false-positive corpus. Excluding Windows wrapper changes has zero tax because `skills/implement-review/scripts/health-check.ps1` only locates Python and executes `health-check.py`.
- **(c) Simplest path:** A twenty-line linear scan over `BACKTICK_RUN_RE.finditer` with one reverse pass is the simplest sound path. A backreference regex such as ``r"(`{3,})[\s\S]*?\1"`` still backtracks from four backticks to three when a four-backtick run has no partner (reintroducing the exact bug alongside quadratic $O(N^2)$ scans on long dispatch tails), and Python 3.9 (this repository's CI floor) lacks possessive quantifiers (`*+`) and atomic groups (`(?>...)`) in `re`. Duplicating that small pure function across the two standalone scripts with an AST equality test avoids introducing import-path plumbing into consumer-deployed script invocation.

## Previously raised

None.

Commit verdict: BLOCK
