---
name: nsf-proposal-guardrail
description: Unified NSF proposal requirements, question-answering, and preflight checking for a single proposal repository. Use when a user has an NSF solicitation PDF/text and needs to (1) ingest and normalize proposal requirements, (2) ask drafting-time questions such as "do we need X?" or "where does this go?", or (3) run a pre-submission gap check against the current proposal files.
---

# NSF Proposal Guardrail

## Overview

Use this skill as the single entry point for NSF proposal compliance work
inside one proposal repository.

This skill is NSF-first. If the user provides another sponsor's governing call
text, FAQ, or related requirements under `<proposal-dir>/context/solicitation/`,
you can still use the same ingest and QA workflow, but treat the supplied call
materials as authoritative over generic NSF expectations.

The skill has three operating modes:

1. `ingest`: parse the solicitation and build a requirements baseline
2. `qa`: answer "is this required?" during drafting
3. `preflight`: check what is missing or risky before submission

Keep the raw solicitation inputs in
`<proposal-dir>/context/solicitation/` and write durable guardrail artifacts
under `<proposal-dir>/guardrail/`. Reserve `<proposal-dir>/out/` for temporary
build or compile outputs.

In a multi-proposal repo, use `<proposal-dir>` to mean one concrete proposal
workspace such as `proposals/nsf-25-533-fairos`.

## Repository Convention

For one proposal workspace, prefer this layout:

```text
<proposal-dir>/
  context/
    solicitation/
      solicitation.pdf
      solicitation.txt
      faq.txt
      pappg-excerpt.txt
    team/
    notes/
  guardrail/
  solicitation-requirements.json
  solicitation-qc.md
  solicitation-from-pdf.txt
  solicitation-source-check.json
  solicitation-source-check.md
```

Only `<proposal-dir>/context/solicitation/solicitation.txt` is required for
parsing. Keep `<proposal-dir>/context/solicitation/solicitation.pdf` nearby for
manual verification of tables, footnotes, or formatting details that raw text
may flatten.

## Mode 1: `ingest`

Use this mode when:

- a proposal starts
- the solicitation changes
- you need a fresh compliance baseline

When both PDF and text are available, start with a source cross-check:

```powershell
python skills\nsf-proposal-guardrail\scripts\verify_solicitation_sources.py --pdf proposals\nsf-25-533-fairos\context\solicitation\solicitation.pdf --txt proposals\nsf-25-533-fairos\context\solicitation\solicitation.txt --pdf-text-output proposals\nsf-25-533-fairos\guardrail\solicitation-from-pdf.txt --report-json proposals\nsf-25-533-fairos\guardrail\solicitation-source-check.json --report-md proposals\nsf-25-533-fairos\guardrail\solicitation-source-check.md
```

This step does three things:

1. extracts machine text from the PDF
2. checks high-value signals in both sources
3. surfaces TXT-only and PDF-only candidates for manual review

Then run the parser:

```powershell
python skills\nsf-proposal-guardrail\scripts\parse_solicitation_text.py --input proposals\nsf-25-533-fairos\context\solicitation\solicitation.txt --output proposals\nsf-25-533-fairos\guardrail\solicitation-requirements.json
```

If there are supporting sources:

```powershell
python skills\nsf-proposal-guardrail\scripts\parse_solicitation_text.py --input proposals\nsf-25-533-fairos\context\solicitation\solicitation.txt --input proposals\nsf-25-533-fairos\context\solicitation\faq.txt --input proposals\nsf-25-533-fairos\context\solicitation\pappg-excerpt.txt --output proposals\nsf-25-533-fairos\guardrail\solicitation-requirements.json
```

Then render the checklist:

```powershell
python skills\nsf-proposal-guardrail\scripts\render_qc_checklist.py --requirements proposals\nsf-25-533-fairos\guardrail\solicitation-requirements.json --proposal-dir proposals\nsf-25-533-fairos --output proposals\nsf-25-533-fairos\guardrail\solicitation-qc.md
```

The parser is heuristic. Treat the generated JSON and markdown as candidate baselines, not final truth.

Open [references/output-schema.md](references/output-schema.md) if you need field meanings.
Open [references/verification-rules.md](references/verification-rules.md) when resolving ambiguity.

