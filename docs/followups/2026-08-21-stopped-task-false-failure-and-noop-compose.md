# Stopped background tasks read as failed reviews, and a compose that rewrites 86 unchanged files

Date: 2026-08-21. Two independent defects found in one sweep of the local
consumer repositories. The first is fixed in this commit; the second is
recorded here with its measurement and a proposed shape, and is not fixed.

## 1. A stopped task is not a dead reviewer (fixed here)

`/implement-review` dispatches the reviewer as a background task and reads the
harness's task notification. When that notification carries `killed`, with the
summary `Background command "..." was stopped`, the round was treated as a
dispatch failure. Two of them in a row set sticky downgrade for the session.

The notification describes the harness's task wrapper. The reviewer is spawned
detached, through `cmd /c` on Windows, so it outlives the wrapper and keeps
writing to the same inherited handles.

**Measured 2026-08-21.** Six such notifications across two repositories, all
while the reviewer was still running:

| repo | notification | evidence it was alive |
|---|---|---|
| trading-doc | 21:15:39 UTC, dispatch + watcher | dispatch task output last written 21:25:23; watcher output last written 21:25:10, holding `DONE` |
| trading-doc | 21:19:36 UTC, dispatch + watcher | dispatch task output last written 21:36:57; `Review-Codex.md` mtime 21:35:09 |
| agent-startup-thesis | 22:10:05 UTC, dispatch + watcher | watcher output last written 22:12:13, holding `DONE`; `Review-Codex.md` mtime 22:15:59; state-dir tail last grew 22:16:14 |

Each cell is a file mtime, so it dates the last write to that file rather than
the moment a line inside it was produced. The agent-startup-thesis row is the
one that needs saying out loud: the watcher's `DONE` was written at 22:12:13,
about three minutes before the review file's final mtime, because the reviewer
published once, satisfied the watcher, and then published again. The ordering
to take from these rows is only that each artifact was still being written
after its task was reported stopped, which is the claim the rule rests on.

Over the same window (since 2026-08-19, so after v0.7.15 and v0.7.16), the
transcripts hold 34 bootstrap-dispatch task records with 3 stops, all three
identical in shape. Across all history there are 122 stop notifications in 10
repositories, 77 of them review dispatches or watchers; the older output files
are cleaned from the temp directory, so only these six can be proven false.

Both tasks are stopped in the same second, so the lost watcher corroborates
nothing. The stop lifetime is not fixed either: 2m46s, 2m29s, and 24m44s after
dispatch. Both incidents happened while the machine was running a large
fan-out, and one of them observed `pwsh` failing to start with
`0xC0000142`, which is the same process-creation pressure recorded in aa#40.

**The cost was real.** trading-doc's round 3 was declared failed twice, sticky
downgrade was set, and the session stopped. The review it was waiting for
landed ten minutes later, complete, with a `BLOCK` verdict, and was never read.

**The fix**: `skills/implement-review/scripts/await-review.py` resolves the
round from state-dir evidence and returns one of `REVIEW-READY` (0), `ALIVE`
(3), `DEAD` (4), or one of two exit-2 checkpoints for a person: `TIMEOUT` when
the round outlived its deadline, and `REAP-UNKNOWN` when a stream death never
produced its reap-completion marker. SKILL.md now states that a stop
notification carries no authority, that only a `DEAD` verdict is an
Auto-terminal runtime failure, and that the silent-advance gate accepts a
resolved stop in place of an exit code it can never see. Run in the foreground:
the default budget stays under the 600-second cap a single tool call gets, and a
background probe would be exposed to the same stop it exists to diagnose.

The round's bound is a file, `<state-dir>/round-deadline`, stamped once at the
round's origin plus 60 minutes and never rewritten. A deadline held only in the
calling agent's context does not survive the thing this change is about:
the session that dispatched the round can be stopped, compacted, or handed over,
and the ALIVE loop would then have nothing to end it. Writing it once also means
an automatic redispatch cannot quietly buy the round a second hour.

