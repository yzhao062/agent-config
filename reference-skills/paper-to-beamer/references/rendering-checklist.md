# Rendering Checklist

Follow this checklist every time.

All repo paths below are relative to the workspace root, not the skill directory.

## Read First

1. Verify that the workspace contains `README.md`, `templates/demo.tex`, `templates/paper-deck-base.tex`, and `theme/beamerthemeuscmoloch.sty`.
2. Read `README.md`.
3. Read `templates/demo.tex`.
4. Read `references/content-diagnosis.md`.
5. Read `references/engagement-dynamics.md`.
6. Read `references/time-flexible-design.md`.
7. Read `references/visual-payoff.md`.
8. Read `references/presenter-map.md`.
9. Read `references/deck-outline.md`.
10. Open `templates/paper-deck-base.tex`.

## Generation Rules

- Keep the generated deck entry file in `decks/<paper-slug>/` as `decks/<paper-slug>/<paper-slug>-deck.tex`.
- Do not assume a uniform Overleaf layout. Resolve the entry `.tex` from an explicit user path first, then obvious top-level candidates such as `main.tex`, `paper.tex`, `acl_latex.tex`, or similar conference-style filenames. If needed, inspect candidate files for `\documentclass`, title metadata, abstract, and top-level `\input` or `\include` structure. If multiple candidates remain plausible, stop and ask instead of guessing.
- Derive `<paper-slug>` from the nearest ancestor folder under `papers/` that contains the resolved entry file.
- Leave the USC colors, headline, progress bar, and footline behavior alone unless the user asks for style changes.
- Reuse the paper's own figure files by copying only the needed assets into `decks/<paper-slug>/figures/`, and keep the bibliography deck-local. Copy the required `.bib` file into `decks/<paper-slug>/` and point `\bibliography{...}` only to the local copy.
- Do not leave `\includegraphics{../../papers/...}` or `\graphicspath{../../papers/...}` in the final deck when a deck-local figure copy is feasible.
- Favor explicit slide titles over vague labels like "More Results" or "Discussion".
- Favor meaningful titles that state a question, claim, or contrast.
- Keep most titles short enough to scan quickly.
- Keep slide titles in Title Case by default, except for intentionally preserved lowercase technical tokens, symbols, or quoted text.
- Use `\section{...}` to keep section pages meaningful.
- Use `standout` only for the closing question slide or a major transition.
- Do not force absent elements such as theorems, threat models, pipelines, qualitative examples, ablations, failure cases, or deployment implications.
- Remove or merge any slide that does not have a clear role in the paper's argument.
- Make the audience know why a slide exists before they have to parse its details.
- Do not turn routine support slides into rhetorical set pieces.
- Mark slide roles in source comments when useful: `CORE`, `OPTIONAL`, `SKIP FIRST`, `BACKUP`.
- Output `presenter-map.md` next to the main deck.
- Keep source role comments and `presenter-map.md` aligned.
- Prefer a fuller 20-25 minute deck when the paper supports more useful evidence, but keep the core path safely skippable.
- Make the plain version of the deck work first. Any added visual should be a low-risk readability improvement, not a requirement for basic clarity.
- For any slide that needs revision, classify it first as text-first, figure-first, table-first, example-first, or equation-first.
- Prefer the smallest readable change first: tighter title, shorter bullets, one takeaway line, crop, table reduction, slide split, comparison box, then one simple source-built schematic or before-vs-after visual if still needed.
- Do not make more than one risky visual change in the same local revision pass. Compile and compare before continuing.

## Slide Writing Rules

- Prefer 4-6 bullets or one compact equation block per slide.
- Put dense derivations in appendix slides if they break pacing.
- Use the paper's exact notation for important equations and objectives.
- Cite claims or external baselines when the slide depends on them.
- If a detail is unclear in the paper, write `[Paper unclear on X]` rather than guessing.
- State the research gap explicitly.
- State the novelty explicitly; do not leave it implied.
- Distinguish descriptive slides from critique slides.
- Keep visible slide text separate from presenter-facing content. Put skip guidance, delivery hints, ambiguity framing, and critique prompts in `presenter-map.md` or source comments rather than projected bullets.
- Use concrete phrasing when possible. Prefer outcomes the audience can picture over abstract summary language.
- Use contrast deliberately to keep novelty legible.
- Preserve presenter freedom. Do not write slides as if they were a full speaker script.
- Prefer a few strong visual-payoff slides over many crowded mixed-media slides.
- Avoid long runs of bullet-only slides. If the paper supports it, break support material with a figure, compact table, or clean equation block.
- Prefer low-risk layout improvements such as grouped bullets, side boxes, reduced tables, cropped figures, and one takeaway line under a visual before introducing any more ambitious new graphic.
- Keep one primary object of attention per slide.
- Protect compact contribution slides, limitation slides, takeaway slides, and already-clean setup slides from unnecessary visual augmentation.
- Do not leave bracketed editor comments, TODO markers, or presenter-note phrasing in visible slide text.

## Method and Evaluation Rules

