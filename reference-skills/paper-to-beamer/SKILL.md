---
name: paper-to-beamer
description: Convert an academic paper's LaTeX source, figures, and bibliography into a complete 20-25 minute Beamer presentation using the local USC Moloch template. Use when the user wants a paper turned into a reusable technical deck with core, optional, and backup paths, especially from `.tex`, figure, and `.bib` files in this repo.
---

# Paper To Beamer

Read [references/rendering-checklist.md](./references/rendering-checklist.md) first. Read [references/deck-outline.md](./references/deck-outline.md) before writing slides.
Read [references/content-diagnosis.md](./references/content-diagnosis.md) before planning the deck.
Read [references/engagement-dynamics.md](./references/engagement-dynamics.md) before planning the deck narrative.
Read [references/time-flexible-design.md](./references/time-flexible-design.md) before planning the final deck structure.
Read [references/visual-payoff.md](./references/visual-payoff.md) before choosing figures, tables, slide density, and any visual augmentation.
Read [references/presenter-map.md](./references/presenter-map.md) before finalizing delivery controls.

Use `templates/paper-deck-base.tex` from the repo as the starting point for every generated deck.

## Workspace Contract

This skill is repo-specific. Treat these paths as relative to the workspace root, not the skill directory:

- `README.md`
- `theme/`
- `templates/`
- `papers/`
- `decks/`

Before generating anything, verify that the workspace contains at least:

- `README.md`
- `templates/demo.tex`
- `templates/paper-deck-base.tex`
- `theme/beamerthemeuscmoloch.sty`

If this contract is not satisfied, stop and ask the user instead of improvising a different layout.

Do not assume every paper bundle uses the same Overleaf layout. Resolve the paper entry file in this order:

- if the user gives an explicit entry `.tex` path, use it
- if the user gives `papers/<paper-slug>/`, inspect that folder first
- prefer obvious entry candidates such as `main.tex`, `paper.tex`, `acl_latex.tex`, `submission.tex`, or similarly top-level conference-style filenames
- if needed, scan candidate `.tex` files for `\documentclass`, title metadata, abstract, and top-level `\input` or `\include` structure
- if multiple plausible entry files remain, stop and ask instead of guessing silently

Derive `<paper-slug>` from the nearest ancestor folder under `papers/` that contains the resolved entry file.

## Reference Roles

Use the references as distinct layers rather than overlapping rule sets:

- `rendering-checklist.md`: execution order, repo-specific file checks, and final QA
- `content-diagnosis.md`: what the paper actually contains and what should be omitted
- `deck-outline.md`: default slide budget and talk shape
- `engagement-dynamics.md`: where stronger narrative pressure is worth using
- `time-flexible-design.md`: core path, optional depth, shortening, and backup structure
- `visual-payoff.md`: slide-level dominant mode, conservative figure or table choice, safe slide surgery order, optional visual augmentation, and slide density
- `presenter-map.md`: presenter-facing control artifact and skip logic

## Workflow

