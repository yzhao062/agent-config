# AGENTS.md diet: rule-preservation checklist

Workstream: put the always-loaded rule files on a diet (plan: `PLAN-agents-md-diet.md`, plan-review concluded 2026-09-17 after six rounds with Codex and Antigravity). This file is the Phase 1 acceptance artifact required by plan section 4.2: every instruction sentence and table row of the pre-rewrite `AGENTS.md` (commit `0cc669b`, 74,579 bytes, 499 lines) mapped to where it lives after the rewrite. Reviewers read it beside the diff.

Dispositions: **KEPT** (in the shared `AGENTS.md`, section named), **MOVED** (to a public docs page in `anywhere-agents/docs/`, written in Phase 3), **SCRIPT** (implemented by `scripts/render_banner.py`, Phase 2), **LOCAL** (`agent-config/AGENTS.local.md`), **PACK** (already delivered to consumers by a public agent-pack pack), **DELETED** (with the reason). Line numbers refer to the old file.

## Preamble (lines 1–9)

| Old lines | Instruction | Disposition |
|---|---|---|
| 3 | Determine your context before proceeding | KEPT, preamble |
| 5 | Source repo test with three markers (`bootstrap/bootstrap.sh`, `bootstrap/bootstrap.ps1`, `reference-skills/`); skip bootstrap; proceed to Session Start Check | KEPT, preamble, with a marker set that holds in both source repos (`scripts/generate_agent_configs.py` and `skills/` replace `reference-skills/`) |
| 7 | Consumer path: execute bootstrap every session, idempotent, report the result in one line | KEPT, preamble |
| 9 | Maintainer onboarding pointer to `ONBOARDING.md` | LOCAL |

## Bootstrap: Shared Config and Skills (lines 11–93)

| Old lines | Instruction | Disposition |
|---|---|---|
| 13–14 | This file is the shared configuration hosted at agent-config; project repos include the block | KEPT, "Bootstrap" lead sentence, naming anywhere-agents (no consumer bootstraps from agent-config) |
| 16–18 | Copy the block into each project's `AGENTS.md`; overrides go in `AGENTS.local.md` | KEPT, "Bootstrap" lead sentence and rule 2 |
| 21–39 | The bootstrap block itself (PowerShell and Bash commands) | KEPT verbatim, with anywhere-agents raw URLs |
| 41 | Bootstrap rewrites the root `AGENTS.md` every run, composes passive packs, preserves a composed file when composition cannot run, warns and records `completed: false`; overrides in `AGENTS.local.md` | KEPT, Bootstrap rules 1 and 2 |
| 43 | Read `.agent-config/AGENTS.md` as baseline; `AGENTS.local.md` overrides | KEPT, inside the block |
| 44 | Skill lookup order (three paths) | KEPT once, "Skills" bullet 1 (the duplicate copies in Task Routing, Local Skills Precedence, and Cross-Tool Skill Sharing collapse into it) |
| 45 | Copying shared commands overwrites same-named files only and does not delete unrelated project-local commands | KEPT, Bootstrap rule 3 |
| 46 | Settings merge: shared keys updated, project-only keys preserved; `merge_settings.py`; PowerShell fallback | KEPT as a rule (Bootstrap rule 4); the script names MOVED to `docs/agents-md.md` |
| 47 | Add `.agent-config/` and `agent-config.local.yaml` to `.gitignore`; the three generated files too; never untrack a tracked one automatically; `AGENT_CONFIG_TRACK_GENERATED` | KEPT, Bootstrap rule 6 (`.agent-config/`, `agent-config.local.yaml`, and the generated files gitignored; a generated file never untracked automatically); the env var and the two-machines explanation MOVED to `docs/agents-md.md` |
| 48 | User-level setup: `guard.py`, `statusline.py`, `agent-quota.py`, `user/settings.json` merge, `CLAUDE_CODE_EFFORT_LEVEL=max`; remove the section if unwanted | KEPT, Bootstrap rule 5; the opt-out sentence MOVED to `docs/agents-md.md` |
| 49 | `last-run.json` semantics, `completed: false`, `last_phase`; `pack-lock.json` records the heal pass | KEPT in Bootstrap rule 1 (`completed: false` in `last-run.json`); the rest MOVED to `docs/agents-md.md` |
| 52–61 | "What gets shared" table, including the skill roster by name | MOVED to `docs/agents-md.md`. The roster was the line `scripts/pre-push-smoke.sh` and `scripts/remote-smoke.sh` relied on when they ask an agent to list the shipped skills "from your agent config"; the shared file now names the lookup paths instead, and a `codex exec` probe on 2026-09-17 with the rewritten file listed all ten `skills/` directories by following them, so the smoke prompts stay as they are |
| 63–69 | Override rules: `AGENTS.local.md` wins; do not edit the generated root file; project-local skill wins; shared settings keys updated every run, override in `.claude/settings.local.json`; pack-deployed copy before bootstrapped | KEPT: Bootstrap rule 2 and 4, Skills bullets 1 and 2 |
| 71–93 | Configuration Precedence: three layers, the four-row rule-file table, the `GENERATED FILE` header preservation with rename advice, settings precedence, effort precedence | KEPT, "Configuration Precedence" (table, preservation sentence, one line each for settings and effort), plus the corrected statement that Codex loads only `AGENTS.override.md` or `AGENTS.md` and never `agents/codex*.md` on its own (plan 4.2, after the outline) |

