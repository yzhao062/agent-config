# Neon trial scoring key (written 2026-11-18 before any result was read)

## /vet arms: Carbon medium (registry reviewer) vs Neon high, Agy dispatcher, same staged index

D1 seeded (clone of 0878a02^ with 0878a02's diff staged, plus one seed):
- Seed: in code_span_bounds (health-check.py and its identical copy in dispatch-gemini.py), after a matched span the scan resumes at `index = partner` instead of `partner + 1`. The closing run then opens a new span to the next same-width run on the same line, so text between two code spans on one line is removed. Effect: a one-line JSON dispatch tail (Check 8) or a review line (Checks 7, 10) loses everything between its first and later inline spans; e.g. "ran `pytest -q` then connection refused while fetching `deps`" strips to "ran ". The full suite still passes with the seed.
- Detection = the review names the resume index (or the overlap/stripping between consecutive spans on one line) as a defect, at any severity. Partial credit: says span pairing re-uses the closer or that text between spans disappears without naming the line.
- Also record: other findings, each judged valid / invalid by me; verdict; health check outcome.

D2 clean (clone of 011410a^ with 011410a's diff staged, the Check 5 bare-label fix):
- Known state: Codex and Agy (Carbon medium) both returned PASS with no change required on 2026-11-17.
- Score = number of findings and how many are valid; a BLOCK on this diff needs a concrete, verifiable defect to count as valid.

Cost per review: wall time from dispatch start to file publication; token usage from the tail's result event if present; review-model `actual=` must confirm the arm's model.

## /prun arms: Hydrogen high (registry prun-worker) vs Neon high, units dispatched by the coordinator; third arm: one /swarm on Neon

U1 repo audit (read-only, pinned clone at 53f9c17). Question: where does the repository name a Gemini model family or slug (argon, carbon, hydrogen, neon, flash) outside `user/agent-models.json`; classify each; would removing gemini-4-argon from the registry break any test or script.
- Key: runtime code carries no model literal (tests/test_agent_models.py drift test forbids it outside `user/agent-models.json`, `user/settings.json`, `CHANGELOG.md`, `scripts/agent_models.py`, `tests/`, `docs/followups/`, `archive/`, `legacy/`). Argon appears in: registry family agy model and reviewer fallback_model (2 fields); `scripts/agent_models.py` docstring/example lines 18 and 309 (no behavior); tests as fixture strings in test_agent_models, test_dispatch_gemini, test_dispatch_grok, test_dispatch_task_agy, test_dispatch_task_grok (fixtures with their own registries, not the shipped one); docs/followups eu-guidance pilot record. Removing Argon from the registry breaks nothing in tests; the interactive Agy setting synced from the family row changes on the next bootstrap.
- Score: correct conclusion (yes/no), missed categories, false claims.

U2 web facts (public web only). Question: Gemini 4 Neon in Antigravity vs Argon: release date, plans, CLI slugs, context window in Antigravity, API price, Orchestrator (Neon), and whether Argon is deprecated or replaced, with sources and HTTP status per URL.
- Key: released 2026-11-18; Antigravity on paid AI Pro and Ultra (not Free or AI Plus; enterprise Neon only via Gemini for business, no Orchestrator); slugs gemini-4-neon-{low,medium,high,xhigh}, High default, xhigh via --model or --effort; Antigravity context up to 512K (API 1M); API $3 in / $15 out / $0.15 cached per 1M; Orchestrator (Neon) = Neon plans and reviews, Hydrogen implements; no first-party statement that Argon is retired in Antigravity (9to5Google says Neon replaces Argon in the Gemini app).
- Score: facts right / wrong / missing; fabrication counts double.

U3 code-writing (throwaway clone at 53f9c17). Task: when dispatch-task-agy.py publishes the worker's final response as the result (no worker-written result file), drop any text before the first line that is exactly `# <unit-id> result` and keep the full response beside it as `<result>.response.<ext>`; a response with no such line, or with the header first, publishes unchanged; a worker-written result keeps today's behavior. Add tests.
- Key: (a) the change sits where the final response is published, not where a worker-written file is kept; (b) narration before the header is cut and preserved beside; (c) no header or header-first is byte-identical to today; (d) FALLBACK path unchanged; (e) its new tests and the existing tests/test_dispatch_task_agy.py pass; (f) no unrelated edits.
- Score: each of (a)-(f) pass/fail, plus my reading of the diff.

Swarm arm: one Agy process on Neon given the same three questions as one /swarm task in its own clone. First question: does /swarm run headless at all. If it runs, score its answers against the same keys, plus wall time and token usage.
