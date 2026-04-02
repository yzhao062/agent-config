# Knowledge Ingestion

## Goal

Keep reusable USC reimbursement knowledge separate from individual reimbursement cases.

Store source materials under `knowledge/usc-reimbursement/` and case-specific materials under `cases/<case-id>/`.

## Folder usage

- `knowledge/usc-reimbursement/raw/`: original files exactly as received
- `knowledge/usc-reimbursement/normalized/`: cleaned text extracts, summaries, or table transcriptions
- `knowledge/usc-reimbursement/index.md`: source registry and processing notes

## Source types

Typical inputs:

- PDF policy documents
- screenshots of process diagrams
- plain text or copied email guidance
- Excel trackers or checklists
- Word or exported form templates

## Ingestion rules

- Preserve original filenames inside `raw/` unless they are unusable.
- Prefix ambiguous filenames with a date or short source tag.
- Do not overwrite prior source files silently; add a version suffix if needed.
- Record each new file in `index.md` with what it covers and whether it is authoritative.
- If a spreadsheet contains multiple tabs, note which tabs matter before summarizing it.

## Normalization pattern

For each new authoritative source:

1. Place the original file in `raw/`.
2. Add one row or entry in `index.md`.
3. Create a matching note in `normalized/` when the source is large, image-based, or hard to query directly.
4. Summarize only the reimbursement-relevant sections:
   - triggers
   - required approvals
   - required documents
   - deadlines
   - exceptions
   - department-specific variants

## Priority order

If sources conflict, prefer:

1. current department guidance
2. current USC central policy
3. working examples from completed reimbursements
4. informal email guidance

When the source order is unclear, record the conflict instead of guessing.
