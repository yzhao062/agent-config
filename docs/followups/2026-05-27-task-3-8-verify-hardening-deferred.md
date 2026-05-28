# 2026-05-27: Task 3.8 (verify hardening for stale pointers) deferred from Phase 3

Status: deferred to its own plan-review + implement cycle.

## What's deferred

Task 3.8 of `2026-05-27-issues-6-7-8-9-plan.md` would have added a two-tier pointer-content check in `packages/pypi/anywhere_agents/cli.py` so `anywhere-agents pack verify` detects stale `.claude/commands/<name>.md` pointers (those still carrying the OLD 2-path lookup text after the v0.7.x → vNext upgrade).

The check has two surfaces:

- **`role == "generated-command"`** (composer auto-emits the pointer): if the deployed pointer lacks `.claude/skills/<name>/`, mark the pack state `_VERIFY_STATE_POINTER_STALE` and return non-zero from `_pack_verify`. The composer's template owns the output, so a missing substring means real drift; `--fix` re-emits.
- **Any other role** (verbatim file copy from explicit pointer mappings, e.g., aa's 4 bundled pointers): emit a row-level WARN naming the file path and guidance "update upstream pointer text in the source pack". Non-blocking (exit code unchanged), because the verbatim path includes custom prose (e.g., `argument-hint` in `implement-review.md`) that auto-rewrite would clobber.

## Why this is deferred

1. **User pain from issue #6 is already closed by Tasks 3.2-3.7 + the Phase 3 Round 4 apply-path fix.** New pack deployments emit 3-path pointers via the updated `_POINTER_TEMPLATE` (`scripts/packs/handlers/skill.py:41-48` + `v1 → v2` template tag at line 175). The 12 currently-committed pointer files (4 aa-bundled + 8 ac-bundled) were also edited to 3-path text. **Existing deployments with v1 generated-command pointers** are now classified as `PRESTATE_PACK_OUTPUT` (not `PRESTATE_UNMANAGED`) by `_build_prior_pack_outputs` in `scripts/compose_packs.py:190-203`, which seeds `known_shas` from `output_sha256` for `role: "generated-command"` entries (review Round 4 fix). Both surfaces (fresh installs and v1-to-v2 upgrades) apply cleanly through the normal compose path; no manual intervention required.
2. **Implementation surface is non-trivial.** Adds 1 new state constant, 1 new state-icon entry, a new lock-inspection helper, integration into `_pack_verify` between `_verify_gather` and the row classifier, and the WARN-vs-blocking branching. Two new test fixtures (`tests/test_packs_cli_v0_6.py`) need to build a temp consumer with `.agent-config/pack-lock.json`, `agent-config.yaml`, user config, and a deployed pointer with stale text.
3. **WARN-row classification is a new design surface.** Existing verify rows are either OK or some "bad" state; introducing a third bucket (WARN that is visible to the user but not counted as `bad`) deserves its own plan-review to nail down the row shape, the stdout phrasing, and the interaction with `--fix`.
4. **Risk of an incomplete or shoddy 3.8 is higher than the value of delivering it now.** A half-baked check that misclassifies generated-command rows OR emits noisy WARNs every verify run is a regression vector; better to land it deliberately.

## Re-entry checklist

When the next pass picks this up:

1. Re-read this followup plus `pack-architecture.md` § "STRICT parity trajectory" and § "pack verify" if it exists yet.
2. Decide whether the WARN row also belongs in the new row-state machine vs the existing `_VERIFY_STATE_*` enum. Either is workable; the WARN-as-state route is cleaner if other future warnings ride the same surface.
3. TDD: write the 2 tests from the original Task 3.8 spec verbatim. They are well-bounded.
4. Implement minimally; do not bundle in unrelated cli.py work.
5. Mirror `cli.py` to `packages/pypi/anywhere_agents/composer/cli.py` (aa-internal STRICT, enforced by `check-parity.sh:212+`).
6. Run `bash scripts/check-parity.sh` to confirm STRICT clean.

## What landed in Phase 3 without Task 3.8

- `_POINTER_TEMPLATE` 2-path → 3-path (`aa/scripts/packs/handlers/skill.py:41-48`).
- Template version bump `aa-composer-skill-pointer-v1` → `v2` (line 175).
- 12 committed `.claude/commands/*.md` pointer files edited to 3-path text (4 in aa, 8 in ac).
- `skills/implement-review/SKILL.md` script-lookup lines at :235 / :243 / :269 now name the 3-path order; STRICT byte-identical between ac, aa, and aa's wheel-bundled composer mirror.
- New `tests/test_pointer_files.py` regression test asserts every committed pointer file carries the 3-path lookup in correct order. Added to `strict_test_files` in `scripts/check-parity.sh` so future drift fails parity.
- `tests/test_packs_handlers_skill.py::test_directory_only_skill_auto_emits_pointer` extended to assert the 3-path order.
- `scripts/compose_packs.py:_build_prior_pack_outputs` now seeds `known_shas` from `output_sha256` for `role: "generated-command"` lock entries (mirrored to the wheel composer). Two new regression tests in `tests/test_drift_gate_skill_dir.py::GeneratedCommandPointerPriorOutputsTests` cover the apply path so a v1 → v2 template bump rewrites existing v1 pointers as `PRESTATE_PACK_OUTPUT` instead of failing through `PRESTATE_UNMANAGED`.
