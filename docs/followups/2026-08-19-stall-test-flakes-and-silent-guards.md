# Two flaky stall tests, and two guards that failed silently

**Date:** 2026-08-19
**Status:** Part 1 fixed 2026-08-19; Part 2 still open
**Found during:** the v0.7.16 release
**Scope:** `tests/test_stall_watch.py`, `tests/test_dispatch_codex.py`, and a pattern in `bootstrap/bootstrap.sh`

## Why this note exists

Two separate things went wrong during one release and neither belongs to the release's
own scope. Both are cheap to fix and both cost real time here, so they are written down
rather than carried in someone's head. The flakes blocked a release gate for about an
hour. The silent guards are the reason two defects reached CI at all.

## Part 1: two flaky tests in the stall-detection family

Both tests wait a fixed five seconds for a background watcher to write
`stall-warning`, and five seconds is what a quiet machine needs. Neither failure
says anything about the product; both say the wait was tuned while nothing else
was running.

### `tests/test_stall_watch.py` `test_stall_logged_after_threshold`

The more fragile of the two. It spawns the watcher with `threshold=2, interval=1`,
calls `time.sleep(5)`, then asserts once. There is no retry, so a watcher that has
not finished its poll cycles inside five wall-clock seconds fails the test outright.

Observed on this machine during the v0.7.16 work, on `anywhere-agents`, while two
other full suites were running against the same disk. The same test passed on a
later run with less competing load.

### `tests/test_dispatch_codex.py` `test_stall_warning_survives_dispatch_completion`

Better shaped but capped the same. It polls for the file ten times at half-second
intervals, which is again five seconds, waiting for the watcher's
final-on-parent-dead poll to flush.

Observed on CI, `anywhere-agents` run `32202323898`, commit `d74ca58`, job
`windows-latest . py3.12`. The evidence that it is timing and not a defect is
direct: `tests/test_dispatch_codex.py` is byte-identical between the two
repositories, and `agent-config` run on commit `a2be44f` passed the same test on
the same platform and Python version in the same window. Re-running the single
failed job turned it green with no code change. The one asymmetry between the two
repositories is suite size, 1897 tests against 1018, so the `anywhere-agents`
runner sits under roughly twice the sustained load.

### Suggested direction

Give both waits the treatment `SUBPROCESS_TIMEOUT` already got in v0.7.16: one
named constant, a default with real headroom rather than 2x, and an environment
override. Convert the fixed `time.sleep(5)` into a poll loop at the same time,
since a test that sleeps and asserts once cannot benefit from a longer budget
without paying for it on every green run.

This is the third distinct place where a wait sized on an idle machine has failed
under load in two releases, after the nine bootstrap subprocess call sites. It is
worth one sweep for the remaining ones rather than a fourth visit.

### What was done, 2026-08-19

The fourth visit arrived the same day. Both repositories failed
`test_stall_warning_survives_dispatch_completion` on the same push, on
`windows-latest . py3.12` only, and both went green on a rerun of that single job
with no code change. A later local run then produced a third member of the family,
`test_growth_resets_stall_period_and_relogs`, which this note had not named. So the
sweep covered both files rather than only the test that happened to be red.

Neither file needed a new idiom. `tests/test_stall_watch.py` already had
`_wait_for(predicate, message, timeout)` and used it at eight call sites; three
waits had never adopted it. `tests/test_dispatch_codex.py` already had an inline
deadline loop for its mock reviewer; one wait had not. No second helper was added.
The default is now `STALL_WAIT_TIMEOUT_SECONDS`, 30 seconds, carrying the same name
in both files so one environment variable covers the family.

Five waits were converted: in `test_stall_watch.py` the threshold test this note
opened with, the first stall window, the second stall window after a growth burst,
and the mid-transcript disconnect check; in `test_dispatch_codex.py` the ten-poll
loop.

