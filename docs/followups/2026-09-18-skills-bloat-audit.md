# Are `implement-review` and `prun` bloated? An audit (2026-09-18)

Six read-only Antigravity units (Gemini 3.8 Flash through `prun`, 5 to 10 minutes each) measured the two skills. Their inputs: a throwaway clone at `f7a41c2`, 60 days of Claude Code transcripts (483 files, 5,205 extracted events), 14 dispatched Codex reviewer rollouts, and 12 Antigravity review rounds. Unit results are in the session scratchpad under `prun-skills-audit/agent-io/result-U1.md` to `result-U6.md`; this note keeps the numbers that decide something. The saving plan built from it is `PLAN-skills-diet.md` at the repository root.

## Verdict

Yes on both counts, and the two problems have different sizes.

- **Bloated**: `skills/implement-review/SKILL.md` is 137,076 bytes (15 KB in April, 83 KB in June, 104 KB in August). Forty-three percent of it describes how the scripts work inside rather than what the coordinator or the reviewer must do. `skills/prun/SKILL.md` is 36,473 bytes and 62 percent mechanism. Every `/vet` loads the first file whole, about 34k tokens, before any work starts; 192 invocations in 60 days.
- **Inefficient, by a larger margin**: a dispatched Codex review round ingests about 2.6 MB of tool output, and 40 percent of it is the reviewer reading files it does not need. Those files are the coordinator's own SKILL.md and example reviews (35 percent), `AGENTS.md` and `AGENTS.local.md` from disk although the rules were injected (5 percent), and the diff and the same source files several times over. At 4 bytes per token that is roughly 250k avoidable tokens per round on the Codex pool, over 449 measured rounds. The Antigravity reviewer shows a different but comparable pattern. Fifty-eight percent of its 408 KB of tool payload per round is repeated reads and hunting for `AGENTS.md`. Its prompt carries the full staged diff (107 KB per round on average) although the same diff sits in the snapshot it is told to use.
- **Dead weight**: prun's legacy Codex dispatchers and reaper (32.5 KB) have run zero times since `dispatch-task-agy.py` replaced them on 2026-09-13 (656 runs before), `gather` ran four times in 60 days, and the Claude reviewer backend (47 KB, kept by the Agent Roles rule) ran once. The `health-check` launchers are in use (143 calls). Thirty-four percent of all script bytes are comments, 42 KB of which are tutorial and incident narrative.
- **Housekeeping**: 1,881 `implement-review-*` state directories (18.6 GB, staged snapshots included) and 1,574 `prun-task-*` directories (1.6 GB) sit under `%TEMP%` with no expiry.

## Evidence

### Size and growth

| File or tree | Bytes | Composition (measured) | Growth |
|---|---|---|---|
| `implement-review/SKILL.md` | 137,076 | coordinator contract 50%, mechanism 43%, reviewer contract 4%, examples and rationale 2% (U1, fine-grained) | 6.5 KB (2026-03-31) to 137 KB in 47 commits; the five largest additions are the Auto-terminal channel and health-check prologue (+17.8 KB), the four-channel hardening (+13.0 KB), the `await-review` protocol (+9.2 KB), multi-reviewer (+8.4 KB), the Claude backend (+7.0 KB) |
| `implement-review/scripts/` (17 files) | 294,239 | 6 shell/PowerShell twin pairs, 4 Python modules, one guard helper; comments 95,369 B (34%) | |
| `implement-review/references/` | 36,161 | lenses 14 KB, four example reviews 22 KB | |
| `prun/SKILL.md` | 36,473 | mechanism 62%, coordinator contract 26%, rationale 8%, worker contract 5% (U3) | 8.8 KB (2026-06-26) to 36 KB in 25 commits |
| `prun/scripts/` (13 files) | 130,918 | one Python dispatcher (40 KB), one state module (29 KB), the rest shell twins and launchers | |

