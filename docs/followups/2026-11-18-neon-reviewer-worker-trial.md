# Gemini 4 Neon as Agy reviewer and `prun` worker, and `/swarm` beside `prun`: a trial, 2026-11-18

Google released Gemini 4 Neon on 2026-11-18. This trial asked three questions about the Agy rows of `user/agent-models.json`. Can `gemini-4-neon/high` replace `gemini-4-carbon/medium` as the Agy `/vet` reviewer? Does it also do better than `gemini-4-hydrogen/high` as the `prun` worker? And should a batch of Agy work run as `prun` units that a Claude session coordinates, or as one Agy `/swarm` task? A fourth question came with them: does the registry still need Gemini 4 Argon? The drafting comparison of Neon with Opus 5.5 is a separate note, [neon-opus-blind-read](2026-11-18-neon-opus-blind-read.md).

Models are written as the registry's `<stem>/<effort>`, the form `agent_models.py map` prints. The Agy CLI slug is `<stem>-<effort>`, which is what `ANTIGRAVITY_DISPATCH_MODEL` took in this trial.

**Status**: decided for the Agy rows on 2026-11-18. Argon leaves the registry, the reviewer moves to `gemini-4-neon/high` after a second round on six past commits, and the `prun` worker stays. The side findings are settled: the weak tests are replaced, the dispatcher tests no longer inherit a dispatch override, and the LaTeX-quote pairing in Check 8 stays as a known low risk. Still open: a possible `/swarm` trial on a task whose pieces depend on each other (Decisions). The archive of both rounds (prompts, scoring keys, submitted reviews and results, patches, scripts, measurements, and the dispatchers' model records) is in [2026-11-18-neon-reviewer-worker-trial/](2026-11-18-neon-reviewer-worker-trial/), with round 2 under `round2/`.

## Agy rows of the registry before this change

From `agent_models.py show` on 2026-11-18:

| Agy role | Model | Fallbacks, in order | Source in the registry |
|---|---|---|---|
| interactive | `gemini-4-argon/high` | `gemini-4-hydrogen/high` | the family row |
| premium | `gemini-4-argon/high` | `gemini-4-hydrogen/high` | inherits the family row |
| reviewer | `gemini-4-carbon/medium` | `gemini-4-argon/high`, then `gemini-4-hydrogen/high` | role override |
| worker | `gemini-4-hydrogen/high` | none | role override; effort from the family row |
| prun-worker | `gemini-4-hydrogen/high` | none; second model `claude-sonnet-5-5/high` | role override |

## Design

- **Runs.** `scripts/run_all.sh` launched all eleven arms at 16:06 local time. Nine ran in pinned clones built by `scripts/setup.sh`, and the two U2 web-research units ran in the dispatcher's own scratch directories. Every cell ran once. The coordinating Claude session wrote `scoring-key.md` before it read any result.
- **Reviewer arms.** Both ran through `skills/implement-review/scripts/dispatch-gemini.py` with the same request (`prompts/header.txt` plus a body), on `gemini-4-carbon/medium` (the registry reviewer) or `gemini-4-neon/high`.
  - The seeded diff is 0878a02 (whole-run code-span matching in `health-check.py` and `dispatch-gemini.py`) staged on its parent, plus one planted bug (`patches/seed.diff`): `index = partner` in place of `index = partner + 1` in both copies of `code_span_bounds`. Text between two code spans of the same width then disappears, yet `tests/test_health_check.py` and `tests/test_dispatch_gemini.py` still pass (171 passed, 3 skipped).
  - The clean diff is 011410a (Check 5 accepts a bare `Verification notes` line) staged on its parent. Codex and the `gemini-4-carbon/medium` reviewer passed it on 2026-11-17 with no change required.
- **Worker arms.** Both ran through `skills/prun/scripts/dispatch-task-agy.py`, on `gemini-4-hydrogen/high` (the registry `prun` worker) or `gemini-4-neon/high`, with three units (`prompts/u1.md` to `prompts/u3.md`):
  - U1, a read-only audit of where the repository names a Gemini model and whether dropping Argon from the registry breaks anything;
  - U2, public-web facts about Neon and the status of Argon;
  - U3, a small change to `dispatch-task-agy.py` with tests: publish a worker's final response from its `# <unit-id> result` header and keep the full response beside it.
- **Swarm arm.** One `agy -p "/swarm ..."` process on `gemini-4-neon/high` got the same three tasks in its own clone (`prompts/swarm.md`). It ran outside the dispatcher, for the reason given in the `/swarm` section.
- **Measures.** Wall time runs from dispatch to exit. Input and output tokens and cache reads come from each run's stream-json result event (`scripts/usage.py`). Model calls are the rows of `gen_metadata` in each Agy conversation database. `metrics.txt` holds the raw numbers.

## `/vet` reviewer, round 1: `gemini-4-carbon/medium` against `gemini-4-neon/high`

**Both reviewers found the planted bug, and the `gemini-4-neon/high` reviewer also found a regression in shipped code that the other missed.**

| | `gemini-4-carbon/medium` | `gemini-4-neon/high` |
|---|---|---|
| Seeded diff: the planted bug | found, High, exact rewrite | found, High, exact rewrite |
| Seeded diff: other findings | Medium: test gaps | the same Medium; a Low on Check 8 tails |
| Seeded diff: verdict | BLOCK | BLOCK |
| Clean diff | PASS, no findings | PASS, two optional Lows, both accurate |
| Wall time, seeded / clean | 748 s / 384 s | 345 s / 190 s |
| Input + output tokens, seeded / clean | 221K / 124K | 146K / 108K |
| Cache-read tokens, seeded / clean | 3.29M / 0.86M | 1.19M / 0.63M |
| Model calls, seeded / clean | 32 / 13 | 17 / 11 |

Each review of the seeded diff gave the one-line fix for both files. Their shared Medium has two parts: no test places checked text between two spans of the same width, and two assertions that 0878a02 added already pass on the old code. Both parts hold (Side findings). The `gemini-4-neon/high` reviewer's extra Low also has two parts. Its first part, LaTeX quotes on one stream-json line, holds on the shipped code (Side findings); the second, a stray single backtick before a fence that contains one, was not checked. On the clean diff, the `gemini-4-neon/high` reviewer noted that Check 5 still refuses some bulleted or bold label forms that Check 10 reads, and that the new test could also assert exit 0 and add a negative case. The `gemini-4-carbon/medium` reviewer reported nothing there.

Three of the four runs drew a Check 8 warning. Each traced to a test name or a reproduction string the reviewer had quoted in its own tail. No run hit a quota or backend error, so no retry inflated either arm's counts.

The seeded diff did not test unprompted detection. Focus item 1 of the request asked whether the new code hides a failure marker the old code exposed, which is the planted bug's symptom. Effort also differs between the arms, since the trial compared the registry row with a candidate.

## `/vet` reviewer, round 2: six past commits

**Both reviewers found all four planted defects, and the `gemini-4-neon/high` reviewer took about 40% less time; on d4 it alone treated the defect as a blocker.**

Round 1 used two diffs, and its seeded request pointed at the defect, so a second round replayed six past ac commits, each staged on its parent in its own clone (`round2/scripts/setup.sh`). Four carry one planted defect of a different kind (`round2/scripts/seed.py`, `round2/patches/`), and each seeded clone still passes its relevant tests on Python 3.12 and 3.9. The other two are the commits as made. Every request uses the same lens text and names no focus area, and each summary states what the original commit set out to do (`round2/scripts/make_prompts.py`). Each model started six reviews together, and the dispatcher confirmed the requested model and effort in all twelve runs (`round2/model-actual.txt`). Before any review ran, the coordinating Claude session wrote `round2/scoring-key.md` with its decision rule: move the reviewer if `gemini-4-neon/high` found at least as many planted defects with no more invalid findings, with cost (calls and time, round 1 counted alongside) deciding a tie.

| Diff | Planted defect | `gemini-4-carbon/medium` | `gemini-4-neon/high` |
|---|---|---|---|
| d1 (15e383d) | logic: `worker` and `prun-worker` rows counted toward the review-panel test in `agent_models.py map` | found, High; BLOCK | found, High; BLOCK |
| d2 (37b9b26) | one copy of two: `dispatch-task-agy.py` keeps the slug-tier tuple without `xhigh` | found, High; BLOCK | found, High; BLOCK |
| d3 (932bd74) | document against code: `grok-executor.md` says one override waives a missing registry row, and the dispatcher needs both | found, High; BLOCK | found, High; BLOCK |
| d4 (d3aac68) | a test named for zero usage that uses 1% | found, Medium; PASS | found, High; BLOCK |
| c1 (5ed589b) | none | PASS, two Lows | PASS, the same two Lows |
| c2 (ee57b98) | none | PASS, two Mediums and a Low | PASS, the same three points (one Medium, two Lows) |

Beyond the planted defects, the seeded reviews raised six other findings on `gemini-4-carbon/medium` and seven on `gemini-4-neon/high`, and the clean reviews five each. Every one holds on checking in the clones, and most appear in both arms: the sibling path helpers in `agent_models.py` that do not expand `~`, the exit code 124 that `grok-executor.md` omits, and a window whose `used_percentage` is null still rendering a dash. One c1 Low matches a Low that the commit's own `/vet` had deferred.

| Six reviews each | `gemini-4-carbon/medium` | `gemini-4-neon/high` |
|---|---|---|
| Wall time, total (median) | 3,034 s (490 s) | 1,768 s (282 s) |
| Input + output tokens | 1,107K | 870K |
| Cache-read tokens | 9.33M | 7.59M |
| Model calls | 99 | 99 |

Detection and invalid findings tied, so the rule's cost tie-break decided, and the reviewer moves to `gemini-4-neon/high`. Its reviews finished sooner and used fewer tokens in both rounds; it also made fewer model calls in round 1 (28 against 45), while both models made 99 in round 2. As in round 1, the dispatch override reached each reviewer's shell, and every review that ran the Agy dispatcher tests met failures there. On c1 and d2 both reviewers reran those tests with the override cleared, after 69 failures on c1 and 68 on d2.

## `prun` worker: `gemini-4-hydrogen/high` against `gemini-4-neon/high`

**Both models answered the audit and the research unit correctly, and their code changes passed the tests while sharing one narrow miss. The `gemini-4-neon/high` units wrote fuller answers, and the `gemini-4-hydrogen/high` units finished sooner.**

| Unit | Model | Wall time | Input + output tokens | Cache-read tokens | Model calls |
|---|---|---|---|---|---|
| U1 audit | `gemini-4-hydrogen/high` | 288 s | 260K | 5.05M | 37 |
| U1 audit | `gemini-4-neon/high` | 523 s | 281K | 6.33M | 44 |
| U2 web facts | `gemini-4-hydrogen/high` | 316 s | 157K | 1.21M | 20 |
| U2 web facts | `gemini-4-neon/high` | 364 s | 131K | 0.60M | 14 |
| U3 code | `gemini-4-hydrogen/high` | 165 s | 223K | 0.98M | 14 |
| U3 code | `gemini-4-neon/high` | 275 s | 144K | 1.15M | 14 |
| All three | `gemini-4-hydrogen/high` | | 640K | 7.24M | 71 |
| All three | `gemini-4-neon/high` | | 556K | 8.08M | 72 |

- **U1.** Both concluded that replacing the two Argon fields breaks no test or script and that the next bootstrap rewrites the interactive Agy setting. The `gemini-4-neon/high` unit added that `scripts/check-parity.sh` reports drift until the aa registry matches.
- **U2.** Both reported the facts in the key with first-party sources, and neither found a statement retiring Argon (see Gemini 4 Argon).
- **U3.** `tests/test_dispatch_task_agy.py` passes in both clones on Python 3.12 and 3.9 (98 tests, rerun after the trial). Both changes strip trailing spaces before matching the header. If the last line is the header followed by spaces, both discard the text before it and write a second file, where the unit required an exact line match. The `/vet` review of this note found the miss, and the swarm's change shares it.

The launcher started five individual `gemini-4-neon/high` jobs, three `gemini-4-hydrogen/high` jobs, two `gemini-4-carbon/medium` jobs, and one swarm together, and the swarm's coordinator then added five Neon members. The trial did not measure how the overlapping work affected the timings, so the round-1 wall times compare the models only loosely.

## `/swarm` beside `prun`

**`/swarm` ran headless and completed all three tasks as well as the `prun` units did, including the same U3 miss, at more model calls, more time, and less visibility.**

- `agy -p` expands a prompt that starts with `/swarm`. The coordinator added five members, all on `gemini-4-neon/high`, the conversation's model: a monitor, one worker per task, and a verifier, which ran the code task's tests.
- Wall time was 836 s for the swarm, while the three `gemini-4-neon/high` `prun` units, running in parallel, finished within 523 s.
- Model calls came to 89 (coordinator 14, members 75), against 72 for those three units, about a quarter more.
- Only the coordinator's tokens reach the stream (177K input and output). Each member's usage stays in its own conversation, so the swarm's token total is unknown. Antigravity's documentation says a swarm draws quota faster than a single conversation.
- The stream carried only the coordinator's conversation, and each member's steps were visible only in the local conversation databases after the run. No member failed, so how a member's failure surfaces was not observed.
- The dispatcher cannot start a swarm today. `build_prompt` in `dispatch-task-agy.py` puts relay text ahead of the unit's request, so the prompt never starts with `/swarm` and the command does not expand. This arm therefore ran without the stall reaper, the `model-actual` record, and the result contract. A `prun` unit that runs `/swarm` needs a dispatcher change first.
- The three tasks could proceed independently, which is the shape Google's swarm guide recommends: "`/swarm` works best when the pieces of a task can proceed independently." On that shape, three `prun` units matched the swarm's results with fewer calls and less time. A task with a dependency between two pieces would test whether coordination through the shared board changes the result, and this trial did not run one.

## Gemini 4 Argon

**The repository's tests and scripts pass with Argon out of the registry, although Google has not retired it.**

- Two registry fields named Argon, `families.agy.model` and `roles.reviewer.agy.fallback_model`, and they resolve into three rows: Agy interactive, Agy premium (which inherits the family row), and the reviewer's first fallback. Bootstrap's `sync` writes the interactive row into `~/.gemini/antigravity-cli/settings.json` when `agy models` lists the new model. A drift test in `tests/test_agent_models.py` keeps model names out of runtime code, and every other hit is one of three kinds: test fixtures with their own registries, docstring examples in `scripts/agent_models.py`, and records. All three audits (U1 on each model and the swarm's Task 1) found that replacing the two fields breaks no test or script. aa carries the same registry, so a change goes to both repositories.
- The two research units and the swarm found no first-party statement retiring Argon. Google's Gemini API deprecations page lists `gemini-4-argon` with no shutdown date, and the Antigravity models page still lists it. Among the sources the units checked, only 9to5Google, a third party, reported that Neon replaces Argon in the Gemini app.
- The trial compared neither the interactive nor the premium role against Argon. `gemini-4-neon/high` takes them because, per Google's announcement and the Antigravity models page, Neon becomes the default for a new Antigravity conversation on eligible plans when the user has not chosen a model, and High is its default level.

## Side findings

1. **A regression in shipped `health-check.py` (Low).** Since 0878a02, and still at HEAD, `code_span_bounds` pairs two double-backtick runs on one physical line as a code span. A stream-json tail holds a whole event on one line, so two LaTeX opening quotes (written as two backticks each) in one event hide any failure marker between them from Check 8. The old two-regex code exposed that marker. Only the `gemini-4-neon/high` reviewer reported it, and `scripts/check_side_findings.py` reproduces it. A `/vet` of a LaTeX paper is where it would show up.
2. **Two tests that do not tell old from new.** Both reviewers reported that two assertions added in 0878a02 pass on the old code: the "double-backtick span holding a backtick" case in `tests/test_health_check.py`, and the nested-fence assertion in `tests/test_dispatch_gemini.py`. Each claim holds. The script runs each against both versions, beside an input that does tell them apart. At 0878a02, neither test file placed checked text between two spans of the same width, so both missed the planted bug.
3. **An inherited override breaks the dispatcher tests.** Both reviewers of the seeded diff first saw 26 failures in `tests/test_dispatch_gemini.py`, because the `ANTIGRAVITY_DISPATCH_MODEL` the trial set to choose the model reached the reviewer's shell. Each reran with `env -u`. Round 2 met the same failures in `tests/test_dispatch_gemini.py` and `tests/test_dispatch_task_agy.py` when reviews ran the affected tests with the override set.

## Limits

- `gemini-4-carbon/medium` and `gemini-4-neon/high` each reviewed eight diffs once across the two rounds, and `gemini-4-hydrogen/high` and `gemini-4-neon/high` each ran the three worker units once.
- The coordinating session planted the round-2 defects, and both models found all four, so those diffs may be too easy to separate the models on detection.
- Tokens are not Agy quota, and neither round measured how each model's tokens count against it. Over the first batch the Gemini quota fell from 96% to 90% in the 5-hour window and from 95% to 93% in the 7-day window. That is an upper bound, since another session ran Neon at xhigh at the same time.
- The focus item that pointed at the planted bug in round 1, the effort mismatch, the round-1 load, and the independent swarm tasks are described in their sections.

## Decisions

Agy rows, changed through the `agent-models` skill in ac and aa together:

| Agy role | Before | After | Evidence |
|---|---|---|---|
| interactive | `gemini-4-argon/high` | `gemini-4-neon/high` | Argon section; Antigravity defaults to Neon on eligible plans when the user has yet to choose a model |
| premium | `gemini-4-argon/high` | `gemini-4-neon/high`, through the family row | as above |
| reviewer | `gemini-4-carbon/medium`; fallbacks `gemini-4-argon/high`, `gemini-4-hydrogen/high` | `gemini-4-neon/high` from the family row; the override keeps only its fallback, so fallbacks `gemini-4-carbon/medium`, `gemini-4-hydrogen/high` | both `/vet` rounds |
| worker | `gemini-4-hydrogen/high` | unchanged | |
| prun-worker | `gemini-4-hydrogen/high` | unchanged | `prun` section |

Side findings, settled on 2026-11-18 in the commit after the registry change:

1. `code_span_bounds` tests: the two weak assertions now use the discriminating inputs from `scripts/check_side_findings.py`, and new cases put checked text between two spans of the same width in Check 8, Check 10, and the recovery check. The planted `index = partner` bug fails all three cases, and the old code fails the replaced assertions.
2. `code_span_bounds` behavior: kept as is. Two LaTeX opening quotes on one tail line can hide a marker between them. Check 8 can still warn on a marker in a separate event or in stderr, or on a recovery record the dispatcher writes, and a failed exit or a missing review also exposes the failure. A change would first have to decide how such runs pair without splitting backticked Windows paths at an escaped `\n`.
3. Dispatcher tests: `_run` in `tests/test_dispatch_gemini.py` and `tests/test_dispatch_task_agy.py` now clears `ANTIGRAVITY_DISPATCH_MODEL`, `ANTIGRAVITY_DISPATCH_EFFORT`, and `ANTIGRAVITY_PREFLIGHT` when the caller's shell sets them, as `_print_model` in `tests/test_dispatch_gemini.py` already did. Tests that exercise an override still pass it through `extra_env`. Before the change, the two files had 80 failures with `ANTIGRAVITY_DISPATCH_MODEL` set in the shell and 22 with `ANTIGRAVITY_PREFLIGHT=off`; they now pass with either set.

Still open: `/swarm`. `prun` stays the outer layer. A further trial is worth running only on a broad task whose pieces depend on each other, where the shared board could matter; a dispatcher path that lets a unit start with `/swarm` waits for that result.
