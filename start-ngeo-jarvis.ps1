$ErrorActionPreference = "Stop"
$InstallDir = "C:\N_GEO_JARVIS"
$Python = "$InstallDir\.venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "JARVIS is not installed. Run install-ngeo-jarvis.ps1 first."
}

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    $env:Path += ";$env:LOCALAPPDATA\Programs\Ollama"
}

try {
    ollama list | Out-Null
} catch {
    throw "Ollama is not running. Open Ollama from the Start menu, then try again."
}

Set-Location "$InstallDir\workspace"
& $Python "$InstallDir\jarvis.py"
