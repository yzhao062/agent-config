# Are `implement-review` and `prun` Complete, Effective, and Efficient? An Audit (2026-11-14)

The maintainer asked whether the two most-used skills do what they claim, recover from failure, and spend no more context than they need. Six read-only `prun` units audited throwaway clones at `d9042d0`: two on Codex (U1, U6), two on Agy (U2, U4), and two on Grok (U3, U5). Two verifier units then tried to refute the strongest single-source claims: V1 on Codex against U4, and V2 on Agy against U6. A three-agent Claude Workflow measured real use from local transcripts, Codex rollouts, and state directories since 2026-09-20. It reported aggregates only, because those transcripts also hold private email and proposal work. Unit results and the Workflow's scripts stay in the session scratchpad under `prun-audit/agent-io/` and `telemetry/`; this note keeps what decides a fix.

Two labels recur below. A finding is **Convergent** when two or more units found it independently, and **verified** when a probe, a verifier, or on-disk evidence reproduced it at the cited file and line. Everything else is a single-source code reading, marked as such.

## Verdict

Both skills earn their cost. Of the 1,381 findings whose fate the coordinator recorded since October, 80% were fixed and 4.6% refuted; of the High findings, 88.5% were fixed and 2.8% refuted. The Milestone A reviewer contract held: avoidable reviewer reads are 3.2% on Codex (190 rollouts) and 2.9% on Agy (45 rounds over two days), against 30.6% and 58% before it. A Codex review dispatch now takes a median 6.7 minutes (15.3 in September, on a different model and effort). In `prun`, the monitor classified 3.7% of recent units as FALLBACK and 1.4% as stalled, against about 9% failed in the week before 2026-09-20; the two windows use different classification rules, so this is not a like-for-like failure rate.

The defects cluster in four places.

1. **The review intake gate is weaker than documented.** `SKILL.md` prescribes a `health-check` command that omits two options, so three of its checks always pass. A review that answers the wrong round can be published as current and pass the gate. Meanwhile, of the 660 dispatches with a usable health-check record, 43% warned on Check 7, 8, or 9, every sampled Check 8 warning was noise, and coordinators re-dispatch after 6% of warnings.
2. **Failure paths lose or misreport results.** Grok `prun` overwrites a result its worker wrote and fails every unit launched with `--add-dir`. The restored Codex `prun` executor lacks the interface `SKILL.md` says it shares with Agy. The stall watcher can certify a reviewer dead while it still runs.
3. **Size now costs coverage, not only tokens.** A whole Read of `implement-review/SKILL.md` returns about the first 274 of 684 lines, so a coordinator needs a median of two reads per load and still sees a median 73% of the file. The two files sit 5 and 92 bytes under their test ceilings, so every fix that adds text must first cut some.
4. **The loop leaves no record of its own results.** Findings, fates, and loop boundaries exist only as prose, the round counter is reused across unrelated reviews, and `prun` state is purged from `$TMPDIR` within days. This audit had to reconstruct all three by parsing.

## `implement-review` Findings