Duplication inside implement-review (U1): about 56.8 KB of SKILL.md restates its scripts. The health-check prologue (16.0 KB) repeats the ten checks, three heuristics, and regex lists of `health-check.py`. The Auto-terminal section (14.9 KB) repeats the flags and Windows workarounds in `dispatch-codex.{sh,ps1}`. The "script contract invariants" block (8.5 KB) repeats state-dir lifecycle and timing constants, and the three backend sections (18.5 KB) repeat their dispatchers' headers. Across the scripts, four observers (`auto-watch`, `stall-watch`, `await-review`, `health-check`) each re-implement round-marker validation, tail growth and stall tracking, stream-failure scanning, and verdict extraction: about 410 shared lines (U2).

### Usage in 60 days (U4; real executions, mentions excluded)

| Measure | Value |
|---|---|
| Skill invocations | `/vet` 115, `/implement-review` 77, `/prun` 94; `both` 34, `auto` 33, `agy` 1 |
| Reviewer dispatches | Codex 565 runs (median 15.3 min per round, p90 27.7), Agy 37 runs (median 4.8 min, p90 13.8), Copilot 6, Claude 0 to 1 |
| Rounds per review (161 reconstructed runs) | median 2, mean 4.8, p90 11, max 36 |
| Re-dispatch of the same round within an hour | 97 of 573 dispatches (16.9%): 23 guard denials of compound `cd` retried in under a minute, early exit codes, stalls, backend fallback |
| Health check (441 runs) | all pass 63%, warnings only 30%, a hard failure 6.6%; the warning is check 7 (suspicious phrases, 32%) or check 8 (tail failure markers, 20%); the hard failures are the round marker (11), freshness (9), verdict line (7) |
| Where a round's wall-clock goes | 95 to 98 percent model generation; polling and the health check are under one percent; retries add about 40 seconds of expected delay per round |
| prun | 97 Agy units in 49 runs (71% single-unit runs, p90 five units); legacy `dispatch-task.{sh,ps1}` 656 runs before 2026-09-13 and zero after; `gather.sh` 4 runs, `gather.ps1` 0, `reap-watch.ps1` 0, `report-state`/`snapshot-tail` 0 outside tests |
| Flags never seen in a command | `await-review --poll/--idle/--round-budget` and most `style-audit` options appear only in tests; the environment variables absent from transcripts (`ANTHROPIC_BASE_URL`, `CLAUDE_CODE_USE_*`, `MAMBA_ROOT_PREFIX`, the `*_REEXEC`/`*_SOURCE_DIR` internals) are live interfaces all the same: a credential-mode switch in `dispatch-claude`, an environment input to interpreter discovery, and re-exec guards the scripts set themselves. Plan-review round 1 corrected the first draft's reading of this row as dead code |

### What the reviewers receive and read

Codex (U5, 11 review rollouts of three multi-agent rounds plus 3 probes). Per round the reviewer receives about 57 to 104 KB of injected instructions (the composed `AGENTS.md`; 104 KB before the diet, 57 KB after) and 2.62 MB of tool output. The tool output splits into skill docs 35% (SKILL.md, `references/example-reviews/`), source files 24% (the same section read up to eight times by sub-agents), diff 23% (read two to three times), other 10% (its own `Review-Codex.md` re-read), rules 5% (`AGENTS.md`, `AGENTS.local.md`), and tests and builds 3%. The triggers are in our own text. The prompt template says "See `.claude/skills/implement-review/references/example-reviews/` for expected depth". The injected rules say "Before starting a task, read the router skill" and "Read `AGENTS.local.md` after `AGENTS.md`". The developer instruction says "Follow all other project instructions". Codex spawns sub-agents for a large diff, and each one repeats the reads. One rollout confirms the budget mechanism: a probe without `project_doc_max_bytes=262144` was cut at 34,323 bytes.

