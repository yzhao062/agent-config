# Expected-utility guidance pilot, 2026-10-25

Does a short expected-utility principle steer an agent better than a list of rigid rules, or than no guidance, when a task invites optional additions such as a guard, a caveat, a test, an experiment, or a fix for a review finding? This question came from the style guide in opencode's `AGENTS.md` (<https://github.com/anomalyco/opencode/blob/dev/AGENTS.md>), whose rules include "avoid try/catch where possible" and "do not defensively revalidate values". The shared `AGENTS.md` has no code-side rule of that kind, and the `/vet` Code lens even asks reviewers to check edge cases and graceful error handling (`skills/implement-review/references/review-lenses.md`, Code items 2 and 5). An earlier [defensive-writing trial](2026-10-06-defensive-writing-trial.md) covered the prose side only.

The maintainer's position is that agents will keep getting more capable, so a high-level principle should age better than rigid rules and cost fewer bytes. This small pilot tests that position.

## Design

Each unit received the same three neutral project rules (Python 3.12, plain English, focused replies), followed by one of three conditions:

| Condition | Added text |
|---|---|
| none | nothing |
| rules | seven rigid rules in the style of opencode: avoid try/except, validate once at the boundary, no single-use helpers, avoid mocks, no caveats or hedges (limitations go in a Limitations section), fix only main-path bugs and data-loss risks in review, and run only the experiments the claim needs while skipping extra ablations, seeds, and comparisons |
| eu | "Weigh each optional addition (a guard, error handler, check, caveat, test, abstraction, experiment, or a fix for a review finding) by how likely it is to change an outcome that matters and how much, against its cost. Include it only when you can name that outcome. Accuracy and user-data safety are never traded." |

The eight tasks cover four domains with two tasks each:

- coding: a `deep_merge` whose only caller has already validated its input, and a hook that must let a tool call through when the payload is malformed;
- review triage: seven findings on a note-sync script, and six findings on a paper;
- writing: a results paragraph and a README Installation section, each with filler caveats and load-bearing qualifiers;
- experiment selection: an accuracy-and-speed claim with a GPU budget, and a one-line `guard.py` change with a time budget.

The decision and writing tasks have answer keys with positive items (should fix, run, or keep) and negative ones. Some items are traps, where a literal reading of the rigid rules points the wrong way. The full text and labels are in `2026-10-25-eu-guidance-pilot/scripts/tasks.py`.

Two models ran through `prun` on Agy: Gemini 3.8 Flash Medium and Gemini 4 Argon Medium. That gave 48 units, one run per task, condition, and model. Prompts carried opaque unit ids, and dispatch order was shuffled. Scoring is mechanical: hidden pytest tests and AST counts for code, a comparison with the labels for decisions, and keyword checks for writing. One Workflow run added two Sonnet agents. One judged the twelve writing outputs blind to condition, and it agreed with the keyword checks on every item. The other rebuilt the answer key from the task text without seeing the labels.

The answer key held. The independent key agreed with every label and marked three items as contested (E2, E8, F2). E2 is left out of the counts below because five of the six units skipped it.

## Round 1 results

| Condition | Errors, Flash | Errors, Argon | Errors | Lines of code, both coding tasks (Flash / Argon) |
|---|---|---|---|---|
| none | 1, plus 2 extra `try` blocks | 1 | Flash declined F1, a silent loss of user edits. Argon's hook denied malformed input and failed 2 hidden tests. | 48 / 45 |
| rules | 2 | 2 | Both models declined P3, a single-seed margin smaller than the seed spread. Both cut the limitation that every anomaly was injected. | 31 / 33 |
| eu | 0 | 0 | none | 42 / 21 |

Across the 16 units per condition, eu made no error, rules made 4, and none made 2. With one run per cell, Fisher's exact test of eu against rules gives p of about 0.1.

The rigid rules failed by literal application, and they failed the same way in both models. Argon declined P3 with the words "project rules state to run only the experiments needed and to skip extra seeds". Both models returned the same revised results paragraph, word for word, without the injected-anomaly limitation. Argon, the stronger of the two Gemini models, did not escape the rule.

Without guidance, the errors ran in both directions. Argon's hook failed closed on malformed input, although the task said users file a bug report every week when that happens. Flash wrote three `try` blocks where one was needed and declined the data-loss finding.

No condition over-added on the decision tasks, and every condition cut the filler caveats. The tasks were too easy on that side, so round 1 says nothing about whether the eu guidance reduces unprompted additions.