| ID | Finding | Severity | Found by | Status | Main location |
|---|---|---|---|---|---|
| IR-1 | Prescribed `health-check` call omits `--prompt-file` and `--lens` | High | U1, U4, U6 | verified (U1, V2, live runs) | `SKILL.md:397` |
| IR-2 | Wrong-round review published as current | High | U6 | verified (V2) | `dispatch-gemini.py:668`, `dispatch-claude.sh:560`, `dispatch-claude.ps1:722` |
| IR-3 | Claude reviewer cannot see an untracked plan | High | U1 | verified (U1 mock) | `dispatch-claude.sh:438`, `:509`; `dispatch-grok.py:369` |
| IR-4 | Watcher records a helper and certifies a live reviewer dead | High | U1 | verified (U1 repro) | `stall-watch.sh:148`, `:300`; `dispatch-codex.sh:410` |
| IR-5 | Check 8 pattern `tool .* failed` spans unrelated NDJSON text | Medium | Workflow, U6 | verified (18 of 18 sampled warnings were noise) | `health-check.py` Check 8 patterns |
| IR-6 | A whole Read returns about 38% of `SKILL.md` | Medium | Workflow | measured (118 loads) | `SKILL.md` size |
| IR-7 | Parent-exit reap leaves `await-review` reporting ALIVE | Medium | U4 | partly verified (V1) | `stall-watch.sh:320`; `await-review.py:227` |
| IR-8 | Agy and Grok embed the whole staged diff in scoped rounds | Medium | U1, U4, U6 | verified (U1 sentinel) | `dispatch-gemini.py:466`; `dispatch-grok.py:325` |
| IR-9 | Missing `Verification status:` passes Check 10 | Medium | U6 | partly verified (V2) | `health-check.py:777` |
| IR-10 | Embedded-diff retry cannot pass Check 10 | Medium | U1 | verified (U1 probe) | `SKILL.md:114` |
| IR-11 | An absent single Grok is routed to failover | Medium | U4 | partly verified (V1) | `SKILL.md:392`, `:406` |
| IR-12 | No plan-review prompt branch; Scope-challenge always on | Medium | U4 | verified (V1) | `SKILL.md:363-384`, `:375`, `:394` |
| IR-13 | Successful dispatch replays an 80-line tail | Medium | U6 | verified (V2) | `dispatch-gemini.py:813`, `:1072`; `dispatch-codex.sh:684` |
| IR-14 | No findings ledger; one round counter spans unrelated reviews | Medium | Workflow | measured | Phase 2.5, round numbering |
| IR-15 | A Refuted outcome needs no recorded evidence | Medium | Workflow | 1 of 4 sampled refutations reversed | Phase 2.5 |
| IR-16 | Lost-handle sequential mode names no worker-exit check | Low | U4 | verified, narrow (V1) | `SKILL.md:249-261` |
| IR-17 | Check 7 warns on benign prose | Low | U6 | verified (U6 probe) | `health-check.py:28`, `:719` |
| IR-18 | Smaller contract gaps (list below) | Low | U4 | code reading | various |

**IR-1.** `SKILL.md:397` gives `health-check --state-dir ... --round ... --review-file ...` and never adds the other two options. Without `--prompt-file`, Check 6 (scope correspondence) prints `PASS check-6 no-prompt-file-provided` and the substance-1 timing heuristic sees a 0-character prompt. Without `--lens plan-review`, substance-3 (the plan scope challenge) is skipped (`health-check.py:693-713`, `:780-791`, `:804-817`). U1 and V2 each built a review of an unrelated file: the documented call exited 0, and the same call with both options exited 1 with a scope FAIL. The `/vet` rounds of the advisor change, run the same day, printed `no-prompt-file-provided` and `prompt-below-threshold=0chars`. Fix: write the full call in Phase 2, pass the round's prompt file, and map the lens to the parser's values (`skill`, `code`, `doc`, `plan-review`, `default`); add a contract test that runs the documented call against a mismatched plan review.

**IR-2.** When the response lacks `<!-- Round N -->`, the Agy and Claude dispatchers prepend it, even when the response already opens with another round's marker. V2 published a Round 1 review as Round 2; the file began `<!-- Round 2 -->`, `<!-- Round 1 -->`, and `health-check --round 2` passed Check 3, which reads only the first line (`health-check.py:662-670`). Grok already rejects this case (`dispatch-grok.py:981-990`). Fix: in the three Agy and Claude paths, exit 70 and publish nothing when no standalone marker line names this round and one names another round. A standalone current-round marker in any spelling wins wherever it sits, and round numbers compare with leading zeros removed, so round 1 and round 11 stay distinct.

**IR-3.** The plan-review recipe keeps the plan out of the index (`SKILL.md:38`), and the supplied-input exception at `:40` names only Antigravity. The Claude backend, the default reviewer under a Codex coordinator (`:277`), exports the index and runs the reviewer inside that export, so a mock run recorded `plan_exists=false`. Grok's automatic supplied inputs cover only `AGENTS.md` and `AGENTS.local.md` (`dispatch-grok.py:369`). Fix: make the supplied-input rule cover every snapshot backend and carry a named plan in the request once; add a plan-review test with an untracked plan. The Claude backend ran zero times in the window, so this matters when Codex coordinates.

