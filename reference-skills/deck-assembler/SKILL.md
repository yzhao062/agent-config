---
name: deck-assembler
description: Assemble a coherent USC Beamer talk from the reusable Yue Zhao intro module and one or more existing paper decks in this repo. Use when the user wants a merged deck with light bridge slides, trimmed duplicate wrappers, and one throughline, without regenerating each paper talk from scratch.
---

# Deck Assembler

Read [references/assembly-patterns.md](./references/assembly-patterns.md) first.
Read [references/continuity-checks.md](./references/continuity-checks.md) before finalizing any merged deck.

This skill assembles a combined talk from existing slide assets in this repo. It is for stitching and continuity, not for generating new paper decks from `papers/`, and not for rewriting each paper's technical content from scratch.

When more than one paper talk is merged, default to a long-form combined talk unless the user explicitly asks for a tighter or shorter merged deck.

## Workspace Contract

This skill is repo-specific. Treat these paths as relative to the workspace root:

- `README.md`
- `theme/`
- `templates/`
- `decks/`

Before generating anything, verify that the workspace contains at least:

- `README.md`
- `templates/demo.tex`
- `templates/paper-deck-base.tex`
- `theme/beamerthemeuscmoloch.sty`
- at least one existing `decks/<paper-slug>/<paper-slug>-deck.tex`

Useful optional sources:

- `templates/modules/yzhao-intro-slides.tex`
- `templates/modules/yzhao-intro-facts.md`
- `decks/<paper-slug>/presenter-map.md`

If the contract is not satisfied, stop and ask the user instead of improvising a different layout.

## Default Outputs

Generate these artifacts by default:

- `decks/<talk-slug>/<talk-slug>-deck.tex`
- `decks/<talk-slug>/assembly-map.md`

Create `decks/<talk-slug>/modules/` only when the source decks are standalone documents and you need talk-local frame-block extracts for maintainability.

Compile the merged deck by default if the local LaTeX toolchain works. Output PDFs can remain local artifacts.

## Workflow

1. Verify the workspace contract and identify the inputs:
   - whether the merged deck should include `templates/modules/yzhao-intro-slides.tex`
   - which existing paper decks under `decks/` will be merged
   - the desired `<talk-slug>`, or derive one only if the user does not care
2. Define one master throughline before moving slides:
   - one audience
   - one title or talk topic
   - one sentence for why these parts belong together
   - one role for each inserted paper segment
   - whether the user wants a shortened merged talk or a long-form merged talk
   - if the user does not specify, choose long-form
3. Inspect each source deck only enough to map:
   - title or roadmap wrappers
   - local section structure
   - core technical frames worth preserving
   - local macros, colors, packages, and `\graphicspath` entries required for those frames
4. Follow the assembly patterns in `references/assembly-patterns.md` to choose a light-touch merged structure.
5. Keep each paper's technical content stable. Prefer these low-risk moves before deeper edits:
   - remove duplicate title pages
   - add one quick talk-overview slide after the intro module when multiple talk segments will follow
   - remove duplicate roadmaps or near-duplicate problem framing only if the user wants a tighter merged talk
   - remove standalone `Questions?` endings or references appendices only when the merged deck has its own master ending or merged references appendix
   - add one bridge slide before a paper segment
   - add one synthesis or closing frame only if the combined talk needs it
6. Because source paper decks are usually full standalone documents, never `\input` an entire source deck directly into the merged deck. Extract the needed frame blocks into the merged deck or into talk-local module files under `decks/<talk-slug>/modules/`.
7. Build one master deck under `decks/<talk-slug>/` using `templates/paper-deck-base.tex` or a copied existing deck preamble as the styling base.
8. Lift only the required source-deck dependencies into the master deck:
   - macros needed by imported frames
   - package imports not already covered by the base deck
   - `\graphicspath` entries for the reused figures
   - local bibliography files only if the merged deck still projects citations
9. Create `assembly-map.md` and record:
   - input modules and source decks
   - chosen order
   - omitted wrapper slides
   - bridge-slide intent
   - compatibility imports such as macros, packages, and figure paths
10. Compile from `decks/<talk-slug>/` with `latexmk -pdf <talk-slug>-deck.tex`.
11. Fix integration issues before handoff:
   - missing macros or packages
   - broken figure paths
   - style drift caused by copied local definitions
   - repeated slides or repeated framing that make the talk feel stitched together

## Operating Rules

- This skill assembles from existing decks and modules. If the user only has a paper source under `papers/`, use `$paper-to-beamer` first.
- Preserve the source decks. Do not destructively rewrite or delete the original paper decks just to make the merged deck work.
- Treat `templates/modules/yzhao-intro-slides.tex` as the reusable intro insert when the user wants a personal or lab opening.
- Use one master title page, one master roadmap if needed, and one master closing direction for the merged deck.
- When multiple paper talks are merged, add a quick `Talk Overview` slide after the intro module by default so the audience knows what will happen in the combined talk.
- Multiple-talk assembly defaults to long-form mode. Preserve the main and supporting content of each source talk unless the user explicitly asks for a shorter merged deck.
- Even in long-form mode, trim duplicate title pages first before touching core technical frames.
- Add only enough bridge content to reduce fragmentation. The merged deck should not become a second full narrative layered on top of the papers.
- Make each inserted paper serve a clear role in the combined talk, such as benchmark anchor, systems case study, safety example, or deployment example.
- Keep one narrative voice and one audience assumption across the merged deck, even if the source decks were written separately.
- Prefer light retitling, wrapper removal, and bridge slides over rewriting the technical content of the paper frames.
- When multiple paper decks repeat the same motivation or background, keep the strongest version once and shorten the repeats.
- Keep visual style unified through the master preamble rather than letting each imported segment bring its own chrome.
- Record any source-sensitive decisions in `assembly-map.md`, especially omitted wrappers and any compatibility imports.
- This skill assembles merged decks only. It does not regenerate intro slides, regenerate paper talks from source, or automatically update presenter maps for the source paper decks.
