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

1. Edit the wording where it lives: agent-style `RULES.md` (RULE-03, RULE-08) followed by `scripts/build-compact.py`; the `AGENTS.md` Writing Defaults bullet in ac and aa; `skills/implement-review/references/review-lenses.md`; agent-pack `venue-review-panel` item 7; the edit limits in step 3 of agent-pack `skills/polish/SKILL.md`. `docs/writing-harness-map.md` keeps the current list of these homes.
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
