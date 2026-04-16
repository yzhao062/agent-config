# agent-config: Open-Source Validation Spec

## Problem

AI coding agents now have first-party configuration mechanisms: Claude Code has scoped `CLAUDE.md`, `@path` imports, `.claude/rules/`, skills, hooks, agents, plugins, and auto memory; Codex and other tools increasingly use `AGENTS.md`; Cursor has user and project rules. The remaining gap is narrower but still real: power users and small teams who work across many repositories need a low-friction way to keep their agent instructions, skills, settings, and review workflows consistent without manually copying files or maintaining divergent forks.

The target user is a developer or small team with at least 5 active repositories, repeated agent setup work, and a small set of shared workflows that must stay synchronized.

### Distribution advantage

This project follows the **dotfiles model**: a practitioner with social credibility shares a battle-tested, daily-use setup, and others fork and customize. The value is not just the sync infrastructure; it is the curated defaults, opinionated skill protocols, and refined workflows that come from months of real use across 10+ repos. When a recognized researcher or developer publishes "here is exactly how I configure my AI agents," the community adopts it the way they adopt prominent dotfiles, LaTeX templates, or training configs. This social distribution channel means initial adoption is less speculative than a cold-start framework launch.

## Market Reality / Alternatives

Before building, acknowledge what already exists and where this project fits:

| Alternative | What it covers | Gap this project fills |
|-------------|---------------|----------------------|
| **Claude Code scoped CLAUDE.md + imports + plugins** | Per-project and per-user config, plugin marketplaces, skill auto-discovery | No cross-repo sync from a single source of truth. Plugins are distribution, not personalized config sync. |
| **claude-code-templates** (100+ agents/commands) | Broad catalog of starter templates | Static templates, no ongoing sync. Once copied, they drift. |
| **AGENTS.md / Agent Rules spec** | Cross-agent instruction file convention | Convention only. No sync mechanism, no override layers, no skill distribution. |
| **Agent Skills / agentskills.io** | Standardized SKILL.md format, marketplaces, installers | Skill format and discovery, not config sync. No bootstrap into consuming repos. |
| **Cursor user/project rules** | Cursor-specific rule files | Single-agent, no cross-repo sync. |
| **destructive_command_guard (dcg)** | Safety hooks for destructive commands (821 stars) | Well-covered. Not a differentiator for this project. |

**The wedge in one sentence:** Fork this repo, get a battle-tested agent setup that stays up to date; override anything you disagree with, and your overrides are never touched by sync.

This is not a marketplace or a universal skill standard. It fills the gap between "I have my config" and "all my repos use it consistently, and I can still diverge per project."

## Product Vision

**agent-config** is an opinionated sync layer for agent configuration. It starts as a template and bootstrap flow that distributes AGENTS/CLAUDE instructions, selected skills, command pointers, and settings into consuming repositories. A YAML manifest, generated AGENTS.md, configurable hooks, and broader orchestration are deferred until external users show that the simpler sync layer is not enough.

Positioning: not an "awesome prompts" collection, not another skill format, and not a replacement for Claude Code plugins or AGENTS.md. The wedge is a battle-tested, opinionated agent setup from a practitioner who uses it daily, packaged so others can fork, customize, and keep their repos in sync with minimal ceremony. The sync infrastructure is the mechanism; the curated defaults and skill protocols are the draw.

## Design Principles

1. **Fork and edit.** Users fork the template repo and directly edit AGENTS.md and skills. No config.yaml parser, no template engine, no code generation. The files in the repo are the files that get synced.
2. **Additive override layers.** Consumer repos get the synced AGENTS.md but can override anything via `AGENTS.local.md`. Project-local `skills/<name>/SKILL.md` overrides same-name bootstrapped skills. Layers are clear and predictable.
3. **No new runtime dependency.** Bootstrap is pure shell (bash + PowerShell). Settings merge uses Python only if available; otherwise existing files are left untouched. No pip install, no npm install, no CLI.
4. **Skill-format compatible.** Skills use the SKILL.md convention (compatible with agentskills.io). The project does not invent a new format.
5. **Agent-neutral where possible.** Core infrastructure works for any agent that reads markdown instruction files. Agent-specific wiring (Claude Code pointer commands, Codex openai.yaml wrappers) is a thin layer on top.