## Consumer Repo Layout (lines 95–132)

| Old lines | Instruction | Disposition |
|---|---|---|
| 97–98, 102–110 | Layout table (what is tracked, gitignored, seeded) | MOVED to `docs/agents-md.md` |
| 112–120 | Generated files are not tracked; a repo that already tracks one is left alone; committing them is an operator decision | KEPT, Bootstrap rule 6; rationale MOVED |
| 122–124 | `agent-config.yaml` uses `packs:`; `rule_packs:` deprecated and hard-fails at v1.0.0 | KEPT, Bootstrap rule 6 (`packs:`, `rule_packs:` deprecated); the version schedule MOVED |
| 126–132 | `todo/` is the drop box: a person copies files in, agent reads or moves them; resting state empty; bootstrap seeds its README; `AGENT_CONFIG_NO_TODO_DROPBOX=1`; agent output goes to the scratchpad | KEPT, Bootstrap rule 6 (drop box for people, scratchpad for agents); README seeding and the env var MOVED to `docs/agents-md.md` |

## Session Start Check (lines 134–186)

| Old lines | Instruction | Disposition |
|---|---|---|
| 136 | Mandatory turn-start procedure, branch by runtime | KEPT, "Session Start Check" first sentence |
| 138–141 | Claude Code: per-project flag files, root discovery by walking up, emit when event newer than acknowledgement or acknowledgement absent, write the `ts`, otherwise skip | KEPT, "Session Start Check" (root walk, the event-versus-acknowledgement condition, the `ts` copy) |
| 143 | Hook writes the event on `startup`, `resume`, `clear`; skips on `compact`; 10-second debounce; per-project isolation | KEPT as behavior ("the `compact` source and the debounce do not re-fire"); mechanism detail MOVED to `docs/session-banner.md` |
| 145 | Source repo branch: gate not active; emit on the first response; compact/resume/clear indistinguishable | KEPT ("In a source repo, run `scripts/render_banner.py` ... on the first reply") |
| 147 | Codex has no SessionStart hook; each invocation is a new session; emit on the first response | KEPT with the corrected fact (Codex 0.153.3+ has hooks, not wired yet; first reply of the invocation); closes aa#50's stale sentence |
| 149 | The procedure overrides skill-first or task-first behavior | KEPT ("Before the first content of a reply") |
| 151–163 | Banner format and the "replace `all clear` with issues" rule | SCRIPT: the renderer owns the format; `docs/session-banner.md` documents it |
| 165–172 | How to populate OS, Claude Code (version, latest, auto-update, model, effort), Codex (version, config keys, floors, drift policy), Skills (three buckets with shadowing), Hooks, Session check (workflow pins) | SCRIPT (all six fields); the Codex drift policy text is KEPT in "Environment" (model, tier, effort, `ultra`); the CLI floor history MOVED to `docs/codex.md` |
| 174–186 | Pack deployment counts: user packs, project packs with seeds and layer replacement, gap and update counts, emit lines | SCRIPT (the pack-identity helper beside the renderer implements exactly this); `docs/session-banner.md` documents it |