**IR-4.** `stall-watch.sh:148` stops capturing after it records any child, and identifies children by parentage. The Bash Codex dispatcher starts the watcher at `dispatch-codex.sh:410`, before the registry resolver runs at `:504` and the reviewer launches at `:647`, so a short-lived resolver can become the recorded worker. On a later stream-death line, the reap finds nothing alive, `:301` writes `stream-reap-complete` anyway, and `await-review` reports DEAD (`await-review.py:227`, `:392`). U1 reproduced it with a helper process followed by a longer-lived synthetic reviewer. The PowerShell twin resolves first (`dispatch-codex.ps1:566`) and starts the watcher later (`:627`). Fix: start the Bash watcher after resolution, next to the launch, and publish completion only after the recorded reviewer tree is gone; a stronger fix passes the reviewer PID from the dispatcher.

**IR-5.** Of 660 dispatches with a usable health-check record, 43% warned on Check 7, 8, or 9, and the share of runs with warnings only rose from 30% in September to 47%. Only 6% of those warnings led to a re-dispatch. The Workflow re-ran Check 8 on the 118 real tails of 2026-11-13 and 2026-11-14 and read all 18 matches: every one was noise, and no tail held a real tool failure. Agy and Grok write each event as one long JSON line, so `tool .* failed` matches "tool" and "failed" from unrelated text in the reviewed documents; Grok warns on 55% of rounds for this reason. Fix: bound the pattern to one event field, or scan only tool-error events, and strip tool-output payloads from the tail before the scan. Re-measure afterwards; Check 7 has no ground truth yet.

**IR-6.** A whole Read of `SKILL.md` returned 57 to 61 KB, lines 1 to about 274 of 684, in all 69 whole reads the Workflow found. Most coordinators follow with ranged reads (median two reads and 124 KB per load), but median coverage is 73% of the lines, and the three loads that read the file once saw 38% of it. Phase 2 and the health-check section lie past that boundary. A health-check run is on record for only 54% of completed dispatches; the data cannot say whether the two are linked. Fix: Milestone B, ordered so that every step a coordinator runs each round sits in the first 60 KB.

**IR-8** matters for `/vet both` and `/vet all`: Codex can receive only the selected paths while Agy and Grok receive every staged path, so out-of-scope findings enter consolidation. The rule at `SKILL.md:332` that forbids Claude when staging is broader than scope should name all snapshot backends, failover included. **IR-10**: the retry at `SKILL.md:114` forbids shell commands, yet Check 10 rejects the UNVERIFIED review that follows (`health-check.py:753`), so the retry spends a Codex round and cannot succeed; skip it when the failed capability is the verification Check 10 needs. **IR-13**: Agy writes its whole final review on one NDJSON line, so the 80-line tail prints the review to the coordinator a second time; print a short success line and keep the tail for failures.

**IR-14.** Of the 1,680 finding items recovered from coordinator prose, 18% carry no recognizable status and 37% no reviewer label, and a third of dispatched rounds have no visible review read. One round counter also runs across unrelated reviews in a session: the highest round number per loop reaches 86, while distinct dispatched rounds per loop have a mean of 2.5 and a maximum of 17. Fix, if the record is wanted: one JSON line per distinct finding in the round's `agent-io` directory (loop id, round, reviewers, severity, outcome, Convergent or single-source, fate), with the next round's Prior findings block generated from it, and the round reset to 1 for a new object under review. This adds a few lines of coordinator work per round.

**IR-15.** In one of four sampled refutations, the coordinator reversed itself a round later after Codex re-raised the claim; its first check had read only an instructions page. Fix: a Refuted outcome names the evidence read (command, full URL, file and lines); a refutation without it is recorded as Inconclusive.

