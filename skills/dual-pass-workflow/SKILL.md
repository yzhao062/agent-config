---
name: dual-pass-workflow
description: Structure a task into a first pass and an optional second pass without replacing the domain skill. Use when Codex or Claude Code should collaborate on paper reviews, bug fixes, writing, website edits, research memos, or other tasks where one pass produces the main artifact and a later pass may check or refine it.
---

# Dual Pass Workflow

## Overview

Use this skill as an outer shell. Let the domain skill handle task-specific method, canonical outputs, and detailed verification. Use this skill to define a `first-pass` mode and, when needed, a `second-pass` mode.

## Step 1: Select The Domain Skill

- Identify the task-specific skill first. Examples: `cs-paper-review`, `cs-meta-review`, a bug-fix workflow, a frontend-edit skill, or a writing skill.
- Keep the domain skill as the source of truth for the main artifact and its verification.
- If the domain skill already has an `outputs/` folder or other task-local artifact layout, reuse it. Do not create a second top-level workflow folder unless the task has no obvious artifact directory.

## Step 2: Write The Task Packet

- Prefer `workflow.yaml` in the task root when the repo already has a task folder. If it is missing, infer the packet from the domain skill's standard layout before asking for more setup.
- For review folders in this repo, default to:
  - `task_root: reviews/<paper-id>/`
  - `primary_result: outputs/review.md`
  - `artifact_dir: outputs/`
  - `sources_of_truth: review.yaml, intake/requirements.md, intake/extra-text.md, intake/extracted-paper.md`
- If the task has no dedicated folder and no obvious standard layout, create `.agent/<task-id>/workflow.yaml`.
- Use the required fields in [references/contracts.md](references/contracts.md).
- Fill only the fields needed for a clean handoff: `task_type`, `goal`, `selected_skills`, `task_root`, `primary_result`, `artifact_dir`, `sources_of_truth`, `constraints`, `acceptance_criteria`, and `verification`.
- If the task is already packetized by a domain skill, keep the packet thin and point to the domain files instead of duplicating them.

## Step 3: Run `first-pass`

- The current agent is the default `first-pass` agent unless the user says otherwise.
- `first-pass` uses the domain skill and updates the primary result.
- `first-pass` may also write short workflow artifacts under the artifact directory:
  - `build.<agent>.md`
  - `handoff.<agent>.md`
- `build.<agent>.md` should record what changed, which files moved, and what verification actually ran.
- `handoff.<agent>.md` should contain: `what_i_did`, `assumptions`, `verification`, `open_issues`, and `suggested_audit_focus`.
- When the domain skill already produces evidence or reasoning artifacts, reference them instead of repeating their full contents.
- If the task is low risk or the first pass is already sufficient, stop here.

## Step 4: Run `second-pass` When Needed

- Use `second-pass` only when you want a real check, refinement, or adversarial review.
- The second-pass agent reads `workflow.yaml` when present and otherwise infers the packet from the task layout.
- If independence matters, let the second-pass agent write a short `precheck.<agent>.md` with expected strengths, risks, or failure modes before opening the draft.
- The second-pass agent then reads the primary result, the first-pass handoff when available, and the domain verification artifacts.
- The second-pass agent writes `audit.<agent>.md` with the categories from [references/task-mappings.md](references/task-mappings.md):
  - `factual_or_behavior_issue`
  - `unsupported_claim_or_assumption`
  - `missed_requirement`
  - `clarity_or_structure_issue`
- Default rule: audit first, rewrite second. Do not let the second pass collapse into unstructured polishing.
- If the issues are clear and safe to fix immediately, the second-pass agent may also reconcile the draft in the same turn.

## Step 5: Reconcile Only If `second-pass` Ran

- Reconcile is optional because `second-pass` is optional.
- If `second-pass` ran, update the primary result, keep or reject audit points explicitly, and rerun the domain verification steps.
- Write `reconcile.md` with three short sections: adopted changes, rejected points, and verification after reconcile.
- The primary result remains the canonical artifact. Workflow notes are supporting context only.

## Output Contract

- Use [references/contracts.md](references/contracts.md) to map the workflow onto an existing task layout.
- Use [references/task-mappings.md](references/task-mappings.md) to tune the audit emphasis by task type.
- Copy the templates under `assets/` only when the repo or skill does not already provide an equivalent file.
- Treat `workflow.yaml` as an override file, not a hard prerequisite, when the domain skill already defines a clear task folder layout.

## Stop And Ask

- Ask when there are multiple plausible primary results.
- Ask when the domain skill has no clear verification step and the task is high risk.
- Ask when the checker would need context that the packet does not record and cannot infer safely.
