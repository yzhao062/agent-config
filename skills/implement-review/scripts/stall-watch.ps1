# stall-watch.ps1 -- Background failure and stall observer for Auto-terminal.
#
# Watches <state-dir>/tail and <state-dir>/tail.stderr-tmp. A terminal Codex
# response-stream failure is recorded immediately and the captured worker tree
# is reaped. Silence is lower-confidence: after 10 minutes by default it is
# recorded for auto-watch to surface, but no process is killed for silence.
# If the dispatcher disappears while its worker root is still alive, the
# abandoned worker tree is reaped before this observer exits.
#
# Args (named, --foo style for cross-platform parity with .sh):
#   --state-dir <abs-path>   Directory created by the dispatcher
#   --parent-pid <PID>       PID of the dispatcher
#
# Env:
#   STALL_THRESHOLD_SECONDS      Default 600 (10 min)
#   STALL_POLL_INTERVAL_SECONDS  Default 30
#   IMPLEMENT_REVIEW_STREAM_RETRY_LIMIT
#                                Maximum automatic redispatches after stream
#                                death (default 1; 0 disables). The dispatcher
#                                records the effective value in the state dir.
# Retry attempts reuse the dispatch state dir; the dispatcher archives each
# failed attempt under <state-dir>/attempt-N before starting the next watcher.

$ErrorActionPreference = 'Stop'

