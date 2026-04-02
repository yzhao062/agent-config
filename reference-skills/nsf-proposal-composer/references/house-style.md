# House Style

Use this file when drafting core aim or thrust files for this repository.

## Dominant Formatting Pattern

The user's dominant proposal style is not a paper-style theorem narrative and
not a bullet-heavy memo. Prefer:

- one major unit per file
- bold lead-in labels instead of many low-level headings
- concise technical prose with citations in the background and gap paragraphs
- 2 major subtasks by default; add a 3rd only when the logic truly needs it
- local evaluation hooks inside the aim file, with the full evaluation plan
  staying in `template/20-evaluation.tex`
- 4 numbered core units by default, because that is the most common pattern in
  the user's example library and the blank template exposes 4 slots
- Title Case for `\section{}`, `\subsection{}`, and `\subsubsection{}` titles;
  capitalize major words and do not leave content words in sentence case

## methodology-driven Unit Style

Default unit label: `Aim`

Preferred order:

1. `\subsection{Aim N: ...}`
2. `\textbf{Objective and Motivation.}` or `\textbf{Motivation and Background.}`
3. one framing block such as `\textbf{Limitations of Prior Approaches.}` or
   `\textbf{Threat Model.}` when the call needs it
4. `\textbf{Proposed Research Direction.}`
5. `\subsubsection{Subtask N.1: ...}`
6. `\textbf{Problem.}` or a short transition sentence
7. `\textbf{Technical approach.}`
8. `\textbf{Integration handling.}`
9. `\subsubsection{Subtask N.2: ...}`
10. optional short blocks for evaluation, outcomes, and risk

Use this as the default even when the exact content differs by call.

## ecosystem-building Unit Style

Default unit label: `Thrust`

Preferred order:

1. `\subsection{Thrust N: ...}` or `Work Package N`
2. `\textbf{Motivation and Background.}`
3. `\textbf{Overview.}`
4. `\subsubsection{Task N.1: ...}`
5. `\textbf{Problem.}`
6. `\textbf{Method.}` or `\textbf{Technical and organizational plan.}`
7. `\subsubsection{Task N.2: ...}`
8. `\textbf{Problem.}`
9. `\textbf{Method.}`
10. `\textbf{Milestones and measurable outcomes.}`
11. `\textbf{Dependencies and sustainability path.}`

Even ecosystem units should still read like NSF research prose, not project
management notes.

## Content Conventions

- Do not make aims independent mini-projects. They must form a progression.
- Use specific, domain-bearing titles rather than generic titles like
  `Representation`, `Method`, or `Evaluation` alone.
- Mention downstream or upstream dependence explicitly when helpful.
- Put detailed schedules, broad evaluation tables, and collaboration mechanics
  in other files unless the aim needs a local hook.
- Use figures only when they compress significant logic; do not force one into
  every aim file.

## Default Counts

- `methodology-driven`: 4 aims by default
- `ecosystem-building`: 4 thrusts or work packages by default

Compress to 3 units only when the idea is materially simpler than the user's
usual proposal pattern.
