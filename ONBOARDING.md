# Onboarding — agent-config + anywhere-agents + agent-style + agent-pack

One-page index for a new maintainer machine or future-you coming back after a gap. Read this file first; it points at the right deeper docs for whatever task you are starting.

## New machine in 3 steps

```bash
# 1. Clone all four repos side by side under ~/PycharmProjects/
git clone https://github.com/yzhao062/agent-config.git     ~/PycharmProjects/agent-config
git clone https://github.com/yzhao062/anywhere-agents.git  ~/PycharmProjects/anywhere-agents
git clone https://github.com/yzhao062/agent-style.git      ~/PycharmProjects/agent-style
git clone https://github.com/yzhao062/agent-pack.git       ~/PycharmProjects/agent-pack
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

> Read `anywhere-agents.md`, `../anywhere-agents/RELEASING.md`, and `../anywhere-agents/CHANGELOG.md`. Summarize the two-repo split, the current version, and the release flow.

From there the agent has enough context to work on either repo.

## The four-repo landscape

**Shorthand**: `ac` = `agent-config`, `aa` = `anywhere-agents`, `as` = `agent-style`, `agent-pack` keeps its full name (no two-letter shorthand yet). All forms appear interchangeably in maintainer prompts and docs; either form refers to the same repo as the full name.

The four repos are linked by **three distinct relationships**; do not confuse them:

- **`ac` ↔ `aa` — mirror (shared core).**
  `agent-config` (private working dir, public on GitHub but personal-use-only) is the canonical source for shared components (bootstrap scripts, shared skills, guard hook, `AGENTS.md` baseline) PLUS maintainer-only docs (`pack-architecture.md`, `vision.md`, `anywhere-agents.md`, `archive/`). `anywhere-agents` (public consumer) is the sanitized public release — shared components + packaging (PyPI + npm + RTD site). Shared-core files mirror byte-identically (modulo branding). Not a fork, not a submodule — manual backport from `ac` → `aa` on every release cut; physical isolation is the primary leak defense. "What gets copied vs stays private" table lives in `anywhere-agents.md`.
- **`as` ↔ `ac` / `aa` — reference only (default rule pack).**
  `agent-style` (public) is a standalone project: a literature-backed English technical-prose writing ruleset for AI agents, shipped via PyPI + npm + GitHub. It is NOT a mirror of anything in `ac` or `aa`. The only cross-reference is editorial: each `as` field-observed rule (RULE-A..I) cites `ac/aa`'s `AGENTS.md` "Writing Defaults" section as an adjacent in-practice anchor, not as a source authority. `aa` consumers receive `as` content composed into their `AGENTS.md` because `aa`'s `bootstrap/packs.yaml` registers `agent-style` as a default-on rule pack and points at `as` source. No file copy between repos; three release flows are independent.
- **`agent-pack` ↔ `ac` / `aa` — third-party reference + personal extension layer.**
  `agent-pack` (public) is a separate repo declaring three packs in the v2 manifest format: `profile` (maintainer identity, passive), `paper-workflow` (Overleaf merge protocol + paper venue conventions, passive), `acad-skills` (4 academic-writing skills, active). It serves two purposes: (a) **personal extension layer** — content that used to live only in `ac/AGENTS.md` § "User Profile" and § "Submodule Workflow" migrates here so new projects bootstrap from `aa + agent-pack` rather than from `ac` directly; (b) **third-party reference example** — fork-friendly demonstration of v2 manifest authoring for anyone who wants to ship their own pack. Served as the v0.5.0 remote-fetch acceptance test; `anywhere-agents pack add <agent-pack-url> --ref v0.1.0` now works without forking aa (shipped in v0.5.0; aa is at v0.7.2 as of 2026-05-31). No file copy between repos; independent release flow.

## Direction of travel: gradually retiring `ac`

The `ac` → `aa` mirror relationship is transitional. The maintainer is moving daily use into `aa` directly (consuming the public `anywhere-agents` bootstrap on personal projects) so the shared-core lives in one place rather than two, and the sanitization backport step goes away over time.

What this means in practice:

- **New feature work lands in `aa` first when the change is aa-only.** Rule-pack composition (v0.3.0, 2026-04-22) and the pack composer / CLI / `pack verify` chain (v0.4.0+) ship this way: built, reviewed, tagged, and published from `aa` without an ac mirror. Shared-core code (`scripts/guard.py`, `scripts/session_bootstrap.py`, `scripts/generate_agent_configs.py`) and shared skills (`skills/implement-review/`, `skills/ci-mockup-figure/`, `skills/readme-polish/`) are still maintained ac-first and mirrored to aa under STRICT byte parity. `skills/my-router/` is the documented BY-DESIGN exception (intentional ac/aa divergence).
- **`ac` still holds maintainer-only content indefinitely.** `reference-skills/`, NSF / USC / research docs, and personal runbooks stay private. Only the shared-core layer is converging.
- **Parity expectations loosen for aa-only surfaces, not shared-core or shared skills.** `scripts/check-parity.sh` continues to guard STRICT byte parity for the current shared-core set and the three shared skills listed above; planned v1.0 changes, including `guard.py` extraction to `agent-behave`, are tracked in `pack-architecture.md` § "STRICT parity trajectory". The expected degradation applies only to surfaces ac never owned (composer code, CLI, packaging).
- **Future-you reading this**: prefer touching `aa` directly unless the change is maintainer-only. If a shared-core file has already drifted in `aa`'s favor, do NOT revert it to match `ac` without confirming that is still the intent.

## "I am doing X, what should I read?"

| Task | Read first |
|---|---|
| Setting up a new machine | This file |
| Release cut on `aa` (bump version, publish to PyPI/npm/GitHub) | `../anywhere-agents/RELEASING.md` + the cheat-sheet section below |
| Release cut on `as` (bump version, publish PyPI + npm + GitHub release) | `../agent-style/RELEASING.md` — same 12-section pattern as `aa`, independent version stream |
| Cross-repo shared-core change (guard.py / session_bootstrap.py / AGENTS.md) on `ac`/`aa` | `anywhere-agents.md` — the "what gets copied" table |
| Adding or editing a rule in `as` | `../agent-style/README.md` "Curation and method" details section; canonical rules need a cited source, field-observed rules are the maintainer's call |
| Bootstrap misbehaving on a consumer project / stuck on old version | `docs/migrations.md` § "Bootstrap-cache seed refresh" |
| Complex task (hook redesign, paper outline, proposal structure) | `skills/implement-review/SKILL.md` "When to plan-review first" |
| Banner gate or writing-style gate blocking something unexpected | `AGENTS.md` "Mechanical Enforcement" section; escape via `AGENT_CONFIG_GATES=off` |
| Consumer project not picking up upstream | Open Claude Code there once — bootstrap self-updates automatically. Or force refresh via the seed-refresh block in `docs/migrations.md`. |
| Switching an existing ac-bootstrapped consumer project to aa | `docs/migrations.md` § "Consumer project: ac → aa upstream switch" — Path 1 change-upstream, Path 2 nuke-and-reinstall, verification, rollback |
| Adding a new skill | `skills/implement-review/SKILL.md` shows the skill structure; `skills/my-router/` for routing integration |
| Authoring a new pack (rule pack or skill pack) | `../anywhere-agents/docs/rule-pack-composition.md` § "Rule-pack anatomy"; `../agent-pack/` as the reference example, fork as a starting point |
| Bootstrapping a new personal project (paper, proposal, side dev) | Bootstrap from `aa` (`pipx run anywhere-agents`), then add `profile` and optionally `paper-workflow` from `agent-pack` to project `agent-config.yaml` per `../agent-pack/README.md` § "Consumer Setup" |

## Release cut — minimal cheat-sheet

Full runbook is `../anywhere-agents/RELEASING.md`. Outline, in order (each step gates the next):

1. **Pre-release checks** from a clean `main` in the `anywhere-agents` checkout:
   - Full test suite passes locally (both repos) and CI on Ubuntu + Windows is green
   - Whitespace-clean diff (`git diff --cached --check`)
   - Leak sweep for personal identifiers
   - Bilingual README parity if either `README.md` or `README.zh-CN.md` changed
   - Cross-repo parity: run `bash scripts/check-parity.sh` from the `agent-config` root. STRICT category (`scripts/{_python, guard.py, session_bootstrap.py, statusline.py, agent-quota.py, generate_agent_configs.py, pre-push-smoke.sh, remote-smoke.sh, check-parity.sh}`, `.claude/settings.json`, `.githooks/pre-push`, `.github/workflows/{real-agent-smoke.yml, validate.yml}`, `bootstrap/bootstrap.{sh,ps1}`, `tests/{test_dispatch_codex.py, test_dispatch_copilot.py, test_dispatch_claude.py, test_health_check.py, test_guard.py, test_session_bootstrap.py, test_pointer_files.py, test_prompt_byte_parity.py, test_bootstrap_preflight.py}`, `skills/{implement-review, ci-mockup-figure, readme-polish}` recursive) must be byte-identical. BY-DESIGN category (`AGENTS.md`, `user/settings.json`, `skills/my-router`) reports a +/- line delta per file; a byte-for-byte match warns that sanitization may have been skipped. The 4 shipped `.claude/commands/*.md` pointers were dropped from cross-repo STRICT in v0.4.0 (pack-emitted; see `pack-architecture.md` § "STRICT parity trajectory"). Exit 0 means STRICT clean and every BY-DESIGN mirror present; exit 1 means drift or a missing required mirror.
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
   - **Local end-to-end install tests (Claude-Code-driven).** For releases that touch `bootstrap.sh` / `bootstrap.ps1`, the pack composer (`scripts/compose_packs.py`, or its legacy alias `scripts/compose_rule_packs.py`), or the manifest (`bootstrap/packs.yaml`): ask Claude Code in the active session to drive consumer-install smoke tests end-to-end on **BOTH target platforms** (Windows this machine AND Spark Ubuntu), not only the pytest discover above. The agent has local execution on the maintainer's Windows host and SSH access to Spark, so it can create scratch consumer dirs, fetch the bootstrap from `raw.githubusercontent.com`, run it via Git Bash + PowerShell on Windows and bash on Spark, then verify the composed `AGENTS.md` contains `rule-pack:agent-style:begin` under default-on and matches upstream byte-for-byte under `rule_packs: []` opt-out. This catches shim / Git-Bash-path / PowerShell-execution-policy / pip-install-user-path issues the in-repo pytest suite does not exercise. Ask for it by name: "run the consumer-install end-to-end on Windows bash + PowerShell + Spark Ubuntu against the v<X.Y.Z> candidate".
   - **Multi-agent smoke step.** For matrix verification across hosts, set `AGENT_CONFIG_HOST` to switch the composer between Claude Code and Codex selection rows:

     ```bash
     AGENT_CONFIG_HOST=codex python scripts/compose_packs.py
     ```

     The composer reads `pack.yaml` rows whose `hosts:` field contains the selected host. Rows that omit `hosts:` apply to every host. Run this once with `AGENT_CONFIG_HOST=claude-code` and once with `AGENT_CONFIG_HOST=codex` against the release candidate, and confirm the composed outputs differ only in the host-specific entries.
2. **Pre-tag real-agent smoke** on the candidate checkout: `bash scripts/pre-push-smoke.sh` (the pre-push git hook runs it automatically on affected pushes; this explicit run gates the release-candidate commit regardless of hook bypass).
3. **Bump versions and changelog** before the release commit:
   - `packages/pypi/pyproject.toml`
   - `packages/pypi/anywhere_agents/__init__.py`
   - `packages/npm/package.json`
   - `CHANGELOG.md` (promote `[Unreleased]` to the new version header with today's date; update compare-link references)
4. **Build + scratch-venv verify before tagging**: `python -m build packages/pypi/ --outdir packages/pypi/dist`; `python -m twine check packages/pypi/dist/*`; install the wheel into a scratch venv from outside the repo; assert `anywhere-agents --version` and the Node CLI both print the bumped version.
5. **Commit + push both repos**, then **tag + push the tag** on the `anywhere-agents` commit that contains the version bumps.
6. **Publish and verify**. Since v0.7.0, running `gh release create` on the tag triggers the OIDC auto-publish workflow (PyPI + npm via Trusted Publishing, no local token); poll that workflow, then confirm both registries serve the new version. Manual `twine upload` then `npm publish` is the documented fallback in `RELEASING.md`. Confirm the post-release CI workflows (`real-agent-smoke`, `package-smoke`) go green.
7. **Post-release cleanup**: close addressed issues, reset `[Unreleased]` in `CHANGELOG.md`, delete the release-notes scratch file and any `PLAN-*.md`.

Each step's exact commands are in `../anywhere-agents/RELEASING.md`.

## Private-source acceptance procedure

To verify the pack auth chain (shipped in v0.5.0; implemented in `scripts/packs/auth.py` and `source_fetch.py`) works in your local environment, fetch a private repo you own via SSH:

```bash
python -c "
from scripts.packs import auth
import pathlib
archive = auth.fetch_with_method(
    'git@github.com:owner/private-test.git',
    'main',
    'ssh',
    dest=pathlib.Path('.scratch'),
)
print(archive.archive_dir)
"
```

A clean SSH path returns an archive directory under `.scratch/`. If `ssh-add -L` does not list a key, the SSH method falls through to gh CLI; verify with `gh auth status`. The fall-through chain is documented in `pack-architecture.md`.

Replace `owner/private-test` with one of your own private repos; the test is shape-only and does not depend on a specific repo body. Run the command from the `anywhere-agents` checkout root so the `scripts.packs` import resolves.

## Key files at a glance

### `agent-config` (private, this repo)

- `AGENTS.md` — canonical maintainer rules; auto-loaded as `CLAUDE.md` by Claude Code on every session start
- `anywhere-agents.md` — two-repo relationship, "what gets copied" table, release workflow with sanitization rules
- `docs/migrations.md` — two operational sections: bootstrap-cache seed refresh (machine-level) and consumer project ac → aa upstream switch (project-level)
- `scripts/guard.py` + `scripts/session_bootstrap.py` — shared-core hooks; byte-identical with `anywhere-agents` copies
- `skills/implement-review/SKILL.md` — the review-loop workflow including Phase 0 plan-first
- `reference-skills/` — research-specific skills that never copy to public (NSF, USC, CS paper review, etc.)

### `anywhere-agents` (public)

- `RELEASING.md` — release runbook (six pre-release checks + the publish pipeline). Also hosts the `CI API cost exposure` section (workflow-by-workflow cost table + agent dispatch-approval policy) that applies to both `aa` and `ac` — the `real-agent-smoke.yml` and `validate.yml` workflows are STRICT byte-identical mirrors between the two repos, so the cost model is shared. Read this before dispatching any paid workflow in either repo.
- `CHANGELOG.md` — version history and current version (read this to know what version we are at)
- `README.md` + `README.zh-CN.md` — public-facing docs; bilingual parity required on structural changes
- `packages/pypi/` + `packages/npm/` — CLI package sources; version stream synced to the repo tag
- `docs/` — Read the Docs site source (MkDocs Material), hero/banner images
- `skills/` — only the shared skills (subset of `agent-config/skills/`)

### `agent-style` (public, standalone)

- `RULES.md` — canonical 12 rules (RULE-01..12 from Strunk & White / Orwell / Pinker / Gopen & Swan) + 9 field-observed rules (RULE-A..I from the maintainer); each rule carries source metadata, directive, 5+ BAD/GOOD pairs, rationale
- `README.md` — public landing page with hero figure, four-source collage, and bench scorecard panel
- `CHANGELOG.md` + `RELEASING.md` — version history and release runbook (same general pattern as `aa`, independent version stream). `RELEASING.md` also carries the `CI API Cost Exposure` section: workflow-by-workflow cost table, annual forecast, and an agent dispatch-approval policy ("any `gh workflow run` above $0.01 per dispatch needs explicit user approval even inside a broader approved task"). Read it before dispatching any paid workflow.
- `agents/` — 9 primary adapter files (Claude Code, AGENTS.md, Copilot repo / path, Cursor, Anthropic Skills, Codex, Aider, Kiro); `list-tools` surfaces a 10th entry, `style-review`, owned by `skills/` below
- `skills/style-review/` — opt-in post-hoc review pass (`skill-with-references` install mode added in v0.2.0); complements generation-time soft enforcement. Bundled copies under `packages/pypi/agent_style/data/skills/` and `packages/npm/data/skills/`; manifest-based safe disable (sha256 per file) lives at `.agent-style/skills/style-review/manifest.json` in consumer projects
- `packages/pypi/` + `packages/npm/` — CLI package sources (byte-identical canonical JSON across both ecosystems; `agent-style review <file>` available from the plain CLI without a skill host)
- `scripts/bench/` (`run.sh`, `aggregate.py`, `tasks.md`, `runners/`) + `docs/bench-*.md`: local-only sanity benchmark, 10 prose tasks by 2 generations by 2 conditions. Driven by `scripts/bench/run.sh`; there is no `bench.yml` workflow. Supports up to five runners (claude, gemini, codex, copilot, openai), though published runs have used subsets. `scripts/bench/aggregate.py` merges per-runner scorecards when splicing partial runs. Run on major or minor releases, not patches
- `scripts/smoke-skill-safety.sh` — regression suite for the `skill-with-references` install mode (20 scenarios × Python + Node: ownership proof, atomicity, path traversal, drift fail-closed, missing-sha256, empty entries, absent-manifest). Platform-aware; runs on Windows + Linux
- `.github/workflows/real-agent-smoke.yml` — live-API handshake probe for Claude + Codex + style-review skill + Kiro adapter on `release.published` + `workflow_dispatch` (~$0.05/run, pinned to Sonnet)
- `.github/workflows/adapter-{aider,gemini,agents-sdk}-smoke.yml` — per-adapter runtime regression workflows. `workflow_dispatch` only. 3 fixed prompts × runner, gated on draft-length and violation-count thresholds. Costs ~$0.10 (aider Sonnet), $0 (gemini Flash free tier), ~$0.01 (agents-sdk nano)
- `scripts/verify-fresh-install.py` — cross-platform end-to-end install smoke (Windows + Linux aarch64)

### `agent-pack` (public, third-party reference + personal extension layer)

- `pack.yaml` — self-describing v2 manifest declaring 3 packs (`profile`, `paper-workflow`, `acad-skills`); mirrors the schema used by `aa-core-skills` so v0.5.0 remote-fetch tooling reads it without special handling
- `docs/rule-pack.md` — `profile` pack body (maintainer identity, public projects, communication preferences, tools, conventions); CC-BY-4.0
- `docs/paper-workflow.md` — `paper-workflow` pack body (Overleaf submodule etiquette, merge-conflict resolution, NSF/NIH framework defaults); CC-BY-4.0
- `skills/{bibref-filler,bibref-verify,dual-pass-workflow,figure-prompt-builder}/` — active skill content for the `acad-skills` pack; remote installation via `anywhere-agents` v0.5.0+ direct-URL pack consumption
- `scripts/validate.py` — v2 schema validator (allowed `update_policy`, allowed `kind`, file mapping path existence); CI runs on every push
- `README.md` — Consumer Setup with v0.4.0 vs v0.5.0 honest split (v0.4.0: copy bodies into `AGENTS.local.md` or fork aa's bundled manifest; v0.5.0: native `anywhere-agents pack add <url> --ref <tag>`)

### Consumer projects (your daily projects under `~/PycharmProjects/*`)

- `.agent-config/bootstrap.ps1` + `.sh` — self-updating bootstrap scripts (since 0.1.5)
- `.agent-config/session-event.json` + `.agent-config/banner-emitted.json` — per-project flag files (since 0.1.9)
- `.agent-config/upstream` — which upstream this consumer tracks (`yzhao062/agent-config` for yours, `yzhao062/anywhere-agents` for public consumers)
- `AGENTS.md` + `CLAUDE.md` + `agents/codex.md` — refreshed from upstream on every bootstrap

## When in doubt

Ask Claude Code in natural language: "I am starting work on X. What should I know?" It will cite the right docs, and propose plan-first if the task meets the signals in `skills/implement-review/SKILL.md`.

## When to update this file

Update when:
- The repo family relationships change (convergence, split, new sibling repo, migration to a different platform)
- The release workflow gains or loses a major step
- A new shared-component category is added
- A change in daily workflow big enough that future-you would forget (0.1.9 per-project flag migration was a good candidate; agent-pack as a separate personal extension layer in 2026-04 was another; typo fixes are not)

Do NOT update for: small skill updates, bug-fix releases, documentation tweaks inside the deeper docs this file points at.
