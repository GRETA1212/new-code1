# N GEO Local JARVIS Starter

This starter runs **Open Interpreter + Ollama + CodeLlama locally on Windows**.

- No OpenAI API key
- No paid API tokens
- Model runs on your PC
- Commands require approval because `auto_run` is disabled
- Initial workspace: `C:\N_GEO_JARVIS\workspace`

## Important

This is a local-model agent. The brain is CodeLlama running through Ollama, not the GPT-5.5 model in your normal ChatGPT conversation.

Open Interpreter can generate and run commands. Start only with disposable files in the workspace. Do not point it at your whole C: drive, original survey jobs, passwords, digital signatures, or banking folders.

## Installation

1. Download or clone this repository.
2. Right-click `install-ngeo-jarvis.ps1`.
3. Choose **Run with PowerShell**.

If Windows blocks the script, open PowerShell in the repository folder and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install-ngeo-jarvis.ps1
```

The installer:

- checks for Python 3.11
- installs Ollama if needed
- creates `C:\N_GEO_JARVIS`
- creates a Python virtual environment
- installs Open Interpreter, pyproj, and pandas
- downloads `codellama:7b-instruct`
- copies the safe launcher and test workspace

## Start

Use the desktop shortcut **N GEO Local JARVIS**, or run:

```powershell
C:\N_GEO_JARVIS\start-ngeo-jarvis.ps1
```

## First test

Inside JARVIS, paste:

```text
Work only in the current workspace. Open loc.txt, show me its contents, and propose changing line 3 to apple. Do not change anything until I approve.
```

After approval, verify:

```powershell
Get-Content C:\N_GEO_JARVIS\workspace\loc.txt
```

Expected final content:

```text
line one
line two
apple
line four
```

## Coordinate transformation utility

A guarded transformation utility is included:

```powershell
C:\N_GEO_JARVIS\.venv\Scripts\python.exe `
  C:\N_GEO_JARVIS\tools\transform_coordinates.py `
  --input C:\N_GEO_JARVIS\workspace\points.csv `
  --output C:\N_GEO_JARVIS\workspace\points_transformed.csv `
  --source-epsg 4326 `
  --target-epsg 6316
```

This is only an example. For Leica or cadastral work, use the exact approved source CRS, target CRS, transformation parameters, axis order, and control points. Never guess them.

## Change model later

CodeLlama works for the first test, but it is an older model. To try another local model:

```powershell
ollama pull qwen3:8b
```

Then edit this line in `C:\N_GEO_JARVIS\jarvis.py`:

```python
MODEL = "ollama/qwen3:8b"
```