The origin is the earliest readable timestamp in the state directory rather
than the root `timestamp`. A successful redispatch copies the state into
`attempt-N/` and then rewrites the root, so a first resolver call that lands
after a retry would otherwise read the retry's clock. Round 4 of the review
measured that directly: 840 seconds of extension in a replay where no resolver
had run before the retry.

Both `auto-watch` variants gained the same `REAP-UNKNOWN` exit. They now wait
for `stream-reap-complete` before emitting `STREAM-DEAD`, which is right,
because that output costs the session its channel; but each swallows a failed
completion write in a catch block, so waiting alone could hold a round for the
full hour on proof that is never coming. They also accept the state directory by
handoff through `IMPLEMENT_REVIEW_STATE_DIR`. The 30-second discovery window
remains as the fallback, and these incidents happened under exactly the kind of
process-creation pressure that makes such a window miss.

Replayed against the three real state directories above, the script returns
`REVIEW-READY` for all three. Asked for a round that was never dispatched, it
returns `ALIVE reason=round-marker-mismatch`: a wrong marker is reported and
left to the round's deadline, because the same evidence set shows a reviewer
publishing twice.

### A second defect found while verifying the first (fixed here)

`tests/test_session_bootstrap.py` reported all seven of its spawning tests as
`TimeoutExpired` on every full-suite run of the day. The obvious reading was
contention: two suites were running at once, the file carried a hard 60-second
cap that the v0.7.16 sweep had raised in its sibling and missed here, and the
module finished in about 3 seconds when run by itself. So the cap was raised to
the shared 90-second default with the `AGENT_CONFIG_TEST_TIMEOUT` override, and
when 90 seconds was exceeded too, the note here said the remedy was to stop
running two suites at once.

That was wrong, and the number is what gave it away. Run alone, with nothing
else on the machine, the module took **634 seconds**: seven timeouts at
90 seconds each and nothing else. A hang, not a slowdown.

`run_session_bootstrap` passed no `stdin`, so the hook inherited the test
process's own. `session_bootstrap.py` reads stdin to find the SessionStart
payload's `source`, and a handle that never reaches EOF makes that read block
until the subprocess timeout fires. Interactively the parent's stdin was
already at EOF, which is why the module passed in 2.2 seconds and why the
failure looked like it followed the machine's load. The helper now passes
`stdin=subprocess.DEVNULL`, which is what "no payload" should have meant all
along. Same detached launcher, same machine: 634 seconds became 5.

Two things are worth keeping from this. A timing failure that lands on an exact
multiple of the timeout is a hang wearing a slowdown's clothes, and a plausible
first explanation held for two rounds because nobody made it predict a number.
The other is a live one: a `session_bootstrap.py` process had been running on
this machine since 16:00, more than five hours, in the same blocked read. The
hook is invoked with a payload in production, so this needs a caller that
attaches no stdin and never closes it; that path is unproven, and a
`select`-guarded or non-blocking read would close it.

## 2. Compose rewrites 86 unchanged files, and one of them fails (fixed 2026-08-28)

Same day, unrelated path. `bootstrap.ps1` in trading-doc recorded
`completed: false` at phase `generate`, having stopped at `compose` with rc=1:

```
packs.transaction.TransactionError: transaction 20260821T192624-8e5d34af failed
at op[37] (write): [WinError 5] Access is denied:
  '...\pack-compose.staging-3524\dispatch-task.sh.fe0f97ab.new'
  -> '...\.claude\skills\prun\scripts\dispatch-task.sh'
```

The journal left on disk answers the interesting question: **all 86 write ops
in that transaction were no-ops**, every one with `pre_state_sha256` equal to
`new_content_sha256`. Every session start replaces the whole deployed skill
tree with byte-identical content, and the run died on one of those pointless
replacements.

Since 2026-08-19 this shape has failed 3 times in 3 repositories, always on a
`.sh` file under `.claude/skills/prun/scripts/`. Windows Defender has no
detection record for the file and Controlled Folder Access is off, so a
quarantine is not the mechanism. `scripts/packs/transaction.py` already retries
`os.replace` on `PermissionError`, but `_REPLACE_RETRIES = 2` at 0.1s gives a
0.2-second window, and that file has not been touched since 2026-04-27, so no
recent release addressed this.

