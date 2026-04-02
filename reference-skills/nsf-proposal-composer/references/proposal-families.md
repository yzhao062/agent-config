# Proposal Families

Use exactly one dominant family when composing a proposal. Do not add a third
family unless the repository's examples and user workflow prove the split is
insufficient.

## 1. ecosystem-building

Use this family for proposals whose primary value is building an open ecosystem,
platform, infrastructure, workflow, community, or adoption pathway.

Reviewer question:
Will this capability actually get built, adopted, and sustained?

Typical signals:

- open ecosystem
- open science
- platform or infrastructure
- community resource
- mentoring or workforce development tightly tied to the technical plan
- deployment, adoption, translation, or broad enablement

Default narrative arc:

1. motivate the need and who is blocked today
2. define the ecosystem or platform vision
3. describe the architecture or capability model
4. break execution into work packages or thrusts
5. show adoption, community engagement, and sustainability logic
6. define measurable outcomes and evaluation

Common section labels:

- vision
- ecosystem architecture
- work packages
- adoption plan
- community engagement
- management plan
- measurable outcomes

Common failure mode:
The proposal reads like a generic software roadmap instead of a credible NSF
research-capability case.

## 2. methodology-driven

Use this family for proposals whose primary value is a new method, algorithm,
theory, system methodology, or technically novel research agenda.

Reviewer question:
Is the technical novelty real, coherent, and testable?

Typical signals:

- new method or algorithm
- hypothesis-driven technical advance
- clear research gap
- aims or studies structure
- benchmark, dataset, or experimental evaluation
- risk and mitigation tied to technical uncertainty

Default narrative arc:

1. define the problem and research gap
2. state the core hypothesis or technical premise
3. decompose into aims or studies
4. explain methods and alternatives
5. define evaluation and success criteria
6. connect to broader impacts

Common section labels:

- aims
- studies
- technical approach
- risk and mitigation
- evaluation
- intellectual merit

Common failure mode:
The proposal reads like an incremental paper plan without clear program-scale
impact or reviewer-facing justification.

## Decision Rule

Choose `ecosystem-building` if the strongest win condition is proving that a
shared capability, platform, or open ecosystem will exist and be used.

Choose `methodology-driven` if the strongest win condition is proving that the
technical research contribution is novel and testable.

If both appear true, choose the family that should dominate the project
summary's first paragraph. Treat the other emphasis as an overlay, not a new
family.

## Example Signals In This Repo

Likely `ecosystem-building` examples:

- `examples/proposals/GEO OSE Proposal`
- `examples/proposals/NSF-23-POSE-Phase-II-OpenAD`
- `examples/proposals/NSF_24_POSE_Phase_I_TrustLLM`
- `examples/proposals/NSF_POSE_Phase_1_Proposal`

Likely `methodology-driven` examples:

- `examples/proposals/NSF-Core-2026-Feb5th-Agentic-AD`
- `examples/proposals/NSF-SaTC-MultiAgent-Safety`
- `examples/proposals/NSF_Algorithms_for_Threat_Detection___2024`

Some newer examples may need a quick manual classification pass before using
them as style anchors.
