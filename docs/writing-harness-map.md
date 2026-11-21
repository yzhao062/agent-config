# Writing harness map

This file is the one place that says where each part of the writing harness lives. By harness we mean everything that shapes how an agent writes or revises prose: rule text the agent reads, hooks that check a write, scripts that measure a draft, skills that draft, review, or polish, review lenses, and the evidence behind them. The parts span four source repositories (`agent-config` and its mirror `anywhere-agents`, `agent-style`, `agent-pack`) and the consumer repositories.

Before adding or changing anything that shapes how an agent writes, find its home in the first table, put it there, make the mirrored edits that row names in the same change, and update this map in that change too. The map holds paths and owners, never rule text, so it does not drift from the rules it points at.

## Where a new piece goes

| To add or change | Home | Same change also updates |
|---|---|---|
| A general writing rule, for any author | `agent-style/RULES.md`, then `agent-style/scripts/build-compact.py` regenerates `docs/rule-pack-compact.md` | an `agent-style` release, then the default ref in `anywhere-agents/bootstrap/packs.yaml` |
| A rule against defensive writing (a caveat tail, underclaiming, stacked figures, a defense nobody asked for, growth without new content) | RULE-08 and RULE-03 in `agent-style/RULES.md` | every other home of the concern that the change touches: the one-line bullets in the Writing Defaults of `AGENTS.md`, the Paper preamble, Paper items 4 and 8, and General item 8 in `review-lenses.md`, Revision Discipline in `agent-pack/docs/paper-workflow.md`, the Content and Expression section of `/polish` and the word-count rule in its step 3, and `venue-review-panel/references/review-protocol.md`; evidence goes to `docs/followups/2026-10-06-defensive-writing-trial.md` |
| A habit of the maintainer's own voice | the House Style section of `agent-style/RULES.md`, which every consumer loads | `agent-pack/skills/author-voice` when the habit is section-level: `references/templates.md`, `references/exemplars.md`, and the ranges in `scripts/voice_check.py` |
| A word to ban | the Writing Defaults list in `agent-config/AGENTS.md` | the banned list in `scripts/guard.py`, which `style-audit.py` also reads; both files mirror to `anywhere-agents`, and `tests/test_style_audit.py` fails when the two lists disagree |
| A mechanical check | a detector in `agent-style/packages/pypi/agent_style/review/detectors_mech.py` and its twin in `packages/npm/lib/review/detectors_mech.js` | the release gate in `scripts/guard.py` that turns the detector on for the advisory; `style-audit.py` inherits that gate |
| A review criterion | `skills/implement-review/references/review-lenses.md` (Paper, Proposal, or General) | `venue-review-panel/references/` in `agent-pack` when the venue panel should apply it too |
| An explanatory figure creation process | `skills/editable-figure/SKILL.md` and its linked references | the same skill tree in `anywhere-agents` and its wheel composer mirror |
| A paper or proposal process rule (revision discipline, venue conventions) | `agent-pack/docs/paper-workflow.md` | `agent-pack/docs/paper-workflow-compact.md`, which consumers load |
| A default about who writes what, or which skill applies when | `agent-pack/docs/rule-pack.md` | `agent-pack/docs/rule-pack-compact.md`; measure the composed consumer size first, since `anywhere-agents/tests/test_composed_consumer_size.py` had a few bytes of headroom in October 2026 |
| A step in reviewing and polishing a draft, or a limit on what an edit may change | `agent-pack/skills/polish/SKILL.md`, which holds the procedure and the line between content and expression, with its `scripts/content_check.py` | nothing else; a style rule that the step applies goes to its own row above |
| An exception for one project or genre (federal proposals, peer reviews, email templates, social posts) | that repository's `AGENTS.local.md` | nothing shared; a rule that lives only in an agent's private memory is invisible to the other agents |
| Evidence for a change (bench, pilot, trial) | `agent-style/docs/bench-*.md` or `agent-config/docs/followups/` | a link from the CHANGELOG entry of the change it supports |

## Canonical homes by layer

