---
name: mac-storage-audit
description: Audit this personal Mac's disk usage, growth since an earlier scan, and scattered research artifacts whose recovery is uncertain. Read-only by default. Use for shrinking free space, storage classification, or project outputs outside PycharmProjects.
---

# Mac Storage Audit

Private skill for agent-config only. Do not mirror it into anywhere-agents, deploy it globally, or modify machine settings as part of an audit. The existing baseline is [Mac storage audit](../../docs/mac-storage-audit.md), beside [Mac setup](../../docs/mac-mouse-preferences.md). Treat those numbers as dated evidence, not current state.

Invoke this skill by its path inside agent-config. Do not add a `.claude/commands/` pointer: bootstrap copies those pointers into consumer repositories.

## Permissions and priorities

Inspect existing files without modifying, moving, deleting, installing, or changing settings. Read-only analysis is permitted when the user says not to modify files. Create only small new analysis artifacts in a fresh system temporary directory when needed. Saving a report in the repo, updating a baseline, cleaning caches, or creating a scheduled scan each needs user authorization. Do not bootstrap inspected projects. Never print credentials, session message contents, or complete environment variables.

The highest-risk finding is a potentially unique artifact with no verified recovery source. Size and age alone do not establish that a path is disposable. Keep these classes separate:

| Class | Evidence to seek |
| --- | --- |
| Recovery verified within the checked scope | Matching verified backup or a demonstrated reconstruction path for the specific artifact |
| Recovery depends on conditions | Download URL, exact revision, credentials, dependencies, cost, or compute needed to reproduce it |
| Recovery unconfirmed | An artifact exists, but a complete alternative copy or reconstruction has not been checked |
| Potential unique-copy risk | Hand edits, raw observations, experiment outputs, local-only commits, settings, or data exist outside documented storage with no alternative copy found in the checked scope |

Do not claim that no backup exists merely because one was not found locally. A configured backup destination is not proof that a particular file is backed up. A Git remote or clean worktree does not cover ignored files, untracked data, local-only commits, or unpushed branches. Read Git status and existing refs without fetch or index-refresh writes, using `git --no-optional-locks` and `GIT_NO_LAZY_FETCH=1` where applicable. Do not inspect missing promisor blobs through commands that could download them. Compare candidate copies selectively; do not hash entire disks. Prefer a small manifest or sample first, and state whether verification covered all files or only a sample. Re-running a stochastic or paid experiment is not recovery of the original result.

Inspect local backup configuration with read-only commands such as `tmutil destinationinfo` and check whether the exact at-risk paths are covered. A visible sync folder is not proof of backup coverage; absent local configuration does not rule out external drives, manual uploads, or cluster copies.

## Establish the current footprint

Start with `df -k /System/Volumes/Data`. State whether the user's number means used or available space. Use decimal GB throughout, or explicitly label GiB. Convert KiB to GB with `KiB * 1024 / 1e9`. Compare like-for-like measurements, preserving dates and the distinction between a filesystem free-space change and the sum of directory changes.

Use `scripts/scan_storage.py` with a working Python interpreter to collect metadata. It writes JSON to stdout and never creates a report itself. Supply a small set of roots for the first pass, then inspect large children. With no roots it examines the home directory, `/private/tmp`, `/private/var/folders`, `/Applications`, and `/Library`. Those roots do not constitute an exhaustive volume scan.

```bash
python -B scripts/scan_storage.py --root "$HOME/.codex" --root "$HOME/.gemini" --depth 1
```

Resolve the script relative to this skill, and prefer the local Miniforge py312 interpreter. Redirect stdout only to an authorized new report or temporary evidence file. `--baseline` accepts an earlier JSON produced by this collector. For the older Markdown baseline, compare named paths manually. Use the same roots and depth for reproducible deltas. An absent row, a failed scan, and a zero-byte directory are different states. The collector lists unmatched paths explicitly. Partial root pairs retain before/after observations but suppress numeric deltas; rescan accessible children as separate roots and retain those captures for future comparisons.

Inspect independently sized areas without counting parent and child totals twice:

