<!-- Round 1 -->

Intended file: `Review-Antigravity.md`

## Verification notes

All commands ran from the disposable staged snapshot (`/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-85af83a4-round1-12566-13e8da9df5174efb/staged-snapshot`) using `$HOME/miniforge3/envs/py312/bin/python` (Python 3.12.14).

- `agy models`: exited 0. Confirmed the live Antigravity CLI lists `gemini-4-hydrogen-high`, `gemini-4-hydrogen-xhigh`, `gemini-4-hydrogen-medium`, and `gemini-4-hydrogen-low` (display names `Gemini 4 Hydrogen (High/XHigh/Medium/Low)`), as well as `gemini-4-neon-{high,xhigh,medium,low}`, `gemini-4-argon-{low,medium,high}`, `gemini-4-carbon-{low,medium,high}`, and `claude-sonnet-5-5-{low,medium,high}`.
- `agy --help`: confirmed `--effort` accepts `(low|medium|high|xhigh|max)`.
- `$HOME/miniforge3/envs/py312/bin/python scripts/agent_models.py show`: exited 0. Confirmed `agy` resolves to `interactive=gemini-4-argon-high` (fallback `gemini-4-hydrogen-high`), `reviewer=gemini-4-carbon-medium` (fallbacks `gemini-4-argon-high>gemini-4-hydrogen-high`), `worker=gemini-4-hydrogen-high`, and `prun-worker=gemini-4-hydrogen-high` (`second_slug=claude-sonnet-5-5-high`).
- `$HOME/miniforge3/envs/py312/bin/python scripts/agent_models.py render --check`: exited 0 (`user/settings.json` is current).
- `$HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_agent_models.py`: exited 0 (106 tests, 1 skipped).
- `env -u ANTIGRAVITY_DISPATCH_MODEL -u ANTIGRAVITY_DISPATCH_EFFORT $HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_agent_models.py tests/test_dispatch_gemini.py tests/test_dispatch_task_agy.py tests/test_render_banner.py`: exited 0 (346 tests, 2 skipped). Note: running without unsetting the reviewer process's inherited `ANTIGRAVITY_DISPATCH_MODEL=gemini-4-neon-high` caused 68 pre-existing integration-test failures because `_run()` in those test suites does not strip `ANTIGRAVITY_DISPATCH_MODEL`.
- `env -u ANTIGRAVITY_DISPATCH_MODEL -u ANTIGRAVITY_DISPATCH_EFFORT $HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_prun_executors.py tests/test_prun_deployed_path.py tests/test_check_parity.py tests/test_skill_md_contract.py`: exited 0 (37 tests, 3 skipped).
- `$HOME/miniforge3/envs/py312/bin/python -m unittest discover -s tests -p "test_*.py" -v`: ran 1778 tests; the only failures outside inherited `ANTIGRAVITY_DISPATCH_MODEL` were 9 `test_repo.py` tests and 1 `test_line_endings.py` test that run `git ls-files` (expected in a non-git snapshot). Verified directly with Python that all four staged files use LF line endings.
- Direct unit check of `effort_for` in `skills/implement-review/scripts/dispatch-gemini.py` and `--print-model` with `ANTIGRAVITY_DISPATCH_MODEL=gemini-4-hydrogen-xhigh`: exited 0, printed `gemini-4-hydrogen-xhigh xhigh`.
- Direct reproduction against `skills/prun/scripts/dispatch-task-agy.py` using `tests/test_dispatch_task_agy.py`'s updated `MOCK_AGY` and a `gemini-4-hydrogen` worker registry: both a floated `MOCK_AGY_MODELS=gemini-4-hydrogen-xhigh` listing and an explicit `ANTIGRAVITY_DISPATCH_MODEL=gemini-4-hydrogen-xhigh` override exited 2 with `error: --model gemini-4-hydrogen-xhigh conflicts with --effort=high` and logged `dispatch-task-agy: MODEL-MISMATCH requested=gemini-4-hydrogen-xhigh high actual=gemini-4-hydrogen-xhigh xhigh`.

Verification status: VERIFIED

