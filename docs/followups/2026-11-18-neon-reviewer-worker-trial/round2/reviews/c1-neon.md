<!-- Round 1 -->
Intended file: `Review-Antigravity.md`

# Review (Antigravity)

## Verification notes
All verification commands ran inside the disposable staged snapshot `/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-77ebdaee-round1-12581-93b014056ccd4f2c/staged-snapshot` with `/Users/yzhao062/miniforge3/envs/py312/bin/python`:

- `scripts/agent_models.py show` and `scripts/agent_models.py render --check`: exited 0. Confirmed `grok` resolves to `grok-4.7-build-fast` at `high` for `interactive`, `reviewer`, and `premium`, and `grok-4.7-build-fast` at `medium` for `worker` and `prun-worker`. `user/settings.json` needed no render update.
- `python -m unittest tests/test_agent_models.py tests/test_dispatch_grok.py tests/test_dispatch_task_grok.py -v`: exited 0 (`Ran 138 tests in 18.744s — OK (skipped=1)`).
- `python -m unittest tests/test_dispatch_claude.py tests/test_dispatch_codex.py tests/test_dispatch_gemini.py tests/test_dispatch_task_agy.py tests/test_dispatch_task.py tests/test_render_banner.py -v`: first run failed 69 tests in `test_dispatch_task_agy.py` due to `ANTIGRAVITY_DISPATCH_MODEL=gemini-4-neon-high` inherited from the reviewer's own outer environment; reran with `env -u ANTIGRAVITY_DISPATCH_MODEL -u ANTIGRAVITY_DISPATCH_EFFORT`: exited 0 (`Ran 462 tests in 84.718s — OK (skipped=97)`).
- `python -m unittest tests/test_repo.py tests/test_skill_md_contract.py tests/test_skill_size.py tests/test_check_parity.py tests/test_pointer_files.py tests/test_style_audit.py tests/test_line_endings.py tests/test_prun_executors.py`: 132 passed, 1 skipped; the 10 failures were all `git ls-files` calls in `test_repo.py` and `test_line_endings.py` because the disposable snapshot has no `.git` directory.
- `scripts/agent_models.py scan skills/agent-models/SKILL.md`: exited 0 (no disallowed model or effort literals). Byte check confirmed LF line endings on all three staged files.
- Direct Python verification of `agent_models.validate`/`resolve` and live dispatcher imports:
  - Old `reg_without_grok` fixture (`schema_version: 1`, `agy: gemini-3.1-pro-high`) raises `registry schema must be 1`.
  - Fixing only `schema: 1` while leaving `gemini-3.1-pro-high` raises `family agy: model 'gemini-3.1-pro-high' must be a stem without a tier`.
  - New `reg_without_grok` fixture passes `validate()` and raises `registry has no families.grok row`.
  - `skills/implement-review/scripts/dispatch-grok.py` `resolve_model_and_effort()` returns `('grok-4.7-build-fast', 'registry', 'high', 'registry')`.
  - `skills/prun/scripts/dispatch-task-grok.py` resolves `DEFAULT_MODEL='grok-4.7-build-fast'`, `DEFAULT_EFFORT='medium'`.
- Note: Live `grok` CLI invocation (`agent_models.py verify --family grok`) was not run during review to avoid external API/quota side effects; the maintainer should still run step 5 after commit as documented.

Verification status: VERIFIED

Commit verdict: PASS

## Scope and lens
- **Files in scope**: `user/agent-models.json`, `tests/test_dispatch_grok.py`, `skills/agent-models/SKILL.md` (staged diff, Round 1).
- **Review lens**: Code and documentation correctness, edge cases, behavior changes for existing inputs, test strength (old-code failure and regression sensitivity), cross-file consistency, and maintainability.

## Scope challenge
- **(a) Why this scope?** Switching Grok's family model to `grok-4.7-build-fast` and dropping the redundant `roles.prun-worker.grok.model` key in `user/agent-models.json` keeps every Grok role on one family model with effort-only overrides for `worker` and `prun-worker`. A smaller scope (editing only the registry) fails `tests/test_dispatch_grok.py`, which previously read the live registry and asserted `grok-4.7`. Isolating the harness behind `AGENT_MODELS_FILE`, fixing the masked `schema_version` + tier-suffixed Agy stem bug in `reg_without_grok`, and adding the two Grok files and variables to `skills/agent-models/SKILL.md` directly close the test and documentation gap. Only two small in-file doc details in `skills/agent-models/SKILL.md` (listed below) would improve completeness at near-zero cost; the parity mirror (`anywhere-agents` + `scripts/check-parity.sh`) remains the standard separate maintainer step documented in `SKILL.md:96`.
- **(b) Deferred items vs. process tax:** Nothing is deferred to a follow-up cycle. The unrelated `ANTIGRAVITY_DISPATCH_MODEL` environment inheritance observed in `tests/test_dispatch_task_agy.py` during verification is outside this Grok change and should stay out of scope here.
- **(c) Simplest path?** Yes. Removing `roles.prun-worker.grok.model` lets inheritance do the work (consistent with `roles.worker.grok` and `roles.prun-worker.codex`), and giving `DispatchGrokHarness` a fixture registry via `AGENT_MODELS_FILE` matches `test_dispatch_claude.py`, `test_dispatch_task.py`, `test_dispatch_task_agy.py`, and `test_dispatch_task_grok.py`. Keeping `"grok-4.7"` in the test fixture while the live registry holds `"grok-4.7-build-fast"` also ensures `test_normal_round_publishes_review_and_records_state` fails if `dispatch-grok.py` ever ignores `AGENT_MODELS_FILE`.

## Findings

### New
- **[Low]** `skills/agent-models/SKILL.md:22`: Rule 5 adds `GROK_DISPATCH_MODEL` and `GROK_DISPATCH_EFFORT` and updates the final sentence to `"The Antigravity and Grok variables are read by both /vet and prun."` That phrasing implies the Codex override variables are `/vet`-only, whereas `CODEX_DISPATCH_MODEL` and `CODEX_DISPATCH_REASONING` are also read by `prun` (`skills/prun/scripts/dispatch-task.sh:217-238` and `skills/prun/scripts/dispatch-task.ps1:199-225`). Rewording the sentence to `"All six variables are read by both /vet and prun."` is shorter and matches the code.
- **[Low]** `skills/agent-models/SKILL.md:91`: Step 5 of "Change a model or an effort" tells the maintainer to run `verify` and one `/vet both` round, and line 94 warns that an invalid model name fails at step 5. However, bare `agent_models.py verify` checks only `REQUIRED_FAMILIES` (`claude`, `codex`, `agy`, per `scripts/agent_models.py:1235`), and `/vet both` runs Codex and Gemini. Because this change updates the checklist for Grok in step 2, noting `verify --family grok` (already mentioned in the table at line 36) and a Grok review round when changing Grok avoids silently skipping live validation for a Grok model edit.

### Previously raised
None.
