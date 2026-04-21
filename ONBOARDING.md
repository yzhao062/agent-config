# Onboarding — agent-config + anywhere-agents + agent-style

One-page index for a new maintainer machine or future-you coming back after a gap. Read this file first; it points at the right deeper docs for whatever task you are starting.

## New machine in 3 steps

```bash
# 1. Clone all three repos side by side under ~/PycharmProjects/
git clone https://github.com/yzhao062/agent-config.git     ~/PycharmProjects/agent-config
git clone https://github.com/yzhao062/anywhere-agents.git  ~/PycharmProjects/anywhere-agents
git clone https://github.com/yzhao062/agent-style.git      ~/PycharmProjects/agent-style
```

```
# 2. In PyCharm: open agent-config (primary), then File > Open > choose
#    anywhere-agents directory > "Attach". Both trees become visible. Claude
#    Code's Additional working directories already covers ~/PycharmProjects,
#    so agent can read/write both repos without /add-dir.
```

```bash
# 3. Open a PyCharm terminal in agent-config and launch Claude Code:
claude
```

First prompt after `claude` starts:

> Read `docs/anywhere-agents.md`, `../anywhere-agents/RELEASING.md`, and `../anywhere-agents/CHANGELOG.md`. Summarize the two-repo split, the current version, and the release flow.

From there the agent has enough context to work on either repo.

## The three-repo landscape

**Shorthand**: `ac` = `agent-config`, `aa` = `anywhere-agents`, `as` = `agent-style`. All three forms appear interchangeably in maintainer prompts and docs; either form refers to the same repo as the full name.

The three repos are linked by **two distinct relationships**; do not confuse them:

- **`ac` ↔ `aa` — mirror (shared core).**
  `agent-config` (private) is the canonical source for shared components (bootstrap scripts, shared skills, guard hook, `AGENTS.md` baseline) PLUS personal content (USC-specific rules, `reference-skills/`, research docs, maintainer runbooks). `anywhere-agents` (public) is the sanitized public release — only the shared components + packaging (PyPI + npm + RTD site). Shared-core files mirror byte-identically (modulo branding). Not a fork, not a submodule — manual backport from `ac` → `aa` on every release cut; physical isolation is the primary leak defense. "What gets copied vs stays private" table lives in `docs/anywhere-agents.md`.
- **`as` ↔ `ac` / `aa` — reference only.**
  `agent-style` (public) is a standalone project: a literature-backed English technical-prose writing ruleset for AI agents, shipped via PyPI + npm + GitHub. It is NOT a mirror of anything in `ac` or `aa`. The only cross-reference is editorial: each `as` field-observed rule (RULE-A..I) cites `ac/aa`'s `AGENTS.md` "Writing Defaults" section as an adjacent in-practice anchor, not as a source authority. No files are copied between `as` and the other two; the three release flows are independent.

## "I am doing X, what should I read?"

| Task | Read first |
|---|---|
| Setting up a new machine | This file |
| Release cut on `aa` (bump version, publish to PyPI/npm/GitHub) | `../anywhere-agents/RELEASING.md` + the cheat-sheet section below |
| Release cut on `as` (bump version, publish PyPI + npm + GitHub release) | `../agent-style/RELEASING.md` — same 12-section pattern as `aa`, independent version stream |
| Cross-repo shared-core change (guard.py / session_bootstrap.py / AGENTS.md) on `ac`/`aa` | `docs/anywhere-agents.md` — the "what gets copied" table |
| Adding or editing a rule in `as` | `../agent-style/README.md` "Curation and method" details section; canonical rules need a cited source, field-observed rules are the maintainer's call |
| Bootstrap misbehaving on a consumer project / stuck on old version | `MIGRATIONS.md` |
| Complex task (hook redesign, paper outline, proposal structure) | `skills/implement-review/SKILL.md` "When to plan-review first" |
| Banner gate or writing-style gate blocking something unexpected | `AGENTS.md` "Mechanical Enforcement" section; escape via `AGENT_CONFIG_GATES=off` |
| Consumer project not picking up upstream | Open Claude Code there once — bootstrap self-updates automatically. Or force refresh via `MIGRATIONS.md` block. |
| Adding a new skill | `skills/implement-review/SKILL.md` shows the skill structure; `skills/my-router/` for routing integration |

