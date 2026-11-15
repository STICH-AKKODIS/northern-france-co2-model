param([switch]$NoBrowser)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$environmentPath = Join-Path $PSScriptRoot ".venv"
$environmentPython = Join-Path $environmentPath "Scripts\python.exe"
$requirementsFile = Join-Path $PSScriptRoot "requirements.txt"
$applicationFile = Join-Path $PSScriptRoot "ui\app.py"

if (-not (Test-Path -LiteralPath $environmentPython)) {
    Write-Host "Preparing the CO2 model for first use..." -ForegroundColor Cyan
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $pythonCommand) {
        throw "Python 3.11 or newer is required. Install Python, then double-click START_MODEL.bat again."
    }
    & $pythonCommand.Source -m venv $environmentPath
}

$savedErrorPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $environmentPython -c "import streamlit, pandas, plotly, matplotlib, networkx, numpy" 2>$null
$componentsAvailable = $LASTEXITCODE -eq 0
$ErrorActionPreference = $savedErrorPreference
if (-not $componentsAvailable) {
    Write-Host "Installing the model interface (first launch only)..." -ForegroundColor Cyan
    & $environmentPython -m pip install --disable-pip-version-check --quiet --upgrade pip
    & $environmentPython -m pip install --disable-pip-version-check --quiet -r $requirementsFile
    if ($LASTEXITCODE -ne 0) {
        throw "The required model components could not be installed. Check the internet connection and try again."
    }
}

Write-Host "Opening Northern France CO2 Model v0.8 with connected capture, purification and PR transport..." -ForegroundColor Green
Write-Host "Close this window when the presentation is finished." -ForegroundColor DarkGray
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"
$dashboardUrl = "http://localhost:8501"
$browserJob = $null
if (-not $NoBrowser) {
    $browserJob = Start-Job -ScriptBlock {
        param($Url)
        for ($attempt = 0; $attempt -lt 60; $attempt++) {
            try {
                $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 1
                if ($response.StatusCode -eq 200) {
                    Start-Process $Url
                    return
                }
            }
            catch {
                Start-Sleep -Milliseconds 500
            }
        }
    } -ArgumentList $dashboardUrl
}

try {
    & $environmentPython -m streamlit run $applicationFile --server.address localhost --server.port 8501 --server.headless true --browser.gatherUsageStats false
}
finally {
    if ($null -ne $browserJob) {
        Stop-Job -Job $browserJob -ErrorAction SilentlyContinue
        Remove-Job -Job $browserJob -Force -ErrorAction SilentlyContinue
    }
}