The mid-transcript one was not on the original list and is the more interesting
repair. It slept, then asserted that no `stream-death` file had appeared. That
reads as a settle window for a negative, which is why the first pass left it
alone, and Codex Round 1 pointed out that it is also a false green: a watcher that
never polled during the window would satisfy the assertion without the classifier
ever being asked. The replacement waits for a second `STALL` line instead. Both
implementations test the stream-death suffix at the top of the growth branch and
exit there on a match, so the latch reset that permits a second `STALL` is
reachable only past that check (`stall-watch.ps1` lines 309-341, `stall-watch.sh`
lines 281-301). Stated precisely, a second `STALL` proves the watcher observed
growth and that the suffix check returned no match. It does not prove a successful
read, because both classifiers report no match when their own read fails. That is
still more than the sleep established, which was nothing at all.

Three sleeps remain in these two files, and they are not one category. One is a
deliberate watcher-survival interval, `assertIsNone(watch.poll())` after two
seconds. One sets the mock's stderr-progress cadence and is workload rather than a
wait. The third, the post-dispatch check that no `stall-warning` was written under
continuous progress, is the same shape as the mid-transcript case and has the same
false-green exposure, but closing it needs a completion signal the dispatcher does
not currently expose. It stays as timing debt for the repository-wide sweep this
note keeps deferring. Raising its sleep would not fix it.

That sweep now has a shape, which it did not before. Classify each wait as a
positive event wait, a negative observation window, or workload cadence. Positive
waits become deadline waits. Negative windows need an observable acknowledgment
from the thing being watched, since a longer sleep buys nothing there. Cadence
stays as it is. The mid-transcript repair above is a worked example of the middle
case, and the post-dispatch check is the next one waiting for it.

Green runs got faster, because a deadline loop leaves when the event arrives while
a sleep always pays in full. Measured here: the threshold test went from 5.0s to
3.9s and the growth test from 10.0s to 6.3s. Each converted test still fails, and
fails inside its budget, when the watcher is pointed at a file name nothing reads.
That was checked on the PowerShell lane on Windows and on the bash lane on ARM64
Linux, since Windows skips the bash class by design.

## Part 2: both v0.7.16 defects failed closed and silent

Two defects reached CI during this release. Neither raised anything. Both exited 0
and left the run looking healthy, which is why each took a full gate cycle to find.

**The missing-source guard.** `test_an_absent_upstream_readme_creates_nothing`
asserted only that the README was absent. The capture helper reports an absent file
and a directory the same way, so a mutation that created `todo/` before checking for
the template stayed green in all three entry points. Codex Round 1 found it by
mutation. Fixed in v0.7.16 with `capture_exists_into`.

**The `cut` dependency.** The lone-negation repair took its line numbers through
`cut`, the only use of it in the script, and the test fixture builds a minimal PATH
that has none. Both pipelines returned an empty string, the `-n` guards below read
that as "nothing to compare", the repair was skipped, and the run exited 0. Windows
CI, three local Windows full-suite runs, the 221-test preflight module and the Codex
review all passed it. The runbook's Linux gate caught it, and CI then showed the real
blast radius: seven failing jobs, every ubuntu and every macOS job.

The shape is the same both times. A guard meant to say "this input is not applicable"
also absorbs "this did not work", and the two cases are indistinguishable from the
outside. The `-n` guards in the negation repair are the clearest example: an empty
line number means either the rule is absent, which is normal, or the pipeline broke,
which is not.

### Suggested direction

Worth deciding, not worth guessing at here. The narrow version is to make the ignore
helpers complain when a probe they depend on cannot run. The broader version is to
ask which of bootstrap's skip paths can currently absorb a failure, since bootstrap
runs at session start in every consumer and a silent skip there is invisible by
construction. The ledger is the natural place for the answer to land, because it
already records what each phase wrote.

## What is not proposed

Nothing here argues for changing the stall-detection behavior itself. The watcher
works; the tests measure it with a stopwatch that is too short.
