<!-- Round 1 -->
# Review (Antigravity)

Intended file: `Review-Antigravity.md`

## Verification notes

All commands were run from `/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-ccabfdc6-round1-12582-41d0928e34524eb0/staged-snapshot` using `$HOME/miniforge3/envs/py312/bin/python`:

1. `$HOME/miniforge3/envs/py312/bin/python scripts/agent_models.py show` -> exit `0`; resolved all five `grok` roles to `grok-4.7-build-fast` with `high` effort for `interactive`, `reviewer`, and `premium`, and `medium` effort for `worker` and `prun-worker`.
2. `$HOME/miniforge3/envs/py312/bin/python scripts/agent_models.py render --check` -> exit `0`; `user/settings.json` matches the rendered Claude entries.
3. `$HOME/miniforge3/envs/py312/bin/python scripts/agent_models.py map .` -> exit `0`; confirmed `grok` role readers (`dispatch-grok.py` -> `grok/reviewer`, `dispatch-task-grok.py` -> `grok/prun-worker`) and resolved model/effort summary.
4. `$HOME/miniforge3/envs/py312/bin/python scripts/agent_models.py scan skills/ scripts/ bootstrap/ .claude/ AGENTS.md AGENTS.local.md` -> exit `1` with only the 4 expected hits inside allowlisted `scripts/agent_models.py` (the snapshot omits `.git`, so `DriftGuardTests` skips `git ls-files`; running `scan` directly confirmed zero unallowed model or effort literals in `skills/agent-models/SKILL.md` or neighboring live trees).
5. `$HOME/miniforge3/envs/py312/bin/python -m pytest tests/test_agent_models.py tests/test_dispatch_grok.py tests/test_dispatch_task_grok.py tests/test_dispatch_claude.py tests/test_dispatch_codex.py tests/test_dispatch_gemini.py tests/test_dispatch_task_agy.py tests/test_dispatch_task.py tests/test_render_banner.py` -> `test_agent_models.py` (105 passed, 1 skipped), `test_dispatch_grok.py` (19 passed), `test_dispatch_task_grok.py` (13 passed), `test_dispatch_claude.py` (40 passed, 37 skipped), `test_dispatch_codex.py` (69 passed, 45 skipped), `test_dispatch_task.py` (16 passed, 14 skipped), `test_render_banner.py` (81 passed, 1 skipped); the two Agy suites failed 69 cases in that invocation only because the reviewer harness sets `ANTIGRAVITY_DISPATCH_MODEL` in the parent environment.
6. `env -u ANTIGRAVITY_DISPATCH_MODEL -u ANTIGRAVITY_DISPATCH_EFFORT $HOME/miniforge3/envs/py312/bin/python -m pytest tests/test_dispatch_gemini.py tests/test_dispatch_task_agy.py` -> exit `0` (158 passed).
7. `$HOME/miniforge3/envs/py312/bin/python -m pytest tests/test_dispatch_path_resolution.py` -> exit `0` (1 passed, 11 skipped).
8. Counterfactual check via `$HOME/miniforge3/envs/py312/bin/python -c ...` against `tests.test_dispatch_grok.TestDispatchGrokNormalAndStreaming`:
   - Passing `AGENT_MODELS_FILE=""` (simulating the pre-diff harness reading live `user/agent-models.json`) wrote `['model=grok-4.7-build-fast source=registry effort=high effort_source=registry', 'actual=grok-4.7-build high status=mismatch']` to `review-model`, confirming `test_normal_round_publishes_review_and_records_state` fails without the harness fixture.
   - Passing a fixture with `"schema_version": 1` (simulating the pre-diff `reg_without_grok`) produced `registry schema must be 1` on stderr and lacked `"registry has no families.grok row"`, confirming the tightened assertion fails on the old fixture.

Verification status: VERIFIED

Commit verdict: PASS

## Scope and lens

- **Files changed**: `skills/agent-models/SKILL.md`, `tests/test_dispatch_grok.py`, `user/agent-models.json`.
- **Lens**: Code and its documentation: correctness, edge cases, behavior change for existing inputs, test discrimination (failure on old code and on broken new code), consistency across the change and neighboring code/docs, maintainability, and mandatory scope challenge.

## Scope challenge

