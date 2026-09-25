# Native PowerPoint authoring and inspection

## Tool choice and source structure

Use the current presentation skill and its documented API when one is available. In an environment without it, an available library such as PptxGenJS or native PowerPoint automation can produce editable drawings. Check local capabilities before selecting a backend. Do not hard-code a user's cache paths, install a replacement runtime without need, or claim another application was tested because a PPTX package opens as ZIP.

A reproducible builder should separate the figure's labels, palette, coordinates, and primitives. Use a figure-sized canvas, semantic object names such as `LIVE_boundary` and `POST_event_3`, and groups that correspond to meaningful regions. Keep labels separately editable unless text belongs inside its node. An explicit source image may remain an image; a flattened diagram does not meet a native editability requirement.

Use attached connectors when moving a node should move its edges. Static curves or freeforms are appropriate for decorative arcs or relationships that do not need attachment. If a curve is only a freeform, do not describe it as an automatically rerouting connector.

For a hybrid figure, follow the picture boundary in [hybrid-figures.md](hybrid-figures.md). Apply one typography, stroke, dash, and arrowhead system across all regions, including links around imported objects. Route smooth curves with deliberate control points and clear endpoint tangents. Check clearance and contact with the visible object silhouette; a picture's rectangular bounds can differ substantially from that silhouette.

Choose an available font and verify actual rendered text. Numeric dimensions may be pixels, points, or EMUs depending on the API. In OOXML, 1 inch is 914400 EMUs; in a 96 DPI authoring canvas, 1 pixel is 9525 EMUs. Check the library's conventions. A figure scaled to one third of its slide width also scales its text to one third of its point size.

## Lessons from an actual native build

These were observed in September 2026 with the Artifact Tool deck-authoring runtime and native PowerPoint. Artifact Tool is one authoring runtime, not a required dependency of this skill. Recheck API-specific remedies against the installed version; they are diagnostics, not reasons to patch every deck.

| Symptom | What to inspect | Narrow remedy |
|---|---|---|
| Connector exists but is invisible | Z-order relative to panel backgrounds | Bring that connector forward or send the relevant background back. Keep intended masks above hidden content. |
| An overhead curved connector collapses onto an intermediate node in PowerPoint | The native export, not only the library preview | If that renderer cannot preserve the curve, use attached straight segments with transparent native routing anchors. Group the route and its nodes; verify attachments and clearance after moving them. |
| Arrow points backward | The exported arrowhead and actual start/end attachment | Fix the head/tail option that controls the intended endpoint. API naming can differ; inspect the rendered direction. |
| PowerPoint disables grouping | Group locks on the specific native shapes | Prefer the authoring API's unlock option. If the exporter wrote `a:spLocks noGrp="1"`, remove only that grouping restriction in a new draft copy, then revalidate. |
| COM rejects restoring a position | A `Single` property passed to a setter expecting `Double` | Preserve and restore as an explicit `[double]`, for example `[double]$originalLeft = $shape.Left`. |
| PowerPoint opens a path but export fails | Absolute export path and native Windows separators | Normalize export paths with .NET path utilities or `Join-Path`. |
| A picture shows the wrong crop | Source dimensions, image transform, and exported `a:srcRect` | Compute the crop from actual source pixels. Verify the native render; an authoring API may substitute a center crop. Repair only the affected crop if necessary. |
| A requested curve renders as straight segments | Exported path geometry, including `a:cubicBezTo` versus `a:lnTo` | Use explicit curve controls supported by the current API. Inspect and edit a control point in PowerPoint before claiming curve editability. |
| A dash style disappears after XML repair | Child ordering within the line properties | Follow OOXML schema order, including dash properties before arrow ends, then render again. |
| COM reports `80070520` in a sandbox | Whether the current runtime has an interactive logon session | Use the supported execution/approval mechanism if authorized. Otherwise export with the available renderer and disclose the missing native check. Do not disable controls or repeatedly retry unchanged calls. |

If XML repair is necessary, keep it confined to the known defect in a new file. Preserve relationships and other package parts. Run the active presentation workflow's package, layout, font, and import checks after the final repair. Validate the delivered bytes, not an earlier version.

## Native charts and their data

When data editing is part of the deliverable, create a native chart with a functioning data source. Editable lines and labels do not by themselves provide editable chart data. Check the series values, category labels, chart relationships, and embedded workbook when portable PowerPoint data editing is expected. A native chart count or a successful package import does not prove that the workbook exists or agrees with the plot.

In the observed Artifact Tool finalizer, `nativeChartTargetApplication: 'powerpoint'` accepted literal native charts but did not create a workbook even with `materializeLiteralChartWorkbooks: true`. For that version, `'portable'` together with `materializeLiteralChartWorkbooks: true` materialized and validated a workbook from complete literal data. Verify the installed API and the resulting package instead of relying on the option name. Preserve existing formulas and linked data sources; do not replace them with a literal snapshot merely to pass a check.

Inspect both literal series (`c:numLit`) and referenced series caches (`c:numRef/c:numCache`) when validating OOXML. Follow the chart's relationship to its workbook and the series' referenced cells; do not assume a particular embedded filename or worksheet.

