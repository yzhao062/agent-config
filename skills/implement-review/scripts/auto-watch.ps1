# Auto-watch -- implement-review Phase 1d watcher (PowerShell variant).
#
# Polls every 5s until a Review-<reviewer>.md file lands that satisfies
# all three trigger conditions, then emits "DONE <abs-path>" on stdout
# and exits 0. Times out after 60 minutes by default with "TIMEOUT" and
# exit 2.
#
# Stdout starts with WATCH-START and ends with one terminal line. A confirmed
# automatic retry adds one visible AUTO-REDISPATCH line between them:
#   WATCH-START round=<N> reviewers=<csv> timeout=<seconds>s
#   AUTO-REDISPATCH attempt=<N>/<total> reason=codex-response-stream-disconnected state-dir=<abs-path>
#   DONE <abs-path> | TIMEOUT | STREAM-DEAD <state-dir> | STALL <state-dir>
#
# Usage:
#   pwsh auto-watch.ps1 <FileGlob> <Round> <Reviewers>
#   powershell -File auto-watch.ps1 <FileGlob> <Round> <Reviewers>
#
# Env:
#   AGENT_CONFIG_AUTO_WATCH_TIMEOUT  override timeout in seconds (tests).
#   IMPLEMENT_REVIEW_STREAM_RETRY_LIMIT
#                                    maximum automatic redispatches after a
#                                    confirmed stream death (default 1; 0
#                                    disables). The dispatcher records the
#                                    effective value in the state directory.
#
# Exit codes: 0 = DONE, 2 = TIMEOUT, 3 = dispatch failure/stall surfaced.
# A retry keeps the original state directory so the dispatcher's single
# STATE-DIR line stays valid. Failed-attempt files are archived under
# <state-dir>/attempt-N before the same logical dispatch starts again.

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)][string]$FileGlob,
    [Parameter(Mandatory = $true, Position = 1)][int]$Round,
    [Parameter(Mandatory = $true, Position = 2)][string]$Reviewers
)

$ErrorActionPreference = 'Stop'

