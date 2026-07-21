$ErrorActionPreference = "Stop"

Write-Host "Installing Project RISING Phase 3..."

if (-not (Test-Path "requirements.txt")) {
    throw "Run this script while your terminal is inside the Project-Rising repository root."
}

$PatchRoot = (Resolve-Path (Split-Path -Parent $MyInvocation.MyCommand.Path)).Path
$RepositoryRoot = (Resolve-Path ".").Path

if ($PatchRoot -ne $RepositoryRoot) {
    Copy-Item "$PatchRoot\api" "." -Recurse -Force
    Copy-Item "$PatchRoot\main.py" ".\main.py" -Force
    Copy-Item "$PatchRoot\tests\test_phase3_api.py" ".\tests\test_phase3_api.py" -Force
    Copy-Item "$PatchRoot\PHASE3_SETUP.md" ".\PHASE3_SETUP.md" -Force
    Copy-Item "$PatchRoot\README_PHASE3_SECTION.md" ".\README_PHASE3_SECTION.md" -Force
} else {
    Write-Host "Phase 3 files are already located in the repository root."
}

Write-Host "Running tests..."
py -m pytest

Write-Host "Done. Start the API with: py -m uvicorn main:app --reload"
