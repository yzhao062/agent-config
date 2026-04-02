---
name: nsf-proposal-composer
description: Compose NSF proposal outlines and section drafts from a project idea, prior proposal examples, and solicitation requirements. Use when Codex needs to choose between ecosystem-building and methodology-driven proposal families, turn a brief into a proposal structure, draft or refresh LaTeX sections, introduce an optional cross-section running example for abstract infrastructure proposals, or keep summary, aims, evaluation, and impact sections aligned during proposal writing.
---

# NSF Proposal Composer

## Overview

Use this skill to turn an early proposal idea into a concrete NSF writing plan
and section draft sequence. Treat `nsf-proposal-guardrail` as the compliance
layer and this skill as the composition layer.

This skill is optimized for NSF proposal structure. It can still be reused for
other calls when explicit sponsor requirements are present in
`<proposal-dir>/context/solicitation/`, but those requirements should override
default NSF conventions instead of turning the skill into a generic
multi-sponsor composer.

Primary use case:

- the user gives a core proposal concept, or Codex reads the current
  introduction from an active proposal folder as the seed idea
- Codex improves the introduction architecture so it clearly moves from
  importance, to gaps or challenges, to a coherent thrust sequence
- Codex chooses the proposal family and target structure
- Codex generates or refreshes numbered aim files in the active proposal folder
- Codex syncs the introduction back to the generated aims so the narrative
  stays aligned

Treat this as a bidirectional sync skill, not a one-shot drafter:

- intro-framing mode: `importance -> gaps -> thrust chain`
- early framing mode: `intro -> aims`
- later revision mode: `aims -> intro`
- final consistency mode: `intro <-> aims <-> summary <-> evaluation`

Once the proposal scaffold exists and the user wants thrust-level literature,
technical deepening, local evaluation hooks, or figure thinking inside a single
unit, prefer `nsf-thrust-refiner` instead of stretching this skill beyond
structure and cross-section sync.

When the user wants an actual proposal-figure workflow, editable-source plan,
or outside-tool prompt pack, prefer `nsf-figure-builder`.

Do not mimic old proposal wording. Abstract structure, decision patterns,
argument flow, and section slotting from prior examples.

Read these references only as needed:

- Proposal family selection: `references/proposal-families.md`
- Required brief fields: `references/project-brief-schema.md`
- Section design and repo mapping: `references/section-blueprints.md`
- Prior sample selection: `references/example-anchors.md`
- Running example decisions for reviewer comprehension:
  `references/running-examples.md`
- Majority unit progression: `references/major-unit-patterns.md`
- House style for aim files: `references/house-style.md`
- Direct workflow for idea-to-aim generation: `references/idea-to-aim-files.md`
- Intro-first narrative architecture:
  `references/intro-architecture.md`
- Intro-to-aim sync workflow: `references/intro-aim-sync.md`
- Edit boundaries between composer and refiner:
  `references/edit-boundaries.md`

`nsf-proposal-composer` owns the default heading style for proposal sections.
When it creates or refreshes `\section{}`, `\subsection{}`, or
`\subsubsection{}` titles, use Title Case rather than sentence case.

In a multi-proposal repo, treat `proposals/` as a container. Use
`<proposal-dir>` to mean one concrete proposal workspace such as
`proposals/nsf-25-533-fairos`.

## Workflow

### 1. Gather Inputs

Read the smallest set of inputs that will support drafting:

- Solicitation requirements if available:
  `<proposal-dir>/guardrail/solicitation-requirements.json`,
  `<proposal-dir>/guardrail/solicitation-qc.md`,
  `<proposal-dir>/context/solicitation/solicitation.txt`
- Current working proposal entrypoints such as:
  `<proposal-dir>/00-project-summary.tex`,
  `<proposal-dir>/00-project-description.tex`,
  `<proposal-dir>/03-team-qualification.tex`,
  `<proposal-dir>/11-aim1.tex`, `<proposal-dir>/20-evaluation.tex`,
  `<proposal-dir>/30-collaborators.tex`, `<proposal-dir>/34-facility.tex`,
  `<proposal-dir>/21-prior-nsf-support.tex`
- Supporting proposal context such as:
  `<proposal-dir>/context/team/*/profile.md`,
  `<proposal-dir>/context/team/*/cv.pdf`,
  `<proposal-dir>/context/team/*/webpage.txt`,
  `<proposal-dir>/context/notes/*.md`
- The long-lived fallback template under `template/` when no active proposal
  folder exists yet
- Prior examples under `examples/proposals/` when the user wants style or
  structure mined from older proposals
- Any user notes describing the concept, target program, collaborators, and
  desired emphasis

If compliance constraints are unclear, consult `nsf-proposal-guardrail` outputs
before drafting.

When drafting from investigator materials, treat raw HTML, copied Google
Scholar pages, and CV PDFs as source evidence. Normalize them into prose or
cleaned `profile.md` facts before writing final LaTeX. If an investigator
citation key, role detail, institution, or partner-specific fact is still
unresolved, leave a visible LaTeX `\todo{...}` placeholder instead of a hidden
comment so the coauthor team can see and resolve it later.

