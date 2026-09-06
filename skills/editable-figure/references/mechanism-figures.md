# Make a mechanism easier to understand

Use this reference when a figure must explain how a method, intervention or evaluation works, especially when a draft has become a list of operations. It complements the first-figure case in [iteration-example.md](iteration-example.md).

## Build the smallest example that carries the distinction

Identify the original object, the operation, what changes, and how the output or target is determined. A minimal before/after example can carry more meaning than a longer abstract pipeline. Keep the unchanged original visible when it establishes the comparison or control. Use parallel examples for mutually exclusive interventions; merging them into one graph can imply both happen together.

Trace each drawn change to the implementation or other authoritative source for that exact setting. Check arrow direction, the object being edited, label construction, and any eligibility or selection rule. Evidence from a related version is insufficient when the illustrated version has a different mechanism. A small read-only check of the relevant functions can settle a concrete question without rerunning the full experiment.

For proposals, use the same before/after structure to explain a proposed operation and label its status. For READMEs, use an actual supported input/output transformation. Neither requires pretending that a schematic is an observed experiment.

## Translate terminology without losing the claim

Use a short verb and a concrete object for the main label. Keep the formal name as a secondary label when the reader needs to find it in the paper. Check the graphic, caption and adjacent prose together rather than demanding that every qualification appear inside the artwork.

The CatchBench Gold revision illustrates the difference:

| Draft wording | Revision and reason |
|---|---|
| `Use older information` | `Point to older step` describes the dependency-record edit without claiming the agent consumed different data during execution. |
| `Changed step: 3` | `True label: step 3`, with a caption explaining that the edit determines the label independently of a detector. |
| `Before the change` | `From the original` under `Steps to rank`, with the caption explaining that candidates are fixed from the original record. This clarifies selection rather than suggesting a timeline. |

Preserve short qualifiers when they constrain the example. In this case `Example: remove a link` matters: original steps 2 and 3 are both eligible for dropped grounding, but only step 3 is eligible for the illustrated stale-state edit. The source functions confirmed that distinction. The text also limits the candidate pool to the matched control and states that controlling eligibility does not eliminate every construction artifact. Neither the figure nor its caption turns an injected diagnostic into validated natural-failure evidence.

These are examples of distinctions to retain, not labels every future figure must use.

## Remove secondary content that does not explain enough

The initial figure included `Named-value v2 -> Edit one value -> Rebuild the links -> Record step + field`. This distinguished the second substrate, but it did not show which value changed or why its dependencies changed. Recording the target also overlapped with the label box above. The user chose to remove the strip and retain one caption sentence explaining that v2 edits an argument value and rebuilds dependencies from the edited record.

This decision focused the image on injection, label construction and candidate selection. The canvas changed from 1664 by 600 to 1664 by 490, reducing height by about 18 percent at the same manuscript width. The retained panels and fonts stayed fixed. Non-node labels fell from 60 to 48 words, and minimum printed text stayed approximately 7.62 pt at a 396 pt width. These measurements describe this case; they are not layout targets or a general minimum font size.

If value editing were the main contribution, the better next figure would show a specific value before and after the edit and the resulting link change. Generic operation lists do not substitute for that explanation. Apply this criterion to optional proposal workstreams and README internals too, while retaining pipelines that actually explain a dependency or user workflow.

## Use review and verification at the right scope

The requested Claude review received only the authorized image, caption, Section 4.3 and necessary code excerpts. It identified missing distinctions and a gap in the supplied file-level pool evidence. Adding the exact relevant excerpt closed the gap. Its warning about a two-column layout was conditional; the actual manuscript was single-column, so the existing full-textwidth float was appropriate.

Shorter wording can resolve a review finding without copying the reviewer's longer label. Include scientific substance and the author's reading-load goal in the reconciliation. The closing review inspected the then-current image; the later user-requested strip removal was verified locally and recorded as a subsequent version. It did not require another broad review.

Native PowerPoint inspection found a curved edge that collapsed onto the middle node despite looking correct in the library preview. The fix used attached segments and transparent routing anchors; see [native-powerpoint.md](native-powerpoint.md). Editing/restoring a label and moving/restoring a connected node tested behavior separately from package validity and vector PDF export.

Finally, update the caption in its canonical place and all figure exports, then render or compile the document and inspect the actual page. If other figures changed during the work, preserve them and distinguish their resulting page reflow from a defect in this figure. Report checks against the current artifact; keep earlier reviews and measurements as dated evidence.

Case evidence: `papers/iclr-2027-auditablebench/figure-spec/gold-mechanism-vet/` and `figure-src/gold-mechanism/` in `internal-writing`, 2026-09-05. The guidance above is usable without those project files.
