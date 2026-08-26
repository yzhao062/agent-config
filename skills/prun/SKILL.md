---
name: prun
description: Parallel delegation fan-out. The Claude session coordinates (on whatever Claude model is currently selected, e.g. Opus or Fable) while task units run in parallel on workers (never on the coordinator). Codex (`codex exec`, a separate abundant account) is the prioritized default; Sonnet is reserved for units needing Claude-session-internal capabilities (MCP/email tools, Artifacts, cross-vendor web verification), with the orchestrator deciding per unit. Units may read or write code; workers never commit or push, and the session plus the user are the final integration gate.
---

# prun (parallel run)

## Overview

`prun` fans a task out into independent units that run in parallel on separate-quota or in-session
workers, while the Claude session only coordinates. Workers are **Codex** (`codex exec`, a separate abundant account, frontier model) and **Sonnet**
subagents (inside the Claude session). **Codex is the prioritized default**: its quota is separate
from the Claude plan and its current model (gpt-5.6 tier) is strong on hard reasoning and code, so
most units go to Codex. **Sonnet is reserved** for units that need something the Claude session
uniquely provides (see the Executors rule). The coordinator decomposes the task, dispatches the units, gathers
their results, reviews their diffs, and integrates. It never runs a unit itself.

The orchestrator picks the executor per unit; when in doubt, Codex. A Codex unit runs through the
separately authenticated Codex/OpenAI account, so the worker run does not draw on the Claude plan at
all. A Sonnet unit and the Claude coordinator both consume the current Claude account's quota; the
exact split across models and weekly buckets depends on the plan and on active promotions and shifts
over time, so check Settings > Usage before relying on any model-specific split. Codex is the default
because its worker run is outside the Claude plan; keep Sonnet units targeted because they draw
Claude-side quota.

## Relationship to the native Workflow tool

The native Workflow tool fans a task out across **Claude** subagents under a deterministic script,
with structured output, judge panels, and resume. A Workflow run counts against the Anthropic plan's
usage and rate limits, and its agents use the session model unless the script routes a stage to a
different Claude model.

`prun` has a different quota shape. A **Codex** unit is dispatched by a shell call to `codex exec`,
so the worker run uses the separate Codex/OpenAI account. A **Sonnet** unit and the coordinating
session both draw the current Claude account's quota, so reserve Sonnet for units that need the
Claude session's own tools. The coordinating session also spends a small Anthropic amount while it
decomposes, dispatches, reads results, and integrates.

The two relate in two ways, both with the current session as the orchestrator:

- **Substitute (quota).** When the Anthropic pool is too constrained to run a Workflow, use prun
  with Codex-only units, or keep any Sonnet units small and targeted. This shifts the heavy fan-out
  to Codex while leaving only the coordinator and any chosen Sonnet work in the Anthropic pool.
- **Complement (diversity).** When a Workflow is affordable and you want cross-vendor perspectives,
  run a Claude panel through the Workflow and a Codex panel through prun. Use the same structured
  contract and the same question on both sides, then cross-check. Agreement across vendors is usually
  a stronger signal than agreement inside one model family, because shared model lineage and tools
  can share blind spots. Invoke them together in one natural-language request; no special mode is
  needed. Reserve this for high-stakes work (a review, an audit, a hard design call), since it spends
  both pools and the coordinator must merge two result sets.

## When to use

Use `prun` when the task splits into **independent units that can run at once** (different
modules, separate research questions, parallel analyses). Units may be heterogeneous, and there
can be **many of them**: a dozen or twenty in parallel is normal when the task warrants it.

Do not use `prun` when the task is one sequential unit, or units depend on each other's output,
or a unit's result cannot be checked without redoing it.

## Executors

| Executor | Quota | Notes |
|---|---|---|
| Codex (`codex exec`) | Separately authenticated Codex/OpenAI account; abundant | **Prioritized default.** Frontier model (gpt-5.6 tier), strong on hard reasoning and code, and the worker run spends no Claude-plan quota. Run many in parallel. |
| Sonnet subagent | Current Claude account; check Settings > Usage for the applicable limits or credits | Reserved, not a default. Runs in the Claude session, so it alone can reach session-internal tools (MCP / email / Artifacts) that Codex cannot. |
| Claude session (this session) | Current Claude account; check Settings > Usage for the applicable limits or credits | Coordinator and integrator only, on whatever model is selected. Never a unit. |

