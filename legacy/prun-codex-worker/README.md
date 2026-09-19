# prun's Codex worker, retired 2026-09-18

These three scripts ran a `prun` unit on a Codex worker. They are kept here, out of the skill tree, because the reason they stopped being used is a price, and a price can change back.

| File | What it did |
|---|---|
| `dispatch-task.sh` | Ran `codex exec` on a unit prompt from a per-unit working directory, Bash variant. Generalized from `skills/implement-review/scripts/dispatch-codex.sh`. |
| `dispatch-task.ps1` | The PowerShell twin. It launches a hidden worker through a `cmd` helper and spawns the watcher below. |
| `reap-watch.ps1` | The idle-stall and hard-timeout watcher that `dispatch-task.ps1` spawns. Polling and process-tree termination live apart from worker launch because a single `.ps1` doing all three trips some Windows antivirus AMSI heuristics and is blocked at parse, which both scripts document at `dispatch-task.ps1:170` and `reap-watch.ps1:9`. The Bash variant does the same work inline. |

## Why they are here

`prun` routed units to Codex while that was the cheaper pool. On 2026-09-13 it moved to Agy workers through `skills/prun/scripts/dispatch-task-agy.py`, which run on the separate Google AI pool and do not bill the session's own account. The audit of 60 days of transcripts counted 656 runs of these scripts before that date and none after it.

Nothing routes to them now, and no script, test, or document calls them. Moving them out of `skills/prun/scripts/` takes them out of what `bootstrap` ships to every consumer. That is the point. A file in the skill tree is a file someone can reach for by accident.

They are kept rather than deleted because the choice that retired them was a pricing one. The archive preserves a working implementation for reuse if Codex workers become the cheaper pool again.

## Bringing them back

Reactivating Codex is more than restoring three files. Current routing excludes it in several places, and each of them has to agree.

1. Restore the three scripts under `skills/prun/scripts/` in both `agent-config` and `anywhere-agents`, and copy them explicitly into the wheel mirror at `packages/pypi/anywhere_agents/composer/skills/prun/scripts/`. That mirror is a committed tree, nothing copies into it automatically, and `check-parity.sh` fails until it matches.
2. Recover the Codex-specific contract tests from `<archive-commit>^:tests/test_dispatch_task.py`. Leave the monitor and gather tests where they are now, in `tests/test_prun_deployed_path.py`, so they are not duplicated. Verify the restored scripts against whatever Codex CLI is current, because that contract has moved since.
3. Register the recovered test file in `strict_test_files` in `scripts/check-parity.sh` in both repositories, and in `STRICT_MEMBERSHIP_FLOOR` in `tests/test_check_parity.py` in `agent-config` only. The file of that name in `anywhere-agents` is a different test with no such registry.
4. State the restored executor policy consistently. Five places say Agy today. Three sit in the skill: `skills/prun/SKILL.md`, `.claude/commands/prun.md`, and `skills/prun/agents/openai.yaml`. The other two are the rendered `docs/skills/prun.md` in `anywhere-agents` and the assignment assertions in `tests/test_prun_executors.py`. Copy the updated skill definition, command pointer, and OpenAI wrapper into the wheel mirror under `packages/pypi/anywhere_agents/composer/` as well. Otherwise the wheel keeps shipping the Agy-only policy and parity fails. Then run the recovered contracts, the retained prun tests, and cross-repository and wheel parity.

## What does not depend on them

Recovering an old unit's state does not depend on these scripts. The `report-state` and `snapshot-tail` launchers call `skills/prun/scripts/prun_state.py` directly, and that module holds the recovery code these scripts were once described as carrying. A state directory written by a Codex unit in August is still readable today with the retained launchers.

`monitor.sh` also still recognizes the FALLBACK header these scripts wrote, alongside the Agy dispatcher's own, so a result file from that era reads correctly.
