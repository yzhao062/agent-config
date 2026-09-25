# Find references before choosing a composition

For a new figure or substantial redesign, search for relevant examples after understanding the source and before committing to a layout. The goal is a defensible design choice, not an exhaustive literature review. Reuse a relevant reference already inspected in the current task; a small correction to an accepted layout does not need another search.

## Route by the requested document

| Target | Search first | Inspect | Prefer |
|---|---|---|---|
| ML/AI paper | Related papers in NeurIPS, ICML, and ICLR; use other leading field venues when appropriate | The actual first figure or matching method figure, its caption, and nearby introduction | Similar scientific contribution and figure purpose, with a clear problem, example, mechanism, or result |
| GitHub README | Current GitHub Trending in a relevant category, then related active repositories | The rendered README, actual hero/workflow asset, opening description, and quick start | A recognizable user benefit, honest input/output example, and readable composition at README width |
| Proposal | The author's selected proposal examples, then the local awarded/funded collection and its indexes as needed | Overview or aim figure with surrounding narrative, funding context, and available editable source | A match to the figure's job and the author's preference; agency/program and audience provide additional context |

### Paper references

Search with both topic and figure role, for example `agent evaluation benchmark ICLR overview figure` or `scientific machine learning framework ICML`. Prefer official proceedings and author-hosted originals. Confirm publication venue and year from the source when calling a paper accepted or published; an arXiv upload alone does not establish acceptance.

Read the actual figure rather than inferring its content from the abstract. A first figure may be an example, architecture, or result plot, and those serve different purposes. Inspect its relation to the surrounding text. Record the page and figure number so another agent can find it again.

### README references

Treat "trending" as a dated observation. Check the current listing and record the date and daily/weekly/monthly window when available. Stars or historical popularity alone do not prove a repository is currently trending. Activity and visual quality are separate selection criteria.

Use trending projects as candidates, then inspect related repositories whose users and outputs resemble the target. A popular project with a decorative logo may offer little guidance for an explanatory figure. Prefer the actual rendered README and source asset over a search thumbnail. Record a commit or retrieval date where practical because README layouts change.

### Local awarded proposal references

Start with the author's [selected proposal examples](proposal-style-exemplars.md) and choose by figure job: integrated research overview, ecosystem argument, or compact framework. Search further when those examples do not serve the current figure's role. Use the user-named collection, project README, or existing local index and targeted searches for terms such as `awarded`, `funded`, agency names, and the proposal topic. Prefer indexed final awarded versions over unrelated drafts. Do not assume every proposal in a figure bank was funded.

Use the user's explicit identification, a trusted local award index, or an award record to establish funding status. Otherwise mark the status unverified. If the collection path is unknown after checking the available project indexes, ask for its location while continuing source analysis and any available reference inspection. Do not invent a standard local path or scan unrelated personal folders.

When the author asks to retain reference preferences or lessons in a local skill, record the source locators and concise design descriptions. This does not automatically authorize copying private artwork, PDF pages, or verbatim passages into that skill, a public reference bank, or an external prompt. Use any existing authorization for the actual material and destination; keep broader proposal contents outside a limited figure review.

Inspect the current proposal's figures alongside the awarded examples. The former establish the document's own typography, palette, object shapes, and icon vocabulary; the latter can supply useful composition ideas. Resolve figure numbers through the current manuscript's actual asset inclusions. A similarly named small export or an older PPTX may contain different artwork. When the author asks to reuse their own elements, look for the editable source first and retain exact asset or crop locations. See [proposal-figures.md](proposal-figures.md) for choosing what to reuse.

An existing `figure-references/index.md` can help discover visual references, but its style tags do not establish award status. If no awarded example is accessible, state that limitation and continue with user-supplied or clearly labeled alternative references. Do not claim to have completed an awarded-proposal comparison.

## External Plotting Repositories

Use an external repository as a specific design or plotting reference. Inspect its rendered example, corresponding source script, and applicable skill instructions before deciding what transfers. Record the revision, inspected paths, chosen convention, and whether code or artwork was copied. Reading a repository by path or URL does not require installing its skill; installation changes discovery, not the rendering capability.

### figures4papers Worked Reference