IR-7, IR-9, IR-11, IR-12, and IR-16 are narrowed by the verifiers; see "Claims Refuted or Narrowed". IR-18 groups the smaller contract gaps U4 read in the code, none reproduced:

- `await-review` exit 1 is missing from the `SKILL.md:454-460` result table.
- `SKILL.md:135` and `:527` describe STALL handling differently.
- A `Disagree` reply has no Phase 3 or Phase 4 mapping.
- The Grok state-directory hash uses 12 hex characters, while `auto-watch` uses 8.
- `dispatch-grok.py:1235` sets the review mtime, and `health-check.py:654` compares with a strict `>`.
- Terminal-relay skips the mtime check for expected files.
- `all` must be a leading token, and its meaning under a fourth coordinator is undefined.

U6 also lists missing tests: wrong-round output through publication and intake, partial output without status or verdict, the prescribed health call, a three-slot `all` intake with one failed backend, and the full coordinator routing matrix.

## `prun` Findings

| ID | Finding | Severity | Found by | Status | Main location |
|---|---|---|---|---|---|
| PR-1 | Codex `dispatch-task` lacks the Agy interface it is said to match | High | U2, U5 | verified (code, this run); fixed in a follow-up | `dispatch-task.sh:123-135`; `SKILL.md:331-332` |
| PR-2 | Grok fallback overwrites a result the worker wrote | High | U2, U5 | verified (code) | `dispatch-task-grok.py:1060-1072` |
| PR-3 | Grok fails every unit launched with `--add-dir` | High | Workflow | verified (6 units on disk, one batch) | `dispatch-task-grok.py:916-917`; `grok-executor.md:22` |
| PR-4 | Agy has no idle reaper; a stall runs to the 2,700 s print timeout | High | U5 | code reading | `dispatch-task-agy.py` |
| PR-5 | Agy and Codex worker preambles omit the skip-bootstrap line | Medium | U2, U5 | verified (code); Codex half fixed in a follow-up | `dispatch-task-grok.py:637` has it |
| PR-6 | "Usable result" is undefined; `gather` reports DONE on a FALLBACK | Medium | U2, U5 | code reading | `SKILL.md` flow step 6 |
| PR-7 | Transient failures get no automatic retry | Medium | Workflow | measured | Agy and Grok dispatchers |
| PR-8 | Batches run through hand-written loops the flow does not describe | Medium | Workflow | measured | `SKILL.md` flow |
| PR-9 | `ANTIGRAVITY_DISPATCH_EFFORT` alone conflicts with the tiered slug (exit 2) | High | U2 | code reading | `dispatch-task-agy.py` |
| PR-10 | `monitor` hides a dead dispatcher until the stall threshold | High | U2 | code reading | `monitor.sh:165-183` |
| PR-11 | The single-worker gate branch contradicts "never run a unit" | Medium | U5 | code reading | `SKILL.md` |
| PR-12 | Worker limits described as structural are prompt-only | Medium | U2 | code reading | `SKILL.md:129` |
| PR-13 | Quota cache trusted for 900 s against a 300 s TTL | Medium | U2 | code reading | quota routing |
| PR-14 | Default stall threshold overridden in 40% of monitor launches | Low | Workflow | measured | `monitor.sh` default 600 s |
| PR-15 | Registry exit codes, preflight order, a redundant `agy --version` | Low | U2 | code reading | `dispatch-task-agy.py` |

**PR-1.** The Codex dispatcher accepts only `--prompt-file`, `--result-file`, and `--unit-id`, and exits on anything else (`dispatch-task.sh:123-135`). It therefore takes no `--mode`, `--add-dir`, or `--continue-from`, so a Codex unit gets no follow-up turn. Nor does it add a worker preamble, tell the worker the result path, or refuse an existing result file, and its FALLBACK carries the whole stream tail. `SKILL.md:331-332` says the arguments "match the Agy dispatcher". This run reproduced the cost: U1 and U6 wrote their results inside their clones, the dispatcher saw no result, and it published FALLBACK files of 976 KB and 388 KB. V1 succeeded only because its prompt named the absolute result path. Outside this audit the dispatcher ran zero times since 2026-09-13, while 261 hand-typed `codex exec` calls appear in 30 sessions that also invoked `/prun`; the data cannot say whether any were meant as units. Fix: correct `SKILL.md:331-332` and require the absolute result path in every Codex unit prompt. A follow-up change the same day took a different route: the dispatcher now tells the worker how its result is collected and publishes the worker's final message, so a prompt needs no path (see the decisions at the end).

