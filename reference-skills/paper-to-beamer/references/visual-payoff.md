# Visual Payoff

Use this to keep the deck readable at presentation speed, not merely complete on paper.
Prefer readability, robustness, and low regression risk over visual novelty.

## Core Principle

Protect the existing strengths of the deck:

- clear problem framing
- explicit contributions
- coherent method story
- interpretable evidence
- honest caveats
- clean takeaways

Do not trade these for more visual complexity.

The baseline deck should already be clear through good titles, clean section structure, selective paper figures or tables, and concise interpretation text.
New visuals are optional improvements, not requirements.
If a new visual is added, prefer one that is deterministic, source-built, and easy to check against the paper.

## Default Baseline

Assume the safest baseline is:

- a strong slide title
- one primary object of attention
- minimal supporting text
- one clear takeaway

If the slide already works in that form, do not add more.

## No-Regret Rule

Every slide should satisfy all three conditions:

- the slide still works without any newly added visual
- any added visual makes the slide easier to understand in about 3 to 5 seconds
- if the gain is uncertain, keep the simpler version

Prefer omission over weak augmentation.

## Planning Summary

Before writing the deck and before changing visuals, identify:

- strongest visual anchor
- best method visual
- best result visual
- whether a concrete before-vs-after example exists
- weakest current slide by readability
- simplest possible improvement for that slide
- safest possible added visual for that slide
- fallback if the change is weaker after compile
- slides that are too text-heavy
- longest text-only streak in the current plan
- slides that should stay text-first
- tables that should remain tables
- tables that should be reduced
- figures that should be cropped, reduced, or replaced by a source-built schematic

## Slide-Level Diagnosis

Before changing any slide, classify it as exactly one of:

- text-first
- figure-first
- table-first
- example-first
- equation-first

Each slide should have one dominant mode.
If uncertain, keep the slide text-first.

## One Primary Object Rule

Each slide should have one primary object of attention:

- one figure
- one table
- one formula block
- one compact comparison box
- one short takeaway statement

Do not make the audience choose among multiple equally important objects.

## Safe Revision Order

For any slide that feels weak, apply the smallest reasonable change first:

1. tighten the title
2. shorten or regroup bullets
3. add one takeaway line under the current content
4. crop and enlarge one paper figure panel
5. reduce a table to the rows and columns needed for the claim
6. split one overloaded slide into two simpler slides
7. add one small comparison box or delta callout
8. add one simple source-built schematic or before-vs-after visual

Do not jump straight to a subjective redraw or hand-crafted illustration.

## Usefulness Gate

Only add a non-paper visual if it passes all of these checks:

1. It supports one clear message on the slide.
2. It is understandable in about 3 to 5 seconds.
3. It is easier to explain than the text-only or paper-figure version.
4. It uses the same visual style family as the rest of the deck.
5. It does not require a long spoken setup to make sense.
6. It can be regenerated or revised from explicit structure or data without aesthetic guesswork.

If any check fails, do not add the visual.

## Preferred Low-Risk Additions

Safest additions:

- a simplified before-vs-after example
- a compact system or threat-model schematic built from explicit components and links
- a minimal deck-native method schematic or toy walkthrough when the paper figure is too dense
- a reduced chart derived from one paper table
- a cropped figure or reduced source-built schematic derived from one dense paper figure
- a small comparison strip such as prior assumption vs proposed view

By default, avoid:

- decorative stock photos
- abstract illustrations without direct technical meaning
- style-heavy icon collages
- fully new complex diagrams with many moving parts
- visuals whose quality depends more on aesthetic judgment than technical clarity
- freehand redraws that are not driven by explicit structure or data

## Before-vs-After Rule

If the paper concerns attacks, failures, robustness, retrieval behavior, ranking behavior, generation behavior, or system behavior, prefer one concrete before-vs-after example when the paper naturally supports it.

Examples:

- original document vs edited document
- before attack vs after attack retrieval
- baseline output vs manipulated output
- benign case vs failure case
- original ranking vs changed ranking

This slide should show one operational effect, not the whole method.
Do not force this when the paper has no natural example.

## Dense Figure Policy

For each paper figure or table, choose exactly one of:

- reuse directly
- crop and enlarge
- reduce to a source-built schematic
- omit

Prefer direct reuse only when the original is already clean at presentation scale.
Prefer crop-and-enlarge when only one panel matters or labels are too small.

If a figure has many tiny labels, many subpanels, or paper-specific layout clutter, do not use it as the slide's only explanation object.

Safer options:

- crop one subpanel
- pair the figure with 1 to 2 short guiding bullets
- split the figure across two slides
- replace it with a simpler source-built schematic only if the schematic is clearly easier to read and driven by explicit structure

If simplification is not obviously safer, keep the original figure or omit it.

## Overview Figure Rule

If the paper has a large method-overview figure, do not assume it should appear as-is.

Safer options:

- replace it with a 3-step strip
- crop the figure into one step per slide
- keep the original in backup and use a simplified version in the main path
- build a small deck-native schematic, timeline, toy trace, state diagram, or graph view when that is clearer than reusing the full paper figure and the structure can be expressed explicitly in source

The main path should favor readability over full paper coverage.

## Method Block Visual Coupling

For method-heavy papers, do not treat each method slide as a fresh visual problem.

Prefer one repeated method visual family:

- one running example that appears across multiple slides
- one consistent color mapping for agents, modules, or stages
- one recurring text strip, score trace, graph, or pipeline scaffold

This reduces cognitive reset cost for non-expert audiences.

If the method block currently explains several abstractions only with equations and bullets, first ask whether one recurring visual scaffold can carry them instead.

## Non-Expert Comprehension Gate

