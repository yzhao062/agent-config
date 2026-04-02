# Project Brief Schema

Normalize the user's idea into this brief before drafting substantial prose.
This keeps composition stable across different calls.

If an active proposal folder already exists, derive the first-pass brief from
the introduction and overview paragraphs in `00-project-description.tex` before
asking the user for more material.

## Minimum Brief

- working title
- target NSF program or solicitation
- dominant proposal family: `ecosystem-building` or `methodology-driven`
- source path for the active proposal workspace, usually
  `proposals/<proposal-slug>/`
- one-paragraph problem statement
- one-paragraph proposed contribution
- intended beneficiaries or user communities
- 2-4 core technical or capability components
- preferred major-unit count if the user already knows it; otherwise assume 4
- rough evaluation plan
- main collaborators and their roles

## Extended Brief

Add these when available:

- scientific gap
- capability gap
- why now
- key prior work and differentiators
- required datasets, facilities, or external partners
- adoption or sustainability path
- broader impacts strategy
- management plan details
- known reviewer concerns
- hard solicitation constraints from `nsf-proposal-guardrail`

## Family-Specific Emphasis

### ecosystem-building

Prioritize:

- user communities
- ecosystem architecture
- partner roles
- adoption and sustainability
- measurable outcomes

### methodology-driven

Prioritize:

- research gap
- novelty claim
- aims or studies
- experimental logic
- risks, alternatives, and evaluation criteria

## Missing Information Policy

If the user gives only a rough idea, infer a first-pass brief with explicit
placeholders rather than stopping entirely. Mark assumptions clearly so the user
can refine them later.
