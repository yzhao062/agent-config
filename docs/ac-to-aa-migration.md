# Consumer-repo migration: `ac` → `aa`

This doc is for the maintainer (and future-you coming back after a gap). It explains how to migrate an existing `agent-config` (ac) consumer project to the `anywhere-agents` (aa) bootstrap upstream, when to do it, and when NOT to do it. The destination is the direction of travel recorded in `ONBOARDING.md`: gradually retire ac's public-facing role so daily shared-core lives in aa, while ac keeps maintainer-only content indefinitely.

**Audience:** single-maintainer migration notes, not a user-facing public guide. Commands assume your daily-driver Windows + Spark Ubuntu setup and Miniforge py312 Python. Public consumers of aa never had an ac install, so this guide does not apply to them.

## TLDR

- One-line switch for any consumer project: change `.agent-config/upstream` to `yzhao062/anywhere-agents`, rerun bootstrap. Rollback is the same one-line change in the opposite direction.
- Paper / proposal / submodule-coupled repos stay on ac (ac-only skills — both `ac/skills/{bibref-filler,dual-pass-workflow,figure-prompt-builder}` and `ac/reference-skills/*` — plus USC/Overleaf AGENTS.md sections live there). Dev projects switch.
- `~/.claude/hooks/` files are byte-identical across ac and aa (STRICT parity guarantee), so switching does not change hook behavior.
- aa v0.3.0+ composes the `agent-style` rule pack into `AGENTS.md` by default. Opt out per-project with `rule_packs: []` in `agent-config.yaml`.

## Why migrate

As of 2026-04-22, the direction in `ONBOARDING.md` is "gradually retire ac". Rule-pack composition (v0.3.0) was the first feature to land aa-first without a parallel ac mirror commit. Future aa-first features will keep widening the gap; ac-only consumers miss them unless you manually backport. Migration is how daily-driver projects stop falling behind.

Separate reasons that also count:

- **One source of truth** for shared-core. Two sources meant two places to edit the same content, a sanitization step between them, and a `check-parity.sh` gate protecting against drift. Retiring the ac public-facing role collapses this to one place (aa) and one flow.
- **Private content stays private more cleanly.** With ac shrinking to only maintainer-only content (`reference-skills/`, USC/Overleaf sections, research runbooks), the "private content might accidentally ship to aa" risk goes down.
- **New public consumers never see the legacy path.** They already install from aa. Aligning your own daily use with their path means dogfooding what external users get.

## Non-goals

This guide does NOT cover:

- Migrating ac itself — ac stays canonical for private content indefinitely. No ac-repo changes required by this guide.
- Public aa consumers — they never had an ac install. Migration is a single-maintainer-only concern.
- `agent-style` repo — independent release stream; not affected.

## Scope

A single consumer project, one repo at a time. The migration is project-scoped; other ac-consumer projects on the same machine are unaffected until you migrate them separately.

## Decision: which projects switch, which stay

The practical check is _does this project need any file that lives only in ac?_

Stay on ac when the project uses any of:

- **ac-only shared skills in `ac/skills/`**: `bibref-filler`, `dual-pass-workflow`, `figure-prompt-builder`. ac ships seven shared skills; aa ships only the four the public mirror needs (`implement-review`, `my-router`, `ci-mockup-figure`, `readme-polish`). The three ac-only entries would disappear from `.agent-config/repo/skills/` after migration.
- **Private reference skills in `ac/reference-skills/`**: NSF templates, USC proposal helpers, CS paper review helpers, CV / deck helpers, `nsf-merit-review`, and related. These are never mirrored to aa and would also disappear after migration.
- **USC / Overleaf / PyCharm-specific AGENTS.md sections.** aa's sanitized mirror strips those.
- **Submodule-coupled paper repos shared with co-PIs.** Submodules are separate repos with their own `.agent-config/upstream`; bootstrap does not recursively walk submodules. Flipping the outer project's upstream does NOT automatically flip a submodule — you would need to rerun the migration inside the submodule separately. For co-authored paper repos, the recommendation is to audit the submodule as its own project and usually leave it on ac unless the co-PI has agreed to the switch.

Switch to aa when the project is:

- A pure dev project (PyOD, general code, tooling) with no dependency on any ac-only skill (`ac/skills/{bibref-filler,dual-pass-workflow,figure-prompt-builder}` or `ac/reference-skills/*`) and no need for USC/Overleaf-specific AGENTS.md sections.
- A fresh project. Bootstrap from aa directly; skip the ac path.
- Any project where the sanitized public AGENTS.md is sufficient.

Suggested decision matrix (post-v0.5.0):

| Project type | Decision | Driver |
|---|---|---|
| Paper repo (USC, NSF, Overleaf) | aa + private pack via auth chain | v0.5.0 direct-URL packs replace the ac-only skill load path; the 4-method auth chain handles private repos |
| Private pack (single-maintainer skills, USC templates) | aa with SSH / gh CLI / PAT auth (one-line install) | `anywhere-agents pack add <url> --ref <tag>` resolves auth automatically; no manual checkout |
| Dev repo (PyOD, general coding, infra tooling) | Switch to aa | No private dep; gains aa-first features (rule-pack composer + direct-URL packs) |
| Fresh project | Bootstrap from aa directly | Zero legacy; skip ac entirely |
| Submodule-coupled shared repo | Stay on ac unless co-PI agrees | Co-PI consent gates the upstream switch; v0.5.0 capability is technical, not social |
| Teaching / admin / committee docs | Repackage as pack, then aa | Templates that previously lived in `ac/skills/` ac-only subset or `ac/reference-skills/` can ship as a private pack served from your own GitHub repo |
| Unclear | Stay on ac | Switching later is cheap; losing private content and rediscovering it is not |

## Rollout cadence (opinionated, optional)

1. **Today:** bootstrap every new project from aa directly. Zero migration; costless. This is the highest-value step because it compounds over time.
2. **One low-stakes dev project:** flip it. Use it for 2-3 sessions. Confirm nothing breaks, confirm the rule-pack composition on AGENTS.md is what you want.
3. **Batch-switch remaining dev projects:** once confident, flip others in one short sitting.
4. **Indefinitely:** paper / proposal / submodule repos stay on ac. The retirement is about shrinking ac's _public-facing_ role, not shutting ac down.

Skip the rollout if you prefer; every project can migrate independently when convenient. The only scheduled step is "greenfield projects go to aa starting now".

## Mechanics: how to switch a single project

Two paths. Path 1 is the recommended one. Path 2 is for when Path 1 misbehaves or you want a clean slate.

### Path 1: Change upstream (recommended)

Bash (macOS / Linux / Git Bash):

```bash
# From the consumer project root
echo 'yzhao062/anywhere-agents' > .agent-config/upstream
bash .agent-config/bootstrap.sh
```

PowerShell (Windows):

```powershell
# From the consumer project root
Set-Content -Path .agent-config/upstream -Value 'yzhao062/anywhere-agents' -NoNewline
& .\.agent-config\bootstrap.ps1
```

That is the full migration. Bootstrap is idempotent and self-healing; on the next run it:

- Refetches `AGENTS.md` from `yzhao062/anywhere-agents` (now the sanitized public version with the `agent-style` rule-pack block composed on top, under default-on).
- Re-sparse-clones aa's `skills/` tree. Drops both ac-only private `reference-skills/` AND the three ac-only shared skills `ac/skills/{bibref-filler, dual-pass-workflow, figure-prompt-builder}`. Keeps only the four aa-shipped skills: `implement-review`, `my-router`, `ci-mockup-figure`, `readme-polish`.
- Regenerates `CLAUDE.md` and `agents/codex.md` from the refetched AGENTS.md via `scripts/generate_agent_configs.py`.
- Merges aa's `.claude/settings.json` shared keys over the existing project settings (project-only keys preserved).
- Leaves `~/.claude/hooks/guard.py` and `session_bootstrap.py` untouched — they are byte-identical between ac and aa per the STRICT parity guarantee, so whichever you bootstrap from deploys the same hooks.

### Path 2: Nuke and reinstall (only when Path 1 misbehaves)

Use this when the project's `.agent-config/` cache is corrupted, or when you want to start from a verified-clean state.

