# Edit Boundaries

Use this reference when `nsf-proposal-composer` and
`nsf-thrust-refiner` both touch the numbered unit files.

## Default Contract

The repository uses visible LaTeX comment markers inside each numbered
`11-aim1.tex` through `14-aim4.tex` file:

- `% composer:sync-start`
- `% composer:sync-end`
- `% refiner:body-start`
- `% refiner:body-end`

These are plain comments. They do not affect compilation.

## Ownership Model

Default ownership is:

- `composer` owns the `composer:sync` region
- `thrust-refiner` owns the `refiner:body` region

This means:

- `composer` may refresh titles, top-level framing, and high-level overview text
- `composer` should not rewrite the detailed task or subtask body by default
- `thrust-refiner` may deeply revise task-level prose, literature grounding,
  technical measures, local evaluation hooks, and figure placeholders

## What Composer May Touch By Default

In a numbered unit file, `composer` may patch:

- the unit title
- the opening motivation or objective block
- the opening overview or proposed-direction block

Outside the unit files, `composer` may also patch:

- `00-project-description.tex` intro and pre-unit bridge
- `00-project-summary.tex`
- `20-evaluation.tex` when the high-level unit logic changed

## What Composer Must Not Touch By Default

Unless the user explicitly asks for a rewrite, `composer` must not:

- rewrite text inside `% refiner:body-start` ... `% refiner:body-end`
- collapse or reorder refined subtasks or tasks
- replace local literature grounding inserted by `thrust-refiner`
- remove visible `\todo{...}` markers that still represent unresolved issues

## Explicit Override

If the user says any of the following, `composer` may rewrite more aggressively:

- regenerate this thrust from scratch
- rewrite aim 2 completely
- overwrite thrust 3
- allow overwrite of protected body
- ignore protected body
- replace the current thrust structure

When using an override, say so clearly in the user update before editing.

The safest form is explicit and scoped, for example:

- `overwrite current Thrust 2`
- `rewrite Aim 3 from scratch`
- `allow overwrite of protected body in Thrust 1`

Do not treat a vague request for "polish" or "refresh" as overwrite
authorization.

## Refiner Behavior

`thrust-refiner` should usually focus on the `refiner:body` region.

If a refined body makes the opening sync region stale, `thrust-refiner` may:

- lightly patch the sync region for local coherence, or
- ask `composer` to do a follow-up sync pass

Do not let `thrust-refiner` silently change the whole proposal frame.
