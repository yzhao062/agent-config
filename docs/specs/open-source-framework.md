# anywhere-agents: Public Release Plan

## What This Is

**`anywhere-agents`** is a production agent stack for the agentic era: a maintained, opinionated configuration that turns AI coding agents into coherent infrastructure across every project, every machine, every session. Skills, guardrails, review loops, writing preferences, settings — versioned in one repo, refreshed automatically, designed to be forked and kept in sync with upstream.

The name has two layers. **Portability**: the stack runs anywhere the user works — any OS, any repo, any machine where Claude Code or Codex operates. **Openness**: the stack is battle-tested by one practitioner and published for anyone who wants a well-tested starting point they can bootstrap, evolve, and personalize into their own. It is a launchpad, not a framework.

The public release ships at `github.com/yzhao062/anywhere-agents`, distinct from the private `yzhao062/agent-config` daily driver. Others in this space (`dotagents`, `agentrc`, `agentfiles`, `agents-anywhere`) exist, but stars are not traction. This release competes on quality, curation, and the fact that the maintainer lives inside this workflow every day.

## Two-Repo Split

| Repo | Purpose | Visibility |
|------|---------|------------|
| `yzhao062/agent-config` | Personal daily driver. Contains USC-specific content, reference-skills (NSF, reimbursement), figure-references from the author's own projects, and anything else not suited for public consumption. Evolves freely. | Private (stays as-is) |
| `yzhao062/anywhere-agents` | Public release. Clean AGENTS.md, shared skills only, generic profile placeholders, LICENSE, CONTRIBUTING.md. This is what others fork or consume. | Public |

**Canonical source:** the private `agent-config` is the canonical source for shared skills and bootstrap scripts. The public `anywhere-agents` is a sanitized downstream release, not an independent fork.

**Release discipline:** when a shared skill or bootstrap script is improved in `agent-config`, the change lands in `anywhere-agents` as part of the next public release cut (batched, not same-day). If a fix originates in `anywhere-agents` via an external PR, it is backported to `agent-config` before the next public release, so the two never diverge on shared components. Same-day sync is an aspiration, not a guarantee; the release checklist enforces the invariant.

The two repos are not linked as submodules or forks — keeping them independent avoids accidental personal leaks.

## Problem

In the agentic era, AI agents are infrastructure, not plugins. A practitioner's agent setup — the skills that fire automatically, the guardrails that prevent self-harm, the review loops between models, the writing style and formatting preferences, the environment wiring — is as much a part of "how they build" as their editor and shell. Today, that infrastructure is invisible and fragmented: scattered across personal repos, copied manually, drifting silently across machines.

If you follow a practitioner whose AI agent workflow you admire, there is no good way to adopt it. You read their blog, copy-paste fragments, never get updates. `anywhere-agents` is the opposite: a maintained, forkable agent stack you can run in any project and stay in sync with the author's ongoing refinements.

## Positioning

**One line:** "An agent stack that follows you across projects. Fork it, run it in any repo, stay in sync with the maintainer."

**What it is:**
- A curated, actively maintained agent config repo
- With a bootstrap mechanism that lets other repos consume it directly or via a fork
- Shipping battle-tested skills (implement-review, dual-pass-workflow, bibref-filler, figure-prompt-builder, ci-mockup-figure)
- Shipping a battle-tested safety hook (`guard.py`) that has actually caught real destructive commands in daily use. Deliberately memorable warning messages ("STOP! HAMMER TIME! A wild git push appeared!") make the friction impossible to auto-dismiss — the kind of UX decision you do not know you need until after a near-miss.
- Written by a researcher, opinionated for research + development work
- Genuinely useful as daily-driver infrastructure, not just a demo

**What it is not:**
- Not a framework or CLI tool — no install step, no YAML manifest
- Not a universal sync tool covering every agent (Claude Code + Codex is enough; others can be added via fork)
- Not a marketplace or registry