Before finalizing a method-heavy deck, check each main-path method slide:

1. Could a broad CS listener identify the single new idea on this slide in about 5 seconds?
2. Does the slide reuse enough visual context from the previous method slide?
3. Is there more than one newly introduced abstract object?
4. If an equation appears, is there also one intuitive label, one short takeaway, or one companion visual?

If the answer to 1 or 2 is no, or the answer to 3 is yes, revise before adding more detail.

## Table Policy

A table may stay a table.
Do not convert tables into charts by default.

Keep the table when:

- exact values matter
- multiple metrics matter at the same time
- the table is already readable
- a chart would need extra styling or cleanup

Reduce the table when:

- the slide supports one main claim
- only a subset of rows or columns matters
- the full table is harder to scan than the claim itself

Safe table reductions:

- keep only baseline vs method
- keep only one metric family
- keep only the strongest rows
- add one short takeaway line below

Convert a table into a chart only when:

- the slide makes one simple comparison
- the ranking or delta is the main message
- the chart is easier to scan than the table
- the chart can stay visually simple

Do not chartify every evidence slide.

## Text-to-Visual Threshold

A text-heavy slide should not automatically become a visual slide.
Only replace text with a visual if the visual compresses the same message more clearly.

Good conversions:

- prior assumption vs reality into a 2-column contrast box
- pipeline in three steps into a 3-stage strip
- adaptive vs fixed into one compact comparison visual
- different terms fix different failure modes into a compact trade-off view

Bad conversions:

- replacing short bullets with icons that add no information
- turning a clear table into a busy chart
- adding a concept diagram that only repeats the title

For method blocks, good conversions also include:

- hidden execution state into a repeated colored strip
- local scores into a simple heatmap or score trace
- boundary detection into a margin curve with one or two marked change points
- evolving topology into a graph that grows over steps

## Micro-Readability Rules

- when a figure is present, keep support text short and directional
- when a table is present, add at most one takeaway line and one small contrast
- do not place a dense figure and a dense table on the same slide
- do not place more than one independent claim on the same slide
- do not use more than about 3 short bullets on a visual-first slide
- do not shrink fonts to rescue a crowded layout; split instead
- use bold only for one value family, one phrase, or one conclusion

## Low-Risk Layout Changes

Prefer layout changes with high payoff and low regression risk:

- split one overloaded slide into two
- enlarge one visual instead of showing two side by side
- move support detail into a small side box
- add one takeaway line under a table
- use one compact right-side summary box for setup coverage or protocol
- keep generous white space instead of filling all empty space

These usually help more than adding new assets.

## Density by Slide Type

- Visual-first slides: one strong figure or example, minimal text, one clear takeaway
- Method slides: one core diagram or one equation block, only the claims needed to understand the mechanism
- Result slides: one visual or one table, one explicit interpretation, one contrast to remember
- Setup slides: enough detail to support validity, no exhaustive listing unless required

Split crowded slides instead of shrinking text.
Also split long text-only runs when a nearby figure, table, or equation can carry part of the explanation.

## Protect Text-First Slides

Some slides should remain text-first even in a visually improved deck:

- compact contribution slides
- clear limitation slides
- final takeaway slides
- short setup summaries that already read cleanly

Do not force a visual where text is already better.

## Style Stability

When adding any new schematic, chart, or comparison strip:

- keep the same font family
- keep the same line and box style family
- use restrained colors
- avoid mixing illustration styles
- prefer source-native tools such as TikZ, tables, or simple chart code over manual drawing
- prefer grayscale plus one accent color if unsure

## Safe Visual Budget

For a 20 to 25 minute talk, usually add at most:

- 1 concrete before-vs-after visual
- 1 simplified source-built method schematic if needed
- 1 compressed result visual if clearly useful

The talk should still feel like one academic presentation, not a sequence of designed posters.

## Regression Prevention and Fallback

If a new visual makes the slide busier, less legible, harder to explain, more style-inconsistent, or more dependent on narration, revert it.

If visual augmentation is uncertain or fails quality checks, fall back to:

- paper figure reuse
- cropped figure reuse
- reduced table
- plain table plus one takeaway line
- text-only explanation

Do not force augmentation.

## Codex Revision Policy

Prefer small, verifiable changes over broad redesign.

Safe edit priority:

1. shorten a title
2. regroup bullets
3. add one takeaway line
4. crop and enlarge one figure panel
5. reduce a table
6. split one slide
7. add one compact comparison box
8. add one simple source-built boxes-and-arrows schematic

Only after those are exhausted should you consider whether any additional source-built visual is actually necessary.
Do not introduce subjective redraws or style-heavy illustration work.

Still avoid:

- several new visuals in one section
- converting many tables into charts
- style-heavy layout redesign

Do not make several risky visual changes at once.
In one revision pass, change at most one dense overview figure, one evidence-slide family, one before-vs-after example, or one method schematic.

For each nontrivial visual revision, keep an internal log:

- slide number
- change made
- why it should help readability
- fallback if it is weaker after compile

Compile after each local batch of changes and stop early once the slide is clearly readable.
If an original paper figure is already readable and tied to the main point, keep it.

## Final Check

Before finalizing, ask:

1. Which 3 to 5 slides provide the strongest visual payoff?
2. Is there at least one slide the audience can understand in about 5 seconds?
3. Does each main-path slide have one primary object of attention?
4. Is there a concrete operational example when the paper naturally supports one?
5. Are any dense original figures being used without crop, split, or guidance?
6. Did any revision reduce font size or increase clutter?
7. Does the deck still work if all newly added visuals are removed?
8. Are the changed slides clearly easier to read rather than merely more designed?
9. Can each new visual be traced back to explicit structure or data in the paper?
