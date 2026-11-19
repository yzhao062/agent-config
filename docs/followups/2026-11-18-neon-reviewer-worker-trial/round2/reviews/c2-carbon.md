<!-- Round 1 -->
Intended file: `Review-Antigravity.md`

## Verification notes

Executed from `/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-270197b0-round1-12585-43164bd3d12f4c73/staged-snapshot`:

1. `"$HOME/miniforge3/envs/py312/bin/python" -m unittest tests/test_skill_size.py tests/test_skill_md_contract.py tests/test_style_audit.py tests/test_pointer_files.py tests/test_bootstrap_size.py tests/test_check_parity.py`
   Outcome: exit `0`, ran `159` tests in `7.050s` (`OK`). Confirmed `skills/implement-review/SKILL.md` passes size ceiling, Reference Index, Phase 1b numbering/reference, prompt template, and Round checklist line/byte/slug checks.
2. `"$HOME/miniforge3/envs/py312/bin/python" -m unittest tests/test_prompt_byte_parity.py tests/test_health_check.py tests/test_classify_reviewer_io.py`
   Outcome: exit `0`, ran `120` tests in `5.359s` (`OK`, `skipped=8`).
3. `"$HOME/miniforge3/envs/py312/bin/python" skills/implement-review/scripts/style-audit.py CHANGELOG.md skills/implement-review/SKILL.md`
   Outcome: exit `0`; `0` findings on the newly added or modified lines in either file (`15` pre-existing advisory findings elsewhere in the two files).
4. `wc -c skills/implement-review/SKILL.md CHANGELOG.md`
   Outcome: exit `0`; `skills/implement-review/SKILL.md` is `65597` bytes (`196` bytes below the `65793`-byte ceiling in `tests/test_skill_size.py:34` and well within `RATCHET_SLACK = 4096`), `CHANGELOG.md` is `25845` bytes.
5. `grep -rn "DEFAULT_CHANNEL\|DEFAULT_REVIEWER\|IMPLEMENT_REVIEW" scripts/ user/` and `grep -rn "DEFAULT_REVIEWER\|DEFAULT_CHANNEL" skills/ scripts/ tests/ .claude/`
   Outcome: confirmed that no executable script in `scripts/` or `skills/implement-review/scripts/` reads or prints `IMPLEMENT_REVIEW_DEFAULT_CHANNEL` or `IMPLEMENT_REVIEW_DEFAULT_REVIEWER`; only prose in `skills/implement-review/SKILL.md`, `skills/implement-review/references/grok-backend.md`, and `.claude/commands/{vet,implement-review}.md` references them.
6. `"$HOME/miniforge3/envs/py312/bin/python" -m unittest tests/test_prompt_byte_parity.py tests/test_repo.py tests/test_line_endings.py`
   Outcome: `test_prompt_byte_parity.py` passed; `test_repo.py` and `test_line_endings.py` failed with `git ls-files` exit `128` (`fatal: not a git repository`) as expected inside the `.git`-free exported staged snapshot.

Verification status: VERIFIED

## Scope and lens

- **Files in scope**: `CHANGELOG.md`, `skills/implement-review/SKILL.md` (staged diff).
- **Out of scope**: nothing beyond the files changed.
- **Review lens**: Code and its documentation (correctness, edge cases, behavior change for existing inputs, tests, internal consistency and consistency with neighboring files, maintainability).

## Scope challenge