- **(a) Why this scope, smaller scope, or marginally larger scope**: Updating `families.grok.model` to `grok-4.7-build-fast` and removing the redundant `model` key in `roles.prun-worker.grok` puts all Grok roles on one measured model while preserving the `high` vs `medium` effort split and preventing `roles.prun-worker.grok` from shadowing future `agent_models.py set --family grok --model ...` edits. A smaller scope is not viable: changing `user/agent-models.json` alone breaks `tests/test_dispatch_grok.py`, and isolating the harness without fixing `"schema_version": 1` in `TestDispatchGrokRegistryAndGuards` would leave a nearby test passing for the wrong reason (schema validation rather than a missing `families.grok` row). A marginally larger scope within the already-staged `skills/agent-models/SKILL.md` can close two remaining documentation gaps at near-zero cost: clarifying in Rule 5 that all six override variables work in both `/vet` and `prun`, and noting `verify --family grok` in Step 5 of `Change a model or an effort` (detailed in Findings below). Cross-repo parity sync to `anywhere-agents` (`user/agent-models.json` and `skills/agent-models/SKILL.md` are both gated by `scripts/check-parity.sh`) remains required at push time per `skills/agent-models/SKILL.md:96`.
- **(b) Deferred items vs. process tax**: The change defers nothing beyond the three staged files, which avoids unnecessary follow-up overhead. Folding the two one-line `skills/agent-models/SKILL.md` wording fixes into this commit (rather than spinning up a separate review, parity, and push cycle) avoids extra process tax on a file already in the index.
- **(c) Simplest path**: Yes. Letting `roles.prun-worker.grok` inherit `model` from `families.grok` (matching `roles.worker.grok` and `roles.prun-worker.codex`), supplying a dedicated fixture through `AGENT_MODELS_FILE` in `DispatchGrokHarness` (matching `tests/test_dispatch_task_grok.py`), and asserting the resolver's exact `"registry has no families.grok row"` diagnostic is the cleanest path.

## Findings

### New

- **[Low]** `skills/agent-models/SKILL.md:91` (with context at line 94) - In `## Change a model or an effort`, Step 2 (line 88) is updated to include the two Grok dispatcher test suites, both of which now run against synthetic `AGENT_MODELS_FILE` fixtures rather than `user/agent-models.json`. That leaves Step 5 (`Run doctor, then verify. ... Run one /vet both round`) as the only step that tests whether a newly set model string exists on the live account (`skills/agent-models/SKILL.md:94`: *"A model that does not exist for the account fails at step 5, not before, so do not skip it."*). However, `doctor_checks()` ignores Grok, bare `agent_models.py verify` checks only `REQUIRED_FAMILIES` (`claude`, `codex`, `agy` at `scripts/agent_models.py:1235`), and `/vet both` dispatches Codex and Antigravity. Following Steps 1 through 6 after a Grok edit therefore never invokes Grok unless Step 5 calls out `verify --family grok` (already documented in the table at `skills/agent-models/SKILL.md:36`).
  - Suggested edit at `skills/agent-models/SKILL.md:91`:
    `5. Run doctor, then verify (and verify --family grok when Grok changed). Start a new Claude session, since an open one keeps its startup effort. Run one /vet both round and check the review-model records.`

- **[Low]** `skills/agent-models/SKILL.md:22` - Rule 5 lists three pairs of per-run overrides (`CODEX_DISPATCH_MODEL` / `CODEX_DISPATCH_REASONING`, `ANTIGRAVITY_DISPATCH_MODEL` / `ANTIGRAVITY_DISPATCH_EFFORT`, `GROK_DISPATCH_MODEL` / `GROK_DISPATCH_EFFORT`) and ends with: *"The Antigravity and Grok variables are read by both `/vet` and `prun`."* Naming two of the three pairs implies that `CODEX_DISPATCH_MODEL` and `CODEX_DISPATCH_REASONING` apply only to `/vet`, whereas `skills/prun/scripts/dispatch-task.sh:25-26,237-238`, `skills/prun/scripts/dispatch-task.ps1:13-14,224-225`, and `skills/prun/SKILL.md:337` read both Codex variables in `prun` too.
  - Suggested edit at `skills/agent-models/SKILL.md:22`: replace `The Antigravity and Grok variables are read by both \`/vet\` and \`prun\`.` with `All six variables are read by both \`/vet\` and \`prun\`.`

### Previously raised

None.
