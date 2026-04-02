# Intake Fields

## Core identity

- `case_id`: stable folder and tracking identifier
- `title`: short human-readable label
- `requester`: person asking for help
- `payee`: person who should be reimbursed
- `department`: USC unit involved

## Expense facts

- `expense_type`: travel, meal, supplies, registration, lodging, transport, other
- `business_purpose`: one or two sentences in plain language
- `purchase_date`
- `event_or_trip_dates`
- `total_amount`
- `currency`
- `merchant_or_vendor`

## Funding and approvals

- `funding_source`: chartstring, grant, project, or "unknown"
- `approver`
- `approval_status`
- `pre_approval_required`: yes, no, unknown

## Supporting evidence

- `receipt_present`
- `proof_of_payment_present`
- `itemization_present`
- `attendee_list_present`
- `agenda_or_invitation_present`
- `travel_support_present`

## Workflow control

- `target_submission_date`
- `current_status`
- `missing_items`
- `open_questions`
- `last_updated`

## Notes on usage

- Prefer `unknown` over leaving fields blank when the field was checked but not resolved.
- Separate raw facts from interpretation. For example, record "email from PI on 2026-03-10 says approved" as a fact; record "likely satisfies pre-approval" as an inference.
- Keep a short list of missing items that can be sent back to the requester without rewriting the full case.