## Round 2

Round 2 ran on 2026-10-25 and made three changes.

- Four eu traps, each a needed step whose payoff looks small: checking three citations written from memory before a camera-ready upload, the required review round for a one-line rename, a backup before a script rewrites 2,000 user notes in place, and a leak check plus a baseline re-run after a change of data loader.
- Three open tasks with no hints: a TOML config reader, a line counter, and a three-sentence release summary of a table in which one dataset's AUROC falls from 0.781 to 0.751. The hidden tests for the two coding tasks check only the behavior the task states, and the summary must report the fall.
- Claude Sonnet 5.5 Medium as a third model, also through Agy. The eight round-1 tasks ran once more on every model and the seven new tasks ran twice, for 198 units.

Sonnet agents judged the 36 new writing outputs blind to condition, and another rebuilt the key for the four new decision tasks from the task text alone. That key agreed with every label and marked B5 and L5 as contested; no unit ran either. E2 stays out of the counts: the Gemini models skipped it in all six round-2 units, and Sonnet ran it in all three.

The scorer and the judge read every text block of an output whole. One Sonnet unit put its limitation in a second block, and one round-1 Argon README nested its install commands in `sh` blocks. The round-1 judge had seen that README cut off at the first nested block and counted the install line as lost; `round1/judge.json` records the correction.

### Round 2 results

All units in this table ran on Agy. Flash and Argon ran the round-1 tasks once per round, and Sonnet ran them once.

| Tasks | Units per condition | Units with an error: none | rules | eu |
|---|---|---|---|---|
| Round-1 tasks, both rounds | 40 | 5 | 8 | 0 |
| eu traps | 24 | 0 | 0 | 0 |
| Open tasks | 18 | 0 | 0 | 0 |

Repeated runs of one prompt on one model are not independent samples, so the fairer unit is the (task, model) pair. Of 45 pairs per condition, eu had an error in none, and the rigid rules and no guidance in 4 each. Fisher's exact test gives p of about 0.12 for eu against either.

**The rule failures replicated in the Gemini models and did not appear in Sonnet.** All eight rules errors are the two round-1 errors, repeated: Flash and Argon declined P3 and deleted the injected-anomaly limitation (Q4) in both rounds. Sonnet fixed P3. It kept Q4 by moving it into a separate Limitations block, which is what the rule asks for, and broke the single-block reply format to do it.

**Without guidance, the errors are scattered.** The five come from four pairs. Argon's hook failed closed on malformed input in both rounds, and Flash declined the data-loss finding F1 once. Sonnet fixed F2, an item the round-1 key marked contested, and kept the generic "confounding factors" hedge (Q5).

**The eu traps did not separate the conditions.** Across all 72 units, every step labelled run was run and every step labelled skip was declined. The eu guidance did not talk itself out of a needed step, but no other condition did either, so these traps were too easy to test it.

**No condition reduced unprompted code consistently.** All 36 open coding units passed the hidden tests, and none used a mock. Code size moved with the condition, but in a different direction for each model.

| Mean lines per open coding unit | Flash | Argon | Sonnet |
|---|---|---|---|
| none | 22 | 16 | 14 |
| rules | 8 | 18 | 8 |
| eu | 13 | 9 | 15 |

The eu guidance gave the shortest code with Argon and the longest with Sonnet. The rules shortened Flash and Sonnet code and lengthened Argon's, which read "validate input once at the boundary" as a call to add validation. Both Argon config readers under the rules check that the file exists before opening it, and one also rejects negative values. The task asks for neither check.

**Under the rules, half the release summaries gave both satimage values without naming the decrease.** Three of the six wrote only that AUROC "changes from 0.781 to 0.751" or an equivalent; no summary under the other conditions did. All 18 summaries gave the satimage numbers, and the judge found no wrong figure. In the other direction, four Sonnet summaries, two without guidance and two under eu, added advice for users of similar data, which the judge counted as filler.

### Claude Code check

Every unit above ran inside Agy's agent harness, while daily work runs in Claude Code and Codex. Nine units therefore ran as Claude Code Workflow subagents (Sonnet 5.5 at medium effort), one unit per agent: triage-paper, exp-leak, and open-config under each condition. Each received its Agy Sonnet prompt verbatim plus one line confining file writes to a scratch folder. These subagents also load this repository's `CLAUDE.md` and the maintainer's memory, so their none condition already carries the shared rules, and the check asks what each condition adds on top of them.

