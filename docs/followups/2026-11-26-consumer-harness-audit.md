# Consumer Sessions Under the Harness Before v0.11.0: An Audit (2026-11-26)

Before tagging v0.11.0, the maintainer asked whether real sessions in the consumer repositories on this machine behaved the way the harness and its skills now say they should, from the guard and bootstrap down to `/vet`, `/prun`, and `/polish`. The audit is non-defensive: it reports what happened and proposes no new gates. A rule that agents skip without harm is reported as a finding about the rule.

## Verdict

Nothing found blocks the release in the sense of lost work or a wrong result reaching the user unannounced. The new mechanisms that ship in v0.11.0 mostly work as described: the approval move to push and publish, snapshot cleanup, the model registry's requested-versus-actual records, the Codex guard hook, and the `prun` executor rules. Five small harness bugs turned up, all in scripts, and the maintainer chose F1 to F4 for v0.11.0. Only one of the five (F5) came in with this cycle's changes; the other four predate v0.10.0 and surfaced because this cycle exercised them more. A set of `/vet` rules that coordinators routinely skip also emerged, the step 3 channel line above all. Those rules can be reworded, narrowed, or dropped; they do not call for enforcement.

## Method

The scope was every consumer session active since 2026-11-15, plus mechanical counts back to 2026-11-10 when the model registry landed.

1. **Mechanical layer.** Scripts counted events over 124 Claude Code sessions in 13 consumer repositories: guard denials and asks by gate, slash commands, Skill calls, `SKILL.md` reads, dispatches by backend, Workflow and Agent spawns, and advisor calls. They also read the 613 `review-model` and `model-actual` records in temp state directories, the leftover staged snapshots, and every consumer's `last-run.json`.
2. **Judgment layer.** Nine Agy units read episode logs cut from 70 sessions: four on `/vet`, two on `/prun`, one on `/polish`, and two on interactive Codex sessions. Each unit judged a fixed list of checks against the rule text in effect at the time of the episode. The three repositories holding mail, letters, and admin records were counted mechanically and never sent to Agy.
3. **Verification layer.** A five-agent Claude Workflow re-read 78 of the units' claims against the raw transcripts. It confirmed most of them and corrected several counts. A few claims did not survive, and the pass found cases the units had missed.

A number below comes from a script or from the verification pass unless it is marked *(unit count)*, which means it rests on one Agy unit's reading. Unit results, the expectations map, the scripts, and the verification output stay in the session scratchpad under `harness-audit/`; they name sessions and repositories, which this note leaves out because the repository is public.

## Candidate Fixes

| ID | Finding | Since | Evidence | Fix |
|---|---|---|---|---|
| F1 | The nested `git init` gate does not expand a variable assigned earlier in the same command, so `R=/private/tmp/...; git init -q $R` is read as a path relative to the cwd and denied as a nested repository | 2026-09-13 (`8fa9719`) | 11 denials in 7 Claude Code sessions and 3 of the 4 Codex denials since 11-15. Every one targeted a scratch path for a `/vet` isolated repo or a `prun` clone, and each case checked was retried with a literal path. Reproduced against the deployed `guard.py`. | Resolve the target with the same assignment and environment expansion the shell-write gate already uses. Treat a still-unresolved `$var` as unknown rather than as a relative path. |
| F2 | `health-check.py` Check 7 reports `lines=` counted in the code-stripped text, while step 7 tells the coordinator to read those lines in the review file | first health check (2026-05); the 11-15 stripper rewrite kept it | Replaying the check on one review gives `lines=40,57,85,87`, while the flagged phrases sit on file lines 98, 135, and later. | Keep the newlines of each stripped span, as the guard's style advisory already does. |
| F3 | Check 7 phrases have no word boundaries | 2026-05 | Check 7 warned in 99 of 228 health-check runs since 11-15 (43%), and Check 8 in 58 (25%). Of 18 sampled Check 7 warnings, 12 were word matches on prose: `quota` inside "quotation" about nine times, `i cannot` inside "CLI cannot", and `unauthorized` in manuscript text. The other 6 were real tool limits that did not block the review. | Add `\b` boundaries to the phrase list. This continues IR-17 of the 2026-11-14 audit. |
| F4 | Check 6 hard-FAILs a review that discusses the plan without writing its filename | 2026-05; runs only when the coordinator adds `--prompt-file`, which the step 7 command still omits | 4 FAIL lines in 2 sessions, all on valid VERIFIED reviews that engaged the plan ("as the plan says") but never named `PLAN-*.md`. No coordinator refused them. One told the user "health check normal" while the FAIL was on screen. | Downgrade a filename miss to a WARN, or accept a reference to "the plan" when the prompt supplied exactly one plan. Do not keep it as a hard refusal that coordinators override by hand. |
| F5 | A refused Claude review is recorded as a model mismatch | 2026-11-10 (`d21e08f`, this cycle) | On 11-26 the Claude reviewer was blocked by a `general_harms` safeguard. `claude_actual` read the `<synthetic>` error message and wrote `actual=<synthetic> status=mismatch`. The Codex coordinator still told the user the review was refused. | Recognize `<synthetic>` and `stop_reason: refusal` in `claude_actual` and label the round refused, not mismatched. |