| Layer | Piece | Home | When it acts | Agents |
|---|---|---|---|---|
| Rules read while writing | `agent-style` rules with the Escape Hatch and the House Style | `agent-style/RULES.md`; consumers load `docs/rule-pack-compact.md` | always, through the composed `AGENTS.md` | every agent that reads `AGENTS.md` |
| | Communication, Writing Defaults, Formatting Defaults | `agent-config/AGENTS.md` (byte-identical in `anywhere-agents`) | always | every agent |
| | Profile defaults: `agent-style` binding, `/polish` as the one entry for drafting or revising prose (`author-voice` on each paper or proposal section where `/polish` is absent), the decision-support stance kept out of manuscripts | `agent-pack/docs/rule-pack-compact.md` | always | every agent |
| | Revision discipline and venue conventions | `agent-pack/docs/paper-workflow-compact.md` | always | every agent |
| Drafting | `author-voice`: templates, exemplars, `voice_check.py` | `agent-pack/skills/author-voice/` | through `/polish` on every paper or proposal section; by the profile rule directly only where `/polish` is absent; alone on command to read a model or measure a draft | Claude Code, Codex |
| | `bibref-filler` | `agent-pack/skills/bibref-filler/` (a copy also sits in `agent-config/skills/`) | on command | Claude Code, Codex |
| Figures | Quantitative paper figures and their data-derived annotations | `skills/programmatic-figure/` in both shared repositories | on command | any |
| | Editable explanatory figures (overview, mechanism, README) | `skills/editable-figure/` in both shared repositories | on command | any |
| Write-time checks | Banned-word gate on `Write`, `Edit`, `MultiEdit`, and shell writes | `scripts/guard.py` | every prose write | Claude Code |
| | The same gate on `apply_patch` and shell writes | `scripts/guard.py` (`main_codex`) | every prose write | Codex, once the user trusts the hook |
| | `agent-style` advisory, release-gated: RULE-03 from 0.6.0, RULE-A from 0.7.0, the RULE-12 and RULE-08 document profiles from 0.8.0 | `scripts/guard.py` with the installed `agent_style` package | every `Write`, `Edit`, or `MultiEdit` to prose | Claude Code only |
| Review | `/vet` with its pre-review style audit and lenses | `skills/implement-review/` (`scripts/style-audit.py`, `references/review-lenses.md`) | on command, before a commit | any coordinator, cross-vendor reviewers |
| | Venue-calibrated review panel | `agent-pack/skills/venue-review-panel/` | on command | Claude Code, Codex, Agy, Grok |
| | Citation audit | `agent-pack/skills/bibref-verify/` | on command | Claude Code, Codex |
| | `agent-style review` CLI: deterministic checks on any file; `--polish` needs a skill host | `agent-style/packages/pypi/agent_style/cli.py`, installed with the package | on command, in any repository | any agent with a shell |
| | `style-review` skill: semantic review and a revised copy beside the file | `agent-style/skills/style-review/` | on command, inside the `agent-style` repository only | Claude Code |
| Polish | `/polish`, the one entry for writing: read the rules and the author's models, plan, draft from sources or rewrite each paragraph that does not read well, check content, report | `agent-pack/skills/polish/`; `skills/my-router/SKILL.md` in `agent-config` routes writing requests to it | on command, and by the profile rule on every piece of prose a person will read | on request, the Claude Code or Codex coordinator edits; on an automatic pass, Claude drafts and a Codex or Agy coordinator hands off |
| | `readme-polish`: README layout and structure | `skills/readme-polish/` | on command | any |
| Evidence and decisions | Habit bench, House Style bench, human baseline | `agent-style/docs/bench-habit-v0.5.0.md`, `docs/bench-house-style.md`, `scripts/human-baseline/` | manual | |
| | Defensive-writing trial, expected-utility pilot, slimming audit | `agent-config/docs/followups/2026-10-06-defensive-writing-trial.md`, `2026-10-25-eu-guidance-pilot.md`, `2026-10-18-harness-slimming-audit.md` | manual | |
| | Student handoff of the whole workflow | `agent-config/docs/writing-harness-handoff.md` | manual | any |

## What `/polish` draws on

`/polish` is the one entry for writing. This table records where it reads each rule and runs each check, and a change that adds a piece to this map adds its row here too. `/polish` adds no style rule of its own. It runs the checks below and has the coordinating agent read the rule text, so a change to an existing rule or detector in these homes reaches the next pass without an edit to the skill. A new check reaches it through `implement-review/scripts/style-audit.py`, through `author-voice/scripts/voice_check.py` on a paper or proposal, through a new line among the diagnostics of the skill's step 4, or through `agent-pack/skills/polish/scripts/content_check.py`, which snapshots in step 3 and compares in step 4.

| Concern | Rule text the agent reads | Check the skill runs |
|---|---|---|
| Author voice | the House Style in the composed `AGENTS.md`; `author-voice` templates and exemplars for an abstract, introduction, or conclusion | `author-voice/scripts/voice_check.py`, papers and proposals only |
| Banned words | the Writing Defaults list in `AGENTS.md` | `style-audit.py`, which takes the list and its close variants from `guard.py`; the guard hook also blocks them at write time |
| `agent-style` rules | the composed rule pack | `implement-review/scripts/style-audit.py`, which takes the release-gated detector set from `guard.py` and runs it from the installed `agent_style` package |
| Defensive writing | RULE-08 and RULE-03, Revision Discipline, the review lenses named in the first table | the RULE-08 repeated-caveat detector inside `style-audit.py`, and the word count against the last commit |
| Revision discipline and venue conventions | Revision Discipline and the venue conventions of `paper-workflow` in the composed `AGENTS.md` | none; the step 1 reading and the step 2 plan |
| Project and genre conventions | the repository's `AGENTS.local.md` and every style source it names | none; step 1 reads them |
| Numbers and summary sections | the House Style and Writing Defaults on figures; Paper lens item 4; the `author-voice` templates | `voice_check.py` figure, pointer, and citation ranges for an abstract or conclusion; `content_check.py` for a removed, retokenized, or added value, and the step 4 reading for a move that keeps the count |
| The edit itself | the skill's Content and Expression section and steps 3 and 4 | `agent-pack/skills/polish/scripts/content_check.py`, which reports per-file count changes for the numbers, citations, links, labels, cross-references, and math expressions it recognizes; the coordinating agent checks backing, claim strength and scope, qualifiers, and relations against the baseline by reading |

