# Defensive-Writing Calibration: Field Trial

Workstream: stop agent drafts of papers and proposals from attaching a caveat to every good result and from transcribing tables into prose, without a swing to overclaiming. Plan: `PLAN-defensive-writing.md` at the repo root (gitignored, maintainer-local); its § 10 holds the execution log. Shipped on 2026-10-06 as a field trial.

## What Shipped

| Repo | Change |
|---|---|
| agent-style v0.5.0 | RULE-08 names the caveat tail and keeps only qualifiers that change the claim. RULE-03 asks for the pattern with its key magnitude and leaves full results to tables. RULE-H examples stop stacking scores, and the semantic judge prompts check both directions. Bench report: `docs/bench-habit-v0.5.0.md`. |
| agent-config, anywhere-agents | One `AGENTS.md` Writing Defaults bullet. The `/vet` paper and proposal lenses check calibration in both directions. aa bundles agent-style `v0.5.0`. |
| agent-pack | The decision-support stance stays out of drafted manuscripts, and `venue-review-panel` item 7 checks understatement. |

## Why It Shipped with Two Unmet Criteria

On the release wording, the habit bench met the reflexive-qualifier criterion (3 to 0) and both pairwise criteria (62% and 69%). It missed the strict per-cell safety rule on three minor confirmed patterns: an extrapolated recommendation, an inconclusive difference called a "tie", and one reversed phrase. It also missed the numeric-density target, −13% against −25%, and Sonnet drafts did not move. Run 1 had shown that wording which cut numbers harder also dropped qualifiers that change the claim. The maintainer chose to run the release wording in daily work and revise it on evidence from real drafts, instead of tuning it further against a small synthetic bench.

## What to Watch

Signs that the wording swung too far, which call for a RULE-08 or RULE-03 revision:

- a recommendation or conclusion that reaches past what the results show;
- "tie", "comparable", or "matches" for a difference whose interval crosses zero;
- the weakest case or a loss missing from an abstract or a conclusion;
- a direction or a trend stated backwards.

Signs that the old habits persist:

- "however", "further work is needed", or "does not establish" attached to a result by habit;
- result paragraphs that restate a table cell by cell, most likely in Sonnet drafts;
- `/vet` reviews that ask for added qualifiers and never flag understatement.

## How to Revise

1. Edit the wording where it lives: agent-style `RULES.md` (RULE-03, RULE-08) followed by `scripts/build-compact.py`; the `AGENTS.md` Writing Defaults bullet in ac and aa; `skills/implement-review/references/review-lenses.md`; agent-pack `venue-review-panel` item 7; the Content and Expression section of agent-pack `skills/polish/SKILL.md` and the word-count rule in its step 3. `docs/writing-harness-map.md` keeps the current list of these homes.
2. Rerun the habit bench (`scripts/bench/habit/README.md` in agent-style) with the v0.5.0 compact pack as condition A, against the same criteria.
3. Release agent-style, move the aa bundled ref, and append the new ref to the aa ledger `_AUTO_RECONCILED_DEFAULT_REF_REWRITES`.

## How to Roll Back in One Project

Pin agent-style to `v0.4.2` under `packs:` in that project's `agent-config.yaml`. aa never bundled v0.4.2 as its default, so the ref ledger reads the pin as deliberate and leaves it in place. The pin rolls back the rule pack only; the `AGENTS.md` bullet and the `/vet` lenses stay.

## Patch Accretion (Added 2026-10-08)

The internal-writing records show a third form of defensive writing: each review round answers a finding by adding material, and nobody owns the total. QEMScore grew from 46 to 80 pages over its panel rounds before a dedicated trim cut it to 31. The agent-risk paper reached 59 to 63 pages and needed a readability round that cut its appendix from 48 to 37 pages. The shared `AGENTS.md` had the same history before its diet (74.6 KB to about 23 KB).

`AGENTS.md` adds revise-in-place, and the `/vet` lenses check accretion. For papers, proposals, and plans, `/vet` tracks size and consolidates after two rounds of growth with no new result or step. The panel protocol favors rewriting, moving, or cutting; repeat panels compare page counts.