**PR-2.** On a nonzero exit, `dispatch-task-grok.py` saves the worker's final response beside the result, then calls `publish_fallback`, which replaces the result file the worker wrote. The Agy twin returns early when a non-empty result exists (`dispatch-task-agy.py:867-868`). Its test covers the success path only. Fix: return early as Agy does, and add the nonzero-exit test.

**PR-3.** All six Grok units of one batch on 2026-11-13 failed with "additionalDirectories is not supported: a session works only in its cwd". The dispatcher validates `--add-dir` and passes it through (`dispatch-task-grok.py:916-917`), and `references/grok-executor.md:22` documents it. All six succeeded when re-dispatched without it. Fix: refuse `--add-dir` before launch with a message naming the Grok limit, update the reference, and add a test with the observed error text.

**PR-4.** Codex and Grok units are reaped at `PRUN_STALL_THRESHOLD`, but an Agy unit that stops producing output runs until `--print-timeout` (2,700 s). Re-dispatching a stalled Agy unit then doubles its spend. Either add the idle reaper or say in `SKILL.md` that an Agy stall must be stopped before it is re-dispatched.

**PR-5.** Grok's preamble tells the worker to skip bootstrap, banner, session-start, and router steps (`dispatch-task-grok.py:637-641`); Agy and Codex preambles did not; the follow-up gave the Codex executor Grok's preamble, so only Agy lacks it. In a clone of a consumer repository, a worker that follows `AGENTS.md` would run bootstrap, rewrite the generated rule files in the clone, and refresh files under `~/.claude`. Fix: add the same line to both preambles.

**PR-6.** Flow step 6 asks for a "usable result" without defining it or checking the dispatcher's exit code, and `gather` reports DONE for a FALLBACK file. Exit 75 writes `STATE-DIR` and a FALLBACK but no `model` file. Fix: define a usable result as exit 0 plus a result whose first line is not a FALLBACK header, and make `gather` report FALLBACK as its own state.

**PR-7 and PR-8.** The FALLBACK causes since 2026-09-20 are mostly transient: an empty or short final response (10), a nonzero exit (10), a preflight timeout or sign-in (8), and an interrupted stream (5). Only 12 of 68 FALLBACK units were re-dispatched under the same id. One dispatcher-side retry for those classes, recorded in the state directory, would cover them without a coordinator decision; quota exit 75 stays unretried. Batches also run as hand-written shell loops and helper scripts (100 of 375 dispatch commands). The 17 dispatch errors coordinators caused themselves (compound `cd` denials, reused result paths, bad unit ids, an unknown flag) are the kind a documented batch form would prevent: a prompt directory and a results directory, with paths and unit ids checked by the dispatcher.

PR-4 and PR-9 to PR-15 are single-source readings or one-number measurements that no verifier checked; confirm each before fixing it.

## Efficiency

| Measure | Value | Source |
|---|---|---|
| `implement-review/SKILL.md` | 147,793 B, ceiling 147,798; peak 156,036 on 2026-11-12 | measured |
| `prun/SKILL.md` | 40,684 B, ceiling 40,776; `prun/scripts/` 200,090 B (+53% since September) | measured |
| Growth of `implement-review/SKILL.md` since 2026-09-18 | +10,717 B net; largest: Codex-waiting section +5,088, Milestone A +2,943, parallel `both` +2,105, Grok +1,549; Copilot removal −8,238 | U3 |
| Loaded by one Codex `/vet` | 167,119 B (about 41.8k tokens); 27,083 B are sections that round never uses | U3 |
| Delivered per coordinator load, as measured | median 124 KB in two reads | Workflow |
| Loaded by `/vet all` | 177,375 B | U3 |
| Loaded by one `prun` run | 40.7 KB whole by the Skill tool; about 131 loads in 56 days, about 1.3M tokens | Workflow |
| Coordinator `prun` calls | median 6 per run, 1.0 per unit | Workflow |
| Coordinator control cost per normal review round | about 1.5k to 2k tokens, plus the review and tail bytes it reads | U6 |
| Reviewer request on a 203-byte diff | Codex 6,699 B, Agy 7,112 B, Grok 8,347 B | U6 |

