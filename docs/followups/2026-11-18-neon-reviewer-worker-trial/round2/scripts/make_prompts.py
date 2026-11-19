"""Round 2: write the six review request bodies from one template.

Usage: python make_prompts.py <out-dir>

Every body shares the same lens, reading contract, and scope-challenge text, and
names no focus area, so no request points at a planted defect. Each summary
states what the original commit set out to do, taken from its message.
__REPO__ is replaced with the clone path at dispatch time.
"""
import sys
from pathlib import Path

READING = (
    "Reading contract: your task, lens, and response format are supplied here, and the project rules already supplied to you apply, including local overrides. Skip router dispatch and coordinator-workflow discovery at all skill lookup locations (skills/implement-review/, .claude/skills/implement-review/, .agent-config/repo/skills/implement-review/, .agents/skills/implement-review/). Do not load coordinator skill files or example reviews to discover the workflow or response format. Files under review remain readable. A targeted read outside the review scope is permitted when it supplies missing context, resolves truncation, or answers a concrete verification question. Read an applicable instruction file that was not supplied (for example AGENTS.local.md) once. Obtain the selected diff once with the command above; if this request embeds that diff, use it and do not obtain another copy. Do not read the same content twice.\n\n"
    "Note on the reading contract: the staged files are the files under review, so read them as review material, and any other file in the repository may be read as context. The skip rule above applies only to discovering the response format.\n"
)
LENS = (
    "Lens: Code and its documentation. Correctness, edge cases, behavior change for existing inputs, tests (does each new test fail on the old code, and would the tests fail if the new code broke?), consistency between the parts of the change and with the neighboring code and documents, maintainability.\n"
    "Focus: the whole diff under the lens above; no area is singled out.\n"
)
TAIL = (
    "Working method (optional, only if your runtime supports it): for a large or multi-file diff, you may parallelize across scopes only where no shared contract crosses the boundary (mirrored platform files, a script and its tests, and a source and its generated or vendored copies stay in one scope), keeping every shared-contract pair in one reviewer's context and re-reading that boundary while consolidating; for any finding that rests on a checkable external fact (citation, link, library or API behavior, version), use web search to verify it before asserting, and record what you checked in Verification notes.\n"
    "Scope-challenge focus (mandatory; reviewer must take an explicit position): (a) Why exactly this scope — what user pain or opportunity does it close, could a smaller scope close most of it, could a marginally larger scope close all of it for low cost? (b) Is each \"out of scope / deferred to vNext\" worth its process tax (extra plan-review + implement + execution-review + CI + publish cycle) versus inclusion now? (c) Is this plan the simplest path? Be adversarial about purpose and shape; do NOT fish for low-probability edge cases.\n\n"
    "Out of scope: nothing beyond the files changed.\n"
)

