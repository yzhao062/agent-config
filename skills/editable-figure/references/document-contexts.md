# Adapt the figure to its document

The invariant is the reader's decision, not a shared page template.

| Context | Reader should quickly understand | Strong visual content | Detail usually better elsewhere |
|---|---|---|---|
| Paper first figure | The problem, contribution, and why the work is useful or surprising | A concrete failure, a new evaluation question, a mechanism, or one verified result | Complete corpus lists, every metric, implementation parameters, repeated contribution bullets |
| Paper method figure | How the central mechanism works and which distinction is technically important | Named inputs, operations, constraints, outputs, and necessary dependencies | Boilerplate infrastructure, incidental class names, generic arrows between empty boxes |
| Proposal overview | Why the gap matters, how the proposed approach addresses it, and what successful work produces | Gap linked to mechanisms and outcomes, with essential dependencies or validation | Every work package, staffing detail, acronym, and schedule item |
| Proposal aim or timeline | Feasibility, logical dependency, or a concrete success criterion | The relevant aim's method and evaluation, or a schedule when timing is the actual question | Unrelated aims, speculative results presented as completed, repeated overview text |
| README hero or overview | Who the project helps, what it does, and what using it yields | An actual input/output example, user workflow, or screenshot of an existing feature | Installation flags, internal module lists, unsupported performance claims, tiny terminal text |

## Papers

Read the introduction around the figure callout. Allocate information across figure, caption, and surrounding prose as a unit. The figure need not restate the title, abstract, benchmark inventory, and methods table.

For a benchmark, ask what meaningful evaluation becomes possible. Coverage counts can support that point, but do not automatically make the figure persuasive. A method-family comparison needs supported results and compatible metrics. Separate data tracks must not be drawn as a matched experiment unless such pairing exists.

A large overview plus a compact result can make both the contribution and its quantitative evidence visible. Use [panels-and-results.md](panels-and-results.md) for hierarchy, whitespace, and statistical scope. A selected result can earn introductory space even if Results explains it again.

Keep scientific distinctions that affect interpretation: input versus target label, prediction versus ground truth, natural data versus injected diagnostics, observation versus intervention, and measured versus illustrative quantities. Remove decorative qualifiers, not essential scope.

Judge legibility at the final column or text width. Compute the scaled type size rather than relying on the font size in the PPTX. Inspect the actual manuscript when integrating; placement, caption length, and neighboring text change the space cost.

## Proposals

Read the relevant aims and, when provided, the solicitation's criteria. Make the intellectual connection between the problem, proposed mechanism, and expected outcome clear. A diagram of three aims becomes useful only when it explains why those aims belong together or how their outputs support the proposed result.

Use restrained labels such as "proposed" or "target" where they prevent anticipated outcomes from reading as achieved results. Distinguish preliminary evidence from planned experiments. Do not invent partner commitments, data access, milestones, or measured gains to strengthen the figure.

Aim numbers, validation milestones, and responsibilities belong in the figure when they resolve feasibility or integration. Keep them out of a motivation figure if they divert attention from the problem. Match the proposal's print context and page constraints; do not assume a full presentation slide can be pasted at readable size.

## GitHub READMEs

Read the opening paragraph, quick start, and actual supported behavior. Select one workflow or recognizable output that helps a visitor decide whether to keep reading or try the project. Build a visual example from genuine capabilities; label synthetic examples when they could be mistaken for measured output.

Choose a web display export and retain the PPTX as its editable source. Inspect at a typical README content width and on a narrow viewport. Labels must survive scaling. Use a background that remains legible in the intended light/dark context; verify transparency deliberately rather than assuming it helps.

A real screenshot may be a native image inside the figure. Surrounding callouts and workflow arrows can be editable without claiming that the screenshot's UI is editable. Avoid imitating controls that do not exist. Put installation instructions and detailed options in accessible Markdown, and supply alt text for the image.
