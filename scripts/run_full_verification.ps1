param(
    [string]$Python = "python",
    [string]$PapaReferenceRoot = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    if ($PapaReferenceRoot) {
        $env:PAPA_REFERENCE_ROOT = $PapaReferenceRoot
    }

    & $Python -m compileall -q src ui scripts
    if ($LASTEXITCODE -ne 0) { throw "Python compilation failed." }

    & $Python scripts/run_papa_reference.py
    if ($LASTEXITCODE -ne 0) { throw "Papa reference execution failed." }

    & $Python scripts/compare_papa_models.py
    if ($LASTEXITCODE -ne 0) { throw "Matched-input comparison failed." }

    & $Python run_model.py --all-scenarios --output-dir verification/process_linked
    if ($LASTEXITCODE -ne 0) { throw "Scenario generation failed." }

    $env:PYTHONPATH = "src"
    & $Python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "Automated tests failed." }

    & $Python scripts/compare_release_outputs.py
    if ($LASTEXITCODE -ne 0) { throw "Release comparison failed." }

    Write-Host "Verification complete. Open verification/VERIFICATION_REPORT.md"
}
finally {
    Pop-Location
}
