# Quality Checks

Use this file after drafting and before preview generation or handoff.

## Quality Bar

The final module should feel like:

- a stable reusable intro insert
- a clean identity + agenda + systems block
- a module that can be dropped into another deck with minimal editing

It should not feel like:

- a website summary
- a compressed CV
- a metrics wall
- a second talk opening
- a project catalog

## Role Separation

Default slide family:

- `About Yue Zhao`
- `FORTIS Lab Research Agenda`
- `Representative Systems and Impact`

Required role split:

- Slide 1: identity and positioning
- Slide 2: agenda map
- Slide 3: execution evidence

Fail the draft if one slide is trying to do two or three of these jobs at once.

## Dominant Mode And Primary Object

Each slide must be classified as exactly one of:

- `text-first`
- `visual-first`
- `compact card grid`

Each slide must also have exactly one primary object of attention.

Fail the draft if the audience has to choose between multiple equally important regions.

## Per-Slide Self-Critique

Before finalizing, internally answer these questions for each slide:

- What is the slide role?
- What is the dominant mode?
- What is the primary object?
- What should be removed first if the slide feels crowded?
- Is the slide understandable in about five seconds?
- Does the wording feel like slide text rather than profile prose?

If either of the last two answers is `no`, revise again.

## Density Checks

Fail the preview if any slide violates these checks:

- more than one dominant mode
- more than one primary object of attention
- a long prose block that reads like website copy
- a personal slide that becomes metrics-heavy
- a systems slide with more than `4` representative projects
- a systems slide that mixes project cards, a long takeaway paragraph, and a dense metrics strip
- a systems slide where sponsor logos become as visually strong as the project cards or stronger than the metrics strip
- any volatile number without a dated source in `yzhao-intro-facts.md`
- slide text that depends on presenter notes or surrounding deck context

## Metrics Checks

If including stars, downloads, scans, vulnerability counts, or similar signals:

- record the exact source and date in `yzhao-intro-facts.md`
- put metrics only on the systems slide
- keep them visually secondary to the project cards
- add an explicit visible date only when the slide text needs it for interpretation
- remove the metrics entirely if they create clutter or compete with the main object

## Sponsor Checks

If including sponsor or research-support logos:

- keep them only on the systems slide unless the user explicitly asks otherwise
- keep the strip visually quieter than the metrics strip
- cap the row to a small selected set rather than a logo wall
- record the chosen assets and rationale in `yzhao-intro-facts.md`
- remove the sponsor strip before removing the metrics strip if Slide 3 starts to feel crowded

## Safe Slide Surgery

Revise weak slides in this order:

1. tighten the title
2. shorten or regroup bullets
3. reduce repeated phrasing
4. convert paragraph text into grouped bullets or compact cards
5. remove secondary content that competes with the main object
6. for the agenda slide, add one subtle relation visual if the space still feels underused
7. only then consider a layout change

Do not jump straight to a major redesign if shortening and regrouping are enough.

## Mergeability Checks

Before finalizing, confirm:

- output remains frame blocks only
- slides stay theme-compatible
- module remains reusable in arbitrary decks
- wording does not assume section pages, presenter notes, slide numbering, or venue-specific context
