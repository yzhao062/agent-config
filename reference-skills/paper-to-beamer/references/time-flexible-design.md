# Time-Flexible Design

Use this to design the deck as a layered talk rather than a rigid script. Use `presenter-map.md` to record the actual slide roles, timings, and skip jumps after the structure is decided.

## Core Principle

A good deck should have:

- a core path that fits safely within the nominal time
- optional expansion slides that can be included if time allows
- skip-safe slides that can be removed without breaking the logic
- backup slides for deeper technical discussion
- enough total content that a full version can use most of a 20-25 minute slot without feeling padded

Do not build the deck so tightly that every slide is required.

## Default Time Budgeting

For an advertised talk length of `T` minutes:

- design the core path for about `0.7T` to `0.8T`
- leave the rest for pauses, transitions, questions, and optional detail

Examples:

- 20-minute talk -> core path around 14 to 16 minutes
- 25-minute talk -> core path around 18 to 20 minutes
- 30-minute talk -> core path around 21 to 24 minutes

When the paper has enough substance, prefer a fuller extended deck with obvious skip points over an over-compressed deck that leaves useful evidence out.

## Slide Roles

Separate slides into four roles:

- `CORE`: required for the talk to make sense
- `OPTIONAL`: deepens the talk but is not required for coherence
- `SKIP FIRST`: useful support material that should not be load-bearing
- `BACKUP`: not part of the planned main flow

These labels can live in source comments or light internal annotations. Do not make them visually dominant unless requested.

The presenter-facing delivery artifact should mirror these roles.

## Minimal Talk Spine

Before drafting the full deck, identify:

1. What is the research problem?
2. Why is it important?
3. What is the key idea?
4. What is the strongest result?
5. What is the main caveat?

This spine should already form a complete talk.

## Skip-Safe Design

A slide is skip-safe only if the previous and next slides still connect directly.

Good pattern:

- core claim
- optional intuition
- formal method

Bad pattern:

- claim
- hidden definition
- formal method

Do not define essential notation or key terms only on optional slides.

## Local Blocks and Progressive Depth

Organize sections as local blocks rather than one fragile chain.

For each block, think in levels:

- Level 1: one-slide version
- Level 2: two-slide version
- Level 3: extended version with deeper detail

Example for a method block:

- Level 1: core idea
- Level 2: add objective
- Level 3: add the next load-bearing mechanism, implementation choice, or proof intuition

For method-heavy papers, extend this idea into a fuller main-path block when the method is the paper's real novelty:

- Level 1: method overview
- Level 2: add challenge and formalization
- Level 3: add whichever deeper mechanism, theorem step, control loop, or implementation assumption actually carries the paper

In a 20-25 minute talk, this often means 6-8 method slides in the full path, with a shorter 3-4 slide core path available only through clean skip points rather than initial under-allocation.

Use the same pattern for evidence blocks:

- Level 1: headline result
- Level 2: add one concrete visual payoff slide
- Level 3: add ablation, caveat, or secondary result

## Endings and Backup

- End the main deck with a complete takeaway slide.
- Put optional or backup slides after that.
- Do not require backup material to reach the real conclusion.

## Multi-Paper Talks

If presenting two papers in one session:

- use one shared opening when possible
- compress each paper into a clear core path
- reserve optional slides inside each paper block
- keep the transition between papers brief and explicit
- prefer a shared closing if the papers support it

## Planning Summary

Before generating the deck, write this internal summary:

- Nominal talk length:
- Safe core length:
- Single most important claim:
- Minimal talk spine:
- Core slides:
- Optional expansion slides:
- Skip-safe slides:
- Backup slides:
- Best shortening points:
- Best expansion points:
- Full extended length:
- Section timing:
- If presenting two papers, what opening and closing can be shared?

## Final Check

Before finalizing, verify:

1. Can the talk still work if about 20 percent of slides are skipped?
2. Is there a clean version that fits safely within time?
3. Are there at least 2 clear expansion points?
4. Are there at least 2 clear shortening points?
5. Does the ending still work without optional slides?