## Scope and lens

- **Staged files reviewed**: `skills/implement-review/scripts/dispatch-gemini.py`, `tests/test_dispatch_gemini.py`, `tests/test_dispatch_task_agy.py`, `user/agent-models.json`.
- **Context files inspected**: `AGENTS.local.md`, `scripts/agent_models.py`, `skills/prun/scripts/dispatch-task-agy.py`, `skills/agent-models/SKILL.md`, `tests/test_agent_models.py`.
- **Review lens**: Code and its documentation (correctness, edge cases, behavior change for existing inputs, test strength, cross-file consistency, maintainability), plus the mandatory scope-challenge evaluation.

## New

### High

1. **`skills/prun/scripts/dispatch-task-agy.py:1162` still omits `"xhigh"` from its slug-tier tuple, and `tests/test_dispatch_task_agy.py:1590` does not test `xhigh`**

   This change moves `roles.prun-worker.agy.model` in `user/agent-models.json` to `gemini-4-hydrogen` (which lists `gemini-4-hydrogen-xhigh`) and updates `MOCK_AGY` in `tests/test_dispatch_task_agy.py:149` to reject `--model <slug>-xhigh` when `--effort` differs from `xhigh`. However, the sibling Agy dispatcher in `skills/prun/scripts/dispatch-task-agy.py:1160-1163` was not updated:

   ```python
   if "ANTIGRAVITY_DISPATCH_EFFORT" not in os.environ:
       slug_tier = model.rsplit("-", 1)[-1]
       if slug_tier in ("low", "medium", "high", "max"):
           effort = slug_tier
   ```

   As reproduced against the updated mock (and matching the real Agy CLI), both `ANTIGRAVITY_DISPATCH_MODEL=gemini-4-hydrogen-xhigh` (with `ANTIGRAVITY_DISPATCH_EFFORT` unset) and a listing that floats `prun-worker` to `gemini-4-hydrogen-xhigh` pass `--effort high` and exit with code 2 (`error: --model gemini-4-hydrogen-xhigh conflicts with --effort=high`). This violates the documented contract in `skills/prun/SKILL.md:208` ("An unset `ANTIGRAVITY_DISPATCH_EFFORT` follows the chosen slug's tier, because Agy rejects a conflicting `--effort`").

   `tests/test_dispatch_task_agy.py:1590-1599` (`test_effort_follows_a_resolved_tier_other_than_high`) only checks `medium`, so the new `xhigh` check in `MOCK_AGY` at line 149 is never exercised by any test in that file and did not catch the missing fix.

   Exact rewrite for `skills/prun/scripts/dispatch-task-agy.py:1160-1163`:

   ```python
       if "ANTIGRAVITY_DISPATCH_EFFORT" not in os.environ:
           slug_tier = model.rsplit("-", 1)[-1]
           if slug_tier in ("low", "medium", "high", "xhigh", "max"):
               effort = slug_tier
   ```

   Exact rewrite for `tests/test_dispatch_task_agy.py:1590-1599` (using a distinct `result_path` per `subTest` because `dispatch-task-agy.py:1012` refuses an existing result file):

   ```python
       def test_effort_follows_a_resolved_tier_other_than_high(self) -> None:
           # The strict mock rejects a conflicting --effort, as Agy 1.2.16 does.
           for listing, slug, tier in (
               ("gemini-3.9-flash-medium\ngemini-3.9-flash-low", "gemini-3.9-flash-medium", "medium"),
               ("gemini-3.9-flash-xhigh", "gemini-3.9-flash-xhigh", "xhigh"),
           ):
               with self.subTest(tier=tier):
                   result, target = self._run(
                       result_path=self.root / f"unit-result-{tier}.md",
                       extra_env={"MOCK_AGY_MODELS": listing},
                   )
                   self.assertEqual(result.returncode, 0, result.stderr)
                   argv = json.loads((self.log / "args.json").read_text(encoding="utf-8"))
                   self.assertIn(slug, argv)
                   self.assertEqual(argv[argv.index("--effort") + 1], tier)
                   self.assertTrue(target.is_file())
   ```