1. Verify the workspace contract, resolve the paper entry `.tex` file, derive `<paper-slug>`, and inspect the entry file, included files, figure paths, and bibliography files.
2. Diagnose the paper before outlining: primary paper type, optional secondary type, strongest contribution type, strongest evidence, key caveat, best figure or table, and what should be omitted because the paper does not contain it.
3. Build a normalized fact table before writing slide prose: task or setting, datasets, baselines, metrics, method components, equations or objectives, implementation choices, key tables and figures, headline results, ablations, limitations or caveats, ambiguities, and citation or evidence source for every number likely to appear on slides.
4. Choose a presentation mode before outlining. Default to `reading_group` unless the user clearly wants `author_talk` or `paper_review`. If the user clearly signals that this is their own paper, draft, or review-stage submission, default to `author_talk` unless they ask for a review stance. Keep that voice consistent across visible text and presenter notes.
5. Extract only the elements that are actually central: problem setting, explicit contributions, objective or algorithm, theorem or proof sketch if present, architecture or pipeline if present, implementation choices if material, headline quantitative results, ablations, qualitative examples, limitations, and implications.
6. Build a slide plan that adapts the default 20-25 minute outline from [references/deck-outline.md](./references/deck-outline.md) to the paper's actual type and content, structure it as a guided argument rather than a compressed paper, and separate core path, optional expansion, skip-first support, and backup material. If the paper is method-heavy and the method itself carries the core novelty, explicitly reserve a larger method block instead of compressing the explanation into 3-4 slides.
7. For method-heavy papers, write a short internal method-comprehension plan before drafting the method slides: broad-audience assumption, one running example if available, one persistent visual anchor, per-slide abstraction ladder, equations that need companion visuals, and which method slides can stay optional.
8. Create a deck directory as `decks/<paper-slug>/`.
9. Create the deck entry file as `decks/<paper-slug>/<paper-slug>-deck.tex`.
10. If the paper uses citations, copy the required `.bib` database into `decks/<paper-slug>/` as a deck-local bibliography, preferably `references.bib`. If multiple `.bib` files are required, copy each one into the deck directory and point the deck only to those local copies.
11. If the deck reuses paper figures, copy every referenced figure asset into `decks/<paper-slug>/figures/`, preferably only the assets actually used by the deck. Point `\includegraphics` or `\graphicspath` only to those deck-local figure copies, not to `../../papers/...`.
12. Copy `templates/paper-deck-base.tex` into the new deck file, then replace the metadata placeholders and write the slide bodies. Point `\paperbibpath` to the deck-local bibliography name such as `references`, not to `../../papers/...`.
13. Choose 3-5 visual anchors for the main path when the paper supports them, but make the baseline deck clear before adding any new visual. Before revising any weak slide, classify it as text-first, figure-first, table-first, example-first, or equation-first. For each candidate figure or table, decide whether to reuse, crop, reduce, extract one explicit structure into a source-built visual, or omit, and prefer the smallest readable change first.
14. Apply slide surgery in low-risk order: tighten the title, shorten or regroup bullets, add one takeaway line, crop or enlarge one paper figure panel, reduce one table to the needed rows and columns, split one crowded slide, add one compact comparison box, then add one simple source-built schematic or before-vs-after visual only if still needed.
15. Create `decks/<paper-slug>/presenter-map.md` with slide roles, timings, shortening points, expansion points, and skip jumps. Keep it consistent with any `CORE`, `OPTIONAL`, `SKIP FIRST`, and `BACKUP` source comments.
16. Compile from `decks/<paper-slug>/` with `latexmk -pdf <paper-slug>-deck.tex`. After any nontrivial batch of visual changes, compile again before making more.
17. Fix compile errors, missing figure paths, bibliography issues, slide overflow, visual-density problems, and presenter-map inconsistencies before handing off.

## Operating Rules

