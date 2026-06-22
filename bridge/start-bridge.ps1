$ErrorActionPreference = "Stop"

$Bridge = Join-Path $PSScriptRoot "jarvis_bridge.py"
$PythonCandidates = @(
    "C:\N_GEO_JARVIS\.venv\Scripts\python.exe",
    "python"
)

$Python = $null
foreach ($Candidate in $PythonCandidates) {
    if ($Candidate -eq "python") {
        $Command = Get-Command python -ErrorAction SilentlyContinue
        if ($Command) {
            $Python = $Command.Source
            break
        }
    } elseif (Test-Path $Candidate) {
        $Python = $Candidate
        break
    }
}

if (-not $Python) {
    throw "Python was not found. Expected C:\N_GEO_JARVIS\.venv\Scripts\python.exe or python in PATH."
}

if (-not (Test-Path $Bridge)) {
    throw "Bridge file was not found: $Bridge"
}

Write-Host "Starting N GEO Local GitHub Bridge..."
Write-Host "Python: $Python"
Write-Host "Bridge: $Bridge"
Write-Host "Press Ctrl+C to stop."

& $Python $Bridge
exit $LASTEXITCODE
