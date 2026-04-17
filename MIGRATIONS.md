# Migrations

One-shot seed refreshes you need to run on each machine when a bootstrap-script fix lands that existing cached bootstraps cannot self-apply. The `.agent-config/bootstrap.{ps1,sh}` inside every consumer project is gitignored and machine-local, so fixes to the upstream bootstrap script do not propagate via `git pull`; each machine needs its own one-time refresh. After the seed refresh, the self-update tail in the new script keeps subsequent changes propagating automatically.

## 2026-04-17 — Bootstrap self-update

The shared `bootstrap.{ps1,sh}` scripts now end with a self-update step that rewrites the cached entrypoint from the sparse clone. Before this fix, a consumer's cached bootstrap was permanently frozen at whatever version was first downloaded. The sparse-checkout spec also now includes `bootstrap/`, without which the self-update source file does not exist in the sparse tree and the guard silently no-ops.

**Who needs to run this:** any machine where a consumer project was bootstrapped before 2026-04-17.

### Detection

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

### Seed-refresh command

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

### After refresh

Next Claude Code or Codex session in each consumer project:

1. SessionStart hook runs the now-latest cached bootstrap.
2. Sparse clone pulls the latest `.agent-config/repo/bootstrap/`.
3. The self-update tail copies the sparse version over the cache.
4. From here forward, any future bootstrap improvement arrives automatically on the next session; no further machine-by-machine migrations required for bootstrap-script changes.
