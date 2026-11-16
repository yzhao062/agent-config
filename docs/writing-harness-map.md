# Writing harness map

This file is the one place that says where each part of the writing harness lives. By harness we mean everything that shapes how an agent writes or revises prose: rule text the agent reads, hooks that check a write, scripts that measure a draft, skills that draft, review, or polish, review lenses, and the evidence behind them. The parts span four source repositories (`agent-config` and its mirror `anywhere-agents`, `agent-style`, `agent-pack`) and the consumer repositories.

Before adding or changing anything that shapes how an agent writes, find its home in the first table, put it there, make the mirrored edits that row names in the same change, and update this map in that change too. The map holds paths and owners, never rule text, so it does not drift from the rules it points at.

## Where a new piece goes

| To add or change | Home | Same change also updates |
|---|---|---|
| A general writing rule, for any author | `agent-style/RULES.md`, then `agent-style/scripts/build-compact.py` regenerates `docs/rule-pack-compact.md` | an `agent-style` release, then the default ref in `anywhere-agents/bootstrap/packs.yaml` |
| A habit of the maintainer's own voice | the House Style section of `agent-style/RULES.md`, which every consumer loads | `agent-pack/skills/author-voice` when the habit is section-level: `references/templates.md`, `references/exemplars.md`, and the ranges in `scripts/voice_check.py` |
| A word to ban | the Writing Defaults list in `agent-config/AGENTS.md` | the banned list in `scripts/guard.py`; both files mirror to `anywhere-agents`, and no test checks that the two lists agree |
| A mechanical check | a detector in `agent-style/packages/pypi/agent_style/review/detectors_mech.py` and its twin in `packages/npm/lib/review/detectors_mech.js` | the release gate in `scripts/guard.py` that turns the detector on for the advisory; `style-audit.py` inherits that gate |
| A review criterion | `skills/implement-review/references/review-lenses.md` (Paper, Proposal, or General) | `venue-review-panel/references/` in `agent-pack` when the venue panel should apply it too |
| A paper or proposal process rule (revision discipline, venue conventions) | `agent-pack/docs/paper-workflow.md` | `agent-pack/docs/paper-workflow-compact.md`, which consumers load |
| A default about who writes what, or which skill applies when | `agent-pack/docs/rule-pack.md` | `agent-pack/docs/rule-pack-compact.md`; measure the composed consumer size first, since `anywhere-agents/tests/test_composed_consumer_size.py` had a few bytes of headroom in October 2026 |
| A step in reviewing and polishing a draft, or a limit on what an edit may change | `agent-pack/skills/polish/SKILL.md`, which holds the procedure and the limits on an edit | nothing else; a style rule that the step applies goes to its own row above |
| An exception for one project or genre (federal proposals, peer reviews, email templates, social posts) | that repository's `AGENTS.local.md` | nothing shared; a rule that lives only in an agent's private memory is invisible to the other agents |
| Evidence for a change (bench, pilot, trial) | `agent-style/docs/bench-*.md` or `agent-config/docs/followups/` | a link from the CHANGELOG entry of the change it supports |

## Canonical homes by layer