Milestone B, re-measured by U3: moving only mechanism, rationale, and incident history leaves an `implement-review` core of about 103 KB (about 45.8 KB moves) and a `prun` core of about 26.6 KB. The unused sections in a Codex round are plan review, the Agy and Claude backends, and Codex waiting. In `prun`, the `report-state`, `snapshot-tail`, and quota-routing mechanics are the candidates: `gather`, `report-state`, and `snapshot-tail` had zero real invocations since 2026-09-20, and the second Agy group served 0 of 37 November units with model evidence.

Literal duplication is only about 3 KB; most of what the 2026-09 audit called restatement paraphrases the scripts. Three duplicates are real:

- The save-contract blockquote at `SKILL.md:352` (2,608 B) repeats the pinned prompt fence at `:363-384`.
- The Check 7 and Check 8 phrase lists appear in both `SKILL.md` and `health-check.py:1-60`.
- `.claude/commands/prun.md` (2,113 B) and `agents/openai.yaml` restate `prun` policy.

The pointers `vet.md` and `implement-review.md` tell the agent to read `references/` "as needed" (49,948 B). Naming `review-lenses.md` for every round and `grok-backend.md` only when Grok reviews would bound that read.

## Usage Since 2026-09-20

The Mac transcripts start on 2026-09-24; a Windows backup covers the days before. Codex reviewer rollouts exist only from 2026-11-07, and `$TMPDIR` state directories only from 2026-11-13, so the per-unit and per-dispatch disk figures cover one or two days.

| `/vet` measure | Now | September audit |
|---|---|---|
| Reviewer dispatches | 1,416 in 51 days: Codex 779, Agy 601, Grok 36, Claude 0 | Codex 565, Agy 37, Copilot 6 in 60 days |
| Reviewer set per loop | Codex and Agy 80%, Codex only 14%, all three 6% (Grok from 2026-11-12) | mostly Codex |
| Dispatch time, median / p90 | Codex 6.7 / 11.3 min, Agy 5.6 / 13.5, Grok 11.6 / 18.5 | Codex 15.3 / 27.7, Agy 4.8 / 13.8 |
| Round time, median / p90 | 8.3 / 15.1 min; Agy finishes last in 41% of paired rounds | |
| Distinct rounds per loop | mean 2.5, p90 4 | median 2, mean 4.8 (same counter problem) |
| Same-round re-dispatch within 1 h | 9.4%; compound `cd` denials 8 | 16.9%; denials 23 |
| Health check, usable runs | all pass 48.8%, warnings only 47.0%, hard fail 4.2% | 63%, 30%, 6.6% |
| Hard-fail checks | Check 5 (verification notes missing) 17, Check 6 11, Check 3 2 | round marker 11, freshness 9, verdict 7 |
| Avoidable reviewer reads | Codex 3.2% of 32.9 MB over 190 rollouts; Agy 2.9% over 45 rounds on 2026-11-13 and 11-14 | 30.6% before Milestone A, 8.7% after |
| Grok list price reported by its CLI (the plan is a subscription) | median 3.28 USD per review, 119.6 USD for 36 | |