Two smaller items are candidates too.

- **Codex banner placeholder.** `render_banner.py` puts `<model>` on the Claude Code row. When Codex follows AGENTS.md literally ("with `<model>` replaced by your model id"), the user sees the Claude Code row labelled with a GPT model. This happened in 3 sessions.
- **Auto mode for the Agy and Codex dispatchers.** The auto-mode classifier denied `dispatch-task-agy.py` and `dispatch-task.sh` (`[Unauthorized Access]`) in two sessions and let `dispatch-task-grok.py` through. The only `autoMode.allow` entry, which `prun/references/grok-executor.md` documents, names the Grok dispatchers. A user-named three-agent route therefore ran on Grok alone. An equivalent documented entry for the Agy and Codex dispatchers would remove the asymmetry.

## Rules Agents Routinely Skip

These are the rule-level findings. In none of them did the skip produce a wrong output that the user was not told about.

**`/vet` channel line (step 3, made explicit on 11-17).** The line was missing or came after the dispatch in 41 of 45 exercised episodes *(unit count; a looser form of the rule held before 11-17)*. No user asked about it.

**`/vet` reviewer set carried through later rounds.** Of about 52 multi-round Claude-coordinated loops after 11-17, 14 dropped a reviewer in a later round with no user words and no failure behind it. The usual move was to re-send the round only to the reviewer that still blocked. In 3 more loops, a bare or "quick" `/vet` ran Codex alone from round 1, although the default resolves to Codex and Agy, and one more dropped Codex after a hard health-check FAIL. The coordinator named the reviewer it sent, before or within seconds of dispatch, in 17 of 18 narrowed loops and asked first in none. One case is a misstatement: in one paper loop the coordinator said "Codex only, as you said", while the environment printed `both` and no user line names Codex. The changes that only the remaining reviewer saw reached a commit, push, deploy, or pasted deliverable in all 14 loops, each after the user approved the push. No wrong output traces to the narrowing, and in one loop the single remaining reviewer caught an error that a `/polish` rewrite had introduced. The written exceptions are the user's words and a failure path. They do not cover a confirming round sent only to the blocking reviewer, a "quick" `/vet`, or a reviewer at 0% quota before dispatch. Either the rule names those cases or the practice continues.

**`/vet` loop stop.** Seven loops applied the last round's Will fix edits and stopped while a reviewer still said BLOCK, with no confirming round. In every case the agent chose the stop and said plainly that the last edits were unreviewed. The user then pushed, deployed, or moved on. Rule B and step 11 imply another round. The text does not cover a stop for quota, for the user's stated aversion to defensive rounds, or at the point of push approval. Agents therefore treat disclosure plus the user's decision as the exit.

**`/vet` round report and WARN readings.** The opening line requires each Auto-terminal round to report the reviewer, its review file, and the health-check result. Most summaries named only the verdicts *(unit count)*. Step 7 asks that each WARN reading be recorded in the round summary, and most summaries left it out *(unit count)*. Given F2 and F3, coordinators had reason to treat WARN output as noise.

**`/vet` health check skipped or FAIL overridden.** The health check never ran in four loops: for one Agy round in the first, nine rounds in the second, two rounds in the third, and one round in the fourth. The skips cluster after compaction and in runs that replaced `auto-watch.sh` with a custom wrapper. Eight FAIL lines in seven rounds were not routed through section 1c. Three were true positives: the concurrency collision below, plus a Check 5 and a Check 10 caused by short custom prompts that left out the save contract. The other five were false positives: one from the four-backtick parser bug, 3.5 hours before its fix in `0878a02`, and the four F4 lines. None led to a wrong output.