Proposed shape, in priority order:

1. **Skip write ops whose staged content already matches the target.** The
   journal records `pre_state_sha256`, so the comparison is free. This removes
   the failing op rather than making it more patient, and takes 86 replaces per
   session to zero.
2. **On `PermissionError`, verify before failing.** If the target already
   hashes to `new_content_sha256`, the op's purpose is met; continue.
3. Widen the retry window as a third layer behind those two.

Consequence when it fires: `bootstrap` exits 1 after `generate`, so
`project_files`, `user_files`, `external` and `finalize` never run that
session, and a staging directory is left behind (13 MB in the trading-doc
case). Content integrity held: the deployed tree was byte-identical to a repo
whose run completed.

### What shipped (2026-08-28)

Proposal 1 was taken. The review rounds that followed rejected proposals 2 and 3, and added a
second half that this note had not asked for.

`Transaction._apply_op` now returns early when the target already hashes to the op's
`new_content_sha256`, so a rename that would change nothing is never attempted (aa `c0ee761`).
The measurement held on a fresh sample: a stranded journal from `NSF-Proposal-Template-Yue`
carried 102 write ops and every one was a no-op, including the op that aborted it.

The check sits in `_apply_op` rather than in `stage_write`, which was the first placement tried
and was wrong. An op has to stay queued: the v0.5.2 drift gate walks `self.ops`,
`_validate_prestate` records unmanaged-file adoptions from that same walk, and
`handlers/permission.py` queues several writes to one target where only the last one carries the
answer. `tests/test_packs_reconciliation.py` now pins the classification the skip depends on,
since reordering two comparisons in `_classify_write_op` would have turned it into data loss
while every existing test still passed (aa `3eed3fc`).

**Proposal 2 was rejected on review.** Treating any locked target as satisfied lets
`pack-lock.json` and `pack-state.json` record a directory digest while the tree on disk is a mix
of old and new files. `pack verify` only checks that output paths exist, so it stays quiet about
exactly that drift, and `--fix` reports nothing to repair. Only the narrow form ships: skip when
the bytes match, abort when they do not.

**Proposal 3 was rejected on measurement.** The holder is not an antivirus scan. A shell holds a
script open for as long as it is executing it, and `dispatch-task.sh` waits on its worker, so the
window is minutes rather than milliseconds. No retry length reaches it.

That left the case the skip cannot cover: a release that genuinely changes one of those scripts.
All three long-running `prun` Bash entry points now hand off to a private temp copy before doing
any work, so the deployed path is free while they run (ac `1ee6f6c` and `da1ef1a`, aa `563ff70`
and `e6aad32`). `monitor.sh` and `gather.sh` were never safe, only hidden: files stage in sorted
path order and the transaction stops at its first failure, so `dispatch-task.sh` took every abort
ahead of them. The same defect in the user-level helper deploy is fixed the same way (ac
`0d212d3`, aa `fe81e29`), which is the half aa#44 actually reported.

Verified on Windows 11 and on Linux 6.17 aarch64. The Linux lane is not a second opinion here:
the shared Bash contract mixin skips on Windows, and NTFS reports a plain file as executable, so
the mode half of the helper condition has no state to distinguish there.

Two things were split out rather than folded in. aa#47 records that deployed scripts are not
executable on POSIX, so the bare invocation documented in `SKILL.md` fails with exit 126 there.
aa#48 records that `implement-review` still carries the unreachable exec-failure cleanup that the
`prun` scripts shed in ac `d067c0c` / aa `9f873d5`.

The CHANGELOG entry is queued in
[windows-rename-failure-class-pending-changelog](2026-08-28-windows-rename-failure-class-pending-changelog.md).

## 3. Two smaller findings from the same sweep (open)

- **The session-banner pack-gap check reports a false alarm in every consumer.**
  Shared `AGENTS.md` item 7 compares user-level packs against
  `agent-config.yaml` only, and has no notion of aa's bundled default-on packs.
  26 of 27 consumers on this machine do not name `agent-style` in their yaml
  and all 27 carry the composed block at the pinned `v0.4.1`.
  `anywhere-agents pack verify` gets this right (`deployed (bundled default)`),
  so the two judgements disagree and the banner's is the wrong one.