## User Profile, Agent Roles, Fungibility, Memory, Routing (lines 188–223)

| Old lines | Instruction | Disposition |
|---|---|---|
| 190 | User-level defaults reusable across projects unless a local rule is stricter | DELETED as a sentence; the precedence table already says local rules win |
| 191–192 | The user is a CS professor in ML/AI; common tasks are papers, proposals, scientific and administrative writing | LOCAL (also PACK: `profile`); the shared file keeps a one-line `## User Profile` placeholder that tells a fork to describe its user (plan row 14) |
| 196–198 | Claude Code primary, Codex gatekeeper, default division unless overridden | KEPT, "Agent Roles" |
| 202–208 | Fungibility: absence and reversal scenarios; core functions reachable via primitives; hard-coded CLI documents the other side; docs name the cross-vendor equivalent near the top; deferred half may ship later | KEPT, "Agent Roles" bullets 3 and 4 |
| 212–214 | Prefer version-controlled files for durable context; agent memory only for short local convenience; never the sole home | KEPT, "Memory and Persistence" |
| 218–220 | Read the router first through the lookup order; do not ask which skill when the table is clear; superpowers outer loop; ask when ambiguous | KEPT, "Task Routing" bullet 1 |
| 222–223 | No fan-out on own initiative; propose `prun` or Workflow; honor a chosen route; a bounded helper is not fan-out | KEPT, "Task Routing" bullet 3 (the 2026-09-13 incident date MOVED to `docs/guard-hook.md`) |

## Codex MCP Integration (lines 225–256, codex-tagged)

| Old lines | Instruction | Disposition |
|---|---|---|
| 227–231 | Register Codex as an MCP server in Claude Code; prerequisites | DELETED: the route is unused (17 MCP sessions in 3,009; maintainer confirmed); MOVED as history to `docs/codex.md` |
| 232–242 | Recommended `config.toml` (model, effort, tier, fast_mode, conversationDetailMode) | KEPT, "Environment" Codex bullet (model, tier, fast_mode, effort); `conversationDetailMode` MOVED to `docs/codex.md` |
| 243–245 | CLI floors per model generation; `npm install -g @openai/codex@latest`; Codex reserved for `/vet`, `prun` uses Agy | Floors MOVED to `docs/codex.md`; "Codex is reserved for `/vet`" KEPT in "Agent Roles" and "Task Routing"; `prun` on Agy KEPT in "Task Routing" |
| 246–248 | Service tiers, price multipliers, sources, `fast` dial-up, dispatcher ignores user config, `CODEX_DISPATCH_ISOLATE_MCP` | Tier and dispatcher-isolation rule KEPT in one Environment sentence; multipliers, sources, and profiles MOVED to `docs/codex.md` |
| 249–252 | `model_reasoning_effort` not validated client-side; `max` and `ultra` accepted; `ultra` enables delegation; check the rollout; dispatcher keeps `xhigh` floor | `xhigh` default, `max` dial-up, `ultra` semantics KEPT in "Environment"; the rollout inspection and the rest MOVED to `docs/codex.md` |
| 253 | `conversationDetailMode` | MOVED to `docs/codex.md` |
| 254–256 | Windows PATH note for MCP; `approval_policy=never` for MCP and `on-request` for interactive; prefer terminal over MCP on Windows | `approval_policy = "on-request"` for interactive sessions KEPT in "Environment"; the MCP notes DELETED with the route (history in `docs/codex.md`) |

## Writing and Formatting Defaults (lines 258–284)

