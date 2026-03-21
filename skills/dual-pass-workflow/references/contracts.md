# Contracts

## Task Packet

Use `workflow.yaml` to declare the collaboration contract when you need explicit control. Keep it short.

Required fields:

- `task_type`
- `goal`
- `selected_skills`
- `task_root`
- `primary_result`
- `artifact_dir`
- `sources_of_truth`
- `constraints`
- `acceptance_criteria`
- `verification`

Recommended optional fields:

- `pass_mode`
- `builder_agent`
- `checker_agent`
- `notes`
- `workflow_artifacts`

Recommended shape:

```yaml
task_type: ""
goal: ""
selected_skills: []
pass_mode: ""
builder_agent: ""
checker_agent: ""
task_root: "."
primary_result: ""
artifact_dir: ""
sources_of_truth: []
constraints: []
acceptance_criteria: []
verification: []
workflow_artifacts:
  build_note: ""
  handoff_note: ""
  audit_note: ""
  reconcile_note: ""
notes: ""
```

## When `workflow.yaml` Is Optional

You do not need `workflow.yaml` when all of the following are already obvious from the task layout or domain skill:

- the task root
- the canonical output
- the artifact directory
- the source-of-truth files
- the verification steps

Example in this repo:

- a review folder already implies `outputs/review.md` as the canonical result
- `outputs/` is already the artifact directory
- `review.yaml` and the `intake/` files already define most of the packet

In that case, create workflow notes directly under the existing artifact directory and use `workflow.yaml` only if you want to pin agent roles, acceptance criteria, or non-default checks.

## Pass Modes

Preferred external language:

- `first-pass`: create the main result and stop if it is good enough
- `second-pass`: audit the first pass and optionally reconcile it

Internal files may still use names such as `build.<agent>.md`, `handoff.<agent>.md`, `audit.<agent>.md`, and `reconcile.md`.

## Output Contract

The domain skill keeps control of the canonical output. The workflow adds only supporting artifacts.

Required decisions:

- `task_root`: the folder that contains the task packet and task-local outputs
- `primary_result`: the canonical file or file set that represents the final answer
- `artifact_dir`: the directory for workflow notes
- `verification`: the checks that must run after build and after reconcile

Optional decision:

- `pass_mode`: `first-pass` or `second-pass`

Default artifact names:

- `workflow.yaml`
- `build.<agent>.md`
- `handoff.<agent>.md`
- `audit.<agent>.md`
- `reconcile.md`

## Integration Rule

Do not move the main output just to satisfy the workflow.

Examples:

- Review packet: keep `outputs/review.md` as canonical, add workflow notes under `outputs/`.
- Code task in a repo: keep the edited source files as canonical, add workflow notes under `.agent/<task-id>/` or an existing task-local artifact directory.
- Writing task: keep the requested draft file as canonical, add workflow notes next to it or under an existing `outputs/` directory.

## Builder Handoff Contract

`handoff.<agent>.md` should answer:

- What changed?
- Which assumptions might fail?
- What verification actually ran?
- What is still unresolved?
- What should the checker focus on first?

## Audit Contract

`audit.<agent>.md` should separate:

- factual or behavioral issues
- unsupported claims or assumptions
- missed requirements
- clarity or structure issues

For high-stakes tasks, order findings by severity.

If no second pass is used, `audit.<agent>.md` and `reconcile.md` are not required.
