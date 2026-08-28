# Windows rename failure class: CHANGELOG entry queued for the next release

**Date:** 2026-08-28
**Status:** drafted, not yet placed; belongs in the next release commit
**Scope:** `anywhere-agents/CHANGELOG.md`
**Reader:** whoever cuts the release after 0.7.18

## Why this note exists

Six commits close aa#43 and aa#44. None of them touched a release-record file, which is this
project's normal shape: feature commits and release commits stay separate. The entry below is
recorded here so the next release does not have to reconstruct it from the diff.

| Repo | Commit | What |
|---|---|---|
| aa | `c0ee761` | composer skips a write whose bytes already match the target |
| aa | `3eed3fc` | reconciliation tests pinning the classification that skip relies on |
| ac / aa | `1ee6f6c` / `563ff70` | `dispatch-task.sh` re-executes from a private temp copy |
| ac / aa | `0d212d3` / `fe81e29` | bootstrap helper deploy skips when the target already matches |
| ac / aa | `da1ef1a` / `e6aad32` | `monitor.sh` and `gather.sh` get the same release |
| ac / aa | `d067c0c` / `9f873d5` | the exec-failure cleanup becomes reachable; liveness test fixed |

The measurement, the rejected alternatives, and the review history live in
[stopped-task-false-failure-and-noop-compose](2026-08-21-stopped-task-false-failure-and-noop-compose.md)
section 2. Two issues were split out rather than folded in: aa#47 (deployed scripts are not
executable on POSIX) and aa#48 (`implement-review` still carries the unreachable exec cleanup).

## The entry

Place under the new version heading, alongside anything else landed since 0.7.18.

### Fixed

- **A compose no longer aborts because a worker is running.** On Windows a rename over a file
  another process holds open without `FILE_SHARE_DELETE` is refused, and a shell holds a script
  open for as long as it is executing it. `prun`'s dispatcher waits on its worker for the whole
  run, so any compose that fired during a live fan-out died on that one file and left the pack
  tree half replaced. Across every session transcript on one machine, 13 of 15 recorded compose
  aborts between 2026-08-08 and 2026-08-28 named it.

  Two changes close the class from opposite ends.

  A compose no longer performs a rename that would change nothing. `Transaction._apply_op`
  returns early when the target already hashes to the op's `new_content_sha256`. One stranded
  journal from a real consumer measured how much of that work was pointless: 102 write ops, and
  all 102 carried equal pre-state and new-content hashes, including the one that aborted the
  transaction. That check sits in `_apply_op` rather than in `stage_write` because the op has to
  stay queued for the v0.5.2 drift gate, for the unmanaged-file adoption record, and for the
  handlers that queue several writes to one target. Only the rename half of a restamp is
  skippable; the old path is still removed.

  This is not a general rule that a locked file may be ignored. A write whose content genuinely
  changed and cannot land still aborts, because the lock file records the hash the compose
  intended and a quiet skip would leave it describing bytes that are not on disk.

  For that remaining case, the three long-running `prun` Bash entry points now hand off to a
  private temp copy before doing any work, so the deployed path is free while they run.
  `dispatch-task.sh`, `monitor.sh`, and `gather.sh` each carry the guard with their own sentinel.
  The last two were never safe, only hidden: skill files stage in sorted path order and the
  transaction stops at its first failure, so `dispatch-task.sh` took every abort ahead of them.
  Their `.ps1` siblings need none of this, because PowerShell releases a parsed script file.

- **A bootstrap run is no longer recorded as incomplete because a helper did not need
  deploying.** The user-level helper deploy renamed a staged copy over its target on every run,
  and both entry points exit when that rename is refused, so the phases after it never ran.
  `_atomic_deploy_helper` and `Copy-HelperAtomic` now return success when the target already
  holds what would be deployed. The Bash side also requires the executable bit the caller asked
  for, since returning success while the target is not executable would leave a helper the
  caller wanted runnable sitting there unrunnable.

- **A failed re-exec now reports itself.** All three `prun` guards placed a diagnostic, a removal
  of the private directory, and `exit 2` after a bare `exec`. Bash exits a noninteractive shell
  on exec failure by default, so none of it could run and a launch failure would have leaked the
  directory silently. `set +e` and `shopt -s execfail` immediately before the exec make the
  cleanup reachable. Measured both ways on Git Bash 5.2 and on Linux bash 5.2.

## Verification recorded for the release

Run on both platforms, because two of these paths cannot be observed on Windows at all: the
shared Bash contract mixin skips there, and NTFS reports a plain file as executable, so the
mode half of the helper condition has no state to distinguish.

| | Windows 11, Python 3.12.12 | DGX Spark, Linux 6.17 aarch64, Python 3.12.3 |
|---|---|---|
| aa packs + compose | 744 passed, 4 skipped | 731 passed, 10 skipped |
| ac bootstrap + repo suites | 334 passed, 11 skipped | 167 passed, 41 skipped |
| ac `test_dispatch_task.py` | 38 passed, 21 skipped | 30 passed, 29 skipped |
| helper executable-bit case | skipped, platform cannot observe | passed |

`scripts/check-parity.sh` reported STRICT clean throughout. Three review rounds, final verdict
PASS, with the round-1 and round-2 findings taken in full.
