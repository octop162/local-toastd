[CmdletBinding()]
param(
    [string]$Version,
    [switch]$SkipChecks
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$buildScript = Join-Path $PSScriptRoot "build.ps1"
$pyprojectPath = Join-Path $repoRoot "pyproject.toml"
$releaseRoot = Join-Path $repoRoot "build\release"
$distDir = Join-Path $repoRoot "build\nuitka\local-toastd.dist"

function Get-ProjectVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $inProjectSection = $false
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -match '^\[project\]$') {
            $inProjectSection = $true
            continue
        }

        if ($inProjectSection -and $line -match '^\[') {
            break
        }

        if ($inProjectSection -and $line -match '^version\s*=\s*"([^"]+)"') {
            return $Matches[1]
        }
    }

    throw "Project version not found in $Path"
}

if (-not $Version) {
    $Version = Get-ProjectVersion -Path $pyprojectPath
}

$releaseName = "local-toastd-$Version-win64"
$releaseDir = Join-Path $releaseRoot $releaseName
$zipPath = Join-Path $releaseRoot "$releaseName.zip"

if (-not $SkipChecks) {
    uv run ruff check .
    if ($LASTEXITCODE -ne 0) {
        throw "ruff check failed with exit code $LASTEXITCODE."
    }

    uv run mypy
    if ($LASTEXITCODE -ne 0) {
        throw "mypy failed with exit code $LASTEXITCODE."
    }

    uv run pytest
    if ($LASTEXITCODE -ne 0) {
        throw "pytest failed with exit code $LASTEXITCODE."
    }
}

& "$buildScript" -Version $Version

if (-not (Test-Path -LiteralPath $distDir)) {
    throw "Built distribution not found: $distDir"
}

if (Test-Path -LiteralPath $releaseDir) {
    Remove-Item -LiteralPath $releaseDir -Recurse -Force
}

if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
Copy-Item -Path (Join-Path $distDir "*") -Destination $releaseDir -Recurse
Copy-Item -LiteralPath (Join-Path $repoRoot "README.md") -Destination (Join-Path $releaseDir "README.md")
Set-Content -LiteralPath (Join-Path $releaseDir "VERSION.txt") -Value $Version -Encoding ascii

Compress-Archive -Path $releaseDir -DestinationPath $zipPath

Write-Host "Release package created:"
Write-Host "  Folder: $releaseDir"
Write-Host "  Zip:    $zipPath"