## Coverage by agent

Claude Code reaches every row above. Codex reads the same composed `AGENTS.md` and the skills linked under `.agents/skills/`, and its hook runs the banned-word gate but not the `agent-style` advisory. Outside a bootstrapped repository Codex falls back to `~/.codex/AGENTS.md`, a hand-written file whose banned list covers 13 of the shared 45 words. Agy reads `AGENTS.md` as a `/vet` reviewer and as a `prun` worker, and no hook checks its writes. Claude Code's private memory is visible to Claude Code on one machine only, so a writing rule kept there reaches no other agent.

Mechanical coverage also depends on the file type. The RULE-12 sentence-length share reads only a complete LaTeX document. A LaTeX section file still gets the `, so` density and extreme-length checks, and a Markdown file only the extreme-length check; `voice_check.py` measures the share for a paper or proposal section. `style-audit.py` with `--all-lines` and file arguments reads the working tree, including untracked files.

## Consumer-local pieces

Consumers add genre-specific pieces of their own. Each belongs in its repository and follows the exception row of the first table; the list shows where they are, not what they say.

| Repository | Local writing pieces |
|---|---|
| `internal-writing` | `polish-section`, `restructure-paper`, `submission-gate`, `rebuttal-playbook`, a paper-writing guide |
| `NSF-Proposal-Template-Yue` | a proposal composer with its own style reference, a thrust refiner, a heading-case check, a proposal review panel |
| `internal-review` | peer-review and meta-review skills |
| `Letter-` | recommendation-letter drafting |
| `usc-slides` | deck, poster, and rehearsal-note skills |
| `yzhao062.github.io` | social-post skills with their own style references, CV condensing, citation audit |
| `usc-email` | reply templates |
| others | `AGENTS.local.md` sections only |

## Open follow-ups

This list is the backlog of the writing harness. Add an item when a gap or conflict turns up, with the file it concerns and the date it was checked; a change that fixes one deletes it here and names the fix in the CHANGELOG. Items without a date were checked on 2026-11-15.

- The profile pack still says Codex does not draft prose a person will read. `/polish` states its override in the skill only, because the compact profile counts against the composed consumer ceiling; mention the exception in `agent-pack/docs/rule-pack-compact.md` when that ceiling has room.
- The guard table row in `AGENTS.md` for the `agent-style` advisory does not say that the advisory runs under Claude Code only.
- `~/.codex/AGENTS.md` carries 13 of the 45 banned words and a narrower dash rule than `AGENTS.md`.
- `voice_check.py` accepts up to two figures in an abstract, while the House Style and `author-voice` say one rounded figure.
- `skills/readme-polish/references/patterns.md` prescribes an em dash in each feature bullet, against the Formatting Defaults dash rule.
- `skills/implement-review/SKILL.md` still names "the four checks" of General lens item 7, which now lists more.
- `skills/my-router/references/routing-table.md` lists `bibref-filler` and `bibref-verify` among the shared skills, though consumers get them from `agent-pack`. `agent-config/skills/` also keeps a second copy of both, and the two copies of `bibref-verify/SKILL.md` already differ.
- The `style-review` skill in `agent-style` reviews Markdown only, is not deployed to consumers, and its revision prompt does not mention the House Style.
- At the next `agent-style` release, after measuring the composed consumer size, add to the House Style and RULE-04 four section habits that `agent-pack/skills/author-voice/references/templates.md` has carried since 2026-11-19. Abstracts and conclusions state the answer the body supports (for proposed work, the question the work will test), point at no section, appendix, figure, or table (RULE-04 already names tables and figures), and cite papers rarely. Contribution lists in the introduction use short heads in the MetaOD form. `voice_check.py` measures the pointers, citations, and heads, and a reader judges the answer. Checked 2026-11-19.
- Consumer-local exceptions and writing rules kept only in Claude Code memory are listed in the maintainer's local follow-up plan, since several repositories are private.

## Refreshing this map

The 2026-11-15 inventory ran as five read-only `prun` units on Agy, one each for the shared harness, `agent-style`, `agent-pack`, the consumer repositories, and user-level files. Each unit returned one JSON line per piece with its home, layer, trigger, agents, and reach, plus the conflicts, stale references, and gaps it found. Rerun the same split when this map has drifted, open every claim before it enters the map, and keep consumer detail at the level of the table above.