## Mode 2: `qa`

Use this mode when the user asks questions such as:

- "Do we need X?"
- "Is this section required or optional?"
- "Where should this content go in the template?"
- "Is this a must-have, conditional item, or just a recommendation?"

Workflow:

1. Read `<proposal-dir>/guardrail/solicitation-requirements.json` and `<proposal-dir>/guardrail/solicitation-qc.md` if they exist.
2. If they are missing or stale relative to the current solicitation, run `ingest` first.
3. Answer with this exact shape:
   - verdict: `required`, `conditional`, `not required`, or `unclear`
   - evidence: short cited excerpt
   - location: where it belongs in the current proposal repository
   - status: whether the repository appears to already contain it

When mapping to the proposal repository, use [references/template-mapping.md](references/template-mapping.md).

## Mode 3: `preflight`

Use this mode immediately before submission or whenever the user asks:

- "What is still missing?"
- "What do we still need before submission?"
- "What is noncompliant?"
- "What should I double-check?"

Workflow:

1. Ensure `ingest` has been run on the current solicitation.
2. Compare the requirements artifacts against the repository contents.
3. Run a personnel consistency pass when the repository contains multiple
   investigator-owned sections:

```powershell
python skills\nsf-proposal-guardrail\scripts\check_personnel_consistency.py --proposal-dir proposals\nsf-25-533-fairos --output-json proposals\nsf-25-533-fairos\guardrail\personnel-consistency.json --output-md proposals\nsf-25-533-fairos\guardrail\personnel-consistency.md
```

4. Run a heading-style consistency pass for `\section{}`, `\subsection{}`, and
   `\subsubsection{}` titles:

```powershell
python skills\nsf-proposal-guardrail\scripts\check_heading_case.py --proposal-dir proposals\nsf-25-533-fairos --output-json proposals\nsf-25-533-fairos\guardrail\heading-case.json --output-md proposals\nsf-25-533-fairos\guardrail\heading-case.md
```

5. Include any PI/co-PI role, roster, or heading-style mismatches in the findings.
6. Also treat missing cleaned investigator profiles under
   `<proposal-dir>/context/team/<person>/profile.md` as a preflight gap, because
   those files are the preferred drafting-time source for team qualification.
7. Report findings in descending priority:
   - missing required items
   - present but likely noncompliant items
   - unresolved conditional items
   - recommended but non-blocking follow-ups

Treat `preflight` as a guardrail, not as a legal assertion. Surface ambiguity instead of pretending certainty.

## Answering Rules

- Prefer the solicitation text over informal summaries.
- Use PAPPG text only when the solicitation explicitly defers to it or when the user provides it as governing context.
- Keep `required`, `conditional`, and `prohibited` separate.
- Cite the source file and a short excerpt for non-obvious answers.
- Do not infer that a standard NSF section is required unless the solicitation or governing PAPPG material supports that conclusion.
- Do not silently discard low-confidence items; mark them for review.

## Bundled Resources

### `scripts/parse_solicitation_text.py`

Parse one or more raw text files and emit a structured JSON file with requirement candidates and supporting evidence.

### `scripts/verify_solicitation_sources.py`

Extract PDF text and compare it against `<proposal-dir>/context/solicitation/solicitation.txt`
before drafting-time use.

### `scripts/render_qc_checklist.py`

Render the parsed JSON into a markdown checklist and optionally map common NSF sections to files in the current workspace.

### `scripts/check_personnel_consistency.py`

Compare `30-collaborators.tex` against the active proposal `.tex` files and
flag PI/co-PI role mismatches, unknown personnel mentions, missing institution
mentions in `03-team-qualification.tex`, and missing cleaned team profiles
under `context/team/`.

### `scripts/check_heading_case.py`

Check whether sectioning commands in proposal `.tex` files follow the repo's
Title Case heading convention.

### `references/output-schema.md`

Describe the JSON shape used by both `qa` and `preflight`.

### `references/verification-rules.md`

Define source precedence, ambiguity-handling rules, and what to leave unresolved.

### `references/template-mapping.md`

Map common NSF proposal components onto the repository layout.