## Release cut — minimal cheat-sheet

Full runbook is `../anywhere-agents/RELEASING.md`. Outline, in order (each step gates the next):

1. **Pre-release checks** from a clean `main` in the `anywhere-agents` checkout:
   - Full test suite passes locally (both repos) and CI on Ubuntu + Windows is green
   - Whitespace-clean diff (`git diff --cached --check`)
   - Leak sweep for personal identifiers
   - Bilingual README parity if either `README.md` or `README.zh-CN.md` changed
   - Cross-repo parity — run `bash scripts/check-parity.sh` from the `agent-config` root. STRICT category (`scripts/{guard.py, session_bootstrap.py, generate_agent_configs.py, pre-push-smoke.sh, remote-smoke.sh}`, `.claude/settings.json`, `.githooks/pre-push`, `.github/workflows/{real-agent-smoke.yml, validate.yml}`, 4 shipped `.claude/commands/*.md` pointers, `skills/{implement-review,ci-mockup-figure,readme-polish}` recursive) must be byte-identical. BY-DESIGN category (`AGENTS.md`, `bootstrap/bootstrap.{sh,ps1}`, `user/settings.json`, `skills/my-router`) reports a +/- line delta per file; a byte-for-byte match warns that sanitization may have been skipped. Exit 0 means STRICT clean and every BY-DESIGN mirror present; exit 1 means drift or a missing required mirror.
   - **Spark Linux test** runs before tagging:
     ```bash
     ssh yzhao062@spark-37f2.local '
       if [ -d ~/agent-config ]; then
         git -C ~/agent-config pull --ff-only
       else
         git clone https://github.com/yzhao062/agent-config.git ~/agent-config
       fi
       python3 -B -m unittest discover -s ~/agent-config/tests -p "test_*.py" 2>&1 | tail -5
     '
     ```