Watch for papers or plans that grow without a new result or step, or requests for additions that name no missing evidence or explanation. Also watch for consolidation that cuts evidence a retained claim needs. The round-11 QEMScore panel found five trim defects; the fixes restored or corrected the affected passages.

## First Real-Draft Pass (Added 2026-11-15)

The acceptance run for `/polish` (`agent-pack/skills/polish/`) was the first time the watch list above met real drafts: a paper abstract, a results section, and a technical Markdown report, each polished in a throwaway repository by Claude Code and by Codex, then judged by three independent Claude agents. No edit added a number, citation, or claim, no table was transcribed into prose, and no habitual caveat tail was added. The swing toward cutting showed up instead, in compression. Codex turned a guarantee with a hedge into a flat statement of state and removed the stated reason a contrast was unresolved. Both agents deleted markers that flagged material added during review, and both rewrote `, so` joins to move a `voice_check` count. The skill's step 3 now keeps hedges, guarantees, stated causes, intervals, ties, losses, and status markers, keeps each relation at its strength and place, and treats a count as a prompt to reread. An exploratory second Codex run on that text lost no meaning-bearing word.

The final acceptance ran the staged skill. Claude Code changed 13 lines of a results section: three `, so` splits that keep the cause word, and nine RULE-G fixes that put full-sentence paragraph leads in sentence case. It dropped no hedge or status marker, changed no number, and listed eight facts for the author to verify. Codex made no edit to the Markdown report and returned its findings with locations, because that version had Codex review and report only, following the profile pack's rule that Claude writes prose a person will read. The maintainer then chose that whichever agent runs `/polish` as coordinator makes the edits, so a `/polish` request overrides that default and step 3's limits bind Codex as well; the exploratory Codex run on the revised step 3 is the evidence for that path.

## Seeded Check of the RULE-08 Line (Added 2026-11-15)

A `/polish` pass nested inside a paper round made one edit, skipped the reading pass, and gave a one-line report. The pass had audited a file of changed lines pasted together, which the detectors read as one paragraph. Since then, the skill has a round form, requires the step 2 list and a full report also when nested, and keeps intermediate files out of the repository.

The revised skill then ran twice on throwaway copies, and an Agy judge scored each run against a key the polishing agent never saw.

- **Paper round.** One round of a real paper's edits was polished as a step inside a larger task. The round held six seeded items:
  - two habitual caveat tails;
  - a general limitation that the Limitations section already states;
  - one that Limitations does not state;
  - an overloaded sentence;
  - a banned word.

  Seven load-bearing qualifiers were already in the text. The agent cut both tails and the repeated limitation and listed each cut. It kept the unstated limitation in place and flagged it, split the overloaded sentence with both causes kept, and replaced the banned word. All seven qualifiers survived, and the judge found no violation.
- **Proposal Introduction.** A federal proposal's Introduction was polished under its repository's local rules. The national-importance material and the aims preview stayed in place, and every edit stayed inside the Introduction. This run also showed that the pre-review audit did not report close variants of banned words already in a draft: the agent found four by reading. `style-audit.py` now reports them.

Everything else the judges found concerned the report, not the edits. One run named no lens items, and neither run accounted for every `CHECK`, so step 5 now asks for both. The proposal judge counted two "e.g." glosses, made to answer a `voice_check` glosses `CHECK`, as count-chasing. Author-voice step 4 names that move, so step 3 now allows it only where the sentence reads at least as well.

## Content and Expression Acceptance (Added 2026-11-18)

