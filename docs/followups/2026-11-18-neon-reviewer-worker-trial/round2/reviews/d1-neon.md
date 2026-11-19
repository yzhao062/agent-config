<!-- Round 1 -->
Intended file: `Review-Antigravity.md`

## Verification notes

All commands ran in the disposable staged snapshot (`/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-42d08fa9-round1-12562-9946839a726b49d5/staged-snapshot`) using `$HOME/miniforge3/envs/py312/bin/python`:

- `python -m unittest tests/test_agent_models.py -v`: exited 0 (`Ran 122 tests in 3.309s`, `OK (skipped=1)`; the one skip is `DriftGuardTests.test_no_model_or_effort_literal_outside_the_allowlist`, skipped because the disposable snapshot has no `.git` directory).
- `python -m unittest tests/test_skill_md_contract.py tests/test_style_audit.py -v`: exited 0 (`Ran 126 tests in 4.332s`, `OK`).
- `python -m unittest tests/test_repo.py tests/test_skill_size.py tests/test_line_endings.py tests/test_pointer_files.py tests/test_check_parity.py -v`: `test_skill_size.py`, `test_pointer_files.py`, `test_check_parity.py`, and all non-git `test_repo.py` tests passed; 10 tests requiring `git ls-files` failed solely because the disposable snapshot has no `.git` directory.
- Verified LF line endings on all five changed files via Python `read_bytes()`: all five use LF.
- `python scripts/agent_models.py render --check && python scripts/agent_models.py scan docs/writing-harness-map.md skills/agent-models/SKILL.md`: exited 0, no output.
- `python scripts/agent_models.py map .` and `python scripts/agent_models.py map --json .`: exited 0; confirmed `skills/agent-models/SKILL.md` is omitted and `gaps` is `[]` on the snapshot.
- Executed a targeted Python reproduction against `agent_models.map_repo()` with two synthetic consumer files: `skills/fanout/SKILL.md` (referencing `dispatch-task-agy.py`, `dispatch-task.sh`, and `/vet`) and `skills/mixed/SKILL.md` (referencing `codex/reviewer`, `claude/worker`, and `/vet`). Confirmed that `map_repo` stripped `("*", "reviewer", "/vet")` from both files and emitted false `"role": "reviewer"` gaps (`["claude", "grok"]` and `["agy", "grok"]`, respectively).

Verification status: VERIFIED
Commit verdict: BLOCK

## Scope and lens

- **Files changed**: `CHANGELOG.md`, `docs/writing-harness-map.md`, `scripts/agent_models.py`, `skills/agent-models/SKILL.md`, `tests/test_agent_models.py`.
- **Review lens**: Code and its documentation (correctness, edge cases, behavior change for existing inputs, tests, consistency across the change and neighboring files, maintainability), plus mandatory scope-challenge evaluation.

## Findings

### New

#### High