**Precondition (aa v0.4.0+)**: if the project has active packs installed (detectable by the presence of `.agent-config/pack-state.json`), **run the uninstall-all step first**. Deleting `.agent-config/` alone is cache cleanup; it does not clean user-level pack-owned hooks in `~/.claude/hooks/<pack>/` or pack-owned entries in `~/.claude/settings.json`, and skipping the uninstall leaves them orphaned with the current repo still in their `owners:` list. The aa v0.4.0 composer ships the canonical command `anywhere-agents uninstall --all`; the PyPI entry point and `npx anywhere-agents uninstall --all` expose the same command semantics. If the command exits nonzero, stop and resolve the reported issue before deleting `.agent-config/`.

```bash
# From the consumer project root

# Pre-step (aa v0.4.0+ only): uninstall active packs to clean user-level state.
# Skippable when .agent-config/pack-state.json does not exist (pre-v0.4.0
# install) OR when the project had only passive packs installed.
# Nonzero exit from uninstall aborts Path 2 so the state file needed for
# retry/inspection is not destroyed (drift, lock timeout, malformed state
# all surface here via the exit-code contract in docs/pack-architecture.md).
if [ -f .agent-config/pack-state.json ]; then
  if ! anywhere-agents uninstall --all; then
    echo "anywhere-agents uninstall --all failed; aborting Path 2 cleanup." >&2
    exit 1
  fi
fi

# DANGER: deletes local cache and generated per-agent files.
# Confirm AGENTS.local.md is committed and any direct edits to AGENTS.md are
# already migrated to AGENTS.local.md. Bootstrap regenerates AGENTS.md and
# the CLAUDE.md / agents/codex.md files from upstream; anything unique in
# them that is not in .local.md will be lost.
rm -rf .agent-config AGENTS.md CLAUDE.md agents/codex.md
mkdir -p .agent-config
curl -sfL https://raw.githubusercontent.com/yzhao062/anywhere-agents/main/bootstrap/bootstrap.sh -o .agent-config/bootstrap.sh
bash .agent-config/bootstrap.sh
```

`AGENTS.local.md` and `.claude/settings.local.json` are NEVER touched by either path.

**Warning**: skipping the uninstall pre-step and going straight to `rm -rf .agent-config/` leaves any user-level hooks (`~/.claude/hooks/<pack>/*`) and permission entries (`~/.claude/settings.json`) orphaned. Running bootstrap afterward does not re-register ownership of those orphans, and a future install from the same or a different pack at the same target path will fail closed with `user-level-output-conflict` until you manually clean the orphan entry from `~/.claude/pack-state.json`.

## Pre-migration checks (do these once, per project)

Before flipping a given project's upstream:

1. **Confirm `AGENTS.md` was not manually edited.** Bootstrap overwrites `AGENTS.md` on every run, so any direct edits you made are already at risk — but the migration is a good time to audit. Run `git log --follow --pretty=short AGENTS.md`; if any commit reads as a manual edit rather than a bootstrap refresh, move those rules into `AGENTS.local.md` first.
2. **Confirm no dependency on ac-only skills.** Check `.claude/commands/` pointer files: `grep -r '.agent-config/repo/skills/' .claude/commands/` and read any hits. If any reference a skill that exists ONLY in ac — either `ac/skills/{bibref-filler,dual-pass-workflow,figure-prompt-builder}` OR any `ac/reference-skills/<name>/` — this project should stay on ac, or copy the needed skill into the project's own `skills/<name>/` directory (repo-local beats shared).
3. **Confirm the four aa skills are enough.** Any routing logic in the project that expects a skill not in `{implement-review, my-router, ci-mockup-figure, readme-polish}` and not in the project's own `skills/` directory will break on migration.
4. **Run pre-push smoke on the project** (if the project has a pre-push hook tied to the shared-core): optional but cheap. Catches local misconfiguration before the flip.

## Verification after switch

Immediately after the first post-migration bootstrap run:

```bash
cat .agent-config/upstream
# expected: yzhao062/anywhere-agents

grep -c 'rule-pack:agent-style:begin' AGENTS.md
# expected: 1   (aa v0.3.0+ default-on rule-pack composition)

ls .agent-config/repo/skills/
# expected: ci-mockup-figure implement-review my-router readme-polish
# (exactly four entries)

ls .claude/commands/
# expected shared aa pointers: ci-mockup-figure.md implement-review.md my-router.md readme-polish.md
# Any extra file is either project-local or a STALE ac-only pointer
# (bibref-filler.md, dual-pass-workflow.md, figure-prompt-builder.md, plus
# any reference-skill pointer the project previously enabled). Bootstrap
# does NOT delete stale pointers; remove them manually unless the project
# has copied the matching skill into repo-local skills/<name>/.

ls -1 AGENTS.local.md .claude/settings.local.json 2>/dev/null
# your local overrides must still be present
```

