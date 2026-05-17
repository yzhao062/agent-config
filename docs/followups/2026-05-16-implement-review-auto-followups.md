# PLAN-implement-review-auto-followups (post-ship triage)

**Status**: 6 follow-up items + 4 dismissed concerns captured. All 6 items completed by end of day 2026-05-16: Item 3 (Spark validation) and Item 4 (random / NSF dogfood) closed earlier; Items 1 (Check 8 FP), 2 (aa test mirror), 5 (health-check arg doc) shipped as the Items-1+2+5 batch; Item 6 (WSL stub `bash` mitigation) surfaced during that batch's Round 1 review and bundled into the same commit.
**Owner**: Yue (driver) + Claude (implementer when invoked).
**Parent work**: [`2026-05-15-implement-review-auto-terminal.md`](2026-05-15-implement-review-auto-terminal.md) (Auto-terminal channel design) + ac `90fe721` (dispatcher hardening + guard auto-allow) + ac `7fa0559` (Codex sandbox 1312 bypass + retry doctrine).

## Why this file exists

The 2026-05-16 ship closed the Codex-Windows-1312 problem end-to-end. Three review rounds + an embedded-diff retry dry-run validated `--sandbox danger-full-access` as the primary fix and turned the retry path into a sandbox-strict-environment fallback. The review loop surfaced four items correctly out of scope for that commit; consumer-project dogfood surfaced a fifth (Item 5); the Items-1+2+5 batch's own Round 1 review surfaced a sixth (Item 6 -- a distinct 1312 class triggered by the WSL launcher stub when Codex tries `bash <script>` tool calls). All six are now closed. A separate "Functional concerns considered and dismissed" section captures four non-issues evaluated during the same loop, so the next round does not re-derive their resolution.

## Item 1 — Check 8 prompt-content false-positive

### Symptom

Running `/implement-review auto` on changes that touch the 1312 / sandbox pattern set itself produces a high Check 8 marker count even when Codex's actual tool calls run cleanly. Observed: Round 2 ac review = 139 markers, Round 3 = 151 markers. Real 1312 count in the same runs: 0.

### Root cause

