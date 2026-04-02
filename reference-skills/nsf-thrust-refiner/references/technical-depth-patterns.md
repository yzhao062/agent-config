# Technical Depth Patterns

Use this reference when a refined unit reads like expanded prose but still
lacks the technical density expected in this repository's prior proposals.

## Default Rule

Do not equate refinement with adding more paragraphs.

For most units, especially method-heavy subtasks, the patch should include at
least one compact technical object such as:

- a typed tuple or schema
- a graph or state definition
- a score, risk, or objective function
- a constrained mapping or alignment rule
- a short algorithmic pipeline with named stages

The point is not to make every thrust theorem-heavy. The point is to give the
reviewer something operational enough to imagine implementation.

## Family-Specific Guidance

### methodology-driven

Default target per unit:

- 1-3 compact equations or formal definitions across the unit
- explicit notation for the main signal, state, or objective
- subtask methods that are distinguishable at the mechanism level

Good technical depth often looks like:

- an ambiguity score
- a value or risk function
- a constraint set
- an optimization target
- a control or intervention rule

See the user's prior style in:

- `examples/proposals/NSF-Core-2026-Feb5th-Agentic-AD/01aim1.tex`

### ecosystem-building

Do not leave these as all-text infrastructure narratives.

Default target per technical task:

- one formal representation of the asset, graph, workflow, or interface being
  built
- one explicit staged pipeline or edge-typing rule
- one local measurable criterion tied to the representation

Good technical depth often looks like:

- an asset schema tuple
- a typed graph definition
- a link-confidence score
- a normalization function
- a provenance relation set

See the user's prior style in:

- `examples/proposals/GEO OSE Proposal/1thrust1-spatio-temporal-scoping.tex`

## Quantity Heuristic

Use notation sparingly but deliberately.

- For one refined unit, 1-3 compact formal blocks is usually enough.
- Avoid dropping equations into every paragraph.
- Each equation or definition should support a concrete method sentence nearby.

If the unit becomes harder to read because of notation, scale back.

## What Not To Do

- do not add abstract symbols with no operational meaning
- do not paste generic ML objectives that are not specific to the unit
- do not turn an ecosystem thrust into a math paper
- do not replace all readable prose with notation
