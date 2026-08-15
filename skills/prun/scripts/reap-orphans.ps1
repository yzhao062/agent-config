# reap-orphans.ps1 -- reap prun worker trees whose recorded dispatcher is gone.
#
# This tool acts by default because it replaces the unsafe practice of killing
# every process with a worker executable's name, which previously killed two
# live workers. A dry-run-only default would invite callers to bypass it again.
# Safety comes from the bounded target set: only PIDs read from prun state directories
# with dead dispatchers are eligible, and processes are never listed by name.
# This differs from guard.py, which requires human confirmation for arbitrary
# process-destruction commands because their affected set cannot be inferred
# from command text. Here the affected set is enumerable and test-covered.
#
# Usage: reap-orphans.ps1 [--dry-run] [--state-dir <path>]...
# Exit: 0 after classification/reaping, 2 on usage error.

$ErrorActionPreference = 'Stop'

$DryRun = $false
$StateDirs = [System.Collections.Generic.List[string]]::new()

function Write-Usage {
    [Console]::Error.WriteLine('Usage: reap-orphans.ps1 [--dry-run] [--state-dir <path>]...')
}

$i = 0
while ($i -lt $args.Length) {
    switch ($args[$i]) {
        { $_ -in @('--dry-run', '-DryRun') } {
            $DryRun = $true
            $i += 1
        }
        { $_ -in @('--state-dir', '-StateDir') } {
            if ($i + 1 -ge $args.Length) {
                [Console]::Error.WriteLine('reap-orphans: --state-dir needs a value')
                Write-Usage
                exit 2
            }
            $StateDirs.Add([string]$args[$i + 1])
            $i += 2
        }
        default {
            [Console]::Error.WriteLine("reap-orphans: unknown argument: $($args[$i])")
            Write-Usage
            exit 2
        }
    }
}

$tmpBase = $env:TMPDIR
if (-not $tmpBase) { $tmpBase = $env:TEMP }
if (-not $tmpBase) { $tmpBase = $env:TMP }
if (-not $tmpBase) { $tmpBase = [System.IO.Path]::GetTempPath() }
$tmpBase = $tmpBase.TrimEnd('\', '/')

$candidates = @()
if ($StateDirs.Count -gt 0) {
    $candidates = @($StateDirs)
} elseif (Test-Path -LiteralPath $tmpBase -PathType Container) {
    $candidates = @(Get-ChildItem -LiteralPath $tmpBase -Directory -Filter 'prun-task-*' -ErrorAction SilentlyContinue |
        Sort-Object -Property Name |
        ForEach-Object { $_.FullName })
}

[Console]::Out.WriteLine("REAP-START base=$tmpBase candidates=$($candidates.Count)")

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$reapedCount = 0
$leftCount = 0

function Write-Left {
    param([string]$StateName, [string]$Reason)
    [Console]::Out.WriteLine("LEFT $StateName $Reason")
    $script:leftCount += 1
}

function Get-Win32ProcessRows {
    param([string]$Filter)
    if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) {
        if (-not $Filter) {
            return @(Get-CimInstance -ClassName Win32_Process -ErrorAction Stop)
        }
        return @(Get-CimInstance -ClassName Win32_Process -Filter $Filter -ErrorAction Stop)
    }
    if (Get-Command Get-WmiObject -ErrorAction SilentlyContinue) {
        if (-not $Filter) {
            return @(Get-WmiObject -Class Win32_Process -ErrorAction Stop)
        }
        return @(Get-WmiObject -Class Win32_Process -Filter $Filter -ErrorAction Stop)
    }
    throw 'Win32 process enumeration is unavailable'
}

