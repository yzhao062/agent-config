# Position and concept paper overview figures

Use this reference when a paper's main contribution is a position, framework, taxonomy, or research agenda rather than a single implemented method. The first figure should make the paper's argument easier to reconstruct. It need not summarize every section.

## Compress the argument before the text

Start from the smallest claim graph that explains why the position follows. A useful graph often contains:

- a concrete carrier, such as an agent task, record, scientific object, or deployment setting;
- the necessary concepts and relationships, including any dependency or boundary central to the claim; and
- a consequence, diagnosis, decision, or unresolved case that gives those concepts a reason to matter.

These are semantic roles, not required panels or a fixed left-to-right layout. A paper may need a different structure. The test is whether a reader can trace the argument through visible objects and relations rather than recover it from a list of labels.

Avoid two opposite failures:

| Failure | What remains visible | What is lost |
|---|---|---|
| Taxonomy display | The names of the concepts | Why they belong together, how they constrain one another, and what follows from them |
| Poster-like minimalism | A polished contrast or slogan | The evidence or reasoning that makes the position informative |

A dense operational workflow can fail for a third reason: it may preserve the logic but bury it in field names, repeated annotations, and procedural detail. Reduce that reading load by replacing prose with object silhouettes, attached edges, containment, a small exception path, or a diagnostic output. Do not delete the few relations that let the reader explain what leads to what.

## Run a meaning checkpoint after simplification

Treat semantic density and text density as separate variables. A figure can contain few words and still carry a rich argument; it can also contain many correct words and explain very little.

After a substantial simplification, inspect the image without relying on the caption and ask:

1. Is the concrete setting or object identifiable?
2. Can the reader trace the central dependencies, intervention, or information flow?
3. What consequence or limitation does the figure show?
4. Are illustrative objects, proposed mechanisms, and measured evidence distinguishable?

If any answer is no, restore the missing object, relation, consequence, or claim boundary before polishing the layout. A cleaner canvas is not an improvement when it no longer explains the paper's position. Use the caption for qualifications and scope, but do not require it to reconstruct the entire claim graph.

When another model is requested, use the image-only first-read protocol in the skill's inspection step instead of relying on this self-check.

## Refine in semantic stages

Keep revisions ordered so visual polish does not reopen settled reasoning:

1. **Argument structure:** establish the claim graph, concrete carrier, and claim boundaries, using the manuscript's names and order for its central concepts.
2. **Content economy:** remove repeated prose and secondary detail while preserving the graph.
3. **Visual polish:** align corresponding edges and baselines, regularize padding, reclaim unused bands, and assign colors by semantic role.
4. **Navigation aids:** add compact numbering, markers, or section references only when they help a reader find the matching text. They can change label widths and heading hierarchy, so rerun the stage 3 alignment and text-bound checks afterward.

Use the skill's visual-only freeze-and-compare rule to keep alignment, footprint, and palette changes separate from semantic redesign. Recheck rendering and text bounds after reflow.

Assign colors by semantic role, starting from [default-palette.md](default-palette.md) unless the document has its own palette. Give each accent one meaning across the figure; when two different states share an accent, recolor one of them. Keep structural objects and headings neutral when coloring them would imply a category membership they do not have.

## Link the figure back to the paper carefully

When a framework has a stable set of central concepts, use consistent names, ordering, or small markers to make the mapping visible. A marker can connect a concept to a table, checklist, contribution, or later analysis without repeating that material in the figure. Do not add a marker for every subsection.

Section references are optional navigation aids with the limits described in the skill's design step. Numbers printed inside the artwork cannot follow a renumbered manuscript. When the destination is LaTeX, prefer carrying section references in the caption with `\ref`, and recheck any number printed in the figure after structural edits.

## Case note

For reference selection, follow [reference-search.md](reference-search.md). In the Auditable Agents case, AgentDojo supplied a concrete agent and tool setting, and an authenticated-delegation position paper supplied a focal-document hierarchy; no artwork was copied. The paper's own enterprise example, five dimensions, palette, and layout belong to that case and are not defaults.

Case evidence: `papers/aisummit-2026-auditable-agents/figure-src/audit-redraw-v1/` through `audit-redraw-v7/` in `internal-writing`, 2026-09-13. The guidance above is usable without those project files.