- Method slides should explain what is optimized or constructed, why that design addresses the problem, what the key mechanism is, and what approximation or assumption matters.
- Reveal technical material in layers: intuition, challenge, formalization, implementation choice, implication.
- If the paper has a central figure, use it early and orient the explanation around it.
- If the method still feels compressed after the first pass, split the middle further instead of tightening prose. For method-heavy papers, prefer one major operation, assumption block, or transformation per slide instead of combining several decisions into one dense frame.
- Use whatever explanation object best fits the paper: running example, paper-native overview figure, reduced theorem statement, architecture panel, toy trace, or one simple deck-native schematic. Prefer visuals that can be generated or revised from explicit structure or data, such as LaTeX or TikZ schematics, reduced charts from paper tables, or graph or timeline views built from explicit nodes, edges, or stages.
- Evaluation slides should separate setup, headline result, component analysis, and caveat or limitation whenever the paper supports that split.
- If the paper has one truly important table or figure, dedicate a slide to it and interpret it instead of shrinking it into a crowded summary.
- For empirical papers, prefer framing results around research questions rather than listing tables flatly.
- Make result slides answer a question the audience already has.
- Keep setup and metric slides compact unless they materially affect interpretation.
- Reduce tables to the rows and columns needed for the current claim whenever possible.
- Keep tables as tables when exact values or multiple metrics matter more than a chart's scanning speed.
- Prefer one figure, one table, or one equation block per slide unless the comparison itself is the point.
- Try to give each major section at least one visual, table, or equation payoff when the paper supports it.

## Compile and QA

1. Run `latexmk -pdf <paper-slug>-deck.tex` from `decks/<paper-slug>/`.
2. Check missing figures, unresolved citations, BibTeX errors, and compile warnings.
   - If citations are present, verify that BibTeX is reading a deck-local `.bib` file rather than a `../../papers/...` path.
   - If paper figures are reused, verify that the deck reads them from `decks/<paper-slug>/figures/` rather than `../../papers/...`.
3. Check for overcrowded slides and split them rather than reducing font size.
4. Verify that the title slide, section pages, and standout slide still use the local USC styling correctly.
5. Verify that the references appendix compiles if citations are present.
6. Verify that the deck answers these questions:
   - Is the research gap clear?
   - Is the novelty explicit?
   - Is the evidence aligned with the claims?
   - Are the strongest results surfaced rather than buried?
   - Are assumptions and limitations presented honestly?
   - Are numeric claims consistent with the normalized fact table rather than restated differently across slides?
7. Verify that the deck is engaging as well as correct:
   - Is there question-to-answer rhythm rather than flat exposition?
   - Is there one memorable anchor?
   - Do the slide titles help the audience follow the argument by themselves?
   - Does the talk end on real takeaways rather than generic future work?
   - Are only a few slides carrying most of the narrative weight?
   - Is there exactly one main hook and one main anchor phrase?
   - Do any titles read like speaker notes?
8. Verify that the deck is time-flexible:
   - Is there a safe core path that fits within about 70 to 80 percent of the nominal time?
   - Are there at least 2 clear shortening points?
   - Are there at least 2 clear expansion points?
   - Does the ending still work if optional slides are skipped?
   - Is the full deck substantive enough to use most of a 20-25 minute slot without padding?
   - If the paper is method-heavy, did the deck spend enough slide budget on the method block to be understandable without rushing?
9. Verify visual payoff and density:
   - Are there 3 to 5 strong visual-payoff slides in the main path when the paper supports them?
   - Is there at least one slide that is understandable in about 5 seconds?
   - Does each main-path slide have one dominant mode and one primary object of attention?
   - Does the deck still work if newly added visuals are removed?
   - Is each added visual clearly better than the simpler text or paper-figure alternative?
   - Is there one concrete operational example when the paper naturally supports one?
   - Are any tables larger than the claim they support?
   - Are tables being converted to charts only when the chart is clearly easier to scan?
   - Are any slides dense because both text and visuals are doing too much?
   - Are any new visuals higher-risk than necessary for the message they support?
   - If a new visual was added, can it be checked against explicit source structure or data rather than subjective redrawing?
   - Were weak slides revised in low-risk order before adding new visuals?
   - Did any change shrink fonts or increase clutter to preserve layout?
   - Are there more than two consecutive text-heavy slides in the main path?
11. Verify title consistency:
   - Are slide titles consistently in Title Case across the main deck?
   - Are any lowercase words there because they are technically standard, code-like, symbolic, or quoted, rather than accidental sentence case?
12. Verify the presenter map:
   - Does `presenter-map.md` exist?
   - Does each substantive slide have a role, estimated time, and skip target when relevant?
   - Does the map include section timing, shortening points, and expansion points?
13. Verify visible-text hygiene and ending discipline:
   - Does any visible slide text contain presenter-facing phrasing such as skip advice, transition coaching, or note-to-self language?
   - Are there unresolved editor comments such as `TODO`, `FIXME`, or stray bracketed reminders in visible text?
   - Does the ending avoid near-duplicate conclusion families such as both "What the Paper Establishes" and "Takeaways" unless they clearly do different jobs?
14. Verify the deliverables:
   - Does `decks/<paper-slug>/<paper-slug>-deck.tex` exist?
   - Does `decks/<paper-slug>/presenter-map.md` exist?
   - If paper figures are reused, does `decks/<paper-slug>/figures/` exist with the needed assets?
   - If citations are used, does `decks/<paper-slug>/references.bib` or an equivalent deck-local `.bib` file exist?
   - If compilation succeeded, is there a current PDF next to the deck source?