- Treat `theme/` as stable infrastructure. Do not edit `theme/*.sty`, USC color definitions, or the deck chrome unless the user explicitly asks.
- Keep generated decks self-contained enough to move to Overleaf. Do not leave `\bibliography{../../papers/...}`, `\includegraphics{../../papers/...}`, `\graphicspath{../../papers/...}`, or other paper-relative asset paths in the final deck when deck-local copies are feasible.
- Keep the audience fixed at a broad CS academic level: technical, concise, and readable across subfields.
- Default the presentation mode to `reading_group`. Switch to `paper_review` when the user clearly wants a review stance. Switch to `author_talk` when the deck is for the user's own paper, current draft, review submission, or other clearly first-party work unless the user explicitly wants a review-style deck instead.
- Default to a fuller 20-25 minute deck rather than the tightest possible 20-minute version when the paper supports additional useful evidence.
- Target about 17-21 main slides for a 20-25 minute talk, but design the required core path for about 15-18 minutes rather than treating every slide as mandatory.
- For method-heavy, theory-heavy, systems-heavy, or multi-stage papers, allow a fuller main path when clarity requires it. In those cases, prefer roughly 19-23 numbered slides and accept that the compiled PDF may reach about 25-30 physical pages once title pages, section pages, references, and backup are included.
- For method-heavy papers, do not default to a 3-4 slide method section. When the method is the paper's load-bearing contribution, reserve about 6-8 slides in the full main path for method explanation, usually around 30 to 40 percent of the non-opening, non-ending slide budget.
- Treat the audience as broad-CS by default, not domain-expert by default. Method slides should remain legible to listeners who are technical but not already inside the paper's subfield.
- Add 2-5 appendix or backup slides only when needed for references, extra ablations, or anticipated technical questions.
- Protect the baseline strengths of the deck: clear problem framing, explicit contributions, coherent method story, interpretable evidence, honest caveats, and clean takeaways. Do not trade these for more visual complexity.
- Keep most slides to 4-6 bullets maximum. Split a crowded slide instead of shrinking text.
- Do not mechanically fill a fixed slide skeleton. Merge or remove slides that do not have a clear academic communication role.
- Prefer question-to-answer rhythm over flat exposition. Let one slide raise a concrete question and the next slide resolve it.
- Calibrate engagement by slide function. Use stronger hooks only on high-salience slides and keep routine support slides quieter.
- Default to one primary object of attention per slide. If a slide does not clearly need a figure, table, example, or equation, keep it text-first.
- Do not let the main path become bullet-dominated. Aim for a small number of strong visual anchors that carry the method, result, or failure mode.
- Do not let the main path turn into a long text-only run. When the paper provides usable figures, tables, or equations, break support material with visual-first or equation-first slides.
- Treat new visuals as optional improvements, not requirements. The deck must remain clear with strong titles, clean structure, selective paper figures or tables, and concise interpretation even if no new visual is added.
- If a new visual cannot be regenerated from explicit structure or data in the paper, do not add it.
- Prefer omission over weak augmentation. If a visual addition is not clearly better than the plain version, keep the simpler version.
- Every slide should answer one of these questions: what is the problem, why it matters, what is new, how it works, what evidence supports it, or what caveats remain.
- Every visible number in the deck should come from the normalized fact table rather than being regenerated independently on multiple slides.
- Never fabricate missing categories such as theorems, threat models, pipelines, qualitative examples, ablations, deployment implications, or failure cases.
- Reallocate slide budget to the paper's real strengths. If an element is absent, omit it and spend the time elsewhere.
- Preserve mathematical rigor when the paper depends on it. Use the paper's notation and equations rather than inventing a simplified surrogate.
- Never fabricate missing results or implementation details. Mark genuine ambiguities explicitly in the slide text.
- Prefer one strong visual or equation block per technical slide. Do not cram multiple dense figures onto one frame unless the comparison is essential.
- Keep visual changes low-risk and easy to verify in source and compiled PDF. Prefer crop, enlarge, reduce, or a simple comparison box before introducing any new source-built explanatory visual.
- Keep tables as tables unless a chart is clearly easier to scan. Prefer reduced tables, cropped figures, and one-line takeaways over introducing new visuals by default.
- Keep compact contributions, limitations, and takeaway slides text-first unless the paper genuinely needs a visual there.
- Use informative slide titles that carry the argument, but keep them glanceable. Prefer short claim or question titles over long explanatory sentences.
- Default slide titles to Title Case for visual consistency across decks. Preserve standard lowercase only where the token itself is conventionally lowercase, code-like, or part of quoted text.
- Use at most one main hook and one main anchor phrase for the deck unless the paper clearly has multiple stages with different stakes.
- Spend the most attention on the core research question, the key mechanism, the strongest result, and the main caveat. Do not explain every detail at equal depth.
- For method papers, the key mechanism may require multiple layers: overview, intuition, formalization, core mechanism, second mechanism or recovery stage, and implementation or assumption slide. Prefer splitting these layers across separate readable slides over collapsing them into one dense summary.
- For method-heavy papers, prefer a consistent method block grammar: one running example if available, one recurring color or object mapping, and at most one newly introduced abstract object per slide.
- Equations should rarely stand alone in the method block. If an equation is in the main path, pair it with one short intuitive label, one plain-language takeaway, or one companion visual that explains what changes from the previous slide.
- Preserve presenter flexibility. The slides should support live explanation, not script every transition in full text.
- Keep visible slide text and presenter-facing content separate. Put skip logic, delivery hints, ambiguity framing, and critique prompts in `presenter-map.md` or source comments, not in projected slide text.
- Make at most one risky visual change per revision pass. Compile, compare, and stop early once the slide is clearly readable.
- Generate a short presenter-facing control artifact with timings and skip paths. Do not rely only on source comments for delivery control.