`health-check.py` Check 8 scans the entire `<state-dir>/tail` for `TOOL_FAILURE_PATTERNS`. The tail contains Codex's full stdout+stderr, which includes Codex's own reasoning text where it echoes prompt fragments and diff hunks. When the change under review *is* `skills/implement-review/scripts/health-check.py` (or SKILL.md's Check 8 description, or the prompt that names the patterns), the pattern strings appear inside the echoed content. Check 8 fires on them as if they were real errors.

This is the same FP class Check 7 already handles. SKILL.md:309 documents:
> Check 7 firing on Codex's own meta-discussion of the regex pattern list. Mitigated: Check 7 excludes content inside backtick code spans.

Check 8 has no analogous exclusion.

### Suggested approach

Add a structural exclusion to Check 8 similar to Check 7's. Two candidate shapes:

- **Narrow** — Check 8 excludes content inside backtick code spans (same as Check 7).
- **Broad** — Check 8 also excludes content inside the recorded prompt body. The dispatch writes the prompt to a known file; health-check can subtract that prefix from the tail before scanning.

Narrow first. Test the marker count drop on a `health-check.py` self-edit review. If still noisy, layer in broad.

### When to pull in

When a real /implement-review run produces > 0 unexplained Check 8 markers AND substance heuristics also flag. Until then the existing WARN + Proceed-or-Downgrade flow handles it.

### Effort estimate

Half a day. One regex addition + one test fixture that mimics Codex meta-discussing the pattern list + one SKILL.md doc line in the False-positive tuning principle section.

## Item 2 — aa-side test backport (or formalize `tests/` in STRICT mirror)

### Symptom

ac `7fa0559` updated `tests/test_dispatch_codex.py` to accept the new `exec --sandbox <mode> -` arg shape. aa's `tests/` is NOT in the cross-repo STRICT mirror (per `scripts/check-parity.sh` since v0.4.0), so the test update did not propagate. aa CI ran the OLD assertion against the NEW dispatcher across all 7 matrix entries (Ubuntu 3.10/3.11/3.12/3.13, Windows 3.12/3.13, macOS 3.13) and failed every one with `AssertionError: '--sandbox' != '-'`. Fixed in aa `1295c60` by re-applying the assertion change manually.

### Root cause

Two coupled facts:

1. The skill's runtime contract source-of-truth (`skills/implement-review/scripts/dispatch-codex.{ps1,sh}`) is in STRICT mirror: a change in ac flows to aa byte-identically and CI gates both sides.
2. The tests that pin that contract (`tests/test_dispatch_codex.py`) are NOT in STRICT mirror. Each repo has its own copy, drift-friendly.

Result: when the runtime contract changes, the runtime files mirror automatically but the tests do not. CI on the aa side runs the stale tests against the fresh code. The class of failure repeats every time we add a substantive contract change to dispatch / health-check / guard, exactly when we want CI to catch a regression.

### Options

**Option A — Backport ac's new test ADDITIONS to aa** (narrow): copy the runtime sandbox-flag tests, the isolated Check 8 fixtures, the SKILL.md doc tests, the pointer slash-arg test from ac to aa. Keeps the existing "tests are aa-local" architecture but eliminates the gap for the specific tests that pin the shared skill contract.

**Option B — Add the overlapping tests to STRICT mirror** (formal): extend `scripts/check-parity.sh` STRICT block with `tests/test_dispatch_codex.py`, `tests/test_health_check.py`, `tests/test_guard.py`, `tests/test_prompt_byte_parity.py`. Each repo can still have its own additional test files (aa's `test_compose_packs.py`, ac's `test_repo.py`, etc.); only the shared-contract tests are gated.

**Option C — Leave it, fix gaps reactively** (status quo). Cost: each round of skill changes risks aa CI breakage; the aa `1295c60` pattern repeats.

### Recommendation

Option B. The fact that `tests/test_dispatch_codex.py` failing is a SIGNAL — both sides should run that test against the shared dispatcher. The other shared-contract tests are the same shape. Option A solves the immediate gap but the next change re-opens it; Option B turns the gap into a release-gate property.

### When to pull in

Before the next substantive shared-skill change (Auto-terminal extension, guard auto-allow addition, health-check pattern change). The cost is one `check-parity.sh` edit + one round of cp tests across repos.

### Effort estimate

Two hours: `check-parity.sh` STRICT list extension + cp the 4 test files ac→aa + one ac+aa CI run to confirm parity gate holds.

## Item 3 — Ubuntu Spark cross-platform validation

### Symptom

All 2026-05-16 validation happened on Windows. The dispatcher contract is identical across `.ps1` and `.sh`, but the `.sh` path has not been exercised against a real Codex install on Linux this cycle. ac CI runs the .sh contract tests on Ubuntu 3.10–3.13 (the bash-only DispatchCodexBashTests class fires), but those use a mock codex, not the actual Codex CLI.

### What to validate

Three things on Spark, in order of value:

1. **`codex --version` resolves to a runnable binary on Spark's PATH** — same shape as the Windows live-PATH test in `test_dispatch_path_resolution.py`. Reads only; cheap.
2. **`echo "Run: git --version" | codex exec --sandbox danger-full-access -` returns non-error** — same probe as 2026-05-16 Windows confirmation. Validates that the Linux Codex sandbox bypasses cleanly too (or detects if Linux has the same workspace-write bug — would be useful prior art).
3. **One real `/implement-review auto` round on a tiny staged change** — full end-to-end. Validates the .sh dispatcher + auto-watch + health-check + the embedded-diff retry path if Linux Codex has its own quirks. Token cost: one codex-exec call.

### Completed 2026-05-16

Validated end-to-end on Ubuntu Spark (Linux aarch64, Codex 0.121.0):

1. `codex --version` resolved cleanly on Spark PATH.
2. `echo "Run: git --version" | codex exec --sandbox danger-full-access -` returned `git version 2.45.x` with no 1312 — confirms the Linux Codex sandbox bypasses cleanly under the same flag that fixes Windows.
3. `python3 -B -m unittest discover -s tests`: 339 tests passed, 0 failures. Bash dispatch lane confirmed against the shared `dispatch-codex.sh` (byte-identical with Windows source per STRICT mirror).

No Linux-specific quirks surfaced. The `.sh` path of the fix is validated against a real Codex install, not just the mock-codex CI tests.

## Item 4 — Random dogfood: validate the user-facing flow

### Symptom

The fix is shipped to `main` on ac + aa. Consumer projects need to bootstrap again to pull the updated `dispatch-codex.{ps1,sh}` + `health-check.py` + `SKILL.md` + pointer. Until that happens, /implement-review in random keeps using the pre-7fa0559 dispatcher (Codex sandbox 1312 will still fire, no retry coverage).

### Procedure

1. Open Claude Code in `~/PycharmProjects/random`.
2. SessionStart hook should fire bootstrap (CLAUDE.md mandates it for consumer repos). If not, `pwsh .agent-config/bootstrap.ps1` manually.
3. Verify `~/.claude/skills/implement-review/scripts/dispatch-codex.ps1` md5 matches ac source: should be `9862d7764f5a8150c6cf91df6bc1abc1` (or whatever the SHA is at next bootstrap).
4. Stage one real change, run `/implement-review auto`.
5. Check Phase 2.0 health-check output: Check 8 should report 0 real markers (any markers should be prompt-content FP per Item 1).
6. Confirm Codex's review contains substantive findings, not "could not access files".

### Completed 2026-05-16

Validated in two consumer projects:

**random** (`~/PycharmProjects/random`):

- Bootstrap pulled updated `dispatch-codex.ps1` + `health-check.py` + `SKILL.md` + pointer.
- `/implement-review auto` dispatched cleanly via Auto-terminal.
- Phase 2.0 health-check: Check 8 WARN with prompt-content markers (FP per Item 1, 0 real 1312); all other checks PASS; substance heuristics PASS; dispatch exit 0.
- Codex produced a substantive review (not "could not access files").

**NSF-Proposal-Template-Yue** (`~/PycharmProjects/NSF-Proposal-Template-Yue/reports/nsf-pose-openad-2346158/yr2-2026-annual/`):

- Same bootstrap + dispatch flow.
- Round 1 review found 3 real Highs + 3 Mediums (par-upload-checklist self-contradiction, 02-products missing D1-D4 + author errors, 03-participants stale). All Highs Phase 2.5-verified before fix-apply. Round 2 verification dispatched after fix-apply.
- Phase 2.5 trigger fired correctly per the new SKILL.md doctrine (Round 1 had Highs touching substantive content → Round 2 auto-dispatched).

Both runs exercised the full Auto-terminal pipeline: dispatcher PATH resolution, `--sandbox danger-full-access` default, dispatch + auto-watch loop, health-check phase, and Phase 2.5 verification gate.

## Item 5 — Health-check arg-contract documentation tightening

### Symptom

The `health-check.ps1` / `health-check.sh` script signature requires three args: `--state-dir <path>`, `--round <int>`, `--review-file <path>`. SKILL.md Phase 1c step 6 names `--state-dir` clearly but the other two are referenced less prominently. Observed during dogfood: random's Claude invoked `health-check.ps1 --state-dir ...` without `--round` on the first call (script errored), then re-read the contract and retried with the full arg set. NSF's Claude invoked all three args on the first call.

The system recovers (Claude sees the error and re-reads SKILL.md), so no run failed end-to-end. But the recovery costs a tool round-trip and a misleading "step 6 failed" surface.

### Root cause

SKILL.md Phase 1c step 6 reads (approximately):

> Run `<repo>/skills/implement-review/scripts/health-check.{ps1,sh} --state-dir <abs-path>` and capture the structured pass/fail table.

The `--round <int>` and `--review-file <path>` args are documented elsewhere (script `--help`, the contract test), but a fresh reader scanning Phase 1c may not click through. The fix is to inline all three required args in the step-6 example so the call shape is unambiguous from the SKILL.md alone.

### Suggested approach

Update Phase 1c step 6 to show the full invocation:

> Run `<repo>/skills/implement-review/scripts/health-check.{ps1,sh} --state-dir <abs-path> --round <N> --review-file <path>` and capture the structured pass/fail table.

Cross-check the script's `argparse` definition and update the SKILL.md text to match (currently the script accepts `--round` as `int` and `--review-file` as the path to read).

### When to pull in

Before the next consumer-side dogfood round, OR bundled with the next substantive SKILL.md edit. Not load-bearing — the system recovers — but tightening the contract eliminates one tool round-trip per session.

### Effort estimate

30 minutes. One SKILL.md edit + one assertion in `tests/test_prompt_byte_parity.py` that pins the new doc text to the script's argparse contract.

## Item 6 — WSL launcher stub interception of Codex's `bash` tool calls

### Symptom

Surfaced 2026-05-16 during Round 1 of the Items 1+2+5 batch review. The review prompt focused on staged `check-parity.sh` changes, so Codex (correctly) tried to verify by running `bash scripts/check-parity.sh`. On the maintainer's Windows host, PATH `bash` resolves to the WSL launcher stub (`C:\Windows\System32\bash.exe`, or the Microsoft Store WSL alias under `WindowsApps\`). The WSL stub requires elevation-token resolution that `CreateProcessAsUserW` cannot supply from Codex's spawn context, so the tool call failed. Result: 30 `CreateProcessAsUserW failed: 1312` errors in `<state-dir>/tail`, burst within 51 ms. Codex fell back to `C:\Program Files\Git\bin\bash.exe` explicitly and completed the review with substantive findings, but the noise polluted Check 8 and could mask real failures in a future run.

### Root cause

Distinct from the workspace-write sandbox 1312 bug that `--sandbox danger-full-access` handles. That fix made Codex skip its OWN sandbox restrictions for outer-level subprocess spawn. But the OS-level spawn primitive is still `CreateProcessAsUserW` (Codex's sandbox runner's spawn machinery on Windows), and `CreateProcessAsUserW` fails for any subprocess that itself needs elevation-token brokering -- the WSL stub is one such case (it brokers a syscall to the WSL service, requires session-token chain).

So `--sandbox danger-full-access` is correct and unchanged; what surfaces here is a separate condition: the specific subprocess (WSL stub) cannot be spawned via the underlying Win32 API Codex uses.

### Completed 2026-05-16: signal-layer fix, not runtime prevention

Fixed in the same commit as Items 1+2+5, but the implementation is **NOT** a runtime PATH mitigation. Two PATH-prepend approaches were attempted and reverted in-flight:

1. PowerShell `$env:PATH = "$gitBashBin;$env:PATH"` -- triggers Bitdefender's PATH-hijacking heuristic and blocks `dispatch-codex.ps1` from loading entirely. Verified live: `ParserError: This script contains malicious content and has been blocked by your antivirus software.`
2. cmd helper injection `IF EXIST "C:\Program Files\Git\bin\bash.exe" SET "PATH=C:\Program Files\Git\bin;%PATH%"` injected before the `codex exec` line -- still triggers the same heuristic because the literal `SET "PATH=...;%PATH%"` string appears in the PowerShell source that constructs the cmd body.

Both block the dispatcher entirely, which is strictly worse than the noise. The mitigation lives at the SIGNAL layer instead:

- `skills/implement-review/scripts/health-check.py` Check 8 now emits a per-pattern breakdown alongside the marker total when WARN fires: `WARN check-8 N tool-failure-markers breakdown=createprocessasuserw:30 windows:24 sandbox:24 rate:13 429:11 ...`. Pattern labels derive from the longest word run in each `TOOL_FAILURE_PATTERNS` entry, lowercased, capped at 20 chars, sorted by count descending.
- SKILL.md FP-tuning principle subsection catalogues the WSL-stub-bash 1312 shape (envelope co-occurrence of `createprocessasuserw` + `windows` + `sandbox` patterns; Substance heuristics pass; review-mtime fresh) as a known graceful-fallback noise pattern. Downstream Claude reads the breakdown, matches against the catalogue, and Proceeds without user escalation when the shape fits.
- User-side resolution path (optional, out of skill scope): remove the WSL stub from PATH or reorder PATH so `C:\Program Files\Git\bin` precedes `C:\Windows\System32`. Subsequent Auto-terminal runs then emit 0 WSL-stub 1312 markers.

### Why this is a real fix despite no runtime prevention

The user-facing complaint was "Check 8 reports 91 markers, looks broken even when review succeeded". The signal-layer fix solves that exactly:

- Before: `WARN N markers` (opaque), downstream Claude has to grep tail to classify
- After: `WARN N markers breakdown=...` (transparent), downstream Claude matches against doctrine and proceeds in one read

Codex's tool dispatch behavior is unchanged (still hits 1312 on WSL stub); the noise still appears in tail. But the signal that flows to the human and downstream agents is now actionable and correctly categorized.

### Why bundled into the same commit

Surfaced during Round 1 of the Items 1+2+5 review (live test of Item 1 backtick exclusion -- the Check 8 91-marker count looked like residual FP but was actually 30 real WSL-stub 1312s + remaining other patterns). Treating it as a separate followup would have left a confusing signal whenever a Windows + WSL-stub user reviews `.sh` files (which the next aa shared-skill change always involves). Bundling closes the doctrinal loop in one ship cycle.

### Future improvements (not blocking)

- Codex upstream issue: ask whether Codex can detect the WSL launcher stub via process-image inspection (e.g., `bash.exe` under `System32\` or `WindowsApps\` with a known PE timestamp signature) and fall back to alternative bash without surfacing the 1312 envelope at all. This would prevent the noise at source without consumer-side PATH manipulation.
- AV-safe runtime PATH mitigation, if Codex declines the upstream fix: construct the cmd `SET PATH=...` line via string fragments that never appear adjacent in source (e.g., split `'PATH'` and `'%PATH%'` across multiple assigned variables before concatenation). Fragile and would need re-testing as Bitdefender signatures evolve.

## Functional concerns considered and dismissed

The 2026-05-16 review loop also surfaced four functional concerns that were evaluated and ruled out. Capturing them here so the next round does not re-derive the reasoning.

### Sandbox flag default = `danger-full-access`

**Concern:** The default sandbox mode in `dispatch-codex.{ps1,sh}` was switched from Codex's implicit `workspace-write` to explicit `danger-full-access`. Is this a silent trust-model expansion?

**Resolution:** No. The user enters the Auto-terminal channel only by explicit opt-in (typing `/implement-review auto`, `cli`, or `auto-terminal`). The trust posture is identical to Terminal-relay — both run Codex with unrestricted local access. SKILL.md:94 documents the trust-model alignment. `CODEX_DISPATCH_SANDBOX` is available as an env override for CI / sandbox-strict environments.

### No macOS CI coverage against a real Codex install

**Concern:** ac CI runs Ubuntu 3.10-3.13 + Windows 3.12/3.13 + macOS 3.13. The macOS lane covers Python compatibility but not the dispatcher's `--sandbox` flag against a real macOS Codex install (CI uses mock-codex).

**Resolution:** Low risk. `--sandbox` is a Codex CLI argument, not an OS-specific system call. Ubuntu Spark validation (Item 3) confirmed the flag works on Linux. The `.sh` dispatcher is shared between Linux and macOS by design. If macOS Codex has its own sandbox-runner quirk, the retry path in SKILL.md:100 catches it.

### `--sandbox` deprecation or rename in a future Codex version

**Concern:** If Codex changes the `--sandbox` flag semantics or removes it, every Auto-terminal dispatch fails at parse time.

**Resolution:** Covered by SKILL.md:100 "future-regression" retry exception. A parse-time fail surfaces as a non-zero exit; the Phase 2.0 health check fails its "dispatch exit 0" gate; the user sees the error directly. No silent degradation. The retry doctrine (line 96) explicitly covers this case as one of the conditions that legitimizes the embedded-diff retry path.

### `CODEX_DISPATCH_SANDBOX` env override not end-to-end tested

**Concern:** `test_codex_invoked_with_overridden_sandbox_flag` asserts `--sandbox workspace-write` reaches argv through the env var, but uses mock-codex. The override's behavior against a real Codex sandbox-strict environment was not E2E-tested.

**Resolution:** Low priority. The override is only used when (a) running in a sandboxed CI environment or (b) a future Codex version makes `danger-full-access` unavailable. Both are narrow trigger conditions. The mock test pins the dispatcher's arg-handling correctness, which is the part the dispatcher controls; the rest is Codex's responsibility.

## Cross-references

- ac `7fa0559` commit: full message has the load-bearing context.
- aa `2de6c32` + `1295c60`: mirror sync + CI repair.
- `skills/implement-review/SKILL.md:94-100`: trust-model and retry-fallback doctrine.
- `skills/implement-review/scripts/dispatch-codex.{ps1,sh}`: --sandbox + CODEX_DISPATCH_SANDBOX implementation.
- `tests/test_dispatch_codex.py`: DispatchSandboxFlagContract + runtime argv assertions.

## Delete this file when

Both remaining items (1 and 2) are either landed or explicitly dropped, AND a follow-up plan has subsumed any new concerns. Until then keep it discoverable so the next round of /implement-review work picks up the same context instead of rediscovering it.
