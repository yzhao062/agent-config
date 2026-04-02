# Citation Rules

Use this reference only when you need section-specific placement guidance or a
clear density rule.

## Density Modes

- `sparse`: cite only the highest-value non-obvious claims, the team's most
  relevant prior outputs, and 1-2 essential external anchors per local topic.
- `moderate`: support each major paragraph or technical move with one exact
  citation cluster when strong evidence exists.
- `heavy`: use only for related-work-heavy sections or when the user explicitly
  asks for dense grounding. Even here, do not add approximate or weakly
  related citations.

If the user does not specify a mode, default to `sparse`.

## Source Priority

Use evidence in this order:

1. cite keys already present in `<proposal-dir>/bibs/*.bib`
2. cite keys already used in neighboring active proposal sections
3. exact matches already present in `template/bibs/*.bib`
4. exact matches from example proposal `.bib` files
5. externally verified entries added to the active `.bib` only after exact
   metadata confirmation

For the team's own work, the default expectation is that the needed entries
already exist locally. If they do not, do not improvise.

This priority order is for exact entry reuse, not for deciding whether a
self-citation is the right rhetorical support. For broad framing claims,
external literature usually outranks the team's own papers.

## Storage Rules

- Keep existing human-maintained bibliography files as they are.
- Put new machine-added entries into `<proposal-dir>/bibs/working.bib`.
- If you are editing the scaffold instead of the active proposal, use
  `template/bibs/working.bib`.
- Do not duplicate an entry into `working.bib` if the exact cite key already
  exists in a human-maintained local bib file.
- If a machine-added entry needs later human cleanup, leave it in
  `working.bib` until a human explicitly consolidates it.

## Placement By Section

### Project Summary

- Keep citations minimal unless the user explicitly asks for more.
- Cite only when a sentence makes a non-obvious technical, infrastructure, or
  community claim that will look unsupported without a source.
- Avoid turning the summary into a literature review.

### Intro Or Problem Framing

- Cite the problem landscape, prior infrastructure, scientific-data setting, or
  gap-defining prior work.
- Prefer a small number of representative citations over long laundry lists.
- Cite foundational benchmarks, standards, or community platforms only when
  they materially help frame the gap.
- Default to external surveys, principles, standards, or community
  infrastructure papers as the main anchors.
- Do not make the team's own papers the primary support for broad field,
  community, or infrastructure claims.
- Use the team's own papers here only when the sentence explicitly references a
  prior system, dataset, or method that this proposal directly builds on.

### Team Qualification

- Cite the team's own papers, systems, software, or datasets when the prose
  claims prior capability or concrete track record.
- Do not over-cite biography-like facts unless the section uses publication
  evidence to prove fit.
- If a specific prior output is mentioned by name, use the exact local entry or
  leave a visible TODO.

### Thrust Or Aim Files

- Cite directly adjacent technical methods, data models, workflows, or prior
  community systems.
- Use citations to sharpen the gap, not to inflate the paragraph.
- When the section names a technical component that builds on the team's own
  work, prefer those local citations first.
- In motivation, background, or overview paragraphs inside a thrust, start with
  external anchors for the field-wide problem and then add self-citations only
  when they document a concrete technical foundation carried into the thrust.

### Evaluation, Translation, Or Infrastructure Sections

- Cite benchmarks, standards, reproducibility practices, shared platforms, or
  community workflows only when they are directly relevant to the promised
  measures or artifacts.
- Avoid vague "best practice" citations that do not materially support the
  metric or release plan.

## External Verification Rules

When an exact local entry is missing and the user allows external additions:

- prefer DOI or publisher pages, official arXiv pages, DBLP, OpenReview, ACL
  Anthology, IEEE, ACM, Springer, Nature, or equivalent canonical sources
- verify title, author list, venue, year, and DOI or canonical URL
- add the entry to `<proposal-dir>/bibs/working.bib` before using the cite key

Leave a visible `\todo{...}` instead of adding a citation when:

- preprint and published versions disagree and you cannot confirm the intended
  version
- multiple papers fit the description but the sentence does not disambiguate
- the exact local cite key for the team's own work cannot be located
- the candidate source supports only the general topic, not the specific claim

## What Not To Do

- Do not invent cite keys.
- Do not guess titles, authors, venues, years, or DOIs.
- Do not cite a paper just because it is nearby in topic.
- Do not copy a key from `template/` or examples without confirming the entry is
  the exact intended paper.
- Do not add dense citation clusters just to make a paragraph look scholarly.