function Add-NewRetainedDescendants {
    param(
        [System.Collections.ArrayList]$Retained,
        [hashtable]$Seen,
        [hashtable]$DepthByPid,
        [int]$MaxRetained
    )

    try {
        $rows = @(Get-Win32ProcessRows '')
    } catch {
        return [pscustomobject]@{ Added = 0; Complete = $false }
    }

    $added = 0
    $complete = $true
    $changed = $true
    while ($changed) {
        $changed = $false
        $opened = New-Object System.Collections.ArrayList
        foreach ($row in $rows) {
            try {
                $childPid = [int]$row.ProcessId
                $parentPid = [int]$row.ParentProcessId
            } catch {
                $complete = $false
                continue
            }
            $childKey = [string]$childPid
            $parentKey = [string]$parentPid
            if ($Seen.ContainsKey($childKey) -or -not $Seen.ContainsKey($parentKey)) {
                continue
            }
            if ($Retained.Count + $opened.Count -ge $MaxRetained) {
                $complete = $false
                continue
            }

            $child = Get-Process -Id $childPid -ErrorAction SilentlyContinue
            if ($child) {
                try {
                    [void]$child.Handle
                    if ($child.HasExited) {
                        $child.Dispose()
                        continue
                    }
                } catch {
                    $complete = $false
                    $child.Dispose()
                    continue
                }
            }
            [void]$opened.Add([pscustomobject]@{
                Process = $child
                Pid = $childPid
                Key = $childKey
                ParentPid = $parentPid
                ParentKey = $parentKey
            })
        }

        if ($opened.Count -eq 0) { break }
        try {
            $confirmRows = @(Get-Win32ProcessRows '')
        } catch {
            $complete = $false
            foreach ($candidate in $opened) {
                if ($candidate.Process) { $candidate.Process.Dispose() }
            }
            break
        }
        $confirmByPid = @{}
        foreach ($confirmRow in $confirmRows) {
            try {
                $confirmKey = [string]([int]$confirmRow.ProcessId)
            } catch {
                $complete = $false
                continue
            }
            if ($confirmByPid.ContainsKey($confirmKey)) {
                $complete = $false
            } else {
                $confirmByPid[$confirmKey] = $confirmRow
            }
        }

        foreach ($candidate in $opened) {
            $keepChild = $false
            try {
                if (-not $confirmByPid.ContainsKey($candidate.Key)) {
                    if ($candidate.Process -and -not $candidate.Process.HasExited) {
                        $complete = $false
                    }
                    continue
                }
                $currentRow = $confirmByPid[$candidate.Key]
                if ([int]$currentRow.ParentProcessId -ne $candidate.ParentPid) {
                    continue
                }
                if (-not $candidate.Process) {
                    $complete = $false
                    continue
                }
                if ($candidate.Process.HasExited) { continue }

                $Seen[$candidate.Key] = $true
                $DepthByPid[$candidate.Key] = [int]$DepthByPid[$candidate.ParentKey] + 1
                [void]$Retained.Add([pscustomobject]@{
                    Process = $candidate.Process
                    Depth = [int]$DepthByPid[$candidate.Key]
                })
                $keepChild = $true
                $changed = $true
                $added += 1
            } catch {
                $complete = $false
            } finally {
                if ($candidate.Process -and -not $keepChild) {
                    $candidate.Process.Dispose()
                }
            }
        }
    }
    return [pscustomobject]@{ Added = $added; Complete = $complete }
}

function Stop-RetainedProcessTree {
    param([object[]]$Retained)

    $killSent = $false
    foreach ($entry in @($Retained | Sort-Object -Property Depth -Descending)) {
        try {
            if (-not $entry.Process.HasExited) {
                $entry.Process.Kill()
                $killSent = $true
            }
        } catch { }
    }
    return $killSent
}

function Wait-RetainedProcessTree {
    param([object[]]$Retained, [DateTime]$Deadline)

    foreach ($entry in $Retained) {
        try {
            $remaining = [int][Math]::Max(
                0,
                ($Deadline - [DateTime]::UtcNow).TotalMilliseconds
            )
            [void]$entry.Process.WaitForExit($remaining)
        } catch { }
    }

    foreach ($entry in $Retained) {
        try {
            if (-not $entry.Process.HasExited) { return $false }
        } catch {
            return $false
        }
    }
    return $true
}

function Test-RetainedProcessTreeExited {
    param([System.Collections.ArrayList]$Retained)

    foreach ($entry in $Retained) {
        try {
            if (-not $entry.Process.HasExited) { return $false }
        } catch {
            return $false
        }
    }
    return $true
}

