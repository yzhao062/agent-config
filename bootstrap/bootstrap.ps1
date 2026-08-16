# Line endings are handled by this repo's .gitattributes. Bootstrap intentionally
# avoids changing user-level Git configuration.

param(
    [Parameter(Position=0)][string]$Upstream,
    [string]$RulePacks,
    [switch]$NoCache,
    [Alias("h")][switch]$Help
)

# Verify a candidate python actually executes before trusting it. Exit status
# alone is not proof that Python ran, so require the interpreter to echo a
# sentinel produced by the -c program.
function Test-PythonRuns([string]$PythonPath) {
  try {
    $global:LASTEXITCODE = $null
    $probeOutput = & $PythonPath -c 'import sys; sys.stdout.write("__ANYWHERE_AGENTS_PY3__" if sys.version_info[0] >= 3 else "")' 2>$null
    $launched = $?
    return ($launched -and $LASTEXITCODE -eq 0 -and ([string]$probeOutput).Trim() -eq '__ANYWHERE_AGENTS_PY3__')
  } catch {
    return $false
  }
}

function Test-PythonHasYaml([string]$PythonPath) {
  $global:LASTEXITCODE = $null
  & $PythonPath -c "import yaml" 2>$null
  return ($? -and $LASTEXITCODE -eq 0)
}

# Find a real Python interpreter, avoiding the Windows Store App Execution
# Alias shim under %LOCALAPPDATA%\Microsoft\WindowsApps\ that prints
# "Python was not found; install from Store" and exits non-zero on call.
# See https://github.com/yzhao062/anywhere-agents/issues/2.
function Find-RealPython {
  if ($env:ANYWHERE_AGENTS_PYTHON) {
    $override = Resolve-Path -LiteralPath $env:ANYWHERE_AGENTS_PYTHON -ErrorAction SilentlyContinue
    if ($override) {
      $cmd = Get-Command $override.ProviderPath -ErrorAction SilentlyContinue
      if ($cmd -and (Test-PythonRuns $cmd.Path)) { return $cmd }
    }
    [Console]::Error.WriteLine("[anywhere-agents] ANYWHERE_AGENTS_PYTHON did not execute Python 3 successfully: $($env:ANYWHERE_AGENTS_PYTHON); trying automatic discovery.")
  }
  $candidates = @()
  $candidates += Get-Command python3 -All -ErrorAction SilentlyContinue
  $candidates += Get-Command python -All -ErrorAction SilentlyContinue
  foreach ($c in $candidates) {
    if (-not $c) { continue }
    if ($c.Source -and ($c.Source -notmatch 'WindowsApps') -and (Test-PythonRuns $c.Path)) {
      return $c
    }
  }
  return $null
}

# Read the legacy passive-pack selection from one config layer without Python
# or PyYAML. The return value is one of: none, empty, nonempty.
function Get-RulePacksConfigState([string]$ConfigPath) {
  if (-not (Test-Path -LiteralPath $ConfigPath)) { return 'none' }
  $found = $false
  $inList = $false
  foreach ($line in [System.IO.File]::ReadAllLines((Resolve-Path -LiteralPath $ConfigPath))) {
    if ($line -match '^rule_packs:(.*)$') {
      $found = $true
      $inList = $true
      $tail = (($matches[1] -replace '#.*$', '') -replace '\s', '').ToLowerInvariant()
      if ($tail -and $tail -notin @('[]', 'null', '~')) { return 'nonempty' }
      continue
    }
    if ($inList) {
      if ([string]::IsNullOrWhiteSpace($line) -or $line -match '^\s*#') { continue }
      if ($line -match '^\s+') {
        if ($line -match '^\s*-') { return 'nonempty' }
        continue
      }
      break
    }
  }
  if ($found) { return 'empty' }
  return 'none'
}