When an active proposal folder already exists, prefer intro-driven drafting:

- read the introduction and overview paragraphs in
  `00-project-description.tex` as the current seed idea
- treat those paragraphs as the initial source of truth unless the user gives a
  newer brief
- update those same paragraphs after aim drafting so introduction and aims stay
  consistent
- inspect the bridging prose between the introduction and the numbered
  `\input{11-aim1}` ... `\input{14-aim4}` region; if it still reflects an older
  proposal family or topic, rewrite it instead of leaving stale narrative in
  place

When the user has already revised the aim files and asks for alignment, switch
the source of truth:

- treat `11-aim1.tex` through `14-aim4.tex` as the structural source of truth
- refresh the introduction so it matches the current thrust or aim titles,
  sequence, scope, and project claims
- keep the introduction high level; do not copy full aim prose into it

When numbered unit files contain `% composer:sync-*` and `% refiner:body-*`
markers, default to protected mode:

- patch only the `composer:sync` region inside `11-aim1.tex` through
  `14-aim4.tex`
- treat the `refiner:body` region as protected
- do not rewrite a refined body unless the user explicitly asks for a
  regenerate-from-scratch or overwrite pass

### 2. Normalize The Intro Architecture

Before drafting aims, reduce the current introduction or user idea into a
proposal-level narrative architecture.

The minimum normalized output is:

- 1 short importance claim about why the problem matters for science,
  infrastructure, national capability, or open-science practice
- 2-4 explicit gaps or challenges
- 1 central proposal claim about what this project will make possible
- 1 candidate thrust chain showing how the technical units resolve the gaps in
  sequence

When the current introduction is weak, do not treat it as fixed source
material. Repair its architecture first.

For this repository, a strong introduction usually follows:

1. why the problem matters
2. why current practice still falls short
3. what the project will build or study
4. how the thrusts form a coherent progression

Visible `\todo{...}` placeholders are acceptable for supporting citations or
fine-grained wording if the architecture is the main issue being solved in the
current pass.

If a clean gap-to-thrust mapping does not yet exist, stop and present the
candidate mappings instead of pretending the structure is already settled.

When the proposal introduces layered infrastructure objects or abstract
handoffs that reviewers may not parse quickly, consider carrying one running
example across the intro, numbered units, and evaluation. Use
`references/running-examples.md` for selection and placement. Treat this as an
optional narrative aid, not a template default or mandatory section pattern.

### 3. Choose The Proposal Family

Select exactly one family as the dominant narrative:

- `ecosystem-building`
  Use for open ecosystem, platform, community, infrastructure, open science,
  adoption, or capability-building calls.
- `methodology-driven`
  Use for classical method, algorithm, theory, systems-method, or
  hypothesis/aim-driven calls.

Do not create more families unless the user explicitly asks to redesign the
taxonomy. Use overlays instead of new families.

Typical overlays:

- `collaborative`
- `community-or-mentoring-heavy`
- `open-source-or-open-data`
- `deployment-or-adoption-heavy`
- `management-plan-heavy`
- `bpc-required`

### 4. Build A Composer Plan

Turn the user idea into a concrete writing plan before drafting prose. The plan
should include:

- active proposal folder, if one exists
- dominant family
- normalized intro architecture: importance, gaps, central claim
- 1-2 example anchors from `examples/catalog.csv` that best match the family and
  unit pattern
- target count and role progression for the numbered aim files
- target reviewers the narrative must satisfy
- section tree
- estimated page budget by section
- section-to-file mapping for this repo
- unresolved questions that block high-quality drafting
- recommended drafting order

Keep the plan explicit. This skill should not jump directly into long prose when
the narrative frame is still unclear.

### 5. Generate Aim Files First

For most tasks in this repository, the first substantial drafting artifact
should be the core aim or thrust files, not the full proposal description.

Default behavior:

- infer the unit count from the gap map and the logical progression rather than
  forcing a fixed count
- prefer 3 numbered units when one apparent "fourth thrust" is really an
  evaluation, adoption, or validation layer
- use 4 numbered units only when the fourth unit has a genuine research or
  capability role that stands alongside the others
- use `references/major-unit-patterns.md` to infer the first-pass progression
  when the user only gives a high-level concept

When the user wants files created or reset, use
`scripts/configure_aim_files.py` to scaffold the active aim slots and sync the
entrypoint before drafting prose into them.

When the user wants a fresh working copy, use `scripts/instantiate_proposal.py`
to copy `template/` into one proposal workspace such as
`proposals/nsf-25-533-fairos/` before drafting.

If the numbered aim files already exist and the user edits them manually, this
skill should still be used. In that case, treat the task as a refresh pass
rather than a fresh generation pass.

When a refresh pass runs after `nsf-thrust-refiner`, preserve the protected
body regions by default. High-level polish belongs in the sync region and in
cross-section files such as the intro, summary, and evaluation.

### 6. Draft Incrementally

