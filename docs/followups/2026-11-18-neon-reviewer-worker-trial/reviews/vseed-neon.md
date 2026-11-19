<!-- Round 1 -->

# Review (`Review-Antigravity.md`)

## Verification notes

Ran from `/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-2cb3430f-round1-56372-4f3e6a4d41dc46b4/staged-snapshot`:

- `env -u ANTIGRAVITY_DISPATCH_MODEL -u ANTIGRAVITY_DISPATCH_EFFORT -u IMPLEMENT_REVIEW_ORCHESTRATOR "$HOME/miniforge3/envs/py312/bin/python" -m unittest tests/test_health_check.py tests/test_dispatch_gemini.py`: exited 0 (`Ran 174 tests in 31.218s`, `OK (skipped=3)`). (An initial run with inherited `ANTIGRAVITY_DISPATCH_MODEL` had 26 expected environment-override failures in `DispatchGeminiIntegrationTests`.)
- `env -u ANTIGRAVITY_DISPATCH_MODEL -u ANTIGRAVITY_DISPATCH_EFFORT -u IMPLEMENT_REVIEW_ORCHESTRATOR "$HOME/miniforge3/envs/py312/bin/python" -m unittest tests/test_repo.py tests/test_line_endings.py tests/test_skill_md_contract.py`: all `test_skill_md_contract.py` tests passed; 10 tests in `test_repo.py` and `test_line_endings.py` require `.git` (`git ls-files`) which is absent in the exported snapshot.
- Ran scratch verification scripts against `health-check.py` and `dispatch-gemini.py` in the snapshot:
  - End-to-end `health-check.py` on a valid `VERIFIED` review containing two triple-backtick code blocks surrounding `Verification status: VERIFIED` and a tail `'{"text":"ran `curl` got connection refused from `api`"}\n'`: exited 1 with `FAIL check-10 verdict=BLOCK verification=MISSING` and `PASS check-8 0-tool-failure-markers`.
  - Direct call `has_review_structure(two_fence_review, 1)` on the same valid review: returned `False`.
  - Simulated the pre-change regexes against every new test input in `tests/test_health_check.py` and `tests/test_dispatch_gemini.py` to check which assertions fail on the old code.
  - Benchmarked `code_span_bounds` (with `index = partner + 1`) on a 660 KB tail with 120k backtick runs (0.046s) and on 50k lines with unpaired single backticks (0.036s), confirming linear `O(N)` scaling.
- Grepped `skills/implement-review/scripts/` for `strip_code_spans`, `code_span_bounds`, `has_review_structure`, and `VERIFICATION_STATUS_RE` to confirm no other script duplicates this logic.

Verification status: VERIFIED

## Scope and lens

- **Files reviewed (from staged diff)**: `skills/implement-review/scripts/health-check.py`, `skills/implement-review/scripts/dispatch-gemini.py`, `tests/test_health_check.py`, `tests/test_dispatch_gemini.py`, `CHANGELOG.md`.
- **Context read**: `AGENTS.local.md`, `skills/implement-review/references/health-check.md`.
- **Lens**: Code (correctness, edge cases, behavior delta on Check 8 tails, performance, test strength, maintainability, and scope challenge).

## New

### 1. [High] `code_span_bounds` sets `index = partner` instead of `index = partner + 1`, stripping all prose between any two same-width code spans or fenced blocks

