---
name: usc-reimbursement
description: Standardize intake, evidence collection, precheck, packet assembly, and status tracking for USC reimbursement and expense-report workflows. Use when Codex needs to turn scattered USC reimbursement materials such as receipts, emails, approvals, travel details, and policy notes into a clean case folder, identify missing information, prepare a submission checklist, or maintain repeatable administrative workflows in this repo.
---

# USC Reimbursement

## Overview

Use this skill to convert an ad hoc reimbursement request into a tracked case with a consistent folder structure, intake record, precheck checklist, and submission notes.

Keep the workflow deterministic. Capture facts first, classify the case second, and only then prepare the packet or handoff notes.

The primary use case is intent-to-form support: the user tells Codex what they want to do, Codex decides whether a USC form is required, selects the correct form, and drafts the submission content.

## Quick Start

1. Run `skills/usc-reimbursement/scripts/new-case.ps1 -CaseId <id> -Title <short-title>`.
2. Fill the generated `intake.md` with the requester, business purpose, dates, amounts, and funding context.
3. Use `request-brief.md` to translate the user's plain-language goal into a form decision.
4. Use `form-draft.md` to draft the exact USC form content if a form is needed.
5. Use `checklist.md` to mark what is present, missing, or blocked.
6. Use `timeline.md` to preserve who said what and when.
5. Load the reference files only when needed:
   - Read `references/process-map.md` when deciding the processing path.
   - Read `references/intake-fields.md` when normalizing raw request details.
   - Read `references/policy-gaps.md` when USC-specific rules are still unknown or disputed.
   - Read `references/knowledge-ingestion.md` when new USC policy files or spreadsheets are added to the repo.
   - Read `../../knowledge/usc-reimbursement/normalized/common-knowledge.md` when the task depends on existing USC workflow knowledge already extracted from source files.
   - Read `../../knowledge/usc-reimbursement/normalized/account-reference-yue-zhao.md` when choosing or validating funding sources for Yue Zhao accounts.
   - Read `../../knowledge/usc-reimbursement/normalized/amazon-fellowship-rules.md` when an expense may charge `GF1028771` or another Amazon fellowship-linked account.
   - Read `../../knowledge/usc-reimbursement/normalized/form-field-map.md` when drafting or checking USC form inputs.
   - Read `../../knowledge/usc-reimbursement/normalized/policy-rules-from-forms.md` when checking deadlines, pre-approval triggers, or discretionary spending constraints.
   - Read `../../knowledge/usc-reimbursement/normalized/intent-to-form-playbook.md` when the user describes an activity in plain language and needs a form decision plus draft text.

## Workflow

### 1. Stabilize the request

Normalize the incoming request into one case folder. Do not leave source information scattered across chat, email, screenshots, and attachments.

Record:

- who spent the money
- who is requesting reimbursement
- business purpose
- event or travel dates
- total amount and currency
- any known line-item prices and their sources
- chartstring or funding source if known
- submission deadline or urgency
- current blockers

### 2. Classify the reimbursement path

Decide the path before checking documents. At minimum, distinguish:

- employee reimbursement vs non-employee or student reimbursement
- travel-related vs non-travel expense
- single purchase vs multi-line trip/event bundle
- reimbursement vs expense report correction vs missing receipt exception
- one-time approver question vs full packet preparation
- cs-order-form vs cs-reimbursement-form vs spending-request-approval-form

If the path is ambiguous, write the competing interpretations in `notes.md` and list what evidence would resolve the ambiguity.

When the user's input is just a description of planned activity, first answer:

- does any form need to be filed
- which exact form should be used
- which fields can already be drafted
- which facts are still missing

For estimates, tighten the draft as soon as reliable price evidence appears. If the user provides an official conference, vendor, or receipt-backed line item, replace generic `TBD` wording with:

- a concrete numeric total when all required components are known
- or a concrete partial estimate such as `registration fee + $121 poster printing` when only some line items are known

Do not keep `Estimated Cost` fully `TBD` once any material price component is confirmed.

For `Business Purpose/Justification` fields, prefer a concise natural paragraph that reads like a human submission. Include the equivalent of who, what, where, when, and why inside the prose when needed, but do not default to rigid label-style formatting.

### 3. Precheck the evidence

Verify that the packet can answer the basic reviewer questions:

- What was purchased?
- Why was it necessary for USC business?
- Who benefited?
- When did it happen?
- Was prior approval required, and is it documented?
- Is the amount mathematically consistent across receipts, reimbursement form, and ledger notes?

Flag missing items explicitly instead of using vague wording such as "needs follow-up".

### 4. Prepare the submission packet

Build a packet that a reviewer can process without re-reading the full email chain.

Summarize:

- case type
- business purpose
- expense breakdown
- exceptions or anomalies
- attached support
- open items

Keep factual notes separate from inferred notes. Label any inference.
For expense breakdowns, show the arithmetic explicitly when more than one cost component contributes to the estimate.

### 5. Track the handoff

Update `timeline.md` whenever the case changes state. Preserve:

- submission date
- recipient or system
- follow-up date
- decision or rejection reason
- reimbursement completion date

## Working Rules

- Prefer case IDs that sort well, such as `2026-03-trip-chen`.
- Keep one case folder per reimbursement packet, not per email thread.
- Preserve raw filenames inside `receipts/` and `approvals/`.
- Do not edit the original source facts in place after submission; append corrections in `notes.md` or `timeline.md`.
- Record unknown USC policy details in `references/policy-gaps.md` so the workflow improves over time.

## Resources

### scripts/

- `scripts/new-case.ps1`: create a standardized case folder from the bundled template

### references/

- `references/process-map.md`: generic reimbursement triage and packet-prep workflow
- `references/intake-fields.md`: canonical fields to capture from a reimbursement request
- `references/policy-gaps.md`: USC-specific rules that still need to be confirmed
- `references/knowledge-ingestion.md`: how to store and normalize USC source documents in this repo
- `../../knowledge/usc-reimbursement/normalized/common-knowledge.md`: normalized USC process knowledge extracted from local source files
- `../../knowledge/usc-reimbursement/normalized/account-reference-yue-zhao.md`: extracted funding and balance reference for Yue Zhao accounts
- `../../knowledge/usc-reimbursement/normalized/amazon-fellowship-rules.md`: fellowship-specific restrictions for Amazon ML Fellowship funding
- `../../knowledge/usc-reimbursement/normalized/form-field-map.md`: normalized form schemas for USC order, reimbursement, and spending-approval forms
- `../../knowledge/usc-reimbursement/normalized/policy-rules-from-forms.md`: deadlines, approval triggers, and FAQ-derived operating rules

### assets/

- `assets/case-template/`: markdown templates and storage folders copied into each case
