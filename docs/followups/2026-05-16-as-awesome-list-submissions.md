# agent-style: `awesome-*` list submissions (2 drafted + 3 queued)

**Status**: open. **Source**: `agent-style/PLAN-awesome-claude-code-submission.md`, `agent-style/PLAN-awesome-copilot-submission.md` (both gitignored in agent-style), plus the next-batch table at `PLAN-awesome-claude-code-submission.md:168-177`. **Target**: human form-submission window (5-15 minutes per list).

## Why this file exists

The two drafted submissions and the three queued ones are gated on **human action** (filling web forms or opening upstream PRs), not on agent engineering work. They tend to be forgotten because they do not trigger an obvious "next step" in any one repo's CI or commit flow. Surfacing them from `agent-config/docs/followups/` makes them visible whenever the maintainer reviews the backlog from ac.

## Drafted and ready to submit

| Submission | Plan file | Upstream repo | Eligibility |
|---|---|---|---|
| awesome-claude-code | `agent-style/PLAN-awesome-claude-code-submission.md` | hesreallyhim/awesome-claude-code | Met 2026-04-26 |
| awesome-copilot | `agent-style/PLAN-awesome-copilot-submission.md` | github/awesome-copilot | Met (prereqs in plan file) |

Each plan file contains verbatim form contents, eligibility checks, and source-doc URLs. Submission is web-form filling or PR opening (5-15 min).

## Queued behind the first one landing

Per the table at `PLAN-awesome-claude-code-submission.md:168-177` (note the table lists 4 rows; `github/awesome-copilot` is the 3rd and is already covered by `PLAN-awesome-copilot-submission.md` as a separate dedicated draft, so the remaining 3 are):

- `PatrickJS/awesome-cursorrules` (Cursor adapter fit)
- `Ischca/awesome-agents-md` (AGENTS.md adapter fit)
- `RichardLitt/awesome-styleguides` (cross-domain writing-side fit)

Wait until at least one of the first two lands before queueing these, to avoid stacking up rejections that might share a reason.

## When to pull in

Any time the maintainer has 15-30 min and is reviewing the backlog from ac. No engineering blocker on either side; agent-style content is stable enough that the form submissions are not at risk of going stale.

## Effort estimate

5-15 min per list. Total for first 2: ~30 min. Queued 3 add another 30-45 min once the first batch is accepted.

## Cross-references

- `agent-style/PLAN-awesome-claude-code-submission.md` (entire): drafted form contents
- `agent-style/PLAN-awesome-copilot-submission.md` (entire): drafted PR contents
- `agent-style/PLAN-awesome-claude-code-submission.md:168-177`: next-batch table (4 rows; `github/awesome-copilot` row is duplicated by the dedicated copilot draft)
- `agent-style/TODO.md:11-71`: Copilot instruction-loading verification, which gates the awesome-copilot submission if Smoke A fails (stays in agent-style TODO.md per its own scope)
