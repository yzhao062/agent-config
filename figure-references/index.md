# Figure Reference Bank

This folder stores reusable figure references organized by visual job and
composition pattern, not by project history.

Unless marked otherwise, references in this bank are treated as broadly
approved by default.

## Label Schema

- `role`
  `structure` = strong composition or geometry donor
  `style` = primarily a finish, palette, or visual-language donor
  `both` = useful for both structure and style

- `density`
  `low`, `medium`, `high`

- `liked_traits`
  Short operational tags the figure skill can reuse during reference
  grounding.

- `reuse_for`
  The figure settings where the reference is most likely to help.

## Usage Rules

- Keep only the most relevant 1-3 references active for any one figure task.
- Use one structural base and at most 1-2 style donors.
- Do not try to average many references into one prompt.
- Prefer same-archetype structure donors before cross-archetype borrowing.
- Treat result panels as companion donors by default, not as the main target of
  an LLM-generated figure workflow.

## System Overviews And Architectures

- `overview-architecture/agentad-general-new-small.pdf` | `role: both` | `density: high` | `liked_traits: grouped regions; end-to-end story; central orchestrator; compact proposal overview` | `reuse_for: overview-architecture; platform architecture; ecosystem overview`
- `overview-architecture/attack.jpg` | `role: style` | `density: medium` | `liked_traits: contrastive framing; directional flow; clean story split` | `reuse_for: motivation overview; before-after framing; contrast diagrams`
- `overview-architecture/defense.jpg` | `role: style` | `density: medium` | `liked_traits: contrastive framing; directional flow; clean story split` | `reuse_for: motivation overview; defense-side framing; contrast diagrams`
- `overview-architecture/intro-illustration.png` | `role: both` | `density: medium` | `liked_traits: clean intro composition; moderate text; explanatory illustration` | `reuse_for: intro figure; overview-architecture; teaser overview`
- `overview-architecture/openad-illustration-final.pdf` | `role: both` | `density: high` | `liked_traits: polished proposal hierarchy; grouped modules; balanced multi-zone overview` | `reuse_for: overview-architecture; capability architecture; proposal intro`
- `overview-architecture/overview-2.pdf` | `role: both` | `density: high` | `liked_traits: end-to-end architecture; balanced blocks; readable overview density` | `reuse_for: overview-architecture; infrastructure overview; cross-domain intro`
- `overview-architecture/short-illustration.jpg` | `role: style` | `density: low` | `liked_traits: concise intro visual; simplified narrative; quick read` | `reuse_for: teaser figure; short overview; simplified intro visual`
- `overview-architecture/skills1.png` | `role: structure` | `density: medium` | `liked_traits: separate question cue; dominant central thrust stack; grouped testbeds; distinct outcomes card; bottom FAIR strip` | `reuse_for: overview-architecture; proposal intro; capability stack`
- `overview-architecture/skills2.png` | `role: both` | `density: medium` | `liked_traits: polished overview card hierarchy; restrained typography; compact right-side outcomes card; quiet bottom strip` | `reuse_for: overview-architecture; proposal intro; infrastructure overview`

## Workflows, Aims, And Local Pipelines

- `thrust-and-task-pipelines/agentad-aim1-small.pdf` | `role: structure` | `density: medium` | `liked_traits: single-aim decomposition; staged logic; compact thrust figure` | `reuse_for: aim figure; thrust figure; task breakdown`
- `thrust-and-task-pipelines/agentad-aim2-small.pdf` | `role: structure` | `density: medium` | `liked_traits: single-aim decomposition; staged logic; compact thrust figure` | `reuse_for: aim figure; thrust figure; task breakdown`
- `thrust-and-task-pipelines/agentad-aim3-small.pdf` | `role: structure` | `density: medium` | `liked_traits: single-aim decomposition; staged logic; compact thrust figure` | `reuse_for: aim figure; thrust figure; task breakdown`
- `thrust-and-task-pipelines/aim-1.jpg` | `role: both` | `density: medium` | `liked_traits: task sequencing; grouped submodules; readable pipeline` | `reuse_for: aim figure; method workflow; thrust subfigure`
- `thrust-and-task-pipelines/aim-4.jpg` | `role: both` | `density: medium` | `liked_traits: task sequencing; grouped submodules; readable pipeline` | `reuse_for: aim figure; method workflow; thrust subfigure`
- `thrust-and-task-pipelines/development-process-final.pdf` | `role: both` | `density: medium` | `liked_traits: process flow; lifecycle logic; development stages` | `reuse_for: workflow pipeline; development process; method lifecycle`
- `thrust-and-task-pipelines/task-2-1.pdf` | `role: structure` | `density: medium` | `liked_traits: subtask breakdown; focused workflow; local pipeline` | `reuse_for: task figure; local method pipeline`
- `thrust-and-task-pipelines/task-2-2.pdf` | `role: structure` | `density: medium` | `liked_traits: subtask breakdown; focused workflow; local pipeline` | `reuse_for: task figure; local method pipeline`
- `thrust-and-task-pipelines/task-2-3.pdf` | `role: structure` | `density: medium` | `liked_traits: subtask breakdown; focused workflow; local pipeline` | `reuse_for: task figure; local method pipeline`
- `thrust-and-task-pipelines/thrust-1.png` | `role: both` | `density: medium` | `liked_traits: layered thrust logic; readable grouped stages; proposal-friendly flow` | `reuse_for: thrust figure; capability stack; method decomposition`
- `thrust-and-task-pipelines/thrust-2.pdf` | `role: both` | `density: medium` | `liked_traits: layered thrust logic; readable grouped stages; proposal-friendly flow` | `reuse_for: thrust figure; capability stack; method decomposition`
- `thrust-and-task-pipelines/thrust-3.pdf` | `role: both` | `density: medium` | `liked_traits: layered thrust logic; readable grouped stages; proposal-friendly flow` | `reuse_for: thrust figure; capability stack; method decomposition`