- Agent state: `~/.codex`, `~/.claude`, `~/.gemini`, `~/.cache`, and tool version directories. Separate persistent scratch, databases, conversation records, worktrees, runtime installs, and downloadable caches.
- Research and personal content: `~/PycharmProjects`, `~/Documents`, `~/Downloads`, visible experiment directories in home, and `~/data`. Identify intentional backups separately.
- Applications and system temporary storage: `~/Library`, `/private/tmp`, `/private/var/folders`, applications, and readable system data. Application VM images and caches need their own interpretation.

`du` reports allocated blocks, not guaranteed reclaimable bytes. APFS clones, hardlinks, sparse files, shared container space, and scans of a live system prevent a naive reconciliation with `df`. Hardlink blocks may be credited to a different child between scans, producing a child delta with no new disk allocation. Preserve permission errors and partial results. Do not describe a protected directory as empty. `tmutil listlocalsnapshots /` covers Time Machine local snapshots; use the relevant `diskutil apfs listSnapshots` volume query before making a broader APFS claim. Investigate deleted-open files or snapshots only when the remaining discrepancy justifies it. Do not request elevated privileges or restart applications automatically.

## Trace scattered artifacts

First revisit every high-risk artifact named in the previous audit. Record present, confirmed relocated, or missing from the original location. Put missing high-risk artifacts first in the report. Search documented archives and selected distinctive filenames before asking where they went. An unsuccessful Spotlight search is not exhaustive. Do not equate a missing original path with data loss, or infer automatic retention from a size reduction. Agent-managed scratch, including Agy brain, is not dependable archival storage.

For large project-external paths, inspect names and metadata, source-code output defaults, and references from current project scripts. Watch for `Path.home()`, `expanduser`, model download defaults, `HF_HOME`, `cache_dir`, persistent agent scratch, and relative paths resolved from an unexpected working directory. Distinguish reads from writes, local execution from remote/CI code, and cleaned-up temporary contexts from retained workspaces.

For the most concerning paths, record the owner project or task when supported, current size, latest write time, references still depending on it, and recovery evidence. An empty `lsof` result does not prove inactivity. A directory named `scratch`, `tmp`, or `cache` inside home is not covered by assumptions about system temporary-directory cleanup. Do not promise that reboot clears every system temporary path.

Use modification, metadata-change, and creation timestamps together when investigating dates. Copies can preserve old modification times; tools can touch metadata without adding data. Timestamps support a chronology but do not establish byte identity, complete historical occupancy, or physical allocation by themselves.

Prioritize scattered hand-edited or irreplaceable research artifacts over redownloadable package caches. Inspect manifests for exceptions inside cache containers, such as locally generated probe data. The personal storage convention is project output in the project, disposable work in system temporary space, and long-term non-Git research archives in `~/PycharmProjects/research-data/`. That convention is not a backup and is not an enforced sandbox.

## Optional independent analysis

Use local `prun` and `/vet` only when the user requests or authorizes them. Do not silently add workers to an ordinary scan. Read their current local skills before dispatch. Partition by disjoint roots to avoid repeated full scans and duplicated totals. Give workers the read-only boundary, the baseline, units, and recovery-risk question. Run workers from temporary scratch, with prompts, evidence, results, and ledger under `agent-io`.

When three-party analysis is requested, reconcile the Agy findings in the coordinator and obtain independent Claude and Gemini review of the evidence and conclusions as available under `/vet`. Record the actual backend/model, failures, disagreements, and whether a claim has independent support. Reviewers inspect evidence and selected paths; they do not remediate findings. User no-modification limits override skill defaults that would write review files or snapshots into the real repository. Use a temporary review sink and never change `.git/info/exclude` for this audit.

## Report and revisit

Lead with used/available space and the measured change since the baseline. Show current large paths, comparable deltas, what the data represents, and recovery status. Separate verified growth from currently large paths lacking a baseline. Explicitly mark nested totals and partial scans. Do not label all agent data as logs or all old directories as zombies.

Identify a short priority list of recovery risks and what would resolve each uncertainty, such as checking the exact backup, locating the original remote revision, or archiving unique results. Do not equate a cleanup candidate with permission to delete it. Include scan timestamp, scope, measurement method, and significant gaps.

Return findings in chat unless a saved report is requested. If authorized, update the Mac storage record with a new dated measurement while preserving the earlier baseline and link it from Mac setup. A reusable JSON capture may accompany an authorized report. Never overwrite a prior capture silently. Do not commit, push, schedule, migrate, or clean as part of the scan.