The six decision units made the same choices as their Agy twins, with no error. The code differed: the Claude Code config readers ran to 22, 9, and 15 lines under none, rules, and eu, against 7, 6, and 6 on Agy, with type checks and up to 11 test functions. With one unit per cell, this check cannot separate the harness from run-to-run variation.

### Codex check

Fifteen units ran through `codex exec` on `gpt-6-astra`, the maintainer's configured Codex model, at medium effort. They cover the four tasks where some condition had erred (triage-paper, writing-results, code-hook, and triage-code) plus open-config, once under each condition, each in its own scratch folder with the same prompt and extra line as the Claude Code units. Codex loads the global `~/.codex/AGENTS.md` on every run, and that file asks for narrow bug fixes without speculative fallbacks, so here too the none condition is not empty.

Codex made neither rules error. Under the rules it fixed P3, and it kept the injected-anomaly limitation by writing a Limitations heading inside the single text block. Its one error came under eu: it fixed F2, the contested finding about a partial copy left behind when a network drive disconnects while the local disk is full, to protect the existing copy. That is the first eu error in the pilot, and it follows the clause that user-data safety is never traded. Its code was compact in every condition: 9 to 11 lines for the config reader and 13 for the hook, with the one needed `try` and no failed hidden test. The three writing outputs were scored by the keyword checks alone, which agreed with the blind judge on all 150 keep-or-cut items across both rounds. A comparison by hand with the task text found no lost fact.

By quota meters read during the runs (the readings were not kept as records), the whole pilot used about 5 points of the Agy Gemini five-hour meter, 8 points of its Claude-and-GPT meter, under one point of the weekly Codex meter, and roughly 750k tokens on the Claude account, 420k of them for the nine Claude Code units.

## Reading for the guidance decision

The evidence favors the eu guidance over these rigid rules on a narrow basis: two rules ("skip extra seeds" and "no caveats") that the Gemini models applied against the task, every time. Two objections limit how far that carries.

- The rule failures appeared only in the Gemini models, which serve as `prun` workers. Sonnet, on Agy and in Claude Code, and Codex made no rules error. Sonnet made no eu error either, and Codex made one, on the contested F2. For the agents that load the shared `AGENTS.md`, these checks show no eu advantage.
- The eu guidance did not reduce unprompted code or caveats, and its traps never fired, so the case for it rests on avoiding literal-rule errors, not on shorter output.

Decision, 2026-10-25: the shared `AGENTS.md` stays unchanged.

## Limits

- The coordinator who proposed the eu guidance also wrote the tasks and the labels. Round 2 added traps against it, but no condition fell into them, so its weak side is still untested.
- Cells hold at most two runs, and repeated runs of one prompt are correlated. All but 24 units ran in Agy's harness, and the Claude Code and Codex checks hold one run per cell on a subset of tasks.
- The rules condition is one wording. A rule set with "unless it changes the claim" clauses would sit closer to the eu guidance.

## Files

`2026-10-25-eu-guidance-pilot/` holds:

- `scripts/`: the tasks and labels (`tasks.py`), the prompt builder for both rounds (`build.py`, with `python build.py 2` for round 2), the unit builder for the Claude Code and Codex checks (`build_cc.py`), the `prun` and Codex runners, the scorer, the judge input builder and merger, and `report.py`, which prints every table from one or more `scores.json` files;
- `hidden/`: the hidden tests for the four coding tasks;
- `round1/` and `round2/`: the raw unit outputs (48 and 198), `scores.json`, the blind judge verdicts (`judge.json`), and the independent answer key;
- `claude-code/` and `codex/`: the 9 Claude Code and 15 Codex outputs, their scores, and `twins.json`, which maps each one to its Agy unit.

From the folder, `python scripts/report.py round1/scores.json round2/scores.json` prints the pooled tables. The other scripts read and write an `agent-io/` folder beside them, so rescore in a scratch copy: `python scripts/build.py 2` rebuilds the round-2 ledger and prompts there, then copy `round2/results/` to `agent-io/results/` and `round2/judge.json` to `agent-io/`, and `python scripts/score.py` writes `agent-io/scores.json`, with the extracted code under `agent-io/code/`. Round 1 works the same way without the `2`; the Claude Code and Codex ledgers come from `build_cc.py`, whose docstring gives its arguments. `runner.py` names the maintainer's checkout of the `prun` dispatcher.