| Review value measure | Value |
|---|---|
| Finding fates (1,381 with a status) | fixed 80%, declined or deferred 11%, refuted 4.6%, open 3.7% |
| High findings (218 with a status) | fixed 88.5%, refuted 2.8%; hand-coded sample of 29 loops: 48 of 49 fixed, none refuted |
| Round 1 BLOCK share | Codex 80%, Agy 56% |
| Codex and Agy disagreement | 28.3% Codex BLOCK with Agy PASS, 3.8% the reverse; in the sample, 9 of 10 such Codex findings were fixed |
| Refuted share of single-source findings | Codex 1.2% (395), Agy 9.3% (302), Grok 17.6% (17) |
| Earlier fixes confirmed in round 2 | Codex 97%, Agy 92% |
| Rounds dispatched after an all-PASS round | 18.6% of 279 transitions, an upper bound because chained reviews share the counter |

| `prun` measure | Now | September audit |
|---|---|---|
| Invocations and runs | 136 invocations, 162 runs in 56 days | 94 invocations, 49 runs in 60 days |
| Units | 1,272 to 1,496 by counting rule; median 6 per run, p90 about 20 | 97 Agy units, p90 5 per run |
| Executors | Agy 373 dispatch commands; Grok 19 units on disk; Codex `dispatch-task` 0 outside this audit | |
| Outcomes, monitor-observed (a kept worker result counts as done whatever the exit code) | 93.1% done, 3.7% FALLBACK, 1.4% stalled | about 9% failed (2026-09-13 to 09-19, another rule) |
| Agy unit time, median / p90 | 6.4 / 13.6 min | 5 to 10 min |
| Grok list price reported by its CLI | median 1.86 USD per unit | |
| Result contract complete | 91 to 95% of results | |
| Monitor use | 60% of runs; runs without it have a median of 2 units | `gather` 4 runs |

Two conclusions follow. Dropping either reviewer from `both` would lose the single-source findings that reviewer alone produced and the coordinator fixed: 292 from Codex and 206 from Agy. And an Agy PASS is weaker evidence than a Codex PASS: Agy passes where Codex blocks in 28% of shared rounds, and its single-source findings are refuted eight times as often. The usual refuted case is a quoted passage or line range that does not exist in the file, which a mechanical check of quoted strings against the snapshot would catch before the coordinator reads the review.

## Claims Refuted or Narrowed

- **IR-7.** Stopping only the outer wrapper leaves the inner dispatcher and reviewer alive with no reap, so a harness stop does not by itself trigger `parent-exited` (V1). When the inner dispatcher dies, the reviewer is reaped with no stream markers, and `await-review` reports ALIVE until the round deadline, then TIMEOUT. A published review still wins, so the problem needs a missing review. No harness stop notification arrived on any of the 1,416 reviewer dispatches in the window.
- **IR-11.** A preflight absence never sets the sticky downgrade (`SKILL.md:392`). The downgrade can follow only if the coordinator takes the inconsistent failover path and the replacements also fail (V1). No failover dispatch and no sticky downgrade appear in the window.
- **IR-9.** `SKILL.md` requires a `Verification status:` line in every review but accepts reviews without a verdict for backward compatibility (`SKILL.md:112`, `:488`). A review that writes `Verification notes: none.` without a status already fails (V2). The defect is the missing status alone.
- **IR-12.** Plan review has usable instructions at `SKILL.md:18`, `:40-41`, and `:54-60`; what is missing is a template branch, and `:68` and `:394` point plan-review sends at the staged template (V1).
- **IR-16.** A normal dispatcher return already proves worker exit, and `SKILL.md:257-259` prescribes a bounded checkpoint when exit is unknown. The gap is confined to a lost dispatcher handle (V1).
- **2026-09 audit, restatement.** The 56.8 KB of "restated scripts" is mostly paraphrase; deleting literal copies saves about 3 KB (U3).
- **2026-09 audit, Agy diff plus snapshot.** The embedded diff and the snapshot do not cause a second ingestion, because the relay forbids a second diff read (`dispatch-gemini.py:535`, `SKILL.md:369`). Tokens grow with the diff only (U6).
- **2026-09 audit, rounds per review.** The September maximum of 36 rounds and mean of 4.8 likely carry the same counter reuse as IR-14.
- **Copilot residue.** None in the active skill, its references, or the command pointers (U1).
- **Instruments.** `classify_reviewer_io.py` misses one form of the `AGENTS.md` injection header, the Agy `read_file` tool name, and Grok's tail format, and counts negated globs and metadata-only diff commands as reads (`anywhere-agents#60`); `measure_acceptance.py` needs the September Windows rollouts, which are not on this machine. The figures above work around these by hand.

