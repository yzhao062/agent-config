# Figure Archetypes

Use this file to map a proposal need to one of a small number of reusable
figure patterns.

## 1. Overview Architecture

Use when the proposal introduction needs a single visual summary of the whole
project.

Typical content:

- problem setting or input context
- 3-4 major technical or capability layers
- outputs, testbeds, or broader impacts

Representative examples in this repo:

- `examples/proposals/NSF-Core-2026-Feb5th-Agentic-AD/00-project-description.tex`
  with `figure/agentad-general-new-small.pdf`
- `examples/proposals/NSF_POSE_Phase_1_Proposal/000description.tex`
  with `figs/ecosystem-pic-all.pdf`
- `examples/proposals/NSF-23-POSE-Phase-II-OpenAD/main.tex`
  with `figure/OpenAD-illustration-final.pdf`

## 2. Thrust Mechanism

Use when a single thrust or aim needs one picture that clarifies the local
mechanism.

Typical content:

- 2-4 subtasks or stages
- core data objects or signals
- one or two key transitions
- optionally one explicit output artifact

Representative examples:

- `examples/proposals/NSF-Core-2026-Feb5th-Agentic-AD/01aim1.tex`
  with `figure/agentad-aim1.pdf`
- `examples/proposals/GEO OSE Proposal/2thrust2-llm-reasoning.tex`
  with `figs/thrust2.pdf`
- `examples/proposals/NSF25_S_CC_Full_Proposal/main.tex`
  with `figs/new/fig-1-1.pdf`

## 3. Workflow Or Method Pipeline

Use when the proposal needs a concrete task flow, algorithm pipeline, or
data-processing path.

Typical content:

- inputs
- transforms
- intermediate artifacts
- outputs or metrics

Representative examples:

- `examples/proposals/CPS_CIR_2025_Foodbank/03 study 02 - rl.tex`
  with `figs/task2.1.pdf`, `figs/task2.2.pdf`, `figs/task2.3.pdf`
- `examples/proposals/NSF_Algorithms_for_Threat_Detection___2024/03 study 02 - trajectory encoding and embedding.tex`
  with `fig/study 2 flowchart.pdf`
- `examples/proposals/NSF_Algorithms_for_Threat_Detection___2024/03 study 03 - gnn.tex`
  with `fig/study 3 flowchart.pdf`

## 4. Timeline Or Work Plan

Use for proposal-wide sequencing, milestones, and collaboration logic.

Typical content:

- years or semesters
- thrust ownership
- deliverables
- evaluation milestones

Representative examples:

- `examples/proposals/NSF-Core-2026-Feb5th-Agentic-AD/05evaluation.tex`
  with `figure/timeline.pdf`
- `examples/proposals/GEO OSE Proposal/5evaluation.tex`
  with `figs/timeline-extended.pdf`
- `examples/proposals/NSF_POSE_Phase_1_Proposal/000description.tex`
  with `figs/timeline-metrics.pdf`

## 5. Ecosystem Or Adoption

Use for open-ecosystem, infrastructure, governance, or community-building
proposals.

Typical content:

- platform or tool stack
- contributors or communities
- governance or adoption loops
- sustainability or impact pathways

Representative examples:

- `examples/proposals/NSF_POSE_Phase_1_Proposal/000description.tex`
  with `figs/ecosystem-pic-all.pdf`
- `examples/proposals/NSF-23-POSE-Phase-II-OpenAD/main.tex`
  with `figure/development process - final.pdf`
- `examples/proposals/NSF_24_POSE_Phase_I_TrustLLM/project_description.tex`
  with `figure/development process - final.pdf`

## 6. Evidence Or Impact

Use when the figure's main job is to document uptake, citation, reach, or
deployment evidence rather than method mechanics.

Typical content:

- usage footprint
- citation or adoption map
- partner or stakeholder reach
- system outcomes

Representative examples:

- `examples/proposals/NSF_24_POSE_Phase_I_TrustLLM/project_description.tex`
  with `figure/citation-map.png`
- `examples/proposals/NSF_POSE_Phase_1_Proposal/000description.tex`
  with `figs/citation_map.png`

## Quick Heuristic

- if the whole proposal needs one memorable picture, choose
  `overview-architecture`
- if one thrust is still hard to explain, choose `thrust-mechanism`
- if the logic is a process, choose `workflow-or-method-pipeline`
- if the question is sequencing or milestones, choose `timeline-or-work-plan`
- if the question is community or infrastructure growth, choose
  `ecosystem-or-adoption`
- if the question is proof of traction, choose `evidence-or-impact`