Rule: **units never run on the coordinator (the Claude session itself).** The orchestrator picks the
executor per unit, with a strong default toward Codex:

- **Codex is the default for almost every unit** (code, research, analysis, web fetch). Its quota is
  separate and abundant and its frontier model (gpt-5.6 tier) is capability-competitive with the top Claude models,
  so there is rarely a reason to prefer another worker. Start here.
- **Sonnet is the reserved exception, chosen only when a unit needs a tool the Claude session has but
  the isolated Codex worker does not.** Codex is an external process, so route to Sonnet when a unit
  needs a session-internal MCP / email connector (Gmail, Calendar, Drive, Slack), the Artifact tool,
  or a **cross-vendor web-search verification** where you want a Claude-side `WebSearch` result to
  cross-check the Codex one. A normal Sonnet subagent inherits the session's available tools but
  **starts with fresh, isolated context** (it does not see the conversation history), so put any
  needed state in its unit prompt; if a task truly needs the full live conversation, keep it in the
  coordinator (an explicit fork inherits that context but also the coordinator's model, so it is not
  a Sonnet worker). The orchestrator decides per unit; when in doubt, use Codex. Sonnet draws
  Claude-side quota, so keep these units targeted.
- **The Claude session stays the coordinator, never a unit.** A single small session-tool task the coordinator can
  do inline; reach for Sonnet when you need to run *many* such units in parallel.

## Concurrency

The orchestrator decides the unit count autonomously. Partition the task by **dependency
structure** (split only along genuinely independent boundaries) and **balanced workload**
(roughly equal-sized units, each worth a full worker run). High autonomy is the intent: do not
target a fixed number, and do not cap artificially. A dozen-plus in parallel is fine when the
task genuinely decomposes that way.

Two soft bounds, not hard rules: local CPU/RAM (heavy Codex workers contend past roughly a
handful at once, and the excess just queues) and Codex quota headroom. The usual real ceiling is
**integration bandwidth**, since the orchestrator must read and reconcile every result, so
prefer fewer well-scoped units over many tiny ones. Over-splitting into trivial units wastes
worker startup and tends to produce thin results.

## What a unit may do, and the one rule

A unit may **read or write code**, run commands, and fetch the web, with full access. The single
hard rule: a worker **never commits, pushes, or runs destructive git** (`commit`, `push`,
branch/tag mutation, `reset --hard`, `clean`). Everything else is allowed. The final gate is
**the Claude session integrating the results and the user deciding**; workers never touch the real repo history.

This is enforced structurally, not by trust:

- **Read-only / research units** run from a per-unit scratch cwd, so accidental writes stay out of
  the repo. `dispatch-task` does this by default.
- **Code-writing units** run inside a **throwaway local clone** of the repo with its remote removed:
  ```
  git clone --local -c core.longpaths=true <repo> <clone-dir>   # longpaths: Windows MAX_PATH safety
  git -C <clone-dir> remote remove origin
  ```
  The worker edits freely in the clone. An accidental `git push` has no remote to reach (GitHub /
  Overleaf stay untouched); an accidental `git commit` only lands in the throwaway clone. The coordinator reads
  `git -C <clone-dir> diff`, integrates the wanted changes into the real tree, and **the user
  approves the actual commit**. That is the only gate.

No credential scrubbing or sandbox wall: the user writes the prompts, the clone has no path to the
real remotes, and the Claude session plus the user are the integration gate. That is the whole safety model.

## Flow

1. **Gate**: confirm the task splits into independent, checkable units. Else use a single worker.
2. **Decompose**: write one prompt per unit. State the task; for a code-writing unit, that the
   working dir is a throwaway clone to edit freely but **not** commit or push; that the unit writes
   a result summary to its result file (a fresh path, in one write).
3. **Assign**: default the unit to Codex; pick Sonnet only for the reserved cases (session-internal
   MCP / email / Artifacts, or cross-vendor web verification). Also pick read-only (scratch) or code-writing (clone) mode.
   For a web-heavy unit, "Web access" below covers which executor fits.
