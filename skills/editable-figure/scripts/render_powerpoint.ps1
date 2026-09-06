[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$InputPptx,
    [Parameter(Mandatory=$true)][string]$OutputBase,
    [ValidateRange(320,7680)][int]$PngWidth = 2400,
    [string]$ReportPath
)

$ErrorActionPreference = 'Stop'

function Get-AbsolutePath([string]$Value, [string]$Label) {
    if (-not [IO.Path]::IsPathRooted($Value)) { throw "$Label must be absolute." }
    return [IO.Path]::GetFullPath($Value)
}

$figureInput = Get-AbsolutePath $InputPptx 'InputPptx'
$figureBase = Get-AbsolutePath $OutputBase 'OutputBase'
if (-not (Test-Path -LiteralPath $figureInput -PathType Leaf)) { throw 'Input PPTX does not exist.' }
if ([IO.Path]::GetExtension($figureInput) -ine '.pptx') { throw 'Input must be a PPTX file.' }
$figurePng = "$figureBase.png"
$figurePdf = "$figureBase.pdf"
$figureTargets = @($figurePng, $figurePdf)
if ($ReportPath) {
    $figureReport = Get-AbsolutePath $ReportPath 'ReportPath'
    $figureTargets += $figureReport
}
# Compare case-insensitively: Select-Object -Unique is case-sensitive on
# strings, while the Windows filesystem is not. Without the fold, figure.pdf
# and FIGURE.PDF pass this guard and both nonexistence checks below, and the
# report JSON then overwrites the exported PDF while the run reports success.
if (@($figureTargets | ForEach-Object { $_.ToUpperInvariant() } | Select-Object -Unique).Count -ne $figureTargets.Count) { throw 'Output paths must be distinct.' }
foreach ($figureTarget in $figureTargets) {
    if ($figureTarget -ieq $figureInput) { throw 'An output path points to the input.' }
    if (Test-Path -LiteralPath $figureTarget) { throw "Output already exists: $figureTarget" }
}

$figureInputHash = (Get-FileHash -LiteralPath $figureInput -Algorithm SHA256).Hash
$figureAppExisted = @(Get-Process -Name POWERPNT -ErrorAction SilentlyContinue).Count -gt 0
$figureApp = $null
$figureDeck = $null
$figureCounts = [ordered]@{groups=0;nativeShapes=0;textObjects=0;connectors=0;charts=0;pictures=0;otherObjects=0}

function Measure-FigureShapes($ShapeCollection) {
    for ($figureIndex=1; $figureIndex -le $ShapeCollection.Count; $figureIndex++) {
        $figureShape = $ShapeCollection.Item($figureIndex)
        if ($figureShape.Type -eq 6) {
            $figureCounts.groups++
            Measure-FigureShapes $figureShape.GroupItems
            continue
        }
        if ($figureShape.Connector -eq -1) {
            $figureCounts.connectors++
        } elseif ($figureShape.HasChart -eq -1) {
            $figureCounts.charts++
        } elseif ($figureShape.Type -in @(11,13)) {
            $figureCounts.pictures++
        } elseif ($figureShape.Type -in @(1,5,9,17)) {
            $figureCounts.nativeShapes++
        } else {
            $figureCounts.otherObjects++
        }
        if ($figureShape.HasTextFrame -eq -1 -and $figureShape.TextFrame.HasText -eq -1) {
            $figureCounts.textObjects++
        }
    }
}

try {
    $figureApp = New-Object -ComObject PowerPoint.Application
    $figureDeck = $figureApp.Presentations.Open($figureInput, $true, $false, $false)
    if ($figureDeck.Slides.Count -ne 1) { throw 'Expected one figure slide; use a deck renderer for multiple slides.' }
    $figureSlide = $figureDeck.Slides.Item(1)
    Measure-FigureShapes $figureSlide.Shapes
    [double]$figureWidth = $figureDeck.PageSetup.SlideWidth
    [double]$figureHeight = $figureDeck.PageSetup.SlideHeight
    [int]$figurePngHeight = [math]::Round($PngWidth * $figureHeight / $figureWidth)
    if ($figurePngHeight -lt 1 -or $figurePngHeight -gt 16000) { throw 'Export height is outside the supported figure range.' }
    foreach ($figureTarget in $figureTargets) {
        New-Item -ItemType Directory -Force -Path ([IO.Path]::GetDirectoryName($figureTarget)) | Out-Null
    }
    $figureSlide.Export($figurePng, 'PNG', $PngWidth, $figurePngHeight)
    $figureDeck.SaveAs($figurePdf, 32)
    if ((Get-FileHash -LiteralPath $figureInput -Algorithm SHA256).Hash -ne $figureInputHash) { throw 'Input PPTX changed during rendering.' }
    foreach ($figureExport in @($figurePng, $figurePdf)) {
        if (-not (Test-Path -LiteralPath $figureExport -PathType Leaf)) { throw "Export missing: $figureExport" }
        if ((Get-Item -LiteralPath $figureExport).Length -eq 0) { throw "Empty export: $figureExport" }
    }
    $figureResult = [ordered]@{
        input=$figureInput
        inputSha256=$figureInputHash
        powerpointVersion=$figureApp.Version
        slideCount=1
        sizePoints=@($figureWidth,$figureHeight)
        pngPixels=@($PngWidth,$figurePngHeight)
        objects=$figureCounts
        png=$figurePng
        pdf=$figurePdf
        editableBehaviorTested=$false
        visualInspectionPerformed=$false
    }
    $figureJson = $figureResult | ConvertTo-Json -Depth 5
    if ($ReportPath) { Set-Content -LiteralPath $figureReport -Value $figureJson -Encoding utf8 }
    Write-Output $figureJson
}
finally {
    if ($null -ne $figureDeck) {
        try { $figureDeck.Close() } finally { [Runtime.InteropServices.Marshal]::ReleaseComObject($figureDeck) | Out-Null }
    }
    if ($null -ne $figureApp) {
        try {
            if (-not $figureAppExisted -and $figureApp.Presentations.Count -eq 0) { $figureApp.Quit() }
        } finally { [Runtime.InteropServices.Marshal]::ReleaseComObject($figureApp) | Out-Null }
    }
}
