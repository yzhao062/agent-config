# Verification Rules

## Source precedence

Use the strongest governing source available in this order unless the user tells you otherwise:

1. Current solicitation or program description
2. Official program-page instructions directly tied to that solicitation
3. Governing PAPPG text explicitly invoked by the solicitation
4. FAQ or Dear Colleague material that clarifies but does not override the solicitation
5. Prior proposals or local templates

Do not let prior-template habits override solicitation-specific instructions.

## Verification rules

- When both `<proposal-dir>/context/solicitation/solicitation.pdf` and `<proposal-dir>/context/solicitation/solicitation.txt` are available, cross-check them before relying on the text copy for drafting or QA.
- Prefer the manually curated text copy for parsing, but treat the PDF as the governing fallback when page limits, footnotes, or tabular requirements look inconsistent.
- Confirm all page-limit claims against the PDF if a table, list, or footnote may have been flattened in raw text.
- Confirm any rule with `confidence < 0.75` before treating it as binding.
- Keep `conditional` requirements conditional until you know the proposal type triggers them.
- Surface explicit prohibitions separately from missing requirements.
- If two sources conflict, report the conflict and identify which source appears controlling.
- If a rule is implied but not explicit, mark it as an open question instead of converting it into a requirement.

## Required reporting shape

When summarizing results, always separate:

- Must-have items
- Conditional items
- Prohibited items
- Open questions

This separation matters more than completeness theater. A shorter verified list is better than a long speculative one.