- **Locations**: `skills/implement-review/scripts/health-check.py:335-336` and `skills/implement-review/scripts/dispatch-gemini.py:739-740`.
- **Problem**: After matching `opener = runs[index]` with its closing run `runs[partner]`, the loop sets `index = partner` instead of `index = partner + 1`. On the next iteration, `runs[partner]` is re-consumed as a new opening delimiter and paired with `next_same[partner]` (the opening delimiter of the next span of the same width). This produces overlapping bounds `[(r0.start, r1.end), (r1.start, r2.end), (r2.start, r3.end), ...]`. Because `strip_code_spans` (`health-check.py:362-364`) and `has_review_structure` (`dispatch-gemini.py:767-770`) slice `text[keep_from:start]` (empty when `start < keep_from`) and advance `keep_from = end`, everything between any two same-width spans is deleted or blanked.
- **Reproduced impact**:
  1. **Check 10 breaks on valid reviews with two or more fenced blocks**: Placing one triple-backtick block before `Verification status: VERIFIED` and another after it causes `strip_code_spans` to delete `Verification status: VERIFIED` and exit 1 with `FAIL check-10 verdict=BLOCK verification=MISSING`.
  2. **Backend-error recovery breaks on the same reviews**: `dispatch-gemini.py`'s `has_review_structure` returns `False` on the same valid two-fence review.
  3. **Check 7 and Check 8 drop real signals between any two same-width spans**:
     - `Check \`pytest\` failed to run \`test_foo.py\`.\n` strips to `'Check .\n'` (Check 7 misses the phrase).
     - `'{"text":"ran `curl` got connection refused from `api`"}\n'` strips to `'{"text":"ran "}\n'` and emits `PASS check-8 0-tool-failure-markers` instead of `WARN`. Any dispatch tail with two triple-backtick blocks drops every real failure marker between them.
     - Even the new test input `` `example` then ` connection refused\n `` (`tests/test_health_check.py:597`) had ` then ` stripped and passed only because the marker sat after the third backtick.
- **Exact rewrite**:

In `skills/implement-review/scripts/health-check.py:335-337`:
```python
        bounds.append((opener.start(), runs[partner].end()))
        index = partner + 1
    return bounds
```

In `skills/implement-review/scripts/dispatch-gemini.py:739-741`:
```python
        bounds.append((opener.start(), runs[partner].end()))
        index = partner + 1
    return bounds
