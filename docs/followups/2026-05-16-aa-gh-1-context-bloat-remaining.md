# aa GH #1 — context-bloat trajectory: 2 remaining items of 6

**Status**: 4 of 6 milestones shipped; 2 remain. **Source**: [yzhao062/anywhere-agents#1](https://github.com/yzhao062/anywhere-agents/issues/1) (filed 2026-04-23). **Target**: split across remaining v0.x and v1.0.0.

## Why this file exists

The GH issue tracks the full v0.4.0 → v1.0.0 trajectory. Most of it has shipped. This file mirrors the *remaining* items into `agent-config`'s working memory so the next maintainer session can pick up the next concrete step without re-deriving what's already done from the issue body.

## Trajectory status (verified 2026-05-16)

| Milestone | Status | Evidence |
|---|---|---|
| v0.4.0 unified pack abstraction | ✅ shipped | aa `c9bba88` (Release v0.4.0) |
| v0.4.x default switch to `agent-style-field` | ❌ blocked | `aa/scripts/compose_rule_packs.py:64` still has `DEFAULT_SELECTIONS = [{"name": "agent-style"}]`; aa CHANGELOG L278 documents the dependency on agent-style shipping the slim pack first |
| v0.5.0 private-source packs via auth chain | ✅ shipped | aa `7124dd9` (Release v0.5.0) |
| v0.6.0 noise audit + composer budget gate | ✅ shipped | aa `0de7482` (Release v0.6.0) |
| v1.0.0 `guard.py` → `agent-behave` extraction | ❌ future | `ac/scripts/guard.py` still ships from `agent-config` into consumer projects via bootstrap; no `agent-behave` pack exists |

## Item A — v0.4.x `agent-style-field` default switch

**Blocker**: agent-style needs to ship a slim variant first (`rule-pack-field.md` or equivalent). Current agent-style is at v0.3.5; the slim-variant strategy is tracked in [agent-style#4](https://github.com/yzhao062/agent-style/issues/4).

**When unblocked**: edit `DEFAULT_SELECTIONS` in `aa/scripts/compose_rule_packs.py` and mirror to `aa/packages/pypi/anywhere_agents/composer/scripts/compose_rule_packs.py`. Fresh-install consumer `CLAUDE.md` size should drop under the 40 k warning threshold.

**Effort**: 1 hour once agent-style ships the slim pack.

## Item B — v1.0.0 `guard.py` → `agent-behave` extraction

**Scope**: split the PreToolUse hook out of `ac/scripts/guard.py` into a standalone pack called `agent-behave`. Hard-fail consumer projects pinned to the legacy `rule_packs:` key with an explicit migration error (env-var override cannot bypass per the original design).

**When**: v1.0.0 release. No concrete timeline.

**Effort**: multi-day. New pack scaffold, migration path, tests across consumer projects, breaking-change CHANGELOG entry.

## Cross-references

- aa GH#1: trajectory issue itself.
- agent-style#4: tracks the slim-variant dependency that gates Item A.
- `agent-config/pack-architecture.md`: maintainer's architecture doc.
- `agent-config/scripts/guard.py`: current monolithic implementation that Item B will split.
