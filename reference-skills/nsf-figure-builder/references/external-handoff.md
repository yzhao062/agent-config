# External Handoff

Use this file when the user wants to involve an outside tool such as Gemini,
Claude, ChatGPT image tools, Sora, or Nano Banana to reduce manual drawing
work.

## Goal

Use outside tools for ideation and visual exploration, not as the final
editable source of truth.

## Cross-Model Prompt Strategy

When the user wants a prompt for an outside image model, the default deliverable
should be a single model-neutral prompt that can be pasted directly into the
tool. Keep it clean enough that the model can follow it without seeing the
entire local figure workflow.

Structure that prompt in this order:

1. figure type and scientific context
2. core message
3. reviewer takeaway
4. required layout
5. required semantic elements
6. required arrows or dependencies
7. visual-quality requirements
8. output-quality requirements

Do not include repo-only instructions such as:

- local folder names
- editable-source plans
- review rubrics
- file naming conventions
- notes to future collaborators

## Visual-Quality Layer

When the user wants the figure to look polished, the prompt should say some
version of the following:

- infer the correct figure type from the scientific context
- prioritize semantically central elements only
- make causal or structural directionality explicit
- use consistent visual encoding across the full figure
- assign color by functional role, not arbitrarily
- use a colorblind-friendly palette
- benchmark against high-end scientific schematics and polished grant figures
- keep a white or soft off-white background
- keep the figure legible when scaled down in a proposal PDF
- keep the layout modular and vector-friendly for later Illustrator cleanup

It is acceptable to use a soft prestige anchor such as
`Nature/Cell-family scientific schematics` if the user clearly wants that level
of polish, but translate that into general figure qualities rather than domain-
specific biological styling.

## Minimal Universal Prompt Template

```text
Create a publication-quality scientific figure for a research proposal.

Core message:
[one paragraph]

Reviewer takeaway:
[one short paragraph]

Figure archetype:
[overview architecture / thrust mechanism / workflow pipeline / timeline]

Required layout:
[left-to-right / layered / hub-and-spoke / stacked]

Required elements:
- ...
- ...

Required arrows or dependencies:
- ...

Visual quality requirements:
- infer the correct scientific figure type from the context
- prioritize only semantically central elements
- make causal directionality explicit
- use consistent visual encoding across the figure
- assign color by functional role with a colorblind-friendly palette
- benchmark against high-end scientific schematics and polished grant figures
- use a white or soft off-white background
- keep the figure modular and suitable for later vector cleanup

Output quality requirements:
- large readable labels
- minimal decorative clutter
- avoid photorealism
- avoid dense tiny text
- keep the image clear when placed in a proposal PDF
```

## Import Back Into This Repo

When the user gets a returned image or draft:

1. if it should stay in the repo, place it under
   `<proposal-dir>/figure-src/reference/`
2. compare it with the original figure spec
3. preserve only the layout or grouping ideas that actually help
4. rebuild the final figure in `<proposal-dir>/figure-src/`
5. export the final PDF into `<proposal-dir>/figure/`

## Acceptable Uses Of Outside Outputs

- layout inspiration
- icon placement inspiration
- grouping and flow inspiration
- general color and spacing inspiration

## Not Acceptable As Default Final Source

- raster image with tiny fixed text
- image that cannot be updated when the proposal changes
- image whose structure does not match the active intro or thrust text
- image that looks like a generic dashboard, startup infographic, or marketing
  poster rather than a scientific proposal figure