function Test-PassiveRulePackConfigured {
  $trackedState = Get-RulePacksConfigState 'agent-config.yaml'
  $localState = Get-RulePacksConfigState 'agent-config.local.yaml'
  $envCompact = ([string]$env:AGENT_CONFIG_RULE_PACKS) -replace '[\s,]', ''
  # Layer order matters, and it is not a merge. Probing the real resolver gives
  # [] for tracked [agent-style] plus local [], so a later empty list clears an
  # earlier selection rather than adding nothing to it. Treating either layer's
  # non-emptiness as sufficient marked a deliberate opt-out as an incomplete
  # bootstrap. The environment variable is additive, so it wins when set.
  if ($envCompact) { return $true }
  if ($localState -eq 'nonempty') { return $true }
  if ($localState -eq 'empty') { return $false }
  if ($trackedState -eq 'nonempty') { return $true }
  if ($trackedState -eq 'empty') { return $false }
  # No signal in either layer: the composer's default selection includes
  # agent-style, so a passive pack is configured.
  return $true
}

# Stage beside the destination, then rename over it. Readers therefore see a
# complete old helper or a complete new helper, never a truncated copy.
function Copy-HelperAtomic([string]$Source, [string]$Destination) {
  $destinationDirectory = Split-Path -Parent $Destination
  $destinationName = Split-Path -Leaf $Destination
  $tempPath = $null
  $backupPath = $null
  try {
    New-Item -ItemType Directory -Force -Path $destinationDirectory -ErrorAction Stop | Out-Null
    $tempPath = Join-Path $destinationDirectory ('.{0}.{1}.tmp' -f $destinationName, [guid]::NewGuid().ToString('N'))
    Copy-Item -LiteralPath $Source -Destination $tempPath -Force -ErrorAction Stop
    if (Test-Path -LiteralPath $Destination) {
      $backupPath = Join-Path $destinationDirectory ('.{0}.{1}.bak' -f $destinationName, [guid]::NewGuid().ToString('N'))
      [System.IO.File]::Replace($tempPath, $Destination, $backupPath)
    } else {
      try {
        [System.IO.File]::Move($tempPath, $Destination)
      } catch {
        # Another bootstrap may have created the target after Test-Path.
        if (Test-Path -LiteralPath $Destination) {
          $backupPath = Join-Path $destinationDirectory ('.{0}.{1}.bak' -f $destinationName, [guid]::NewGuid().ToString('N'))
          [System.IO.File]::Replace($tempPath, $Destination, $backupPath)
        } else {
          throw
        }
      }
    }
    return $true
  } catch {
    throw "Could not atomically deploy '$Source' to '$Destination': $($_.Exception.Message)"
  } finally {
    if ($tempPath -and (Test-Path -LiteralPath $tempPath)) {
      Remove-Item -LiteralPath $tempPath -Force -ErrorAction SilentlyContinue
    }
    if ($backupPath -and (Test-Path -LiteralPath $backupPath)) {
      Remove-Item -LiteralPath $backupPath -Force -ErrorAction SilentlyContinue
    }
  }
}

function Write-Ledger([string]$LastPhase, [bool]$Completed) {
  try {
    $ledgerDir = Join-Path (Get-Location).Path '.agent-config'
    New-Item -ItemType Directory -Force -Path $ledgerDir -ErrorAction Stop | Out-Null
    $path = Join-Path $ledgerDir 'last-run.json'
    $tempPath = Join-Path $ledgerDir 'last-run.json.tmp'
    $document = [ordered]@{
      schema = 1
      emitted_by = 'bootstrap.ps1'
      run_id = $script:LedgerRunId
      started_at = $script:LedgerStarted
      upstream = $script:LedgerUpstream
      completed = $Completed
      last_phase = $LastPhase
      steps = @($script:LedgerSteps)
    }
    $json = $document | ConvertTo-Json -Depth 6
    [System.IO.File]::WriteAllText(
      $tempPath,
      $json + [Environment]::NewLine,
      (New-Object System.Text.UTF8Encoding $false)
    )
    Move-Item -LiteralPath $tempPath -Destination $path -Force -ErrorAction Stop
  } catch {
    # The ledger must never change bootstrap's outcome.
  }
}