Draft by section, not by monolithic full proposal generation. Prefer this order:

1. normalize the intro architecture: importance, gaps, central claim
2. family-specific unit progression and example-anchor selection
3. aim or thrust titles and file scaffolding
4. core aims, thrusts, or work packages
5. introduction / motivation refresh
6. project summary
7. evaluation and measurable outcomes
8. broader impacts / ecosystem or adoption plan
9. supporting sections

Use these sync directions explicitly:

1. first pass: normalize idea or intro, improve the intro architecture if
   needed, then draft aims
2. after aim edits: reread `11-14`, then refresh intro and bridge text
3. after intro edits that materially change scope: regenerate or revise aims
4. before submission: refresh summary and evaluation against the latest aims

When the active `00-project-description.tex` still contains a stale pre-aim
bridge from an earlier proposal draft, replace that bridge during the same pass
that generates new aim files. Do not leave old family-specific framing text in
place just because the numbered aim files were updated.

When editing this repo, prefer an instantiated working folder under
`<proposal-dir>` if one exists. Otherwise use `template/`.

Default slots:

- `<proposal-dir>/00-project-summary.tex`: concise summary aligned with dominant family
- `<proposal-dir>/00-project-description.tex`: top-level composition and section ordering
- `<proposal-dir>/03-team-qualification.tex`: team fit, collaboration rationale, and investigator qualifications
- `<proposal-dir>/11-aim1.tex` ... `<proposal-dir>/14-aim4.tex`: method aims or ecosystem work packages
- `<proposal-dir>/20-evaluation.tex`: evaluation, milestones, measurable outcomes
- `<proposal-dir>/21-prior-nsf-support.tex`: per-investigator prior-NSF-support summaries
- `<proposal-dir>/31-data-management.tex`, `<proposal-dir>/32-collaboration-plan.tex`,
  `<proposal-dir>/33-bpc.tex`, `<proposal-dir>/34-facility.tex`: supporting modules enabled
  by the solicitation
- `<proposal-dir>/context/solicitation/`: raw solicitation materials for guardrail ingest
- `<proposal-dir>/context/team/`: PI source materials used to draft or refresh team qualification text
- `<proposal-dir>/context/notes/`: active-project notes that may influence framing decisions

For `ecosystem-building`, it is acceptable to reinterpret `aim` files as
`work packages`, `thrusts`, or `capability tracks` if that better fits the call.

For team-qualification work, use this sub-workflow:

1. read `context/team/<person>/profile.md` if present
2. otherwise extract facts from `html`, `txt`, `scholar`, and `cv.pdf` inputs
3. draft or refresh `03-team-qualification.tex`
4. if citations or affiliations are not final, leave visible `\todo{...}`
   markers in the LaTeX
5. ensure role, name, and institution references remain consistent with
   `30-collaborators.tex`, `20-evaluation.tex`, and `34-facility.tex`

### 7. Refresh Cross-Section Consistency

After any substantial draft update, check for these cross-file mismatches:

- summary claims not backed by the project description
- intro first paragraph does not establish importance before diving into method
- gaps or challenges named in the intro do not map cleanly to the active
  thrusts
- thrusts read as parallel fragments rather than a progression
- introduction promises not backed by the aims
- aim changes not propagated back into the introduction
- aims/work packages not reflected in evaluation
- broader impacts disconnected from technical work
- collaborator roles inconsistent with the management narrative
- PI/co-PI names, ordering, roles, or institutions inconsistent across
  `03-team-qualification.tex`, `20-evaluation.tex`, `30-collaborators.tex`,
  and `34-facility.tex`
- ecosystem/adoption promises unsupported by resources or milestones

When the user asks a narrow sync question such as "update intro to match the
current aims," do not redraft the entire proposal. Limit the patch to the intro
seed region, the pre-aim bridge, and any directly affected high-level
enumeration.

When a numbered unit file contains explicit composer/refiner markers, limit
unit-file edits to the `composer:sync` region unless the user explicitly says
to rewrite or overwrite the unit from scratch.

### 6. Ask Only The Questions That Change Aim Structure

If the user gives only a high-level idea, ask at most the minimum needed to
build good aim files:

- target program or solicitation, if it changes the family choice
- whether the proposal is better framed as `ecosystem-building` or
  `methodology-driven` when the answer is not inferable
- whether a dominant 4-unit progression should be compressed to 3 units

Otherwise, infer a reasonable first pass and write the files.

### 7. Escalate Only When Necessary

Ask the user concise follow-up questions only when one of these is missing:

- the dominant proposal family is ambiguous
- the central research or capability claim is unclear
- the expected deliverable is unknown
- a solicitation constraint changes the structure materially

Otherwise, infer a reasonable first-pass structure and draft it.

## Output Style

When using this skill, prefer outputs that are easy to apply:

- a proposal family decision with short justification
- a section outline with page budget
- a section draft plan mapped to concrete `.tex` files
- section prose that is ready to paste or patch

Keep reviewer logic explicit and keep prose reusable.
