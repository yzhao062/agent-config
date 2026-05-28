# Agent fungibility refactor plan: graceful degradation when an agent is unavailable

**Status**: Plan captured 2026-05-16. Phase 0 (maintainer-local) completed 2026-05-16. Phase 0.5 completed 2026-05-19 (shipped as v0.7.0 Slice B). Phases 1-7 open; Phase 8 deferred. Adjacent increment 2026-05-22: `dispatch-copilot` third-agent reviewer shipped (see "Shipped adjacent" below); de-risks Phase 2, does not close it. Adjacent increment 2026-05-27: AGENTS.md § "Local Skills Precedence" + § "Cross-Tool Skill Sharing" now describe a 3-path skill lookup order (`skills/` → `.claude/skills/` → `.agent-config/repo/skills/`) and explicitly mark the `.claude/`-prefixed paths as cross-agent surfaces despite the Claude-centric naming. Shipped as part of the issue #6 pointer-lookup fix; partially overlaps Phase 1 (SKILL.md agent-agnostic refactor) and Phase 3 (AGENTS.md slash-command fallback) without closing either.
**Owner**: Yue (driver) + Claude (implementer when invoked); reversal scenario explicitly includes Codex-as-implementer.
**Driver**: Two concrete failure modes for the current Claude-primary design: (1) service outage or regional block (e.g., maintainer travel to a country where Claude is restricted), and (2) quality drift between Claude and Codex over time. Reversal testing is the deliberate flip of primary/gatekeeper roles to evaluate which agent is currently stronger for a given task class.

## Principle

Not 1:1 replication. The two agents have different ergonomic surfaces and different strengths; trying to mirror every feature both ways is wasted effort. The constraint is narrower: when one agent is absent or when roles are reversed, the **core functions** still work. Define "core function" by user value (review-loop, dispatch, health check, bootstrap) rather than by surface convenience (slash-command sugar, IDE plugin polish).

The shared source for the principle is `AGENTS.md` § "Agent Roles" (once Phase 0.5 lands). `CLAUDE.local.md` carries a maintainer-local copy for ac-source-repo sessions but is gitignored and does not reach downstream consumers.

## Two scenarios this plan addresses

1. **Absence**: one agent is genuinely unavailable. Service outage, regional block, API quota exhaustion, or hardware-induced refusal (e.g., Codex Windows 1312, Claude install lock). Work continues, possibly with degraded ergonomics, on the remaining agent.
2. **Reversal testing**: the user deliberately swaps primary/gatekeeper roles. Codex-as-primary + Claude-as-gatekeeper is a supported configuration, not a workaround.

## Shipped adjacent: dispatch-copilot third-agent reviewer (2026-05-22)

Not one of the numbered phases below, but the first concrete realization of the principle and a working precedent for Phase 2. Shipped to both repos (ac `88a7c97`, aa `d5a0b90`): a GitHub Copilot CLI reviewer backend for the implement-review Auto-terminal channel, opt-in via `/implement-review auto copilot`. It serves the **absence** scenario plus the **codex-only reversal mode** named in Phase 4: when Claude is unavailable and Codex is the implementer, the reviewer "must be Codex itself or a third agent", and Copilot is that third agent.

What it delivered:

- `skills/implement-review/scripts/dispatch-copilot.{ps1,sh}`: mirrors the `dispatch-codex` contract (named args, single `STATE-DIR` stdout line, state-dir with pre-mtime/timestamp/tail, stall-watch, exit-code passthrough) with Copilot specifics: prompt via `-p "@file"`, `copilot` resolution with a `gh copilot` fallback, a narrow read+write+`shell(git:*)` allow-list scoped to the repo, `GIT_PAGER=cat`, and Copilot writing `Review-GitHub-Copilot.md` itself.
- `tests/test_dispatch_copilot.py`: gated STRICT in `check-parity.sh` per the Phase 7 / Item 2 doctrine, byte-mirrored ac↔aa.
- SKILL.md: an additive "Auto-terminal Copilot backend" subsection plus opt-in routing. Bare `/implement-review auto` still selects Codex (additive, no shared Codex script touched).
- Validated with real `copilot` on Windows (`.cmd` path) and Spark Ubuntu (`.sh` path), and dogfooded through the new backend itself (12/12 Phase 2.0 health checks, no blocking findings).