**`/vet` skill reload.** For at least 36 of 44 `/vet` requests after 11-15, the coordinator read `implement-review/SKILL.md` again before dispatch. The other 8 relied on a read earlier in the session. Here the loading mechanism matters. `prun` and `polish` are native `.claude/skills/` entries, so the Skill tool loads the whole `SKILL.md` and Claude Code re-injects it after compaction; the transcripts show "Re-invocation of /prun ... the full instructions follow". `vet` is a command alias, so the Skill tool injects only the 1.5 KB pointer. A coordinator whose earlier read was compacted away loses the round checklist, and that matches where the health-check skips cluster.

**`/vet` watcher.** Coordinators replaced `auto-watch.sh` with their own wrappers, `nohup` launches, or `sleep` polling in at least five sessions *(unit count)*. In one case this ran the health check while Grok was still `ALIVE`.

**`prun` ledger and exit check.** About 3 of 22 runs kept and updated the ledger the skill describes. Five kept part of one, and the rest kept none, with no visible harm. The reconcile step says a nonzero dispatcher exit fails a unit, but the common launch patterns leave no exit code to read. A `&` in a foreground call loses it, `dispatch-task-agy.py` writes no exit file, and `monitor.sh` records none. In at least five sessions, coordinators probed for `exit-code`, `exit`, or `status` files that do not exist. They then used the dead dispatcher pid, the final status in the tail, and `model-actual` instead. Writing `<state-dir>/exit-code` would make the existing rule checkable.

**`/polish`.** Under the version that requires showing the step 2 list before any edit, at least four checked runs edited first. Nested passes gave the step 5 report after dispatching `/vet` but before any review returned, which the text leaves ambiguous. Three passes changed a claim or scope, and `/vet` caught each before it reached the user.

**Router and banner.** `my-router` was read in 6 of the 22 interactive Claude Code sessions that started after 11-15, and skills were still invoked whenever the user named them. Since September, the banner was missing from the first turn in about half of interactive sessions. In four spot checks the session wrote the acknowledgement file without printing the banner, which the gate allows because it checks the file and not the reply. Both patterns predate this release.

## Codex Sessions

Codex ran bootstrap in all 22 interactive consumer sessions since 11-15, launching it as a background exec, and in about 9 of the 22 it kept working before reading the result. The banner appeared in only 4 sessions, none of them among the last 9, while all 3 Codex sessions in the source repository printed it. Nothing enforces the banner under Codex: the guard's banner gate and the SessionStart hook are Claude-only, and `docs/codex-desktop-custom-instructions.md` leaves banner emission out on purpose. Keeping the banner rule for Codex in AGENTS.md is a choice to make explicitly.

Codex read `AGENTS.local.md` in 21 of 22 sessions, loaded skills on `/<name>`, and spawned sub-agents only when the user asked. Most `/vet` loops it coordinated followed Rule A, and one session edited twice while a Claude reviewer was still pending.

Of 44 push episodes in 25 Codex sessions, the user's own message already named the push in 41 or 42. In all but about 5, Codex showed the command and ran it in the same turn; at least 5 asked first. One push went to a new remote branch that Codex named itself, after a push to `main` was rejected, and Codex disclosed it. AGENTS.md does not say whether a push named in the same request counts as the approval. Codex's practice matches the maintainer's stated preference to approve once per change, so a sentence in Git Safety would settle the question.

The guard hook does fire inside Codex Desktop's code-mode exec. Four denials were recorded after 11-15: the three F1 false positives and one correct writing-style deny that the agent rerouted to an `agent-io` path.

When Codex delegates prose to `claude -p` from a consumer root, each run is a SessionStart: it reruns bootstrap and rewrites `.agent-config/session-event.json`. The model also printed the banner into stdout in 24 of 44 matched runs, and Codex had to cut it out of the draft. Such runs are one of several writers that advance the session event behind a long-lived interactive session, which never re-acknowledges after a resume. In the one long session traced, they accounted for a minority of its advisories. Other sessions' startups and resumes accounted for more, and a write a few seconds before each of the session's own resumes was the largest share, from a writer not identified. Together these produced 13,371 `[banner-gate] SessionStart re-fire detected` advisories since 11-10. The lines go to stderr with exit 0 and never reached a model-bound record, so they cost nothing beyond log noise.

## Other Observations

