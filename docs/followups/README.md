# Followups

Open follow-up items for `agent-config`. Per-workstream files; status-by-glance below.

## Open

| File | Workstream | Items | Next trigger |
|---|---|---|---|
| [implement-review-auto](2026-05-16-implement-review-auto-followups.md) | `implement-review` skill | 3 open (1, 2, 5) + 2 done (3, 4) + 4 dismissed concerns | Bundled into next /implement-review work session |
| [aa-gh-5-pack-compose-staging-gc](2026-05-16-aa-gh-5-pack-compose-staging-gc.md) | composer / pack-lifecycle | Staging-dir GC after failed compose | aa v0.6.x patch |
| [aa-gh-1-context-bloat-remaining](2026-05-16-aa-gh-1-context-bloat-remaining.md) | pack-architecture | 2 remaining of 6: `agent-style-field` default, v1.0.0 `guard.py` extraction | agent-style slim pack ship (Item A); v1.0.0 (Item B) |

## Conventions

- One file per workstream. Filename: `YYYY-MM-DD-<workstream>-<subject>.md` where the date is when the item was promoted to followup, not the original deferral date.
- Per-item shape: Symptom / Root cause / Suggested approach / Trigger / Effort. See `implement-review-auto` for the reference.
- Cross-repo items (aa-side, agent-style-side): tracked here when the maintainer's working memory lives in `agent-config` even though the code change is in the sibling repo.
- Done items stay in the file with a "Completed YYYY-MM-DD" subsection (not deleted), so the next reader sees what shipped.
- Delete a file only when all items are closed AND a follow-up plan has subsumed any new concerns.

## What does NOT go here

- Tactical TODOs / FIXMEs with single-line context — leave them in code.
- Doc typos, version bumps, mechanical refactors.
- Items tracked in `agent-style/TODO.md` or aa-side `archive/plans/` — those stay in their own repo's tracker.
- Shipped work — moves to `archive/plans/` (gitignored) at release time.
