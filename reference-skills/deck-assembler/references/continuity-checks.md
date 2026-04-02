# Continuity Checks

Use this file before finalizing any merged deck.

## Quality Bar

The final deck should feel like:

- one talk with one throughline
- a clean merge of intro context and paper evidence
- a deck that reduces fragmentation without rewriting the papers

It should not feel like:

- raw concatenation of existing decks
- multiple title pages stapled together
- repeated mini-openings
- a talk that keeps resetting its audience assumptions

## Core Checks

Fail the merged deck if any of these are true:

- more than one visible title page or more than one visible roadmap
- a multi-paper merged talk has no clear talk-overview slide after the intro unless the user explicitly asked for a tighter variant
- a paper segment starts without a clear bridge or rationale
- the same motivation or background is repeated with no new payoff
- copied paper frames require macros, colors, or figure paths that are missing in the master deck
- visible style drift makes the deck feel like separate documents stitched together
- the merged deck changes technical claims, numbers, or figures without recording why
- the closing feels like multiple paper endings instead of one combined ending
- a long-form merged talk trims source-talk setup or evidence aggressively without a stated reason

## Per-Segment Self-Critique

For each inserted paper segment, answer these questions before finalizing:

- What role does this segment play in the merged talk?
- Which source frames are preserved?
- Which wrapper frames were omitted?
- What would be removed first if the overall deck is too long?
- Is it clear in about five seconds why this segment appears here?

If the last answer is `no`, revise the bridge slide or reduce repeated framing.

## Mergeability Checks

Before handoff, confirm:

- source decks remain untouched
- the new deck has one master preamble
- figure paths resolve from the merged deck directory
- imported macros and packages are recorded in `assembly-map.md`
- section names and transitions match the combined throughline
- if multiple paper segments are present, the intro is followed by a clear audience-facing talk overview unless the user asked not to add one

## Assembly Map Expectations

`assembly-map.md` should record at least:

- input intro module and source decks
- selected order of segments
- omitted wrapper slides
- bridge-slide purpose for each segment
- any macros, packages, or figure paths imported from source decks
