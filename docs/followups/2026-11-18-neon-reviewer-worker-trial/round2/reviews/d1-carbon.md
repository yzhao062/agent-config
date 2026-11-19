<!-- Round 1 -->
Intended output file: `Review-Antigravity.md`

## Verification notes

Executed in the disposable staged snapshot (`/var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-01d9a1ec-round1-12559-7a3e388ab5a146a2/staged-snapshot`):

1. `$HOME/miniforge3/envs/py312/bin/python -m unittest tests.test_agent_models tests.test_skill_md_contract tests.test_bootstrap_size` -> exit 0 (`Ran 170 tests in 3.276s`, `OK (skipped=1)`).
2. `$HOME/miniforge3/envs/py312/bin/python -m unittest tests.test_style_audit` -> exit 0 (`Ran 81 tests in 2.986s`, `OK`).
3. `$HOME/miniforge3/envs/py312/bin/python scripts/agent_models.py map /var/folders/sj/82qpdfvj21g5ydhsrw5xpc940000gn/T/implement-review-gemini-01d9a1ec-round1-12559-7a3e388ab5a146a2/staged-snapshot` and `... map --json ...` -> exit 0 (`skills/agent-models/SKILL.md` excluded, `"gaps": []`).
4. `$HOME/miniforge3/envs/py312/bin/python skills/implement-review/scripts/style-audit.py --all-lines CHANGELOG.md docs/writing-harness-map.md skills/agent-models/SKILL.md` -> exit 0 (`0` findings on lines added or modified by this diff).
5. Targeted Python reproduction against `scripts/agent_models.py` (`map_repo` and `main(["map", ...])` on temporary consumer repositories) -> confirmed that `direct_reviewer` includes `"worker"` and `"prun-worker"` rows (`scripts/agent_models.py:1038`), causing a two-family `prun-worker` consumer skill with `/vet` to lose `*/reviewer via /vet`, emit a spurious `"role": "reviewer"` gap in `--json`, and omit that gap from human-readable `map` output; also confirmed that `1 worker + 1 reviewer` triggers panel mode and `2 reviewer + 1 prun-worker` masks a missing `reviewer` family.
6. `$HOME/miniforge3/envs/py312/bin/python -m unittest discover -s tests -p 'test_*.py'` -> exit 1 (`Ran 1918 tests in 275.124s`, `failures=89, errors=1, skipped=198`); all failures are outside the changed modules (`test_repo.py` and `test_line_endings.py` require a `.git` directory absent from the exported snapshot, and `test_dispatch_gemini.py` / `test_dispatch_task_agy.py` inherit the active Antigravity review runner environment).

Verification status: VERIFIED

Commit verdict: BLOCK

## Scope and review lens

- **Files reviewed**: `CHANGELOG.md`, `docs/writing-harness-map.md`, `scripts/agent_models.py`, `skills/agent-models/SKILL.md`, `tests/test_agent_models.py`.
- **Review lens**: Code and its documentation (correctness, edge cases, behavior change for existing inputs, test adequacy in both failure directions, internal and neighboring consistency, maintainability, and mandatory scope challenge).

## Scope challenge