- **Concurrent `/vet` loops in one repository.** Two loops share the repo-root `Review-<Reviewer>.md` names. On 11-26 a round-13 `Review-Codex.md` from one session overwrote round 12 of another. Check 3 caught it, and the coordinator recovered its own review from the dispatch tail and told the user. The skill covers stale files from finished loops but not two live loops.
- **Agy result written to the wrong directory.** In one 20-unit run on 11-24, 4 workers wrote their real result into a sibling directory whose session id they had mistyped. The dispatcher then published the worker's 1.1 KB closing reply at the expected path, and `monitor` reported the units done. Only the project wrapper's size check caught it. The same failure appeared at a larger scale on 11-13.
- **One leftover staged snapshot.** A Claude reviewer died when the user aborted a Codex turn on 11-24, and the kill left no chance for the exit cleanup. Every other dispatcher since the 11-22 fix removed its snapshot.

## Working as Intended

- **Approval at the edge.** After the guard refresh on 11-22 at 18:37 PST, no commit or `rm -rf` prompt fired. The three that appear later in UTC timestamps all predate the refresh. Push prompts fired for pushes.
- **Model records.** Of the 613 records since 11-10, 604 read `status=ok`. The other nine are five test-fixture runs, two reviews still in flight when read, the reviewer killed on 11-24, and F5.
- **Fan-out.** All 116 Workflow runs since 11-15 followed a route the user had chosen for the task. Of the 22 Agent calls, 21 were bounded web-fetch lookups and one was a single editing helper inside a Workflow-routed task. Every Codex or Grok `prun` unit had been named by the user, and no coordinator subagent filled a reviewer slot.
- **`prun` hygiene.** Executor choice, fresh result paths, `agent-io` layout, and throwaway clones were as specified in every executed run.
- **Bootstrap.** All 13 consumers with sessions in the window report `completed: true` with no warnings.

## Disposition

The maintainer sorted the findings by whether they can go wrong unnoticed and how often they occur, then decided what v0.11.0 fixes.

**Fixed for v0.11.0.**

- F1, the nested `git init` gate: it now expands variables first.
- F2, F3, and F4 in `health-check.py`: line numbers, word boundaries, and Check 6 as a WARN.
- The `vet` alias now loads `implement-review` through the Skill tool where the deployed skill is the first match in the lookup order. The tool then carries the whole `SKILL.md`, and a re-invocation after compaction reloads it.
- The Agy `prun` dispatcher adopts a result that the worker wrote under a mistyped path its final response names.
- The `prun` references describe the auto-mode entry for the Agy and Codex dispatchers. The maintainer's machine-local entry now covers them.

**Recorded, not fixed.** Each of these is rare, cosmetic, or a rule that agents skip without harm.

- F5. A safeguard refusal is labelled a model mismatch (one case). The coordinator still told the user the review was refused.
- Two live `/vet` loops in one repository share the repo-root `Review-<Reviewer>.md` names (one case). Check 3 caught it.
- A dispatcher killed with its parent leaves its staged snapshot behind (one case).
- The `[banner-gate]` re-fire advisories are log noise only.
- Banner presentation. The banner was missing from about half of Claude Code first turns, and Codex printed it in 4 of 22 sessions. When Codex did print it, the `<model>` placeholder sat on the Claude Code row.
- Rules skipped without harm, candidates to drop or reword rather than enforce:
  - the `/vet` channel line;
  - the per-round report of the review file and health-check result;
  - the `prun` ledger;
  - reading `my-router` before every task.
- The `prun` reconcile step asks for a dispatcher exit code, which the common launch patterns never record. Writing `<state-dir>/exit-code` would make the step checkable.
- Codex treats a push named in the same request as the approval. A sentence in Git Safety would settle whether that counts.

**Open decision.** The maintainer has to decide two things about how the final round is reviewed. One is whether a confirming round may go only to the reviewer that still blocks. The other is whether a loop may stop after its last Will fix edits with the stop disclosed. Both practices are common. Coordinators disclosed all seven stops and named the reviewer before or near dispatch in 17 of 18 narrowed loops, no wrong output traces to either practice, and the current text forbids neither cleanly. The one case where a coordinator attributed its own choice of reviewer to the user stays on record here.

## Limits

- **Episode cuts.** Episodes run from one user prompt to the next. The `/vet` inventory missed about a dozen loops, which the verification pass then scanned.
- **Dropped meta messages.** The event logs drop meta messages, so the units' skill-load verdicts were recomputed from the raw transcripts.
- **Codex coverage.** The Codex units read 27 rollouts. Only the push, hook, and banner checks were extended to every rollout with events since 11-15.
- **Excluded repositories.** The three mail, letter, and admin repositories were never sent to Agy. The Claude verification pass read their Codex rollouts for the push, hook, and banner checks only.
- **Self-audit.** The agents under audit were mostly Claude. Gemini judged first and Claude verified, so the second read is not vendor-independent for Claude's own behaviour.