- **`pack verify` reports a permanent phantom update.** `_ls_remote_head` does
  not peel annotated tags, so `refs/tags/v0.4.1` (`89abbc63`) is compared with
  the locked commit (`65ef8c79`) and never matches. Every consumer pinned to an
  annotated tag shows `1 pack(s) have updates available` that no command can
  clear.

## 4. A stall watcher that fails to start is indistinguishable from a quiet round (open)

Found while releasing v0.7.17. `test_stall_warning_survives_dispatch_completion`
failed on `windows-latest . py3.13` in CI, with an empty dispatch stderr and no
`stall-warning` file after a 30-second wait, on a commit whose only changes were
elsewhere. The same test failed the same way on py3.12 one release earlier and
went green on a rerun with no code change, which is the fifth visit to this
family.

It then failed a third time, on `agent-config`'s `windows-latest . py3.12`, on a
commit whose only change was this file. A rerun of that same job passed with no
code change. Three failures, two repositories, both Python lanes, and one of
them on a docs-only commit: whatever this is, it is not a regression.

There are **three** silent-abort paths, and the one recorded first here is the
least likely of them. Any of them produces the same evidence: dispatch exit 0,
empty stderr, no `stall-warning`, ever.

1. `stall-watch.ps1:121-126` resolves the parent's start ticks with
   `Get-Process` followed by `.StartTime`. That property throws on Windows when
   the process cannot be opened for query, and the handler is a bare `exit 0`.
   The dispatcher's `Start-Process -PassThru` has already returned by then, so
   `$stallProc` is non-null and nothing indicates the watcher is already gone.
2. `stall-watch.ps1:36-49` creates its re-exec directory as
   `implement-review-stall-watch-reexec-$PID` and exits 2 if `New-Item` throws.
   The name is keyed on a PID, the cleanup is a `finally` that a killed process
   never runs, and CI runners recycle PIDs inside one suite. A leftover
   directory from an earlier test therefore aborts a later watcher. The message
   goes to stderr, and the watcher is launched `-WindowStyle Hidden` with no
   redirection, so nobody reads it.
3. `dispatch-codex.ps1:437` launches the watcher with `Start-Process ...
   -ErrorAction SilentlyContinue -PassThru`. A failed launch leaves `$stallProc`
   null and the dispatch continues. This is the path recorded first, and it is
   the only one of the three that leaves any in-process trace.

This is the shape the rest of this note is about, one layer down. A round with
no watcher and a round with a healthy quiet reviewer produce identical
evidence, and Phase 2.0 Check 9 reports `PASS no-stall-warning` for both. The
test is the only thing that currently notices, and it notices as a flake.

Proposed shape. Do not try to pick the guilty path first, because all three are
worth closing and none of them is currently observable. Make startup observable
instead, and the next occurrence names itself:

- The watcher writes `<state-dir>/stall-watch-started` once it is past every
  abort path and about to poll, and writes `<state-dir>/stall-watch-error` with
  a one-line reason on each abort. The re-exec block runs before arguments are
  parsed, so it has to scan `$args` for `--state-dir` to know where to write.
- Check 9 reads those markers. A round whose watcher never started must not
  report a clean `no-stall-warning`, which is the production half of this: today
  a round with no watcher and a round with a healthy quiet reviewer are
  indistinguishable to Phase 2.
- `test_stall_warning_survives_dispatch_completion` waits for the start marker
  before asserting on the warning, and reports the error marker's contents when
  it is absent. That turns this flake into either a green run or a red one that
  says which path fired.
- The Bash variant needs the same treatment, and path 2 argues for a re-exec
  directory name that does not collide, `mkdtemp`-style rather than PID-keyed.

Retrying a failed launch is worth considering separately, since the failure mode
looks transient, but the markers are what close the ambiguity. Note that
resolving path 1 by simply not exiting would be wrong: `$parentStartTicks` is
what `Test-ParentAlive` uses to detect parent death, so a watcher that continues
without it cannot tell when to stop, and this machine has already produced one
process that sat for nine hours.