DIFFS = {
    "d1": (
        ["CHANGELOG.md", "docs/writing-harness-map.md", "scripts/agent_models.py",
         "skills/agent-models/SKILL.md", "tests/test_agent_models.py"],
        "`agent_models.py map` shows which files read each registry row. A file that resolves two or more reviewer rows dispatches its own reviewers (a review panel), so the shared `/vet` reader no longer stands in for the families that file skips: the map ends that file's line with `no reader for: <families>`, and `--json` carries the same list as `gaps`. The expected families are the ones the registry has, so a registry without a Grok row reports no Grok gap. In such a file a `/vet` mention no longer shows as `*/reviewer`, and the map skips `skills/agent-models/`, whose examples name every family. Two review panels had resolved the Codex, Claude, and Agy rows and never the Grok one, and the old output gave no sign of it. `docs/writing-harness-map.md` names Grok in the review-panel row, `skills/agent-models/SKILL.md` describes the new output, and new tests cover the gap report, the skipped skill directory, and a registry without Grok.",
    ),
    "d2": (
        ["skills/implement-review/scripts/dispatch-gemini.py", "tests/test_dispatch_gemini.py",
         "tests/test_dispatch_task_agy.py", "user/agent-models.json"],
        "The Agy `worker` and `prun-worker` rows and the family `fallback_model` in `user/agent-models.json` move from Gemini 3.8 Flash to Gemini 4 Hydrogen, which the Antigravity CLI lists at low, medium, high, and xhigh. No effort changes, so each resolved slug goes from `gemini-3.8-flash-high` to `gemini-4-hydrogen-high`. The Agy dispatcher lets an unset effort follow the tier in the slug, because Agy rejects a conflicting `--effort`. The tuple it tested the slug against omitted `xhigh`, so `ANTIGRAVITY_DISPATCH_MODEL=gemini-4-hydrogen-xhigh` alone sent `--effort high` and Agy exited on the conflict; the dispatcher now reads `xhigh` as a tier. The mock Agy rejects that conflict as the CLI does, and the existing test of this behavior gains an xhigh-only listing as a second input. `EFFORTS[\"agy\"]` is unchanged: the registry still refuses xhigh for an Agy row, since no row asks for it.",
    ),
    "d3": (
        ["scripts/agent_models.py", "skills/prun/references/grok-executor.md", "tests/test_agent_models.py"],
        "`grok_home_path()` in `scripts/agent_models.py` used `GROK_HOME` as written, while the Grok `prun` dispatcher's login and budget checks expand a leading `~`; with `GROK_HOME=~/.grok` the model check looked in a directory named `~` and reported `MODEL-UNVERIFIED`. It now expands `~` the same way, with a test. A Grok `prun` run had checked `skills/prun/references/grok-executor.md` against `skills/prun/scripts/dispatch-task-grok.py` and `scripts/agent_models.py` and found 21 of 46 claims out of step with the code, and the reference is corrected in those places to match the code.",
    ),
    "d4": (
        ["scripts/agent-quota.py", "scripts/statusline.py", "tests/test_codex_usage.py"],
        "Verified Ultra accounts have no five-hour limit, so `five_hour` is missing from the statusLine stdin and null in the usage response. `scripts/statusline.py` and `scripts/agent-quota.py` rendered that as a dash (`cc 5h— 7d93%`), which read as a broken meter. An absent window is now left out of both readouts, a window that returns shows again, and no window at all keeps a placeholder. New tests in `tests/test_codex_usage.py` cover both readouts.",
    ),
    "c1": (
        ["skills/agent-models/SKILL.md", "tests/test_dispatch_grok.py", "user/agent-models.json"],
        "The Grok family model in `user/agent-models.json` changes from `grok-4.7` to `grok-4.7-build-fast`, and the Grok `prun-worker` override keeps only its effort, so every role inherits the family model and the roles differ in effort alone: interactive, reviewer, and premium at high, worker and prun-worker at medium, as before. The maintainer chose this on measurement and accepted the higher spend. `tests/test_dispatch_grok.py` read the live registry, and one case asserted the live reviewer row, so it failed when the row changed; the harness now writes its own registry and passes it through `AGENT_MODELS_FILE`, as `tests/test_dispatch_task_grok.py` already does. The fixture for a registry without a Grok row used the key `schema_version` where the registry's key is `schema`, and the case passed only because the schema error also names `families.grok`; the fixture now uses `schema`, and the case asserts the resolver's own missing-row message. `skills/agent-models/SKILL.md` names the two Grok dispatcher test files among the tests to run after a registry edit, and the two Grok variables among the per-run overrides.",
    ),
    "c2": (
        ["CHANGELOG.md", "skills/implement-review/SKILL.md"],
        "Step 3 of the round checklist in `skills/implement-review/SKILL.md` said only \"Choose both by Path selection\". It now carries the decision: before dispatching, emit one channel line per reviewer naming what selected the channel and the reviewer set, and dispatch that set; only the user's words for that review, or a rewrite or failure path the file defines, change it, and the line then names the reviewer and why. Section 1c had its own rule for the expected reviewer set (a recent turn, then the prior round, then Codex alone), which never read `IMPLEMENT_REVIEW_DEFAULT_REVIEWER`; it now takes the set step 3 resolved and carries it into later rounds. On 2026-11-17 a coordinator that had read the whole file sent a bare `/vet` under `IMPLEMENT_REVIEW_DEFAULT_REVIEWER=both` to Codex alone for three rounds and printed no channel line. The file stays under its size ceiling, and `CHANGELOG.md` records the change.",
    ),
}


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    for key, (files, summary) in DIFFS.items():
        names = ", ".join(f"`{f}`" for f in files)
        body = (
            "Review staged changes in __REPO__. Round 1.\n"
            f"Run `git diff --cached` to see the diff. Files changed: {names}.\n"
            + READING + "\nSummary: " + summary + "\n\n" + LENS + TAIL
        )
        (out / f"{key}-body.txt").write_text(body, encoding="utf-8")
    print("wrote", len(DIFFS), "bodies")


if __name__ == "__main__":
    main()