PowerShell equivalent for the pointer check:

```powershell
Get-ChildItem .claude/commands
# Expected shared aa pointers: ci-mockup-figure.md, implement-review.md, my-router.md, readme-polish.md.
# Remove any stale ac-only pointer manually.
```

If any of these diverges from expected, roll back and investigate (most likely cause: Path 1 ran from the wrong cwd, or the project has a stale `.agent-config/` cache — try Path 2 in that case).

## Rollback

Fully reversible. Point upstream back at ac:

```bash
echo 'yzhao062/agent-config' > .agent-config/upstream
bash .agent-config/bootstrap.sh
```

PowerShell:

```powershell
Set-Content -Path .agent-config/upstream -Value 'yzhao062/agent-config' -NoNewline
& .\.agent-config\bootstrap.ps1
```

The round-trip is free. The rule-pack block in `AGENTS.md` disappears on the next ac bootstrap because ac does not ship the rule-pack composer today.

## Opting out of the default `agent-style` rule pack

If a specific project should NOT carry the agent-style writing rules (e.g., a code-only repo with no prose, a repo for a co-author who dislikes the ruleset), add an explicit opt-out at project root:

```yaml
# agent-config.yaml (tracked, at consumer project root)
rule_packs: []
```

Commit `agent-config.yaml`. Bootstrap on every subsequent run respects the opt-out and writes upstream `AGENTS.md` verbatim without the rule-pack block.

Transient per-session opt-out (no commit) is not cleanly supported today; the `AGENT_CONFIG_RULE_PACKS` env var adds packs on top, it does not subtract. If you need a one-run opt-out, the cleanest path is still the committed `rule_packs: []` file.

## What does ac keep, long-term

After retirement stabilizes, ac's footprint shrinks to maintainer-only content:

- `reference-skills/` — private research skills not shipped publicly.
- AGENTS.md private sections — USC / Overleaf / PyCharm-specific rules stripped from aa's sanitized mirror.
- Private runbooks and planning docs — internal CI-cost drafts, research-project plans, `PLAN-*.md` scratch files, `docs/vision.md`.
- ac's own `bootstrap.sh` and `bootstrap.ps1` — these stay operational so paper / proposal / submodule projects continue to bootstrap from ac indefinitely.

Expect ac's shared-core to drift from aa's shared-core as aa-first features (rule-pack composer today; future features later) accumulate. But today, `scripts/check-parity.sh` is still BLOCKING for files it classifies as STRICT — hooks (`guard.py`, `session_bootstrap.py`), generator scripts (`generate_agent_configs.py`), smoke scripts, GitHub workflows (`validate.yml`, `real-agent-smoke.yml`), `.claude/settings.json`, `.githooks/pre-push`, and shipped shared-skill pointers. The script exits 1 on strict drift and the release runbook still treats that as blocking.

Treat aa-first rule-pack composition as a by-design divergence, but do NOT ignore genuine STRICT drift in hooks or workflows just because ac is retiring — those mirrors still protect release correctness today. If and when the script and runbook are changed to make the STRICT category informational (because ac is no longer a release-facing mirror), update this paragraph to match. Until then: `check-parity.sh` STRICT remains a release gate.

No scheduled end-of-life for ac. Retirement is about shrinking the public-facing role, not about shutting ac down.

### Forward direction: direct-URL packs in aa (v0.5.0)

aa v0.5.0 (2026-04-26) shipped direct-URL pack consumption. A consumer's `agent-config.yaml` can now list any GitHub repo as a pack source via `source.url` and `source.ref`; the 4-method auth chain (SSH agent, `gh` CLI token, `GITHUB_TOKEN` env, anonymous fallback) negotiates access on every fetch. Public URLs succeed on the anonymous method; private URLs succeed on whichever authenticated method the host has configured. No manifest fork is required.

