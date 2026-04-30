# Migrations

Two distinct one-shot migration types live in this file. Both are maintainer-only operational notes; neither applies to public consumers of `anywhere-agents`.

- **§ Bootstrap-cache seed refresh** (machine-level): when an upstream fix to `bootstrap/bootstrap.{sh,ps1}` cannot self-apply because each consumer's cached bootstrap is gitignored and machine-local. One dated entry per fix.
- **§ Consumer project: ac → aa upstream switch** (project-level): flip a single consumer project's `.agent-config/upstream` from `yzhao062/agent-config` to `yzhao062/anywhere-agents`. Most active maintainer projects switched during 2026-04; the section preserves operational mechanics for rare future flips, rollbacks, and submodule cases.

## Bootstrap-cache seed refresh

One-shot seed refreshes you need to run on each machine when a bootstrap-script fix lands that existing cached bootstraps cannot self-apply. The `.agent-config/bootstrap.{ps1,sh}` inside every consumer project is gitignored and machine-local, so fixes to the upstream bootstrap script do not propagate via `git pull`; each machine needs its own one-time refresh. After the seed refresh, the self-update tail in the new script keeps subsequent changes propagating automatically.

### 2026-04-17 — Bootstrap self-update

The shared `bootstrap.{ps1,sh}` scripts now end with a self-update step that rewrites the cached entrypoint from the sparse clone. Before this fix, a consumer's cached bootstrap was permanently frozen at whatever version was first downloaded. The sparse-checkout spec also now includes `bootstrap/`, without which the self-update source file does not exist in the sparse tree and the guard silently no-ops.

**Who needs to run this:** any machine where a consumer project was bootstrapped before 2026-04-17.

#### Detection

Check cached bootstrap line counts. Pre-fix values are `ps1 <= 85`, `sh <= 81`. Post-fix values are `ps1 = 96`, `sh = 89`. Anything below the post-fix line count needs a seed refresh.

Bash (macOS / Linux / Git Bash on Windows):

```bash
for d in ~/PycharmProjects/*/; do
  f="${d}.agent-config/bootstrap.sh"
  p="${d}.agent-config/bootstrap.ps1"
  [ -f "$f" ] || [ -f "$p" ] || continue
  s="-"; q="-"
  [ -f "$f" ] && s=$(wc -l < "$f")
  [ -f "$p" ] && q=$(wc -l < "$p")
  printf "%-30s sh=%s ps1=%s\n" "$(basename "$d")" "$s" "$q"
done
```

Adjust `~/PycharmProjects/*/` if the project root differs on that machine.

#### Seed-refresh command

The migration looks at each consumer's cached script, detects whether the upstream is `yzhao062/agent-config` or `yzhao062/anywhere-agents`, and overwrites the cache with the freshly-fetched matching upstream.

Bash (macOS / Linux / Git Bash on Windows):

```bash
mkdir -p /tmp/ac-migration
curl -sfL https://raw.githubusercontent.com/yzhao062/agent-config/main/bootstrap/bootstrap.sh   -o /tmp/ac-migration/ac.sh
curl -sfL https://raw.githubusercontent.com/yzhao062/agent-config/main/bootstrap/bootstrap.ps1  -o /tmp/ac-migration/ac.ps1
curl -sfL https://raw.githubusercontent.com/yzhao062/anywhere-agents/main/bootstrap/bootstrap.sh  -o /tmp/ac-migration/aa.sh
curl -sfL https://raw.githubusercontent.com/yzhao062/anywhere-agents/main/bootstrap/bootstrap.ps1 -o /tmp/ac-migration/aa.ps1

for d in ~/PycharmProjects/*/; do
  dir="${d}.agent-config"
  for ext in sh ps1; do
    f="${dir}/bootstrap.${ext}"
    [ -f "$f" ] || continue
    if grep -q 'yzhao062/anywhere-agents' "$f"; then
      cp "/tmp/ac-migration/aa.${ext}" "$f"
    else
      cp "/tmp/ac-migration/ac.${ext}" "$f"
    fi
    echo "  updated ${f}"
  done
done
```

PowerShell (Windows, if Bash is not preferred):

