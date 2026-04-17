# Let .gitattributes handle line endings; silence CRLF warnings on Windows

param([string]$Upstream)

# Upstream cascade: argv > env var > persisted file > hardcoded default.
# Forkers can persist a different default in their fork; consumers can pass
# upstream via `.\.agent-config\bootstrap.ps1 <user>/<repo>` or the
# $env:AGENT_CONFIG_UPSTREAM environment variable.
if (-not $Upstream) { $Upstream = $env:AGENT_CONFIG_UPSTREAM }
if (-not $Upstream -and (Test-Path .agent-config/upstream)) {
  $Upstream = (Get-Content .agent-config/upstream -Raw).Trim()
}
if (-not $Upstream) { $Upstream = 'yzhao062/agent-config' }
New-Item -ItemType Directory -Force -Path .agent-config | Out-Null
Set-Content -Path .agent-config/upstream -Value $Upstream -NoNewline

git config --global core.autocrlf false

function Merge-Json($base, $over) {
  foreach ($p in $over.PSObject.Properties) {
    $b = $base.PSObject.Properties[$p.Name]
    if ($b -and $b.Value -is [PSCustomObject] -and $p.Value -is [PSCustomObject]) {
      Merge-Json $b.Value $p.Value
    } elseif ($b -and $b.Value -is [Array] -and $p.Value -is [Array]) {
      # Arrays of objects (e.g., hooks): replace. Arrays of strings: dedup.
      $hasObj = $false; foreach ($el in $p.Value) { if ($el -is [PSCustomObject]) { $hasObj = $true; break } }
      if ($hasObj) {
        $base | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value -Force
      } else {
        $s = [System.Collections.Generic.HashSet[string]]::new()
        $m = @(); foreach ($i in $b.Value) { if ($s.Add($i)) { $m += $i } }
        foreach ($i in $p.Value) { if ($s.Add($i)) { $m += $i } }
        $base | Add-Member -NotePropertyName $p.Name -NotePropertyValue $m -Force
      }
    } else {
      $base | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value -Force
    }
  }
}
New-Item -ItemType Directory -Force -Path .agent-config, .claude, .claude/commands | Out-Null
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/$Upstream/main/AGENTS.md" -OutFile .agent-config/AGENTS.md
Copy-Item .agent-config/AGENTS.md AGENTS.md -Force
$RepoUrl = "https://github.com/$Upstream.git"
if (Test-Path .agent-config/repo/.git) {
  git -C .agent-config/repo remote set-url origin $RepoUrl
  git -C .agent-config/repo pull --ff-only
} else {
  git clone --depth 1 --filter=blob:none --sparse $RepoUrl .agent-config/repo
}
git -C .agent-config/repo sparse-checkout set skills .claude scripts user bootstrap
# Generate per-agent config files (CLAUDE.md, agents/codex.md) from AGENTS.md.
# Generator preserves hand-authored files (no GENERATED header) and warns loudly.
if (Test-Path .agent-config/repo/scripts/generate_agent_configs.py) {
  $genPy = Get-Command python -ErrorAction SilentlyContinue
  if (-not $genPy) { $genPy = Get-Command python3 -ErrorAction SilentlyContinue }
  if ($genPy) {
    & $genPy.Path .agent-config/repo/scripts/generate_agent_configs.py --root . --quiet
  }
}
if (Test-Path .agent-config/repo/.claude/commands) {
  Copy-Item .agent-config/repo/.claude/commands/*.md .claude/commands/ -Force
}
if (Test-Path .agent-config/repo/.claude/settings.json) {
  if (Test-Path .claude/settings.json) {
    $shared = Get-Content .agent-config/repo/.claude/settings.json -Raw | ConvertFrom-Json
    $project = Get-Content .claude/settings.json -Raw | ConvertFrom-Json
    Merge-Json $project $shared
    $project | ConvertTo-Json -Depth 10 | Set-Content .claude/settings.json
  } else {
    Copy-Item .agent-config/repo/.claude/settings.json .claude/settings.json -Force
  }
}
# --- User-level setup: hooks and settings ---
# This section modifies ~/.claude/ (user-level, not project-level).
# It deploys a PreToolUse hook guard and merges shared permission settings.
# Remove this section if you do not want bootstrap to modify user-level config.
$userClaude = Join-Path $env:USERPROFILE '.claude'
if (Test-Path .agent-config/repo/scripts/guard.py) {
  $hooksDir = Join-Path $userClaude 'hooks'
  New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null
  Copy-Item .agent-config/repo/scripts/guard.py (Join-Path $hooksDir 'guard.py') -Force
}
if (Test-Path .agent-config/repo/scripts/session_bootstrap.py) {
  $hooksDir = Join-Path $userClaude 'hooks'
  New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null
  Copy-Item .agent-config/repo/scripts/session_bootstrap.py (Join-Path $hooksDir 'session_bootstrap.py') -Force
}
if (Test-Path .agent-config/repo/user/settings.json) {
  New-Item -ItemType Directory -Force -Path $userClaude | Out-Null
  $userSettings = Join-Path $userClaude 'settings.json'
  if (Test-Path $userSettings) {
    $shared = Get-Content .agent-config/repo/user/settings.json -Raw | ConvertFrom-Json
    $existing = Get-Content $userSettings -Raw | ConvertFrom-Json
    Merge-Json $existing $shared
    $existing | ConvertTo-Json -Depth 10 | Set-Content $userSettings
  } else {
    Copy-Item .agent-config/repo/user/settings.json $userSettings -Force
  }
}
# Heal legacy autoUpdates: false in ~/.claude.json. When the flag was already
# false at Claude Code native-install launch, the updater daemon never spawns
# (autoUpdatesProtectedForNative does not actually neutralize it in that path).
# To genuinely disable auto-updates, use DISABLE_AUTOUPDATER=1 via the env
# block in ~/.claude/settings.json; that takes precedence regardless.
$claudeJson = Join-Path $env:USERPROFILE '.claude.json'
if (Test-Path $claudeJson) {
  try {
    $claudeState = Get-Content $claudeJson -Raw | ConvertFrom-Json
    if ($claudeState.PSObject.Properties['autoUpdates'] -and $claudeState.autoUpdates -eq $false) {
      $claudeState.autoUpdates = $true
      # Best-effort heal. Atomic replace (staged temp + Move-Item -Force) prevents
      # a truncated config if this process is interrupted mid-write. It is NOT a
      # cross-process lock: a concurrent Claude Code write that lands between our
      # read and replace will still be clobbered by our older snapshot. The
      # healed flag persists on the next session if Claude Code re-wrote with
      # the stale value. Key ordering may change during the round trip; Claude
      # Code reads by key so this is acceptable. Unique GUID suffix avoids
      # concurrent-bootstrap temp-path collisions.
      $tmp = Join-Path (Split-Path $claudeJson) (".claude.json.{0}.tmp" -f [guid]::NewGuid().ToString("N"))
      $claudeState | ConvertTo-Json -Depth 20 | Set-Content $tmp
      Move-Item -Force $tmp $claudeJson
    }
  } catch {
    # ~/.claude.json is runtime-managed by Claude Code; skip on any read/parse error.
    if ($tmp -and (Test-Path $tmp)) { Remove-Item -Force $tmp }
  }
}

if (-not (Test-Path .gitignore) -or -not (Select-String -Quiet -Pattern '^\/?\.agent-config/' .gitignore)) {
  Add-Content -Path .gitignore -Value "`n.agent-config/"
}
# Self-update: copy the latest bootstrap script from the sparse clone over this
# one. Without this, a consumer that initially fetched an older bootstrap.ps1
# stays on that version forever; future bootstrap improvements added upstream
# (e.g. the 2026-04-16 generator step) would never reach them automatically.
if (Test-Path .agent-config/repo/bootstrap/bootstrap.ps1) {
  try {
    Copy-Item .agent-config/repo/bootstrap/bootstrap.ps1 .agent-config/bootstrap.ps1 -Force -ErrorAction Stop
  } catch {
    Write-Warning "Could not self-update .agent-config/bootstrap.ps1: $($_.Exception.Message)"
  }
}