### Saving can rewrite data representations

A native edit/restore test, and even a later geometry-only COM save, can reserialize `0.103` as `0.10299999999999999`. Numerical equality within tolerance and exact workbook/cache agreement are different checks. In the observed workflow, this changed representation failed the finalizer's precision check.

If reconciliation is needed, first establish the authoritative source for that chart: the original decimal values for a literal-data build, or its actual referenced worksheet for a workbook-backed chart. Confirm point counts, series/category identities, and numerical agreement within a justified tolerance before restoring the source representation. Never round every chart number or weaken validation to conceal a real discrepancy. If source and cache disagree materially, resolve that conflict before exporting.

For a layout-only edit, preserve the chart and embedded workbook parts byte-for-byte where practical. Otherwise recheck them after the save. Run the final package validator and export only after the last repair has succeeded.

### Compact chart labels need native inspection

Inspect after changing chart fonts: PowerPoint can wrap a short series name or split a numeric label across lines. On affected data labels in the observed COM workflow, `Format.TextFrame2.WordWrap = 0` and `Format.TextFrame2.AutoSize = 1` resolved wrapping. Apply label styling, then check and position the updated text bounds. These are targeted remedies, not blanket settings for every text box.

Set axis number formatting explicitly when its default obscures the intended precision. Inspect unwanted leader lines and marker contrast. Changing marker style reset marker colors in the observed build, so restore foreground/background colors when that occurs. A failed `PlotArea.InsideLeft` setter is a reason to inspect the supported chart-layout API, not to retry the same call repeatedly.

## Canvas and group geometry

For a schematic that should read as level, derive node centers, label baselines, and connection ports from shared horizontal and vertical guides. Equal bounding boxes alone do not align the visible artwork. Check each arrow's final segment and its contact with the node silhouette. Use orthogonal branches where they clarify the relationship, and matched radii with horizontal or vertical end tangents for symmetric loops. Preserve deliberate diagonals when the structure calls for them.

Inspect this geometry in the native export at manuscript width. In a September 2026 Stellar proposal revision, individually reasonable coordinates produced sloping venue links, uneven title baselines, and an asymmetric bot loop. Shared guides and equal-radius corners corrected the appearance while preserving the mechanism. Native connector tests had passed before this visual correction; editability and visual alignment were separate checks.

Align paired comparison rows by deriving both rows' node centers and their connection ports from the same guides. When one downstream node serves both rows, its outgoing edge can leave from their midpoint if that edge represents their joint result. Place a fan-out junction clear of the source node's silhouette; a technically attached route can still overprint that node's border. Inspect the rendered fork and arrowhead contact alongside endpoint attachment flags. A small geometry check can assert the intended row equality, axis alignment, and attachment with a declared tolerance. Visual inspection remains necessary.

Capture top-level object positions before changing the slide size. In the observed PowerPoint COM workflow, increasing `PageSetup.SlideWidth` recentered the existing groups by half the increase. Applying the planned panel shift afterward displaced the result twice and clipped its right edge. Compare before/after absolute positions rather than assuming a canvas change leaves objects fixed.

For a narrow spacing adjustment, a targeted OOXML edit can preserve chart data and other unaffected parts. Change the slide size and the intended panel transforms in a new copy, then compare package parts and render. Group `a:xfrm` uses both parent `off`/`ext` and child `chOff`/`chExt` coordinates; changing only one extent can unintentionally scale its children. Maintain the intended mapping and account for panel titles that live outside the moved group. Do not apply a case-specific pixel shift to every group.

After a wider canvas or changed group transform, inspect clipping and the effective font size at the document width. See [panels-and-results.md](panels-and-results.md) for the visual tradeoff between separation and scaling.

When deleting a footer or secondary strip, remove its separator, arrows and group definition as well as its text. Reduce canvas height to the remaining artwork with a modest margin, keeping canvas width, retained object coordinates and font sizes fixed. This preserves printed text size when the figure is inserted at the same document width. If the width or object scale changes, recalculate printed text size. Update the builder, expected canvas in validators, and export aspect ratio together. Native PDF export may quantize page dimensions slightly; use a small declared geometry tolerance and inspect the rendered bounds rather than requiring exact floating-point equality with the slide size.

## Native rendering helper

On Windows with PowerPoint installed, the bundled helper opens a single-slide PPTX read-only, exports PNG and PDF, and prints a JSON inventory. Supply absolute paths. It refuses to replace existing outputs and does not edit the input deck.

```powershell
& '<skill-root>/scripts/render_powerpoint.ps1' `
  -InputPptx '<absolute-path>/figure.pptx' `
  -OutputBase '<absolute-path>/exports/figure' `
  -PngWidth 2400
