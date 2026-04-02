# Deck Outline

Use this as a planning guide for a 20-25 minute paper talk aimed at a broad CS academic audience. It is a default starting point, not a rigid template.

## Defaults

- Main deck: 17-21 slides
- Appendix: 2-5 optional backup slides
- Tone: technically precise, cross-subfield readable
- Each main slide should have one clear job
- Omit or merge slide types that the paper does not support
- Favor a guided argument with question-to-answer rhythm
- Design the required core path for about 70 to 80 percent of the advertised time
- Aim for 3 to 5 strong visual-payoff slides in the main path
- Avoid long runs of text-first slides when the paper provides usable figures, tables, or equations
- For method-heavy papers, expect the method block to take about 6-8 slides in the fuller main path rather than 3-4 compressed technical slides
- For especially dense method-heavy, theory-heavy, systems-heavy, or multi-stage papers, it is acceptable for the numbered main path to grow to about 19-23 slides when that is what makes the deck understandable

## Core Slide Roles

Most good paper talks cover these roles:

1. Title and context
2. Problem and importance
3. Explicit contributions
4. Technical core
5. Evidence
6. Caveats and takeaways

Allocate slide budget around those roles based on paper type.

Within those roles, keep the audience moving with simple open loops: one slide raises a concrete question, the next slide answers it.

## Core vs Optional Structure

For a typical paper talk:

- Core slides: problem, importance, contributions, core method idea, strongest evidence, main caveat, takeaways
- Optional expansion: proof intuition, implementation detail, secondary ablations, extra critique
- Skip-safe support: detailed setup, full baseline list, secondary tables, extra intuition
- Backup: appendix-style theorem detail, extra results, likely Q\&A material

## Example 18-Slide Shape

1. Title and paper context
2. Problem statement
3. Why the problem matters
4. Main contributions
5. Method overview with central figure
6. Technical intuition or challenge
7. Objective, theorem, or algorithm core
8. Implementation, complexity, or design choices
9. Experimental setup
10. Headline quantitative result
11. Before-vs-after result or strongest visual payoff
12. Secondary evidence or transfer result
13. Ablation or component analysis
14. Failure case, qualitative analysis, or robustness caveat
15. Limitations and assumptions
16. Broader critique or deployment implications
17. Key takeaways
18. Questions or discussion

Use this example only when the paper actually contains those elements. Do not force slides 7, 11, 13, 14, or 16 if the paper does not provide that content.

## Engagement Rules

- Prefer meaningful titles such as claims, contrasts, or questions.
- Keep routine support slides calmer than the high-salience slides.
- Surface the strongest or most surprising supported result early enough that the audience has a reason to follow the rest.
- Use one memorable anchor when possible: a central figure, a decisive table, a before-vs-after example, or a compact contrast phrase.
- Keep routine setup short unless it materially affects the conclusion.
- Keep the main path from becoming bullet-dominated.
- If the paper supports it, do not allow more than two consecutive text-heavy support slides in the main path.

## Research Question Framing

For empirical or evaluation-heavy papers, organize the evidence around 2-4 research questions when possible.

Examples:

- Does the method outperform strong baselines?
- Does it transfer across models or domains?
- Which components matter?
- Under what settings does it fail?

These questions should appear implicitly in the talk flow, not just in the planner.

## Adaptation Rules

- For theory-heavy papers, spend slides 6-9 on definitions, assumptions, theorem statements, and proof sketches. Compress setup and qualitative analysis if the paper has little empirical content.
- For empirical method papers, use more room for the method itself before the evidence block. If the method is the real novelty, budget about 6-8 slides for method explanation, but choose the internal structure that matches the paper rather than forcing one fixed progression.
- For method papers, choose a progressive technical block that matches the real mechanism: for example running example plus overview plus one major operation per slide, or assumptions plus theorem plus proof sketch, or architecture plus bottleneck plus control loop. Do not force one fixed stage template across papers.
- For method-heavy papers presented to broad-CS audiences, make the method block cumulative rather than modular. Reuse one running example, one color mapping, or one recurring strip when possible so the audience is not forced to relearn the visual language on every slide.
- In method blocks, prefer one new abstraction per slide. If a slide introduces a new variable, state, or score, keep the rest of the slide familiar from the previous one.
- For systems papers, use more room for architecture, complexity, throughput, latency, cost, scaling, or bottlenecks.
- For safety, robustness, privacy, or security papers, reserve a late slide for threat-model realism, attack surface, defenses, or deployment constraints.
- For dataset or benchmark papers, replace some method detail with benchmark construction, coverage, and evaluation protocol.
- If the paper has one indispensable figure, show it on slide 5 or 6 and orient the rest of the method section around it.
- If the paper has multiple useful visuals, spread them across method and evidence rather than clustering them all in one section.

## Appendix Guidance

- Add a references frame when citations are used.
- Add one or two backup slides for extra ablations, theorem details, or experimental caveats if the paper is likely to trigger questions there.
- End the main deck cleanly before optional or backup material starts.
- Output a presenter-facing map alongside the main deck.