The inspected [figures4papers snapshot](https://github.com/ChenLiu-1996/figures4papers/tree/3c181f85e82c6f24948fcaaf3be6696102b41d8d) supplies scientific plotting examples and a Matplotlib-oriented skill. Use it alongside editable-figure for result panels and plotting conventions. Keep contribution selection, explanatory artwork, editable PowerPoint construction, and native checks in this workflow.

Useful entry points at that revision:

| Inspected Source | Transferable Choice | Adaptation Boundary |
|---|---|---|
| [VIGIL teaser](https://github.com/ChenLiu-1996/figures4papers/blob/3c181f85e82c6f24948fcaaf3be6696102b41d8d/assets/VIGIL_teaser.png) | Combine a concrete explanatory scene with compact quantitative evidence | Rebuild the relationship using the current paper's objects and verified results. |
| [Dispersion motivation](https://github.com/ChenLiu-1996/figures4papers/blob/3c181f85e82c6f24948fcaaf3be6696102b41d8d/assets/Dispersion_motivation.png) | Connect a mechanism to its geometric consequence | Preserve the causal connection rather than copying the layout alone. |
| [ImmunoStruct bars](https://github.com/ChenLiu-1996/figures4papers/blob/3c181f85e82c6f24948fcaaf3be6696102b41d8d/figure_ImmunoStruct/figures/bars_comparison_IEDB.png) and [plot script](https://github.com/ChenLiu-1996/figures4papers/blob/3c181f85e82c6f24948fcaaf3be6696102b41d8d/figure_ImmunoStruct/plot_bars.py) | Aligned small multiples, restrained axes, and consistent emphasis | Replace project-specific inputs and recompute printed type size before reusing the canvas. Do not inherit limits that distort a magnitude comparison. |

Read its [scientific-figure-making skill](https://github.com/ChenLiu-1996/figures4papers/blob/3c181f85e82c6f24948fcaaf3be6696102b41d8d/scientific-figure-making/SKILL.md) for plotting guidance. Its [API reference](https://github.com/ChenLiu-1996/figures4papers/blob/3c181f85e82c6f24948fcaaf3be6696102b41d8d/scientific-figure-making/references/api.md) is an interface specification to implement or adapt, not evidence of an importable plotting package. Inspect dependencies, input paths, and output paths before executing an example script.

For a scientific plot, adapt an appropriate plotting script with real data. For a hybrid PowerPoint figure, recreate selected conventions as native shapes and text if that satisfies the editing requirement. Describe those objects accurately: editable bars and labels do not provide a chart workbook. Preserve the accepted document palette, consistent scales, and explicit units; prefer direct labels when they save legend lookup.

The inspected repository carries a [CC BY-NC 4.0 license](https://github.com/ChenLiu-1996/figures4papers/blob/3c181f85e82c6f24948fcaaf3be6696102b41d8d/LICENSE). Check applicable terms and file-specific notices before copying code or artwork, and retain required attribution when reusing material. These reference notes copy neither its code nor its artwork. Recheck the selected revision when adopting later repository changes.

## Select what transfers

Inspect a small candidate set, often three to five examples, and select one to three useful references. Expand only if none solves the design question. These are effort guides, not quotas. The best structural reference and the best style reference may be different examples.

Compare candidates on the following questions:

- Does the figure serve the same reader decision and document role?
- What makes its usefulness, novelty, or feasibility apparent?
- How does it divide information between graphics, labels, caption, and surrounding prose?
- Which relationships remain clear at the intended display size?
- Can the useful structure be rebuilt as editable PowerPoint objects?

Keep a compact reference record with the working figure brief:

| Source and locator | Role in this task | What to adopt | What does not transfer |
|---|---|---|---|
| URL or local path, figure/page or README section, date/version as relevant | Structure, visual style, or concrete-example treatment | Specific hierarchy, evidence boundary, grouping, or input/output arrangement | Unsupported claims, domain-specific content, excessive density, or incompatible format |

Recommend a composition in one or two sentences that connect the chosen references to the current reader takeaway. Proceed to a draft; reference selection is not a mandatory approval gate. When useful, show the inspected references or link their exact locations alongside the explanation.

Use references to inform an original design. Reuse artwork from the author's own figures when requested or otherwise authorized, preserving its meaning and source. Do not assume permission to reproduce unrelated reference artwork or invent impressive-looking results. Acceptance, funding, and GitHub popularity help identify candidates but do not prove that their figures caused those outcomes.

If web or local access is unavailable, describe which part of the search was not performed, use the material actually available, and continue within the authorized scope. A user instruction to skip research or use a supplied template takes precedence.