Antigravity (U6, 12 rounds). The prompt averages 114 KB, of which 107 KB is the embedded staged diff, while the preamble also points the reviewer at a snapshot directory. Tool payload is 408 KB per round, 58 percent of it avoidable: repeated reads of the same source files (38%), searching the tree for `AGENTS.md` because a focus item names "the writing rules of AGENTS.md" without the list (10%), reading its own past step files after a failed web fetch (10%), and skill docs (0.5%). Per-round wall-clock is a third of Codex's.

## What this rules out

- **Not the observers or the health check.** They cost under one percent of a round. Merging the four observers is a code-quality task, not a speed or token task.
- **Not the injected rules.** U5 proposed replacing the injected `AGENTS.md` with a 2 KB reviewer prompt. Rejected. The reviewer writes prose and runs commands under the same Writing Defaults and Git Safety rules as every agent; `dispatch-codex` raises the byte budget precisely so the whole file reaches it; and the file is 57 KB after the 2026-09 diet. The waste is the re-reads, not the injection.
- **Not `dispatch-claude`.** Zero to one run in 60 days, but the shared rules (Agent Roles) require the cross-vendor equivalent of `dispatch-codex` to stay wired. It stays; its 47 KB is a candidate for a Python merge later, not for deletion.

## Saving plan

`PLAN-skills-diet.md` turns this into three milestones, each gated by `/vet both`; plan-review reached PASS from Codex and Antigravity in round 3 on 2026-09-18. The contract-preserving set, in the order of tokens saved (risk per milestone is in the plan: A and the main B extractions medium, C low):

1. Milestone A, reviewer contract (prompt and dispatcher text, one registered test edit, one sentence in `AGENTS.md`). Tell the reviewer that its task, lens, and format are supplied: skip the router and the coordinator's skill tree, do not re-read injected rules, obtain the diff once (by the selected command on the Codex path, from the prompt on the embedded paths), and read a source or instruction file only when it is in scope or answers a verification question. Local policy (`AGENTS.local.md`) still applies. For a snapshot backend (Antigravity), the coordinator pastes a gitignored plan, an untracked note, or an untracked local override into the request once, because `git checkout-index` does not export them. Drop the example-reviews pointers. Inline the banned-word list when a focus item names it. For Antigravity, keep the diff and present the snapshot as the place for tools and verification, not as a second copy. Expected: about 1.0 MB of tool output per Codex round and 150 to 250 KB per Antigravity round, measured before and after with a classifier kept next to this note.
2. Milestone B, `implement-review/SKILL.md` to a core of about 75 to 80 KB: sentences are classified before they move; coordinator decisions (backend and reasoning choice, timeout budgets, retry scope, WARN handling and silent-intake conditions, recovered-response inspection) stay; mechanism, rationale, incidents, and examples go once to `references/` with a read-on-demand pointer; the two reference duplicates go. The 24 tests in `tests/test_skill_md_contract.py` and the pins in `tests/test_prompt_byte_parity.py` name what must stay word for word.
3. Milestone B, `prun/SKILL.md` to about 20 KB by the same rule; `tests/test_prun_executors.py` pins the executor table.
4. Milestone C, legacy cleanup: delete `prun/scripts/dispatch-task.{sh,ps1}` (the "recovery tooling" they are kept for does not exist in them; `prun_state.py` holds it) and `reap-watch.ps1` in all three copies; move the monitor and gather deployed-path tests to their own file and retire the rest of `tests/test_dispatch_task.py`; update the parity registry. `gather` stays: it is an advertised interface with four runs.
Withdrawn after plan-review round 1: removing environment variables and flags (live interfaces), a separate comment-trimming sweep (headers now only lose text that moved to `references/`), and an automatic state-directory expiry (no backend records enough liveness evidence to make deletion safe; a retention design with a dry run and tests is its own plan).

Deferred, each a contract change: merging the shell twins into Python (about 100 KB), merging the four observers, and removing `gather`. The `health-check` launchers stay.
