[CmdletBinding()]
param(
    [string]$Version,
    [string]$ProductName = "local-toastd",
    [string]$FileDescription = "Local HTTP toast notification daemon powered by PySide6 and Flask.",
    [string]$CompanyName = "local-toastd"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$pyprojectPath = Join-Path $repoRoot "pyproject.toml"
$outputDir = Join-Path $repoRoot "build\nuitka"
$iconPath = Join-Path $repoRoot "icons\icon.ico"
$entryPoint = Join-Path $repoRoot "src\run_local_toastd.py"
$pythonPath = Join-Path $repoRoot ".venv\Scripts\python.exe"
$distSource = Join-Path $outputDir "run_local_toastd.dist"
$distTarget = Join-Path $outputDir "local-toastd.dist"

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

function ConvertTo-WindowsVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$InputVersion
    )

    if ($InputVersion -notmatch '^\d+(\.\d+){1,3}$') {
        throw "Version '$InputVersion' must use numeric dot-separated segments, for example 1.2.3 or 1.2.3.4."
    }

    return $InputVersion
}

if (-not $Version) {
    $Version = Get-ProjectVersion -Path $pyprojectPath
}

$windowsVersion = ConvertTo-WindowsVersion -InputVersion $Version

if (-not (Test-Path -LiteralPath $iconPath)) {
    throw "Icon file not found: $iconPath"
}

if (-not (Test-Path -LiteralPath $entryPoint)) {
    throw "Entrypoint not found: $entryPoint"
}

if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Project virtualenv not found. Run 'uv sync --extra dev' first."
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

Write-Host "Building $ProductName $Version"

& "$pythonPath" -m nuitka `
    --standalone `
    --assume-yes-for-downloads `
    --enable-plugin=pyside6 `
    --include-package-data=local_toastd `
    --windows-console-mode=disable `
    --windows-icon-from-ico="$iconPath" `
    --company-name="$CompanyName" `
    --product-name="$ProductName" `
    --file-description="$FileDescription" `
    --file-version="$windowsVersion" `
    --product-version="$windowsVersion" `
    --output-dir="$outputDir" `
    --output-filename="local-toastd.exe" `
    "$entryPoint"

if ($LASTEXITCODE -ne 0) {
    throw "Nuitka build failed with exit code $LASTEXITCODE."
}

if (Test-Path -LiteralPath $distTarget) {
    Remove-Item -LiteralPath $distTarget -Recurse -Force
}

if (Test-Path -LiteralPath $distSource) {
    Move-Item -LiteralPath $distSource -Destination $distTarget
}

Write-Host "Built $ProductName $Version to $distTarget"
