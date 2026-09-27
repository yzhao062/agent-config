# Prompt Design

Use this file when the user wants a model-neutral prompt that can be pasted
into an outside image model.

## Principle

The copied prompt should control the image model's visual output, not explain
the repo's internal workflow.

Keep internal planning separate from the pasted prompt.

## Format Restriction For External Prompts

Never ask an outside image model to produce code-based output formats such as
TikZ, SVG, Graphviz, or Mermaid. These formats drastically limit the visual
quality and richness the model can deliver. External image models should always
produce raster or rendered visual output. When a code-based editable source is
needed, the agent should write it directly rather than prompting an external
model for it.

## What A Good Cross-Model Prompt Should Do

A strong prompt for a research or technical figure should:

- identify the correct figure archetype from the scientific context
- state the core message and reviewer takeaway
- specify the main semantic regions and required directionality
- describe color as functional-role logic
- constrain the aesthetic family
- state readability and output constraints

## Recommended Prompt Layers

Write prompts in this order:

1. `figure type`
2. `core message`
3. `reviewer takeaway`
4. `layout`
5. `required elements`
6. `required arrows or dependencies`
7. `selected style-reference images and qualities to transfer or avoid`
8. `visual quality requirements`
9. `output quality requirements`

## Preference precedence

For Yue Zhao's paper and proposal figures, the selected gallery images and the concrete qualities to imitate are the primary aesthetic specification. Carry the reference-to-design mapping into the copied prompt, including exclusions such as gallery 15's heavy colors. The defaults below apply only where that mapping leaves a choice open. Keep approved technical detail, formulas, meaningful 3D objects, and real-world imagery; reserve native text regions if a generator cannot render them reliably. Do not replace the selected aesthetic with a generic prestige anchor.

## Visual Requirements To Reuse

These are strong default requirements for polished scientific figures:

- publication-quality scientific figure
- infer the correct figure type from the scientific context
- prioritize semantically central elements only
- avoid unsupported or speculative decorative elements
- make causal or structural directionality explicit
- use consistent visual encoding across the full figure
- assign color by functional role, not arbitrarily
- use a colorblind-friendly palette
- benchmark against high-end scientific schematics and polished research
  figures
- use a white or soft off-white background
- preserve clean professional typography and clear spatial organization
- keep the composition clean enough for optional later editing

## Output Requirements To Reuse

- readable at the intended final display size
- large readable labels
- no tiny dense paragraph text
- minimal decorative clutter
- avoid decorative glossy 3D effects; retain meaningful 3D treatment supported by a selected reference
- no marketing infographic tone
- no dashboard styling
- no startup pitch-deck aesthetics
- use cartoon or robot imagery only when it serves the content and the selected preference mapping

## Text Density Rule

Outside image models are weak at dense typography. Default to:

- short block titles
- at most one short supporting line per major block
- concise labels instead of paragraph text

If the user prioritizes beauty over exact wording, tell the model to preserve
clean label regions that can be refined later if needed.

## Prestige Anchors

If the user wants very polished output, it is acceptable to say:

- benchmark against high-end scientific schematics
- benchmark against polished research overview figures
- benchmark against Nature/Cell-family figure clarity

Translate those anchors into visual properties:

- clarity
- hierarchy
- color discipline
- white background
- crisp modular composition

Do not let the prompt drift into biology-specific conventions unless the figure
itself is biological.