# Release the deployed path before either session can refresh the shared
# scripts. Invoking the copy in the same PowerShell host preserves the
# caller-visible background PID; child-script exit status flows through
# $LASTEXITCODE, after which the temporary copy and directory are removed.
if ($env:IMPLEMENT_REVIEW_AUTO_WATCH_REEXEC -ne '1') {
    $reexecTmpBase = $env:TMPDIR
    if (-not $reexecTmpBase) { $reexecTmpBase = $env:TEMP }
    if (-not $reexecTmpBase) { $reexecTmpBase = $env:TMP }
    if (-not $reexecTmpBase) { $reexecTmpBase = [System.IO.Path]::GetTempPath() }
    $reexecTmpBase = $reexecTmpBase.TrimEnd('\', '/')
    $reexecDir = Join-Path $reexecTmpBase "implement-review-auto-watch-reexec-$PID"
    $reexecCopy = Join-Path $reexecDir 'auto-watch.ps1'

    try {
        New-Item -ItemType Directory -Path $reexecDir | Out-Null
        Copy-Item -LiteralPath $PSCommandPath -Destination $reexecCopy
    } catch {
        [Console]::Error.WriteLine("auto-watch: failed to create re-exec copy: $reexecCopy")
        if (Test-Path -LiteralPath $reexecCopy -PathType Leaf) {
            Remove-Item -LiteralPath $reexecCopy -Force -ErrorAction SilentlyContinue
        }
        Remove-Item -LiteralPath $reexecDir -Force -ErrorAction SilentlyContinue
        exit 2
    }

    $env:IMPLEMENT_REVIEW_AUTO_WATCH_REEXEC = '1'
    $env:IMPLEMENT_REVIEW_AUTO_WATCH_SOURCE_DIR = $PSScriptRoot
    $reexecExit = 2
    try {
        & $reexecCopy $FileGlob $Round $Reviewers
        $reexecExit = $LASTEXITCODE
    } catch {
        [Console]::Error.WriteLine("auto-watch: failed to launch re-exec copy: $reexecCopy")
    } finally {
        Remove-Item -LiteralPath $reexecCopy -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $reexecDir -Force -ErrorAction SilentlyContinue
    }
    exit $reexecExit
}

$scriptDir = if ($env:IMPLEMENT_REVIEW_AUTO_WATCH_SOURCE_DIR) {
    $env:IMPLEMENT_REVIEW_AUTO_WATCH_SOURCE_DIR
} else {
    $PSScriptRoot
}
Remove-Item Env:IMPLEMENT_REVIEW_AUTO_WATCH_REEXEC -ErrorAction SilentlyContinue
Remove-Item Env:IMPLEMENT_REVIEW_AUTO_WATCH_SOURCE_DIR -ErrorAction SilentlyContinue

$timeout = if ($env:AGENT_CONFIG_AUTO_WATCH_TIMEOUT) {
    [int]$env:AGENT_CONFIG_AUTO_WATCH_TIMEOUT
} else { 3600 }
$pollSeconds  = 5
$stableWindow = 10

$expected = $Reviewers -split ','

function Get-EpochSeconds {
    param([datetime]$Utc = ([datetime]::UtcNow))
    [long](($Utc - [datetime]'1970-01-01').TotalSeconds)
}

function Get-StateCounter {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    try {
        $raw = (Get-Content -LiteralPath $Path -TotalCount 1 -ErrorAction Stop).Trim()
    } catch {
        return $null
    }
    $value = 0
    if (-not [int]::TryParse($raw, [ref]$value) -or $value -lt 0) { return $null }
    return $value
}

# Snapshot existing matching files' mtimes (UTC epoch seconds). Without
# this, a file that already exists with the matching round marker would
# fire immediately on the first poll, defeating the "wait for reviewer
# to write" intent.
$preSnap = @{}
foreach ($f in @(Get-ChildItem -Path $FileGlob -File -ErrorAction SilentlyContinue)) {
    $preSnap[$f.FullName] = Get-EpochSeconds -Utc $f.LastWriteTimeUtc
}

[Console]::Out.WriteLine("WATCH-START round=$Round reviewers=$Reviewers timeout=${timeout}s")

$startEpoch = Get-EpochSeconds

# Auto-terminal dispatch creates its state directory immediately before this
# watcher starts. Capture only same-repo/same-round directories started within
# 30 seconds, so stale rounds and work in other repositories cannot signal.
$cwdBytes = [System.Text.Encoding]::UTF8.GetBytes((Get-Location).Path)
$sha = [System.Security.Cryptography.SHA256]::Create()
try {
    $hashBytes = $sha.ComputeHash($cwdBytes)
    $repoHash = ([System.BitConverter]::ToString($hashBytes)).Replace('-', '').Substring(0, 8).ToLower()
} finally {
    $sha.Dispose()
}
$tmpBase = $env:TMPDIR
if (-not $tmpBase) { $tmpBase = $env:TEMP }
if (-not $tmpBase) { $tmpBase = $env:TMP }
if (-not $tmpBase) { $tmpBase = [System.IO.Path]::GetTempPath() }
$activeStateDirs = @()
$retryNotified = @{}
foreach ($stateDir in @(Get-ChildItem -LiteralPath $tmpBase -Directory `
        -Filter "implement-review-*-$repoHash-round$Round-*" `
        -ErrorAction SilentlyContinue)) {
    $timestampPath = Join-Path $stateDir.FullName 'timestamp'
    if (-not (Test-Path -LiteralPath $timestampPath -PathType Leaf)) { continue }
    $stateStart = 0L
    try {
        $rawStart = (Get-Content -LiteralPath $timestampPath -TotalCount 1 -ErrorAction Stop).Trim()
    } catch {
        continue
    }
    if (-not [long]::TryParse($rawStart, [ref]$stateStart)) { continue }
    if ($stateStart -ge ($startEpoch - 30) -and $stateStart -le ($startEpoch + 5)) {
        $activeStateDirs += $stateDir.FullName
    }
}

while ($true) {
    $now = Get-EpochSeconds
    if (($now - $startEpoch) -ge $timeout) {
        [Console]::Out.WriteLine('TIMEOUT')
        exit 2
    }

    foreach ($f in @(Get-ChildItem -Path $FileGlob -File -ErrorAction SilentlyContinue)) {
        $name = $f.BaseName -replace '^Review-', ''
        if ($expected -notcontains $name) { continue }

        $cur = Get-EpochSeconds -Utc $f.LastWriteTimeUtc
        $pre = if ($preSnap.ContainsKey($f.FullName)) {
            $preSnap[$f.FullName]
        } else { 0 }

        # (a) mtime advanced past the watcher's startup snapshot.
        if ($cur -le $pre) { continue }
        # (b) mtime has been quiet for $stableWindow seconds.
        if (($now - $cur) -lt $stableWindow) { continue }
        # (c) first line equals "<!-- Round N -->" after \r + trailing-
        # whitespace stripping. Windows newline tolerance.
        $first = Get-Content -Path $f.FullName -TotalCount 1 -ErrorAction SilentlyContinue
        if ($null -eq $first) { continue }
        $first = ($first -replace "`r$", '') -replace '\s+$', ''
        if ($first -ne ("<!-- Round $Round -->")) { continue }

        [Console]::Out.WriteLine("DONE $($f.FullName)")
        exit 0
    }

    foreach ($stateDir in $activeStateDirs) {
        $retryLimit = Get-StateCounter (Join-Path $stateDir 'stream-retry-limit')
        $retryCount = Get-StateCounter (Join-Path $stateDir 'stream-retry-count')
        if ($null -ne $retryLimit -and $null -ne $retryCount -and $retryCount -gt 0) {
            $retryKey = "${stateDir}`t$retryCount"
            if (-not $retryNotified.ContainsKey($retryKey)) {
                $retryNotified[$retryKey] = $true
                [Console]::Out.WriteLine(
                    "AUTO-REDISPATCH attempt=$($retryCount + 1)/$($retryLimit + 1) " +
                    "reason=codex-response-stream-disconnected state-dir=$stateDir"
                )
            }
        }
        if (Test-Path -LiteralPath (Join-Path $stateDir 'stream-death') -PathType Leaf) {
            $retryRequest = Join-Path $stateDir 'stream-retry-request'
            if ((Test-Path -LiteralPath $retryRequest -PathType Leaf) -and
                $null -ne $retryLimit -and $null -ne $retryCount -and
                $retryCount -lt $retryLimit) {
                try {
                    $requestAge = ([datetime]::UtcNow -
                        (Get-Item -LiteralPath $retryRequest -ErrorAction Stop).LastWriteTimeUtc
                    ).TotalSeconds
                } catch {
                    $requestAge = 30
                }
                if ($requestAge -lt 30) { continue }
            }
            [Console]::Out.WriteLine("STREAM-DEAD $stateDir")
            exit 3
        }
        if (Test-Path -LiteralPath (Join-Path $stateDir 'stall-warning') -PathType Leaf) {
            [Console]::Out.WriteLine("STALL $stateDir")
            exit 3
        }
    }

    Start-Sleep -Seconds $pollSeconds
}