```

### 2. [Medium] Test gaps: no case tests prose between consecutive same-width spans, and two new assertions already pass on the old regex

- **Locations**: `tests/test_health_check.py:577-608`, `tests/test_health_check.py:1304-1365`, `tests/test_dispatch_gemini.py:446-466`.
- **Details**:
  1. **Why Finding 1 passed all 174 tests**: `test_check10_reads_the_status_after_an_inline_span_quoting_a_fence` (`tests/test_health_check.py:1318-1324`) places a 4-backtick span before `Verification status: VERIFIED` and a 3-backtick block after it (different widths), and no Check 7, Check 8, or `has_review_structure` test puts a checked line or marker between two spans of the same width. Add cases with:
     - two triple-backtick blocks surrounding `Verification status: VERIFIED` (in both `tests/test_health_check.py` and `tests/test_dispatch_gemini.py`),
     - two single-backtick spans on one line surrounding a real Check 8 marker (for example, `'{"text":"ran `curl` got connection refused from `api`"}\n'`) and a Check 7 phrase, and
     - two triple-backtick blocks surrounding a real Check 8 marker.
  2. **Two new assertions do not fail on the old regexes**:
     - `tests/test_dispatch_gemini.py:459-466`: `template = f"{fence}text\nexample\n{fence}\n{whole}"` inside a 4-backtick fence already returned `False` under the old `r"```.*?```"` regex, because the first match paired the opening 4-backtick run with the inner opening 3-backtick run, and the second match paired the inner closing 3-backtick run with the closing 4-backtick run, swallowing `{whole}` by accident. Placing `{whole}` inside the inner triple-backtick fence (`template = f"{fence}markdown\n{whole}{fence}\n"`, mirroring `tests/test_health_check.py:1343`) fails on the old regex (`True`) and actually verifies whole-run matching.
     - `tests/test_health_check.py:592-594`: `"double-backtick span holding a backtick": f"Quoted ``a ` {marker}`` here.\n"` already passed under the old `r"`[^`\n]*`"` regex, which matched the opening ` `` ` as empty and then stripped `` ` connection refused` `` up to the first backtick of the closing ` `` `. Moving `marker` before the inner single backtick (`f"Quoted ``{marker} ` a`` here.\n"`, matching `tests/test_health_check.py:1347`) fails on the old regex and exercises double-backtick pairing.
- **Note on test style**: The tests otherwise assert check outcomes and structure rather than prose, consistent with `AGENTS.local.md`, and `test_code_span_bounds_matches_the_health_check_copy` (`tests/test_dispatch_gemini.py:468-494`) cleanly checks AST parity while stripping docstrings and failing loudly if either symbol is renamed or missing.

### 3. [Low] Check 8 single-line JSON-tail behavior delta after fixing `index = partner + 1`

- **Location**: `skills/implement-review/scripts/health-check.py:329-336` (applied to Check 8 at `health-check.py:573`).
- **Behavior comparison (old regexes vs fixed `code_span_bounds` on realistic Check 8 tails)**:
  - **Fixed cases**: Real markers between a quoted fence (4-backtick inline span) and a later fenced block now surface; failure patterns inside double-backtick spans or inside 4-backtick fences wrapping 3-backtick blocks are now hidden.
  - **New false-negative class on single-line JSON tails**: Because `stream-json` events escape newlines as `\n` (two characters) rather than `0x0a`, a multi-kilobyte event sits on one physical line, so the width `< 3` newline guard does not break across escaped `\n`.
    1. **Repeated ` `` ` tokens**: Previously `r"`[^`\n]*`"` stripped each ` `` ` as an empty span. Now two ` `` ` tokens anywhere in the same JSON event (for example, LaTeX double quotes `` ``first'' `` ... `` ``second'' `` or empty JS/TS template literals ``const a = ``;`` ... ``const b = ``;``) pair across all intervening escaped lines and hide any failure marker between them. (In review files with real newlines, this affects only two ` `` ` pairs on the same line.)
    2. **Unpaired single backtick before a fenced block containing a single backtick on the same JSON line**: Previously pass 1 removed triple-backtick blocks before pass 2 ran, so an earlier stray single backtick remained unpaired. Left-to-right scanning now pairs that stray single backtick with the first single backtick inside the fenced block, hiding markers between them and leaking the tail of the fenced block.
  - **New false-positive class**: A triple-backtick fence closed by four backticks stays visible, which is explicitly documented in the docstring as a heuristic tradeoff.
- **Recommendation**: In practice, Agy backend errors usually land on their own JSON event line or in `tail.stderr-tmp`, so this is low-risk and does not require a Markdown parser or JSON unescaping. Documenting that ` `` ` pairs inside single-line JSON tails span escaped newlines (or checking whether `text.find("\\n", ...)` is even desired, which risks false splits on Windows paths) is optional; leaving the implementation simple after fixing Finding 1 is reasonable.

## Focus checklist

1. **Check 8 tails**: Severely regressed under current `index = partner` (drops markers between any two same-width spans); after fixing to `index = partner + 1`, matches or improves on the old code except for the narrow single-line JSON ` `` ` / stray-backtick-into-fence deltas noted in Finding 3.
2. **Scan correctness and performance**: `next_same` reverse pass, width `< 3` single-line guard, unpaired-run skipping, and piece assembly are sound and strictly `O(N)` once `index = partner + 1` is fixed (for widths 1 and 2, the `(runs[i].end(), runs[next_same[i]].start())` ranges are pairwise disjoint per width, so `text.find("\n", ...)` scans each character at most twice).
3. **`dispatch-gemini.py` copy and AST test**: Newline-preserving mask (`"\n" * text.count("\n", start, end)`) preserves 1-to-1 line indexing with `marker_index` once intervals are non-overlapping (`index = partner + 1`). AST identity test is clean and verifies both `code_span_bounds` (body sans docstring) and `BACKTICK_RUN_RE`.
4. **Tests**: Structure-based (no prose pinning), but missing consecutive-same-width-span cases and carrying two assertions that pass on the old code (Finding 2).

## Scope-challenge

- **(a) Why this scope (smaller vs marginally larger)**: The scope targets a real production Check 10 false failure on a valid Agy review while keeping `dispatch-gemini.py`'s recovery mask in lockstep. A smaller scope that left `dispatch-gemini.py` on the old regex would reintroduce Check 10 / recovery disagreement on the exact observed review shape; a smaller lookaround regex patch (`(?<!\`)` around triple backticks) would leave 4-backtick fences holding 3-backtick examples and double-backtick spans broken. A marginally larger scope is unnecessary: no other script in `skills/implement-review/scripts/` duplicates code-span stripping or review-structure parsing, and `health-check.ps1` delegates to `health-check.py`.
- **(b) Deferrals vs process tax**: Keeping tilde fences and unrelated Check 7/8/10 patterns out of scope is justified; there is no observed pain there and touching them adds regression risk. Keeping `code_span_bounds` copied between the two standalone scripts with an AST-identity test avoids adding a shared helper module and import-path plumbing across deployed skill directories for ~20 lines of code; that deferral is worth keeping.
- **(c) Simplest path**: Yes, once `index = partner` is corrected to `index = partner + 1`. A 20-line whole-run linear scanner is simpler and more predictable than nested lookaround regexes or a CommonMark parser.

## Previously raised

None.

Commit verdict: BLOCK
