<!-- Round 1 -->

Intended file: `Review-Antigravity.md`

## Verification notes

All commands ran from `/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-19a404ca-round1-12586-430da0558b384b75/staged-snapshot` using `$HOME/miniforge3/envs/py312/bin/python`:

- `"$HOME/miniforge3/envs/py312/bin/python" -m unittest tests/test_skill_size.py tests/test_skill_md_contract.py tests/test_pointer_files.py tests/test_prompt_byte_parity.py -v && wc -c skills/implement-review/SKILL.md`: exit 0; 64 tests ran (59 passed, 5 Windows-only PowerShell byte-parity tests skipped). `skills/implement-review/SKILL.md` is 65,597 bytes (196 bytes under the 65,793-byte ceiling in `tests/test_skill_size.py`).
- `"$HOME/miniforge3/envs/py312/bin/python" -m unittest tests/test_skill_size.py tests/test_skill_md_contract.py tests/test_repo.py tests/test_pointer_files.py tests/test_line_endings.py -v`: exit 1; 10 failures exclusively in `test_repo.py` and `test_line_endings.py` caused by `git ls-files` failing (`fatal: not a git repository`) in the exported non-git snapshot, not by the diff.
- `"$HOME/miniforge3/envs/py312/bin/python" skills/implement-review/scripts/style-audit.py --all-lines CHANGELOG.md skills/implement-review/SKILL.md`: exit 0; 15 pre-existing findings reported. Confirmed that none originate from the changed lines (the `CHANGELOG.md:25` `RULE-C` line anchor belongs to pre-existing `Step 2 ... Step 4 ...` prose at `CHANGELOG.md:27` in the same list).
- `grep -rn "IMPLEMENT_REVIEW_DEFAULT" .` and `grep -rn "DEFAULT_CHANNEL\|DEFAULT_REVIEWER\|IMPLEMENT_REVIEW" scripts/`: exit 0; confirmed no script in `scripts/` or `skills/implement-review/scripts/` reads `IMPLEMENT_REVIEW_DEFAULT_CHANNEL` or `IMPLEMENT_REVIEW_DEFAULT_REVIEWER`, and checked neighboring references in `.claude/commands/vet.md`, `.claude/commands/implement-review.md`, `skills/implement-review/agents/openai.yaml`, `skills/implement-review/references/failover-and-recovery.md`, and `skills/implement-review/references/plan-review.md`.

Verification status: VERIFIED

Commit verdict: PASS

## Scope and Lens

- **Scope**: Staged diff across `CHANGELOG.md` and `skills/implement-review/SKILL.md` (Round 1).
- **Lens**: Code and its documentation (correctness, edge cases, behavior change for existing inputs, tests, internal and cross-file consistency, maintainability), plus mandatory adversarial scope challenge.

## Scope-Challenge Position

- **(a) Why this exact scope**: The staged diff closes a real, observed failure mode: a bare `/vet` under `IMPLEMENT_REVIEW_DEFAULT_REVIEWER=both` silently ran Codex alone for three rounds with no channel line. Removing the competing `{Codex}`-default rule in section 1c (`SKILL.md:191`) fixes an actual contradiction inside `SKILL.md`, and lifting the channel-line and exact-set decision into Step 3 of the round checklist (`SKILL.md:41`) puts the contract in the head of the file while net-shrinking `SKILL.md` by roughly 115 bytes. A strictly smaller scope (changing only section 1c without Step 3, or vice versa) would leave either the checklist blind to the decision or section 1c contradicting Path selection. One low-cost addition within the same file is worth taking now: naming `IMPLEMENT_REVIEW_DEFAULT_CHANNEL` and `IMPLEMENT_REVIEW_DEFAULT_REVIEWER` right in Step 3 (see Finding 3 below), because `grep` confirms no script reads or prints either variable and neither appears in the model's prompt text unless the coordinator checks the environment.
- **(b) Deferrals vs inclusion now**: No code-level enforcement (such as a deterministic `resolve-reviewers.py` helper or printing `IMPLEMENT_REVIEW_DEFAULT_*` from `agent-quota.py`) is included here. Deferring a new resolver script is justified for now: parsing slash tokens, natural-language phrases with negation guards, coordinator identity, and `PATH` probes in a new script carries real design, test, and cross-platform maintenance cost, whereas the 2026-11-17 incident occurred while `SKILL.md` still contained an explicit `{Codex}` contradiction in section 1c. However, if a bare `/vet` drops `IMPLEMENT_REVIEW_DEFAULT_REVIEWER` again after this prose fix lands, another prose edit will be the wrong response; at that point surfacing the two env vars deterministically (for example in the Step 1 preflight output or a small resolver script) should replace further prose hardening.
- **(c) Simplest path**: Yes. Editing the two prose locations in `SKILL.md` (plus the `CHANGELOG.md` entry) without adding a prose-pinning test matches `AGENTS.local.md` (which forbids pinning prose) and `tests/test_skill_md_contract.py` (which checks checklist structure, links, and byte ceilings without pinning step wording).