function Initialize-Ledger {
  try {
    $script:LedgerSteps = @()
    $script:LedgerTargets = @()
    $script:LedgerIncomplete = $false
    $script:LedgerRunId = "$PID-" + [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $script:LedgerStarted = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
    # Coalesce to a string. bootstrap.sh emits "" for an unset upstream, and
    # ConvertTo-Json renders $null as JSON null, so leaving it unset would give
    # the two entry points different types for the same field.
    $script:LedgerUpstream = if ($Upstream) { $Upstream } elseif ($env:AGENT_CONFIG_UPSTREAM) { $env:AGENT_CONFIG_UPSTREAM } else { '' }
    Write-Ledger 'start' $false
  } catch {}
}

function Add-LedgerTarget([string]$TargetPath) {
  try {
    $script:LedgerTargets += $TargetPath
  } catch {}
}

function Add-LedgerStep {
  param(
    [string]$Phase,
    [string]$Scope,
    [string]$Status,
    [Nullable[int]]$Rc = $null,
    [string]$Reason
  )
  try {
    $stepRc = if ($PSBoundParameters.ContainsKey('Rc')) { [int]$Rc } else { $null }
    $step = [ordered]@{
      phase = $Phase
      scope = $Scope
      status = $Status
      rc = $stepRc
      targets = @($script:LedgerTargets)
    }
    if ($PSBoundParameters.ContainsKey('Reason')) {
      $step['reason'] = $Reason
    }
    $script:LedgerSteps += [pscustomobject]$step
    $script:LedgerTargets = @()
    Write-Ledger $Phase $false
  } catch {}
}

$script:GeneratorStatus = 'skipped'
$script:GeneratorRc = $null

function Invoke-AgentConfigGenerator($PythonCommand) {
  try {
    if (-not $PythonCommand -or -not (Test-Path .agent-config/repo/scripts/generate_agent_configs.py)) {
      return
    }
    $global:LASTEXITCODE = $null
    & $PythonCommand.Path .agent-config/repo/scripts/generate_agent_configs.py --root . --quiet
    $rc = if ($LASTEXITCODE -ne $null) { [int]$LASTEXITCODE } elseif (-not $?) { 1 } else { 0 }
    $script:GeneratorRc = $rc
    $script:GeneratorStatus = if ($rc -eq 0) { 'ok' } else { 'failed' }
  } catch {
    $script:GeneratorRc = 1
    $script:GeneratorStatus = 'failed'
  }
}

function Add-GeneratorLedgerStep {
  try {
    if ($script:GeneratorStatus -eq 'ok') {
      Add-LedgerTarget 'CLAUDE.md'
      Add-LedgerTarget 'agents/codex.md'
      Add-LedgerStep 'generate' 'repo' 'ok'
    } elseif ($script:GeneratorStatus -eq 'failed') {
      Add-LedgerStep 'generate' 'repo' 'failed' $script:GeneratorRc
    } else {
      Add-LedgerStep 'generate' 'repo' 'skipped'
    }
  } catch {}
}

# Detect git binary and reject pre-2.25 versions before any git invocation
# below. Sparse clone uses `git clone --filter=blob:none --sparse`; `--sparse`
# is the Git 2.25 floor (2020-01-13), while `--filter=blob:none` is the older
# partial-clone option (Git 2.19+). On parse failure default-pass with a
# stderr warning so unexpected version strings (alpha builds, distro
# suffixes like `2.30.1.windows.1`) do not block already-modern systems.
function Invoke-GitPreflight {
  if ($env:AGENT_CONFIG_SKIP_GIT_PREFLIGHT) { return }
  if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    [Console]::Error.WriteLine("[anywhere-agents] git is not installed or not on PATH; bootstrap needs git >= 2.25 for sparse clone.")
    [Console]::Error.WriteLine("[anywhere-agents] install: https://git-scm.com/download/win")
    exit 1
  }
  $verLine = $null
  try {
    $verLine = (& git --version 2>$null | Select-Object -First 1)
  } catch {
    $verLine = $null
  }
  if (-not $verLine) {
    [Console]::Error.WriteLine("[anywhere-agents] could not run git --version; assuming OK")
    return
  }
  $verStr = $verLine -replace '^git version ', ''
  if ($verStr -match '^(\d+)\.(\d+)') {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
  } else {
    [Console]::Error.WriteLine("[anywhere-agents] could not parse git version from '$verLine'; assuming OK")
    return
  }
  if (($major -lt 2) -or (($major -eq 2) -and ($minor -lt 25))) {
    [Console]::Error.WriteLine("[anywhere-agents] git $major.$minor is too old; bootstrap needs git >= 2.25 for sparse clone.")
    [Console]::Error.WriteLine("[anywhere-agents] install: https://git-scm.com/download/win")
    exit 1
  }
}

