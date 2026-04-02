# Output Schema

The parser produces a JSON document with four top-level keys:

- `source_files`: raw text inputs used for extraction
- `metadata`: solicitation identifiers and other candidate metadata
- `requirements`: categorized rule candidates
- `open_questions`: unresolved items that require manual confirmation
- `notes`: warnings about heuristic extraction

## `metadata`

Expected fields:

- `primary_solicitation_number`
- `program_title_candidates`
- `solicitation_numbers`
- `replaced_solicitation_numbers`
- `referenced_solicitation_numbers`
- `deadline_candidates`
- `nsf_unit_candidates`

These are candidate values, not guaranteed truths. Confirm them against the PDF or official page before relying on them.

## `requirements`

Buckets:

- `required_documents`
- `conditional_documents`
- `prohibited_or_restricted`
- `page_limits`
- `review_criteria`
- `eligibility_and_limits`
- `budget_and_duration`
- `submission_and_formatting`
- `program_specific_requirements`

Each requirement item contains:

- `requirement`: the normalized text block that triggered extraction
- `source_file`: file path that supplied the evidence
- `heading`: nearest heading candidate, if detected
- `document`: normalized document name when one was detected
- `classification`: `required`, `conditional`, `prohibited`, or `informational`
- `confidence`: heuristic confidence score between `0` and `1`
- `signals`: matched rule/document signals
- `evidence_excerpt`: shortened source excerpt for quick review
- `category`: output bucket

## How to use the output

Use the JSON as a review scaffold:

1. Confirm high-confidence items first.
2. Promote only verified items into a final proposal checklist.
3. Keep low-confidence or conflicting items in `open_questions`.
4. Distinguish program-specific requirements from generic NSF/PAPPG defaults.