## Architecture

### Repo types

```
┌─────────────────────────────┐
│  agent-config (template)    │  ← open-source template repo
│  - AGENTS.md (hand-edited)  │
│  - skills/ (built-in)       │
│  - bootstrap/ (sync engine) │
│  - scripts/ (merge, guard)  │
└──────────┬──────────────────┘
           │ user forks
           ▼
┌─────────────────────────────┐
│  user's config repo         │  ← user's fork (private or public)
│  - AGENTS.md (customized)   │
│  - skills/ (built-in + own) │
│  - bootstrap/ (unchanged)   │
└──────────┬──────────────────┘
           │ bootstrap syncs into
           ▼
┌─────────────────────────────┐
│  consuming project repo     │  ← any project that uses the config
│  - AGENTS.md (synced copy)  │
│  - .agent-config/ (cached)  │
│  - AGENTS.local.md (local)  │
│  - skills/ (project-local)  │
└─────────────────────────────┘
```

### Override hierarchy (lowest to highest priority)

```
Template defaults (built-in skills, default AGENTS.md)
  < User's fork (customized AGENTS.md, added/removed skills)
    < Project AGENTS.local.md (consuming project)
      < Project-local skills/ (consuming project)
```

## Bootstrap Engine

### Flow

Bootstrap is the same proven mechanism already running in this repo. No config.yaml parsing, no template rendering. Just fetch and copy.

```
Consumer repo runs bootstrap.sh / bootstrap.ps1
  │
  ├─ 1. Download bootstrap script from user's config repo
  ├─ 2. Sparse-clone user's config repo into .agent-config/
  ├─ 3. Copy AGENTS.md to consumer repo root (overwrite)
  ├─ 4. Copy .claude/commands/ pointer files (non-destructive)
  ├─ 5. Deep-merge .claude/settings.json (project level, Python if available)
  ├─ 6. Deep-merge ~/.claude/settings.json (user level, Python if available)
  ├─ 7. Deploy guard.py to ~/.claude/hooks/ (if present in config repo)
  ├─ 8. Add .agent-config/ to .gitignore
  └─ 9. Report: "bootstrap: synced AGENTS.md, N skills, settings"
```

### Idempotency

Bootstrap runs every session. It must be safe to run repeatedly:
- AGENTS.md is overwritten (local overrides go in AGENTS.local.md)
- Settings merge preserves project-only keys
- Pointer file copy is non-destructive (does not delete project-local commands)
- .gitignore append is idempotent (checks before adding)

### Bootstrap block for consumer repos

Consumer repos embed this in their AGENTS.md (same pattern as today):

````
## Shared Agent Config (auto-fetched)

PowerShell (Windows):

```powershell
New-Item -ItemType Directory -Force -Path .agent-config | Out-Null
Invoke-WebRequest -UseBasicParsing `
  -Uri https://raw.githubusercontent.com/<user>/<config-repo>/main/bootstrap/bootstrap.ps1 `
  -OutFile .agent-config/bootstrap.ps1
& .\.agent-config\bootstrap.ps1
```

Bash (macOS/Linux):

```bash
mkdir -p .agent-config
curl -sfL https://raw.githubusercontent.com/<user>/<config-repo>/main/bootstrap/bootstrap.sh \
  -o .agent-config/bootstrap.sh