A user ran `/polish` on a paper's abstract, introduction, and conclusion and found them still hard to read. Step 3's limits on an edit had become the goal, and the pass made the smallest edit that cleared each finding. The maintainer restated the task: make the draft read well without changing its scientific content. Under the revised skill, the document keeps its facts, numbers, citations, links, definitions, and results, along with claim strength and scope, qualifiers, stated relations, ties, losses, and status markers. Wording, sentence structure, and sentence order within a section are open to the writer. A summary section may select from the body, and a passage that reads badly is rewritten by default. This revision restates the content limits of the two sections above in the Content and Expression section, and changes two of them: sentence order inside a section is open, and an interval may leave the prose when a table in the same section states it. Step 3 still says to reread a count and not edit only to move the number, and it no longer states the gloss allowance. `agent-pack/skills/polish/scripts/content_check.py` saves the targets before the pass and reports per-file count changes for the numbers, citations, links, labels, cross-references, and math expressions it recognizes. Qualifiers, claim strength, and relations are outside that count, and the writer checks them by reading, as step 4 requires.

Each acceptance run polished the abstract, the introduction, and the file holding the Discussion and the Conclusion of a committed paper, in a throwaway repository with the paper project's local rules. Before the runs, Agy extracted an 81-item key of the paper's claims, qualifiers, and relations, which no writer saw. Two Agy judges then scored each run. One compared the original and the polished text blind and recorded a preference or a tie for each section. The other gave each key item one of six verdicts (kept, kept elsewhere, weakened, strengthened, relation changed, lost) and listed new claims.

- **Calibration.** Both judges first scored a rewrite of the same sections that another session had made along the `author-voice` template. The reading judge preferred it in three of four sections and the original in the fourth. On content, the rewrite lost 4 items, weakened 4, strengthened 2, and added 2 new claims. That rewrite drifted on content, so the content criterion stayed: no item lost or strengthened and no new claim, with each weakened item or relation change checked against the original.
- **Small diffs.** The first two drafts of the change produced about 30 changed lines per run. Both writers treated every stated figure as fixed in place, which froze the abstract. Content moved to the document level, and the summary rule and a step-2 verdict of *redraft* or *edit in place* arrived.
- **Before review.** Two writers on the next draft changed 94 and 65 lines. The blind judge preferred one writer's text in all four sections. For the other writer it preferred the polished conclusion and the original abstract, and called the introduction and the Discussion ties. No key item was lost in either run. The content judge marked one item strengthened and two or three relation changes in each; in one run the strengthened item was a result stated for three named test conditions that became a result for the whole circuit family. Each run failed the content criterion because it strengthened one item.
- **After review.** Four `/vet` rounds tightened the content rules, and a run on that text changed 25 lines and marked every section *edit in place*. Its writer judged that a redraft would not help the reader, and the verdict then left that call to the writer. Step 2 now marks a section *redraft* on a stated trigger: more figures than the House Style and the template allow, more labels or terms than a first read can hold, or moves in an order that loses the thread.
- **With the trigger.** A rerun marked the abstract *redraft*, where `voice_check` counted 11 numeric figures against its abstract range of 0 to 2, and the introduction and the conclusion *edit in place*. It changed 47 lines. `content_check` listed 14 count changes, and every figure the summaries dropped or rounded is still stated in the body. The writer kept the three named test conditions because removing them would widen the claim, and left three facts unchanged and flagged them for the author to verify. In the blind reading, the polished abstract, introduction, and conclusion won and the Discussion tied. Scored against the key, the run lost or strengthened no item and added no claim. The content judge marked one relation change and one weakened item. A stated cause became a circumstance, a fault under the skill, where a cause stays a cause. For the weakened item, the writer added a post-hoc marker to the conclusion for a result the body marks post-hoc. That marker matches the body and adds no unsupported claim.

The `/vet` reviews by Codex, Agy, and Grok raised five High findings: a "judgment call" clause that licensed content edits, summary omission without the bounds on the answer, a `content_check` classification that called real changes harmless, a step 4 that undid permitted edits, and a Markdown link pattern with super-linear backtracking.

Watch for a summary section above its figure budget that comes back marked *edit in place*, and for a redraft that drops a bound on its answer (a tie, a loss, a qualifier, a named condition). Also watch for a summary that leaves out a result the author counts as part of the answer: the rule lets a summary omit a secondary detail the body states, which goes past "rewrite without changing content" as first stated.