if ($Help) {
    Write-Output "Usage: .\bootstrap.ps1 [UPSTREAM] [-RulePacks PACK] [-NoCache]"
    Write-Output "  UPSTREAM      user/repo form; overrides AGENT_CONFIG_UPSTREAM env and persisted file"
    Write-Output "  -RulePacks P  print agent-config.yaml snippet for pack P and exit (dry helper)"
    Write-Output "  -NoCache      force refetch of rule-pack content on this run"
    exit 0
}

# Dry helper: -RulePacks prints a YAML snippet and exits without running
# bootstrap. Flag wins when both -RulePacks and AGENT_CONFIG_RULE_PACKS
# are set simultaneously.
if ($PSBoundParameters.ContainsKey('RulePacks')) {
    if ([string]::IsNullOrEmpty($RulePacks)) {
        [Console]::Error.WriteLine("error: -RulePacks requires a pack name")
        exit 1
    }
    if ($env:AGENT_CONFIG_RULE_PACKS) {
        [Console]::Error.WriteLine("notice: -RulePacks is a dry helper; AGENT_CONFIG_RULE_PACKS env var is ignored in this mode")
    }
    $snippet = @"
Add the following to agent-config.yaml at your project root, then run bootstrap again to apply:

  rule_packs:
    - name: $RulePacks
      # Optional: pin to a specific ref (defaults to manifest's default-ref)
      # ref: v0.3.5

After committing agent-config.yaml, run:

  .\bootstrap.ps1
"@
    Write-Output $snippet
    exit 0
}

try { Initialize-Ledger } catch {}
Invoke-GitPreflight
if ($env:AGENT_CONFIG_PREFLIGHT_TEST) { exit 0 }

# Legacy AC -> AA migration for direct PowerShell-bootstrap runs. If the
# persisted upstream or cached repo origin still points at agent-config
# and the caller did not pass an explicit upstream, delete the old cache
# so the normal clone path below re-clones anywhere-agents.
$explicitUpstream = $PSBoundParameters.ContainsKey('Upstream') -or $env:AGENT_CONFIG_UPSTREAM
$legacyAC = $false
if (-not $explicitUpstream) {
  if (Test-Path .agent-config/upstream) {
    $persisted = (Get-Content .agent-config/upstream -Raw).Replace("`r", "").Replace("`n", "").Trim()
    if ($persisted -eq 'yzhao062/agent-config') { $legacyAC = $true }
  }
  if (-not $legacyAC -and (Test-Path .agent-config/repo/.git/config)) {
    try {
      $originUrl = git -C .agent-config/repo remote get-url origin 2>$null
      if ($originUrl -match '(^|[:/])yzhao062/agent-config(\.git)?/?$') { $legacyAC = $true }
    } catch {}
  }
}
if ($legacyAC) {
  [Console]::Error.WriteLine('[anywhere-agents] Migrating from agent-config bootstrap to anywhere-agents...')
  Remove-Item -LiteralPath .agent-config/repo -Recurse -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath .agent-config/upstream, .agent-config/bootstrap.sh, .agent-config/bootstrap.ps1 -Force -ErrorAction SilentlyContinue
}

