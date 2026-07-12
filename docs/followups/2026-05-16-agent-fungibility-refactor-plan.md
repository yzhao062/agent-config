# Agent fungibility refactor plan: graceful degradation when an agent is unavailable

**Status**: Plan captured 2026-05-16. Phase 0 (maintainer-local) completed 2026-05-16. Phase 0.5 completed 2026-05-19 (shipped as v0.7.0 Slice B). **Phase 2 + Phase 7 shipped 2026-05-28** (`dispatch-claude.{ps1,sh}` + `tests/test_dispatch_claude.py`: feat `102ab2c`, bash-3.2 portability fix `63dd90e`, live-invocation fix `e25e993`). Phases 1, 3, 4, 5, 6 open; Phase 8 deferred. Phase 2.5 (reviewer-selection primitive) and Phase 7.5 (automated live-dispatch smoke) added 2026-05-28 from the symmetry review. **Phases 1 and 6 are reclassified as symmetry-blocking**, not optional polish (rationale in each phase).

**Merged 2026-05-28**: the standalone `2026-05-28-codex-primary-symmetry-plan.md` is folded into this file. Its three steps were a Codex-primary runbook, an `AGENTS.md` Codex-primary section, and `bootstrap --primary codex`; those map to parent Phases 3 and 4 and are concretized there. The symmetry review that prompted the merge found that the standalone plan delivered the parts that *look* like symmetry (the entry points) while leaving two load-bearing parent phases open: Phase 1 (SKILL.md still reads "Codex reviews") and Phase 6 (health-check still tuned to Codex failure envelopes). It also surfaced three missing pieces now captured below: an automated live-dispatch smoke (Phase 7.5), a reviewer-selection primitive (Phase 2.5), and a degradation list reframed as function-mapping rather than flat loss (inside Phase 3).

Adjacent increment 2026-05-22: `dispatch-copilot` third-agent reviewer shipped (see "Shipped adjacent" below); de-risked Phase 2, did not close it. Adjacent increment 2026-05-27: AGENTS.md § "Local Skills Precedence" + § "Cross-Tool Skill Sharing" now describe a 3-path skill lookup order (`skills/` → `.claude/skills/` → `.agent-config/repo/skills/`) and explicitly mark the `.claude/`-prefixed paths as cross-agent surfaces despite the Claude-centric naming. Shipped as part of the issue #6 pointer-lookup fix; partially overlaps Phase 1 (SKILL.md agent-agnostic refactor) and Phase 3 (AGENTS.md slash-command fallback) without closing either.

**Owner**: Yue (driver) + Claude (implementer when invoked); reversal scenario explicitly includes Codex-as-implementer.
**Driver**: Two concrete failure modes for the current Claude-primary design: (1) service outage or regional block (e.g., maintainer travel to a country where Claude is restricted), and (2) quality drift between Claude and Codex over time. Reversal testing is the deliberate flip of primary/gatekeeper roles to evaluate which agent is currently stronger for a given task class.

## Principle

Not 1:1 replication. The two agents have different ergonomic surfaces and different strengths; trying to mirror every feature both ways is wasted effort. The constraint is narrower: when one agent is absent or when roles are reversed, the **core functions** still work. Define "core function" by user value (review-loop, dispatch, health check, bootstrap) rather than by surface convenience (slash-command sugar, IDE plugin polish).

A corollary the symmetry review made explicit: a "degraded" Claude surface is not automatically a lost function. Where Codex has a native equivalent (its own approval policy, its first-response banner convention), the function is reachable and should be **mapped** to that equivalent, not listed as a flat loss. A genuine loss is only the case where no Codex-side primitive reaches the function.

The shared source for the principle is `AGENTS.md` § "Agent Fungibility" (promoted there in Phase 0.5). `CLAUDE.local.md` carries a maintainer-local pointer for ac-source-repo sessions but is gitignored and does not reach downstream consumers.

## Two scenarios this plan addresses

1. **Absence**: one agent is genuinely unavailable. Service outage, regional block, API quota exhaustion, or hardware-induced refusal (e.g., Codex Windows 1312, Claude install lock). Work continues, possibly with degraded ergonomics, on the remaining agent.
2. **Reversal testing**: the user deliberately swaps primary/gatekeeper roles. Codex-as-primary + Claude-as-gatekeeper is a supported configuration, not a workaround.

## Symmetry priority (set 2026-05-28)

Priority is by the principle's test: does the gap break a **core function** (review-loop, dispatch, health check, bootstrap) under reversal, or is it surface convenience? Core-function gaps are blocking; surface gaps are optional.

**P0 - symmetry-blocking (until these land, "Codex-primary is symmetric" is not true):**

