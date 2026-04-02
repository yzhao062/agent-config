---
name: nsf-thrust-refiner
description: Refine one or more NSF thrust, aim, or study files after the initial scaffold exists. Use when Codex needs to deepen a core proposal unit with sharper gaps, local literature grounding, concrete technical measures, evaluation hooks, reviewer-facing running examples or artifact sketches, figure ideas, or visible TODO placeholders while preserving alignment with the current intro, summary, and evaluation plan.
---

# NSF Thrust Refiner

## Overview

Use this skill after `nsf-proposal-composer` has already created the proposal
frame.

This skill is optimized for NSF-style proposal units, but it can still refine
non-NSF proposal sections when the surrounding call requirements have already
been made explicit. In those cases, preserve the given call's structure and
constraints rather than re-imposing generic NSF defaults.

This skill is for unit-level refinement, not for first-pass structure:

- `composer` decides the family, scaffold, and cross-section frame
- `thrust-refiner` deepens 1-2 concrete thrusts or aims at a time

Use it when the user asks for work such as:

- refine the current thrust or aim
- brainstorm stronger technical ideas inside a unit
- add a small amount of local literature grounding while refining the unit
- make a vague method more concrete
- add local evaluation hooks
- think through a figure for a thrust
- leave visible TODOs for unresolved citations or collaborator facts

If the request goes beyond a local figure concept and needs an actual figure
spec, editable-source plan, or outside-tool handoff, switch to
`nsf-figure-builder`.

If the request is primarily a citation pass, asks for explicit citation
density, requires careful external verification, or needs new entries added to
`<proposal-dir>/bibs/working.bib`, hand off that part to `nsf-bibref-filler`
instead of recreating its workflow inside `thrust-refiner`.

Read these references only as needed:

- refinement modes: `references/refinement-modes.md`
- local literature grounding: `references/local-literature-grounding.md`
- figure planning patterns: `references/figure-patterns.md`
- technical depth patterns: `references/technical-depth-patterns.md`
- unit quality checklist: `references/unit-quality-checklist.md`
- house style and example anchors from composer when needed:
  `../nsf-proposal-composer/references/house-style.md`,
  `../nsf-proposal-composer/references/example-anchors.md`,
  `../nsf-proposal-composer/references/running-examples.md`

When literature grounding touches overview, motivation, or background
paragraphs, do not let the team's own papers become the primary support for
broad field or infrastructure claims. Use external anchors first and use the
team's own work mainly for direct technical inheritance or prior capability.

When `thrust-refiner` adds or rewrites local sectioning commands such as
`\subsection{}` or `\subsubsection{}`, inherit the heading style owned by
`nsf-proposal-composer`: use Title Case and do not leave content words in
sentence case.

In a multi-proposal repo, use `<proposal-dir>` to mean one concrete proposal
workspace such as `proposals/nsf-25-533-fairos`.

If solicitation constraints materially affect the unit, consult
`<proposal-dir>/guardrail/solicitation-qc.md` before patching prose.

When a numbered unit file contains `% composer:sync-*` and
`% refiner:body-*` markers, treat the `refiner:body` region as the primary
editing target. Only patch the sync region when the refined body makes the
top-level framing stale.

## Workflow

### 1. Gather Only The Inputs Needed For The Target Unit

Read the smallest set of files that support the refinement request:

- `<proposal-dir>/11-aim1.tex` through `<proposal-dir>/14-aim4.tex`
- `<proposal-dir>/00-project-description.tex` for intro framing and the pre-unit bridge
- `<proposal-dir>/20-evaluation.tex` if the refinement changes measurable outcomes
- `<proposal-dir>/00-project-summary.tex` only if the user wants summary sync
- `<proposal-dir>/guardrail/solicitation-qc.md` when the request touches
  solicitation-facing criteria such as measurable outcomes, cyberinfrastructure,
  adoption, or open-science impact
- relevant `.bib` files and a small number of prior example units

Do not reload the whole proposal unless the user explicitly asks for a global
rewrite.

### 2. Choose One Or More Refinement Modes

Use one or more of these modes, but keep the patch focused:

1. `gap-tightening`
2. `literature-grounding`
3. `technical-deepening`
4. `local-evaluation`
5. `figure-planning`
6. `sync-followthrough`

See `references/refinement-modes.md` for what each mode should produce.