```powershell
iwr -UseBasicParsing -Uri https://raw.githubusercontent.com/yzhao062/agent-config/main/bootstrap/bootstrap.ps1  -OutFile $env:TEMP/ac.ps1
iwr -UseBasicParsing -Uri https://raw.githubusercontent.com/yzhao062/anywhere-agents/main/bootstrap/bootstrap.ps1 -OutFile $env:TEMP/aa.ps1
foreach ($d in Get-ChildItem "$env:USERPROFILE\PycharmProjects" -Directory) {
  $f = Join-Path $d.FullName '.agent-config\bootstrap.ps1'
  if (-not (Test-Path $f)) { continue }
  $src = if ((Get-Content $f -Raw) -match 'yzhao062/anywhere-agents') { "$env:TEMP/aa.ps1" } else { "$env:TEMP/ac.ps1" }
  Copy-Item $src $f -Force
  Write-Host "  updated $f"
}
```

#### After refresh

Next Claude Code or Codex session in each consumer project:

1. SessionStart hook runs the now-latest cached bootstrap.
2. Sparse clone pulls the latest `.agent-config/repo/bootstrap/`.
3. The self-update tail copies the sparse version over the cache.
4. From here forward, any future bootstrap improvement arrives automatically on the next session; no further machine-by-machine migrations required for bootstrap-script changes.

## Consumer project: ac → aa upstream switch

Most active maintainer projects switched during 2026-04. This section preserves the mechanics for rare future flips (new projects that should bootstrap from aa, rollback, submodule cases), not for active migration work.

The switch is a one-line change to `.agent-config/upstream`. Bootstrap is idempotent and self-healing on the next run: it refetches `AGENTS.md` from the new upstream, re-sparse-clones the matching `skills/` tree, regenerates `CLAUDE.md` and `agents/codex.md`, and merges shared keys into project `.claude/settings.json`. `~/.claude/hooks/guard.py` and `session_bootstrap.py` are byte-identical between ac and aa per STRICT parity, so the switch does not change hook behavior. `AGENTS.local.md` and `.claude/settings.local.json` are never touched.

### Before switching

For an existing ac-bootstrapped project, do these quick checks before changing `.agent-config/upstream`:

1. Move any direct edits in `AGENTS.md`, `CLAUDE.md`, or `agents/codex.md` into the matching `.local.md` file, because bootstrap rewrites the generated files.
2. Check `.claude/commands/` for pointers to ac-only skills (`bibref-filler`, `dual-pass-workflow`, `figure-prompt-builder`, or any `reference-skills/` entry). Either keep the project on ac, or copy the needed skill into repo-local `skills/<name>/`.
3. Confirm the aa skill set (`implement-review`, `my-router`, `ci-mockup-figure`, `readme-polish`) plus repo-local `skills/` covers any router expectations the project encodes.
4. Run the project's pre-push smoke check if it has one.

### Path 1: Change upstream (recommended)

Bash (macOS / Linux / Git Bash):

```bash
# From the consumer project root
echo 'yzhao062/anywhere-agents' > .agent-config/upstream
bash .agent-config/bootstrap.sh
```

PowerShell (Windows):

```powershell
# From the consumer project root
Set-Content -Path .agent-config/upstream -Value 'yzhao062/anywhere-agents' -NoNewline
& .\.agent-config\bootstrap.ps1
```

That is the full migration. Bootstrap on the next run picks up the new upstream and redeploys the matching shared content.

### Path 2: Nuke and reinstall (only when Path 1 misbehaves)

Use this when `.agent-config/` is corrupted or when you want a verified-clean state.

**Precondition (aa v0.4.0+)**: if `.agent-config/pack-state.json` exists, run `anywhere-agents uninstall --all` before deleting `.agent-config/`. Skipping leaves user-level pack-owned hooks (`~/.claude/hooks/<pack>/`) and permission entries orphaned in `~/.claude/settings.json`; future installs at the same target path fail closed with `user-level-output-conflict` until you manually clean `~/.claude/pack-state.json`.