1. **Phase 6 - reviewer-agnostic health-check.** Highest. A Codex-tuned health-check is blindest to the silent Claude-reviewer hang that motivated the Phase 2 rework, so the safety net is pointed at the wrong agent. Phase 7.5 depends on it.
2. **Phase 1 - SKILL.md narrative.** The one doc both agents read first via the 3-path lookup; Codex-default framing is backwards for Codex-primary and drifts against the Phase 3 runbook if left.
3. **Phase 7.5 - automated live-dispatch smoke.** The regression net. Direct lesson from `e25e993`: command-string tests were green while the live invocation hung.

**P1 - entry points and hardening (make the mode usable and robust):**

4. **Phase 3 - AGENTS.md section + runbook.** The Codex-primary entry point.
5. **Phase 4 - `bootstrap --primary codex`.** Config healing for the mode.
6. **Phase 2.5 - `dispatch-review` selector.** Turns prose reviewer-selection into a tested primitive.

**P2 - meaningful but not blocking (ergonomics / observability):**

7. **Phase 9 - cross-agent quota visibility.** Useful for the human's which-agent decision; not on the review-loop path. Feasible on the data side, contingent on a Codex rendering surface (see Phase 9).

**Not pursued - function already reachable, symmetry not forced (confirmed 2026-05-28):**

- **Destructive-command guard.** Codex reaches the gating function through its own `approval_policy` + `approvals_reviewer = guardian_subagent` + sandbox. Map it in Phase 3; no mirror of `guard.py` is built.
- **Slash-command surface.** No Codex `/implement-review`; the runbook starter prompt is the reachability path.
- **SessionStart banner.** Codex reaches it via the first-response emission convention in `AGENTS.md` § "Session Start Check".

## Shipped adjacent: dispatch-copilot third-agent reviewer (2026-05-22)

Not one of the numbered phases below, but the first concrete realization of the principle and a working precedent for Phase 2. Shipped to both repos (ac `88a7c97`, aa `d5a0b90`): a GitHub Copilot CLI reviewer backend for the implement-review Auto-terminal channel, opt-in via `/implement-review auto copilot`. It serves the **absence** scenario plus the **codex-only reversal mode** named in Phase 4: when Claude is unavailable and Codex is the implementer, the reviewer "must be Codex itself or a third agent", and Copilot is that third agent.

What it delivered:

- `skills/implement-review/scripts/dispatch-copilot.{ps1,sh}`: mirrors the `dispatch-codex` contract (named args, single `STATE-DIR` stdout line, state-dir with pre-mtime/timestamp/tail, stall-watch, exit-code passthrough) with Copilot specifics: prompt via `-p "@file"`, `copilot` resolution with a `gh copilot` fallback, a narrow read+write+`shell(git:*)` allow-list scoped to the repo, `GIT_PAGER=cat`, and Copilot writing `Review-GitHub-Copilot.md` itself.
- `tests/test_dispatch_copilot.py`: gated STRICT in `check-parity.sh` per the Phase 7 / Item 2 doctrine, byte-mirrored ac↔aa.
- SKILL.md: an additive "Auto-terminal Copilot backend" subsection plus opt-in routing. Bare `/implement-review auto` still selects Codex (additive, no shared Codex script touched).
- Validated with real `copilot` on Windows (`.cmd` path) and Spark Ubuntu (`.sh` path), and dogfooded through the new backend itself (12/12 Phase 2.0 health checks, no blocking findings).

How it de-risked the remaining phases:

- **Phase 2 (`dispatch-claude`)**: dispatch-copilot was the same "mirror dispatch-codex for a non-Codex reviewer" pattern, proven cross-platform. The prompt-shape, state-dir, stall-watch, and AV-avoidance lessons transferred. (See Phase 2 below for where the Claude path diverged anyway, because the dispatch *shape* was reusable but Claude's headless permission behavior was not.)
- **Phase 1 (reviewer-agnostic SKILL.md)**: only partially touched. SKILL.md stays Codex-default; the Copilot backend was added as an opt-in path, not a full narrative genericization. Phase 1 stays open.
- **Phase 6 (reviewer-agnostic health-check)**: not required for Copilot. The existing generic patterns plus the backtick-code-span exclusion handled the Copilot tail cleanly. Phase 6's Claude-specific survey still stands for the Claude tail.
- **Phase 7 (test gating)**: precedent set. `test_dispatch_copilot.py` is in the STRICT block; `test_dispatch_claude.py` followed the same wiring.

## Phase 0 - Capture the maintainer-local principle in CLAUDE.local.md (DONE, local-only)

### Scope

Add an "Agent fungibility" section to `CLAUDE.local.md` so maintainer sessions in this repo see the principle while the shared plan is being reviewed.

### Done when

The local principle is recorded in `CLAUDE.local.md` and this followup file links to the local note.

### Completed 2026-05-16

The `CLAUDE.local.md` edit exists for maintainer sessions, but it is ignored by `.git/info/exclude` and is not part of any staged commit. Treat it as a local note, not the shared source of truth.

## Phase 0.5 - Promote the principle to AGENTS.md (half day, CRITICAL PATH)

### Scope

Add the agent-fungibility principle near `AGENTS.md` section "Agent Roles", then regenerate `CLAUDE.md` and `agents/codex.md` via `scripts/generate_agent_configs.py` so consumer repos receive the same intent through bootstrap.

### Done when

A fresh consumer bootstrap includes the principle in `AGENTS.md`, `CLAUDE.md`, and `agents/codex.md`; this plan no longer names `CLAUDE.local.md` as the shared source. Verification: grep the principle's first sentence in a fresh aa consumer clone after bootstrap.

### Completed 2026-05-19

Shipped as v0.7.0 Slice B. `## Agent Fungibility` is now a top-level section in both ac and aa `AGENTS.md`, immediately after `## Agent Roles`. The CLAUDE.local.md section was trimmed to a one-line pointer at the canonical shared source. `CLAUDE.md` and `agents/codex.md` were regenerated in both repos. Reviewed via /implement-review (Codex) as part of the Slice B+C combined review.

## Phase 1 - SKILL.md agent-agnostic refactor (1 day, OPEN, SYMMETRY-BLOCKING)

### Why this is symmetry-blocking, not polish

`SKILL.md` is the single doc that every agent resolves through the 3-path lookup (`skills/` → `.claude/skills/` → `.agent-config/repo/skills/`). A Codex-primary session reads it first, before any runbook or `AGENTS.md` mode section. As long as the narrative defaults to "Codex reviews", that session sees the reviewer role assigned to itself, which is backwards for Codex-primary mode. Patching over this with a separate runbook (Phase 3) creates two docs describing the same loop, which drift. Phase 3 can ship the entry points, but the loop does not read symmetrically until Phase 1 reconciles the canonical doc. Pick one of two resolutions and state which is canonical: genericize the SKILL.md narrative, or have the runbook explicitly supersede the relevant SKILL.md sections for Codex-primary mode.

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
3. **Document both paths without publishing a broken runtime path**. Claude-reviewer Auto-terminal is now usable (Phase 2 shipped), so the unavailable marker is no longer required; the script-presence probe is the live gate.

### Done when

SKILL.md reads as "primary agent dispatches to reviewer agent" with Codex as the default reviewer and Claude as a usable reviewer path covered by the script-presence probe. The doc states explicitly which artifact is canonical for Codex-primary mode (SKILL.md narrative or the Phase 3 runbook), so the two cannot drift.

## Phase 2 - dispatch-claude.{ps1,sh} scripts (3-5 days, CRITICAL PATH, SHIPPED 2026-05-28)

### Scope

Mirror `skills/implement-review/scripts/dispatch-codex.{ps1,sh}` for Claude as the reviewer. This was the load-bearing primitive that gated every downstream phase.

### What actually shipped (and how it diverged from the original implementation notes)

The original notes guessed `claude -p --dangerously-skip-permissions` with Claude writing `Review-Claude.md` itself. The shipped design is different on three points, all learned from live probes rather than the spec:

- **Permission model**: the first cut (`102ab2c`) used `--permission-mode dontAsk` with a path-scoped `--allowedTools "Read,Write(/Review-Claude-Code.md),Edit(/Review-Claude-Code.md)"` so Claude wrote the file under a narrow allow-list. A live probe showed current Claude Code (2.1.153) **hangs** under unattended `dontAsk` when given path-scoped `Write(...)` or exact `Bash(...)` preapproval patterns on Windows. `e25e993` reworked it to `--permission-mode bypassPermissions --tools "Read,Bash"`: Claude gets no Write/Edit tools at all.
- **Who writes the review file**: not Claude. The dispatcher wraps the review prompt in a relay prompt, captures Claude's stdout, and writes `Review-Claude-Code.md` itself (with Round-marker normalization). stderr is split to `<state-dir>/tail.stderr-tmp` so it does not pollute the review body.
- **Isolation**: the dispatcher exports the git index to `<state-dir>/staged-snapshot` via `git checkout-index -a` and runs Claude from that disposable copy, falling back to the original worktree (with a recorded reason) when export fails. This is the isolation the original path-scoped allow-list was reaching for, achieved without the hang.
- **AV avoidance**: `dispatch-claude.ps1` decomposes its self-review env-check into a sibling `_claude_guard.ps1` to clear a Bitdefender AMSI heuristic. `dispatch-claude.sh` keeps the guard inline (POSIX scanners lack the heuristic).
- **`--bare` opt-in**: `CLAUDE_DISPATCH_BARE=1` opts into `--bare` only where `ANTHROPIC_API_KEY` or an `apiKeyHelper` exists; default off, because Claude Code 2.1.153 disables OAuth/keychain auth in bare mode. `63dd90e` fixed the empty-array expansion of this opt-in under macOS bash 3.2 / `set -u`.

### Lesson carried into Phase 7.5

This phase is the clearest evidence that command-string unit tests are necessary but not sufficient: every `test_dispatch_claude.py` assertion was green while the live invocation hung. The done-when below was satisfied by mock-argv tests, yet the runtime was broken until a human ran it. That gap is what Phase 7.5 closes.

### Done when (met)

`dispatch-claude.ps1` + `dispatch-claude.sh` exist and are byte-mirrored ac↔aa under `scripts/check-parity.sh` STRICT. Mock-Claude argv tests pin the invocation shape on POSIX and PowerShell. A manual `dispatch-claude` succeeds against a real Claude install with an end-to-end `Review-Claude-Code.md` write (note: `Review-Claude-Code.md`, not the originally-guessed `Review-Claude.md`).

### Critical path

Was the gate for Phases 2.5, 3, 4, 6, 7, 7.5. Now satisfied, those phases are unblocked.

## Phase 2.5 - Reviewer-selection primitive: dispatch-review (half day, OPEN, NEW 2026-05-28)

### Scope

Reviewer selection ("probe Claude, else Copilot, else a labeled self-audit") currently lives only in prose: the Phase 3 runbook and `AGENTS.md` tell the primary agent to choose. Dispatch is a named core function, and the Phase 2 lesson is that prose contracts are exactly what fail silently. Encode the selection as a thin `dispatch-review.{ps1,sh}` wrapper that probes available reviewer binaries in a fixed order and calls the matching `dispatch-<reviewer>` script.

### Suggested approach

- Probe order configurable via an env var (default: the reviewer opposite the current primary, then Copilot, then self-audit), with `--reviewer <name>` to force a choice.
- Refuse self-review: if the only available reviewer equals the orchestrator (Claude probing Claude, Codex probing Codex), fall through to the next candidate rather than dispatching a same-agent review. This reuses the `_claude_guard` refusal contract.
- Emit one line naming the selected reviewer and the probe results, so a transcript shows why a given backend was chosen.
- Return the selected `dispatch-<reviewer>` script's exit code unchanged, so downstream health-check logic is unaffected.

### Done when

`dispatch-review` selects the right backend across the three reviewer binaries on both shells, is byte-mirrored ac↔aa under STRICT, and has a contract test (`tests/test_dispatch_review.py`) covering: each single-available-binary case, the self-review fall-through, the forced `--reviewer` path, and the all-absent → self-audit path.

## Phase 3 - AGENTS.md Codex-primary section + runbook (half day, OPEN; concretized from the merged 2026-05-28 plan)

### Scope

`AGENTS.md` describes the default routing (Claude primary, Codex gatekeeper). When the user opts into Codex-as-primary, the entry points change and need to be documented in the always-loaded instructions plus a companion runbook. The merged 2026-05-28 plan specified both; this phase carries that design with the symmetry-review fixes applied.

### Implementation

1. **`AGENTS.md` subsection "When Codex Is Primary"** (about 20 to 30 lines), placed after `Agent Fungibility`. Specify three modes:
   - **normal**: Claude implements, Codex reviews (the default; unchanged).
   - **reversal**: Codex implements, Claude reviews through `dispatch-claude` (or `dispatch-review`).
   - **codex-only**: Codex implements, Copilot reviews if available; otherwise a clearly labeled self-audit, which is not an independent reviewer.
2. **Review-file contract** (state exactly which file each reviewer writes):
   - Claude reviewer → `Review-Claude-Code.md`
   - Copilot reviewer → `Review-GitHub-Copilot.md`
   - Codex self-audit → `Review-Codex-Self-Audit.md`, not treated as independent
   - **Symmetry add**: `Review-Claude-Self-Audit.md` for the Claude-primary case where no independent reviewer is available, with the same "not independent" rule. The self-audit fallback must be symmetric across both primaries.
3. **Companion runbook `docs/codex-primary.md`** (the 2026-05-28 plan's first step): a single-page workflow covering prerequisites, the 3-path skill lookup, the implement loop, reviewer selection (point at `dispatch-review` once Phase 2.5 lands), review intake, and the degradation mapping below. Include one copy-pasteable starter prompt under 25 lines, and a short "manual fallback" section for the no-reviewer-CLI worst case.
4. **Degradation list as function-mapping, not flat loss** (symmetry-review fix). For each Claude-only surface, name the Codex-side reachability path rather than listing it as absent:
   - SessionStart banner → reachable: `AGENTS.md` § "Session Start Check" already specifies Codex emits the banner as the first content of an invocation's first response. Different trigger, same function.
   - PreToolUse destructive-command guard → reachable: Codex's `approval_policy` + `approvals_reviewer = guardian_subagent` + sandbox gate destructive commands natively. Map to that; do not call it lost. Confirmed 2026-05-28: no mirror of `guard.py` is built for Codex; its auto-approval is accepted as the equivalent.
   - Slash-command discoverability → genuinely absent; the runbook starter prompt is the reachability path.
   The phase keeps the inventory honest: only surfaces with no Codex primitive are listed as true gaps.
5. **Discoverability**: cross-link the runbook from both `SKILL.md` and the `AGENTS.md` section so a fresh session surfaces it without already knowing it exists.
6. **Parity class**: declare `docs/codex-primary.md`'s class in `scripts/check-parity.sh`. If it carries USC / personal specifics it is BY-DESIGN (sanitized mirror, like `AGENTS.md`); if fully generic it is STRICT. A mirrored doc with no declared class is a drift gap.

### Open questions carried from the 2026-05-28 plan

1. Runbook location: `docs/` vs `skills/implement-review/references/`. Recommend `docs/` (agent-mode runbook, not a review lens), paired with the cross-links in step 5.
2. Should Codex-primary bootstrap touch `approval_policy`? Recommend no (see Phase 4); approval policy is personal and environment-specific.
3. Self-audit file vs no file. Recommend the file (`Review-Codex-Self-Audit.md` / `Review-Claude-Self-Audit.md`), so the intake format is preserved while the lack of independent review is explicit.

### Done when

A consumer in a Claude-restricted region can read `AGENTS.md` plus `docs/codex-primary.md` and complete a `/implement-review` cycle on Codex alone. Verification: grep the generated `AGENTS.md` for the three-mode taxonomy, the four review-file names, and the degradation *mapping* (not a flat loss list); the runbook is cross-linked from SKILL.md; the parity class is declared.

## Phase 4 - Codex-primary bootstrap entry point (half day, OPEN; reconciled with the merged plan)

### Scope

`bootstrap.{sh,ps1}` currently sets up Claude defaults: `~/.claude/settings.json` merge, PreToolUse hook (`guard.py`), SessionStart hook (`session_bootstrap.py`). A Codex-primary install needs the analogue, but the flag must not conflate primary-agent choice with whether Claude is configured at all.

### CLI contract

Keep the parent's two-flag design; do not narrow it to `--primary codex` only (the 2026-05-28 plan dropped `--primary claude`, which is worth keeping as a symmetric no-op for scripting and explicitness):

- `--primary <claude|codex>`: which agent is the primary workhorse (default `claude` for back-compat). Does NOT by itself disable Claude config. `--primary claude` is accepted and is a no-op relative to the default.
- `--skip-claude-user-setup`: allowed only with `--primary codex`. It creates codex-only mode by leaving `~/.claude/` untouched.
- `--skip-claude-user-setup` with the default or explicit Claude primary exits non-zero with a clear message.

### Semantics

- Default remains Claude-primary; no-flag bootstrap reproduces the pre-Phase-4 Claude setup.
- `--primary codex` heals `~/.codex/config.toml` (or `%USERPROFILE%\.codex\config.toml`): `model = "gpt-5.6-sol"` (or the current highest-capability generally available model; do not freeze this string), `model_reasoning_effort = "max"` for maximum single-agent reasoning, `service_tier = "fast"`, `[features] fast_mode = true`. `ultra` is an explicit opt-in when automatic task delegation is intended, not a higher effort. Preserve unrelated keys; do not rewrite when already current; create the parent directory if missing.
- `--primary codex` still performs Claude setup unless `--skip-claude-user-setup` is also passed (reversal mode needs Claude installed as the reviewer half).
- Print one line naming the active primary mode and any degraded features (using the Phase 3 function-mapping, not a flat loss list).

### Re-add the dropped inventory step

The 2026-05-28 plan dropped the parent's "codex-side hook equivalent" inventory. Restore it: Codex has no SessionStart-hook equivalent, so the Codex config does not self-heal each session the way Claude's does (Claude re-heals via the SessionStart bootstrap hook). Phase 4 must either wire whatever Codex-side trigger exists or document the asymmetry plus a mitigation (a runbook prerequisite: "re-run `bootstrap --primary codex` when the Codex config drifts"). Name it; do not leave it implicit.

### Done when

`bash bootstrap.sh --primary codex` produces a working Codex-primary setup with Claude config still healed (reversal mode). `--primary codex --skip-claude-user-setup` produces codex-only mode with `~/.claude/` untouched. No-flag bootstrap reproduces the pre-Phase-4 `~/.claude/settings.json` merge result in a temp-consumer fixture. `bash bootstrap.sh --skip-claude-user-setup` (alone) and `--primary claude --skip-claude-user-setup` both exit non-zero with a clear message, with fixture tests pinning both rejections. An existing `config.toml` with unrelated keys is preserved. The Codex-config self-heal asymmetry is documented with its mitigation.

## Phase 5 - Cross-agent docs (half day, OPEN)

### Scope

`README.md` and the aa RTD docs currently show Claude-centric examples (install via `claude install`, first-run via `claude /implement-review`). Add parallel Codex-centric examples. This is distinct from the Phase 3 runbook: the runbook is the operational how-to; Phase 5 is the public onboarding surface. Both are needed; neither replaces the other.

### Suggested approach

For each install-flow / first-run doc, add a tab or sibling subsection labeled "Using Codex as primary" with the analogous commands, and link to `docs/codex-primary.md` for the full loop. Do not duplicate the narrative; only the commands.

### Done when

A reader can pick "Claude" or "Codex" at the install-flow entry point and complete onboarding without cross-referencing the other tab.

## Phase 6 - health-check.py reviewer-agnostic (1 day, OPEN, SYMMETRY-BLOCKING, HIGHEST PRIORITY)

### Why this is the highest-priority remaining symmetry gap

`health-check.py` exists to catch a reviewer that silently failed or stalled. Its `TOOL_FAILURE_PATTERNS` are Codex failure shapes (1312, `createprocessasuserw`, `windows sandbox`, rate-limit 429). In Codex-primary mode the reviewer is Claude, so the health check watches for the wrong agent's failure signatures. The failure that motivated the whole Phase 2 rework (`e25e993`) was a Claude reviewer silently hanging, which is precisely the class a Codex-tuned health-check is least able to detect. Health check is one of the four named core functions; running it on a Claude tail without Claude patterns means the loop completes but the safety net is blind. `e25e993` added `tail.stderr-tmp` scanning to Check 8 but did not add Claude failure patterns or a reviewer switch, so this stays substantively open.

### Suggested approach

Split the pattern list and add a `--reviewer <codex|claude|copilot>` flag (auto-detect from the `Review-<Name>.md` filename when possible):

- **Reviewer-agnostic** patterns: rate-limit indicators, generic "tool call failed" markers, exit-code-like patterns.
- **Reviewer-specific** patterns: Codex-side (`createprocessasuserw`, `windows sandbox`), Claude-side (survey the Claude headless failure envelopes, including the silent-hang signature from `e25e993`, plus auth/bare-mode and permission-prompt stalls), Copilot-side as needed.

### Done when

`health-check.py --reviewer claude` runs against a committed Claude tail fixture and produces the expected WARN-breakdown labels per a pinned assertion (`tests/test_health_check.py::test_claude_reviewer_breakdown`), including a label for the hang signature. `--reviewer codex` continues to produce the existing Codex-side labels against existing fixtures.

## Phase 7 - Test coverage for dispatch-claude (1 day, SHIPPED 2026-05-28, with caveat)

### What shipped

`tests/test_dispatch_claude.py` mirrors the dispatch contract suite, is in the `check-parity.sh` STRICT block, and is byte-mirrored ac↔aa; `tests/test_health_check.py` picked up the new `tail.stderr-tmp` and Check-5 cases. Both run green in ac + aa CI.

### Caveat (motivates Phase 7.5)

These are command-string / mock-argv tests. They assert the constructed invocation (flags, allow-list, guard presence, parity), not the live CLI's runtime behavior. They were all green while the live `claude -p` invocation hung on Windows (`e25e993`). The contract suite is necessary and stays; it is not sufficient on its own.

## Phase 7.5 - Automated live-dispatch smoke (half to 1 day, OPEN, NEW 2026-05-28)

### Scope

Add a cheap, gated, end-to-end probe that actually invokes a reviewer through `dispatch-<reviewer>` and confirms a `Review-*.md` is written with a valid Round marker. This is the safety net that mock tests structurally cannot provide, and it is the direct lesson from `e25e993`. Without it, the next Claude (or Codex, or Copilot) CLI version bump can silently re-break a reviewer path exactly as 2.1.153 did.

### Suggested approach

Fold in the 2026-05-28 plan's integrated-validation steps as the smoke body:

1. Stage a one-line change in a scratch repo.
2. Dispatch the reviewer (each direction: Codex-primary → Claude review, Claude-primary → Codex review, and → Copilot).
3. Confirm the expected `Review-*.md` exists, starts with the Round marker, and is non-trivial.
4. Confirm no unintended files except the review artifact, and that `health-check` (Phase 6) flags an injected failure fixture.

Two tiers, to keep cost down:
- **Mock-binary tier** (runs in CI always): a stub `claude`/`codex`/`copilot` on PATH that emits a canned review to stdout, exercising the full dispatcher wrapper (relay prompt, staged snapshot, stdout→file, marker normalization, exit-code passthrough) without an API call.
- **Real-binary tier** (gated like `real-agent-smoke.yml`: release / manual dispatch): one real round-trip per reviewer to catch live permission/auth/hang regressions.

### Done when

The mock-binary smoke runs in ac + aa CI on every push and fails if any dispatcher wrapper step breaks; the real-binary tier runs on release/dispatch and writes a real `Review-*.md` per reviewer. A simulated silent hang (stub that sleeps past the stall threshold and writes nothing) is caught by the smoke, not just by a human.

## Phase 8 - Pack handler split (spike, likely 3-5+ days after discovery; DEFERRED)

### Scope

The `anywhere-agents` pack lifecycle (compose, verify, install) is currently driven from the Claude side via `bootstrap.{sh,ps1}` and the composer. A truly Codex-primary world needs an equivalent Codex-side pack handler.

### Why deferred

The pack system is not a thin wrapper. The aa composer is ~1,881 lines and the pack CLI is ~3,600+ lines spanning state, reconciliation, and per-pack handler modules. A Codex-side mirror is a structural change to the distribution, not a refactor. A proper spike is the right pre-implementation step. The composer already exposes `pack add / list / update / verify --fix` as the maintainer-side surface, so the gap is interface plumbing under structural complexity, not feature design.

### Re-evaluation trigger

A pack hotfix can land mid-session when a consumer reports a broken pack, so the trigger is: (a) the first time a pack hotfix is needed while Claude is unavailable (travel, outage, quota), OR (b) before known restricted travel with expected pack work, OR (c) when the v1.0.0 architecture rework refactors the composer anyway. Trigger (a) escalates the spike from "deferred" to "blocking" with whatever time the maintainer has.

## Phase 9 - Cross-agent quota visibility / statusline symmetry (OPEN, P2, contingent)

### Scope

`scripts/statusline.py` (the Claude Code statusLine) already shows both agents: Claude 5h/7d from the statusLine stdin `rate_limits` (2.1.80+ Pro/Max), and Codex 5h/7d read from `~/.codex/sessions/**/rollout-*.jsonl` `payload.rate_limits`. Inside Claude Code the view is already symmetric. The gap is the reverse: a Codex session has no equivalent always-on view of both agents' usage and 5h / 7d remaining.

### Feasibility (grounded in statusline.py)

- **Data: feasible, half-built.** Codex quota is already on disk and statusline.py already parses it. Claude quota currently arrives only via Claude Code's statusLine stdin and is not persisted. The small addition is to have statusline.py write the latest Claude `rate_limits` to a cache file (e.g., `~/.claude/rate-limits-cache.json`) on each render. After that both agents' 5h / 7d live on disk, readable from any context.
- **Rendering: uncertain, the real gate.** Whether the combined line can live in Codex's own TUI depends on whether Codex exposes a custom status/footer hook. There is no such key in the current `~/.codex/config.toml`, and it is not confirmed to exist. Verify Codex's statusline-customization support before committing this as TUI-embedded work.
- **Reliable fallback regardless of Codex TUI support.** A standalone `agent-quota` command (reads both on-disk caches, prints the same `Claude 5h .. · 7d .. | Codex 5h .. · 7d ..` line) gives symmetric visibility in any terminal, in either agent, without depending on Codex's TUI. Build this if the TUI hook does not exist.

### Done when

statusline.py persists Claude `rate_limits` to a disk cache; a single command renders both agents' 5h / 7d from disk and runs in any terminal; if (and only if) Codex supports a status/footer hook, the same renderer is wired there. Otherwise the standalone command is the delivered form and the Codex-TUI half is recorded as a known gap with its blocker.

### Progress 2026-05-28 (prototype landed + tested)

Data half done and verified end-to-end: `scripts/statusline.py` now persists Claude `rate_limits` to `~/.claude/rate-limits-cache.json` on each render (atomic, best-effort, display unchanged; STRICT-mirrored to aa), and `scripts/agent-quota.py` reads both agents off disk and prints a two-row `Claude / Codex · 5h / 7d` view that runs in any terminal. Confirmed with real data on Windows. Update 2026-05-28: `agent-quota.py` is now wired into the bootstrap user-level deploy in both `bootstrap.ps1` and `bootstrap.sh` (copied to `~/.claude/agent-quota.py` alongside `statusline.py`) and mirrored to aa; check-parity STRICT clean and the bootstrap preflight test green. The tool is therefore portable with zero per-machine install. The Codex-TUI feasibility check is done and negative: `codex --help` + `codex doctor` expose no custom statusline hook (only terminal title, model, sandbox, approval, profile), so an always-on statusline inside Codex's own UI is not possible. Round 2 of the /implement-review pass completed the STRICT item (`scripts/agent-quota.py` is now in `check-parity.sh` strict_files and the `tests/test_check_parity.py` fixture, parity clean). Remaining: a stable cross-shell shim/alias; decide the auto-display path (the maintainer uses Codex in the terminal, not the JetBrains plugin, and the TUI occupies the screen, so the implement-review touchpoint below is the practical surface; a shell-prompt hook is the only other terminal-side option); and a bootstrap Codex-config healer for the verbose-output reduction. Correction 2026-05-28: the verbose `Automatic approval review approved ... / Auto-reviewer approved codex ...` blocks come from `approvals_reviewer = "guardian_subagent"` in `config.toml`, not `[desktop] conversationDetailMode` (which is plugin-only and moot for terminal use). That key's alternative values and any quiet mode are not discoverable from `codex --help` or the npm install (config-only key compiled into the Rust binary), so the clean-but-safe setting is found by non-destructive experiment (`codex -c <key>=<value> --strict-config`, `--ask-for-approval <mode>`) and only then baked into the healer. Surfacing-by-touchpoint instead of by statusline (shipped 2026-05-28): the implement-review `SKILL.md` Prerequisites step now runs `agent-quota` at every skill start and shows the two-row quota, in both agent directions — a ~0.1s local read, mirrored to the aa source tree and the wheel composer, parity clean. This is the practical answer to "show quota in Codex" given the missing statusline hook; it is an orchestrator instruction (prose), acceptable here because a missed quota print is harmless, with a hard-wired dispatch/health-check embed as the escalation if it is ever skipped.

### Not blocking

P2. Does not gate any core-function symmetry and does not block deletion of this file.

## Effort summary

| Phase | Effort | Critical path? | Status |
|---|---|---|---|
| 0 - CLAUDE.local.md principle (local-only) | 5 min | no (local-only) | Done 2026-05-16 |
| 0.5 - Promote principle to AGENTS.md | half day | yes | Done 2026-05-19 |
| 1 - SKILL.md refactor | 1 day | yes | **Open (symmetry-blocking)** |
| 2 - dispatch-claude scripts | 3-5 days | yes | **Shipped 2026-05-28** |
| 2.5 - dispatch-review selector | half day | no | Open (new) |
| 3 - AGENTS.md section + runbook | half day | yes | Open (concretized) |
| 4 - Codex-primary bootstrap | half day | yes | Open (reconciled) |
| 5 - Cross-agent docs | half day | no | Open |
| 6 - health-check reviewer-agnostic | 1 day | **yes (symmetry-blocking)** | Open (highest priority) |
| 7 - dispatch-claude tests | 1 day | yes | **Shipped 2026-05-28** |
| 7.5 - Automated live-dispatch smoke | half-1 day | yes | Open (new) |
| 8 - Pack handler split | spike, 3-5+ days | no | Deferred |
| 9 - Cross-agent quota visibility | half day (+ spike on Codex TUI) | no | Open (P2, contingent) |

**Remaining critical path to real symmetry**: Phase 6 (health-check) and Phase 1 (SKILL.md) are the load-bearing opens; Phase 3 + Phase 4 deliver the entry points; Phase 7.5 is the regression net; Phase 2.5 hardens reviewer selection. Phase 5 (docs) and Phase 8 (pack split) are not on the symmetry critical path.

## Sequencing

1. Phases 0, 0.5, 2, 7 done. dispatch-claude exists and works headless; tests gate the contract (with the Phase 7 caveat).
2. **Phase 6 first among the remaining**, because it is the safety net for the silent-reviewer-failure class that just bit Phase 2, and because Phase 7.5's failure-injection step depends on it.
3. Phase 1 reconciles SKILL.md before or alongside Phase 3, so the canonical doc and the runbook do not drift.
4. Phase 3 + Phase 4 deliver the entry points; both are unblocked now that Phase 2 shipped.
5. Phase 2.5 (dispatch-review) lands before or with Phase 3, so the runbook can point at the selector script instead of prose.
6. Phase 7.5 lands next to Phase 6 (the smoke exercises the reviewer-agnostic health-check).
7. Phase 5 (cross-agent docs) any time after Phase 3.
8. Phase 8 stays deferred until its trigger fires.

## Cross-references

- `AGENTS.md` § "Agent Fungibility" - the shared principle (promoted in Phase 0.5)
- `AGENTS.md` § "Session Start Check" - the Codex banner-via-first-response convention referenced by the Phase 3 degradation mapping
- `CLAUDE.local.md` § "Agent fungibility" - maintainer-local pointer (gitignored; not the shared source)
- `skills/implement-review/SKILL.md` Phase 1c - current Codex-default dispatch language (Phase 1 target)
- `skills/implement-review/scripts/dispatch-codex.{ps1,sh}` - the reference implementation mirrored for Claude and Copilot
- `skills/implement-review/scripts/dispatch-claude.{ps1,sh}` + `_claude_guard.ps1` - shipped Phase 2 (feat `102ab2c`, fixes `63dd90e`, `e25e993`)
- `skills/implement-review/scripts/dispatch-copilot.{ps1,sh}` + `tests/test_dispatch_copilot.py` - shipped 2026-05-22 third-agent reviewer
- `tests/test_dispatch_claude.py`, `tests/test_health_check.py` - shipped Phase 7 (STRICT, byte-mirrored)
- `2026-05-28-codex-primary-symmetry-plan.md` - merged into this file 2026-05-28; that doc is now a pointer
- [`2026-05-16-implement-review-auto-followups.md`](2026-05-16-implement-review-auto-followups.md) - STRICT-mirror doctrine for shared-contract tests (Item 2) and AV-avoidance lessons (Item 6)

## Delete this file when

Phases 1, 3, 4, 5, 6, 7.5 land (Phases 0, 0.5, 2, 7 already done; Phase 2.5 is a hardening add). After that the principle is in `AGENTS.md` proper and the operational primitives exist. Phase 8 deferral can persist indefinitely without blocking deletion of this file.
