# Process Map

## Goal

Turn a reimbursement request into a repeatable sequence:

1. intake
2. classification
3. evidence check
4. packet assembly
5. submission tracking

## Intake questions

Collect these answers before policy interpretation:

- Who paid out of pocket?
- Is the payee the same person as the requester?
- What was purchased or reimbursed?
- What USC business purpose does it support?
- What dates matter: purchase, travel, event, submission deadline?
- What amount should be reimbursed?
- Is a chartstring, grant, or department funding source already known?
- Are approvals, agendas, attendee lists, or travel authorizations required?

## Classification decision points

Use these splits to choose the workflow:

- travel vs non-travel
- employee vs student vs guest/non-employee
- simple receipt reimbursement vs multi-document expense report
- fully documented request vs exception request

If more than one path looks plausible, record the ambiguity and do not silently choose one.

## Evidence standards

Most reimbursement packets need clear answers for:

- proof of payment
- itemized support
- business purpose
- approver evidence
- timing consistency
- account or project attribution

Common blockers:

- bank screenshot without itemized receipt
- receipt with no proof of payment
- meal expense without attendees or purpose
- travel expense without itinerary or conference context
- approval mentioned in email but not attached

## Packet assembly pattern

Prepare a concise reviewer summary:

- request type
- requester
- beneficiary
- business purpose
- line-item total
- supporting attachments
- missing items or exception statement

Keep the packet summary short enough to scan in under a minute.

## Status model

Use a small, explicit state machine:

- `draft`: facts still being collected
- `precheck`: support is being validated
- `ready`: packet can be submitted
- `submitted`: handed off to approver or system
- `blocked`: waiting on missing document or policy answer
- `resolved`: reimbursement complete or formally denied
