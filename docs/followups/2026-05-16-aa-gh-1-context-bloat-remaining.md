# aa GH #1 follow-on: AGENTS.md size optimization plan

**Status**: aa#1 trajectory effectively closed (5 of 6 milestones shipped). Item B remains future work. This plan replaces the prior trajectory tracker, which was stale on three axes (wrong Item-A naming, wrong as issue cite, unreachable 40 KB projection).
**Source**: [yzhao062/anywhere-agents#1](https://github.com/yzhao062/anywhere-agents/issues/1).

## Why this file replaces the prior tracker

Verified 2026-05-17 across ac / aa / as / ap plus a real consumer (internal-writing):

- aa#1 Items 1, 3, 4, A all shipped. Item A landed via as v0.3.4 `docs/rule-pack-compact.md` (issue [as#6](https://github.com/yzhao062/agent-style/issues/6), not as#4 as the prior tracker claimed) and aa v0.5.7 manifest flip (`bootstrap/packs.yaml:24` `from: docs/rule-pack-compact.md`).
- Real outcome of the slim-as flip: fresh consumer CLAUDE.md dropped from ~125 KB to ~70 KB (~45% cut). The prior tracker's "drop under the 40 KB warning threshold" projection was unreachable: even with a 0-byte agent-style, aa baseline alone is 36.3 KB, already 91% of the 40 KB budget.
- Item B (v1.0.0 `guard.py` → `agent-behave`) is unchanged and carries forward to Phase 4 of this plan.
- New gap exposed by the measurement: the dominant bloat source is now the aa baseline AGENTS.md itself plus agent-pack passive packs, not agent-style. That is what Phases 0-2 of this plan address.

## Verified composition (internal-writing, fetched 2026-05-14, measured 2026-05-17)

| Segment | Source | KB | % of 72 KB |
|---|---|---|---|
| aa baseline AGENTS.md | aa/AGENTS.md (upstream; **NOT** ac/AGENTS.md, which is 43.9 KB and includes maintainer-only sections like Submodule Workflow + Overleaf merge protocol) | 36.3 | 50% |
| `agent-style` passive block | as v0.3.5 `docs/rule-pack-compact.md` | 20.7 | 29% |
| `profile` passive block | agent-pack `docs/rule-pack.md` | 6.8 | 9% |
| `paper-workflow` passive block | agent-pack `docs/paper-workflow.md` | 8.0 | 11% |
| composer marker overhead | block comments + spacing | 0.3 | <1% |
| **Total AGENTS.md** | | **72.1** | |
| **Generated CLAUDE.md** | per-agent tag strip applied | **68.3** | (matches the 65.8 k chars CC warning observed) |

## Target selection (default locked for Phase 1)

CC v2.1.143 fires the soft warning at 40 KB CLAUDE.md. Three target tiers; **Pragmatic is the default for Phase 1 — override only if you choose Defensive or Aggressive before implementation starts.**

| Target | Required levers | Note |
|---|---|---|
| Aggressive: ≤ 40 KB on every consumer shape | Phase 0 + Lever 1 + Lever 2 | Lever 1 alone hits this for `agent-style`-only consumers; paper consumers (profile + paper-workflow loaded) also need Lever 2 |
| **Pragmatic: ≤ 50 KB (default)** | Phase 0 + Lever 1 | Lever 1 alone clears 50 KB for every common consumer shape; agent-pack stays opt-in cost |
| Defensive: hold ≤ 75 KB ceiling | Phase 0 only | Accepts current size as steady-state; growth-guard CI prevents drift |

Rationale for the Pragmatic default: 1M-context Opus plus prompt cache makes 50 KB workable for the maintainer's session pattern, and Lever 2 (skill conversion) carries on-load-miss risk that needs the route-boundary telemetry described below.

## Phase 0: Growth guard (mandatory prerequisite for Phases 1-2)

**Promoted from "orthogonal CI suggestion" to mandatory prerequisite.** Without it, Lever 1's "≤ 40 KB" acceptance gate is manually checkable but not enforced; the compact pass has no real red/green target and regressions land silently.

**Mechanism**: a unittest fixture in `aa/tests/test_bootstrap_size.py` that seeds a tmp consumer with the upstream `aa/AGENTS.md` (baseline only; no passive packs), runs `scripts/generate_agent_configs.py` against it, and asserts each per-agent file's byte count stays under the configured hard ceiling. Loops over a `{path: ceiling_kb}` table so adding a new agent (extending `AGENTS` in the generator) requires only one new map entry; a subset assertion against `generate_agent_configs.AGENTS` enforces this at test discovery time so a missing ceiling fails loudly instead of silently dropping coverage. Discovered automatically by the existing `aa/.github/workflows/validate.yml` matrix (`{ubuntu, windows, macos} × py3.9-3.13`); no new workflow file needed.

**Default ceilings**: 75 KB hard fail (catches gross regression); soft warn at 50 KB (Pragmatic tier); soft warn at 40 KB (Aggressive tier). Tier choice is a single env var per consumer fixture, so Aggressive paper-consumer fixtures and Pragmatic agent-style-only fixtures can coexist.

**Effort**: ~1.5 hours (revised from 0.5 day after implementation 2026-05-17). The existing `validate.yml` matrix discovers `tests/test_*.py` automatically, so no new workflow is needed; the fixture body is ~50 lines of unittest + tempfile + subprocess invocation of `generate_agent_configs.py`. Measured baselines (aa-only, no passive packs): AGENTS.md 35.5 KB, CLAUDE.md 31.6 KB, agents/codex.md 33.7 KB — CLAUDE.md has only 8.4 KB headroom to the 40 KB CC warning, which sharpens the case for Lever 1.

**Acceptance**: the size-gate job reports the measured byte count of `AGENTS.md` and every per-agent file the generator produces (currently `CLAUDE.md` and `agents/codex.md`; a subset assertion against `generate_agent_configs.AGENTS` fails when the ceiling table is missing any generator output, so adding a new agent requires adding one map entry), fails when any synthetic fixture exceeds its configured hard ceiling, and passes again after the injected growth is removed. Use either a low test-only ceiling or an injected addition large enough to cross the production 75 KB ceiling; keep the 50 KB and 40 KB tiers as warnings applied uniformly to every measured file (Pragmatic and Aggressive respectively) unless the selected fixture explicitly promotes one of them to a hard fail.

## Lever 1: aa baseline compaction (Phase 1, highest leverage)

**Scope clarification**: this lever operates on `anywhere-agents/AGENTS.md` (36.3 KB), the consumer-facing baseline. The maintainer-only `agent-config/AGENTS.md` (43.9 KB) stays as the canonical full source; the mirror to aa drops the maintainer-only sections (Submodule Workflow + Overleaf merge protocol, etc.) and that mirroring already happens via the existing ac → aa sync. Phase 1 compacts the post-mirror aa file.

**Mechanism**: edit aa/AGENTS.md in place to strip verbose examples, rationale paragraphs, and how-to-populate detail while preserving normative rules, decision tables, and required content (banner format, guard.py gates table, action-version table). The "full" version of each rule is preserved in the ac source (which the maintainer continues to read) and the git history; no `docs/agents-full/<section>.md` pairing is needed for Lever 1 itself (that pattern belongs to Lever 2 when content moves to on-demand skills).

**Target sections to compact** (measured 2026-05-17 against aa/AGENTS.md; decimal KB):

| Section | Current | Compact target | How |
|---|---:|---:|---|
| Bootstrap setup + shared-config prose | ~7.2 KB | ~3 KB | keep source-vs-consumer test, bootstrap commands, precedence table; drop rationale/history |
| Session Start Check + banner population rules | ~8.4 KB | ~3 KB | keep required banner format + decision rules; drop detailed field-population notes (move to the ac source comment if needed) |
| Codex MCP Integration | ~4.7 KB | ~2 KB | keep registration command, Windows path note, approval-policy warning; drop migration/background notes |
| Environment Notes | ~3.3 KB | ~1.5 KB | keep Miniforge Python guidance + platform-specific interpreter paths; drop install-history notes |
| Mechanical Enforcement + Shell Command Style + GitHub Actions Standards | ~5.1 KB | ~2.5 KB | keep guard table, destructive-op rules, action version table; drop examples/history |
| Other shared runtime rules (Writing Defaults, Formatting Defaults, Git Safety, Local Skills Precedence, Cross-Tool Skill Sharing) | ~7.6 KB | ~4 KB | compact prose without changing normative rules |
| **Total aa baseline** | **36.3 KB** | **~16 KB** | **~56% drop** |

**Submodule Workflow + Overleaf merge protocol is NOT part of this lever** — it lives in ac/AGENTS.md (maintainer-only, line 304) and in agent-pack's `paper-workflow` passive block. Treat that surface under Lever 2 (skill-ify the agent-pack block) or as a separate ac-only compaction task; do not count its bytes toward Lever 1.

**Expected outcome**: fresh consumer with only `agent-style` selected lands at ~37 KB CLAUDE.md (16 KB aa baseline + 20.7 KB as compact + composer overhead). Clears the 40 KB warning (Aggressive tier achieved for this shape). A paper consumer that also selects `profile` and `paper-workflow` lands at ~52 KB until Lever 2 removes those passive blocks.

**Effort**: 2-3 days for the aa compact pass plus generator/bootstrap wiring updates. The risk is losing detail that produces incorrect behavior (e.g., dropping a critical Mechanical Enforcement nuance could weaken a guard). Mitigation: the full version is preserved in ac/AGENTS.md (canonical source) and in git history; the maintainer reads ac, consumers read aa-compact.

**Migration**: zero consumer action. Bootstrap is idempotent and runs every session, so consumers get the compact version on next session start automatically.

**Status — Phase 1.A shipped 2026-05-17** (partial; ~-4 KB delivered vs the ~-20 KB target above). Three inline cuts landed: Pack deployment algorithm compressed (~3 → ~1.3 KB), Codex MCP Integration trimmed (~5 → ~2 KB), npm/winget historical caveat deleted (~0.3 KB). Measured outcome:

- aa AGENTS.md: 35.5 → **31.6 KB** (-4.0 KB, -11%)
- aa CLAUDE.md: 31.6 → **30.2 KB** (-1.4 KB; CC 40 KB headroom 8.4 → **9.8 KB**)
- aa agents/codex.md: 33.7 → **30.2 KB** (-3.5 KB; MCP cut concentrates here)
- ac AGENTS.md: 43.9 → **38.9 KB** (-4.0 KB)

Commits: aa [`ba221f7`](https://github.com/yzhao062/anywhere-agents/commit/ba221f7), ac [`5638585`](https://github.com/yzhao062/agent-config/commit/5638585). Pre-push smoke 3/3 ✓ on both. CI Validate ✓ on both.

Remaining Lever 1 scope (**Phase 1.B + 1.C**, dormant) covers the deeper compressions that would close the gap to the full ~16 KB target: Mechanical Enforcement escape-hatch prose, GHA deprecation context, How-to-populate item 2, Configuration Precedence prose (1.B); Session Start runtime branches consolidation, banned-word list reference (1.C, medium utility risk). Reactivate when ready.

**Acceptance**: Phase 0's size-gate fixture asserts `CLAUDE.md ≤ 40 KB` on a fresh consumer bootstrapped with `agent-config.yaml` selecting only `agent-style`. Existing real-agent smoke (banner emission, guard gates) remains green. Spot-check the compacted aa against the ac source for any normative rule that was accidentally dropped.

## Lever 2: agent-pack slim variants (Phase 2)

**Status — 2026-05-17 architectural correction**: the prior "passive → on-demand skill" design is **closed**. It conflicted with `pack-architecture.md` § "The two axes" (passive vs active is a behavior classification, not a sizing knob) and Round 2 "Compression layering" decision (`pack-architecture.md:914`), which prescribes slim variants (`source.path:` pointing at `pack-name-field.md` or `pack-name-lite.md`) as the canonical way to shrink passive content. The maintainer also explicitly prefers always-available passive load over context-window optimization (2026-05-17), reinforcing the same architectural direction. The Lever 2 below is the rewritten path.

**Mechanism**: agent-pack ships slim variants of its two passive packs, analogous to `as v0.4.0` shipping `rule-pack-field.md` + `rule-pack-lite.md`. The consumer's `agent-config.yaml` picks which variant to load via `source.path:`. Passive load semantics are unchanged; only the byte size differs per variant.

**Slim variant targets** (measured 2026-05-17 against agent-pack):

| Pack | Full | -field (slim) | -lite (smallest) | Compaction risk |
|---|---:|---:|---:|---|
| `profile` (`docs/rule-pack.md`) | 6.8 KB | ~4 KB | ~2 KB | Low — drop "Active focus snapshot" (dated), compress "Decision-support stance" prose; -lite also drops most of "Public projects" bullets |
| `paper-workflow` (`docs/paper-workflow.md`) | 8.0 KB | ~6 KB | ~3 KB | **Medium-high for -lite** — the Overleaf merge protocol prevents silent co-PI data loss; compressing risks losing exact `--theirs` / `--ours` rules. -field keeps full Overleaf section and trims Submodule Workflow verbose bullets only. Maintainer should weigh whether to ship -lite at all |

**Expected outcome** (paper consumer at current 65.8 KB CLAUDE.md baseline):

- `profile-field` only: -2.8 KB → ~63 KB CLAUDE.md
- `profile-field` + `paper-workflow-field`: -4.8 KB → ~61 KB CLAUDE.md
- `profile-lite` + `paper-workflow-field`: -6.8 KB → ~59 KB CLAUDE.md
- `profile-lite` + `paper-workflow-lite`: -9.8 KB → ~56 KB CLAUDE.md (with the Overleaf merge degradation flagged above)

**Effort**: ~1-2 hours for `-field` variant authoring + `agent-pack/pack.yaml` update. Optionally another 0.5 day to cut a tagged release (e.g., `agent-pack v0.2.0`) with CHANGELOG entry per the `as v0.4.0` precedent.

**Acceptance**: agent-pack ships at least `profile-field.md` and `paper-workflow-field.md`; `pack.yaml` exposes them (additional pack entries OR variant `source.path:` options on the existing entries); a consumer with `agent-config.yaml` referencing the slim variants bootstraps to a smaller AGENTS.md without changing load semantics.

**Risk**: low for `-field` variants (compress prose / drop dated content; normative rules unchanged). Medium-high for `paper-workflow-lite` specifically (Overleaf merge protocol is high-stakes detail; compressing risks silent data loss in real merges).

## Lever 3: tiny-tier as variant (deferred)

Considered and deferred. `docs/rule-pack-compact.md` is already 77% smaller than `RULES.md`. A hypothetical `rule-pack-tiny.md` (21 directive paragraphs only, no examples) would land at ~5 KB, but the BAD → GOOD example pairs do detection work: the as v0.3.0 bench measured the example-pair version's FP/FN rate against the model, not the directive-only one. Trading 16 KB of size for measurable detection-quality regression is the wrong move at the current budget level.

Revisit if: a consumer regularly stacks 5+ agent-packs and hits a hard context-budget ceiling, OR aa baseline post-Lever-1 still exceeds the chosen target.

## Item B (carried from aa#1): v1.0.0 `guard.py` → `agent-behave`

Unchanged from the prior tracker. Scope: split the PreToolUse hook out of `ac/scripts/guard.py` into a standalone pack called `agent-behave`. Hard-fail consumer projects pinned to the legacy `rule_packs:` key with an explicit migration error (env-var override cannot bypass per the original design).

When: v1.0.0 release. No concrete timeline.

Effort: multi-day. New pack scaffold, migration path, tests across consumer projects, breaking-change CHANGELOG entry.

Relationship to Levers 1-3: orthogonal (Item B does not touch AGENTS.md content size). Lever 1's compact pass should not absorb the guard.py docblock into the compact file, because that docblock becomes obsolete once Item B ships.

## Phased rollout

| Phase | Work | Effort | Ships in | Acceptance gate |
|---|---|---|---|---|
| **0** | **Growth guard (size-gate unittest fixture; mandatory prerequisite)** | **~1.5 hours** | **aa v0.6.x patch** | **size-gate fixture reports AGENTS.md plus generated per-agent byte counts, fails when any configured hard ceiling is exceeded, and passes after injected growth is removed** |
| **1.A** ✅ | **Lever 1 partial: Pack deployment compressed + Codex MCP trimmed + npm caveat deleted** | **~1.5 hours actual** | **shipped 2026-05-17 on main (aa `ba221f7`, ac `5638585`); next aa tag** | **delivered: aa AGENTS.md -4 KB / CLAUDE.md headroom 8.4 → 9.8 KB; pre-push smoke 3/3; CI Validate ✓ both repos** |
| 1.B / 1.C | Lever 1 remaining: deeper compressions (Mechanical Enforcement escape-hatch, GHA deprecation, Session Start branches, banned-list reference) | dormant | reactivate when ready | full Lever 1 target ~16 KB aa baseline |
| 2 | Lever 2 (agent-pack slim variants per pack-architecture Round 2 decision; ships `-field` / `-lite` analogous to `as v0.4.0`) | ~1-2 hours (`-field` variants); +0.5 day if tagged release | agent-pack v0.2.x | consumer `agent-config.yaml` pins variant via `source.path:`; estimated -3 to -10 KB on paper consumers depending on chosen variants; passive load semantics preserved |
| 3 | Lever 3 (as tiny) | deferred | as v0.4.x (only if needed) | revisit triggers above |
| 4 | Item B (guard.py extract) | multi-day | aa v1.0.0 | guard.py shipped as agent-behave pack; legacy `rule_packs:` key hard-fails with migration message |

## Cross-references

- aa GH#1: trajectory issue itself.
- as#6: ship issue for `docs/rule-pack-compact.md` (prior tracker wrongly cited as#4).
- aa v0.5.7 CHANGELOG: documents the manifest flip that closed Item A.
- `anywhere-agents/AGENTS.md`: the 36.3 KB target file for Lever 1's compact pass.
- `agent-pack/docs/paper-workflow.md`: the Overleaf/submodule material that belongs to Lever 2 (skill conversion) or a separate ac-only compaction task.
- `agent-pack/pack.yaml`: Lever 2 edits land here (skill conversion + on-demand-load metadata).
- `agent-config/AGENTS.md`: maintainer-only canonical source (43.9 KB; includes Submodule Workflow + Overleaf merge protocol); stays as the maintainer's reading copy.
- `agent-config/pack-architecture.md`: maintainer architecture doc; Lever 1 should update the "AGENTS.md as composition target" section.
- `agent-config/scripts/guard.py`: monolithic implementation that Item B will split.
- Prior tracker content preserved in git history at the commit before this replacement.
