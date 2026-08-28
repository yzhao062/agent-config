# Followups

Cross-repo backlog for the maintainer's source repos (ac, aa, ap, as), tracked here because the maintainer uses `agent-config` as the primary working directory. Each entry is a thin pointer to the source-of-truth tracker (GH issue, PLAN file, TODO.md entry, or in-line code TODO); this directory adds the cross-repo visibility layer.

## Open by repo

### `agent-config` (ac)

| File | Workstream | Status |
|---|---|---|
| [implement-review-auto](2026-05-16-implement-review-auto-followups.md) | `implement-review` skill | Closed 2026-05-16 (6 items + 4 dismissed concerns); kept for historical reference |
| [agent-fungibility-refactor-plan](2026-05-16-agent-fungibility-refactor-plan.md) | cross-vendor resilience (Claude / Codex) | Open: 9 phases. Phase 0 done local-only (2026-05-16); Phase 0.5 promoted principle to shared `AGENTS.md` (shipped v0.7.0, 2026-05-19); Phases 1-7 open; Phase 8 deferred. ~6-9 days critical path remaining. |
| [grok-fourth-reviewer-evaluation](2026-08-22-grok-fourth-reviewer-evaluation.md) | `implement-review` reviewer backends / vendor selection | **Decided 2026-08-22: do not add a Grok backend.** Chinese-language decision record. Two-round cross-vendor investigation (6 + 2 prun units, 21-agent Workflow). Blockers: USC policy + NSF reviewer rules for the academic half; no capability evidence for the code half; Grok's 2026-07 repository-transfer incident plus the absence of its built-in OS sandbox on Windows (note: the current Codex default also runs without an OS boundary, so this is a Grok data-governance concern rather than a Codex-vs-Grok gap); 52-78 eng-hours + 16-32/yr maintenance on a public distribution surface. Carries the measured workload baseline, the two-meter billing model, the per-model `api_key` routing design, and the engineering estimate for whenever this is reproposed. Open thread: the §11.3 experiment (one `xhigh` pass vs three independent `xhigh` passes aggregated) needs no new vendor and tests the repeated-review evidence without touching the `SKILL.md:104` effort floor. §10.3 (appended after the review rounds, so weaker evidence) evaluates Cursor Individual Ultra and rejects it for the same double-paying reason, but notes Cursor Pro at $20 is the cheapest legitimate route to trying Grok at all. |

### `anywhere-agents` (aa)

| File | Workstream | Items | Next trigger |
|---|---|---|---|
| [aa-gh-5-pack-compose-staging-gc](2026-05-16-aa-gh-5-pack-compose-staging-gc.md) | composer / pack-lifecycle | Staging-dir GC after failed compose | aa v0.6.x patch |
| [aa-gh-1-context-bloat-remaining](2026-05-16-aa-gh-1-context-bloat-remaining.md) | pack-architecture / AGENTS.md size budget | aa#1 effectively closed (5 of 6 shipped). File rewritten 2026-05-17 as optimization plan: Phase 0 growth-guard CI (mandatory) → Lever 1 aa compact (against aa/AGENTS.md, NOT ac) → Lever 2 **agent-pack slim variants** (rewritten 2026-05-17 from on-demand-skill design that conflicted with pack-architecture Round 2 decision) → Lever 3 deferred → Item B v1.0.0 `guard.py` extract | **Phase 0 ✅ shipped (aa `38c57aa`); Phase 1.A ✅ shipped 2026-05-17 (aa `ba221f7`, ac `5638585`; -4 KB / CC headroom 8.4 → 9.8 KB); Phase 1.B/1.C dormant; Phase 2 redirected to agent-pack `-field` / `-lite` variants per `pack-architecture.md:914`; Item B future** |
| [aa-v0.7.0-noise-audit-fungibility-bootstrap-preflight](2026-05-18-aa-v0.7.0-noise-audit-fungibility-bootstrap-preflight.md) | guard.py noise-audit (Round 6) + fungibility Phase 0.5 + bootstrap git preflight | Three-slice v0.7.0 plan: (A) `Suggested rewrite:` deny messages, narrow `AGENT_STYLE_HOOK` / `AGENT_COMPOUND_CD_HOOK` escape envs (destructive git/gh always-on), composer noise-budget gate on third-party `reroute_hint`; (B) promote fungibility principle from `CLAUDE.local.md` to shared `AGENTS.md`; (C) bootstrap `git --version >= 2.25` preflight with platform-specific install messages | **Shipped v0.7.0 on 2026-05-19** (ac `f270eea`+`158e140`, aa `ae645f6`+tag `v0.7.0`; PyPI manual upload, npm via the new OIDC `publish.yml`). Plan converged 4 rounds, implementation reviewed 5+3 rounds, all 5 release workflows green. |
| [aa-publish-workflow-oidc](2026-05-20-aa-publish-workflow-oidc.md) | release pipeline | `.github/workflows/publish.yml` on release-published, PyPI + npm via Trusted Publishing OIDC. Kills the manual `twine upload` + `npm publish` chore and the token-rotation pain that blocked the v0.7.0 npm step. | **Implemented 2026-05-20** (aa `be6ce22`+`fd07356` workflow, `777da77` RELEASING.md). npm shipped on OIDC (automation token hit E403 under the 2FA-on-publish policy); PyPI OIDC publisher configured, `skip-existing` covers the manually-uploaded v0.7.0; v0.7.1+ fully automatic. |
| [stopped-task-false-failure-and-noop-compose](2026-08-21-stopped-task-false-failure-and-noop-compose.md) | `implement-review` intake + composer transaction | Four findings from one consumer sweep: (1) a harness `killed` task notification read as a failed review, 6 measured false stops across 2 repos; (2) compose replaces 86 byte-identical files every session and dies on one of them with `WinError 5`; (3) the banner's pack-gap check ignores bundled defaults and fires in 26 of 27 consumers; (4) `pack verify` never peels annotated tags, so a phantom update can never clear | **(1) fixed 2026-08-21** (`await-review.py` + SKILL.md contract + tests, mirrored to aa and the wheel). **(2) fixed 2026-08-28** (composer identical-write skip + private-copy re-exec for all three long-running prun Bash entry points + the bootstrap helper half; closes aa#43 and aa#44; split out aa#47 and aa#48). (3), (4) open; each carries its measurement and a proposed shape in the note. |
| [windows-rename-failure-class-pending-changelog](2026-08-28-windows-rename-failure-class-pending-changelog.md) | release record | CHANGELOG entry for the six commits that close aa#43 and aa#44, plus the two-platform verification table | next release after 0.7.18 |

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
