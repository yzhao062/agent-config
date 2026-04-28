# anywhere-agents quickstart

Maintainer-internal cheat sheet for installing `anywhere-agents` and operating it on consumer projects. Not a public-facing user guide; commands assume Windows + Miniforge py312 (the Ubuntu Spark workstation uses the POSIX equivalents).

**Minimum recommended version: v0.5.6.** Earlier v0.5.x releases shipped composer fixes that the wheel CLI did not actually deliver to projects bootstrapped against an older clone. v0.5.6 bundles the composer into the wheel; a `pipx install --force` from v0.5.6+ delivers composer fixes without a re-bootstrap. See `docs/pack-architecture.md` § "aa v0.5.1 → v0.5.6 — operational hardening".

## Install or upgrade

```bash
pipx install anywhere-agents==0.5.6 --force      # or any later version
anywhere-agents --version                         # expect 0.5.6 or later
```

If `pipx` is not available, install it first via `pip install pipx; pipx ensurepath`. Do not mix `pip install anywhere-agents` with `pipx install anywhere-agents`; they conflict at command-resolution time.

For the npm distribution (rarely needed in this environment): `npm i -g anywhere-agents`.

## New project (greenfield)

```bash
cd C:/Users/yuezh/PycharmProjects/<new-project>
anywhere-agents                                   # one-shot: clones .agent-config/repo, deploys bundled defaults, reconciles user-level packs
anywhere-agents pack verify                       # post-check: all rows should show ✅ deployed
```

`anywhere-agents` (no args) is the bootstrap entry point. It fetches `bootstrap.ps1` (or `bootstrap.sh`) from the public repo, clones the source tree into `.agent-config/repo/`, deploys the two bundled defaults (`agent-style`, `aa-core-skills`), and reconciles any user-level packs declared at `%APPDATA%\anywhere-agents\config.yaml` (Windows) or `~/.config/anywhere-agents/config.yaml` (POSIX).

If user-level config declares `acad-skills`, `paper-workflow`, and `profile`, expect five rows in the post-check; otherwise expect two.

## Existing project (already has `.agent-config/repo/`)

```bash
cd C:/Users/yuezh/PycharmProjects/<existing-project>
cp .agent-config/pack-lock.json .agent-config/pack-lock.json.bak    # safety
anywhere-agents pack verify                       # see current state
anywhere-agents pack verify --fix                 # apply
anywhere-agents pack verify                       # confirm all ✅
```

`pack verify --fix` invokes the wheel-bundled composer (v0.5.6+), which:

1. Reads user-level config and merges bundled defaults (`force_defaults=True` resolver).
2. Writes any missing user-level entries to `agent-config.yaml`.
3. Re-composes pack content into project outputs (`AGENTS.md`, `.claude/...`) and writes composer state under `.agent-config/`.
4. Updates `.agent-config/pack-lock.json` to record the resolved state.

The composer is idempotent. Re-running on a clean state is a no-op.

## Add a third-party pack

```bash
anywhere-agents pack add https://github.com/<owner>/<repo> --ref <tag-or-branch>
```

Defaults: `--type skill`. Add `--type rule` for passive rule packs (the `agent-style` family). Add `--name <pack-name>` to disambiguate when a remote repo declares multiple packs and only one is wanted.

Inside a bootstrapped project, `pack add` is one-shot: it writes the user-level config, mirrors the selection into `agent-config.yaml`, invokes the package-owned composer, and deploys immediately. Outside a bootstrapped project it registers globally only; run `anywhere-agents` or `anywhere-agents pack verify --fix` later inside a project to deploy.

To remove: `anywhere-agents pack remove <name>`. Bundled defaults (`agent-style`, `aa-core-skills`) emit a notice if removed; the next `pack verify --fix` re-merges them via `force_defaults`.

## Verify state

```bash
anywhere-agents pack verify                       # status table for all 5 packs (or 2 + N user packs)
(Get-Content .agent-config\pack-lock.json -Raw | ConvertFrom-Json).packs.PSObject.Properties.Name  # PowerShell: list locked pack names
```

Expected post-fix state on a maintainer project with the standard user-level config:

| Pack | Source | Status |
|---|---|---|
| `aa-core-skills` | `bundled` (wheel-shipped) | ✅ deployed (bundled default) |
| `agent-style` | `https://github.com/yzhao062/agent-style @ v0.3.2` | ✅ deployed (bundled default) |
| `acad-skills` | `https://github.com/yzhao062/agent-pack @ main` | ✅ deployed |
| `paper-workflow` | `https://github.com/yzhao062/agent-pack @ main` | ✅ deployed |
| `profile` | `https://github.com/yzhao062/agent-pack @ main` | ✅ deployed |

`pack verify` exits 0 when every row is `✅ deployed`. Any other state exits non-zero so it can gate downstream automation.

## Recover from a broken state

```bash
# Composer subprocess error or stale cache:
rm -rf "$env:LOCALAPPDATA/anywhere-agents/cache"   # PowerShell
anywhere-agents pack verify --fix                  # cold fetch rebuilds the cache

# Lock entry count below expectation:
anywhere-agents --version                          # confirm 0.5.6 or later
type .agent-config\pack-lock.json                  # capture state before any further command

# Bootstrap clone is stale (`.agent-config/repo/` predates the latest release):
anywhere-agents                                    # re-runs bootstrap; refreshes .agent-config/repo/ and re-composes
```

Avoid `anywhere-agents pack verify --fix` in a retry loop on a broken state. The composer is deterministic; a second run on the same input produces the same output. If the lock count is wrong on the first run after upgrade, capture state and read `docs/pack-architecture.md` § "Regression and failure analysis" before re-running.

## Common gotchas

- **`pipx run anywhere-agents` warns "already on PATH".** Cosmetic; the command runs anyway.
- **`anywhere-agents` (no args) fails with `getaddrinfo failed`.** DNS / network issue on the local machine; not a tool bug. Retry, or use `& .\.agent-config\bootstrap.ps1` if `.agent-config/repo/` already exists.
- **`pack verify` shows `agent-style ✅ deployed (bundled default)` with a remote URL source.** Expected. `agent-style` is a bundled default that fetches its content from the `agent-style` upstream repo. `aa-core-skills` is the only true wheel-resident bundled default.
- **`pack verify` after `pack remove agent-style` still shows it.** Expected. `force_defaults=True` re-merges bundled defaults regardless of user-config presence; the next `pack verify --fix` re-deploys the content.
