# N GEO Local GitHub Bridge

This bridge lets approved GitHub issues trigger a small set of safe actions on the local Windows PC.

It does not accept arbitrary shell commands.

Security rules:

- Only issues whose title starts with `[JARVIS-TASK]` are considered.
- Only issues created by GitHub user `GRETA1212` are accepted.
- File actions are restricted to `C:\N_GEO_JARVIS\workspace`.
- Allowed actions are `list_directory`, `read_file`, `git_status`, `check_port`, and `ask_ollama`.
- Results are posted back to the issue and the issue is closed.
- No delete, install, commit, push, email, password, banking, or Windows-security action is implemented.

The repository is currently public. Use only harmless test tasks here. Never place secrets, credentials, client data, cadastral owner data, or private project content in issues.

## Update the local starter

Run in normal PowerShell:

```powershell
Set-Location "C:\Users\ddpcj\Desktop\ngeo-local-jarvis"
git pull --ff-only origin main
```

## Run one test cycle

```powershell
& "C:\N_GEO_JARVIS\.venv\Scripts\python.exe" ".\bridge\jarvis_bridge.py" --once
```

The test issue body is:

```text
ACTION: list_directory
PATH: .
```

The bridge lists the top-level contents of `C:\N_GEO_JARVIS\workspace`, posts the result to the issue, and closes it.

## Run continuously

```powershell
powershell -ExecutionPolicy Bypass -File ".\bridge\start-bridge.ps1"
```

Leave that PowerShell window open. The bridge checks every 10 seconds.