# Resolve Python once before the network-backed fetch and this run's user-level
# helper deployment. Every later Python-backed phase reuses this snapshot.
$pyCmd = Find-RealPython

# Upstream cascade: argv > env var > persisted file > hardcoded default.
# Forkers can persist a different default in their fork; consumers can pass
# upstream via `.\.agent-config\bootstrap.ps1 <user>/<repo>` or the
# $env:AGENT_CONFIG_UPSTREAM environment variable.
if (-not $Upstream) { $Upstream = $env:AGENT_CONFIG_UPSTREAM }
if (-not $Upstream -and (Test-Path .agent-config/upstream)) {
  $Upstream = (Get-Content .agent-config/upstream -Raw).Trim()
}
if (-not $Upstream) { $Upstream = 'yzhao062/anywhere-agents' }
New-Item -ItemType Directory -Force -Path .agent-config | Out-Null
Set-Content -Path .agent-config/upstream -Value $Upstream -NoNewline
try {
  $script:LedgerUpstream = $Upstream
  Add-LedgerTarget '.agent-config/upstream'
  Add-LedgerStep 'preflight' 'repo' 'ok'
} catch {}

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

function Test-DisabledValue([string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) { return $false }
  $normalized = $Value.Trim().ToLowerInvariant()
  return @('off', '0', 'disabled', 'false', 'no').Contains($normalized)
}

function Invoke-CodexAutoUpdate {
  if (Test-DisabledValue $env:ANYWHERE_AGENTS_CODEX_AUTO_UPDATE) { return }
  $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
  if (-not $npmCmd) { return }
  try {
    $npm = $npmCmd.Source
    $globalPrefix = (& $npm prefix -g 2>$null | Select-Object -First 1)
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($globalPrefix)) { return }
    $pkgJson = Join-Path (Join-Path (Join-Path $globalPrefix 'node_modules') '@openai') 'codex'
    $pkgJson = Join-Path $pkgJson 'package.json'
    if (-not (Test-Path $pkgJson)) { return }

    $outdatedRaw = (& $npm outdated -g '@openai/codex' --json 2>$null | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($outdatedRaw) -or $outdatedRaw -eq '{}') { return }
    try {
      $outdated = $outdatedRaw | ConvertFrom-Json
    } catch {
      return
    }
    $entry = $outdated.PSObject.Properties['@openai/codex']
    if (-not $entry) { return }
    $current = [string]$entry.Value.current
    $latest = [string]$entry.Value.latest
    if ([string]::IsNullOrWhiteSpace($latest) -or $latest -eq $current) { return }

    [Console]::Error.WriteLine("[anywhere-agents] updating Codex CLI @openai/codex $current -> $latest")
    & $npm install -g '@openai/codex@latest' --silent
    if ($LASTEXITCODE -ne 0) {
      [Console]::Error.WriteLine("[anywhere-agents] Codex CLI auto-update failed; run ``npm install -g @openai/codex@latest``")
    }
  } catch {
    # Do not let a local npm or registry problem block project bootstrap.
  }
}
New-Item -ItemType Directory -Force -Path .agent-config, .claude, .claude/commands | Out-Null
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/$Upstream/main/AGENTS.md" -OutFile .agent-config/AGENTS.md

