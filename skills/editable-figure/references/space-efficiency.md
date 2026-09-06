# Space efficiency in document figures

Use this reference when a figure leaves broad unused areas, one element forces an oversized canvas, or a paper/proposal layout needs a smaller footprint. The same principle applies to overview diagrams, mechanisms, plots, timelines, screenshots with callouts, and README visuals: preserve the information and reading hierarchy while avoiding space with no useful role. The preferred footprint depends on the destination, not the authoring application's slide default.

## Diagnose the source of the space cost

Inspect at the intended document width. Mark the actual occupied bounds of each panel, not only text-box bounds or background shapes. Check for unused strips beside short labels, empty rows after a deletion, loose inter-panel gaps, and long footers that set the width for otherwise narrow content. A footer spanning the canvas can make an overall crop look tight while hiding a large empty region above it.

Then inspect the document. Include the caption, float margins, wrapped line count, paragraph spacing, and nearby headings. Saving space inside the drawing does not necessarily save space on the page. A compact wrapfigure can still create an extra caption line, leave a heading at half width, or move a later float onto another page.

## Reflow before reducing type

- Narrow or shorten the element that unnecessarily determines the canvas size. Keep all scientifically necessary labels and distinctions.
- Rearrange branches or method groups to fit the intended slot. Preserve their relationships; reflow must not introduce a causal progression, an ordering, or a one-to-one assignment absent from the source.
- Reduce the resulting canvas width or height. Keep retained content and physical type size stable where possible.
- Preserve gutters that separate panels and clearances around labels, axes, and arrows. Useful breathing room serves comprehension; broad empty areas that do not do so should be reclaimed.

Do not fill space with decorative objects, repeated conclusions, unsupported numbers, or extra detail. Do not stretch objects disproportionately or shrink all labels merely to fit an inherited aspect ratio. Uniform pixel coverage is not the objective.

## Return the space to the document

If source width changes from W_old to W_new, keeping placed_width / source_width approximately constant preserves physical type size. For example, reducing an 820 px figure at 50 percent text width to 690 px at about 42 percent text width keeps the label scale almost unchanged. The freed width becomes prose width.

If the placed width is left unchanged after cropping, the content becomes larger and the placed figure can become taller. That can be appropriate for readability, but it is not the same as reducing page cost.

Recompile or render the current document. Inspect the full figure plus caption and the text wrapping beside it. Check the transition back to full-width text and subsequent section headings. Report any material pagination effect without promising that wrapfigure placement or cropping guarantees a lower page count.

## CatchBench example

In the initial wrap version, the upper timeline's longest label ended near x=657 on an 820 px canvas. Wide method bands and a footer extended across the canvas, leaving a visible empty strip beside the timeline. The correction narrowed the canvas to 690 px and reflowed the method bands. Dates, sketches, works, and method names were retained. Reducing the LaTeX wrap width from 0.50 to 0.42 of the text block kept the original label scale and returned the removed strip to neighboring prose.

The reusable lesson is to evaluate each panel and the final document together. These dimensions illustrate one repair; they are not default aspect ratios or mandatory whitespace thresholds for other figures.