- **(a) Why this scope, smaller vs. larger**: Two review panels (`venue-review-panel` in `agent-pack` and a consumer repository's proposal panel) resolved `claude`, `codex`, and `agy` reviewer rows while omitting `grok`, and `agent_models.py map` gave no signal because it neither checked panel completeness nor discounted prose `/vet` mentions inside self-dispatching panels, while `skills/agent-models/SKILL.md` polluted `map` with documentation examples. A smaller scope (patching the two external panels alone, or adding `gaps` without dropping `/vet` on panels and skipping `skills/agent-models/`) would leave the blind spot or produce misleading `*/reviewer` output on panels that mention `/vet`. A larger scope such as failing nonzero on `gaps` or aggregating reviewer rows across whole skill directories would overreach: `map` is an inspection command where a deliberate two-family check can exist without failing CI, and directory-level aggregation would misclassify `skills/implement-review/scripts/dispatch-*` as a panel unless special-cased. Within the current file set, restricting `direct_reviewer` to `role == "reviewer"` and adding one Grok clause to `docs/writing-harness-map.md` § `Coverage by agent` completes the scope cleanly.
- **(b) Deferred / out-of-scope items vs. process tax**: Nothing is deferred to a follow-up round in this repository (`Out of scope: nothing beyond the files changed`), and the review-panel edits themselves live in separate repositories (`agent-pack` and a consumer repo) that cannot share one git commit here. There is no artificial deferral tax.
- **(c) Simplest path**: Yes, once `direct_reviewer` filters on `role == "reviewer"`. Detecting a panel per file from two or more distinct direct `reviewer` families needs no extra registry schema, skill frontmatter, or hardcoded list of panel paths, respects the families actually configured in `user/agent-models.json`, and leaves `/vet`'s single-family backend scripts and reference files untouched.

## New findings

### High priority

1. **`scripts/agent_models.py:1035-1039` (with missing boundary coverage in `tests/test_agent_models.py:1173-1202`): `direct_reviewer` counts `"worker"` and `"prun-worker"` readers as reviewer rows, corrupting existing non-panel inputs, breaking `--json` vs. text parity, and masking panels that run a slot on a worker role.**

   `map_repo` collects `direct_reviewer` with `if role in ("reviewer", "worker", "prun-worker")` (`scripts/agent_models.py:1038`), whereas every contract statement (`scripts/agent_models.py:1041`, `scripts/agent_models.py:1046`, `skills/agent-models/SKILL.md:63`, `CHANGELOG.md:28`) defines a review panel as a file resolving two or more `reviewer` rows. Including `"worker"` and `"prun-worker"` causes three concrete defects:

   - **Spurious `reviewer` gaps, dropped `/vet` readers, and `--json` vs. text divergence on multi-family worker files**: In any repository that does not ship `dispatch-task-*` (every consumer repository), a skill or script that dispatches `prun` or general workers across two families and mentions `/vet` (for example, `dispatch-task-agy.py`, `dispatch-task-grok.py`, and `Run /vet afterwards.`) yields `len(direct_reviewer) == 2` with zero `reviewer` rows. Line 1043 strips its legitimate `("*", "reviewer", "/vet")` reader, and line 1046 records `{"file": ..., "role": "reviewer", "missing": ["claude", "codex"]}` in `gaps`. In `cmd_map` (`scripts/agent_models.py:1106-1116`), `no reader for:` is appended only while iterating `rows` for `purpose == "review"`. Because `/vet` was removed and the remaining readers have `purpose == "general"`, `rows` under `review` has no entry for that file: human-readable `map` prints neither `/vet` nor `no reader for:`, while `map --json` emits the false `reviewer` gap.
   - **False panel classification on `1 worker + 1 reviewer` workflows**: A single-reviewer audit file that uses `claude/worker` subagents for parallel checks and resolves `codex/reviewer` plus `/vet` (compare `skills/bibref-verify/SKILL.md`) reaches `len(direct_reviewer) == 2`, loses its `/vet` reader, treats `claude/worker` as covering `claude/reviewer`, and reports `missing: ["agy", "grok"]`.
   - **Masked missing `reviewer` row in a real panel**: By `skills/agent-models/SKILL.md:19,32`, every panel reviewer must resolve the `reviewer` role. If a panel resolves `claude/reviewer` and `codex/reviewer` and invokes `dispatch-task-agy.py` (`agy/prun-worker`) or `CLAUDE_CODE_SUBAGENT_MODEL` (`claude/worker`) without resolving `--role reviewer`, `direct_reviewer` credits that family anyway and hides that the slot runs on the worker model instead of `reviewer`.

   None of the three new tests in `tests/test_agent_models.py` includes a direct `worker` or `prun-worker` reader (only `/prun`, which is excluded by `how not in SLASH_COMMANDS`), so the tests pass despite the bug.

   Exact rewrite for `scripts/agent_models.py:1035-1039`:

   ```python
           direct_reviewer = {
               family
               for family, role, how in file_readers
               if role == "reviewer" and family != "*" and how not in SLASH_COMMANDS
           }
   ```

   Exact rewrite for `tests/test_agent_models.py:1173-1202` to cover both failure directions (non-reviewer roles do not trigger panel mode or satisfy `reviewer` slots, and multi-family gaps follow `FAMILIES` order):

   ```python
               single = repo / "skills" / "single"
               single.mkdir(parents=True)
               (single / "SKILL.md").write_text(
                   "resolve --family claude --role worker\n"
                   "resolve --family grok --role reviewer\n"
                   "Run /vet afterwards.\n",
                   encoding="utf-8",
               )
               fanout = repo / "skills" / "fanout"
               fanout.mkdir(parents=True)
               (fanout / "SKILL.md").write_text(
                   "Run dispatch-task-agy.py or dispatch-task-grok.py.\n"
                   "Run /vet afterwards.\n",
                   encoding="utf-8",
               )
               worker_leak = repo / "skills" / "worker-leak"
               worker_leak.mkdir(parents=True)
               (worker_leak / "SKILL.md").write_text(
                   "resolve --family claude --role reviewer\n"
                   "resolve --family grok --role reviewer\n"
                   "dispatch-task-agy.py\n",
                   encoding="utf-8",
               )

               with_grok = agent_models.map_repo(repo, expected_families=agent_models.FAMILIES)
               without_grok = agent_models.map_repo(repo, expected_families=agent_models.REQUIRED_FAMILIES)

           self.assertEqual(
               with_grok["gaps"],
               [
                   {"file": "skills/panel/SKILL.md", "role": "reviewer", "missing": ["grok"]},
                   {"file": "skills/worker-leak/SKILL.md", "role": "reviewer", "missing": ["codex", "agy"]},
               ],
           )
           self.assertEqual(
               without_grok["gaps"],
               [{"file": "skills/worker-leak/SKILL.md", "role": "reviewer", "missing": ["codex", "agy"]}],
           )

           panel_readers = [(r["family"], r["role"], r["how"]) for r in with_grok["readers"]
                            if r["file"] == "skills/panel/SKILL.md"]
           self.assertNotIn(("*", "reviewer", "/vet"), panel_readers)
           self.assertIn(("*", "prun-worker", "/prun"), panel_readers)

           full_readers = [(r["family"], r["role"], r["how"]) for r in with_grok["readers"]
                           if r["file"] == "skills/full-panel/SKILL.md"]
           self.assertNotIn(("*", "reviewer", "/vet"), full_readers)

           for non_panel in ("skills/single/SKILL.md", "skills/fanout/SKILL.md"):
               non_panel_readers = [(r["family"], r["role"], r["how"]) for r in with_grok["readers"]
                                    if r["file"] == non_panel]
               self.assertIn(("*", "reviewer", "/vet"), non_panel_readers)
   ```

### Low priority

1. **`docs/writing-harness-map.md:38,62`: `Coverage by agent` omits Grok after line 38 adds Grok to `Canonical homes by layer`.**

   Line 38 makes `Grok` an explicit entry in the `Agents` column of `Canonical homes by layer` (`Claude Code, Codex, Agy, Grok`) for the first time in this file. In `## Coverage by agent` (`docs/writing-harness-map.md:62`), the paragraph accounts for every other named agent in that table (`Claude Code`, `Codex`, `Agy`) and still describes Agy only as a `/vet` reviewer and a `prun` worker while omitting Grok completely. Extending the Agy sentence (for example, noting that Agy and Grok read `AGENTS.md` as `/vet` reviewers, review-panel reviewers, and `prun` workers, with no write-time hook) keeps `Coverage by agent` aligned with the updated table above it.

## Previously raised

None.