### Medium

None.

### Low

1. **Duplicate slug-tier tuples lack a parity check between the two Agy dispatchers (and omit `"max"` in mock conflict checks)**

   `tests/test_dispatch_task_agy.py:1601` (`test_newest_in_family_copies_have_the_same_code`) enforces AST parity for `newest_in_family` across `dispatch-gemini.py` and `dispatch-task-agy.py` because the two skills deploy separately, while the slug-tier effort-following logic is a helper (`effort_for`) in `dispatch-gemini.py:371-378` and an inline block in `dispatch-task-agy.py:1160-1163`. That asymmetry allowed the two copies to diverge in this very change. Extracting `effort_for` in `dispatch-task-agy.py` (or adding a shared tier-following check alongside `newest_in_family`) would prevent future tier additions from drifting again. Separately, both mock conflict checks (`tests/test_dispatch_gemini.py:90` and `tests/test_dispatch_task_agy.py:149`) and `tests/test_dispatch_gemini.py:112` check `("low", "medium", "high", "xhigh")`, whereas `effort_for` and `agy --help` also list `"max"`; adding `"max"` to the mocks would keep them aligned with `agy --help`.

## Previously raised

None.

## Scope-challenge assessment

- **(a) Why this exact scope, and whether a smaller or marginally larger scope is better**:
  Moving the Agy `worker`, `prun-worker`, and family fallback rows from `gemini-3.8-flash` to `gemini-4-hydrogen` is well motivated, and fixing `xhigh` tier-following in the same change is necessary because `gemini-4-hydrogen` introduces an `xhigh` slug that triggers a real Agy CLI conflict when `ANTIGRAVITY_DISPATCH_EFFORT` is unset. A smaller scope (registry edit alone) would leave `ANTIGRAVITY_DISPATCH_MODEL=gemini-4-hydrogen-xhigh` broken. A marginally larger scope that also updates `skills/prun/scripts/dispatch-task-agy.py:1162` and `tests/test_dispatch_task_agy.py:1590` closes the entire `xhigh` problem for almost zero added cost, since `prun-worker` is one of the rows moved to `gemini-4-hydrogen` and `tests/test_dispatch_task_agy.py` is already in this diff.

- **(b) Is each deferred item worth its process tax versus inclusion now?**
  1. `skills/prun/scripts/dispatch-task-agy.py` + `xhigh` test in `tests/test_dispatch_task_agy.py`: Not worth deferring (and a defect as staged). Include now.
  2. `EFFORTS["agy"]` in `scripts/agent_models.py:69` (explicitly kept at `("low", "medium", "high")`): Deferring this is defensible but carries a clear trade-off. Keeping `xhigh` out of `EFFORTS["agy"]` prevents accidentally configuring `effort="xhigh"` on `gemini-4-argon` or `gemini-4-carbon`, which do not list `xhigh` tiers in `agy models`. On the other hand, `agy models` already ships `xhigh` on both `gemini-4-hydrogen` and `gemini-4-neon`, and `EFFORTS["claude"]` / `EFFORTS["codex"]` already allow model-specific top tiers (`max`, `ultra`) that not every model or row uses. Leaving `EFFORTS["agy"]` narrow guarantees a separate code, test, review, and parity cycle as soon as any Agy row wants `xhigh`. Because no row requests `xhigh` today and `scripts/agent_models.py` already handles `xhigh` in `AGY_TIERS` and `agy_actual`, keeping `EFFORTS["agy"]` unchanged is acceptable if that guardrail is intentional, though adding `"xhigh"` now would be a small, low-risk edit (~5 lines across `scripts/agent_models.py` and `tests/test_agent_models.py`).

- **(c) Is this the simplest path?**
  Fixing the registry and the tier-following tuple directly is the simplest path, provided both Agy dispatchers (`dispatch-gemini.py` and `dispatch-task-agy.py`) are updated together. Updating only `dispatch-gemini.py` while updating the mock in `tests/test_dispatch_task_agy.py` leaves the two dispatchers inconsistent and requires a second round anyway.

Commit verdict: BLOCK
