# Followups

Cross-repo backlog for the maintainer's source repos (ac, aa, ap, as), tracked here because the maintainer uses `agent-config` as the primary working directory. Each entry is a thin pointer to the source-of-truth tracker (GH issue, PLAN file, TODO.md entry, or in-line code TODO); this directory adds the cross-repo visibility layer.

## Open by repo

### `agent-config` (ac)

| File | Workstream | Status |
|---|---|---|
| [implement-review-auto](2026-05-16-implement-review-auto-followups.md) | `implement-review` skill | Closed 2026-05-16 (6 items + 4 dismissed concerns); kept for historical reference |

### `anywhere-agents` (aa)

| File | Workstream | Items | Next trigger |
|---|---|---|---|
| [aa-gh-5-pack-compose-staging-gc](2026-05-16-aa-gh-5-pack-compose-staging-gc.md) | composer / pack-lifecycle | Staging-dir GC after failed compose | aa v0.6.x patch |
| [aa-gh-1-context-bloat-remaining](2026-05-16-aa-gh-1-context-bloat-remaining.md) | pack-architecture | 2 of 6: `agent-style-field` default switch + v1.0.0 `guard.py` extraction | agent-style slim pack ship (Item A); v1.0.0 (Item B) |

### `agent-pack` (ap)

| File | Workstream | Items | Next trigger |
|---|---|---|---|
| [ap-pack-yaml-tag-strategy](2026-05-16-ap-pack-yaml-tag-strategy.md) | pack-distribution | `pack.yaml` self-refs `ref: main` despite v0.1.0 ship (3 entries) | Next ap release prep or aa-side bundled-default discussion |

### `agent-style` (as)

| File | Workstream | Items | Next trigger |
|---|---|---|---|
| [as-awesome-list-submissions](2026-05-16-as-awesome-list-submissions.md) | distribution / public-listing | 2 drafted (awesome-claude-code, awesome-copilot) + 3 queued | Human form-submission window (~30 min) |
| [as-pep639-license-migration](2026-05-16-as-pep639-license-migration.md) | PyPI packaging | Migrate to PEP 639 license metadata before setuptools cliff | **2027-02-18 hard deadline** |

## Conventions

- One file per workstream. Filename: `YYYY-MM-DD-<workstream>-<subject>.md` where the date is when the item was promoted to followup, not the original deferral date.
- For cross-repo items where the source-of-truth lives in a sibling repo, the file is a thin pointer (~25-40 lines) covering: Symptom, Suggested approach, Trigger, Effort, and a Cross-references block linking the source files / GH issues. Substantive design discussion belongs in the source-of-truth tracker, not here.
- For self-contained ac items, the file may carry the full design content (see `implement-review-auto`).
- Done items stay in the file with a "Completed YYYY-MM-DD" subsection (not deleted), so the next reader sees what shipped.
- Delete a file only when all items are closed AND a follow-up plan has subsumed any new concerns. The `implement-review-auto` file stays as historical reference even though all 6 items are closed, because the doctrine it carries (Phase 2.5, FP-tuning, etc.) is load-bearing for future implement-review work.

## What does NOT go here

- Tactical TODOs / FIXMEs with single-line context: leave them in code.
- Doc typos, version bumps, mechanical refactors.
- Items already well-tracked in a sibling repo's `TODO.md` with no cross-repo touch and no hard external deadline. Examples (currently in `agent-style/TODO.md`, not mirrored here): Copilot instruction-loading verification (15-min verification plan), Hero figure paper row polish (tactical re-render).
- Business / vendor outreach via GitHub issues (e.g., aa#4 WisePick pitch, as#5 MFKVault pitch): decide on the issue page, not in working memory.
- Shipped work: moves to `archive/plans/` (gitignored) at release time.