### 3. Ground Literature Locally First

Before inventing new citations, prefer local evidence sources:

- `<proposal-dir>/bibs/*.bib`
- `template/bibs/*.bib`
- example proposal `.bib` files under `examples/proposals/`
- citations already used in neighboring units

Use `scripts/search_local_bib.py` when the user asks for related work or when a
unit clearly needs stronger grounding.

This step is for lightweight unit-level grounding only. `thrust-refiner` may
add or tighten a few citations that are directly adjacent to the prose it is
rewriting, but it should not become a full citation-management pass.

Escalate to `nsf-bibref-filler` when any of these are true:

- the user specifies sparse, moderate, or heavy citation density
- the section needs a broad citation sweep rather than 1-3 local fixes
- external literature needs to be verified and added to `working.bib`
- the main task is checking citation accuracy rather than deepening the method

Rules:

- prefer cite keys already available in the active proposal bibliography
- use prior example proposals to learn what literature categories typically
  support this kind of unit
- if a broad framing claim is currently supported mostly by the team's own
  papers, treat that as incomplete grounding and look for better external
  anchors instead
- if the relevant paper title is known but the exact cite key is uncertain,
  leave a visible `\todo{Add citation for "..."}`
- do not silently insert fabricated cite keys
- do not duplicate `nsf-bibref-filler`'s density-control or external-entry
  workflow inside this skill

### 4. Deepen The Unit Without Changing The Whole Proposal

When refining a thrust or aim, keep the persuasive burden local:

- sharpen the problem and gap
- make the technical object explicit:
  data structure, representation, signal, algorithmic move, workflow, or
  system component
- clarify what is learned, built, measured, or released
- add local dependencies on earlier or later thrusts when helpful
- preserve the unit title and role unless the user asks to rethink it

If reviewer comprehension risk is high because the unit relies on abstract
infrastructure objects or layered handoffs, consider tightening one shared
running example instead of adding more definitions. Reuse the same example
across nearby units when possible, and use a compact callout or pseudo-artifact
sketch only when it improves scanability. Treat this as optional; do not force
every refined unit to contain a box.

If the body change implies a narrower or sharper high-level claim, make the
smallest corresponding sync-region change needed for coherence instead of
rewriting the whole unit.

Do not stop at prose expansion when the method is still under-specified. Use
`references/technical-depth-patterns.md` to add the kind of lightweight
formalism that matches the proposal family and the user's prior house style.

Do not turn one unit into a new proposal direction without checking whether it
breaks the intro, summary, or neighboring units.

### 5. Add Figure Thinking Only When It Compresses Logic

Use figures when they clarify mechanism, workflow, or evaluation logic better
than prose alone.

If the target unit has no figure and the mechanism is pipeline-heavy,
dependency-heavy, or infrastructure-heavy, the default behavior should be:

1. propose one concrete figure concept
2. add a placeholder in the unit
3. leave a visible `\todo{...}` for the final asset

Typical outputs:

- refine an existing figure caption
- add a figure placeholder with a filename and caption skeleton
- add a visible `\todo{Draft figure showing ...}`
- describe one concrete figure concept in prose before drawing anything

See `references/figure-patterns.md`.

### 6. Leave Visible TODOs For Human Follow-Up

This skill must make unresolved issues easy for human coauthors to see.

Use visible LaTeX TODOs for:

- uncertain cite keys
- collaborator-provided facts not yet confirmed
- external validator names not yet final
- figure assets not yet drawn
- open choices that need PI review

Prefer `\todo{...}` over hidden `% comments` for anything the coauthor team
still needs to notice.

### 7. Sync Only The Nearby Files That Actually Changed

By default, patch the target unit file only.

Patch nearby files only when the refinement clearly changes them:

- `00-project-description.tex` if the unit title, local promise, or bridge is now stale
- `20-evaluation.tex` if the unit's measurable outcomes materially changed
- `00-project-summary.tex` only when the user asks for summary sync

If the change is local, keep it local.

## Output Style

When using this skill, prefer one of these outcomes:

- a refined unit file patch
- a short refinement plan followed by the patch
- a literature-grounding patch plus visible TODOs for uncertain cites
- a figure concept with caption placeholder and integration point

Keep prose aligned with the repository's existing house style. Reuse the
function of prior examples, not their wording.
