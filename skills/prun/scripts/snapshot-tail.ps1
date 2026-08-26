# Thin launcher for `prun_state.py snapshot-tail`.
#
# Writes exactly one artifact, to a durable per-user location, and never
# replaces an existing one. It does not modify the unit it reads from.
[CmdletBinding()]
param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path

function Test-UsablePython {
    param([string]$Candidate)
    # The Windows Store alias exits 9009 without running anything; see
    # AGENTS.md Environment Notes.
    if ($Candidate -match 'WindowsApps') { return $false }
    try {
        & $Candidate -I -c 'import sys; sys.exit(0)' 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch { return $false }
}

function Resolve-Python {
    $explicit = if ($env:PRUN_PYTHON) { $env:PRUN_PYTHON } else { $env:ANYWHERE_AGENTS_PYTHON }
    if ($explicit) {
        if (Test-UsablePython $explicit) { return $explicit }
        # Write-Error terminates under $ErrorActionPreference = 'Stop', so this
        # died with exit 1 and never reached the exit 2 below. The bash launcher
        # returns 2 for the same input, and the two contracts have to agree.
        [Console]::Error.WriteLine("snapshot-tail: PRUN_PYTHON/ANYWHERE_AGENTS_PYTHON is not usable: $explicit")
        return $null
    }
    foreach ($name in @('python3', 'python')) {
        $found = Get-Command -Name $name -CommandType Application -ErrorAction SilentlyContinue
        foreach ($c in @($found)) {
            if ($c -and (Test-UsablePython $c.Source)) { return $c.Source }
        }
    }
    return $null
}

$python = Resolve-Python
if (-not $python) {
    [Console]::Error.WriteLine('snapshot-tail: no usable Python interpreter found. Set PRUN_PYTHON.')
    exit 2
}

# A caller with $PSNativeCommandUseErrorActionPreference enabled turns any
# nonzero native exit into a terminating error, so the exit line below would
# never run and the documented codes would not reach the caller. Scope it off
# for this invocation only.
$PSNativeCommandUseErrorActionPreference = $false
& $python (Join-Path $here 'prun_state.py') snapshot-tail @Rest
exit $LASTEXITCODE