## Method Composites And Scientific Schematics

- `method-composites/dispersion-motivation.png` | `role: both` | `density: medium` | `liked_traits: motivation plus mechanism; composite storytelling; modular explanation` | `reuse_for: method composite; motivation schematic; system overview`
- `method-composites/dispersion-observation-distillation.png` | `role: both` | `density: high` | `liked_traits: multi-stage method composite; distilled pipeline; linked modules` | `reuse_for: method composite; multi-stage workflow; architecture-meets-results`
- `method-composites/dispersion-observation.png` | `role: both` | `density: high` | `liked_traits: observation-driven schematic; linked modules; compact composite narrative` | `reuse_for: method composite; architecture plus evidence; system story`
- `method-composites/immunostruct-contrastive.png` | `role: both` | `density: medium` | `liked_traits: contrastive method schematic; paired modules; strong explanatory structure` | `reuse_for: method composite; training objective schematic; comparative mechanism`
- `method-composites/immunostruct-results-cedar.png` | `role: style` | `density: medium` | `liked_traits: compact evaluation block; publication panel finish; crisp label discipline` | `reuse_for: result inset; detail panel; evaluation companion panel`
- `method-composites/immunostruct-results-iedb.png` | `role: style` | `density: medium` | `liked_traits: compact evaluation block; publication panel finish; crisp label discipline` | `reuse_for: result inset; detail panel; evaluation companion panel`
- `method-composites/immunostruct-schematic.png` | `role: both` | `density: medium` | `liked_traits: clean method schematic; modular decomposition; readable scientific cartoon` | `reuse_for: method composite; system schematic; architecture detail`
- `method-composites/rnagenscape-schematic.png` | `role: both` | `density: medium` | `liked_traits: clean method schematic; modular decomposition; domain-aware scientific figure` | `reuse_for: method composite; domain workflow; system schematic`

## Result Insets And Detail Panels

Use these mostly as companion panels or style donors, not as the default target
for `figure-prompt-builder`.

- `results-and-detail-panels/bars-ablation-cancer.png` | `role: style` | `density: medium` | `liked_traits: publication bar styling; grouped comparison; compact value communication` | `reuse_for: ablation panel; benchmark comparison; result inset`
- `results-and-detail-panels/bars-comparison-iedb.png` | `role: style` | `density: medium` | `liked_traits: publication bar styling; grouped comparison; compact value communication` | `reuse_for: comparison panel; benchmark figure; result inset`
- `results-and-detail-panels/composition-heatmap.png` | `role: style` | `density: medium` | `liked_traits: heatmap finish; matrix readability; dense detail panel discipline` | `reuse_for: heatmap panel; composition matrix; evidence panel`
- `results-and-detail-panels/correctness-by-category.png` | `role: style` | `density: medium` | `liked_traits: categorical comparison; clean result communication; readable grouping` | `reuse_for: detail panel; category comparison; evaluation inset`
- `results-and-detail-panels/rewriting.png` | `role: both` | `density: medium` | `liked_traits: task-specific result storytelling; compact panel logic; readable local narrative` | `reuse_for: result detail; task comparison; evaluation companion`
- `results-and-detail-panels/self-correction-math.png` | `role: both` | `density: medium` | `liked_traits: task-specific result storytelling; compact panel logic; readable local narrative` | `reuse_for: result detail; task comparison; evaluation companion`
- `results-and-detail-panels/trend-by-month.png` | `role: style` | `density: medium` | `liked_traits: temporal trend readability; clean line-chart finish; compact monitoring panel` | `reuse_for: trend inset; adoption curve; time-series evidence`

## Concept Motifs And Abstract Illustrations

- `concept-illustrations/idea.png` | `role: style` | `density: low` | `liked_traits: conceptual motif; low-density explanatory visual; clean negative space` | `reuse_for: motivation figure; concept callout; visual motif donor`
- `concept-illustrations/illustration.png` | `role: style` | `density: low` | `liked_traits: conceptual motif; clean illustrative language; quiet supporting visual` | `reuse_for: motivation figure; concept callout; visual motif donor`
- `concept-illustrations/manifold-holes.png` | `role: both` | `density: medium` | `liked_traits: geometric concept illustration; abstract scientific cartoon; explanatory topology cue` | `reuse_for: conceptual method figure; geometry explanation; theory illustration`
- `concept-illustrations/manifold.png` | `role: both` | `density: medium` | `liked_traits: geometric concept illustration; abstract scientific cartoon; explanatory topology cue` | `reuse_for: conceptual method figure; geometry explanation; theory illustration`

## Timelines, Gantt Views, And Work Plans

- `timeline-and-workplan/gantt-chart.pdf` | `role: structure` | `density: medium` | `liked_traits: gantt organization; milestone readability; workplan structure` | `reuse_for: project timeline; management plan; milestone figure`
- `timeline-and-workplan/gantt.pdf` | `role: structure` | `density: medium` | `liked_traits: gantt organization; milestone readability; workplan structure` | `reuse_for: project timeline; management plan; milestone figure`
- `timeline-and-workplan/timeline-extended-maine.pdf` | `role: both` | `density: high` | `liked_traits: extended schedule logic; coordination planning; detailed workplan` | `reuse_for: detailed timeline; multi-site coordination; management plan`