- **(a) Why this exact scope, smaller vs. marginally larger**:
  - *Pain closed*: On 2026-11-17, a coordinator read all of `skills/implement-review/SKILL.md`, ran a bare `/vet` under `IMPLEMENT_REVIEW_DEFAULT_REVIEWER=both`, dispatched Codex alone for three rounds, and emitted no channel line. The diff removes two real prose defects: Step 3 of the Round checklist omitted the channel-line requirement and the rule against narrowing the resolved reviewer set, while Section 1c carried a competing `Expected reviewer set` rule whose third branch fell back to `{Codex}` without consulting `IMPLEMENT_REVIEW_DEFAULT_REVIEWER`.
  - *Could a smaller scope close most of it?* No. Updating Step 3 without Section 1c leaves the `{Codex}` fallback contradicting Step 3 at prompt-assembly time; updating Section 1c without Step 3 leaves the top-of-file checklist silent on both channel-line output and set fidelity, while the Path selection trim (`skills/implement-review/SKILL.md:140,146`) is needed to stay below the `65793`-byte ceiling.
  - *Could a marginally larger scope close all of it for low cost?* Yes. A coordinator that already read the whole file still missed `IMPLEMENT_REVIEW_DEFAULT_REVIEWER=both` because neither Claude Code nor Codex injects arbitrary user `env` keys into model prompt context, and no script run during `/vet` (`agent-quota.py`, `style-audit.py`, `dispatch-*`) reads or prints `IMPLEMENT_REVIEW_DEFAULT_CHANNEL` or `IMPLEMENT_REVIEW_DEFAULT_REVIEWER`. Within the current two-file scope, telling the agent in `skills/implement-review/SKILL.md:121` to run a shell lookup of both variables when tokens are omitted closes the visibility gap at near-zero cost (Finding 2 below). A marginally larger ~40-line Python helper (or a flag on an existing `/vet` script) that takes `--coordinator <id> --args "$ARGUMENTS"`, reads both env vars plus `PATH` probes, and prints the exact `Channel:` lines and normalized `EXPECTED_REVIEWERS` list would make set resolution deterministic and unit-testable (`AGENTS.local.md:10`) while freeing prose bytes in `SKILL.md`.
- **(b) Deferrals vs. process tax**:
  - The request declares nothing deferred beyond the two changed files. Leaving env-var discovery implicit in prose carries real risk of a repeat single-reviewer run and another full fix + `/vet` + `anywhere-agents` parity sync cycle (`scripts/check-parity.sh:30` marks `skills/implement-review` as cross-repo `STRICT`). At minimum, the explicit shell lookup in `skills/implement-review/SKILL.md:121` belongs in this change now rather than a later round-trip.
- **(c) Is this plan the simplest path?**
  - Making Step 3 the single authority for the resolved reviewer set and pointing Section 1c at Step 3 is the simplest prose design. Its main limitation is treating an invisible-environment blind spot purely as an instruction-following problem; pairing the single-authority prose with an explicit shell read of `IMPLEMENT_REVIEW_DEFAULT_CHANNEL` and `IMPLEMENT_REVIEW_DEFAULT_REVIEWER` (or a tiny resolver helper) is the simplest path that actually prevents recurrence.

## New

1. **[Medium] `skills/implement-review/SKILL.md:191` — Section 1c's new `Expected reviewer set` wording conflates per-round failover addition with cross-round persistence and slot replacement.**
   `skills/implement-review/SKILL.md:191` states:
   > `- **Expected reviewer set**: the set step 3 resolved, carried into later rounds until the user changes it for this review or a failure path replaces a reviewer.`

   This wording contradicts the failover and consolidation contracts in two ways:
   - **Cross-round persistence**: Under `skills/implement-review/SKILL.md:225`, `skills/implement-review/SKILL.md:235`, and `skills/implement-review/references/failover-and-recovery.md:12-14`, backend failover is scoped strictly to the failing round (`Maintain a failover queue for the round`, `final for that backend this round`, `Do not set sticky downgrade in that case`). Only a total automatic failure that falls back to Terminal-relay sets sticky downgrade across rounds (`skills/implement-review/SKILL.md:226`). Saying the Step 3 set is `"carried into later rounds until ... a failure path replaces a reviewer"` implies that a Round 1 failover (for example, `Codex` failing over to `Antigravity` in Round 1) replaces `Codex` in Round 2+, or leaves Round 2's set unspecified once `until` triggers.
   - **Same-round consolidation (`add` vs. `replace`)**: Within the round where a reviewer fails, `skills/implement-review/SKILL.md:140` keeps the originally expected set for consolidation so surviving reviews are classified against it (`Single-source` if one of `both` fails with no eligible replacement left), while `skills/implement-review/references/failover-and-recovery.md:10` instructs the coordinator to **add** a failover backend to that round's expected set rather than overwrite the original slot.

   Suggested rewrite for `skills/implement-review/SKILL.md:191` (`+12` bytes, keeping `SKILL.md` `184` bytes under its `65793`-byte ceiling):
   ```markdown
   - **Expected reviewer set**: the set step 3 resolved, carried into later rounds unless the user changes it for this review. A failover replacement joins that round's set only. If the set is still unclear, ask the user which reviewers they plan to invoke before presenting the prompt.
   ```