## What to Change

These are the two most-used skills, so the bar for a change is a silent wrong outcome or lost work on a path that runs, verified, and fixable in a few lines with a test. Two findings clear it:

1. **IR-2, reject a wrong-round review.** Agy ran 601 review dispatches in the window, and on this path a stale review becomes the current round's input without any warning. The fix is a refusal at the start of `publish_review` (`other_round_marker`, before `normalize_review`) and the same refusal in the two Claude twins.
2. **PR-2 and PR-3, the Grok `prun` dispatcher.** One file: return early when the worker already wrote its result, and refuse `--add-dir` before launch. The six failed units ran `grok 1.0.77`, the version installed now, whose `--help` still lists `--add-dir`.

IR-1 looked like a third and was dropped after checking what the disabled checks do when they run. In the 67 usable health-check runs that did receive a prompt file, Check 6 failed 11 times, all in one session, and in each failing round Codex and Agy failed together. Two independent reviewers missing the same file name points at the check, which requires the exact backticked path from the prompt (for example `PLAN-agent-adapter.md`) to appear verbatim in the review. Substance-3 warned in 10 of the 14 runs that passed `--lens plan-review`. Wiring both options into every round would add hard failures that route to failover, so IR-1 waits for a Check 6 that accepts a basename or the plan's title.

Two configuration changes go with the fixes. The maintainer's reviewer default (`IMPLEMENT_REVIEW_DEFAULT_REVIEWER` in `~/.claude/settings.json` and `~/.codex/config.toml`) moves from `all` back to `both`: Grok raised the median round time from 8.7 to 13.2 minutes, each review draws on the weekly plan meter (its CLI reports about 3.3 USD of list price per review), and 17 Grok-only findings in 14 loops are too few to judge. `all` stays the explicit choice for papers, proposals, and releases. The proposed stop rule for rounds after an all-PASS round is not adopted: the 18.6% is an upper bound, the hand-coded sample holds a second round that found a real Medium regression after a Low fix, and the maintainer's standing rule allows skipping re-review only for comment or whitespace deltas.

Everything else stays recorded here and unchanged. IR-5 (Check 8 noise) is the first candidate if the warning rate becomes a problem; it touches a pattern list tuned over several rounds, so it needs its own labeled sample before a change. Milestone B (IR-6) remains a separate decision.

Three decisions belonged to the maintainer. Two were settled the same day:

- **PR-1, decided 2026-11-14: keep Codex as a single-turn executor and fix what failed.** The maintainer uses Codex in `prun` occasionally, so deletion was rejected, and no evidence asks for a Codex follow-up turn, so the full Agy interface was not ported. A follow-up change gives `dispatch-task.{sh,ps1}` the worker preamble, publishes the worker's final message (`codex exec --output-last-message`) as the result the way Agy does, refuses an existing result path, and bounds the `FALLBACK` to the final message and the last 200 lines of the tail; `SKILL.md` now says the executor takes only three arguments.
- **The 261 hand-typed `codex exec` calls, closed by the data.** The Codex executor was archived on 2026-09-18 and restored on 2026-11-10. Of the 261 calls, 245 (in 30 sessions) fall in the 53 days it did not exist, and 16 (in 4 of those same 30 sessions) come after it returned; 95 of the 245 commands also mention a review, so many were second opinions rather than units. The split reruns the Workflow's count of hand-typed `codex exec` commands (dispatchers excluded) in `/prun` sessions since 2026-09-20, divided at 2026-11-10. They record the gap, not an ongoing bypass, and the fix above is what keeps the dispatcher the easier path.
- **Milestone B stays open.** The recommendation is the 103 KB core with every step a coordinator runs each round in the first 60 KB, done as its own change with a plan review first.