| Old lines | Instruction | Disposition |
|---|---|---|
| 260–267 | Accessible language, no oversimplifying, technical detail, accuracy, consistent terms and abbreviations, verify citations, BibTeX, code only when necessary | KEPT, "Writing Defaults" |
| 268–269 | NSF and non-federal solicitation rule on DEI terms | PACK: `paper-workflow` carries both branches; the compact `profile` gains the non-federal branch (Phase 3b) |
| 270 | Banned AI-tell list | KEPT verbatim, with aa's "trim or extend in your fork" clause |
| 274–284 | Preserve format; no prose-to-bullets; full forms; `e.g.,`/`i.e.,`; no U+202F; dash rule with the allowed cases; split long sentences; vary structure and openers; no transition overuse; no summary tails; no antithesis; copy-paste block rule; long drafts in a `.md` file with the Outlook/Gmail note | KEPT, "Formatting Defaults" (every directive; explanations shortened; test-pinned phrases verbatim) |

## Git Safety and Mechanical Enforcement (lines 286–376)

| Old lines | Instruction | Disposition |
|---|---|---|
| 288–290 | Never commit or push without approval; non-negotiable; every variant listed | KEPT, "Git Safety and Mechanical Gates" first paragraph |
| 294 | Bootstrap deploys `guard.py` as a PreToolUse hook | KEPT |
| 296–307 | Gate table (ten rows) | KEPT verbatim in substance; the banner row and the classifier row shortened to their trigger and action |
| 309 | Mandatory risk classification: one classifier, exact leading token, wrappers seen through, opaque `python -c` and private wrappers, not disabled by any env, sole risk arbiter | KEPT in the paragraph after the table |
| 311–313 | The advisory reports and does not deny, why, cap of five, shares `AGENT_STYLE_HOOK`; the measurement of how findings reach the model; RULE-G left out | Advisory behavior KEPT in the table row; the rationale and the measurement MOVED to `docs/guard-hook.md` |
| 315 | Both writing guards skip an `agent-io` path; the marker's two trust depths; carried text goes to the scratchpad; an unmarked path is scanned | KEPT (the `agent-io` rule in one sentence); the measurement and the bypass argument MOVED to `docs/guard-hook.md` |
| 317–333 | Nested `git init` is denied: the IDE argument, the measured incident, the escape env for a deliberate inner repository | The gate and its escape KEPT in the tables; the argument MOVED to `docs/guard-hook.md` |
| 335–356 | The gate declines shapes it cannot parse (heredocs, redirections, escaped quotes, comments, PowerShell block comments) and why | MOVED to `docs/guard-hook.md` (the deny message itself carries the reroute at the point of use) |
| 358 | Round 6 noise audit: deny messages carry `Suggested rewrite:`; destructive operations stay `ask` | KEPT as the deny-versus-ask criterion sentence; history MOVED |
| 360–368 | Escape hatches table and disable values | KEPT verbatim |
| 370 | The mandatory risk set is not bypassable; `_ESCAPE_HATCH_ENV_NAMES` test | Rule KEPT; the test reference MOVED to `docs/guard-hook.md` |
| 372 | Set a narrow escape for a meta-discussion write; prefer the narrowest env; remove it after the write | KEPT |
| 374–376 | Fan-out stays a written rule; sharpen prose instead of adding a hook | KEPT in one sentence |

## Shell Command Style, Tool-Use Reliability, GitHub Actions (lines 378–407)

| Old lines | Instruction | Disposition |
|---|---|---|
| 380–388 | All seven bullets: no compound `cd` (git -C, path as argument); read-only list; always-approve list; `cp`/`mv` for scratch, tracked moves reviewed; no nested PowerShell `-Command` with `$`; no delete-then-rewrite of a scratch dir; no inline Python with `#` comments | KEPT, "Shell Command Style" (seven bullets, examples shortened) |
| 392–393 | Retry once and try an alternate read path before reporting a file unreadable; report which paths were tried; same for other transient failures unless deterministic | KEPT, "Tool-Use Reliability" |
| 397–407 | Node.js 24 rollout narrative, the minimum-version table, SHA pins flagged for manual review, newest-major as a separate upgrade, self-hosted runner reminder | Table and the three qualifications KEPT in "Environment"; the dated narrative DELETED (past tense as of 2026-09) |