foreach ($stateDir in $candidates) {
    $trimmedStateDir = ([string]$stateDir).TrimEnd('\', '/')
    $stateName = [System.IO.Path]::GetFileName($trimmedStateDir)
    if (-not $stateName) { $stateName = $trimmedStateDir }

    $dispatchPidText = ''
    $dispatchPidPath = [System.IO.Path]::Combine([string]$stateDir, 'dispatch-pid')
    if (Test-Path -LiteralPath $dispatchPidPath -PathType Leaf) {
        try { $dispatchPidText = [string](Get-Content -LiteralPath $dispatchPidPath -First 1 -ErrorAction Stop) } catch { $dispatchPidText = '' }
    }
    if ($dispatchPidText -notmatch '^\d+$') {
        Write-Left $stateName 'no-dispatch-record'
        continue
    }

    $workerRootsPath = [System.IO.Path]::Combine([string]$stateDir, 'worker-roots')
    if (-not (Test-Path -LiteralPath $workerRootsPath -PathType Leaf)) {
        Write-Left $stateName 'no-worker-record'
        continue
    }
    try { $workerRecord = [string](Get-Content -LiteralPath $workerRootsPath -First 1 -ErrorAction Stop) } catch { $workerRecord = '' }
    if (-not $workerRecord) {
        Write-Left $stateName 'no-worker-record'
        continue
    }
    $workerParts = $workerRecord.Split([char]9)
    if ($workerParts.Count -lt 3) {
        # The legacy two-field PID/token format has no namespace.
        Write-Left $stateName 'unknown-identity'
        continue
    }

    $workerScheme = [string]$workerParts[0]
    $workerPidText = ''
    $workerStart = ''
    $workerInvalid = $false
    $workerForeign = $false
    switch ($workerScheme) {
        'win' {
            if ($workerParts.Count -ne 3) {
                $workerInvalid = $true
            } else {
                $workerPidText = [string]$workerParts[1]
                $workerStart = [string]$workerParts[2]
            }
        }
        'msys' {
            if ($workerParts.Count -ne 5 -or
                $workerParts[1] -notmatch '^\d+$' -or
                $workerParts[2] -notmatch '^\d+$') {
                $workerInvalid = $true
            } else {
                $workerPidText = [string]$workerParts[3]
                $workerStart = [string]$workerParts[4]
            }
        }
        default {
            $workerForeign = $true
        }
    }
    if ($workerForeign) {
        Write-Left $stateName 'foreign-scheme'
        continue
    }
    if ($workerInvalid) {
        Write-Left $stateName 'unknown-identity'
        continue
    }
    if ($workerPidText -notmatch '^\d+$' -or $workerStart -notmatch '^\d+$') {
        Write-Left $stateName 'unknown-identity'
        continue
    }
    try { $workerPid = [int]$workerPidText } catch {
        Write-Left $stateName 'unknown-identity'
        continue
    }

    $dispatchRootsPath = [System.IO.Path]::Combine([string]$stateDir, 'dispatch-roots')
    if (-not (Test-Path -LiteralPath $dispatchRootsPath -PathType Leaf)) {
        Write-Left $stateName 'unknown-identity'
        continue
    }
    try { $dispatchRecord = [string](Get-Content -LiteralPath $dispatchRootsPath -First 1 -ErrorAction Stop) } catch { $dispatchRecord = '' }
    $dispatchParts = $dispatchRecord.Split([char]9)
    if ($dispatchParts.Count -lt 3 -or [string]$dispatchParts[0] -ne $workerScheme) {
        Write-Left $stateName 'unknown-identity'
        continue
    }

    $identityDispatchPidText = ''
    $dispatchStart = ''
    if ($workerScheme -eq 'win') {
        if ($dispatchParts.Count -ne 3) {
            Write-Left $stateName 'unknown-identity'
            continue
        }
        $identityDispatchPidText = [string]$dispatchParts[1]
        $dispatchStart = [string]$dispatchParts[2]
        if ($identityDispatchPidText -ne $dispatchPidText) {
            Write-Left $stateName 'unknown-identity'
            continue
        }
    } else {
        if ($dispatchParts.Count -ne 5 -or
            $dispatchParts[1] -notmatch '^\d+$' -or
            $dispatchParts[2] -notmatch '^\d+$' -or
            [string]$dispatchParts[1] -ne $dispatchPidText) {
            Write-Left $stateName 'unknown-identity'
            continue
        }
        $identityDispatchPidText = [string]$dispatchParts[3]
        $dispatchStart = [string]$dispatchParts[4]
    }
    if ($identityDispatchPidText -notmatch '^\d+$' -or $dispatchStart -notmatch '^\d+$') {
        Write-Left $stateName 'unknown-identity'
        continue
    }
    try { $identityDispatchPid = [int]$identityDispatchPidText } catch {
        Write-Left $stateName 'unknown-identity'
        continue
    }

    $dispatcher = Get-Process -Id $identityDispatchPid -ErrorAction SilentlyContinue
    if ($dispatcher) {
        try { $currentDispatchStart = [string]([int64]$dispatcher.StartTime.ToUniversalTime().Ticks) } catch { $currentDispatchStart = '' }
        if (-not $currentDispatchStart) {
            Write-Left $stateName 'unknown-identity'
            continue
        }
        if ($currentDispatchStart -eq $dispatchStart) {
            Write-Left $stateName 'dispatcher-alive'
            continue
        }
    }

    $worker = Get-Process -Id $workerPid -ErrorAction SilentlyContinue
    if (-not $worker) {
        Write-Left $stateName 'worker-exited'
        continue
    }
    try {
        try { $currentStart = [string]([int64]$worker.StartTime.ToUniversalTime().Ticks) } catch { $currentStart = '' }
        if (-not $currentStart) {
            Write-Left $stateName 'unknown-identity'
            continue
        }
        if ($currentStart -ne $workerStart) {
            Write-Left $stateName 'identity-mismatch'
            continue
        }

        if ($DryRun) {
            [Console]::Out.WriteLine("WOULD-REAP $stateName pid=$workerPid")
            $leftCount += 1
            continue
        }

        $reapReasonPath = [System.IO.Path]::Combine([string]$stateDir, 'reap-reason')
        if (-not (Test-Path -LiteralPath $reapReasonPath)) {
            try { [System.IO.File]::WriteAllText($reapReasonPath, "orphan-reap`n", $utf8NoBom) } catch { }
        }

        $retained = New-Object System.Collections.ArrayList
        $seen = @{}
        $depthByPid = @{}
        $enumerationComplete = $true
        try {
            [void]$worker.Handle
            if (-not $worker.HasExited) {
                $seen[[string]$worker.Id] = $true
                $depthByPid[[string]$worker.Id] = 0
                [void]$retained.Add([pscustomobject]@{
                    Process = $worker
                    Depth = 0
                })
            }
        } catch {
            $enumerationComplete = $false
        }

        $killSent = $false
        $treeGone = $false
        $rootExitedWithoutKill = $false
        $maxFixedPointRounds = 32
        $maxRetained = 4096
        $fixedPointDeadline = [DateTime]::UtcNow.AddSeconds(20)
        try {
            if ($retained.Count -eq 0) {
                try {
                    if (-not $worker.HasExited) {
                        $worker.Kill()
                        $killSent = $true
                    }
                } catch { }
                try {
                    if (-not $worker.HasExited) { [void]$worker.WaitForExit(5000) }
                } catch { }
            } else {
                for ($round = 0; $round -lt $maxFixedPointRounds; $round += 1) {
                    if ([DateTime]::UtcNow -ge $fixedPointDeadline) { break }

                    $query = Add-NewRetainedDescendants `
                        $retained $seen $depthByPid $maxRetained
                    if (-not $query.Complete) { $enumerationComplete = $false }

                    $live = @()
                    foreach ($entry in $retained) {
                        try {
                            if (-not $entry.Process.HasExited) { $live += $entry }
                        } catch {
                            $enumerationComplete = $false
                        }
                    }

                    if ($live.Count -gt 0) {
                        if (Stop-RetainedProcessTree $live) { $killSent = $true }
                        $waitDeadline = [DateTime]::UtcNow.AddSeconds(5)
                        if ($waitDeadline -gt $fixedPointDeadline) {
                            $waitDeadline = $fixedPointDeadline
                        }
                        $batchExited = Wait-RetainedProcessTree $live $waitDeadline
                        if (-not $batchExited) { break }
                        continue
                    }

                    if ($query.Added -gt 0) {
                        # Even a newly retained process that exited on its own may
                        # have created a child. One more complete query is required.
                        continue
                    }
                    if ($query.Complete -and $enumerationComplete -and
                        (Test-RetainedProcessTreeExited $retained)) {
                        $treeGone = $true
                    }
                    break
                }
            }
            try {
                $rootExitedWithoutKill = (-not $killSent -and $worker.HasExited)
            } catch { }
        } finally {
            foreach ($entry in $retained) {
                if (-not [object]::ReferenceEquals($entry.Process, $worker)) {
                    $entry.Process.Dispose()
                }
            }
        }

        if ($treeGone -and $killSent) {
            [Console]::Out.WriteLine("REAPED $stateName pid=$workerPid")
            $reapedCount += 1
        } elseif ($treeGone) {
            Write-Left $stateName 'worker-exited'
        } elseif ($rootExitedWithoutKill) {
            Write-Left $stateName 'worker-exited'
        } else {
            Write-Left $stateName 'kill-failed'
        }
    } finally {
        $worker.Dispose()
    }
}

[Console]::Out.WriteLine("REAP-DONE reaped=$reapedCount left=$leftCount")
exit 0