2. **Pre-tag real-agent smoke** on the candidate checkout: `bash scripts/pre-push-smoke.sh` (the pre-push git hook runs it automatically on affected pushes; this explicit run gates the release-candidate commit regardless of hook bypass).
3. **Bump versions and changelog** before the release commit:
   - `packages/pypi/pyproject.toml`
   - `packages/pypi/anywhere_agents/__init__.py`
   - `packages/npm/package.json`
   - `CHANGELOG.md` (promote `[Unreleased]` to the new version header with today's date; update compare-link references)
4. **Build + scratch-venv verify before tagging**: `python -m build packages/pypi/ --outdir packages/pypi/dist`; `python -m twine check packages/pypi/dist/*`; install the wheel into a scratch venv from outside the repo; assert `anywhere-agents --version` and the Node CLI both print the bumped version.
5. **Commit + push both repos**, then **tag + push the tag** on the `anywhere-agents` commit that contains the version bumps.
6. **Publish and verify** in order, polling between each: TestPyPI → real PyPI → npm → `gh release create`. Confirm the post-release CI workflows (`real-agent-smoke`, `package-smoke`) go green.
7. **Post-release cleanup**: close addressed issues, reset `[Unreleased]` in `CHANGELOG.md`, delete the release-notes scratch file and any `PLAN-*.md`.

Each step's exact commands are in `../anywhere-agents/RELEASING.md`.

## Key files at a glance

### `agent-config` (private, this repo)

- `AGENTS.md` — canonical maintainer rules; auto-loaded as `CLAUDE.md` by Claude Code on every session start
- `docs/anywhere-agents.md` — two-repo relationship, "what gets copied" table, release workflow with sanitization rules
- `MIGRATIONS.md` — one-shot bootstrap upgrade procedures for consumer projects stuck on old versions
- `scripts/guard.py` + `scripts/session_bootstrap.py` — shared-core hooks; byte-identical with `anywhere-agents` copies
- `skills/implement-review/SKILL.md` — the review-loop workflow including Phase 0 plan-first
- `reference-skills/` — research-specific skills that never copy to public (NSF, USC, CS paper review, etc.)

### `anywhere-agents` (public)

- `RELEASING.md` — release runbook (six pre-release checks + the publish pipeline)
- `CHANGELOG.md` — version history and current version (read this to know what version we are at)
- `README.md` + `README.zh-CN.md` — public-facing docs; bilingual parity required on structural changes
- `packages/pypi/` + `packages/npm/` — CLI package sources; version stream synced to the repo tag
- `docs/` — Read the Docs site source (MkDocs Material), hero/banner images
- `skills/` — only the shared skills (subset of `agent-config/skills/`)

### `agent-style` (public, standalone)

- `RULES.md` — canonical 12 rules (RULE-01..12 from Strunk & White / Orwell / Pinker / Gopen & Swan) + 9 field-observed rules (RULE-A..I from the maintainer); each rule carries source metadata, directive, 5+ BAD/GOOD pairs, rationale
- `README.md` — public landing page with hero figure, four-source collage, and bench scorecard panel
- `CHANGELOG.md` + `RELEASING.md` — version history and release runbook (same general pattern as `aa`, independent version stream)
- `agents/` — 9 primary adapter files (Claude Code, AGENTS.md, Copilot repo / path, Cursor, Anthropic Skills, Codex, Aider, Kiro); `list-tools` surfaces a 10th entry, `style-review`, owned by `skills/` below
- `skills/style-review/` — opt-in post-hoc review pass (`skill-with-references` install mode added in v0.2.0); complements generation-time soft enforcement. Bundled copies under `packages/pypi/agent_style/data/skills/` and `packages/npm/data/skills/`; manifest-based safe disable (sha256 per file) lives at `.agent-style/skills/style-review/manifest.json` in consumer projects
- `packages/pypi/` + `packages/npm/` — CLI package sources (byte-identical canonical JSON across both ecosystems; `agent-style review <file>` available from the plain CLI without a skill host)
- `scripts/bench/run.sh` + `.github/workflows/bench.yml` + `docs/bench-*.md` — sanity benchmark: 10 fixed prose tasks × 2 generations, Claude Code baseline vs `agent-style`-loaded. `workflow_dispatch` only (~$0.40–0.80/run). Scorecard committed per release
- `scripts/smoke-skill-safety.sh` — regression suite for the `skill-with-references` install mode (20 scenarios × Python + Node: ownership proof, atomicity, path traversal, drift fail-closed, missing-sha256, empty entries, absent-manifest). Platform-aware; runs on Windows + Linux
- `.github/workflows/real-agent-smoke.yml` — live-API smoke test against Claude + Codex on `release.published` + `workflow_dispatch`
- `scripts/verify-fresh-install.py` — cross-platform end-to-end install smoke (Windows + Linux aarch64)

### Consumer projects (your daily projects under `~/PycharmProjects/*`)

- `.agent-config/bootstrap.ps1` + `.sh` — self-updating bootstrap scripts (since 0.1.5)
- `.agent-config/session-event.json` + `.agent-config/banner-emitted.json` — per-project flag files (since 0.1.9)
- `.agent-config/upstream` — which upstream this consumer tracks (`yzhao062/agent-config` for yours, `yzhao062/anywhere-agents` for public consumers)
- `AGENTS.md` + `CLAUDE.md` + `agents/codex.md` — refreshed from upstream on every bootstrap

## When in doubt

Ask Claude Code in natural language: "I am starting work on X. What should I know?" It will cite the right docs, and propose plan-first if the task meets the signals in `skills/implement-review/SKILL.md`.

## When to update this file

Update when:
- The two-repo relationship changes (convergence, split, migration to a different platform)
- The release workflow gains or loses a major step
- A new shared-component category is added
- A change in daily workflow big enough that future-you would forget (0.1.9 per-project flag migration was a good candidate; typo fixes are not)

Do NOT update for: small skill updates, bug-fix releases, documentation tweaks inside the deeper docs this file points at.
