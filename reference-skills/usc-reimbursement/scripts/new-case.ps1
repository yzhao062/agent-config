param(
    [Parameter(Mandatory = $true)]
    [string]$CaseId,

    [string]$Title = "Untitled reimbursement case",
    [string]$Requester = "unknown",
    [string]$Department = "unknown",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Replace-TemplateTokens {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [hashtable]$Tokens
    )

    $content = Get-Content -Path $Path -Raw
    foreach ($key in $Tokens.Keys) {
        $content = $content.Replace("{{${key}}}", $Tokens[$key])
    }
    Set-Content -Path $Path -Value $content -NoNewline
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillRoot = Split-Path -Parent $scriptDir
$repoRoot = Split-Path -Parent (Split-Path -Parent $skillRoot)
$templateDir = Join-Path $skillRoot "assets\\case-template"
$casesRoot = Join-Path $repoRoot "cases"
$caseDir = Join-Path $casesRoot $CaseId
$createdAt = Get-Date -Format "yyyy-MM-dd"

$tokens = @{
    "CASE_ID" = $CaseId
    "TITLE" = $Title
    "REQUESTER" = $Requester
    "DEPARTMENT" = $Department
    "CREATED_AT" = $createdAt
}

if (-not (Test-Path -Path $templateDir)) {
    throw "Template directory not found: $templateDir"
}

if (Test-Path -Path $caseDir) {
    throw "Case directory already exists: $caseDir"
}

if ($DryRun) {
    Write-Output "Dry run only."
    Write-Output "Template: $templateDir"
    Write-Output "Destination: $caseDir"
    Write-Output "Tokens:"
    $tokens.GetEnumerator() | Sort-Object Name | ForEach-Object {
        Write-Output ("  {0}={1}" -f $_.Name, $_.Value)
    }
    exit 0
}

New-Item -ItemType Directory -Path $casesRoot -Force | Out-Null
Copy-Item -Path $templateDir -Destination $caseDir -Recurse

Get-ChildItem -Path $caseDir -Recurse -File |
    Where-Object { $_.Extension -in @(".md", ".txt") } |
    ForEach-Object {
        Replace-TemplateTokens -Path $_.FullName -Tokens $tokens
    }

Write-Output "Created case: $caseDir"