[`agent-pack`](https://github.com/yzhao062/agent-pack) v0.1.0 is the v0.5.0 acceptance test for this path. Adding it to a consumer is a one-line install:

```bash
anywhere-agents pack add https://github.com/yzhao062/agent-pack --ref v0.1.0
```

Private repos behave the same way. SSH transport (`git@github.com:owner/private.git`) succeeds when `ssh-add -L` lists a usable key. If SSH is unavailable, gh CLI takes over and succeeds when `gh auth status` reports a logged-in account with the right scope. As a third option, `GITHUB_TOKEN` succeeds when the env var holds a personal-access token with `repo` scope. See [`docs/pack-architecture.md`](pack-architecture.md) for the full chain in the order listed.

Practical effect on the decision matrix:

| Project type | Pre-v0.5.0 decision | v0.5.0+ decision |
|---|---|---|
| Paper repo (USC, NSF, Overleaf) | Stay on ac | aa + private pack via auth chain |
| Private pack (single-maintainer skills, USC templates) | Manual checkout + repo-local `skills/` | aa with SSH / gh CLI / PAT auth (one-line install) |

ac retains the rows that did not depend on a private-pack mechanism: `reference-skills/` content that is not yet repackaged as a v2 pack, and AGENTS.md private sections (USC / Overleaf / PyCharm-specific rules) that aa's sanitized mirror still strips. Repackaging a private `reference-skills/<name>/` directory as a pack consumable from aa is straightforward once v0.5.0 is in use; the skill content does not change, only the load path.

## FAQ

**Does switching lose Claude Code memory or project history?**

No. `~/.claude/projects/<project-slug>/memory/` is per-Claude-Code-project state, decoupled from bootstrap upstream. Switching upstream does not touch the memory store.

**Does `~/.claude/hooks/` change on switch?**

No. `guard.py` and `session_bootstrap.py` are byte-identical between ac and aa (STRICT parity guarantee). Bootstrap-from-either deploys the same hook bodies.

**Should `.agent-config/upstream` be committed to the project git history?**

`.agent-config/` is gitignored automatically by bootstrap on every run, so by default the upstream change does not land in your repo. If you want collaborators on a fresh clone to bootstrap from aa (rather than from whatever their local default is), commit an `agent-config.yaml` at project root with rule-pack preferences, and document the aa bootstrap URL in the project's own README. `.agent-config/upstream` itself stays local.

**Can a project pull some skills from ac and some from aa?**

Not with the current bootstrap design. Upstream is a single URL. Workarounds: (a) copy the specific ac-only skill into the project's own repo-local `skills/<name>/` directory (repo-local wins over shared on name conflict); (b) stay on ac for the whole project. There is no partial-upstream mode. See [`docs/pack-architecture.md`](pack-architecture.md) for the long-term design that replaces this workaround with a `packs:` opt-in (public or private source; v0.5.0 target).

**When does ac actually retire?**

No EOL date. Retirement is about shrinking ac's public-facing role — the shared-core scope. ac itself stays maintained as long as its private content has active users (you). Think of it as "ac's scope narrows" rather than "ac gets shut down".

**What if I need to prototype something in ac's shared-core that I do not want shipped to aa yet?**

Two paths: (a) edit in aa directly on a feature branch, ship to PyPI/npm when ready — works for most cases now that aa-first is the default direction; (b) keep the change in ac only and leave it out of aa's next sanitization sweep — works for maintainer-only content by definition, should not happen for shared-core any more.

**What breaks on a submodule-coupled repo if I flip the outer project's upstream to aa?**

Nothing automatic: submodules are separate repos with their own `.agent-config/upstream`, and bootstrap does NOT recursively walk into submodules. Flipping the outer project's upstream leaves every submodule on whatever upstream they were already on. To flip a submodule you would cd into it and run the migration separately. For co-authored paper submodules, the recommendation is to leave them on ac unless the co-PI has explicitly agreed to the switch; audit each submodule's `.agent-config/upstream` (if present) before deciding.

## When to update this file

Update when:

- ac's private content set changes materially (a new category of maintainer-only content appears, or a previously-private content type moves to aa).
- aa gains a new default-on feature that changes the user-visible delta between ac-bootstrapped and aa-bootstrapped states (rule-pack composer was the first; future features count too).
- The rollout cadence needs correction based on actual migration experience (a project type that was supposed to stay on ac turned out fine on aa, or vice versa).
- The STRICT parity gate's role shifts (for example, becoming purely informational, or being removed entirely).

Do not update for: small aa releases with no user-visible delta, typo fixes, formatting.
