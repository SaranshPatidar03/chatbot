# Pack the Knowledge Chatbot project into chatbot.zip (source only, no secrets/deps).
# Usage: powershell -ExecutionPolicy Bypass -File scripts/pack-chatbot-zip.ps1 [-Force]
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$OutputZip = Join-Path $ProjectRoot "chatbot.zip"
$DebounceFile = Join-Path $ProjectRoot ".cursor\.last-zip-pack"
$DebounceSeconds = 20

if (-not $Force -and (Test-Path $DebounceFile)) {
    $last = [datetime]::Parse((Get-Content $DebounceFile -Raw))
    if (((Get-Date) - $last).TotalSeconds -lt $DebounceSeconds) {
        exit 0
    }
}

$TempZip = "$OutputZip.tmp"
if (Test-Path $TempZip) { Remove-Item $TempZip -Force }

$excludes = @(
    "--exclude=node_modules",
    "--exclude=frontend/node_modules",
    "--exclude=.venv",
    "--exclude=venv",
    "--exclude=__pycache__",
    "--exclude=.pytest_cache",
    "--exclude=frontend/dist",
    "--exclude=frontend/.vite",
    "--exclude=.env",
    "--exclude=.env.local",
    "--exclude=storage/uploads",
    "--exclude=backend/storage/uploads",
    "--exclude=backend/storage/temp",
    "--exclude=chroma_data",
    "--exclude=postgres_data",
    "--exclude=redis_data",
    "--exclude=docker/certs",
    "--exclude=frontend/playwright-report",
    "--exclude=frontend/test-results",
    "--exclude=.git",
    "--exclude=chatbot.zip",
    "--exclude=*.zip"
)

Push-Location $ProjectRoot
try {
    $tarArgs = @("-a", "-cf", $TempZip) + $excludes + @(".")
    & tar @tarArgs
    if ($LASTEXITCODE -ne 0) { throw "tar failed with exit code $LASTEXITCODE" }

    if (Test-Path $OutputZip) { Remove-Item $OutputZip -Force }
    Move-Item $TempZip $OutputZip -Force

    $sizeMb = [math]::Round((Get-Item $OutputZip).Length / 1MB, 2)
    $stampDir = Split-Path $DebounceFile -Parent
    if (-not (Test-Path $stampDir)) { New-Item -ItemType Directory -Path $stampDir -Force | Out-Null }
    Set-Content -Path $DebounceFile -Value (Get-Date).ToString("o") -NoNewline

    Write-Host "Packed chatbot.zip ($sizeMb MB) at $OutputZip"
}
finally {
    Pop-Location
    if (Test-Path $TempZip) { Remove-Item $TempZip -Force -ErrorAction SilentlyContinue }
}
