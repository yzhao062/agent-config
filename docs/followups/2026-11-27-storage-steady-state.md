# Keep Agent Tooling Storage at a Steady State (2026-11-27)

On 2026-11-27 a reviewed one-time cleanup freed 53.4 GB on this Mac ([handoff record](../mac-storage-handoff-2026-11-27.md)). The aim now is a steady state that needs no such cleanup. Two tracks carry the work. As default behavior, the composer evicts pack slots its lock no longer names, and a separate plan will test whether dispatched Agy and Grok runs can use stores of their own. Once the weekly prompt permits saving captures, the audit will compare successive scans and report growth elsewhere.

## What grows

Sizes are allocated bytes in decimal GB, measured on 2026-11-27 for entries that still exist and grouped by creation date. They include later writes to those entries.

| Store | Written by | Created in the last 7 days | Created in the last 30 days | On disk | Ours to fix |
|---|---|---:|---:|---:|---|
| Agy conversations: `~/.gemini/antigravity-cli/brain/<id>/` and `conversations/<id>.db` | Of 328 conversations created in the last day, 311 open with the prun worker or `/vet` reviewer preamble and 16 come from meta-finder's funding advisor (`src/meta_finder/funding_codex.py`), which calls Agy directly | 1,055 conversations, 8.4 GB | all 1,219 | 8.8 GB, plus the 0.79 GB `conversation_summaries.db` | Yes |
| Pack cache: `<consumer>/.agent-config/cache/<key>/<commit>/` | anywhere-agents bootstrap and composer in every consumer | 175 slots | 453 slots, 10.1 GB | 20.5 GB before the cleanup; no single consumer exceeded 0.9 GB | Yes |
| Grok sessions: `~/.grok/sessions/<cwd>/` | the `/vet` Grok reviewer and prun Grok units (630 of 631 cwd folders name a temp directory) | 1.35 GB | 2.45 GB | 2.45 GB | Yes |
| Codex sessions from `codex exec` | the `/vet` Codex reviewer, prun Codex units, the model probe, smoke tests | | 476 sessions, 0.35 GB | | No change |
| Claude Code workflow transcripts older than 30 days | Claude Code | | | 168 folders, 3.95 GB | No |

Agy has the largest recent footprint. Through 1.5.14 it kept its 500 newest conversations at startup; 1.5.15, first run here on 2026-11-22, dropped that cap. Until weekly totals exist, plan with 1.2 to 1.8 GB per active day. Codex Desktop sessions (2.17 GB in 30 days) are the user's interactive work and stay out of scope.

## Track 1: default behavior

These changes act on every run and need no invocation. They are code and tool settings; none adds rule text to `AGENTS.md`.

### Pack cache: the composer evicts slots its lock no longer names (ships now)

The composer holds the repo lock through commit, pending-update cleanup, and eviction. `_evict_stale_cache_slots` then removes each `<16-hex>/<40-hex>` slot under `.agent-config/cache/` that matches no lock entry and is at least 24 hours old by modification time, and then removes key directories left empty. A slot matches when its key equals `compute_cache_key(source_url, sha)` for an entry's `resolved_commit` or `latest_known_head`; bundled entries name no slot. Every directory from `.agent-config` down to a slot must be real, with no link or Windows junction, and paths are checked without resolving links. Each cache belongs to one checkout: a cache directory linked into a second checkout is unsupported, because the owning checkout evicts by its own lock alone. If removal fails, the composer reports the affected slot and continues. Eviction keeps everything when any update was skipped or deferred (the global decision or any pack in a selective apply), when `pending-updates.json` remains, when a staging transaction is left over, or when the lock is missing, unreadable, or names no slot. Failures become warnings, and the committed compose stays successful.

Both locked commits stay, so a skipped update still reloads its locked commit from the cache (the skip path in `compose_packs.py`). A lock restored by hand to an evicted commit meets the existing cold-cache fallback, which warns and keeps the newly fetched archive (`test_skip_path_warns_on_cold_cache_and_keeps_new_archive`); consumers gitignore `pack-lock.json`, so no supported flow restores one. Whether that fallback should stop instead is a separate question about the composer and is not changed here.

The helpers `referenced_cache_keys` and `evict_unreferenced_slots` sit beside `_rmtree_existing` in `scripts/packs/source_fetch.py`, copied to the composer mirror (checked by `scripts/check-parity.sh`) and regenerated into `packages/pypi/anywhere_agents/packs/` by `scripts/vendor-packs.py`. The eviction tests in `tests/test_pack_cache_eviction.py` cover retention, age, links and junctions, empty directories, skip conditions, and removal failures. Two compose-level tests in `tests/test_compose_packs_v0_5.py` check that an apply evicts a stale slot and a skip keeps it.

### Codex sessions: unchanged