How it de-risks the remaining phases:

- **Phase 2 (`dispatch-claude`)**: dispatch-copilot is the same "mirror dispatch-codex for a non-Codex reviewer" pattern, now proven cross-platform. The prompt-shape, state-dir, stall-watch, and AV-avoidance lessons transfer; the binary-resolution-with-fallback shape is reusable. dispatch-claude differs mainly in the binary (`claude -p` plus `--dangerously-skip-permissions`) and its failure envelopes.
- **Phase 1 (reviewer-agnostic SKILL.md)**: only partially touched. SKILL.md stays Codex-default; the Copilot backend was added as an opt-in path, not a full narrative genericization. Phase 1 stays open, but now has two concrete backends to generalize from instead of one.
- **Phase 6 (reviewer-agnostic health-check)**: not required for Copilot. The existing generic patterns plus the backtick-code-span exclusion handled the Copilot tail cleanly. Phase 6's Claude-specific survey still stands for the Claude tail.
- **Phase 7 (test gating)**: precedent set. `test_dispatch_copilot.py` is in the STRICT block; `test_dispatch_claude.py` follows the same wiring.

Numbered-plan status is unchanged: Phases 1-7 stay open. This increment lowers Phase 2's unknowns rather than closing any phase.

## Phase 0 - Capture the maintainer-local principle in CLAUDE.local.md (DONE, local-only)

### Scope

Add an "Agent fungibility" section to `CLAUDE.local.md` so maintainer sessions in this repo see the principle while the shared plan is being reviewed.

### Done when

The local principle is recorded in `CLAUDE.local.md` and this followup file links to the local note.

### Completed 2026-05-16

The `CLAUDE.local.md` edit exists for maintainer sessions, but it is ignored by `.git/info/exclude` and is not part of this staged commit. Treat it as a local note, not the shared source of truth.

## Phase 0.5 - Promote the principle to AGENTS.md (half day, CRITICAL PATH)

### Scope

Add the agent-fungibility principle near `AGENTS.md` section "Agent Roles", then regenerate `CLAUDE.md` and `agents/codex.md` via `scripts/generate_agent_configs.py` so consumer repos receive the same intent through bootstrap.

### Done when

A fresh consumer bootstrap includes the principle in `AGENTS.md`, `CLAUDE.md`, and `agents/codex.md`; this plan no longer names `CLAUDE.local.md` as the shared source. Verification: grep the principle's first sentence in a fresh aa consumer clone after bootstrap.

### Completed 2026-05-19

Shipped as v0.7.0 Slice B. `## Agent Fungibility` is now a top-level section in both ac and aa `AGENTS.md`, immediately after `## Agent Roles`. The CLAUDE.local.md section was trimmed to a one-line pointer at the canonical shared source. `CLAUDE.md` and `agents/codex.md` were regenerated in both repos. Reviewed via /implement-review (Codex) as part of the Slice B+C combined review.

## Phase 1 - SKILL.md agent-agnostic refactor (1 day)

### Scope

`skills/implement-review/SKILL.md` was authored under the assumption that Codex is the only reviewer. Several call-outs hard-code Codex:

- Phase 1c dispatch step describes "Codex reviews via Auto-terminal / Terminal-relay / Plugin"
- Channel names embed the Codex CLI (Auto-terminal via `codex exec`, Terminal-relay via the Codex terminal, Plugin via the Codex IDE plugin)
- Filename convention `Review-<Name>.md` is already vendor-agnostic (the normalization rule in the prompt handles any reviewer name)
- FP-tuning doctrine references Codex tail patterns by name (sandbox 1312, WSL stub markers)

### Suggested approach

Three-tier audit:

1. **Keep Codex-named** where the dispatch primitive is specifically Codex's. `codex exec --sandbox danger-full-access -` is a Codex-specific invocation; there is no point genericizing the language when the script under the hood is `dispatch-codex.ps1`.
2. **Switch to reviewer-agnostic** in the narrative layer. "Codex reviews the diff" reads "the reviewer agent reviews the diff" without losing precision, especially in Phase 1c step descriptions and the overview diagram.
3. **Document both paths without publishing a broken runtime path**. If Phase 1 lands before Phase 2, every Claude-reviewer Auto-terminal mention must be labeled "planned, unavailable until `dispatch-claude.{ps1,sh}` exists", and Phase 1c must keep the current script-presence downgrade behavior. If the text presents Claude-reviewer Auto-terminal as usable, Phase 2 must land in the same release unit.

### Done when

SKILL.md reads as "primary agent dispatches to reviewer agent" with Codex as the default reviewer. Claude is documented either as a planned reviewer path with an explicit unavailable marker, or as a usable reviewer path only after `dispatch-claude.{ps1,sh}` exists and is covered by the script-presence probe.

### Dependency

Phase 1 can be authored in parallel with Phase 2, but it cannot be released ahead of Phase 2 unless all Claude-reviewer runtime references are explicitly marked planned/unavailable.

## Phase 2 - dispatch-claude.{ps1,sh} scripts (3-5 days, CRITICAL PATH)

### Scope

Mirror `skills/implement-review/scripts/dispatch-codex.{ps1,sh}` for Claude as the reviewer. This is the load-bearing primitive that gates every downstream phase.

### Implementation notes