# Release the deployed path before either session can refresh the shared
# scripts. Invoking the copy in the same PowerShell host preserves the PID
# recorded by the dispatcher, so worker-tree capture still excludes $PID.
if ($env:IMPLEMENT_REVIEW_STALL_WATCH_REEXEC -ne '1') {
    $reexecTmpBase = $env:TMPDIR
    if (-not $reexecTmpBase) { $reexecTmpBase = $env:TEMP }
    if (-not $reexecTmpBase) { $reexecTmpBase = $env:TMP }
    if (-not $reexecTmpBase) { $reexecTmpBase = [System.IO.Path]::GetTempPath() }
    $reexecTmpBase = $reexecTmpBase.TrimEnd('\', '/')
    $reexecDir = Join-Path $reexecTmpBase "implement-review-stall-watch-reexec-$PID"
    $reexecCopy = Join-Path $reexecDir 'stall-watch.ps1'

    try {
        New-Item -ItemType Directory -Path $reexecDir | Out-Null
        Copy-Item -LiteralPath $PSCommandPath -Destination $reexecCopy
    } catch {
        [Console]::Error.WriteLine("stall-watch: failed to create re-exec copy: $reexecCopy")
        if (Test-Path -LiteralPath $reexecCopy -PathType Leaf) {
            Remove-Item -LiteralPath $reexecCopy -Force -ErrorAction SilentlyContinue
        }
        Remove-Item -LiteralPath $reexecDir -Force -ErrorAction SilentlyContinue
        exit 2
    }

    $env:IMPLEMENT_REVIEW_STALL_WATCH_REEXEC = '1'
    $env:IMPLEMENT_REVIEW_STALL_WATCH_SOURCE_DIR = $PSScriptRoot
    $reexecExit = 2
    try {
        & $reexecCopy @args
        $reexecExit = $LASTEXITCODE
    } catch {
        [Console]::Error.WriteLine("stall-watch: failed to launch re-exec copy: $reexecCopy")
    } finally {
        Remove-Item -LiteralPath $reexecCopy -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $reexecDir -Force -ErrorAction SilentlyContinue
    }
    exit $reexecExit
}

$scriptDir = if ($env:IMPLEMENT_REVIEW_STALL_WATCH_SOURCE_DIR) {
    $env:IMPLEMENT_REVIEW_STALL_WATCH_SOURCE_DIR
} else {
    $PSScriptRoot
}
Remove-Item Env:IMPLEMENT_REVIEW_STALL_WATCH_REEXEC -ErrorAction SilentlyContinue
Remove-Item Env:IMPLEMENT_REVIEW_STALL_WATCH_SOURCE_DIR -ErrorAction SilentlyContinue

$StateDir = $null
$ParentProcessIdRaw = $null

$i = 0
while ($i -lt $args.Length) {
    switch ($args[$i]) {
        '--state-dir' {
            if (($i + 1) -ge $args.Length) { exit 0 }
            $StateDir = $args[$i + 1]; $i += 2
        }
        '--parent-pid' {
            if (($i + 1) -ge $args.Length) { exit 0 }
            $ParentProcessIdRaw = $args[$i + 1]; $i += 2
        }
        default { exit 0 }
    }
}

$ParentProcessId = 0
if (-not $StateDir -or
    -not [int]::TryParse([string]$ParentProcessIdRaw, [ref]$ParentProcessId) -or
    $ParentProcessId -le 0) { exit 0 }
if (-not (Test-Path -LiteralPath $StateDir -PathType Container)) { exit 0 }

$threshold = 600
$parsed = 0
if ([int]::TryParse([string]$env:STALL_THRESHOLD_SECONDS, [ref]$parsed) -and $parsed -gt 0) {
    $threshold = $parsed
}
$interval = 30
$parsed = 0
if ([int]::TryParse([string]$env:STALL_POLL_INTERVAL_SECONDS, [ref]$parsed) -and $parsed -gt 0) {
    $interval = $parsed
}

$tailPath = Join-Path $StateDir 'tail'
$tailStderrPath = Join-Path $StateDir 'tail.stderr-tmp'
$warnPath = Join-Path $StateDir 'stall-warning'
$streamDeathPath = Join-Path $StateDir 'stream-death'
$reapReasonPath = Join-Path $StateDir 'reap-reason'
$workerRootsPath = Join-Path $StateDir 'worker-roots'
$streamRetryLimitPath = Join-Path $StateDir 'stream-retry-limit'
$streamRetryCountPath = Join-Path $StateDir 'stream-retry-count'
$streamRetryRequestPath = Join-Path $StateDir 'stream-retry-request'
$streamReapCompletePath = Join-Path $StateDir 'stream-reap-complete'
$watchedPaths = @($tailPath, $tailStderrPath)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false

try {
    $parentProcess = Get-Process -Id $ParentProcessId -ErrorAction Stop
    $parentStartTicks = [int64]$parentProcess.StartTime.ToUniversalTime().Ticks
} catch {
    exit 0
}

function Test-ParentAlive {
    try {
        $process = Get-Process -Id $ParentProcessId -ErrorAction Stop
        return ([int64]$process.StartTime.ToUniversalTime().Ticks -eq $parentStartTicks)
    } catch {
        return $false
    }
}

function Get-ProcessRecord {
    param([int]$ProcessId)
    try {
        return Get-CimInstance -ClassName Win32_Process `
            -Filter ("ProcessId = {0}" -f $ProcessId) `
            -ErrorAction Stop | Select-Object -First 1
    } catch {
        return $null
    }
}

function Get-CreationTicks {
    param($ProcessRecord)
    if ($null -eq $ProcessRecord -or $null -eq $ProcessRecord.CreationDate) { return $null }
    try {
        return [int64]([datetime]$ProcessRecord.CreationDate).ToUniversalTime().Ticks
    } catch {
        return $null
    }
}

$workerRoots = @{}
$captureAttempts = 0

function Save-WorkerRoots {
    if ($workerRoots.Count -gt 0) { return }
    $script:captureAttempts += 1
    try {
        $children = @(Get-CimInstance -ClassName Win32_Process `
            -Filter ("ParentProcessId = {0}" -f $ParentProcessId) `
            -ErrorAction Stop)
    } catch {
        return
    }
    foreach ($child in $children) {
        $childId = [int]$child.ProcessId
        if ($childId -eq $PID) { continue }
        $created = Get-CreationTicks $child
        if ($null -ne $created) {
            $workerRoots[$childId] = [int64]$created
        }
    }
    if ($workerRoots.Count -gt 0) {
        try {
            $rows = foreach ($entry in $workerRoots.GetEnumerator()) {
                "{0}`t{1}" -f $entry.Key, $entry.Value
            }
            [System.IO.File]::WriteAllLines($workerRootsPath, $rows, $utf8NoBom)
        } catch {
            # State diagnostics are best-effort.
        }
    }
}

function Test-SameWorkerProcess {
    param([int]$ProcessId, [int64]$CreationTicks)
    $record = Get-ProcessRecord $ProcessId
    $currentTicks = Get-CreationTicks $record
    return ($null -ne $currentTicks -and [int64]$currentTicks -eq $CreationTicks)
}

function Invoke-WorkerReap {
    param([string]$Reason)
    $victims = @($workerRoots.GetEnumerator() | Where-Object {
        Test-SameWorkerProcess ([int]$_.Key) ([int64]$_.Value)
    })
    if ($victims.Count -eq 0) { return }

    try {
        [System.IO.File]::WriteAllText($reapReasonPath, "$Reason`n", $utf8NoBom)
    } catch {
        # Best-effort marker; continue with the bounded target set.
    }

    $reapCmd = Join-Path $StateDir 'reap-worker.cmd'
    $reapBody = "@echo off`r`ntaskkill /PID %1 /T /F >NUL 2>&1`r`n"
    try {
        [System.IO.File]::WriteAllText($reapCmd, $reapBody, $utf8NoBom)
        $reaper = if ($env:ComSpec) { $env:ComSpec } else { 'cmd.exe' }
        foreach ($victim in $victims) {
            & $reaper /d /c $reapCmd ([int]$victim.Key) 2>$null | Out-Null
        }
    } catch {
        # Reaping is best-effort and restricted to captured worker identities.
    }
}

function Test-StreamDeathSuffix {
    if (-not (Test-Path -LiteralPath $tailPath -PathType Leaf)) { return $false }
    try {
        $lines = @(Get-Content -LiteralPath $tailPath -Tail 16 -ErrorAction Stop |
            ForEach-Object { ([string]$_).Trim() } |
            Where-Object { $_ -ne '' })
    } catch {
        return $false
    }
    if ($lines.Count -lt 3) { return $false }
    if ($lines[$lines.Count - 2] -cne 'tokens used') { return $false }
    if ($lines[$lines.Count - 1] -notmatch '^[0-9][0-9,]*$') { return $false }
    $first = [Math]::Max(0, $lines.Count - 5)
    for ($j = $first; $j -le ($lines.Count - 3); $j++) {
        if ($lines[$j] -cmatch '^ERROR: stream disconnected before completion: .*chatgpt[.]com/backend-api/codex/responses') {
            return $true
        }
    }
    return $false
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

function Request-StreamRetry {
    param([string]$IsoTimestamp)
    $limit = Get-StateCounter $streamRetryLimitPath
    $count = Get-StateCounter $streamRetryCountPath
    if ($null -eq $limit -or $null -eq $count -or $count -ge $limit) {
        return $false
    }
    try {
        [System.IO.File]::WriteAllText(
            $streamRetryRequestPath,
            (("STREAM-RETRY-REQUEST {0} attempt={1}/{2} " +
                "codex-response-stream-disconnected`n") -f
                $IsoTimestamp, ($count + 2), ($limit + 1)),
            $utf8NoBom
        )
        return $true
    } catch {
        return $false
    }
}

$lastSize = [int64]-1
$lastMtimeTicks = [int64]0
$lastGrowth = [DateTimeOffset]::UtcNow
$stalledLogged = $false

$ErrorActionPreference = 'Continue'

while ($true) {
    $parentAlive = Test-ParentAlive
    if ($parentAlive) { Save-WorkerRoots }

    $currentSize = [int64]0
    $currentMtimeTicks = [int64]0
    $anyExists = $false
    foreach ($path in $watchedPaths) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        try {
            $item = Get-Item -LiteralPath $path -ErrorAction Stop
            $currentSize += [int64]$item.Length
            $itemTicks = [int64]$item.LastWriteTimeUtc.Ticks
            if ($itemTicks -gt $currentMtimeTicks) { $currentMtimeTicks = $itemTicks }
            $anyExists = $true
        } catch {
            # Try the other watched stream.
        }
    }

    if ($anyExists) {
        $now = [DateTimeOffset]::UtcNow

        if ($currentSize -gt $lastSize -or $currentMtimeTicks -gt $lastMtimeTicks) {
            if (-not (Test-Path -LiteralPath $streamDeathPath -PathType Leaf) -and
                (Test-StreamDeathSuffix)) {
                $iso = $now.ToString('yyyy-MM-ddTHH:mm:ssZ')
                $retryRequested = Request-StreamRetry $iso
                try {
                    [System.IO.File]::WriteAllText(
                        $streamDeathPath,
                        "STREAM-DEATH $iso codex-response-stream-disconnected`n",
                        $utf8NoBom
                    )
                } catch {
                    if ($retryRequested) {
                        Remove-Item -LiteralPath $streamRetryRequestPath -Force `
                            -ErrorAction SilentlyContinue
                    }
                }
                Invoke-WorkerReap 'stream-death'
                try {
                    [System.IO.File]::WriteAllText(
                        $streamReapCompletePath,
                        "STREAM-REAP-COMPLETE $iso`n",
                        $utf8NoBom
                    )
                } catch {
                    # The dispatcher treats a missing completion marker as no retry.
                }
                exit 0
            }
            $lastSize = $currentSize
            $lastMtimeTicks = $currentMtimeTicks
            $lastGrowth = $now
            $stalledLogged = $false
        } else {
            $elapsed = [int]($now - $lastGrowth).TotalSeconds
            if ($elapsed -ge $threshold -and -not $stalledLogged) {
                $iso = $now.ToString('yyyy-MM-ddTHH:mm:ssZ')
                try {
                    [System.IO.File]::AppendAllText(
                        $warnPath,
                        ("STALL {0} tail-no-growth-for-{1}s`n" -f $iso, $elapsed),
                        $utf8NoBom
                    )
                    $stalledLogged = $true
                } catch {
                    exit 0
                }
            }
        }
    }

    if (-not $parentAlive) {
        Invoke-WorkerReap 'parent-exited'
        exit 0
    }

    if ($workerRoots.Count -gt 0 -or $captureAttempts -ge 5) {
        Start-Sleep -Seconds $interval
    } else {
        Start-Sleep -Seconds 1
    }
}
