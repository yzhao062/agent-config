<!-- Round 1 -->

Intended file: `Review-Antigravity.md`

## Verification notes

All verification commands ran inside `/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot` with `$HOME/miniforge3/envs/py312/bin/python`:

- `$HOME/miniforge3/envs/py312/bin/python scripts/agent_models.py show && $HOME/miniforge3/envs/py312/bin/python scripts/agent_models.py render --check` -> exited `0`; `agy` `worker` and `prun-worker` resolve to `gemini-4-hydrogen` / `high` (`slug=gemini-4-hydrogen-high`), `agy` `interactive` and `premium` carry `fallback_slugs=gemini-4-hydrogen-high`, `agy` `reviewer` carries `fallback_slugs=gemini-4-argon-high>gemini-4-hydrogen-high`, and [settings.json](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/user/settings.json) matches the rendered registry.
- `$HOME/miniforge3/envs/py312/bin/python scripts/agent_models.py map .` -> exited `0`; confirmed readers of `agy/reviewer` ([dispatch-gemini.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/skills/implement-review/scripts/dispatch-gemini.py)) and `agy/prun-worker` ([dispatch-task-agy.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/skills/prun/scripts/dispatch-task-agy.py)).
- `agy --version && agy models` and `agy --help` -> exited `0` (Antigravity CLI `1.5.12`); confirmed `gemini-4-hydrogen-{low,medium,high,xhigh}` are listed by the live CLI and `--effort` accepts `(low|medium|high|xhigh|max)`.
- `agy --input-format stream-json --output-format stream-json --model gemini-4-hydrogen-xhigh --effort high </dev/null` -> exited `1` with zero turns (`--model gemini-4-hydrogen-xhigh conflicts with --effort=high`), confirming the live CLI conflict behavior modeled by `MOCK_AGY`.
- `$HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_agent_models.py tests/test_dispatch_gemini.py tests/test_dispatch_task_agy.py tests/test_render_banner.py` -> exited `1` (`68` failures) when `ANTIGRAVITY_DISPATCH_MODEL=gemini-4-carbon-medium` was inherited from the parent reviewer session; rerunning with `env -u ANTIGRAVITY_DISPATCH_MODEL -u ANTIGRAVITY_DISPATCH_EFFORT -u ANTIGRAVITY_BIN -u ANTIGRAVITY_PREFLIGHT $HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_agent_models.py tests/test_dispatch_gemini.py tests/test_dispatch_task_agy.py tests/test_render_banner.py` exited `0` (`346` tests, `2` skipped).
- `$HOME/miniforge3/envs/py312/bin/python -m unittest tests/test_prun_executors.py tests/test_bootstrap_size.py tests/test_skill_size.py` -> exited `0` (`7` tests).
- Static literal drift scan (`agent_models.scan` across all `320` non-allowlisted snapshot files, bypassing `git ls-files` in the index export) -> `0` hits.
- Reproduction against [dispatch-task-agy.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/skills/prun/scripts/dispatch-task-agy.py) using `MOCK_AGY` from [test_dispatch_task_agy.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/tests/test_dispatch_task_agy.py): both `ANTIGRAVITY_DISPATCH_MODEL=gemini-4-hydrogen-xhigh` (unset effort) and floating onto `MOCK_AGY_MODELS=gemini-3.8-flash-xhigh` exited `2` with `error: --model ... conflicts with --effort=high` and `MODEL-MISMATCH`; verified in a scratch copy that adding `"xhigh"` at `skills/prun/scripts/dispatch-task-agy.py:1162` makes both `medium` and `xhigh` pass with `returncode=0`.

Verification status: VERIFIED

## Scope and lens

- **Files in diff**: [dispatch-gemini.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/skills/implement-review/scripts/dispatch-gemini.py), [test_dispatch_gemini.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/tests/test_dispatch_gemini.py), [test_dispatch_task_agy.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/tests/test_dispatch_task_agy.py), [agent-models.json](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/user/agent-models.json).
- **Lens**: Code and documentation correctness, edge cases, behavior changes for existing inputs, test discrimination (failing on old code and catching regressions), cross-file consistency with neighboring dispatchers and docs, and maintainability.

### Scope challenge

