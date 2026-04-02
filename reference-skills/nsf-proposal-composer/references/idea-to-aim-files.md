# Idea To Aim Files

Use this workflow when the user gives a core proposal concept and wants the
composer to generate the main aim files.

## Goal

Produce a coherent set of `template/11-aim1.tex` through `template/14-aim4.tex`
or the same files under one concrete proposal workspace such as
`proposals/nsf-25-533-fairos/`, following the repository's house style and
aligning with the proposal family.

## Step 1: Normalize The Idea

If an active proposal folder already exists, read the introduction and
overview-of-proposed-work paragraphs in `00-project-description.tex` first and
use them as the initial idea seed.

Reduce the user input to:

- one-sentence importance claim
- one-sentence problem statement
- 2-4 named gaps or challenges
- one-sentence proposed contribution
- target users, domains, or communities
- main technical or capability ingredients
- likely NSF family: `methodology-driven` or `ecosystem-building`

If the introduction jumps directly into methods, repair the architecture first:

1. importance
2. gaps
3. central project claim
4. candidate thrust chain

Visible citation `\todo{...}` markers are acceptable at this stage.

## Step 2: Decide The Major Units

### methodology-driven

Infer the count from the gap map first. Use 4 aims only when four genuinely
distinct research roles exist.

1. foundation, representation, data, uncertainty, or anomaly formulation
2. core method, model, or algorithmic advance
3. integration, control, decision support, external interaction, or deployment
4. cross-cutting multi-agent, human-in-the-loop, robustness, or meta-control
   layer

If the project should be leaner, merge the last two roles into a single final
integration aim.

### ecosystem-building

Infer the count from the gap map and the proposal progression first. Use 3
thrusts when a cleaner sequence exists and the apparent fourth unit is really
evaluation, adoption, or sustainability.

Common roles are:

1. core architecture, platform, or data/resource layer
2. interoperability, tooling, governance, or enabling methods
3. user-facing workflows, application deployment, or domain-facing capability
4. adoption, community, governance, or sustainability

If deployment and adoption are mainly validation layers, move them into
evaluation rather than forcing a fourth thrust.

## Step 3: Scaffold Before Prose

Use `scripts/configure_aim_files.py` when the user wants the files materialized.

If no active proposal folder exists yet, first create one with
`scripts/instantiate_proposal.py`.

Recommended command pattern:

```powershell
& 'C:\Users\yuezh\miniforge3\envs\py312\python.exe' `
  'skills\nsf-proposal-composer\scripts\configure_aim_files.py' `
  --family methodology-driven `
  --output-dir template `
  --overwrite-existing
```

This command:

- scaffolds the active aim files
- comments out unused aim slots in `template/00-project-description.tex`
- leaves the example aim files in place for collaborator reference while
  keeping their `\input` lines commented by default
- emits visible composer/refiner region markers so later sync passes can avoid
  overwriting refined task-level prose

## Step 4: Draft Titles And Logic

For each unit, decide:

- title
- which named gap it resolves
- family-specific role in the 4-unit progression
- role in the full proposal
- 2 core subtasks
- evaluation hook
- risk or dependency note

Do this before writing long paragraphs.

## Step 5: Draft The Files

Follow `references/house-style.md` and use 1-2 example anchors from the same
family in `examples/catalog.csv`.

When materializing or refreshing numbered unit files, preserve this default
boundary:

- `composer:sync` for high-level framing
- `refiner:body` for detailed task or subtask refinement

## Step 6: Refresh The Rest Of The Proposal

Once the aim files are in place:

- update `template/00-project-summary.tex`
- make the introduction promise the same units
- replace any stale bridge paragraphs between the intro and aim inputs if they
  still describe an older proposal topic or family
- connect `template/20-evaluation.tex` to the generated aims

When a concrete proposal workspace already exists under `proposals/`, apply the
same update sequence there instead of editing `template/`.