4. **Dispatch in parallel**:
   - Codex unit: run `scripts/dispatch-task.{sh,ps1}` in the background (Bash tool,
     `run_in_background=true`). For a code-writing unit, pass the clone dir via `PRUN_SCRATCH_CWD`.
   - Sonnet unit: spawn a background Agent subagent with `model: sonnet`. It inherits the session's
     available tools, including MCP and connector tools; if you set a `tools` allowlist, include every
     connector, Artifact, file, shell, and web tool the unit needs. The subagent starts with fresh
     context, so put any needed state in its prompt. For code-writing it works in a clone too, under
     Claude's `guard.py`, which already gates commit/push.
5. **Monitor (do not go idle)**: launch `scripts/monitor.{sh,ps1} <state-dir> ...` in the background
   (`run_in_background=true`) and wait on its completion. It wakes you on the first actionable event:
   all done, any unit **stalled** (tail no-growth for `PRUN_STALL_THRESHOLD`, default 10 min), or any
   unit **failed** (`FALLBACK` result or dead dispatch), printing a per-unit digest. On a stall,
   surface it to the user with a likely cause (capacity or concurrency pressure; suggest lowering the
   worker count or re-dispatching) rather than waiting silently; act, then re-launch the monitor on the
   still-running units until all are done. `monitor` only observes; the unit's own `dispatch-task`
   reaps a worker idle past `PRUN_STALL_THRESHOLD` at the same threshold, so a persistent stall
   surfaces as a `FALLBACK` to re-dispatch rather than a leaked zombie. (`gather.{sh,ps1}` remains for
   the plain wait-for-all case.)
6. **Reconcile, then integrate**: before integrating, **reconcile the ledger**: every dispatched unit
   must have a non-empty result. If any is missing or empty, do **not** integrate the partial set;
   recover the worker's output from its `<state-dir>/tail` (dispatch-task also salvages the tail into
   the result file automatically under a `FALLBACK` header), then re-dispatch or flag the user if it is
   unusable. Then the coordinator reads each result plus each clone's `git diff`, merges the wanted changes into
   the real tree, runs verification, and **asks the user before any commit**.

Resolve scripts via this order, first hit wins: `skills/prun/scripts/`, then
`.claude/skills/prun/scripts/`, then `.agent-config/repo/skills/prun/scripts/`.

## dispatch-task usage (Codex)

```
scripts/dispatch-task.sh --prompt-file <prompt> --result-file <abs result> --unit-id <id>
```

- Emits exactly one stdout line `STATE-DIR <abs-path>`; codex stdout+stderr land in `<state-dir>/tail`.
- If the worker exits without writing a non-empty result file, dispatch-task salvages its captured
  `<state-dir>/tail` into the result file under a `FALLBACK` header, so a failed result-write never
  makes the unit silently vanish at gather. Treat a `FALLBACK` result as "review or re-dispatch."
- Self-heals a hung worker: if the tail stops growing for `PRUN_STALL_THRESHOLD` seconds (default
  `600`; the same idle signal `monitor` reports) or the run exceeds `CODEX_DISPATCH_TIMEOUT` seconds
  (default `0` = hard cap off, so the idle signal stays primary and an actively streaming long run is
  not killed), dispatch-task kills the worker's whole process tree, exits `124`, and writes the
  `FALLBACK` above naming `idle-stall` or `hard-timeout`. A non-empty result the worker already wrote
  is preserved, never clobbered. On Windows the watch+kill runs in the sibling `reap-watch.ps1` (an
  AMSI-safe split of launch from watch+kill; the `.sh` does it inline).
- Runs codex from a per-unit working dir: a scratch dir by default (read-only units), or the path in
  `PRUN_SCRATCH_CWD` (point this at a throwaway clone for code-writing units).
- Env: `CODEX_DISPATCH_SANDBOX` (default `danger-full-access`), `CODEX_DISPATCH_REASONING` (default
  `xhigh`), `CODEX_DISPATCH_ISOLATE_MCP=off` to drop MCP isolation, `PRUN_SCRATCH_CWD` to set the cwd,
  `PRUN_STALL_THRESHOLD` (default `600`) for the idle-reap threshold, `CODEX_DISPATCH_TIMEOUT`
  (default `0` = disabled) for an optional hard wall-clock cap.

## Sonnet usage

Sonnet is the reserved executor (see Executors), for units needing session-internal tools (MCP /
email connectors, the Artifact tool) or a cross-vendor web verification. Spawn an Agent-tool subagent
with `model: sonnet`. It inherits the session's available tools but starts with **fresh context** (it
does not see the conversation), so put any needed state in the unit prompt. Give it the same return
contract and result-file path. For a code-writing unit, point it at a clone dir; commit and push are
also gated by `guard.py` on the Claude side.