## Content Expectations

- Always include an explicit contributions slide framed in research terms such as new problem formulation, method, theory, system, benchmark, empirical finding, or analysis.
- For empirical or evaluation-heavy papers, prefer organizing evidence around 2-4 research questions instead of a flat sequence of tables.
- Make the opening explain the paper's problem, why it matters, and the academic novelty.
- Make the middle explain the method, objective, theorem, system, or benchmark construction that actually carries the contribution.
- If the paper is a method paper, make the method block feel complete on its own: the audience should understand the setting and the load-bearing mechanism, theorem path, or system loop without needing to infer missing steps from spoken narration.
- For method-heavy papers, optimize for continuity inside the method block: each slide should answer the obvious next question raised by the previous slide, rather than introducing a fresh abstraction without a bridge.
- When the method is hard to parse, spend more slide budget on the middle instead of compressing it. Choose a decomposition that matches the paper rather than forcing one fixed stage path. Useful patterns include contrast with the standard view, running example, paper-native overview figure, one major operation per slide, theorem or proof intuition, architecture or control stages, reconstruction step, or output implication. Use only the stages the paper actually contains.
- When paper figures are too dense or the method still feels opaque, it is acceptable to add one or two minimal deck-native schematics when they are clearly easier to read than the raw paper asset. Prefer deterministic, source-built visuals such as LaTeX or TikZ diagrams, simple charts derived from paper tables, or graph or timeline views generated from explicit structure. Avoid subjective redraws or illustration-style replacements.
- Make the evidence section separate setup, headline result, and component analysis when the paper supports that split.
- Prefer fuller evidence coverage when the paper supports it, as long as optional and skip-first slides are clearly marked and the core path still ends cleanly.
- Make the final section critical, not ritual: limitations, assumptions, missing realism, compute cost, narrow coverage, or other caveats actually supported by the paper.
- Use one memorable anchor when the paper supports it: a central figure, one high-payoff table, a before-vs-after example, or a contrast phrase that the audience can remember.
- Prefer one concrete before-vs-after example for attacks, failures, retrieval behavior, or system manipulation when the paper naturally supports it.
- Keep the visual budget conservative. For a 20-25 minute talk, usually no more than one new before-vs-after visual, one simplified source-built method schematic, and one compressed result visual should be added beyond direct paper assets.
- Try to give each major section at least one non-bullet anchor such as a figure, a compact table, or a clean equation block when the paper supports it.
- Surface genuinely interesting or surprising results early when the paper supports them.
- End with 2-3 takeaways tied to the real contribution. Add discussion questions only if they arise naturally from the work.
- Avoid redundant ending families by default. Do not include both a near-duplicate "What the Paper Establishes" slide and a separate "Takeaways" slide unless they clearly do different jobs.
- Include a references appendix when a usable `.bib` file exists. Use BibTeX rather than hand-writing long references.
- Prefer a deck-local bibliography file such as `decks/<paper-slug>/references.bib` even when the paper source lives under `papers/`. This avoids BibTeX path issues across local builds and Overleaf.
- Mark slide roles in the source with lightweight comments such as `[CORE]`, `[OPTIONAL]`, `[SKIP FIRST]`, or `[BACKUP]` when that helps preparation, but do not make those labels visually dominant in the slides unless the user asks.
- Output a `presenter-map.md` artifact next to the deck by default.

## Repo-Specific Notes

- Read `README.md` to understand the current local-theme workflow.
- The generated main deck should live in `decks/<paper-slug>/`.
- The stable theme files and shared USC assets live in `theme/`.
- The reusable demo and paper templates live in `templates/`.
- The expected output set is `decks/<paper-slug>/<paper-slug>-deck.tex`, `decks/<paper-slug>/presenter-map.md`, `decks/<paper-slug>/figures/` when paper figures are reused, a deck-local bibliography file when citations are used, and a compiled PDF when the local LaTeX toolchain works.
- Output PDFs can stay local artifacts; source files matter more than generated PDFs.
