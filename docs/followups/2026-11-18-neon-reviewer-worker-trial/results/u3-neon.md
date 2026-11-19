# u3-neon result
Conclusion: Trimmed leading narration before an exact `# <unit-id> result` header in `dispatch-task-agy.py`, preserved the full response at `<result>.response.<ext>`, and added integration tests for narration, header-first, and no-header cases (98 passed, 32 subtests passed).
Files: [dispatch-task-agy.py](file:///private/tmp/claude-501/-Users-yzhao062-PycharmProjects-agent-config/fbae8ab0-bac3-4585-b656-5019ef378c4b/scratchpad/neon/u3-neon/skills/prun/scripts/dispatch-task-agy.py), [test_dispatch_task_agy.py](file:///private/tmp/claude-501/-Users-yzhao062-PycharmProjects-agent-config/fbae8ab0-bac3-4585-b656-5019ef378c4b/scratchpad/neon/u3-neon/tests/test_dispatch_task_agy.py)
Open items: none
Verification: `env -u ANTIGRAVITY_DISPATCH_MODEL /Users/yzhao062/miniforge3/envs/py312/bin/python -m pytest -q tests/test_dispatch_task_agy.py` -> `98 passed, 32 subtests passed in 18.49s` (`ANTIGRAVITY_DISPATCH_MODEL=gemini-4-neon-high` was inherited from this worker's own dispatcher environment and caused pre-existing integration tests to fail preflight against the mock's default model list when left set).

## Diff Summary

```text
 skills/prun/scripts/dispatch-task-agy.py | 42 +++++++++++++++-
 tests/test_dispatch_task_agy.py          | 85 ++++++++++++++++++++++++++++++++
 2 files changed, 125 insertions(+), 2 deletions(-)
```

### Key Hunks

1. **[dispatch-task-agy.py](file:///private/tmp/claude-501/-Users-yzhao062-PycharmProjects-agent-config/fbae8ab0-bac3-4585-b656-5019ef378c4b/scratchpad/neon/u3-neon/skills/prun/scripts/dispatch-task-agy.py#L1009-L1031)**: Added `trim_leading_narration(text: str, unit_id: str) -> str | None` beside `response_path_for`. It splits `text.strip().splitlines()` and looks for the first line equal to `f"# {unit_id} result"`. If the line is absent or at index 0 (already the first non-empty line), it returns `None`; otherwise it returns `"\n".join(lines[index:])`. Updated the `response_path_for` docstring to cover both sibling-response cases.
2. **[dispatch-task-agy.py](file:///private/tmp/claude-501/-Users-yzhao062-PycharmProjects-agent-config/fbae8ab0-bac3-4585-b656-5019ef378c4b/scratchpad/neon/u3-neon/skills/prun/scripts/dispatch-task-agy.py#L1533-L1566)**: In the `elif exit_code == 0:` branch (only when no worker-written result file exists and the response passes `MIN_RESULT_BYTES`), called `trim_leading_narration(full, args.unit_id)`. Published the trimmed text (or `full` when `trimmed is None`) to `result_path`, and when `trimmed is not None` and the primary publish succeeds, stored `full + "\n"` at `response_path_for(result_path)` (logging a stderr warning on `OSError`, matching the `worker_wrote` path). Left `worker_wrote` and all FALLBACK paths unchanged.
3. **[test_dispatch_task_agy.py](file:///private/tmp/claude-501/-Users-yzhao062-PycharmProjects-agent-config/fbae8ab0-bac3-4585-b656-5019ef378c4b/scratchpad/neon/u3-neon/tests/test_dispatch_task_agy.py#L1371-L1455)**: Added three `DispatchTaskAgyIntegrationTests` methods exercising the dispatcher against the mock `agy`:
   - `test_narration_before_header_is_trimmed_and_full_response_stored_beside`: checks that leading narration (including an inline mention of `# unit_a result`) is trimmed from `unit-result.md` and preserved verbatim in `unit-result.response.md`.
   - `test_header_first_response_publishes_unchanged_with_no_sibling_file`: checks both line-0 header and leading blank lines before the header publish unchanged with no `.response.md` sibling.
   - `test_response_without_exact_header_publishes_unchanged_with_no_sibling_file`: checks responses with no header, another unit's header (`# unit_b result`), or a non-exact header (`# unit_a result (extra)`) publish unchanged with no `.response.md` sibling.
