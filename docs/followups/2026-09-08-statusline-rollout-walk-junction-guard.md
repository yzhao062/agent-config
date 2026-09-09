# Rollout discovery: exclude Windows junctions from the directory walk

**Status**: Open, captured 2026-09-08. Optional extension of a Low finding that
did not block its commit.

**Owner**: Yue (driver) + Claude (implementer when invoked).

**Origin**: Codex review round 4 of the statusLine plan-meter fix, finding R7.
The commit that carries this file replaced `glob.glob(..., recursive=True)` plus
a per-file `os.path.getmtime` with an `os.scandir` stack walk in
`scripts/statusline.py` and `scripts/agent-quota.py`.

## What the walk does today

Discovery skips a symlinked directory, because it asks
`entry.is_dir(follow_symlinks=False)` before pushing a path onto its stack. That
bounds it against a symlink cycle under `~/.codex/sessions`, which the old
`glob` `**` traversal did not: `**` followed directory symlinks, so a link
pointing at an ancestor could loop or double-count on every status line render.

## The gap

A Windows junction is not a symbolic link. It keeps the directory attribute that
`follow_symlinks=False` tests, so the guard does not exclude it and the walk
descends. The reviewer reproduced repeated descent with a real junction in both
scripts. Duplicate aliases can also fill the twelve-file sample that
`MAX_ROLLOUT_SCAN` bounds, which would push a genuine rollout out of it.

## Why it was not closed in that commit

Three reasons, in order of weight.

The exposure predates the walk. `glob` followed junctions as well, so the change
strictly narrows the problem rather than introducing it, and nothing regressed.

Codex writes `~/.codex/sessions` as a plain date tree. There is no supported
reason for a junction to appear inside it, which is why the reviewer graded the
finding Low and asked only that the docstring stop claiming more cycle safety
than the guard delivers. That much shipped: both docstrings now name the gap.

The review round that returned `PASS` reviewed the production code as it stands.
Adding a guard afterwards would put an unreviewed behavior change into a
STRICT-parity file in two repositories, which is the thing the review loop
exists to prevent.

## What closing it would take

`DirEntry.is_junction()` arrived in Python 3.12 and these scripts run under
whatever interpreter `~/.claude/hooks/_python` resolves, so the call needs a
`getattr` fallback rather than a bare invocation. The change is roughly four
lines in each copy, and the two copies are STRICT-shared, so they move together.

A test cannot create a junction portably, so it would follow the pattern the
round-4 tests already use for the symlink case: a `DirEntry` stand-in whose
`is_junction()` returns `True`, re-appended on every listing so a descending
walk would not terminate. `tests/test_codex_usage.py::TestRolloutDiscovery`
holds the equivalent symlink pair to copy from.

## When it is worth doing

If a junction ever does appear under `~/.codex/sessions`, the symptom is a status
line that stops rendering, because the walk does not terminate. That is loud
rather than silent, which is part of why it can wait. Fold it into the next
change that touches the walk for another reason.
