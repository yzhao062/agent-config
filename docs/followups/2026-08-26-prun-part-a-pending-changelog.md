# prun Part A: CHANGELOG entry queued for the next release

**Date:** 2026-08-26
**Status:** drafted, not yet placed; belongs in the next release commit
**Scope:** `anywhere-agents/CHANGELOG.md`
**Reader:** whoever cuts the release after 0.7.18

## Why this note exists

anywhere-agents#29 Part A shipped in aa `570c89f` and ac `d48b664`. Neither commit touched a
release-record file, which is this project's normal shape: `RELEASING.md:153` names only three
version-bearing files, and recent history keeps feature commits and release commits separate.
`f54d16f` and `4177461` are feature commits that touched none of the four release-record files;
`210ee0c` and `a845718` are the release commits that touched all four.

So there is nothing to correct about `570c89f`. The entry below is simply not written yet, and it
is recorded here so the next release does not have to reconstruct it from the diff.

Two things the release should know:

- The current file has no `## [Unreleased]` section. It carried one between `56f18a0` and `65bc2d1`
  and has used concrete version headings since. `RELEASING.md:164` and `RELEASING.md:302` still
  describe an Unreleased flow that the file no longer follows, which is worth reconciling
  separately.
- `RELEASING.md:12` places tagging before the CI wait, while the mandatory detail at
  `RELEASING.md:191` and `RELEASING.md:205-230` places it after. The detailed section governs.

## The entry

Place under the new version heading, alongside anything else landed since 0.7.18.

### Added

- **`prun` can recover output stranded in interrupted unit directories without deciding whether a worker finished.** `report-state.{sh,ps1}` reads and classifies `prun-task-*` directories, and writes nothing. `snapshot-tail.{sh,ps1}` copies one unit's `tail` into a ZIP containing only stored `tail.bin` and `manifest.json` members. Neither command queries process state.

  The reporter follows one rule: a failed observation never becomes an outcome. It therefore emits orthogonal `result_path_state` and `result` fields instead of one verdict. A label such as `salvageable` reads as permission to act, but this slice carries no process identity to support that permission.

  Only `FileNotFoundError` may produce `missing`. A denial, an I/O error, a non-regular file, an unreadable root, or an over-long entry becomes an error and makes `report-state` exit 1. Before this distinction, an unreadable corpus was indistinguishable from an empty one. For a recovery command, that reads as "nothing here to recover."

  Two disjoint counters carry the summary, `missing_or_empty_result_{units,bytes}` and `unresolved_{units,bytes}`. The first covers observed missing or empty result targets; the second covers tails whose results were never classified. Folding them together would assert that an unresolved unit lost output, something the command did not observe.

  Snapshot publication uses `os.link`, the one portable operation that is both atomic and refuses to replace. `os.replace` overwrites, `os.rename` has platform-dependent replacement semantics, and check-then-rename races. An existing destination exits 3 and leaves the artifact byte-identical. Any other link failure exits 6, with no fallback to a replacing operation.

  Only a regular file, or a symlink to one, may be snapshotted. A FIFO with no writer blocks the open forever, and a device such as `/dev/null` reports `st_size == 0` and would publish an empty archive stamped `complete_bounded_read` without this check.

  The manifest refuses to equate equal byte counts with an unchanged source. A growing, truncated, or rewritten file can supply bytes from different generations while the totals still match.

  Verification passed 512 tests on Windows and 67 tests on real aarch64 Linux hardware, with zero skips on Linux. The Linux run exercised the FIFO, device-file, symlink, chmod-cleanup, and POSIX permission cases. `scripts/check-parity.sh` was STRICT clean across `agent-config` (`ac`), `anywhere-agents` (`aa`), and the wheel composer mirror.

### Changed

- **Recursive skill parity now ignores generated Python bytecode and gates tests that cover shared code.** A recursive skill diff could encounter environment-specific `__pycache__` only after a skill shipped a Python module. All recursive skill comparisons in `scripts/check-parity.sh` now pass `--exclude=__pycache__`. The `strict_test_files` list now registers `tests/test_prun_report.py`, `tests/test_prun_snapshot.py`, and `tests/test_style_audit.py`. Those tests cover STRICT-shared code, so a test present on one side only guards one repository.

- **`style-audit.py` reports policy-suppressed rules in their own coverage bucket.** A suppressed rule now appears under `suppressed` instead of `covered`. Its detector ran, but policy discarded its findings. Counting it as covered overstates the audit, and a coverage report that overstates itself defeats its own purpose.