`--ephemeral` would stop dispatched runs from writing session files, but `scripts/agent-quota.py` reads Codex rate limits from those files for the `/vet` usage snapshot and the status line. Interactive sessions alone would then refresh that reading about twice a day. At 0.35 GB a month, the audit tracks Codex sessions instead.

### Agy and Grok: dispatched runs in stores of their own (gated)

Agy has no data-directory setting. On 2026-11-27, Agy 1.5.18 ran with `HOME` set to an empty directory whose `Library` entry linked to `~/Library`. It authenticated, wrote its new brain, conversation, and summaries data under that directory, and resumed the conversation. Overriding `HOME` also changes it for every command the worker runs, so the candidate is an overlay home that links every top-level entry of the real home except `.gemini`. A separate plan, reviewed before any code, has to meet these requirements:

- Gate: a reviewed, reproducible script kept in the repository, which the user runs. Each trial builds a fresh private overlay with the production initializer and starts two concurrent first runs, each with its own working directory and marker. Both runs must exit successfully and return distinct conversation ids. On resume, each conversation must recall its own marker. The gate compares tools, effective sandbox and permission settings, and model reporting with an ordinary worker, and it tests an existing home path and a newly created home-relative output. It also records whether the quota helper's `/usage` query creates a conversation, checks the interactive store and picker before and after, removes only trial-owned files without following links, and fails closed on any missing check.
- Store publication: keep the store lock outside the store. Under an exclusive lock, the first launcher builds the overlay in a staging directory and renames it into place. Each run then holds a shared lease that its CLI child inherits and records last use at entry and at exit. A sweep takes each other store's lock with `LOCK_EX | LOCK_NB`, rereads last use under it, deletes only a validated store idle 14 days, unlinks links before removal, and never descends through a link. A recorded store that has expired reports expiry rather than starting empty.
- Grok gets its own gate result for authentication, resume, and leader lifetime, with the binary and `GROK_AUTH_PATH` resolved against the real home and `grok_actual` reading the child's `GROK_HOME`. If the gate fails, Grok stays as it is.
- Add the shared helper to the parity check and the wheel mirror. Verify that launchers find it from a source checkout, a bootstrapped consumer, and an installed wheel.

If a gate fails, that tool stays in its shared store, the audit tracks it, and an upstream request asks for a data-directory or retention setting.

### Claude Code workflow transcripts

Report the 168 folders older than 30 days upstream, with their sizes and parent-session dates. The watcher measures total Claude project storage.

## Track 2: active audit (ships now)

The weekly `mac` task (a Codex Desktop automation, Saturday 11:00) runs the private `mac-storage-audit` skill, which stays read-only on the trees it inspects. `growth_watch.py`, beside its collector, measures each home entry, each named agent store, and each consumer pack cache under `~/PycharmProjects` and its `.retired-repositories` as separate `du` roots. When a root scans partially, the script measures each child on its own and repeats this once for a partial child, so readable siblings keep their own totals. On this Mac, `~/Library/Caches/pip`, `~/Library/Application Support/Claude`, and `~/Library/pnpm` measure cleanly, while privacy-protected folders such as `~/Library/Containers` do not. System temporary roots stay with `scan_storage.py`.

The script is read-only unless run with `--save`, which the weekly run may use after the prompt change in step 1. With `--save` it publishes a dated capture atomically to `~/.local/state/mac-storage-audit/` and keeps the newest eight, the one standing write the skill names. Every run subtracts the capture bytes from the `~/.local` totals, and a malformed previous capture is noted rather than compared. Growth is compared only between complete measurements of the same path. Flags cover a store over its budget (Agy dispatch stores over 30 GB, one pack cache over 0.25 GB, all pack caches over 2 GB), growth over 5 GB shown once at the most specific path, and a new home entry over 5 GB when the previous listing was complete. The first capture is a baseline, with budgets applied at once. Its report lists partial scans, the interval between captures, and growth in the shared Agy store. A dry run on 2026-11-27 took about a minute and raised no flag. `tests/test_mac_growth_watch.py` covers the flag rules, deduplication of growth flags for overlapping paths, the recursive split, pack-cache discovery, denied paths, malformed baselines, capture exclusion, the read-only default, and capture rotation, including a failed publish.

Flags report findings and delete nothing. Triage each one with its owner, preserve unique results, and verify any recovery copy before proposing deletion. A one-time cleanup then uses a manifest, records each reviewer's conditions and their disposition, obtains the user's execution approval, and is recorded in the handoff.

## Order and process

1. Ship now. Pack eviction goes out in an anywhere-agents release followed by one consumer re-bootstrap loop. The growth watch and its skill update stay in agent-config. Because the weekly automation's prompt asks for a read-only audit, the user adds one sentence there allowing the `--save` capture.
2. Later. Review the trial plan, implement and run the trials, then enable isolated stores for each tool that passes.

Each change goes through `/vet` and waits for push approval.
