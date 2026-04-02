---
name: nsf-figure-builder
description: Build NSF proposal figures from proposal text, thrust drafts, and prior example figures. Use when Codex needs to decide whether a proposal or thrust needs a figure, turn a figure idea into a concrete figure spec and caption, prepare a prompt pack for third-party image tools, choose an editable vector format, or reconstruct a collaborator-facing figure workflow that reduces manual PPT or Photoshop work.
---

# NSF Figure Builder

## Overview

Use this skill when the user wants help with proposal figures beyond a simple
placeholder.

This skill is optimized for NSF proposal figures, but it can still be reused
for other calls when the surrounding proposal structure and figure purpose are
explicit. In those cases, treat the provided call context as the constraint and
do not force NSF-specific figure assumptions onto the design.

This skill is for figure production workflow, not for proposal framing:

- `nsf-proposal-composer` decides whether the proposal-level story needs an
  overview or ecosystem figure
- `nsf-thrust-refiner` can suggest a local figure concept and leave a visible
  placeholder
- `nsf-figure-builder` turns that need into a reusable figure specification,
  editable-source plan, and collaboration workflow

Use it when the user asks for work such as:

- what figure should support this intro or thrust
- create a figure spec and caption
- generate a model-neutral prompt for Gemini, Claude, ChatGPT image tools, Sora, Nano Banana, or another outside tool
- choose between draw.io, SVG, Graphviz, matplotlib, or TikZ
- reduce hand-drawn PPT or Photoshop work
- rebuild an outside reference image into a locally editable vector figure

Read these references only as needed:

- figure archetypes and example anchors: `references/figure-archetypes.md`
- format and tool choice: `references/tool-selection.md`
- outside-tool prompt packs and import flow: `references/external-handoff.md`
- cross-model prompt design for image generation: `references/prompt-design.md`
- relation to local proposal files: `../nsf-proposal-composer/references/section-blueprints.md`

In a multi-proposal repo, use `<proposal-dir>` to mean one concrete proposal
workspace such as `proposals/nsf-25-533-fairos`.

Use `scripts/init_figure_spec.py` when the user wants a concrete figure spec
file scaffold under `<proposal-dir>/figure-spec/`.

## Workflow

### 1. Read Only The Figure Context You Need

Read the smallest set of files needed to understand the figure's job:

- `<proposal-dir>/00-project-description.tex` for intro and overview figures
- the target thrust or aim file for unit-level figures
- `<proposal-dir>/20-evaluation.tex` for timeline or measurable-outcomes figures
- a small number of prior examples from `examples/proposals/`
- existing figure files under `<proposal-dir>/figure/` only if the user wants a
  refresh rather than a fresh figure

Do not read the whole repo just to draft one figure.

### 2. Decide Whether The Figure Is Worth Making

Add or refresh a figure only when it compresses logic better than prose.

Typical cases:

- intro or overview figure for the end-to-end proposal logic
- thrust or aim figure for a pipeline, mechanism, or layered method
- timeline or work plan figure for evaluation and coordination
- ecosystem or adoption figure for capability-building proposals
- evidence or impact figure when adoption or prior-system footprint matters

If the figure would only restate nearby sentences without clarifying structure,
say so and avoid unnecessary figure bloat.

### 3. Pick A Figure Archetype Before Picking A Tool

Reduce the request to one archetype first:

1. `overview-architecture`
2. `thrust-mechanism`
3. `workflow-or-method-pipeline`
4. `timeline-or-work-plan`
5. `ecosystem-or-adoption`
6. `evidence-or-impact`

Then choose the editable-source format using `references/tool-selection.md`.

### 4. Produce A Figure Spec First

Before proposing final art, produce a figure spec with:

- figure goal
- one-sentence reviewer takeaway
- target section and file
- required boxes, actors, or stages
- required arrows or dependencies
- suggested layout
- short in-figure text
- caption draft
- recommended editable source format
- proposed filenames for `figure/` and `figure-src/`

