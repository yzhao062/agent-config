# Running Examples

Use a running example when proposal logic is easy for the team to name but hard
for reviewers to visualize.

## Consider It When

- the proposal is infrastructure-, platform-, or workflow-heavy
- the same abstract objects recur across sections, such as asset graphs, task
  objects, traces, or capsules
- the thrusts form a handoff chain and one example can show the progression
- adding more definitions would still leave the end-to-end flow unclear

## Skip It When

- domain breadth is itself the main point and one example would over-narrow the
  story
- each thrust genuinely serves a different user or problem family
- the example would become a case study that steals space from the proposal's
  reusable infrastructure claims

## How To Choose The Example

Prefer one persistent example over rotating examples.

Pick an example that:

- is easy to understand in one sentence
- requires multiple assets, repositories, or artifact types
- can be mapped cleanly to each thrust's role
- ends in a concrete downstream deliverable such as a trace, workflow, or
  reproducibility artifact

## Where To Put It

- intro or overview: one short mention if it helps anchor the full proposal
- each major thrust: 2-3 sentences or one compact callout mapping the same
  question to that thrust's infrastructure move
- one section only: if useful, include a pseudo-artifact sketch such as a trace
  snippet or workflow capsule outline
- evaluation: reuse the same example only if it clarifies what success looks
  like

## Format Guidance

- prefer a muted callout box or compact artifact sketch over a large decorative
  box
- use neutral proposal-safe styling instead of bright colors
- keep the box optional; normal prose is fine when the unit is already clear
- make the box answer: question, thrust-specific move, downstream handoff

## Failure Modes

- changing examples between thrusts so the reviewer keeps re-parsing context
- turning the example into a domain case study instead of a system explainer
- adding a box to every section whether it helps or not
- describing the example without showing what gets passed to the next thrust