| Layer | Piece | Home | When it acts | Agents |
|---|---|---|---|---|
| Rules read while writing | `agent-style` rules with the Escape Hatch and the House Style | `agent-style/RULES.md`; consumers load `docs/rule-pack-compact.md` | always, through the composed `AGENTS.md` | every agent that reads `AGENTS.md` |
| | Communication, Writing Defaults, Formatting Defaults | `agent-config/AGENTS.md` (byte-identical in `anywhere-agents`) | always | every agent |
| | Profile defaults: `agent-style` binding, `author-voice` on each paper or proposal section, the decision-support stance kept out of manuscripts | `agent-pack/docs/rule-pack-compact.md` | always | every agent |
| | Revision discipline and venue conventions | `agent-pack/docs/paper-workflow-compact.md` | always | every agent |
| Drafting | `author-voice`: templates, exemplars, `voice_check.py` | `agent-pack/skills/author-voice/` | on command, and by the profile rule on every paper or proposal section | Claude Code, Codex |
| | `bibref-filler` | `agent-pack/skills/bibref-filler/` (a copy also sits in `agent-config/skills/`) | on command | Claude Code, Codex |
| Write-time checks | Banned-word gate on `Write`, `Edit`, `MultiEdit`, and shell writes | `scripts/guard.py` | every prose write | Claude Code |
| | The same gate on `apply_patch` and shell writes | `scripts/guard.py` (`main_codex`) | every prose write | Codex, once the user trusts the hook |
| | `agent-style` advisory, release-gated: RULE-03 from 0.6.0, RULE-A from 0.7.0, the RULE-12 and RULE-08 document profiles from 0.8.0 | `scripts/guard.py` with the installed `agent_style` package | every `Write`, `Edit`, or `MultiEdit` to prose | Claude Code only |
| Review | `/vet` with its pre-review style audit and lenses | `skills/implement-review/` (`scripts/style-audit.py`, `references/review-lenses.md`) | on command, before a commit | any coordinator, cross-vendor reviewers |
| | Venue-calibrated three-agent panel | `agent-pack/skills/venue-review-panel/` | on command | Claude Code, Codex, Agy |
| | Citation audit | `agent-pack/skills/bibref-verify/` | on command | Claude Code, Codex |
| | `agent-style review` CLI: deterministic checks on any file; `--polish` needs a skill host | `agent-style/packages/pypi/agent_style/cli.py`, installed with the package | on command, in any repository | any agent with a shell |
| | `style-review` skill: semantic review and a revised copy beside the file | `agent-style/skills/style-review/` | on command, inside the `agent-style` repository only | Claude Code |
| Polish | `/polish`: review, edit in place, recheck, report | `agent-pack/skills/polish/` | on command | Claude Code edits; under Codex it reviews and reports, and the edits go to Claude or the user, as the profile pack says |
| | `readme-polish`: README layout and structure | `skills/readme-polish/` | on command | any |
| Evidence and decisions | Habit bench, House Style bench, human baseline | `agent-style/docs/bench-habit-v0.5.0.md`, `docs/bench-house-style.md`, `scripts/human-baseline/` | manual | |
| | Defensive-writing trial, expected-utility pilot, slimming audit | `agent-config/docs/followups/2026-10-06-defensive-writing-trial.md`, `2026-10-25-eu-guidance-pilot.md`, `2026-10-18-harness-slimming-audit.md` | manual | |
| | Student handoff of the whole workflow | `agent-config/docs/writing-harness-handoff.md` | manual | any |

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

Each item below was checked against the files on 2026-11-15. None is fixed by the change that added this map.

- The guard table row in `AGENTS.md` for the `agent-style` advisory does not say that the advisory runs under Claude Code only.
- `~/.codex/AGENTS.md` carries 13 of the 45 banned words and a narrower dash rule than `AGENTS.md`.
- No test checks that the banned list in `AGENTS.md` and the one in `scripts/guard.py` agree.
- `voice_check.py` accepts up to two figures in an abstract, while the House Style and `author-voice` say one rounded figure.
- `skills/readme-polish/references/patterns.md` prescribes an em dash in each feature bullet, against the Formatting Defaults dash rule.
- `skills/implement-review/SKILL.md` still names "the four checks" of General lens item 7, which now lists more.
- `skills/my-router/references/routing-table.md` lists `bibref-filler` and `bibref-verify` among the shared skills, though consumers get them from `agent-pack`. `agent-config/skills/` also keeps a second copy of both, and the two copies of `bibref-verify/SKILL.md` already differ.
- The `style-review` skill in `agent-style` reviews Markdown only, is not deployed to consumers, and its revision prompt does not mention the House Style.
- Consumer-local exceptions and writing rules kept only in Claude Code memory are listed in the maintainer's local follow-up plan, since several repositories are private.

## Refreshing this map

The 2026-11-15 inventory ran as five read-only `prun` units on Agy, one each for the shared harness, `agent-style`, `agent-pack`, the consumer repositories, and user-level files. Each unit returned one JSON line per piece with its home, layer, trigger, agents, and reach, plus the conflicts, stale references, and gaps it found. Rerun the same split when this map has drifted, open every claim before it enters the map, and keep consumer detail at the level of the table above.