```bash
# From the consumer project root
if [ -f .agent-config/pack-state.json ]; then
  if ! anywhere-agents uninstall --all; then
    echo "anywhere-agents uninstall --all failed; aborting Path 2 cleanup." >&2
    exit 1
  fi
fi

# DANGER: deletes local cache and generated per-agent files.
# Confirm AGENTS.local.md is committed and any direct edits to AGENTS.md are
# already migrated to AGENTS.local.md. Bootstrap regenerates AGENTS.md and
# the CLAUDE.md / agents/codex.md files from upstream; anything unique in
# them that is not in .local.md will be lost.
rm -rf .agent-config AGENTS.md CLAUDE.md agents/codex.md
mkdir -p .agent-config
curl -sfL https://raw.githubusercontent.com/yzhao062/anywhere-agents/main/bootstrap/bootstrap.sh -o .agent-config/bootstrap.sh
bash .agent-config/bootstrap.sh
```

### Verification

Immediately after the first post-switch bootstrap run:

```bash
cat .agent-config/upstream
# expected: yzhao062/anywhere-agents

grep -c 'rule-pack:agent-style:begin' AGENTS.md
# expected: 1   (aa v0.3.0+ default-on rule-pack composition)

ls .agent-config/repo/skills/
# expected: ci-mockup-figure implement-review my-router readme-polish
# (exactly four entries)

ls .claude/commands/
# expected shared aa pointers: ci-mockup-figure.md implement-review.md my-router.md readme-polish.md
# Any extra file is either project-local or a STALE ac-only pointer
# (bibref-filler.md, dual-pass-workflow.md, figure-prompt-builder.md, plus
# any reference-skill pointer the project previously enabled). Bootstrap
# does NOT delete stale pointers; remove them manually unless the project
# has copied the matching skill into repo-local skills/<name>/.

ls -1 AGENTS.local.md .claude/settings.local.json 2>/dev/null
# your local overrides must still be present
```

If any of these diverges from expected, roll back and investigate (most likely cause: Path 1 ran from the wrong cwd, or the project has a stale `.agent-config/` cache; try Path 2 in that case).

### Rollback

Fully reversible. Point upstream back at ac:

```bash
echo 'yzhao062/agent-config' > .agent-config/upstream
bash .agent-config/bootstrap.sh
```

PowerShell:

```powershell
Set-Content -Path .agent-config/upstream -Value 'yzhao062/agent-config' -NoNewline
& .\.agent-config\bootstrap.ps1
```

The round-trip is free. The rule-pack block in `AGENTS.md` disappears on the next ac bootstrap because ac does not ship the rule-pack composer today.

### Opting out of the default `agent-style` rule pack

If a specific project should NOT carry the agent-style writing rules (e.g., a code-only repo with no prose, a repo for a co-author who dislikes the ruleset), add an explicit opt-out at project root:

```yaml
# agent-config.yaml (tracked, at consumer project root)
rule_packs: []
```

Commit `agent-config.yaml`. Bootstrap on every subsequent run respects the opt-out and writes upstream `AGENTS.md` verbatim without the rule-pack block.

### What ac keeps long-term

ac's footprint shrinks to maintainer-only content: `reference-skills/`, USC / Overleaf-specific AGENTS.md sections, the core narrative docs (`vision.md`, `pack-architecture.md`, `anywhere-agents.md`), private runbooks and planning scratch files, and `archive/`. ac's `bootstrap.{sh,ps1}` stays operational indefinitely so paper / proposal / submodule projects can keep bootstrapping from ac.

No scheduled end-of-life for ac. Retirement is about shrinking the public-facing role, not about shutting ac down.

### Submodule note

Bootstrap does not recursively walk submodules. Each submodule has its own `.agent-config/upstream`; flipping the outer project's upstream does NOT auto-flip a submodule. For co-authored paper submodules, leave on ac unless the co-PI has agreed to the switch.

### FAQ (selected)

**Does switching lose Claude Code memory or project history?** No. `~/.claude/projects/<project-slug>/memory/` is per-Claude-Code-project state, decoupled from bootstrap upstream.

**Does `~/.claude/hooks/` change on switch?** No. `guard.py` and `session_bootstrap.py` are byte-identical between ac and aa (STRICT parity guarantee).

**Can a project pull some skills from ac and some from aa?** Not via bootstrap upstream (single URL). Workarounds: (a) copy the specific ac-only skill into the project's own repo-local `skills/<name>/` (repo-local wins over shared on name conflict); (b) stay on ac for the whole project. The long-term replacement is `packs:` opt-in (public or private source); see `../pack-architecture.md`.