- **(a) Why this scope / marginally larger scope**: Moving Agy general-worker and fallback stems from `gemini-3.8-flash` to `gemini-4-hydrogen` while teaching Agy dispatchers to follow `-xhigh` slugs is the right problem to close, because `gemini-4-hydrogen` introduces `xhigh` in `agy models`. However, the diff stops halfway across the two Agy dispatchers: it updates `MOCK_AGY` in [test_dispatch_task_agy.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/tests/test_dispatch_task_agy.py#L149) without updating the mirrored slug-tier check in [dispatch-task-agy.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/skills/prun/scripts/dispatch-task-agy.py#L1162) or its test at [test_dispatch_task_agy.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/tests/test_dispatch_task_agy.py#L1590-L1599). Adding that one-token script edit and companion subtest closes the entire `ANTIGRAVITY_DISPATCH_MODEL=...-xhigh` failure mode across both `/vet` and `prun` for near-zero cost.
- **(b) Deferred items vs. process tax**: Keeping `EFFORTS["agy"] = ("low", "medium", "high")` in [agent_models.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/scripts/agent_models.py#L69) is sound and should remain out of scope here. In `agy models` (`1.5.12`), only `neon` and `hydrogen` expose `xhigh`, whereas `argon`, `carbon`, and `flash` stop at `high`. Accepting `xhigh` in `EFFORTS["agy"]` without per-family tier checks would let `agent_models.py set --family agy --effort xhigh` write `gemini-4-argon-xhigh`, which floats back to `high` during `sync` and triggers `doctor` drift (`agy_family_state` compares the requested `xhigh` tier against the installed `high` label). By contrast, deferring the `dispatch-task-agy.py` half of slug-tier `xhigh` handling is not worth another review and parity cycle when `test_dispatch_task_agy.py` is already staged.
- **(c) Simplest path**: Updating the registry stems and adding `"xhigh"` to both dispatchers' slug-tier tuples (plus their existing tier-following tests) is the simplest path.

## New

### 1. [High] `prun` dispatcher omits `xhigh` in its mirrored slug-tier check, leaving `test_dispatch_task_agy.py:149` unexercised and breaking `prun` on `-xhigh` slugs

[SKILL.md](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/skills/agent-models/SKILL.md#L22) states that `ANTIGRAVITY_DISPATCH_MODEL` and `ANTIGRAVITY_DISPATCH_EFFORT` are read by both `/vet` and `prun`, and `roles.prun-worker.agy` is one of the rows moved to `gemini-4-hydrogen` in [agent-models.json](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/user/agent-models.json#L52-L54). The staged diff updates `effort_for` in [dispatch-gemini.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/skills/implement-review/scripts/dispatch-gemini.py#L376) and updates `MOCK_AGY` in [test_dispatch_task_agy.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/tests/test_dispatch_task_agy.py#L149) to reject a conflicting `--effort` on `xhigh` slugs, yet [dispatch-task-agy.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/skills/prun/scripts/dispatch-task-agy.py#L1160-L1163) still checks `slug_tier in ("low", "medium", "high", "max")` without `"xhigh"`.

As a result:
1. Running `prun` with `ANTIGRAVITY_DISPATCH_MODEL=gemini-4-hydrogen-xhigh` (and `ANTIGRAVITY_DISPATCH_EFFORT` unset), or floating onto an `xhigh`-only model listing, leaves `effort` at `"high"`, passes `--model ...-xhigh --effort high` to `agy`, exits non-zero on the CLI flag conflict, and emits a false `MODEL-MISMATCH requested=...-xhigh high actual=...-xhigh xhigh`.
2. In [test_dispatch_task_agy.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/tests/test_dispatch_task_agy.py#L149), the staged `"xhigh"` mock change is dead test code because `test_effort_follows_a_resolved_tier_other_than_high` at `tests/test_dispatch_task_agy.py:1590-1599` only tests `medium`.

Exact rewrite for `skills/prun/scripts/dispatch-task-agy.py:1160-1163`:

```python
    if "ANTIGRAVITY_DISPATCH_EFFORT" not in os.environ:
        slug_tier = model.rsplit("-", 1)[-1]
        if slug_tier in ("low", "medium", "high", "xhigh", "max"):
            effort = slug_tier
```

Exact rewrite for `tests/test_dispatch_task_agy.py:1590-1599` (using a distinct `result_path` per iteration because `dispatch-task-agy.py` refuses an existing result file):

```python
    def test_effort_follows_a_resolved_tier_other_than_high(self) -> None:
        # The strict mock rejects a conflicting --effort, as Agy 1.2.16 does.
        for listing, tier in (
            ("gemini-3.9-flash-medium\ngemini-3.9-flash-low", "medium"),
            ("gemini-3.9-flash-xhigh", "xhigh"),
        ):
            with self.subTest(tier=tier):
                result, target = self._run(
                    result_path=self.root / f"unit-result-{tier}.md",
                    extra_env={"MOCK_AGY_MODELS": listing},
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                argv = json.loads((self.log / "args.json").read_text(encoding="utf-8"))
                self.assertIn(f"gemini-3.9-flash-{tier}", argv)
                self.assertEqual(argv[argv.index("--effort") + 1], tier)
                self.assertTrue(target.is_file())
```

### 2. [Low] `_run` helpers in both Agy dispatcher test files inherit `ANTIGRAVITY_DISPATCH_*` from the parent environment

In [test_dispatch_gemini.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/tests/test_dispatch_gemini.py#L1437-L1438), `_print_model` strips `ANTIGRAVITY_DISPATCH_MODEL`, `ANTIGRAVITY_DISPATCH_EFFORT`, and `ANTIGRAVITY_PREFLIGHT` from `os.environ.copy()` before applying `extra_env`. `_run` in [test_dispatch_gemini.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/tests/test_dispatch_gemini.py#L873-L890) and `_run` in [test_dispatch_task_agy.py](file:///var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-a50855a9-round1-12563-2c7d9a64aa154b69/staged-snapshot/tests/test_dispatch_task_agy.py#L851-L883) do not strip those three variables. When these suites are executed from an Antigravity-dispatched session or shell where `ANTIGRAVITY_DISPATCH_MODEL` is set, 68 integration tests fail preflight against the mock model list instead of exercising the fixture registries. Popping those three keys before applying `extra_env` in both `_run` helpers makes the suites self-contained in all environments.

## Previously raised

None.

Commit verdict: BLOCK