## Environment Notes (lines 409–431)

| Old lines | Instruction | Disposition |
|---|---|---|
| 411–416 | Miniforge preference, mamba over conda, `py312` first, do not conclude Python is missing from PATH failures, the two Miniforge path patterns, inspect environments and IDE settings | KEPT, "Environment" bullet 1 (generic form, with the `AGENTS.local.md` interpreter rule); `py312` LOCAL |
| 417 | PyCharm default interpreter | LOCAL |
| 418 | `gh` for PR and issue workflows; install and `gh auth login` reminder | KEPT, "Environment" bullet 2 |
| 419–421 | Console windows flashing during Windows test runs and the two measures | MOVED to `CONTRIBUTING.md` in anywhere-agents (a note about this repository's test suite) |
| 423–431 (claude-tagged) | Prefer the native installer; migration commands from npm and winget; release channel; `claude doctor` and `claude update`; disabling auto-update; the effort slider history and the `CLAUDE_CODE_EFFORT_LEVEL=max` env with its precedence | Native installer, auto-update, `claude doctor`/`claude update`, and the effort env rule KEPT in "Environment" bullet 3; migration commands, channel setting, disable instructions, and the version history MOVED to `docs/install.md` |

## Submodule Workflow and Overleaf (lines 433–476)

| Old lines | Instruction | Disposition |
|---|---|---|
| 435–443 | Submodules exist for shared dirs; run `git submodule status` at session start and warn on `-`; submodules have their own remotes; every write is high-risk; fetch/status/log check before writes; `git -C`; confirm before commit, push, pull, reset; update the parent pointer; internal-only files may be absent on a fresh clone; `context/` syncs; project-specific detail belongs in the project's rule file | PACK: `paper-workflow` carries all of it; the compact variant (Phase 3b) keeps each rule and corrects the pointer to `AGENTS.local.md`. Neither source repo has submodules |
| 447–476 | Overleaf merge conflict resolution: why "theirs" is an older base; co-PI content priority; the six numbered rules; the pre-merge checklist; recovery from `--theirs` | PACK: `paper-workflow` (compact variant keeps the numbered rules, checklist, recovery line, and one sentence of the why) |

## Local Skills Precedence and Cross-Tool Skill Sharing (lines 478–499)

| Old lines | Instruction | Disposition |
|---|---|---|
| 480–488 | Repo-local skills are the source of truth; the lookup order; read local references first; do not modify a global skill that a local one shadows; say briefly that the local copy is in use | KEPT, "Skills" bullets 1 and 2 |
| 492–498 | Skills shared across agents; `SKILL.md` single source, wrappers thin; slash-command pointers reference `SKILL.md`; pack-deployed location; bootstrap copies only shared pointers and does not delete others; edit `SKILL.md` directly, no forks; a new skill gets a pointer | KEPT, "Skills" bullets 3 and 4 and Bootstrap rule 3 |
| 499 | Alias pointers: `alias-of`, the target's three paths; `vet` is the alias for `implement-review`; why renaming is wrong; the pointer-file test | Alias rule KEPT in "Skills" bullet 4; the renaming rationale and the test reference MOVED to `docs/agents-md.md` |

## Cross-checks

- Test-pinned phrases preserved verbatim: the source-repo and consumer-path markers, the bootstrap commands, "rewrites the consuming repo's root `AGENTS.md`", "an existing composed `AGENTS.md` is preserved", "does not delete unrelated project-local commands", the copy-paste block phrases, the `.md`-file draft phrases, and the headings "Configuration Precedence", "Session Start Check", "Writing Defaults", "Git Safety".
- The two agent-tagged blocks are gone; the generator still runs and the generated files equal the shared file plus the header.
- The `agent-config`-specific lines (profile, `py312`, PyCharm, onboarding) are in `agent-config/AGENTS.local.md`.