2. **[Medium] `skills/implement-review/SKILL.md:41` and `skills/implement-review/SKILL.md:121-123` — Neither Step 3 nor Path selection instructs the coordinator to query `IMPLEMENT_REVIEW_DEFAULT_CHANNEL` and `IMPLEMENT_REVIEW_DEFAULT_REVIEWER` in the shell.**
   Claude Code and Codex export `~/.claude/settings.json` (`env`) and `~/.codex/config.toml` (`[shell_environment_policy] set`) into tool subprocesses, and neither host prints those variables into the model's prompt context. No script invoked during `/vet` outputs them either. In `skills/implement-review/SKILL.md:121`, the third-person explanation (`Read the variable once at Phase 1c entry. Claude Code reads it from the env block of ~/.claude/settings.json, and Codex from [shell_environment_policy] set in ~/.codex/config.toml`) reads like passive host behavior rather than a shell command the coordinator must run. Unlike Steps 1, 2, 6, and 7, Step 3 gives no concrete lookup, so a coordinator handling a bare `/vet` can assume unset defaults without ever inspecting the live shell environment.
   Suggested edit at `skills/implement-review/SKILL.md:121` (or briefly in `skills/implement-review/SKILL.md:41`): instruct the coordinator to query `${IMPLEMENT_REVIEW_DEFAULT_CHANNEL-}` and `${IMPLEMENT_REVIEW_DEFAULT_REVIEWER-}` in the shell once at Phase 1c entry whenever the invocation omits channel or reviewer tokens (trimming the redundant third-person `reads it` phrasing so total file size stays under `65793` bytes).

3. **[Low] `skills/implement-review/SKILL.md:41` and `skills/implement-review/SKILL.md:146` — Multi-reviewer channel-line cardinality and post-dispatch failure timing do not quite line up.**
   - `skills/implement-review/SKILL.md:41` requires emitting `"one channel line per reviewer"` before dispatch (matching `skills/implement-review/SKILL.md:132`, `"The channel lines"`), whereas Hunk 2 rewrites `skills/implement-review/SKILL.md:146` to singular `"The channel line goes out at Phase 1c entry"` and shows the `both` case only as the bare fragment `both → codex agy (coordinator: claude; IMPLEMENT_REVIEW_DEFAULT_REVIEWER=both)` without `Channel:` or per-reviewer `PATH` status. Pluralizing `"Channel lines go out at Phase 1c entry"` in `skills/implement-review/SKILL.md:146` keeps it aligned with Step 3.
   - `skills/implement-review/SKILL.md:41` says `"before dispatching emit one channel line per reviewer... Only the user's words for this review, or a rewrite or failure path this file defines, change it, and the line then names that reviewer and why"` (mirrored in `CHANGELOG.md:25`). Pre-dispatch self-review rewrites and preflight probe absences happen before dispatch, whereas a runtime failure path happens after dispatch and emits a separate takeover line (`skills/implement-review/references/failover-and-recovery.md:10`). Changing `"and the line"` to `"and that line or a failover line"` avoids implying the pre-dispatch line reports post-dispatch failures.

## Previously raised

None.

Commit verdict: PASS