bash .agent-config/bootstrap.sh
```
````

The URL points to the user's config repo fork, not the template repo. This way users control what their projects get.

## Skill System

### Skill layout

Each skill follows this structure (compatible with agentskills.io):

```
skills/<skill-name>/
├── SKILL.md              # primary definition (required)
├── agents/
│   └── openai.yaml       # Codex/OpenAI thin wrapper (optional)
├── references/            # supporting docs read by the skill
├── scripts/               # automation scripts
└── assets/                # templates, examples, reference banks
```

### Skill types

| Type | Source | Override behavior |
|------|--------|-------------------|
| **Built-in** | Template repo `skills/` | Comes with the fork; user can delete or modify |
| **User-added** | User adds to their fork `skills/` | Synced to consumer repos via bootstrap |
| **Project-local** | Consumer repo `skills/` | Highest priority; overrides any same-name skill |

### Skill discovery order

When the user or agent invokes a skill:
1. `skills/<name>/SKILL.md` (project-local) -- highest priority
2. `.agent-config/repo/skills/<name>/SKILL.md` (bootstrapped from config repo)
3. If not found, report that the skill is not available.

### Pointer commands

For Claude Code, each skill gets a pointer file in `.claude/commands/<skill-name>.md`:

```markdown
Read and follow the skill definition. Look for it at `skills/<skill-name>/SKILL.md` first,
then `.agent-config/repo/skills/<skill-name>/SKILL.md`.
```

Bootstrap copies these from the config repo. Non-destructive: does not delete project-local commands.

### Adding a custom skill (user workflow)

```bash
# In your config repo fork:
mkdir -p skills/my-custom-skill
$EDITOR skills/my-custom-skill/SKILL.md

# Create a pointer command
cat > .claude/commands/my-custom-skill.md << 'EOF'
Read and follow the skill definition at `skills/my-custom-skill/SKILL.md`.
EOF

