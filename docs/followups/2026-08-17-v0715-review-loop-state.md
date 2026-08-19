# v0.7.15: where the review loop stopped, and what is left

**Date:** 2026-08-17
**Status:** staged in both repos, not committed, not pushed
**Scope:** `bootstrap/bootstrap.{sh,ps1}`, `scripts/merge_settings.py`, `scripts/check-parity.sh`, `tests/`

## Why this note exists

The v0.7.15 review loop ran six rounds in one session. Rounds 3, 4 and 5 each returned
`BLOCK` with High-severity data-loss findings, and each set of repairs introduced defects
the next round caught. Round 6 was dispatched and then left to finish unattended; the
work stopped deliberately rather than because the loop converged. This records the state
so the next session does not have to reconstruct it.

## What is verified

- `agent-config` and `anywhere-agents` full suites green.
- `scripts/check-parity.sh` STRICT clean, run correctly from both directions.
- All 26 consumer checkouts on the maintainer's machine parse as `nonempty` through Bash
  and both PowerShell editions, and every answer matches `scripts/packs/config.py`.
  Before this release all 26 parsed as `empty`, the answer that deletes pack blocks.
- `dgx-spark` answers `configured` through all three entry points.
- Every code change was checked by reverting it and requiring the test that names it to
  go red. Two of those checks were themselves wrong at first and are worth remembering:
  one reverted a no-op, and one ran in `agent-config` where the resolver differential
  skips, so it reported green for a test that never executed.
- A differential over twenty-three project-local layer shapes, each behind a tracked
  `packs: []`, agrees with the resolver on every shape in both directions.

## Round 6

Dispatched at 21:29 and left running. Its review lands in `anywhere-agents/Review-Codex.md`,
which `.gitignore` excludes, so it does not affect the staged tree. It was reviewing the
tree as of that moment; one further fix landed afterwards, the leading-indent rule
described below, so its notes are one change stale.

The prompt asked it to look at five things. Read its answers before doing anything else:

1. The key reader is new and decides every layer's answer.
2. The classifiable-line rule decides when an opt-out is overridden.
3. `Read-JsonFileUtf8` now throws on three conditions, and three call sites depend on it.
4. Whether any new test can pass by skipping.
5. Whether the recorded-gap list's claim holds.

## Known gaps, recorded in both scripts

The no-Python gate answers whether anything is selected, not which packs are. Naming them
means pulling names out of YAML without a YAML parser, which is the fragility this release
exists to remove. Five consequences follow, and each keeps a file the resolver would have
replaced rather than deleting one it would have kept:

1. A subtraction-only overlay cannot be evaluated without resolving names.
2. An overlay whose additions and subtractions cancel reads as one addition here.
3. Marker names are never compared with selected names.
4. `config.parse_env_var` splits on commas alone; these split on whitespace too.
5. A layer this scanner cannot read counts as uncertainty once a clear is in force.

Item 5 is the newest and the one to watch. A line is classifiable when it is blank, a
comment, indented below a top-level line, a block sequence item, or a top-level key whose
name is made of name characters. A root-level flow mapping and a document written one
indent in both fail that test and therefore preserve.

## The seventeen errors in the `anywhere-agents` run, and why they are not regressions

The full `anywhere-agents` run reported `FAILED (errors=17, skipped=125)` over 1860 tests.
Every one of the seventeen is a `subprocess.TimeoutExpired` on `bash.exe bootstrap.sh` after
30 seconds, and all of them land in the first ten methods of `BootstrapLedgerBashTests`.
Three checks settle what they are:

- `tests/test_bootstrap_preflight.py`, `tests/_quiet_spawn.py` and `bootstrap/bootstrap.sh`
  are byte-identical across the two repos, so a code regression would have to fail in both.
  The `agent-config` run of that same file was green at 990 tests.
- Re-running exactly those ten methods on a quieter machine gives `Ran 10 tests in 172.478s`
  and `OK`.
- 172 seconds over ten methods is roughly 17 seconds each against a 30-second cap. A margin
  under 2x on this machine is thin enough that a parallel suite pushes it over.

An earlier run of the same suite also produced one failure in `tests/test_stall_watch.py`
(`first stall should be logged after 2s threshold`). That module run alone gives 20 tests and
`OK`, so it is the same class of load-induced timing failure.

The cap appears at nine call sites in the preflight test. It was left out of v0.7.15
because that release was already closed to code changes. It was fixed in v0.7.16 after
biting a third time, during a reviewer's own verification pass: the nine sites now share
`SUBPROCESS_TIMEOUT`, 90 seconds by default and overridable through
`AGENT_CONFIG_TEST_TIMEOUT`.

## The first release push failed CI on four defects

Both repos were pushed at the release commit and every one of the eighteen Repo
Validation jobs failed. Nothing had shipped, because no tag was cut. The four
causes, all fixed in a follow-up commit:

1. `powershell_stub_dir` returned `stub_dir/"ps"` on every platform, and every
   `.ps1` writer sits behind `os.name == "nt"`. Off Windows the directory is
   never created, so `pwsh` got a PATH entry that does not exist, the git
   preflight failed, and forty-six tests asserted against a bootstrap that
   never started. Every ubuntu and macos job.
2. Seven callers passed `newline=` to `Path.write_text`, which gained the
   keyword in 3.10 while this suite still supports 3.9. The file already
   carried a comment saying so, above `_write_executable`. Every 3.9 job.
3. `_user_config_path` chose the Windows branch from `$OSTYPE` alone. Bash sets
   that variable with `set_if_not`, so an exported value survives; measured,
   Git Bash handed `OSTYPE=linux-gnu` reports `linux-gnu`. The runner exports
   one that is not `msys`. Every windows job, and a real defect off CI as well.
4. The self-comparison guard added in this release refused the one legitimate
   coincidence: the wheel-mirror block needs a single tree, and CI checks
   `anywhere-agents` out with no sibling to compare against. `--aa-internal-only`
   is now that mode.

Two lessons worth keeping. A test-only change is still a change that CI runs on
five Python versions and three platforms, and this release's test additions
broke more jobs than its shipped code did. And a guard added late in a release
needs the same survey of its callers as any other change; this one was written
against the accident it had just seen and never checked against the script's own
test.

## The one thing to do before shipping

Round 6's findings are unread. Everything else is done. If its findings are confined to
input shapes no consumer produces, which is where rounds 4 and 5 were trending, record
them here and ship. If any of them reaches a real consumer configuration, fix it first;
the field scan in `scripts` is the check that decides which it is.

## What not to repeat

- `scripts/check-parity.sh` used to accept an argument that made it compare one tree
  against itself and print `STRICT clean`. Two runs during this release did that, one of
  them the reviewer's own verification. It now exits 2. From `anywhere-agents` run it with
  no argument; from `agent-config` run it with `../anywhere-agents`.
- A revert-and-require-red check proves nothing if the test it targets skips in the repo
  where the check runs. Confirm the test actually executed.