## Findings

### New

1. **[Medium] `skills/implement-review/SKILL.md:191` conflates within-round failover with cross-round persistence and says "replaces" instead of "adds"**
   - **Problem**: The new line reads:
     > `- **Expected reviewer set**: the set step 3 resolved, carried into later rounds until the user changes it for this review or a failure path replaces a reviewer.`
     This conflicts with `skills/implement-review/references/failover-and-recovery.md:10, 12` and `skills/implement-review/SKILL.md:140` in two ways:
     1. **Lifetime**: `references/failover-and-recovery.md:12` scopes a confirmed failure to that round only ("A confirmed failed attempt is also final for that backend this round"), and `SKILL.md:225` and `references/failover-and-recovery.md:14` state that neither preflight absence nor partial multi-reviewer failure sets sticky downgrade. Placing "or a failure path replaces a reviewer" inside the "carried into later rounds until ..." clause implies that a transient Round 1 failover permanently alters the reviewer set for Round 2+.
     2. **Set update**: `references/failover-and-recovery.md:10` instructs the coordinator to **add** the replacement to the expected reviewer set (keeping the failed backend for consolidation accounting per `SKILL.md:140`), rather than replacing it.
   - **Suggested fix** (`skills/implement-review/SKILL.md:191`, +19 bytes, keeping the file at 65,616 / 65,793 bytes):
     ```markdown
     - **Expected reviewer set**: the set step 3 resolved, carried into later rounds until the user changes it for this review (a failure path that adds a failover replacement updates only that round's set). If that leaves the set unclear, ask the user which reviewers they plan to invoke before presenting the prompt.
     ```

2. **[Low] `skills/implement-review/SKILL.md:41` (and `CHANGELOG.md:25`) has a mismatched singular referent and blurs pre-dispatch vs post-dispatch output**
   - **Problem**: Step 3 says:
     > `Dispatch exactly that set. Only the user's words for this review, or a rewrite or failure path this file defines, change it, and the line then names that reviewer and why.`
     There is no singular antecedent for "that reviewer" (the preceding clause refers to "that set", and user words can change the set to multiple reviewers such as `/vet all`, or a failure path can leave a Grok slot failed with no replacement). In addition, "the line" refers back to the pre-dispatch channel line, whereas a post-dispatch failure path happens after dispatch and emits its own one-line takeover or failure notice (`references/failover-and-recovery.md:10`). `CHANGELOG.md:25` repeats the same phrasing.
   - **Suggested fix** (`skills/implement-review/SKILL.md:41`, -2 bytes):
     ```markdown
     Only the user's words for this review, or a rewrite or failure path this file defines, change that set, with a line naming the change and why.
     ```
     Update the matching sentence in `CHANGELOG.md:25` to stay aligned.

3. **[Low] `skills/implement-review/SKILL.md:41` does not name `IMPLEMENT_REVIEW_DEFAULT_CHANNEL` or `IMPLEMENT_REVIEW_DEFAULT_REVIEWER` in Step 3**
   - **Problem**: Unlike other checklist steps that name their key env vars or flags inline (for example `CODEX_DISPATCH_REASONING` later in Step 3, `--expected-review-file` in Step 5, `await-review.py` in Step 6), Step 3's opening sentence still leaves the two user-scoped default env vars inside Path selection. Because no script reads or prints them and Claude Code exports `~/.claude/settings.json` `env` entries only to shell subprocesses rather than the prompt, a coordinator scanning Step 3 on a bare `/vet` can still overlook checking the environment before concluding the shipped defaults apply.
   - **Suggested fix** (`skills/implement-review/SKILL.md:41`, fits inside the 196-byte ceiling headroom even combined with Findings 1 and 2):
     ```markdown
     3. **Channel and reviewers.** Choose both by [Path selection](#path-selection) (checking `IMPLEMENT_REVIEW_DEFAULT_CHANNEL` and `IMPLEMENT_REVIEW_DEFAULT_REVIEWER` when the invocation omits them), and before dispatching emit one channel line per reviewer, naming what selected the channel and the reviewer set.
     ```

### Previously raised

None.
