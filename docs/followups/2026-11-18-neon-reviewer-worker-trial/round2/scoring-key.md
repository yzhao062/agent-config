# Round 2 scoring key (written 2026-11-18, before any round-2 review was dispatched)

Question: should the Agy `/vet` reviewer move from `gemini-4-carbon/medium` to `gemini-4-neon/high`? Round 1 had two reviews, and its seeded request pointed at the planted bug. Round 2 uses six past ac commits, each replayed as a staged diff on its parent in its own clone (`scripts/setup.sh`). Four carry one planted defect (`scripts/seed.py`), and two are the commits as made. Every request uses the same lens text and names no focus area (`scripts/make_prompts.py`); each summary states what the original commit set out to do.

Both arms run all six diffs at once through `skills/implement-review/scripts/dispatch-gemini.py`, with `ANTIGRAVITY_DISPATCH_MODEL` set to `gemini-4-carbon-medium` or `gemini-4-neon-high`, so the two models carry the same number of concurrent conversations. One run per cell. As in round 1, the override reaches the reviewer's shell, and `tests/test_dispatch_gemini.py` fails 26 cases under it; this hits both arms alike and is not scored.

## Planted defects

Each seeded clone passes its relevant tests on Python 3.12 and 3.9 with the defect in place.

- **d1 (15e383d), logic.** `agent_models.py map` treats a file that resolves two or more reviewer rows as a review panel. The seed makes the panel test count `worker` and `prun-worker` rows as well: `if role in ("reviewer", "worker", "prun-worker") and family != "*"`. A file that resolves, for example, `codex/reviewer` and `agy/prun-worker` is then taken for a panel, its `/vet` reader is dropped, and it gets a false `no reader for:` gap. `tests/test_agent_models.py` passes (122).
  - Detected: the review names the role condition in `direct_reviewer` (non-reviewer rows counted toward the panel threshold) as a defect, at any severity.
  - Partial: says the panel test counts rows other than reviewer rows without naming the line, or flags the line only as a style or clarity point.
- **d2 (37b9b26), one copy of two.** The commit added `xhigh` to the slug-tier tuple in both Agy dispatchers. The seed keeps the change in `dispatch-gemini.py` and reverts it in `skills/prun/scripts/dispatch-task-agy.py`, which is then absent from the diff, and drops the xhigh input from that file's test (the strict mock change stays). A `prun` unit run with `ANTIGRAVITY_DISPATCH_MODEL=gemini-4-hydrogen-xhigh` still sends `--effort high`, and Agy exits on the conflict, the bug the commit fixes for `/vet`.
  - Detected: the review names `dispatch-task-agy.py` (the `prun` dispatcher) as still missing `xhigh`.
  - Partial: says another dispatcher or copy may need the same change without naming it, or notes that the `prun` test file changes only its mock.
- **d3 (932bd74), document against code.** The corrected `grok-executor.md` said a missing registry row is waived when both `GROK_DISPATCH_MODEL` and `GROK_DISPATCH_EFFORT` are set. The seed says `GROK_DISPATCH_MODEL` alone waives it. `dispatch-task-grok.py` requires both (`both_overridden`).
  - Detected: the review names the waiver sentence as contradicting the dispatcher.
  - Partial: says the waiver or override text needs checking without stating the contradiction.
- **d4 (d3aac68), a test that does not test its claim.** `test_zero_usage_keeps_its_meter` keeps its name and docstring ("A window at 0% used is present, so it must not be mistaken for an absent one") but now uses `used_percentage: 1` (expecting 99%), so no test exercises a window at zero usage, which an implementation testing the percentage for truth would drop.
  - Detected: the review says that test does not use zero usage, or does not test what its name or docstring says.
  - Partial: says zero usage is untested without naming that test.

## Clean diffs

- **c1 (5ed589b)**, Grok fast model in every role and the Grok review tests' own registry. Its original `/vet all` round 1: Codex PASS with no findings, Grok one Low, Agy three Low.
- **c2 (ee57b98)**, `/vet` reviewer set in checklist step 3. Its committed text passed round 2 of `/vet both` with no new findings.

Score each finding as valid (a defect or gap I can confirm in the clone) or invalid. A BLOCK on a clean diff counts as valid only with a concrete defect I can confirm.

## Also recorded per review

Verdict; every other finding and whether it holds (for a seeded diff, a valid finding other than the planted one counts in the reviewer's favor); the health check outcome; wall time from dispatch to exit; input, output, and cache-read tokens from the stream-json result event; model calls from the conversation database; the dispatcher's `model-actual` record, which must confirm the arm's model.

## Decision rule (set before the run)

Recommend moving the reviewer to `gemini-4-neon/high` if, over the four seeded diffs, it detects at least as many planted defects as `gemini-4-carbon/medium`, with no more invalid findings across all six reviews. If it detects fewer, keep `gemini-4-carbon/medium`. A tie on both counts leaves cost (calls and time) to decide, with round 1 counted alongside.
