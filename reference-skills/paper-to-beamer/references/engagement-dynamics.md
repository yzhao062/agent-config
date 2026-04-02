# Engagement Dynamics

Use this to make the deck feel like a guided argument rather than a compressed paper.

## Core Principle

Prefer this rhythm:

1. raise a concrete question
2. create a small gap in understanding
3. answer it on the next slide
4. move to the next deeper question

Engagement here means clarity, curiosity, and forward motion, not hype.

Use narrative pressure selectively. Engagement should help the audience track the argument, not compete with it.

## Narrative Rules

- Start with the surprising or high-stakes part when the paper supports it.
- Delay low-value detail until the audience has a reason to care.
- Reveal the method as an answer to a previously stated challenge.
- Present results as answers to concrete uncertainties, not as bookkeeping.
- Return to neutral, compact exposition when the figure, table, or setup already carries the point.

## Calibrate by Slide Function

- High-engagement slides: opening problem, contributions, core method idea, headline result, main caveat, takeaways.
- Medium-engagement slides: intuition, setup, ablation, qualitative example, implication.
- Low-engagement slides: notation, metric summary, implementation detail, reference slide, appendix-like precision slides.

Do not try to make every slide equally memorable.

## Titles and Contrast

- Use informative titles that state a claim or a question.
- Keep titles readable at a glance. Prefer roughly 4-10 words when possible.
- Default to Title Case so the deck reads consistently at a glance. Keep lowercase only for standard acronyms, symbols, code-like tokens, or quoted phrases that should preserve source casing.
- Not every slide needs a claim title. Use stronger titles mainly on the central problem, novelty, strongest result, and most important caveat.
- Prefer contrast when the paper supports it:
  - prior assumption vs stronger setting
  - known-query attack vs query-agnostic attack
  - single-query optimization vs region-level optimization
  - stronger attacker knowledge vs weaker attacker knowledge
  - headline gain vs remaining limitation

Avoid titles that read like speaker notes or full explanatory sentences.

## Hooks and Anchor Phrases

- A deck usually needs one opening hook, not repeated re-hooking.
- Prefer at most one primary anchor phrase for the whole talk and optionally one secondary phrase for the main limitation or implication.
- If a figure or table already provides strong payoff, keep the surrounding wording restrained.

## Technical Pacing

Reveal technical material in layers:

1. intuition
2. challenge
3. formalization
4. implementation choice
5. implication

Do not jump directly from motivation to dense equations unless the paper is genuinely theorem-first.

For method-heavy papers aimed at non-experts:

- introduce at most one new abstract object per slide when possible
- let each method slide answer the obvious next question from the previous one
- prefer a recurring running example or visual strip over fresh slide-local examples
- if the audience must hold multiple new symbols at once, slow down and split the slide

Question-to-answer rhythm should be controlled, not constant. Use question framing when the audience naturally has the question and the next slide clearly resolves it.

## Evidence Pacing

Make result slides feel like answers:

- Can the method work under the claimed setting?
- Does it transfer across models or domains?
- What component drives the gain?
- How large is the effect in practical terms?
- Where does the method stop working?

Routine setup, metric, and baseline slides should stay compact. Explain only what affects interpretation, then move on.

## Audience-Memory Rule

Identify these before drafting:

- one sentence the audience should remember
- one slide they should remember
- one contrast they should remember
- one unresolved question they should leave with

If these are not clear, the deck is likely informative but not engaging.

## Presenter Freedom

- Leave room for live emphasis and timing.
- Do not write slide text that resolves every transition explicitly.
- Avoid decks that read like an essay or speaker script.
- Use breathing space: one clean visual or one clean takeaway can stand alone.

## Optional Planning Summary

Before generating the deck, write this internal summary:

- What is the most interesting question in the paper?
- What is the one thing that makes the audience care?
- What is the paper's sharpest contrast with prior work?
- What is the one most memorable figure, table, or example?
- Which slide should create the most curiosity?
- Which slide should provide the strongest payoff?
- Main hook:
- Main anchor phrase:
- 3 highest-salience slides:
- 3 support slides that should stay simple:
- Strongest visual payoff:
- Slides that risk feeling over-scripted:
- Titles that should be shortened:
- Where to leave more breathing space:

## Final Calibration Check

Before finalizing, ask:

1. Which 3 slides carry the most narrative weight?
2. Are the other slides appropriately quieter?
3. Is there exactly one main hook?
4. Is there exactly one main anchor phrase?
5. Are any titles too long or too explanatory?
6. Does any slide read like speaker notes instead of slide text?
7. Does engagement help the audience understand the paper, or just add wording?
8. In the method block, does each slide feel like the next step of one explanation rather than a separate mini-lecture?

## Avoid

- flat exposition with no question-to-answer rhythm
- generic section labels with no argumentative content
- equations before intuition
- large tables without explicit interpretation
- setup detail that never becomes relevant later
- evenly dense slides from start to finish
- repeated rhetorical hooks
- over-scripted slide text