- **Non-interactive invocation**: `claude -p "<prompt>"` is Claude's equivalent of `codex exec`. The `-p` flag forces print mode (no REPL, single response, exit on completion). Stdin vs. positional prompt behavior under PowerShell needs a probe before fixing the dispatch shape.
- **PATH resolution**: Native installer puts the binary at varying locations depending on platform (Windows: `%LOCALAPPDATA%\AnthropicClaude\claude.exe`; macOS: `/usr/local/bin/claude` or `~/.local/bin/claude`; Linux: `~/.local/bin/claude`). npm install puts it under `%APPDATA%\npm` / `~/.npm-global/bin`; winget legacy under `%LOCALAPPDATA%\Microsoft\WinGet\Packages\`. Mirror the PATH-resolution test from `test_dispatch_path_resolution.py` and add per-install-method cases.
- **Permission flag**: Claude's equivalent of `--sandbox danger-full-access` is `--dangerously-skip-permissions`. Use it by default in dispatch for the same trust-posture reasons documented in `SKILL.md:94`. Add `CLAUDE_DISPATCH_SAFE` env override for sandbox-strict environments (mirrors `CODEX_DISPATCH_SANDBOX`).
- **Stdin prompt forwarding**: Same shape as dispatch-codex; prompt fed via stdin, captured to `<state-dir>/prompt` for health-check inspection.
- **Tail capture**: Same shape; stdout + stderr captured to `<state-dir>/tail`. Note: Claude's failure envelopes differ from Codex's; Phase 6 handles the Claude-specific pattern set.
- **Exit-code contract**: Match dispatch-codex's exit-code semantics so downstream health-check logic remains unchanged.
- **AV avoidance**: Apply the same Bitdefender lessons from Item 6 of [`2026-05-16-implement-review-auto-followups.md`](2026-05-16-implement-review-auto-followups.md). No PATH-prepend constructs. No literal `SET "PATH=...;%PATH%"` strings anywhere in source.

### Done when

`dispatch-claude.ps1` + `dispatch-claude.sh` exist and are byte-mirrored ac↔aa under `scripts/check-parity.sh` STRICT. A grep of both scripts shows zero `SET PATH=...;%PATH%` or `$env:PATH = ` PATH-prepend constructs. Mock-Claude argv tests pin the `--dangerously-skip-permissions` default plus stdin-prompt shape on both POSIX and PowerShell. A manual `dispatch-claude` succeeds against a real Claude install on both Windows and a Unix host with an end-to-end `Review-Claude.md` write.

### Effort context

Reference: dispatch-codex initial implementation was ~1 day, but accumulated ~3 more days across review rounds and follow-on fixes (Items 1, 2, 6 in 2026-05-16-implement-review-auto-followups). dispatch-claude carries analogous unknowns (PATH resolution variance, stdin shape under PowerShell, AV-avoidance). 3-5 days is the calibrated estimate including review rounds and follow-ons.

### Critical path

Gate for Phases 3, 4, 6, 7. Without dispatch-claude, the Claude-as-reviewer path is theoretical.

## Phase 3 - AGENTS.md slash-command fallback (half day)

### Scope

`AGENTS.md` describes the default routing (Claude primary, Codex gatekeeper). When the user opts into Codex-as-primary, the slash-command UX changes:

- `/implement-review` is a Claude Code slash command; Codex does not have an equivalent invocation surface
- Codex has its own prompt-preset mechanism (the exact flag and path need verification during Phase 3 implementation)
- The Codex-as-primary path needs a documented invocation that loads SKILL.md content into a Codex session and runs the same workflow

### Suggested approach

Add an `AGENTS.md` subsection: "When the primary agent is Codex". Document:

- How to invoke implement-review without Claude (the verified Codex prompt-preset flow + the dispatch-claude script for the reviewer half)
- The opt-in mechanism (env var `PRIMARY_AGENT=codex` or a flag in `.agent-config/config.yaml`)
- Which Claude-specific features degrade (slash-command discoverability, IDE plugin, SessionStart banner)

### Done when

A consumer in a Claude-restricted region can read AGENTS.md and complete a /implement-review cycle on Codex alone. Verification: grep the generated `AGENTS.md` in a fresh bootstrap for the exact Codex-primary invocation text, the prompt-preset path, and the missing-Claude degradation list; a consumer bootstrap smoke test runs the documented Codex-primary invocation against a mock Claude binary and confirms the cycle completes.

## Phase 4 - Codex-primary bootstrap entry point (half day)

### Scope

`bootstrap.{sh,ps1}` currently sets up Claude defaults: `~/.claude/settings.json` merge, PreToolUse hook (`guard.py`), SessionStart hook (`session_bootstrap.py`). A Codex-primary install needs the analogue, but the flag must not conflate primary-agent choice with whether Claude is configured at all:

- `~/.codex/config.toml` with the recommended model + reasoning + tier defaults already documented in `AGENTS.md` § "Codex MCP Integration"
- A codex-side hook equivalent (Codex's hook surface, if any, is not equivalent to Claude's; the Phase 4 inventory step determines whether to wire codex-side hooks or document the gap)
- Two reversal-relevant modes: **codex-primary-with-claude-reviewer** (Claude is still installed and configured so `dispatch-claude` works as the reviewer half) and **codex-only** (Claude config is skipped entirely; reviewer must be Codex itself or a third agent)

### Suggested approach

Extend bootstrap with two flags, with one invalid combination explicitly rejected:

- `--primary <claude|codex>`: which agent is the primary workhorse (default `claude` for back-compat). Does NOT by itself disable Claude config.
- `--skip-claude-user-setup`: allowed only with `--primary codex`. It creates codex-only mode by leaving `~/.claude/` untouched.
- `--skip-claude-user-setup` with the default Claude primary, or with explicit `--primary claude`, exits non-zero with a clear message. Claude-primary mode cannot opt out of Claude user setup in this phase; no named Phase 4 mode needs Claude-primary without Claude setup.

When `--primary codex` is passed:

- Run a `~/.codex/config.toml` healer that writes the recommended config if absent or out of date
- Print a one-line note about which agent features degrade
- Skip `~/.claude/` setup ONLY when `--skip-claude-user-setup` is also passed

### Done when

`bash bootstrap.sh --primary codex` produces a working Codex-primary setup with Claude config still healed (reversal-testing mode). `bash bootstrap.sh --primary codex --skip-claude-user-setup` produces codex-only mode with `~/.claude/` untouched. `bash bootstrap.sh` (no flag) produces a setup whose `~/.claude/settings.json` merge result equals the pre-Phase-4 baseline in a temp-consumer fixture (output equivalence, not byte-identical script text). `bash bootstrap.sh --skip-claude-user-setup` (alone) and `bash bootstrap.sh --primary claude --skip-claude-user-setup` both exit non-zero with a clear "Claude-primary mode cannot opt out of Claude user setup" message, with fixture tests pinning both rejections.

## Phase 5 - Cross-agent docs (half day)

### Scope

`README.md` and the aa RTD docs currently show Claude-centric examples (install via `claude install`, first-run via `claude /implement-review`). Add parallel Codex-centric examples.

### Suggested approach

For each install-flow / first-run doc, add a tab or sibling subsection labeled "Using Codex as primary" with the analogous commands. Do not duplicate the narrative; only the commands.

### Done when

A reader can pick "Claude" or "Codex" at the install-flow entry point and complete the entire onboarding flow without cross-referencing the other tab.

## Phase 6 - health-check.py reviewer-agnostic (1 day)

### Scope

`skills/implement-review/scripts/health-check.py` was authored with Codex's tail envelopes in mind. The `TOOL_FAILURE_PATTERNS` list catches Codex-specific failure shapes (1312, sandbox errors, rate-limit 429). Claude failures have different envelopes.

### Suggested approach

Split the pattern list:

- **Reviewer-agnostic** patterns: rate-limit indicators, generic "tool call failed" markers, exit-code-like patterns
- **Reviewer-specific** patterns: Codex-side (`createprocessasuserw`, `windows sandbox`) and Claude-side (TBD: needs a survey of Claude's failure-envelope shapes)

Add `--reviewer <codex|claude>` flag to health-check so it loads only the relevant pattern set plus the shared set. Auto-detect from the `Review-<Name>.md` filename when possible.

### Done when

`health-check.py --reviewer claude` runs against a fixture Claude tail (committed under `tests/fixtures/`) and produces the expected WARN-breakdown labels per a pinned assertion (`tests/test_health_check.py::test_claude_reviewer_breakdown`). `--reviewer codex` continues to produce the existing Codex-side labels against the existing fixtures.

## Phase 7 - Test coverage for dispatch-claude (1 day)

### Scope

Mirror `tests/test_dispatch_codex.py` as `tests/test_dispatch_claude.py`. Cover:

- PATH resolution across install methods
- `--dangerously-skip-permissions` default + `CLAUDE_DISPATCH_SAFE` env override
- Prompt stdin forwarding
- Exit-code contract

### Suggested approach

Add `test_dispatch_claude.py` to the STRICT shared-contract list per [implement-review-auto Item 2 doctrine](2026-05-16-implement-review-auto-followups.md), so the test mirrors ac↔aa byte-identically and both sides' CI gates the contract. Phase 7 lands next to Phase 2 (not deferred to last) because dispatcher behavior needs tests before the runtime can be called done.

### Done when

ac + aa CI both run `test_dispatch_claude.py`, all matrix lanes green, and the test is in the STRICT block of `scripts/check-parity.sh`.

## Phase 8 - Pack handler split (spike, likely 3-5+ days after discovery; DEFERRED)

### Scope

The `anywhere-agents` pack lifecycle (compose, verify, install) is currently driven from the Claude side via `bootstrap.{sh,ps1}` and the composer. A truly Codex-primary world needs an equivalent Codex-side pack handler.

### Why deferred

The pack system is not a thin wrapper. The aa composer is ~1,881 lines and the pack CLI is ~3,600+ lines spanning state, reconciliation, and per-pack handler modules. A Codex-side mirror is a structural change to the distribution, not a refactor. The 1-2 day prior estimate undersold the work; a proper spike is the right pre-implementation step. The composer already exposes `pack add / list / update / verify --fix` as the maintainer-side surface, so the gap is interface plumbing under structural complexity, not feature design.

### Re-evaluation trigger

The earlier "SSH-once-per-release" framing was wrong because a pack hotfix can land mid-session when a consumer reports a broken pack. Reframe the trigger as: (a) the first time a pack hotfix is needed while Claude is unavailable (travel, outage, quota), OR (b) before known restricted travel with expected pack work, OR (c) when the v1.0.0 architecture rework happens and the composer is being refactored anyway. Trigger (a) escalates the spike from "deferred" to "blocking" with whatever time the maintainer has.

## Effort summary

| Phase | Effort | Critical path? | Status |
|---|---|---|---|
| 0 - CLAUDE.local.md principle (local-only) | 5 min | no (local-only) | Done 2026-05-16 |
| 0.5 - Promote principle to AGENTS.md | half day | yes | Open |
| 1 - SKILL.md refactor | 1 day | yes | Open |
| 2 - dispatch-claude scripts | 3-5 days | yes | Open |
| 3 - AGENTS.md fallback | half day | yes | Open |
| 4 - Codex-primary bootstrap | half day | yes | Open |
| 5 - Cross-agent docs | half day | no | Open |
| 6 - health-check reviewer-agnostic | 1 day | no | Open |
| 7 - dispatch-claude tests | 1 day | yes (next to Phase 2) | Open |
| 8 - Pack handler split | spike, 3-5+ days | no | Deferred |

**Critical path (Phases 0 -> 0.5 -> 1 -> 2 -> 3 -> 4, with Phase 7 paired to Phase 2)**: ~6-9 days to deliver the resilience guarantee end-to-end (absence + reversal scenarios both work, with dispatcher tests gating the runtime done-when).

**Full plan (Phases 0 -> 7, effort sum)**: ~8-10 days adding cross-agent docs and reviewer-agnostic health-check (sum of table rows: 0.5 + 1 + 3-5 + 0.5 + 0.5 + 0.5 + 1 + 1 = 8-10 days). Calendar elapsed can be shorter if Phase 5 or Phase 6 runs in parallel with the critical path.

**With Phase 8**: add a 3-5+ day spike after the trigger fires; not recommended until then.

## Sequencing

1. Phase 0 (done) -> Phase 0.5 (promote principle to AGENTS.md) before any SKILL.md / dispatch work.
2. Phase 1 and Phase 2 may be developed in parallel, but the release order is Phase 2 first or one combined Phase 1+2 release unless Phase 1 marks the Claude-reviewer runtime path as planned/unavailable.
3. Phase 7 (dispatch-claude tests) lands next to Phase 2, not after; dispatcher cannot be called done without it.
4. Phase 2 + Phase 7 land -> Phase 3 + Phase 4 unblock (both depend on the dispatch primitive existing and tested).
5. Phase 5 (cross-agent docs) can land any time after Phase 2 (it cites the new dispatch path).
6. Phase 6 (health-check reviewer-agnostic) lands after Phase 2 so the Claude tail is real, not hypothetical.
7. Phase 8 stays deferred until the trigger fires.

## Cross-references

- `AGENTS.md` § "Agent Roles" - current default routing (Claude primary, Codex gatekeeper); will carry the principle after Phase 0.5
- `CLAUDE.local.md` § "Agent fungibility" - maintainer-local copy of the principle (gitignored; not the shared source after Phase 0.5)
- `AGENTS.md` § "Codex MCP Integration" - recommended Codex config defaults (`model`, `model_reasoning_effort`, `service_tier`, `[features].fast_mode`)
- `skills/implement-review/SKILL.md` Phase 1c - current Codex-only dispatch language
- `skills/implement-review/scripts/dispatch-codex.{ps1,sh}` - the reference implementation to mirror for Claude
- `tests/test_dispatch_codex.py` - the reference test suite
- `skills/implement-review/scripts/dispatch-copilot.{ps1,sh}` + `tests/test_dispatch_copilot.py` - shipped 2026-05-22; third-agent (Copilot) reviewer realizing the same dispatch-codex-mirror pattern Phase 2 needs for Claude (see "Shipped adjacent" above)
- [`2026-05-16-implement-review-auto-followups.md`](2026-05-16-implement-review-auto-followups.md) - STRICT-mirror doctrine for shared-contract tests (Item 2) and AV-avoidance lessons (Item 6)

## Delete this file when

Phases 0.5 + 1-7 land. After that the principle is in `AGENTS.md` proper and the operational primitives exist. Phase 8 deferral can persist indefinitely without blocking deletion of this file.