```

An optional `-ReportPath '<absolute-path>/build/native-render.json'` saves the inventory outside the deliverable folder. A normal run creates `<OutputBase>.png` and `<OutputBase>.pdf`. Use fresh output and report paths for a revision or failed partial export. Check each stage's exit status before using its files: a finalizer can write an artifact and then fail while writing its receipt. File existence alone is not success. The helper supports one figure slide deliberately; use a presentation renderer for a multi-slide deck.

The inventory records native shapes, text-bearing objects, connectors, charts, groups, pictures, and `otherObjects` for remaining object types such as tables or placeholders. A nonzero `otherObjects` count is not itself an error. The `charts` count reports native chart objects, not embedded workbooks or successful data editing. Native counts cannot prove that every required label is editable, that a connector follows a particular node, or that the content is correct.

## Check actual editing

On macOS, use the session's supported native-app control path. A connection timeout does not prove PowerPoint is absent: retry once, inspect app availability, and retry later if the user or environment resolves the connection. Keep native verification explicitly pending until it succeeds. Follow the current tool policy; do not switch to a prohibited automation API to bypass a connection problem.

After opening a disposable test deck, reacquire the active window and verify its title and file identity before editing. An old window handle can still target the master even when the copy appears in front. Record the master file's hash before and after the test. Discard the test copy after verifying the edits, and investigate any unexpected master change before delivery. When exporting on macOS, inspect the destination and export option: choose a local PDF path when available instead of assuming an option that uses an online service is local.

On a disposable copy of the final source, select and change representative text, change a meaningful shape property, and move a connected node. Confirm its connectors still attach to the correct endpoints. Inspect whether semantic groups can be moved together and ungrouped for detailed changes. Restore or discard the disposable copy; keep the final source unchanged by the test.

For scripted COM checks, name the exact objects being checked, verify the change, and restore it. Example for a known shape:

```powershell
[double]$originalLeft = $shape.Left
$shape.Left = $originalLeft + 2.0
if ([math]::Abs([double]$shape.Left - ($originalLeft + 2.0)) -gt 0.1) {
    throw 'Node movement did not take effect.'
}
$shape.Left = $originalLeft
```

This movement check alone does not establish connector behavior; inspect the relevant `ConnectorFormat` attachments and the moved rendering as well.

For a hybrid figure, also move an imported object independently and edit labels and links around it. Test a static native curve by changing and restoring a control point. Record this separately from attached-connector movement. Check that picture backgrounds and layer order do not hide nearby lines or labels.

For a native chart, also change and restore a known series value on the disposable copy and check the visible update. Test the workbook's Edit Data path when that behavior is required. Record the specific behavior tested; do not present a COM series test alone as proof that workbook editing was tested. Discard the test copy or validate any serialization changes before using it as a source.

Close only the deck opened by the task. Avoid terminating a PowerPoint process that may own the user's work. The helper exits the application only when no PowerPoint process was present at startup and no presentation remains open.

## Inspect the final export

Open the final PNG or rendered PDF. Look for text clipping, changed line breaks, missing masks, wrong arrows, weak contrast, and accidental overlap. Inspect at the intended print or web size as well as full resolution. For a document figure, font sizes and page area matter more than how large the slide looks in the editor.

Retain the native PPTX even when delivering a PDF or PNG. A PDF may be vector while some included assets remain raster; describe that accurately. A future author who changes the PPTX must regenerate the viewing export. Keep generation code when useful, but identify manual PPTX edits so regenerating does not erase them.

Native effects and vector exports are separate properties. In an observed PowerPoint export, editable panel shadows became raster images in the PDF while foreground text and geometry remained vector. When effects are used, inspect the actual PDF before describing it as wholly vector. Use a native effect in the PPTX when editability is required. If a destination requires an entirely vector figure, simplify or remove the effect and verify the export.

### Inspect Physical Text Size

The portable [inspect_figure_pdf.py](../scripts/inspect_figure_pdf.py) helper reads a PDF and prints JSON with its hash, scaled dimensions, smallest extractable text spans, and image occurrence count. It requires Python with the `pymupdf` package. Use the existing document runtime when it provides that dependency.

```bash
python '<skill-root>/scripts/inspect_figure_pdf.py' '/absolute/path/figure.pdf' --width-mm 77 --min-font-pt 7
```

The width and optional minimum above are examples, not venue rules. Supply the actual placement width and an appropriate threshold. For a multipage PDF, select a 1-based `--page`; the width then applies to that entire page, not an individual figure embedded within it. The calculation assumes uniform scaling without extra trimming. Inspect the compiled manuscript separately when LaTeX cropping, rotation, or placement differs from this assumption.

To measure the compiled page, pass its physical page width and `--page N`, for example `--width-mm 215.9` for US Letter. That report includes placement transforms already applied by LaTeX, but also includes body text and other figures. Reported sizes use PDF points (1/72 inch); a 10 pt TeX font can therefore read as about 9.963 PDF points. Inspect the intended figure's labels on the rendered page.

Exit 0 means the report was produced and any requested extractable-text threshold was met. Exit 1 means text falls below that threshold, or no text could be extracted to test it. Exit 2 reports invalid input or a missing dependency. The threshold allows 0.001 pt for PDF rounding. Raster or outlined labels are outside this check even when other text passes; hidden text can also appear in the report. The helper neither certifies legibility nor substitutes for native PowerPoint rendering and editing checks.
