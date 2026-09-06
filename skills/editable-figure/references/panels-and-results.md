# Explanatory panels with compact results

## Give each panel a reading role

An introductory figure can answer two questions together: what does this work enable, and why should the reader care? Let the schematic carry the organizing idea and let a compact measured result provide scale or a consequential contrast. Use this composition when those roles support the same takeaway; a result panel is not mandatory.

A result already discussed later can still earn space in the first figure. Keep the selected comparison interpretable at the smaller size. Move the full experimental inventory and inferential details to their existing table or Results section. Do not hide a qualifier needed to understand the visible claim.

Apply the same decision to proposals and READMEs without copying the paper template. A proposal might pair its mechanism with clearly identified preliminary evidence. A README might pair a workflow with a verified output example. Neither needs a performance chart merely to look impressive.

## Allocate width and whitespace independently

1. Establish the usable width after outer margins.
2. Reserve a gutter that reads as separation between panels.
3. Divide the remaining width according to each panel's information load. For a requested large schematic and narrow result, about 3:1 is a reasonable first draft.
4. Inspect the actual visible bounds, including axis labels, markers, legends, annotations, and panel titles. Plot-area rectangles alone underestimate crowding.
5. Compare the inter-panel gap with gaps inside the schematic. The two panels should read as distinct units without losing their relationship.

Do not assign 75 percent and 25 percent of the full usable width and then discover that the gutter has no room. Avoid a divider when whitespace already separates the panels; when they look crowded, test more whitespace before adding a line.

Expanding the slide can preserve the drawing's internal geometry, but it reduces every label's printed size when the figure is still inserted at the same width. Compute:

`printed font pt = slide font pt * document figure width pt / slide width pt`

Inspect the resulting manuscript page or README viewport. Widening the canvas is a tradeoff, not free space. Tighten low-value content if the final labels become hard to read. See [native-powerpoint.md](native-powerpoint.md) for canvas resizing and group-transform pitfalls.

## Keep the numerical claim attached to its estimator

Read plotted values from an authoritative table, board, or experiment artifact. Prefer a parser shared with the paper's existing plotting code. Retain the input locator, series labels, transformation, and precision beside the builder. Do not infer values from image pixels when source data exists.

Before choosing the chart or caption, establish:

| Question | Why it matters |
|---|---|
| What metric, units, and sign are plotted? | A positive gap needs a named reference and direction. |
| Which methods, population, and observation budget are compared? | A baseline or prefix change can alter the meaning. |
| How are runs, seeds, or predictions aggregated? | Differences of reported means may differ from a registered paired estimator. |
| Are these point estimates or an inferential statement? | A significance label must correspond to the displayed estimand and applicable test. |
| Which test family or diagnostic scope applies? | A result in another state, corpus, or family does not establish this claim. |

For example, one CatchBench curve showed a quarter-prefix difference of printed mean AUCs of `0.113`, while the registered paired effect was `0.101` under a different averaging procedure. Both can be correct. Labelling the plotted `0.113` as the registered effect would be incorrect. The accepted inset showed descriptive gains and left inference in Results.

Preserve small negative values, ties, and non-monotonic behavior. Do not clip an inconvenient point or smooth a measured series into an invented trend. Two curves alone do not establish a cross-corpus significance claim. An unregistered comparison is not automatically evidence of no effect; it simply does not support that registered-test claim.

## Preserve just enough semantic guidance

A small legend or caption phrase can carry essential interpretation: nodes are steps, arcs are dependencies, hatching is unavailable future evidence. A candidate prediction must not look like a target label supplied to an evaluated method. Separate corpora must not look like a matched run across stages unless the source supports that pairing.

Remove repeated inventories and decorative text before removing these distinctions. The aim is fast understanding with sufficient evidence, not minimum word count.

## Keep revisions proportional to the feedback

If the author accepts the content and asks for more separation, change the spacing and inspect its consequences. Preserve the source values and chart/workbook parts where possible. Recheck the panel balance, label placement, effective font size, and final export. Do not reopen a settled concept or request approval for a reversible layout adjustment already authorized by the feedback.

When an independent review is requested, reconcile recommendations against the source and the user's requirements. Record accepted and rejected suggestions with short reasons, and identify the reviewed version. A later result-panel restoration or spacing change is a new local revision, not evidence that the earlier reviewer inspected those final bytes.

See [iteration-example.md](iteration-example.md) for the complete design progression and its case-specific measurements.