1. **`direct_reviewer` counts `worker` and `prun-worker` rows as reviewer rows (`scripts/agent_models.py:1035-1039`)**

   `map_repo()` builds `direct_reviewer` using `role in ("reviewer", "worker", "prun-worker")` rather than `role == "reviewer"`. This contradicts the inline comment (`scripts/agent_models.py:1041-1042`: "A file resolving two or more reviewer rows dispatches its own panel"), the emitted gap payload (`"role": "reviewer"`), the text output filter (`if purpose == "review"` at line 1114), `skills/agent-models/SKILL.md:63`, and `CHANGELOG.md:28`.

   Observed defects on valid inputs (reproduced directly against `map_repo`):
   - **Pure worker/prun-worker file with `/vet`**: A consumer skill or script that calls two `prun` dispatchers (such as `dispatch-task-agy.py` and `dispatch-task.sh`) and finishes with `/vet` reaches `len(direct_reviewer) == 2`. `map_repo` strips its real `("*", "reviewer", "/vet")` reader and emits `{"file": ..., "role": "reviewer", "missing": ["claude", "grok"]}` in `--json`, even though the file reads zero `reviewer` rows (and `prun` never runs on `claude`). Because stripping `/vet` leaves no `purpose == "review"` readers for that file, `cmd_map` text output silently omits the gap while `--json` reports it.
   - **Mixed `reviewer` + `worker`/`prun-worker` file**: A file reading `codex/reviewer` and `claude/worker` alongside `/vet` drops `/vet`, falsely counts `claude/worker` as satisfying `claude/reviewer`, and emits `no reader for: agy, grok`. In a real review panel that mistakenly resolves `claude/worker` instead of `claude/reviewer`, this hides the missing `claude/reviewer` reader.
   - **Missing test coverage**: None of the three new tests in `tests/test_agent_models.py` exercise `worker` or `prun-worker` readers alongside `reviewer` or `/vet`, so the defect is not caught.

   Exact rewrite (`scripts/agent_models.py:1035-1039`):

   ```python
        direct_reviewer = {
            family
            for family, role, how in file_readers
            if role == "reviewer" and family != "*" and how not in SLASH_COMMANDS
        }
   ```

   Also extend `MapTests` in `tests/test_agent_models.py` to cover:
   - a file resolving two `prun-worker` rows (`dispatch-task-agy.py` and `dispatch-task.sh`) plus `/vet`, asserting `("*", "reviewer", "/vet")` stays in `readers` and `gaps` is empty;
   - a file resolving one `reviewer` row (`codex/reviewer`), one `worker` row (`claude/worker`), and `/vet`, asserting `/vet` stays and `gaps` is empty;
   - a panel resolving `codex/reviewer`, `agy/reviewer`, and `claude/worker`, asserting `claude` is still listed in `missing`.

#### Low

2. **`scripts/agent_models.py` command documentation omits the gap output (`scripts/agent_models.py:44-47`)**

   The module docstring entry for `map PATH ... [--json]` describes listing files that read a registry row and direct CLI launches, while `skills/agent-models/SKILL.md:63` was updated to mention missing reviewer families. Adding one short clause to the `map` block in the module docstring keeps the script header aligned with `SKILL.md`.

### Previously raised

None.

## Test audit

- `test_map_repo_reports_missing_reviewer_families_and_drops_vet_for_panels`, `test_map_skips_agent_models_skill_and_prints_gaps`, and `test_map_expects_only_the_families_the_registry_has` all fail on the pre-diff code (new `expected_families` parameter, new `gaps` key, `/vet` suppression on panels, `skills/agent-models/` skip, and `no reader for:` formatting) and assert observable API/CLI outputs rather than source strings.
- The combined fallback assertions across `test_map_skips_agent_models_skill_and_prints_gaps` (three-family panel gets `[]`) and `test_map_expects_only_the_families_the_registry_has` (two-family pair gets `["agy"]`) cleanly verify that an unloadable registry falls back to `REQUIRED_FAMILIES` rather than `FAMILIES` or an empty set.
- Gap in coverage: `worker` and `prun-worker` interactions with `direct_reviewer` are untested (see Finding 1).

## Scope challenge

- **(a) Why this scope?** The change closes a real blind spot: adding an optional family (`grok`) to `user/agent-models.json` left custom multi-vendor review panels silently on three families while `agent_models.py map` displayed `*/reviewer via /vet` beside them. A smaller scope would not close it cleanly: keeping `/vet` on panel lines would produce self-contradictory output (`*/reviewer via /vet; ...; no reader for: grok`), and skipping `skills/agent-models/` is required so the skill's own examples do not trigger a false gap. A marginally larger scope (such as aggregating readers across an entire skill directory or adding a non-zero exit status / `doctor` gate) carries real false-positive risk for multi-file layouts like `skills/implement-review/` and intentionally narrower two-family checks, so staying per-file and advisory matches `map`'s existing `launches` contract.
- **(b) Deferred / out-of-scope items vs. process tax:** Nothing material is deferred to a follow-up cycle here. The two concrete review panels (`venue-review-panel` in `agent-pack` and the consumer's local proposal panel) live in separate repositories and are already updated per `CHANGELOG.md`. Keeping directory-level aggregation and gating flags out of scope avoids speculative complexity without creating a deferred cleanup tax.
- **(c) Is this the simplest path?** Yes, once Finding 1 is fixed (`role == "reviewer"`). Reusing `FAMILIES` and `REQUIRED_FAMILIES` with a single `gaps` field and one appended text suffix solves the problem in roughly 25 lines with no new CLI flags or registry schema changes.