## gather usage

```
scripts/gather.sh <result-file-1> <result-file-2> ...
```

- Prints `GATHER-START count=N timeout=Ss`, then `DONE <abs-path>` per file as it lands; exits 0 when
  all land, exits 2 with `TIMEOUT remaining=<k>`.
- A file is "landed" when it exists, is non-empty, and has been quiet for the stable window
  (default 10s); no startup-snapshot race.
- **Use a fresh result path per unit per run** (delete any stale file before dispatch). Have each unit
  write its result in one operation.

## monitor usage

```
scripts/monitor.sh <state-dir-1> <state-dir-2> ...
```

- Takes the `STATE-DIR` paths from each dispatch (not result files); reads each unit's `tail` (growth),
  `result-file` (done/fail), and `dispatch-pid` (liveness).
- Prints `MONITOR-START units=N stall-threshold=Ts timeout=Ss`, then on the first actionable event
  `MONITOR-EVENT <all-done|stall|fail|timeout>` and one `UNIT <name> <status>` line per unit (`done` /
  `failed(fallback)` / `failed(dispatch-dead)` / `stalled(Ns)` / `growing`).
- Exit: `0` all done, `3` attention needed (a stall or fail), `2` hard timeout.
- Env: `PRUN_STALL_THRESHOLD` (default 600, ten minutes; raise it for long code-writing units),
  `PRUN_MONITOR_POLL` (default 15), `PRUN_MONITOR_TIMEOUT` (default 3600), `PRUN_MONITOR_STABLE_WINDOW`
  (default 10).
- Run it in the background; after handling a stall or fail, re-launch on the still-running units so a
  resolved unit is not re-flagged.

## report-state usage

```
scripts/report-state.sh   [--root DIR] [--json] [--summary] [--sort path|tail-bytes-desc]
                          [--min-tail-bytes N] [--include-legacy-pid]
scripts\report-state.ps1  (same flags)
```

Read-only. It inspects `prun-task-*` directories left behind by earlier runs and writes nothing at
all, which `tests/test_prun_report.py` checks by hashing the tree before and after a run. Reach for
it when a fan-out was interrupted and you need to know which unit output survived. `--root` repeats,
and defaults to the system temp directory.

Every unit carries two independent fields instead of one verdict. A single label such as
"salvageable" would read as permission to act, and this command cannot support that reading without
the process identity it deliberately does not record.

| `result_path_state` | Meaning |
|---|---|
| `resolved` | the unit recorded a result path and it could be read |
| `absent-entry` | no `result-file` entry was written |
| `invalid-entry` | the entry was empty, or a relative path escaping its unit |
| `unreadable` | the entry exists but could not be read |

| `result` | Meaning |
|---|---|
| `present` | the result file exists and holds bytes |
| `empty` | the result file exists and is zero bytes |
| `missing` | the recorded path does not exist |
| `unknown` | nothing is claimed: either the path never resolved, or it resolved and the target could not be observed |

`result` is `unknown` for every `result_path_state` other than `resolved`, and `resolved` may also
carry it. Only `FileNotFoundError` proves a target is gone; a denial or an I/O error yields
`resolved`/`unknown` plus an entry in that unit's `errors`, so a failed observation is never
reported as an outcome. No other pairing can be emitted, and
`test_no_illegal_pair_can_be_emitted` checks that against the table the module exports.

Remaining JSON fields:

| Field | Meaning |
|---|---|
| `schema_version` | `1`; bump on any field change |
| `roots` | absolute directories inspected |
| `unit_count` | units inspected, counted before any display filter |
| `discovery_errors` | roots or matching entries that could not be listed or stated |
| `unit` | absolute path of the unit directory |
| `tail_bytes` | size of the unit's `tail`, `0` when absent, or `null` when it could not be stated or is not a regular file |
| `result_target` | the resolved result path, or `null` |
| `errors` | per-unit observation failures; see the table below |
| `legacy_pid_unverified` | shown only under `--include-legacy-pid` |
| `safety` | the sentence below, present on every run |

Each `errors` entry is `{"stage": <where>, "error": <value>}`. The value is an exception class name,
or one of two names for a condition that raises nothing: `NotARegularFile` when the path exists but
is a directory, FIFO, or device, and `EntryTooLarge` when a `result-file` or `dispatch-pid` entry
exceeds 64 KiB. That size limit reports rather than truncates. A truncated entry can strip down to
a real path and be mistaken for a complete one. Consumers branch on `stage`:

| `stage` | What could not be observed |
|---|---|
| `result-entry` | the unit's `result-file` exists but could not be read |
| `result-target` | the recorded path could not be stated, or is not a regular file |
| `result` | classification raised unexpectedly; the unit is still reported |
| `tail` | the unit's `tail` could not be stated, or is not a regular file |
| `legacy-pid` | `dispatch-pid` exists but could not be read, under `--include-legacy-pid` |

Discovery failures sit apart from any unit, in a top-level `discovery_errors` array whose entries
carry `stage` (`root` or `unit-entry`), the offending `root` or `unit`, and `error`. They are
separate because a root that cannot be listed produces no unit to attach a failure to, and used to
read as an empty corpus. Any entry in either place sets exit `1`.

`--summary` adds two byte counters that never overlap. `missing_or_empty_result` covers units whose
result path resolved to a file that is missing or empty. `unresolved` covers units whose result was
never classified while their tail still holds bytes. Each counter names what was observed rather
than what may be done about it, because neither a missing target nor an empty one proves that no
other copy exists or that a live producer will not fill it. Both appear because the second group is
easy to lose: across a live corpus of 220 units the first counter read 24.3 MiB while another
0.4 MiB sat in a unit nothing had classified.


Under `--json`, those counters arrive in a `summary` object:

| Summary field | Meaning |
|---|---|
| `units` | units inspected, matching `unit_count` |
| `by_result` | count per `result` value |
| `by_path_state` | count per `result_path_state` value |
| `missing_or_empty_result_units` / `missing_or_empty_result_bytes` | resolved path, result file missing or empty, tail holds bytes |
| `unresolved_units` / `unresolved_bytes` | result never classified, tail holds bytes |
`--min-tail-bytes` hides small units from the listing and moves no unit between classes; `unit_count`
still counts them. `--include-legacy-pid` stays off by default. A recorded PID may be stale, or
reused by an unrelated process, so it can never show that a worker is alive.

Exit codes: `0` every root was listed and every unit inspected cleanly, `1` at least one entry
was recorded in a unit's `errors` or in `discovery_errors` while everything readable was still
reported, `2` a usage error. An unreadable root is never reported as an empty one.

## snapshot-tail usage

```
scripts/snapshot-tail.sh   --unit DIR [--dest DIR | --output FILE] [--json]
scripts\snapshot-tail.ps1  (same flags)
```

Copies one unit's `tail` into a ZIP holding exactly two members, `tail.bin` and `manifest.json`,
both stored without compression. Only a regular file, or a symlink to one, may be snapshotted; a
directory, FIFO, or device exits `4` and publishes nothing. Without that rule a device such as
`/dev/null` reported zero bytes and published an empty archive as a complete capture, and a FIFO
with no writer blocked the open indefinitely. The copy is byte-for-byte, so a tail carrying NUL or CR arrives
unchanged. Given neither `--dest` nor `--output`, the archive lands in a per-user state directory:
`%LOCALAPPDATA%\anywhere-agents\prun\snapshots` on Windows, and
`$XDG_STATE_HOME/anywhere-agents/prun/snapshots` elsewhere, falling back to `~/.local/state` when
that variable is unset.

On POSIX the command creates the directory mode `0700` and the archive mode `0600`. A snapshot
extends the lifetime of prompts and tool output, so a directory that already exists and is group- or
world-accessible is refused, with the `chmod` that fixes it named in the message.

Publication goes through `os.link`. That is the one portable operation which is both atomic and
refuses to replace: `os.replace` overwrites, `os.rename` differs by platform, and checking first
races. An existing destination therefore exits `3` and leaves the file byte-identical. Six
concurrent attempts on one name produce exactly one winner. Any other link failure exits `6` rather
than falling back to an operation that could overwrite.

| Manifest field | Meaning |
|---|---|
| `schema_version` | `1` |
| `captured_at` | UTC timestamp of the capture |
| `source_path` | absolute path of the tail that was read |
| `source_size_at_open` | size taken from `fstat` on the already-open handle |
| `bytes_copied` | bytes actually written |
| `sha256` | digest of the copied bytes, re-verified after the archive closes |
| `source_may_be_live` | always `true` |
| `capture_outcome` | `complete_bounded_read` when the two counts agree, `short_read` otherwise |
| `note` | records that equal counts do not prove the source held still |

