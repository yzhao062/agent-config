# Refinement Modes

Use this file to decide what kind of unit-level work the user is actually
asking for.

## `gap-tightening`

Use when the unit is conceptually right but still generic.

Expected outcomes:

- stronger statement of the bottleneck
- clearer separation between prior work and the proposed move
- 1-2 sentences explaining why this gap matters for the proposal's main story

## `literature-grounding`

Use when the user asks for related work, stronger references, or when a claim
reads unsupported.

Expected outcomes:

- 2-6 targeted citations in the background or gap paragraph
- explicit grouping by literature function:
  baseline, competing method, enabling infrastructure, benchmark, or domain precedent
- visible TODOs when the paper title is known but the cite key is uncertain

Scope guard:

- treat this as a lightweight grounding mode inside a broader unit refinement
- if the user mainly wants a citation-first pass, explicit density control, or
  externally verified additions, switch to `nsf-bibref-filler`

## `technical-deepening`

Use when the unit needs sharper methods.

Expected outcomes:

- concrete technical object:
  representation, model component, operator, workflow step, control policy, or system interface
- explicit signal flow:
  input -> transformation -> decision/output
- clear distinction between subtasks
- bounded ambition; do not add three new projects into one thrust

## `local-evaluation`

Use when the unit needs measurable outcomes without rewriting all of
`20-evaluation.tex`.

Expected outcomes:

- one local milestone paragraph or one measurable-outcomes block
- success criteria that are testable within the unit
- direct feed-through into the global evaluation section if needed

## `figure-planning`

Use when a unit contains mechanism, workflow, or dependency logic that is hard
to scan in prose alone.

Expected outcomes:

- figure role
- one-sentence visual message
- proposed filename
- caption skeleton
- optional TODO for future asset creation

## `sync-followthrough`

Use after a unit changed materially.

Expected outcomes:

- patch the pre-unit bridge in `00-project-description.tex` if stale
- patch a matching sentence in `20-evaluation.tex` if measurable outcomes changed
- leave summary unchanged unless the user asked for summary sync
