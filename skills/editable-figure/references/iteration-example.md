# Lesson from a benchmark first figure

## Reduce reading load while keeping the scientific distinction

In a September 2026 CatchBench drafting session, the first editable figure combined three evidence states with corpus names, board counts, label-process information, method families, and scoring details. Its contents were mostly accurate, but the drawing behaved like a benchmark specification table. Readers had to work through the inventory before seeing the reason to use the benchmark.

The author's target was a first figure that, alongside the surrounding paper text, quickly made the benchmark understandable and useful. Completeness inside the image was secondary. An early lean revision retained three record illustrations and short audit questions. It contained about 34 English words, excluding step numbers; reducing the canvas from 1600 by 820 to 1600 by 480 cut height at the same width by about 41 percent. These describe an intermediate draft, not the accepted final composition or an ideal word budget.

A later requested Claude review helped combine the old figure's evidence structure with the lean draft's concrete questions. LIVE and POST traces aligned, while PRE remained a distinct configuration card because it used a separate corpus. A common heading identified the evaluated auditor. Nodes, dependency arcs, and masked future evidence carried the mechanism with minimal text.

Simplification preserved scope. The diagram did not supply an outcome label to a detection entrant, treat all three states as one empirical run, or present Gold cause attribution as a general natural-data claim. The question "Why?" was removed from the general POST heading because attribution belonged to a specific diagnostic board.

## Restore a small result for a different reading role

The reviewed schematic initially omitted the previous LIVE result inset because Results already discussed it. The author then explicitly requested side-by-side (a) and (b), with the explanatory panel much larger. That feedback changed the design: the schematic explained what the benchmark enables, and a compact result gave a numerical reason to care. Repetition in Results was not sufficient reason to exclude that useful introductory evidence.

The result values came from the authoritative board through the existing plotting parser. SWE-Gym gains were `[0.113, 0.103, 0.131, 0.141]`; tau-bench gains were `[0.000, -0.001, 0.020, 0.046]`, at 25/50/75/100 percent prefixes. These were differences of printed mean AUCs for the named methods. The quarter-prefix registered SWE-Gym paired effect was `0.101` under a different averaging procedure. The inset therefore made a descriptive claim and did not label its `0.113` point as that registered effect. Inferential details remained in Results.

Review recommendations were reconciled with sources and user intent. The requested editable PPTX format was retained despite a suggestion to use TikZ. Native export demonstrated searchable vector output. Earlier Claude reviews applied to the preceding schematic; the subsequent result-panel and spacing revisions were checked locally, without claiming a new Claude review of those versions.

## Separate panels with whitespace and check the paper

The first combined draft felt too crowded. Panel widths already had the requested hierarchy; the missing element was enough space between them. The accepted revision increased the nominal gutter from 27 to 91 design pixels, removed the vertical divider, and retained widths of approximately 1180 and 389 pixels, a 3.03:1 ratio.

The canvas widened from 1600 by 580 to 1664 by 580. At the manuscript's fixed 396 pt figure width, the smallest figure text became approximately 7.16 pt. This was inspected in the compiled paper, where Figure 1 remained on page 2 and the caption occupied five lines. These are case measurements, not minimum font sizes, mandatory ratios, or standard gutters.

The lesson is to allocate the gutter independently from panel widths and inspect visible labels, not only panel rectangles. Expanding the canvas trades more separation for smaller printed text; recalculate and view the actual page.

## Deliver editable data as well as editable shapes

The accepted master contained five groups, native diagram shapes and connectors, one native chart, one embedded data workbook, and no picture objects. The Figure 1 PDF contained no raster images. Representative text, node, and chart-series edits were tested in PowerPoint and restored; the final chart values and workbook passed validation. These checks did not claim a separate interactive Edit Data UI test.

PowerPoint saves exposed two non-obvious issues: resizing the canvas recentered existing groups, and even a geometry-only save reserialized chart numbers. The final spacing adjustment preserved chart/workbook parts byte-for-byte while changing the slide and panel geometry. The master PPTX and matching PDF/PNG were saved together in `figure/`; the builder, parsed data, and validation notes were retained beside the figure sources.

Transfer the editorial decision, not the exact layout: give readers a clear reason to care, use visual structure and selected evidence to support it, and retain the qualifiers needed for a correct interpretation. A proposal may pair a mechanism with preliminary evidence; a README may pair a workflow with an actual output. Once the content is accepted, keep spacing feedback a focused layout revision.