This spec is the source of truth. Outside-tool drafts are optional aids, not
the final deliverable.

Do not let the figure collapse into a plain box-only wireframe unless the user
explicitly asks for a minimal placeholder. Proposal-facing figures should use a
light visual language such as icon badges, grouped regions, or restrained
illustrative cues when those cues improve readability.

### 5. When Using Outside Image Models, Produce One Prompt The Model Can Actually Use

When the user wants to test an outside image model, do not dump the entire
figure-spec bundle into the model. Produce:

1. a short local source-of-truth note for the repo
2. one model-neutral prompt meant to be copied into the outside tool

That prompt should be self-contained and visually directive, but not overloaded
with internal reasoning, review rubrics, or repo-specific workflow notes.

Use the cross-model guidance in `references/prompt-design.md`. The prompt
should usually contain these layers in this order:

- figure type and core message
- reviewer takeaway
- required layout and semantic elements
- required arrows or dependencies
- visual-quality layer
- output-quality layer

Prefer prompts that tell the rendering model:

- what kind of scientific figure this is
- what the central semantic blocks are
- how directionality should read
- how color should map to functional role
- what aesthetics to avoid

Do not ask the rendering model to optimize for the repo's internal workflow.
That part belongs in the local spec, not in the copied prompt.

### 6. Support Third-Party Tools Without Depending On Them

When the user wants to use Gemini, Sora, Nano Banana, or similar tools:

1. convert the figure spec into a clean prompt pack
2. tell the user exactly what kind of output is acceptable as a reference
3. if the returned asset should stay in the repo, place it under
   `<proposal-dir>/figure-src/reference/`
4. treat those assets as inspiration or layout references
5. rebuild the final figure in an editable vector format

Do not treat a returned raster image as the long-term source of truth unless
the user explicitly accepts that tradeoff.

### 7. Default To Editable Outputs

Prefer workflows that leave the user with editable local source files:

- `drawio` or `svg` for architecture and ecosystem figures
- `graphviz` for graphs, dependency diagrams, and typed relationships
- `matplotlib` for charts or simpler timelines
- `tikz` only when LaTeX-native generation materially helps and the expected
  complexity is manageable

For complex figures, it is acceptable to produce:

- a strong figure spec
- a prompt pack for outside ideation
- an editable skeleton rather than a fully polished final figure

The goal is to remove most manual figure-design labor, not to promise
fully automatic artistic finish.

When drafting editable skeletons:

- avoid crude box farms unless structure is the only goal
- route arrows deliberately; avoid diagonals that create visual confusion
- prefer grouped regions, icon badges, and 1-2 accent shapes over decorative
  clutter
- keep in-figure text short enough that later style polishing remains easy

### 8. Write Outputs Into Stable Locations

Use these repo locations:

- `<proposal-dir>/figure-spec/` for figure specs and prompt packs
- `<proposal-dir>/figure-src/` for editable local sources
- `<proposal-dir>/figure/` for final exported PDFs
- `<proposal-dir>/figure-src/reference/` for external reference images or drafts

When working on the long-lived template instead of an active proposal, use the
same folder names under `template/`.

When the user explicitly wants an outside-model prompt, save a dedicated prompt
file under `<proposal-dir>/figure-spec/` with a stable name such as
`<figure-name>-universal-prompt.md`. Keep the file easy to copy:

- short title
- optional one-line note
- one fenced `text` block containing the actual prompt

## Output Style

When using this skill, prefer one of these outcomes:

- a figure recommendation with rationale and no new file
- a figure spec and caption draft
- a figure spec plus a prompt pack for outside tools
- a prompt-only file meant to be pasted into an external image model
- a figure spec plus editable-source recommendation and filenames
- a refresh plan for rebuilding an outside draft into a local editable figure

Keep the output practical. The main value is reducing manual figure work while
keeping the resulting assets editable and proposal-aligned.
