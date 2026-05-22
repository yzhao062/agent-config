# Smart approval-reduction guard — plan (2026-05-21)

Status: implemented (Phase 1 landed; execution-review applied). Target repos: `agent-config` (source) + `anywhere-agents` (public mirror).

## Implementation note (as-built, supersedes the Phase 1 / config text below)

Phase 1 shipped **without** the `command_wrappers` config loader. Per the maintainer's call, custom/private wrappers (a personal job-runner such as `psc.py run "..."`) are treated as **opaque**, exactly like `python -c`: only the built-in command-carrying wrappers (`ssh`, `bash -c`, `sh -c`, `zsh -c`, `docker exec`/`run`, `pwsh`/`powershell -Command`) are pierced. There is no `~/.claude/guard-config.json`, no `ask_classes` / `command_wrappers` / `trust_wrappers`, and no bootstrap config deploy. The config-tunability design below (`Target design` item 4 and the `command_wrappers` mentions in Phasing) is **deferred** to a future opt-in and is kept here only as the design record. Everything else matches the implementation.

### Wrapper-coverage boundary (as-built, after code-review rounds 2-4)

Four code-review rounds hardened the wrapper/prefix coverage against realistic agent-emitted forms. The closed-form coverage is:

- **Transparent prefix runners** (stripped by `strip_wrappers`, path-qualified via `_basename`): `sudo`, `doas`, `env`, `command`, `nohup`, `setsid`, plus inline `VAR=VALUE`.
- **Command-carrying wrappers** (pierced + recursed by `_wrapper_payload`, depth ≤ `MAX_WRAPPER_DEPTH`): `bash`/`sh`/`zsh`/`dash`/`ash -c`, `pwsh`/`powershell -Command` (joins all trailing tokens; encoded `-EncodedCommand` fails closed to ASK), `ssh`, `docker exec`/`run` (common run/exec value flags enumerated), Windows `cmd /c`/`cmd /k`, `timeout DURATION CMD`, and `xargs` (typically behind a pipe).
- **Publish interpreters**: `npm`/`pnpm`/`yarn`, `twine`, and `py` / versioned `python\d*(?:\.\d+)*` for the `-m twine upload` module form.