# Commit and push. Consumer repos pick it up on next bootstrap.
```

## Built-in Skills

The template ships with a small set of high-quality, domain-neutral skills. Users can delete any they do not want.

### implement-review

Structured dual-agent review loop (Claude Code implements, Codex reviews).
- Phases: prerequisites, pre-review checks, prepare review, intake feedback, revise, conclude
- Content-type detection: code, paper, proposal, general
- Review lenses: code (Google/Microsoft), paper (NeurIPS/ICLR), proposal (NSF/NIH), general
- Focused sub-lenses: code/security, paper/formatting, proposal/compliance, etc.
- Round history tracking: prevents re-litigation of resolved findings
- Terminal relay (default) and plugin path

This is the project's most differentiated skill. No equivalent exists as a packaged, reusable protocol.

### dual-pass-workflow

Generic two-pass pattern (build then audit).
- Pass 1: implement / draft
- Pass 2: verify / refine using a second agent or self-review
- Configurable verification contracts per content type

### bibref-filler

Safe citation filling with verification.
- Never fabricate references
- Machine-added entries go to separate working.bib
- Leave visible TODOs for uncertain claims

## Settings Merge

### Strategy

Deep merge with these rules:
- Objects merge recursively (nested keys from both sides preserved)
- Arrays deduplicate by value (set union)
- Scalars: config repo value wins over consumer project value for shared keys
- Project-level `.claude/settings.local.json` wins over merged result

### Merge targets

| Target | Source | Trigger |
|--------|--------|---------|
| `.claude/settings.json` (project) | Config repo `.claude/settings.json` | Every bootstrap |
| `~/.claude/settings.json` (user) | Config repo `user/settings.json` | Every bootstrap |

### Implementation

Python script (`scripts/merge_settings.py`). If Python is unavailable, existing settings files are left untouched and bootstrap prints a warning. No pip dependencies required (stdlib json module only).

## What Stays Out

| Component | Reason |
|-----------|--------|
| **config.yaml / YAML manifest** | Deferred. Users edit files directly. Manifest-driven generation is a framework feature for post-validation. |
| **Generated AGENTS.md / Jinja2** | Deferred. AGENTS.md is hand-edited in the fork. |
| **Router / auto-dispatch** | Personal productivity tool for users with many skills. Not part of the open-source scope. Users who want routing can create their own router skill. |
| **reference-skills/** (nsf-proposal-*, usc-reimbursement, etc.) | Too domain-specific. Document as examples of what user-added skills look like. |
| **figure-references/** | Personal asset gallery. Document as example of how to build one. |
| **guard.py** | Ship as optional (included in template but clearly marked). Users can delete it or use dcg instead. |
| **Codex MCP integration details** | Platform-specific, changes frequently. Document in a guide, not in the template AGENTS.md. |
| **Overleaf merge conflict rules** | Niche workflow. Belongs in user's fork or AGENTS.local.md. |

## Validation MVP

### Ship first

- [ ] Publish a clean template config repo with a hand-edited AGENTS.md. Keep the opinionated sections (Writing Defaults, Git Safety, Shell Command Style) as curated defaults that users can modify, not as blank placeholders. The opinionated setup is the product. Replace only truly personal content (specific paths, institutional details) with clear placeholders.
- [ ] Keep bootstrap scripts close to the current implementation: fetch the config repo, refresh AGENTS.md, sync skills in `.agent-config/`, generate Claude command pointers, merge settings where Python is available, add `.agent-config/` to `.gitignore`
- [ ] Ship built-in skills: implement-review, dual-pass-workflow, bibref-filler. Include documentation that users can delete any they do not want.
- [ ] Ship settings merge script (stdlib Python only, no pip dependencies)
- [ ] Ship guard.py as optional (clearly marked, easy to remove)
- [ ] Tests: bootstrap contract on Windows and Linux, idempotent .gitignore, non-destructive command copy, settings merge preservation
- [ ] README: concrete "who this is for" section, 10-minute quickstart, architecture diagram, known alternatives with honest comparison, limitations section
- [ ] LICENSE (Apache 2.0)
- [ ] CONTRIBUTING.md: how to add a skill, how to customize AGENTS.md, how to report issues

### Adoption gates (before building framework features)

These gates must pass before investing in config.yaml, generated AGENTS.md, registry, or other framework features:

- [ ] At least **5 external users or teams** using it in real repos (not stars, actual bootstrap usage)
- [ ] At least **3 concrete requests** for manifest-driven customization ("I want config.yaml because editing AGENTS.md directly is ...")
- [ ] At least **2 reports** that manual template editing is the blocker preventing adoption

### Defer until gates pass

- [ ] `config.yaml` schema and parser
- [ ] Generated AGENTS.md from template engine
- [ ] `agent-config init` CLI
- [ ] Community skill registry (install skills by URL/name)
- [ ] Gemini CLI support (GEMINI.md generation)
- [ ] Configurable guard hook deployment
- [ ] CI workflow template for consuming repos

### Out of scope (future, if ever)

- [ ] Web UI for config editing
- [ ] Skill marketplace
- [ ] Team/org config inheritance (org < team < personal)
- [ ] Auto-detection of config repo changes and re-bootstrap

## Open Questions

1. **Naming**: "agent-config" is descriptive but generic. Check for name conflicts on GitHub/npm/PyPI. Alternatives: "agent-sync", "agentstrap" (bootstrap + agent), "configpilot."
2. **License**: Apache 2.0 (permissive, patent grant) or MIT (simpler)? Apache 2.0 is more common for infrastructure projects.
3. **Template vs org**: Publish as a GitHub template repo (users fork via `gh repo create --template`) or as a GitHub org with the template? Org allows future repos (docs, community skills) without cluttering the main repo.
4. **AGENTS.md sections to keep**: The dotfiles model says keep the opinionated sections (Writing Defaults, Formatting Defaults, Git Safety, Shell Command Style) as the curated product. Strip only personal identifiers (paths, institutional details). The README should frame these as "the author's daily-use defaults, refined over months" rather than "generic framework defaults." Users fork and edit to taste.
5. **Codex dependency**: implement-review assumes a Codex terminal or plugin for the reviewer role. Should the skill also support self-review (Claude Code reviews its own work) for users who do not have Codex? This would broaden the audience but weaken the dual-agent value proposition.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Only the author uses it | Medium | High | Author has social credibility and active followers. Dotfiles-model distribution lowers cold-start risk. Validation gates still apply before framework investment. If gates do not pass in 6 months, archive and move on. |
| Claude Code plugins/marketplace subsume the sync use case | Medium | High | Monitor Claude Code plugin evolution. If org-wide CLAUDE.md lands natively, this project becomes unnecessary for Claude-only users. Cross-agent sync remains the wedge. |
| Maintenance burden exceeds value | Medium | Medium | Keep scope minimal. No generated files, no CLI, no registry until gates pass. |
| Users want more customization than "fork and edit" | Medium | Low | This is the signal to build config.yaml. It is a feature request, not a risk. |
| Bootstrap breaks on a new OS/shell version | Low | Medium | CI tests on Ubuntu + Windows. Bootstrap scripts are simple (curl/sparse-clone/copy). |