# Sparse clone moved up (before composing the root AGENTS.md): the rule-pack
# manifest and composer helper live inside .agent-config/repo/ and must be
# present before we branch on compose vs verbatim fallback.
$RepoUrl = "https://github.com/$Upstream.git"
if (Test-Path .agent-config/repo/.git) {
  git -C .agent-config/repo remote set-url origin $RepoUrl
  git -C .agent-config/repo pull --ff-only
} else {
  git clone --depth 1 --filter=blob:none --sparse $RepoUrl .agent-config/repo
}
git -C .agent-config/repo sparse-checkout set skills .claude scripts user bootstrap
try {
  Add-LedgerTarget '.agent-config/AGENTS.md'
  Add-LedgerTarget '.agent-config/repo'
  Add-LedgerStep 'fetch' 'repo' 'ok'
} catch {}

# Compose root AGENTS.md. Default-on: every aa consumer gets the agent-style
# writing rule pack unless they explicitly opt out via `rule_packs: []` in
# agent-config.yaml. Composition requires Python 3 + PyYAML; when PyYAML is
# missing we attempt a best-effort `pip install --user pyyaml`. If Python or
# PyYAML still are not available, we fall back to a marked upstream
# AGENTS.md and print a one-line tip unless the consumer has explicitly
# referenced rule_packs themselves.
$composeOk = $false
$composeSkipReason = ''
if (-not $pyCmd) {
    $composeSkipReason = 'no Python 3 interpreter found'
} else {
    if (-not (Test-PythonHasYaml $pyCmd.Path)) {
        [Console]::Error.WriteLine("installing PyYAML (enables agent-style rule-pack composition)...")
        $global:LASTEXITCODE = $null
        & $pyCmd.Path -m pip install --user --quiet pyyaml 2>$null
    }
    if (Test-PythonHasYaml $pyCmd.Path) {
        $composeOk = $true
    } else {
        $composeSkipReason = 'Python 3 interpreter has no PyYAML after install attempt'
    }
}

if ($composeOk -and -not (Test-Path .agent-config/repo/scripts/compose_packs.py) -and -not (Test-Path .agent-config/repo/scripts/compose_rule_packs.py)) {
    # Upstream sparse clone has no composer script (e.g. the ac source repo
    # itself, which intentionally ships only generate_agent_configs.py and
    # not the v0.4.0 unified composer). Fall through to the marked-AGENTS.md
    # path instead of crashing on a non-existent Python file.
    [Console]::Error.WriteLine("[anywhere-agents] no composer script in .agent-config/repo/scripts/; falling back to verbatim AGENTS.md")
    $composeOk = $false
    $composeSkipReason = 'no composer script in sparse clone'
}

