# aa GH #5 — `pack-compose.staging-*` directories not garbage-collected

**Status**: open. **Source**: [yzhao062/anywhere-agents#5](https://github.com/yzhao062/anywhere-agents/issues/5) (filed 2026-05-05). **Target**: aa v0.6.x.

## Why this file exists

The bug is tracked on GitHub as the source of truth. This local file is a thin pointer so the maintainer's working memory (in `agent-config`) can find it without round-tripping through GitHub. Substantive design discussion belongs in the GH issue, not here.

## Summary

Failed composer runs leave behind `.agent-config/pack-compose.staging-<pid>/` directories. Subsequent `anywhere-agents` invocations emit `error: reconciliation surfaced blocking orphan staging dir(s); resolve manually` on every run even after wheel-side recovery succeeds. The project ends in a coherent state (exit 0); only the per-run stderr is noisy.

## Reproduction (from the GH issue)

Surfaced during the v0.6.0 pre-release sandbox on Windows, May 2026:

1. Maintainer project carried `.agent-config/pack-compose.staging-6304/` from a prior failed compose + three orphan `staged*.diff` files.
2. Bare `anywhere-agents` v0.6.0 emits the `reconciliation surfaced blocking orphan staging dir(s)` stderr on every run.
3. Wheel-side recovery succeeds (project enters coherent state), but the orphan staging dir is never removed.

## Suggested approach

Add a GC pass in `scripts/packs/reconciliation.py` (or in the `pack verify --fix` heal path) that removes `pack-compose.staging-*` directories older than a threshold (24 h is a safe starting point). Skip removal when the directory's PID has an associated live process to avoid yanking concurrent compose runs.

## When to pull in

Next aa v0.6.x patch release. Not a v0.6.0 regression (same orphan path existed in v0.5.x), so it does not gate v0.6.0.

## Effort estimate

Half a day per the issue: one file change + one repro test in `tests/test_packs_reconciliation.py` (aa repo).
