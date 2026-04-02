# Major Unit Patterns

Use this file when the user gives only a core proposal idea and Codex needs a
first-pass decomposition into numbered aim files.

The examples in this repository most often use 4 core units. Treat 4 as the
default pattern for both proposal families unless the idea is obviously smaller
or the user asks for a 3-unit draft.

## methodology-driven

Dominant file label:

- `Aim` by default
- `Study` only when the anchor examples or solicitation make that more natural

Default 4-unit progression:

1. `Aim 1`: problem formulation, representation, data, perception, or
   foundational anomaly mechanism
2. `Aim 2`: core model, algorithm, reasoning engine, or primary technical
   advance
3. `Aim 3`: external interaction, decision support, deployment pathway, or
   system-level integration of the method
4. `Aim 4`: cross-cutting meta layer such as multi-agent interaction,
   human-in-the-loop behavior, robustness, adaptation, or supervisory control

If the idea only supports 3 units, merge the last two roles into a single
integration aim.

Useful anchors in this repo:

- `examples/proposals/NSF-Core-2026-Feb5th-Agentic-AD/01aim1.tex`
- `examples/proposals/NSF-Core-2026-Feb5th-Agentic-AD/02aim2.tex`
- `examples/proposals/NSF-SaTC-MultiAgent-Safety/01aim1-perception.tex`
- `examples/proposals/NSF-SaTC-MultiAgent-Safety/04aim4-meta.tex`

## ecosystem-building

Dominant file label:

- `Thrust` by default
- `Task` or `Work Package` when the anchor example already uses that language

Default 4-unit progression:

1. unit 1: architecture, data/resource substrate, or ecosystem foundation
2. unit 2: interoperability, intelligence layer, tooling, or enabling methods
3. unit 3: user-facing workflows, domain deployment, or application-facing
   capability buildout
4. unit 4: community engagement, adoption, governance, and sustainability

If the idea only supports 3 units, merge the last two roles into a single
deployment-and-adoption unit.

Useful anchors in this repo:

- `examples/proposals/GEO OSE Proposal/1thrust1-spatio-temporal-scoping.tex`
- `examples/proposals/GEO OSE Proposal/4thrust4community_new.tex`
- `examples/proposals/NSF_POSE_Phase_1_Proposal/2Approach.tex`

## Selection Rule

Choose the first-pass unit progression that makes the full proposal read as a
progression rather than a bag of parallel tasks.

The numbered units should usually move:

- from local or foundational capability to broader interaction or deployment
- from technical core to adoption or meta-control
- from upstream dependencies to downstream integration