The read is bounded by `source_size_at_open`, and it is best-effort. Equal counts do not establish
that the source held still, because bytes can arrive from different generations of a growing file
and still total the same number. Read `complete_bounded_read` as "the reader returned `source_size_at_open` bytes before EOF", never
as "the source was unchanged" or "this is a consistent point-in-time copy". A truncate-and-regrow
sequence can also total exactly that many bytes.

JSON output adds `published`, the final path, and `warning`, which is `null` on a clean run. A
warning appears when the archive is linked into place but the temporary file could not be removed.
The snapshot is valid in that case, so the command still exits `0`.

Exit codes: `0` published, `3` the destination already existed, `4` the tail could not be opened
or is not a regular file,
`5` archive validation failed, `6` publication failed. Every failure other than `3` leaves no file
at the final name.

### The safety sentence

**Snapshotting a tail is the only safe operation offered here. This output does not establish that
deleting, overwriting, or promoting any unit is safe.**

`report-state` prints those words on every run, in both text and JSON. `snapshot-tail` does not
repeat them, so apply them yourself after a successful capture: holding a snapshot does not make the
unit disposable. Deciding that a unit is finished needs process identity, which this slice records
nowhere. See anywhere-agents#29 Part B.

## Return contract (every unit writes this)

```
# <unit-id> result
Conclusion: <one line>
Files: <files created/modified in the clone, or "none (read-only)">
Open items: <blockers or follow-ups, or "none">
Verification: <what was run/checked/searched, or "none">

<body: the findings, survey, analysis, or change summary>
```

## Ledger

Keep a simple run ledger (a file in a scratch area) recording each unit: id, executor, mode, prompt
file, state-dir / clone-dir, result file, status (dispatched / done / failed), start/end. Use it to
report progress and to relaunch only units whose result is missing or fails validation.

**Where a unit's own files go**: four kinds of file belong under an `agent-io` directory inside the scratch area. They are the per-unit prompt, the result file, the shared-context file every worker reads, and the run ledger. The directory name tells the writing-style hook to skip them, because none of that text is the coordinator's prose to rewrite. A unit prompt is an instruction to a worker, and a result file holds what the worker sent back. Anything the fan-out produces for a human reader stays outside `agent-io`.

## Web access

Both executors reach the web by different paths, each with its own strengths, so assign per unit.

**Codex** runs on the user's local machine, so its requests leave from the user's local network
rather than the cloud fetcher's egress IP, often a residential IP. That can reach some pages a cloud
fetcher gets `403` on, though a hardened site can still block on bot score, fingerprint, or rate. It
also surfaces pages a cloud fetch would miss. Web access comes from `--sandbox danger-full-access`
(built-in browser path, confirmed under MCP isolation). Codex quota is abundant, so the extra unit is
cheap.

**Sonnet** units get web from an `agentType` granting built-in `WebSearch` and `WebFetch`. Claude's
`WebSearch` is strong at broad discovery (finding the right page when the URL is unknown), but
discovery alone is not a session-internal capability, so treat Sonnet here as a reserved path for an
explicitly wanted Claude-side cross-check or for recovery after Codex discovery falls short, not as
the default for discovery.

Routing heuristic (apply the Executors rule; when in doubt, Codex):

- **Fetch or discover on one path**: use a **Codex** unit first, whether or not the URL is known. Its
  local-network path also reaches some pages a cloud fetch gets `403` on.
- **Codex discovery fell short, or acceptance needs a Claude-side result**: add a targeted **Sonnet**
  unit and its `WebSearch`.
- **A high-stakes fact that might be stale or blocked**: run Codex first, then add a Sonnet
  cross-check when the value of a second vendor's view justifies the Claude-side quota.

A Codex web-fetch unit can use curl. Report the HTTP status per URL so a cloud-vs-local block shows
up in the result. In Windows PowerShell, name the binary `curl.exe`, since a bare `curl` can resolve
to the `Invoke-WebRequest` alias instead:

```bash
curl -sSL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" -o <body-file> -w "%{http_code} %{url_effective}\n" <URL>
```

```powershell
curl.exe -sSL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36" -o <body-file> -w "%{http_code} %{url_effective}\n" <URL>
```