## Distribution Model

### Path A: Consume directly

Users add the platform-specific bootstrap block to their project `AGENTS.md`.

PowerShell (Windows):

```powershell
New-Item -ItemType Directory -Force -Path .agent-config | Out-Null
Invoke-WebRequest -UseBasicParsing `
  -Uri https://raw.githubusercontent.com/yzhao062/anywhere-agents/main/bootstrap/bootstrap.ps1 `
  -OutFile .agent-config/bootstrap.ps1
& .\.agent-config\bootstrap.ps1
```

Bash (macOS/Linux):

```bash
mkdir -p .agent-config
curl -sfL https://raw.githubusercontent.com/yzhao062/anywhere-agents/main/bootstrap/bootstrap.sh \
  -o .agent-config/bootstrap.sh
bash .agent-config/bootstrap.sh
```

Every session, bootstrap refreshes `AGENTS.md`, skills, pointer commands, and settings from upstream. Customization goes in `AGENTS.local.md` (never overwritten). This is the simplest path for users who trust the upstream and want automatic updates without maintaining a fork.

**Trust tradeoff:** direct consume fetches and applies the author's current config on every session, including bootstrap script changes. Use this path only if you are comfortable receiving upstream changes automatically. If you want to review changes before they land, use the fork path below.

### Path B: Fork and track

Users who want to diverge meaningfully:
1. Fork `yzhao062/anywhere-agents` to their own GitHub account
2. Customize (edit `AGENTS.md`, add/remove skills)
3. Point their project repos at their fork
4. Pull upstream updates when desired: `git pull upstream main` and merge

Standard Git workflow. No special tooling.

### Why this works without a framework

Git already solves subscription and selective updates:
- Want all my updates? `git pull upstream main`
- Want one specific change? `git cherry-pick <sha>`
- Want to skip my changes? Do nothing
- Want to see what changed? `git log upstream/main --oneline`

No custom subscription engine needed. No `.agent-config/state.json`. No selective-update prompts. Git is the subscription model.

## What Ships in v1.0

The goal is a **new, clean repo** (`yzhao062/anywhere-agents`) that a stranger can fork or consume directly. Do not publish the private `agent-config` repo. Roughly a weekend of work.

### Phase A: Reserve the name (do first, ~60-90 min)

Before writing any code, claim the name across the major distribution points so no one else can squat during the weeks between reservation and v1.0 release. Availability verified April 2026.

The main repo lives under the personal namespace (`yzhao062/anywhere-agents`) because a personal-namespace release inherits the author's existing GitHub audience and reinforces the positioning as a practitioner's maintained stack rather than a framework.

**Essential (do all of these):**
- [ ] Create GitHub repo `yzhao062/anywhere-agents` with a placeholder README pointing to future release. Public, Apache 2.0.
- [ ] Defensive GitHub org claim: create empty `anywhere-agents` org with a README pointing to `yzhao062/anywhere-agents`. This prevents future org-name squatting without pulling the main repo into org ownership. 3 minutes, free.
- [ ] Publish placeholder `anywhere-agents@0.0.1` on npm (README only, no code; marks the name as reserved)
- [ ] Publish placeholder `anywhere-agents` 0.0.1 on PyPI (same pattern)
- [ ] Register a domain: **`anywhere-agents.dev`** recommended (available, developer-focused TLD, ~$15/year). `.io`, `.org`, `.net`, `.ai` also available; `.com` is parked for resale so skip unless worth buying.

**Strong (cheap to claim, high defensive value):**
- [ ] Claim Docker Hub user/org `anywhere-agents` (available; even if no container ships, prevents squatting)
- [ ] Create `yzhao062/homebrew-anywhere-agents` tap repo. Actually useful later: macOS users can install via `brew install yzhao062/anywhere-agents/bootstrap`.
- [ ] Reserve Read the Docs project `anywhere-agents` (available; useful if a dedicated docs site is ever wanted)

**Good (optional but brand-relevant):**
- [ ] Verify manually in a browser and claim Twitter/X handle `@anywhereagents` or `@anywhere_agents` (SPA behavior prevents automated availability check; check by hand)

**Skip:**
- winget, Chocolatey, Maven Central, crates.io, RubyGems, Snap Store, AUR. These are for compiled binaries or platform-specific distributions; a shell-script-based release does not need them. Revisit only if/when a real installer ships.

**Placeholder content for npm/PyPI:**
Both packages should be minimal. A single README that says: "This is a name reservation for the [anywhere-agents](https://github.com/yzhao062/anywhere-agents) project. No installable code is published here. See the GitHub repo for bootstrap instructions." This prevents confusion about the "no CLI" stance while preventing squatters.

### Phase B: Copy and sanitize (Day 1 morning)

Start a fresh clone of the private `agent-config`, then prune aggressively:

- [ ] **Copy:** `bootstrap/`, `scripts/guard.py`, `scripts/merge_settings.py`, `user/settings.json` (sanitized), `.claude/commands/`, `.claude/settings.json` (sanitized), `tests/`, `.github/workflows/`
- [ ] **Copy shared skills:** implement-review, dual-pass-workflow, bibref-filler, figure-prompt-builder, ci-mockup-figure. Do not ship `my-router` in v1.0 — routing is a private/power-user pattern and not part of the public release.
- [ ] **Do not copy:** `reference-skills/` (nsf-proposal-*, usc-reimbursement, etc.), `figure-references/`, `docs/superpowers/`, `CodexReview.md`, anything with personal details
- [ ] **Rewrite AGENTS.md from scratch** for the public audience. Keep the opinionated sections (Writing Defaults, Git Safety, Shell Command Style) as the product, but strip USC-specific content, Overleaf rules, and PyCharm-specific paths. Replace specific paths (`C:\Users\yuezh\...`) with platform-generic placeholders.
- [ ] **Sanitize `user/settings.json`:** remove hardcoded user paths; keep permission patterns and hook wiring.

### Phase C: Write public-facing docs (Day 1 afternoon)

- [ ] **README** with sections:
  - What this is (a maintained, forkable agent stack — portable, well-tested, ready to personalize)
  - Who this is for (researchers, devs who want a battle-tested starting point)
  - Two paths: consume directly vs fork and track
  - 10-minute quickstart for each path
  - What is opinionated and why (link to specific AGENTS.md sections)
  - What is not in scope (not a framework; related-projects link)
  - Honest limitations
- [ ] **LICENSE** (MIT or Apache 2.0)
- [ ] **CONTRIBUTING.md.** How to propose a skill improvement, how to report bugs. Explicit: customizations go in your fork, not upstream PRs.

### Phase D: Verify and launch (Day 2)

- [ ] **Fresh-machine test.** On a disposable VM or a clean Codespace, clone `anywhere-agents` from scratch, run bootstrap in a throwaway project, verify AGENTS.md + skills + settings land correctly.
- [ ] **Sweep for leaks.** Grep the published repo for `yuezh`, `USC`, `yzhao010`, `miniforge3/envs/py312`, any collaborator names. Second pair of eyes if possible.
- [ ] **Tag v1.0 and announce.** Short post on the author's usual channels. Point people to the README, not to feature lists.

### Don't do in v1.0

- [ ] No YAML manifest / `config.yaml`. Files are the config.
- [ ] No CLI beyond the shell bootstrap. The placeholder pip/npm packages exist only for name reservation.
- [ ] No selective-update tooling. Git handles it.
- [ ] No environment auto-install. README documents what tools you need; users install them.
- [ ] No multi-agent expansion. Ship Claude Code + Codex (what already works). Users forking for Cursor/Aider can add those themselves.
- [ ] No profiles system. There is one config. Forks are how other "profiles" exist.
- [ ] No marketplace, no registry, no web UI.

## Naming

**`anywhere-agents`** is the chosen name. Availability confirmed (as of April 2026):

- GitHub `yzhao062/anywhere-agents` — clean
- npm `anywhere-agents` — clean
- PyPI `anywhere-agents` — clean
- Domains `anywhere-agents.io`, `anywhere-agents.dev` — available

The private `yzhao062/agent-config` daily-driver repo keeps its existing name.

## Related Projects

A brief section in the README that acknowledges the space without being deferential:

> Other projects in this space take a framework or CLI approach — for example, [iannuttall/dotagents](https://github.com/iannuttall/dotagents), [microsoft/agentrc](https://github.com/microsoft/agentrc), and the `agentfiles` PyPI package. If you want a general-purpose multi-agent sync tool, those may fit better. This repo takes a different approach: it is a published, maintained, opinionated configuration — not a tool that manages configurations. Fork it if you like my setup; use one of the tools above if you want a universal manager.

One paragraph. Not a long comparison table. Users who care about alternatives will click through.

## Success Criteria

Not adoption numbers. Not GitHub stars. Success is:

1. **The private `agent-config` remains useful to the author.** Continues to work as daily infrastructure across 10+ personal repos. This is non-negotiable; the public release must never compromise the private workflow.
2. **A stranger can fork `anywhere-agents` and get value within 30 minutes.** README is clear enough, defaults are sane enough, bootstrap works on Linux + Windows without hand-holding.
3. **When others fork, they can track upstream without pain.** Merge conflicts on their customized sections should be rare. Section boundaries in `AGENTS.md` should be clean so `git merge` rarely conflicts on non-edited sections.
4. **No personal content leaks into the public repo.** Zero hits for USC-specific terms, collaborator names, or personal paths in the v1.0 release.

If all four hold, the release is successful regardless of star count.

## Maintenance Promise

Be explicit in the README about what is and is not maintained:

- **Maintained:** the author's daily-use workflow. Changes land when the author needs them.
- **Not maintained:** feature requests that do not match the author's work. Users should fork.
- **Best-effort:** bug reports, PRs for clear improvements, documentation fixes.

This prevents the "framework maintainer burnout" failure mode: no promises beyond what is sustainable for a single maintainer.

## Risks

| Risk | Mitigation |
|------|------------|
| Users expect ongoing support / feature requests | Maintenance Promise section sets expectations. |
| Personal details leak in v1.0 | Two-repo split isolates private content. Pre-release grep sweep for `yuezh`, `USC`, `yzhao010`, personal paths. Second pair of eyes. |
| Drift between private `agent-config` and public `anywhere-agents` | Private is the canonical source; public is a sanitized downstream release. Every public release cut backports any external PRs from public to private, so the two never diverge on shared components. Release checklist enforces this invariant. |
| Bootstrap has bugs on fresh systems | CI already tests on Ubuntu + Windows. Add a fresh-machine simulation test before v1.0. |
| Consumer accidentally commits `.agent-config/` to their repo | Bootstrap already appends to `.gitignore` automatically. Keep that. |
| AGENTS.md structure changes break existing forks' rebase workflow | Keep section boundaries stable across versions. When renaming or restructuring sections, call it out in release notes so fork maintainers can plan. |
| Name squatted before v1.0 release | Phase A reserves name on GitHub, npm, PyPI within 30 minutes. |

## Timeline

A weekend is realistic for v1.0:

- **Day 1 morning:** audit and strip personal identifiers; prune reference-skills
- **Day 1 afternoon:** write README, LICENSE, CONTRIBUTING.md
- **Day 2 morning:** test fork-and-consume workflow on a fresh throwaway repo; fix anything broken
- **Day 2 afternoon:** release v1.0, tag, write a brief announcement post

Nothing beyond this is required to launch. Everything else is polish.