**Explicit non-goal boundary** (documented limits, NOT blockers, consistent with the obfuscation non-goal): low-frequency transparent prefixes `nice`, `ionice`, `stdbuf`, `time` are not stripped; deliberate obfuscation (base64 — PowerShell already fails closed, `$(...)`/backtick substitution, here-docs, `$VAR` indirection, unicode/IFS tricks, shell line-continuation, aliases/functions) is out of scope; and custom/private wrappers stay opaque. These can be added later if a real form is observed in practice, but the threat model (the user's own non-adversarial agent) does not justify enumerating them now.

## Purpose

Reduce approval prompts to the few that carry real signal. Today the native Claude Code permission layer prompts on every command not covered by an allow rule. On Windows, `PowerShell(*)` is not allowed, so every PowerShell command prompts. The result is alarm fatigue: the user rubber-stamps everything, and a genuinely dangerous command (for example `rm -rf` on a cluster path) gets the same reflexive "yes" as a read-only poll. The approval mechanism then protects nothing while costing maximum friction.

Goal: mechanical guard rules (ask/deny) fire ONLY for the most dangerous actions. Everything else flows silently. The human's attention is reserved for the small set that actually warrants it.

## Principle

Prompt only when an action is (1) outward-facing (publishes or changes shared/external state) or (2) hard to reverse (destroys data or rewrites history). Classify by what the command does, not by which tool ran it or whether it matched a coarse pattern. See through command-carrying wrappers so a dangerous payload is caught wherever it lives.

## Non-goals

- Not a security sandbox and not a defense against a malicious agent. The agent is the user's own; this raises the signal of the approval prompt, it is not a trust boundary. The risk it actually guards against is an honest mistake (a wrong path in `rm -rf`, an accidental `git push --force`, an unintended `npm publish`), not a deliberate attempt to slip a command past the classifier. This is why the classifier catches realistic command shapes but treats deliberate obfuscation as an accepted non-goal: a destructive command reaches the prompt by accident, never by evasion.
- Not a change to the writing-style, banner, or compound-cd gates.
- Not psc-specific. The PSC examples were illustrations; `psc.py` is declared in user config, never in shipped code.
- Not removing human approval for the dangerous set. The point is to keep that approval and make it meaningful.

## Current state

`guard.py` `main()`: Check 0 auto-allow impl-review PS scripts, then writing-style deny, then banner deny, then an early-return for any tool that is not Bash, then compound-cd deny (Bash), then git destructive ask (Bash), then gh destructive ask (Bash). Settings allow is `Bash(*)` plus three PowerShell auto-watch patterns; ask is `Bash(git ...)`, `Bash(rm -rf ...)`, etc. (Bash-only, pattern-based, blind to wrapper payloads.)

Three gaps: (a) the destructive ask gate never runs for the PowerShell tool; (b) a native PowerShell delete (`Remove-Item -Recurse -Force`, or aliases `rm` / `del` / `rd` / `rmdir`) is not classified at all, so once `PowerShell(*)` is allowed it would pass silently; (c) destructive commands hidden inside a wrapper payload (`ssh host "..."`, `bash -c "..."`, container exec, a user-declared `psc.py run "..."`) are invisible because only the leading token of the outer command is inspected.

## Target design

1. Settings: add `PowerShell(*)` to allow, mirroring `Bash(*)`. The native layer becomes allow-by-default; the hook is the sole risk arbiter. This change ships only together with the PowerShell file-destruction classifier in item 3, never before it (otherwise it opens a silent-delete gap).
2. `guard.py`: a `classify(cmd, depth=0) -> ALLOW | ASK | DENY` step that
   - splits the command into sub-commands at unquoted shell operators. Use `_quote_aware_split_on_operators` for POSIX-shaped text; use a separate PowerShell-aware splitter and a native-verb table for PowerShell-shaped text (do not apply POSIX parsing to PowerShell).
   - for each sub-command, strips non-semantic prefixes and wrapper flags;
   - if the leading token is a known shell-command wrapper (`ssh`, `bash -c`, `sh -c`, `zsh -c`, `pwsh -Command`, `powershell -Command`, `docker exec`, plus user-configured wrappers), extracts the inner command and recurses up to `MAX_WRAPPER_DEPTH = 3`; if depth is exceeded, falls back to ASK for any wrapper known to carry a command payload;
   - classifies each terminal sub-command by exact leading token and exact subcommand rules; any mandatory ASK hit makes the whole command ASK.
   - `python -c` is NOT a shell-command wrapper. It carries Python source, not shell, so it is treated as opaque (a documented false-negative consistent with the non-goals). A targeted scanner for literal `os.system(...)` / `subprocess.*(shell=True)` strings is parked for later if it becomes real user pain.
   - The classifier runs for Bash AND PowerShell. Compound-cd stays a Bash-only deny.
3. Dangerous set (the only things that ASK by default):
   - mandatory git safety: `git push` (including force), `git commit`, `git merge`, `git rebase`, `git reset --hard`, `git clean -f`, `git branch -d|-D|--delete`, `git checkout --`, `git stash drop|clear`, `git tag -d|--delete`.
   - mandatory publish / shared-state changes: `gh pr create|merge|close`, `gh repo delete`, `gh release create|delete|upload|edit`, `npm publish`, `npm unpublish`, `twine upload`, `python -m twine upload`, with room to add other package-publish verbs by exact command family.
   - file/device destruction: Bash/POSIX `rm -rf` / `rm -fr` / `rm -r -f`, `dd`, `mkfs`, `shred`; PowerShell `Remove-Item` and aliases `rm` / `del` / `erase` / `rd` / `rmdir` when recursive deletion is requested (`-Recurse`, `/s`, or equivalent).
4. Config-driven tolerance: `guard.py` reads `~/.claude/guard-config.json` on each call (no restart):
   - `ask_classes`: may relax ONLY non-policy classes (currently just `fs_destructive`). The mandatory `git_safety` and `publish` classes are always ASK and cannot be disabled by config, env, or wrapper trust.
   - `command_wrappers`: extra shell-command wrappers to pierce. This is where `psc.py run` is declared, in the user's local config, not in shipped code. The fail-closed, declare-only loader for this lands in Phase 1 (so `PowerShell(*)` never ships with a known wrapper family left as a silent path); `ask_classes` and `trust_wrappers` land in Phase 2.
   - `trust_wrappers`: skips only non-policy classes, and only after classification finds no mandatory `git_safety` or `publish` hit. It can never suppress git commit/push, destructive git-history operations, gh PR/repo/release actions, or package publish/upload.
   - Missing, malformed, or schema-invalid config falls back to baked-in conservative defaults; unknown class names are ignored with defaults preserved.

## Phasing

- Phase 1 (minimum safe relief, single branch, ships together): settings `PowerShell(*)`; tool-agnostic mandatory git/gh/publish ASK; direct file-destruction ASK for BOTH Bash and PowerShell; bounded wrapper recursion (depth 3); and a minimal fail-closed `command_wrappers` config subset for extra shell-command wrappers. This subset only declares wrapper shapes to pierce. It does not relax any class and does not add `trust_wrappers`. Outcome: routine PowerShell (poll, `echo`, `hostname`, job launch) flows in any shell; direct dangerous commands and dangerous payloads inside built-in or declared command wrappers ask. Native PowerShell deletes are caught here, not deferred.
- Phase 2 (tunability, parity-clean tolerance controls): finish the `guard-config.json` schema with non-policy-only `ask_classes` relaxation and `trust_wrappers`. Mandatory `git_safety` and `publish` remain non-disableable. Personal wrapper names such as `psc.py` stay in the maintainer's local config, not shipped code.
- Phase 3 (stretch): learn the user's tolerance from transcript history and propose allow-list additions. Reuses the existing `fewer-permission-prompts` skill. Deferred because the PreToolUse hook never sees the user's eventual yes/no, so the learning signal must come from post-hoc transcript scanning, not the hook.

## Risk and regression analysis

- False negatives: obfuscated payloads (base64, `$VAR` indirection, here-docs), and `python -c` Python source, escape a token scan. Documented limit, consistent with the non-goals.
- False positives: classification keys on the exact leading token of each sub-command, not a substring scan, so `echo "rm -rf"`, `grep "git push"`, and PowerShell `Write-Output "Remove-Item -Recurse -Force"` stay safe, and existing guards like `git merge-base` / `git commit-tree` / `git commit-graph` keep passing. Wrapper recursion classifies each inner payload's leading token the same way.
- PowerShell parsing: PowerShell uses a different statement grammar and native verbs (`Remove-Item`) plus aliases. The plan adds a PowerShell-specific splitter and verb table rather than reusing the POSIX splitter, so PowerShell deletes are classified directly.
- shlex on Windows backslash paths: posix-mode split can mangle backslashes, but the dangerous verbs (`git`, `rm`) sit before any path, so detection still fires; worst case is a missed exotic form, never a destructive-op false pass on the common shapes.
- Config fail-safe: absent or broken config falls back to defaults; config can never relax the mandatory classes.
- Parity: `guard.py` is STRICT byte-identical with `anywhere-agents`; `user/settings.json` is BY-DESIGN. The change mirrors to aa and must keep `check-parity.sh` green; tests run on both.

## Validation

- Extend `tests/test_guard.py`:
  - tool-agnostic mandatory ASK: git/gh/publish ask on both Bash and PowerShell tools.
  - file destruction: Bash `rm -rf` and PowerShell `Remove-Item -Recurse -Force` (and recursive aliases) ask; non-recursive `Remove-Item file.txt` follows the chosen default.
  - publish: `npm publish`, `twine upload`, `python -m twine upload`, `gh release create` ask.
  - wrapper recursion: `ssh host "rm -rf ..."`, `ssh host "bash -c 'git push'"`, `docker exec c bash -lc "rm -rf /tmp/x"` ask; `ssh host "echo ok"` passes; depth-exceeded known wrapper asks.
  - declared command_wrappers (Phase 1 loader): a declared wrapper (for example `psc.py run`) pierces its payload so `psc.py run "rm -rf ..."` asks; a malformed or schema-invalid wrapper spec is fail-closed (ignored, built-in wrappers and defaults preserved, no crash).
  - config invariants: `ask_classes` cannot disable `git_safety` or `publish`; `trust_wrappers` cannot hide a mandatory hit; malformed config preserves defaults; relaxing `fs_destructive` works.
  - false-positive guards (must stay green): `echo "rm -rf"`, `grep "git push"`, PowerShell `Write-Output "Remove-Item -Recurse -Force"`, `git merge-base`, `git commit-tree`, `git commit-graph`.
- Keep every current Bash ask/deny/pass test green.
- Full suite: `python -B -m unittest discover -s tests -p "test_*.py"`.
- Replay the screenshot commands: `run "echo CONNECT_OK; hostname"` passes; `run "...rm -rf..."` asks once `psc.py` is declared in `command_wrappers`.

## Resolved open questions

1. `git commit` stays in ASK. The standing Git Safety rule in AGENTS.md names it directly, so it remains non-disableable.
2. Publish verbs (`npm publish`, `twine upload`, `gh release create`) are in scope now, since this repo ships npm + PyPI + GitHub releases on every cut. They join the mandatory `publish` class.
3. The mandatory safety core (git/publish/file-destruction, both shells, bounded recursion) ships as one branch (Phase 1). Config tunability is Phase 2; transcript learning is Phase 3.
4. Wrapper recursion is bounded at depth 3, with ASK-on-exceed for known command-carrying wrappers.
5. The `publish` class is non-disableable, like `git_safety`. Publishing is outward-facing and hard to reverse (a released version cannot be cleanly withdrawn), so it stays mandatory ASK and cannot be relaxed by config, env, or wrapper trust.
6. The `command_wrappers` declare-only loader lands in Phase 1; only `ask_classes` relaxation and `trust_wrappers` are deferred to Phase 2.

## Scope justification

- Smaller scope (settings `PowerShell(*)` plus tool-agnostic git only) is unsafe: it opens a native-PowerShell silent-delete gap (review finding H2). The file-destruction classifier is not optional next to `PowerShell(*)`.
- Larger scope (transcript learning) needs observability the hook does not have; correctly deferred to Phase 3.
- This scope closes both halves of the user's ask, stop the noise AND keep the dangerous set caught regardless of shell or wrapper, in one safe branch, with config tunability as the piece that makes it general rather than personal.
