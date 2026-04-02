# Content Diagnosis

Use this before writing any slide plan. The goal is to diagnose what kind of paper this is and what deserves slide budget.

## Core Principle

Every slide must answer one of these questions for the audience:

- What is the research problem?
- Why does it matter?
- What is genuinely new?
- How does the method, system, or theory work?
- What evidence supports the claims?
- What assumptions, limits, or risks remain?

If a slide does not serve one of these roles, merge it or remove it.

## Required Diagnosis

Classify the paper into one primary type and at most one secondary type:

- empirical ML or benchmark paper
- method paper
- theory paper
- systems paper
- security, robustness, or privacy paper
- dataset or benchmark resource paper
- application paper

Then identify which of these are actually present and central:

- formal problem definition
- explicit contributions
- theorem, proposition, or proof sketch
- algorithm or objective
- architecture or pipeline figure
- key implementation choices
- quantitative main result
- ablation
- qualitative example
- failure case
- limitation discussion
- deployment or societal implications

Do not force absent categories into the deck.

## Planning Summary

Before outlining, write this internal summary:

- Paper type:
- Main research problem:
- Why it matters:
- Core novelty:
- Central technical mechanism:
- Strongest evidence:
- Most important caveat:
- Best figure or table to surface:
- What not to include because the paper does not contain it:

Also write this engagement summary:

- Most interesting question in the paper:
- One reason the audience should care:
- Sharpest contrast with prior work:
- One memorable figure, table, or example:
- Slide that should create the most curiosity:
- Slide that should provide the strongest payoff:
- Main hook:
- Main anchor phrase:
- 3 highest-salience slides:
- 3 support slides that should stay simple:
- Titles that should be shortened:
- Slides that risk feeling over-scripted:
- Where to leave more breathing space:

Also write this visual summary:

- Strongest visual anchor:
- Best method visual:
- Best result visual:
- Concrete before-vs-after example available:
- Slides that are too text-heavy:
- Longest text-only streak in the current plan:
- Tables that should be reduced:
- Figures that should be cropped, reduced, or replaced by a source-built schematic:
- Slides that should become visual-first:

Also write this time-flex summary:

- Nominal talk length:
- Safe core length:
- Method-budget target:
- Minimal talk spine:
- Core slides:
- Optional expansion slides:
- Skip-safe slides:
- Backup slides:
- Best shortening points:
- Best expansion points:
- Full extended length:
- Section timing:

Also write this method-comprehension summary when the paper is method-heavy:

- Broad-audience assumption:
- Running example available:
- Persistent visual anchor:
- Method slides that must stay text-first:
- Equations that need companion visuals:
- Non-expert bottlenecks:
- Per-slide abstraction ladder:
- Where to slow down:
- Where to compress:

Also build this normalized fact table before any slide prose:

- task or setting
- datasets
- baselines
- metrics
- method components
- equations or objectives
- implementation choices
- key tables and figures
- headline results
- ablations
- limitations or caveats
- ambiguities
- citation or evidence source for each numeric fact likely to appear on slides

Every numeric claim in visible slide text should come from this fact table rather than being regenerated from memory later.

## Contribution Framing

Always include a contribution slide. State contributions as research contributions, not feature lists.

Use one or more of:

- new problem formulation
- new method or algorithm
- new theoretical result
- new system design
- new benchmark or dataset
- new empirical finding
- new analysis or insight

## Adaptation by Paper Type

- Theory papers: spend more budget on definitions, assumptions, theorem statements, and proof intuition. Keep experiments brief unless they are central.
- Empirical method papers: emphasize problem setup, method intuition, objective, experimental design, and main results. If the method is the main contribution, reserve a larger method budget by default, often 6-8 slides in a 20-25 minute talk. Include one slide on what drives gains.
- Method papers: before outlining, decide whether the audience could explain the mechanism back after the talk. If not, the method block is under-budgeted. Prefer layering the explanation across overview, challenge, formalization, core mechanism, second mechanism, and implementation assumptions.
- For method-heavy papers aimed at a broad CS audience, identify the first abstract object likely to lose non-experts. Add a bridge before that point: a toy example, a visual strip, a concrete before-vs-after contrast, or a plain-language target-definition slide.
- Systems papers: emphasize architecture, engineering tradeoffs, complexity, scalability, and operational constraints.
- Security, robustness, or privacy papers: make the threat model explicit, separate attacker assumptions from deployment realism, and note missing adaptive defenses or unrealistic constraints.
- Dataset or benchmark papers: emphasize benchmark motivation, construction, coverage, protocol, and what new conclusions the benchmark enables.
- Application papers: emphasize task setting, data conditions, domain constraints, and practical validity. Separate domain contribution from algorithmic contribution.

## Evidence Discipline

Use precise wording:

- the paper evaluates on ...
- the reported results suggest ...
- the paper does not isolate ...
- [Paper unclear on X]

Never claim deployment readiness, robustness guarantees, causal interpretation, or out-of-scope generalization unless the paper actually supports it.

## Anti-Patterns

Do not:

- mechanically map every paper to the same 16-slide pattern
- force theory, attack, failure-case, or deployment slides when absent
- bury the main claim in the middle of the talk
- repeat paper text without interpretation
- turn limitations into unsupported criticism
- overcompress crowded result slides instead of splitting them
- flatten the narrative so every slide has the same depth and urgency
- make every slide load-bearing