if ($composeOk) {
    $composeArgs = @("--root", ".")
    if ($NoCache) { $composeArgs += "--no-cache" }
    # Prefer the v0.4.0 unified composer. Fall back to the v0.3.x rule-pack
    # composer on pre-v0.4.0 sparse clones that predate compose_packs.py.
    if (Test-Path .agent-config/repo/scripts/compose_packs.py) {
        $composer = ".agent-config/repo/scripts/compose_packs.py"
    } else {
        $composer = ".agent-config/repo/scripts/compose_rule_packs.py"
    }
    # v0.5.8: capture composer rc and always run generator so CLAUDE.md stays
    # coherent even when composition aborts (e.g. DriftAbort, OSError).
    $global:LASTEXITCODE = $null
    & $pyCmd.Path $composer @composeArgs
    $composerRc = if ($LASTEXITCODE -ne $null) { [int]$LASTEXITCODE } elseif (-not $?) { 1 } else { 0 }
    Invoke-AgentConfigGenerator $pyCmd
    if ($composerRc -ne 0) {
        [Console]::Error.WriteLine("[anywhere-agents] pack composition did not complete (rc=$composerRc); generated files (CLAUDE.md, agents/codex.md) refreshed from current AGENTS.md. Re-run ``anywhere-agents`` after addressing the failure.")
        try {
          Add-LedgerTarget 'AGENTS.md'
          Add-LedgerStep 'compose' 'repo' 'failed' $composerRc
          Add-GeneratorLedgerStep
        } catch {}
        exit $composerRc
    }
    try {
      Add-LedgerTarget 'AGENTS.md'
      Add-LedgerStep 'compose' 'repo' 'ok'
    } catch {}
} else {
    $passiveRulePackConfigured = Test-PassiveRulePackConfigured
    if ($passiveRulePackConfigured) {
      $fallbackMarker = "<!-- rule-pack composition skipped: $composeSkipReason; run anywhere-agents to compose -->"
      $upstreamAgents = [System.IO.File]::ReadAllText((Resolve-Path -LiteralPath .agent-config/AGENTS.md))
      [System.IO.File]::WriteAllText(
        (Join-Path (Get-Location).Path 'AGENTS.md'),
        $fallbackMarker + "`n" + $upstreamAgents,
        (New-Object System.Text.UTF8Encoding $false)
      )
      $script:LedgerIncomplete = $true
    } else {
      Copy-Item .agent-config/AGENTS.md AGENTS.md -Force
    }
    $trackedState = Get-RulePacksConfigState 'agent-config.yaml'
    $localState = Get-RulePacksConfigState 'agent-config.local.yaml'
    $rpAware = ($trackedState -ne 'none' -or $localState -ne 'none' -or [bool]$env:AGENT_CONFIG_RULE_PACKS)
    if (-not $rpAware) {
        [Console]::Error.WriteLine("")
        [Console]::Error.WriteLine("tip: anywhere-agents ships with agent-style writing rules enabled by default,")
        [Console]::Error.WriteLine("     but this run skipped them ($composeSkipReason).")
        [Console]::Error.WriteLine("     install Python + PyYAML to enable, or silence with 'rule_packs: []' in agent-config.yaml.")
    }
    try {
      Add-LedgerTarget 'AGENTS.md'
      Add-LedgerStep 'compose' 'repo' 'skipped' -Reason $composeSkipReason
    } catch {}
}
# Generate per-agent config files (CLAUDE.md, agents/codex.md) from AGENTS.md.
# Generator preserves hand-authored files (no GENERATED header) and warns loudly.
# v0.5.8: in the composeOk path the generator already ran above. Only run here
# for the fallback path (Python/PyYAML unavailable) where $composeOk is false.
if (-not $composeOk) {
  Invoke-AgentConfigGenerator $pyCmd
}
Add-GeneratorLedgerStep
if (Test-Path .agent-config/repo/.claude/commands) {
  Copy-Item .agent-config/repo/.claude/commands/*.md .claude/commands/ -Force
  try { Add-LedgerTarget '.claude/commands' } catch {}
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
  try { Add-LedgerTarget '.claude/settings.json' } catch {}
}
try { Add-LedgerStep 'project_files' 'repo' 'ok' } catch {}
# --- User-level setup: hooks and settings ---
# This section modifies ~/.claude/ (user-level, not project-level).
# It deploys a PreToolUse hook guard and merges shared permission settings.
# Remove this section if you do not want bootstrap to modify user-level config.
$userClaude = Join-Path $env:USERPROFILE '.claude'
if (Test-Path .agent-config/repo/scripts/_python) {
  $hooksDir = Join-Path $userClaude 'hooks'
  if (Copy-HelperAtomic .agent-config/repo/scripts/_python (Join-Path $hooksDir '_python')) {
    try { Add-LedgerTarget '~/.claude/hooks/_python' } catch {}
  }
}
if (Test-Path .agent-config/repo/scripts/guard.py) {
  $hooksDir = Join-Path $userClaude 'hooks'
  if (Copy-HelperAtomic .agent-config/repo/scripts/guard.py (Join-Path $hooksDir 'guard.py')) {
    try { Add-LedgerTarget '~/.claude/hooks/guard.py' } catch {}
  }
}
if (Test-Path .agent-config/repo/scripts/session_bootstrap.py) {
  $hooksDir = Join-Path $userClaude 'hooks'
  if (Copy-HelperAtomic .agent-config/repo/scripts/session_bootstrap.py (Join-Path $hooksDir 'session_bootstrap.py')) {
    try { Add-LedgerTarget '~/.claude/hooks/session_bootstrap.py' } catch {}
  }
}
if (Test-Path .agent-config/repo/scripts/statusline.py) {
  if (Copy-HelperAtomic .agent-config/repo/scripts/statusline.py (Join-Path $userClaude 'statusline.py')) {
    try { Add-LedgerTarget '~/.claude/statusline.py' } catch {}
  }
}
if (Test-Path .agent-config/repo/scripts/agent-quota.py) {
  if (Copy-HelperAtomic .agent-config/repo/scripts/agent-quota.py (Join-Path $userClaude 'agent-quota.py')) {
    try { Add-LedgerTarget '~/.claude/agent-quota.py' } catch {}
  }
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
  try { Add-LedgerTarget '~/.claude/settings.json' } catch {}
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
  try { Add-LedgerTarget '~/.claude.json' } catch {}
}
try { Add-LedgerStep 'user_files' 'user' 'ok' } catch {}

# Codex CLI has no native updater like Claude Code. If Codex is installed as
# the global npm package that this config recommends, keep it current during
# bootstrap. Set ANYWHERE_AGENTS_CODEX_AUTO_UPDATE=off to disable.
Invoke-CodexAutoUpdate
# No target here: Invoke-CodexAutoUpdate no-ops when Codex is not the global
# npm install or when ANYWHERE_AGENTS_CODEX_AUTO_UPDATE=off, so naming the
# package would imply an update that may not have happened.
try {
  Add-LedgerStep 'external' 'external' 'ok'
} catch {}

if (-not (Test-Path .gitignore) -or -not (Select-String -Quiet -Pattern '^\/?\.agent-config/' .gitignore)) {
  Add-Content -Path .gitignore -Value "`n.agent-config/"
}
# Rule-pack opt-in writes agent-config.local.yaml as a machine-local override
# that must not be committed. Auto-ignore it idempotently alongside .agent-config/.
if (-not (Test-Path .gitignore) -or -not (Select-String -Quiet -Pattern '^\/?agent-config\.local\.yaml$' .gitignore)) {
  Add-Content -Path .gitignore -Value "`nagent-config.local.yaml"
}
# Self-update: copy the latest bootstrap script from the sparse clone over this
# one. Without this, a consumer that initially fetched an older bootstrap.ps1
# stays on that version forever; future bootstrap improvements added upstream
# (e.g. the 2026-04-16 generator step) would never reach them automatically.
#
# v0.5.2 cross-OS fix: copy BOTH bootstrap.ps1 AND bootstrap.sh. Previously
# the .ps1 entry only refreshed itself, so a developer who later switched
# to Git Bash / WSL on the same project would hit "No such file or
# directory" on .agent-config/bootstrap.sh. Symmetric in bootstrap.sh.
if (Test-Path .agent-config/repo/bootstrap/bootstrap.ps1) {
  try {
    Copy-Item .agent-config/repo/bootstrap/bootstrap.ps1 .agent-config/bootstrap.ps1 -Force -ErrorAction Stop
  } catch {
    Write-Warning "Could not self-update .agent-config/bootstrap.ps1: $($_.Exception.Message)"
  }
}
if (Test-Path .agent-config/repo/bootstrap/bootstrap.sh) {
  try {
    Copy-Item .agent-config/repo/bootstrap/bootstrap.sh .agent-config/bootstrap.sh -Force -ErrorAction Stop
  } catch {
    Write-Warning "Could not copy .agent-config/bootstrap.sh: $($_.Exception.Message)"
  }
}
try {
  Add-LedgerTarget '.gitignore'
  Add-LedgerTarget '.agent-config/bootstrap.sh'
  Add-LedgerTarget '.agent-config/bootstrap.ps1'
  Add-LedgerStep 'finalize' 'repo' 'ok'
  Write-Ledger 'finalize' (-not $script:LedgerIncomplete)
} catch {}
