# Presenter Map

Use this to turn the structural plan from `time-flexible-design.md` into a concrete presenter-facing artifact.

## Core Principle

Do not output only the deck. Also output a short delivery map that tells the speaker:

- which slides are core
- which slides can be skipped first
- which slides are optional expansions
- which slides are backup only
- where to shorten or extend cleanly

Default artifact: `decks/<paper-slug>/presenter-map.md`

This map complements source comments such as `CORE`, `OPTIONAL`, `SKIP FIRST`, and `BACKUP`; it does not replace them.

## Required Fields

For each substantive slide, include:

- slide number
- short title
- role: `CORE`, `OPTIONAL`, `SKIP FIRST`, or `BACKUP`
- estimated speaking time
- why the slide matters
- what slide it can jump to if skipped

If a slide is marked skippable, the jump target is required.

## Time Summary

The presenter map should explicitly state:

- nominal talk length
- safe core length
- full extended length
- whether the current deck is closer to a tight talk or a fuller 20-25 minute version

Also summarize each section with:

- section name
- core time
- extended time
- first shortening point
- best expansion point

## Role Meanings

- `CORE`: required for the talk to make sense
- `OPTIONAL`: useful depth if time allows
- `SKIP FIRST`: useful but should be dropped first under time pressure
- `BACKUP`: Q&A or overflow material only

## Transition Safety

A slide is not truly skippable if it contains:

- the only definition of a key term
- the only explanation of a later result
- notation required by the next slide
- the only rationale for the method

If skipping breaks understanding, the slide should be `CORE` or the content should move.

## Multi-Paper Talks

For multi-paper talks, the presenter map should also note:

- shared opening slides
- per-paper core path
- per-paper optional slides
- shared closing slides
- where to shorten paper 1 or paper 2 if time shifts

## Compact Format Example

- Slide 3 - Problem Setup - `CORE` - 1.5 min - establishes the threat and stakes - if skipping slide 4, jump to slide 5
- Slide 7 - Implementation Choices - `SKIP FIRST` - 0.8 min - useful detail, not load-bearing - jump to slide 8
- Slide 11 - Ablation - `OPTIONAL` - 1.2 min - explains what drives gains - can be skipped if late
- Slide 14 - Backup: Min-Max View - `BACKUP` - Q&A only

## Final Check

Before finalizing, verify:

1. Can the speaker finish cleanly using only the core slides?
2. Are there at least 2 clear shortening points?
3. Are there at least 2 clear expansion points?
4. Are optional slides truly skip-safe?
5. Is the ending complete even if optional slides are skipped?
