# Intro Aim Sync

Use this file when Codex needs to keep the introduction and aim files aligned
inside an active proposal folder.

## Default Rule

Treat `00-project-description.tex` as the current narrative entrypoint.

When a proposal folder already exists:

1. read the introduction and overview paragraphs first
2. normalize them into a project brief with importance, gaps, and central claim
3. generate or revise `11-aim1.tex` through `14-aim4.tex`
4. return to `00-project-description.tex` and refresh the introduction so it
   promises the same units and same scope

This rule is directional only for the first pass. After the aims become the
more stable structure, reverse the direction:

1. read `11-aim1.tex` through `14-aim4.tex`
2. extract the active unit titles, sequence, dependencies, and scope
3. refresh the introduction and bridge paragraphs
4. leave detailed technical prose in the aim files rather than duplicating it
   in the introduction

In this repository, `proposals/` is a container. The active drafting target
should be one concrete workspace such as `proposals/nsf-25-533-fairos/`.

## Template Markers

The template uses comment markers to make this safe for both agents and human
coauthors:

- `% composer:intro-seed-start`
- `% composer:intro-seed-end`
- `% composer:aim-inputs-start`
- `% composer:aim-inputs-end`

These markers are plain comments. They are there to help Codex patch the right
region without forcing collaborators into any special workflow.

Inside each numbered aim or thrust file, the template also uses:

- `% composer:sync-start`
- `% composer:sync-end`
- `% refiner:body-start`
- `% refiner:body-end`

By default, intro or summary sync passes should touch only the
`composer:sync` region and leave the `refiner:body` region alone.

## What To Refresh After Aim Changes

After changing aims, revisit the introduction and refresh:

- the first-paragraph importance framing if the proposal emphasis changed
- the gap or challenge list if the thrust logic changed
- the problem framing if the scope changed
- the overview paragraph that enumerates the aims or thrusts
- any references to the number or role of major units
- any promises about evaluation or adoption that were moved into different aims
- the bridge paragraphs between the introduction and the `11-14` aim inputs if
  they still encode an older narrative or family-specific framing

The introduction should answer only:

- why the problem matters
- what the main gaps are
- what problem the project addresses
- what the overall contribution is
- what the major units are
- why the units form a coherent progression

Do not try to mirror every subtask from the aim files.

Do not rewrite unaffected collaborator-owned sections just to make the draft
look stylistically uniform.
