$ErrorActionPreference = "Stop"

$InstallDir = "C:\N_GEO_JARVIS"
$PythonExe = $null

Write-Host "=== N GEO Local JARVIS Installer ===" -ForegroundColor Cyan
Write-Host "Installs Ollama, a Python 3.11 environment, Open Interpreter, and CodeLlama." -ForegroundColor Gray

try {
    $PythonExe = (& py -3.11 -c "import sys; print(sys.executable)" 2>$null).Trim()
} catch {}

if (-not $PythonExe) {
    Write-Host "Python 3.11 was not found. Installing it with winget..." -ForegroundColor Yellow
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget is unavailable. Install Python 3.11 manually, then rerun this script."
    }

    winget install --id Python.Python.3.11 -e `
        --accept-package-agreements `
        --accept-source-agreements

    $PythonExe = (& py -3.11 -c "import sys; print(sys.executable)").Trim()
}

Write-Host "Using Python: $PythonExe" -ForegroundColor Green

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "Ollama was not found. Running the official Ollama installer..." -ForegroundColor Yellow
    irm https://ollama.com/install.ps1 | iex
}

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    $env:Path += ";$env:LOCALAPPDATA\Programs\Ollama"
}

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    throw "Ollama installation finished, but the command is not available. Restart PowerShell and rerun this installer."
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
New-Item -ItemType Directory -Force -Path "$InstallDir\workspace" | Out-Null
New-Item -ItemType Directory -Force -Path "$InstallDir\tools" | Out-Null

Write-Host "Creating isolated Python environment..." -ForegroundColor Cyan
& py -3.11 -m venv "$InstallDir\.venv"

$VenvPython = "$InstallDir\.venv\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip wheel setuptools
& $VenvPython -m pip install "open-interpreter[local]" pyproj pandas

Write-Host "Downloading CodeLlama 7B Instruct. This can take some time and several GB of disk space..." -ForegroundColor Cyan
ollama pull codellama:7b-instruct

$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Copy-Item "$SourceDir\jarvis.py" "$InstallDir\jarvis.py" -Force
Copy-Item "$SourceDir\start-ngeo-jarvis.ps1" "$InstallDir\start-ngeo-jarvis.ps1" -Force
Copy-Item "$SourceDir\tools\*" "$InstallDir\tools\" -Recurse -Force
Copy-Item "$SourceDir\workspace\*" "$InstallDir\workspace\" -Recurse -Force
Copy-Item "$SourceDir\README.md" "$InstallDir\README.md" -Force

$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "N GEO Local JARVIS.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$InstallDir\start-ngeo-jarvis.ps1`""
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description = "Open N GEO Local JARVIS"
$Shortcut.Save()

Write-Host ""
Write-Host "Installation completed." -ForegroundColor Green
Write-Host "Start it from the desktop shortcut: N GEO Local JARVIS" -ForegroundColor Green
Write-Host "Workspace: $InstallDir\workspace" -ForegroundColor Gray
Write-Host ""
Write-Host "Keep approval enabled. Test only with the included disposable loc.txt first." -ForegroundColor Yellow
