from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO = os.environ.get("JARVIS_GITHUB_REPO", "GRETA1212/new-code1")
AUTHORIZED_USER = os.environ.get("JARVIS_GITHUB_USER", "GRETA1212")
WORKSPACE = Path(os.environ.get("JARVIS_WORKSPACE", r"C:\N_GEO_JARVIS\workspace")).resolve()
MODEL = os.environ.get("JARVIS_MODEL", "qwen2.5-coder:3b")
POLL_SECONDS = int(os.environ.get("JARVIS_POLL_SECONDS", "10"))
STATE_FILE = WORKSPACE / ".jarvis_bridge_state.json"
TITLE_PREFIX = "[JARVIS-TASK]"
MAX_OUTPUT_CHARS = 20000


def run_checked(command: list[str], *, cwd: Path | None = None, timeout: int = 30) -> str:
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "Unknown command error").strip()
        raise RuntimeError(detail)
    return completed.stdout.strip()


def ensure_ready() -> None:
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    try:
        run_checked(["gh", "--version"])
    except (FileNotFoundError, RuntimeError) as exc:
        raise RuntimeError("GitHub CLI is not installed or not available in PATH.") from exc
    try:
        run_checked(["gh", "auth", "status"], timeout=20)
    except RuntimeError as exc:
        raise RuntimeError("GitHub CLI is not authenticated. Run: gh auth login") from exc


def load_state() -> set[int]:
    if not STATE_FILE.exists():
        return set()
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return {int(value) for value in data.get("processed_issue_numbers", [])}
    except (OSError, ValueError, TypeError):
        return set()


def save_state(processed: set[int]) -> None:
    payload = {"processed_issue_numbers": sorted(processed)}
    STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def fetch_tasks() -> list[dict[str, Any]]:
    raw = run_checked(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            REPO,
            "--state",
            "open",
            "--limit",
            "100",
            "--json",
            "number,title,body,author,url",
        ],
        timeout=30,
    )
    issues = json.loads(raw or "[]")
    tasks: list[dict[str, Any]] = []
    for issue in issues:
        title = str(issue.get("title", ""))
        author = issue.get("author") or {}
        if title.startswith(TITLE_PREFIX) and author.get("login") == AUTHORIZED_USER:
            tasks.append(issue)
    return sorted(tasks, key=lambda item: int(item["number"]))


def parse_task(body: str) -> dict[str, str]:
    task: dict[str, str] = {}
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        task[key.strip().upper()] = value.strip()
    return task


def safe_path(value: str | None) -> Path:
    candidate = (WORKSPACE / (value or ".")).resolve()
    try:
        candidate.relative_to(WORKSPACE)
    except ValueError as exc:
        raise ValueError(f"Path is outside the authorized workspace: {candidate}") from exc
    return candidate


def action_list_directory(task: dict[str, str]) -> str:
    target = safe_path(task.get("PATH"))
    if not target.is_dir():
        raise ValueError(f"Directory does not exist: {target}")
    rows = []
    for item in sorted(target.iterdir(), key=lambda path: (not path.is_dir(), path.name.lower())):
        kind = "DIR " if item.is_dir() else "FILE"
        rows.append(f"{kind}  {item.name}")
    return f"Directory: {target}\n" + ("\n".join(rows) if rows else "(empty)")


def action_read_file(task: dict[str, str]) -> str:
    if not task.get("PATH"):
        raise ValueError("PATH is required for read_file.")
    target = safe_path(task["PATH"])
    if not target.is_file():
        raise ValueError(f"File does not exist: {target}")
    content = target.read_text(encoding="utf-8", errors="replace")
    if len(content) > MAX_OUTPUT_CHARS:
        content = content[:MAX_OUTPUT_CHARS] + "\n...[truncated]"
    return f"File: {target}\n\n{content}"


def action_git_status(task: dict[str, str]) -> str:
    target = safe_path(task.get("PATH"))
    if not target.is_dir():
        raise ValueError(f"Directory does not exist: {target}")
    output = run_checked(["git", "status", "--short", "--branch"], cwd=target, timeout=30)
    return f"Repository: {target}\n{output or '(clean)'}"


def action_check_port(task: dict[str, str]) -> str:
    raw_port = task.get("PORT")
    if not raw_port or not raw_port.isdigit():
        raise ValueError("PORT must be an integer.")
    port = int(raw_port)
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535.")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.5)
        open_now = sock.connect_ex(("127.0.0.1", port)) == 0
    return f"127.0.0.1:{port} is {'OPEN' if open_now else 'CLOSED'}"


def action_ask_ollama(task: dict[str, str]) -> str:
    prompt = task.get("PROMPT", "").strip()
    if not prompt:
        raise ValueError("PROMPT is required for ask_ollama.")
    payload = json.dumps(
        {
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "num_ctx": 4096},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach local Ollama: {exc}") from exc
    return str(data.get("response", "")).strip() or "(Ollama returned no text)"


ACTIONS = {
    "list_directory": action_list_directory,
    "read_file": action_read_file,
    "git_status": action_git_status,
    "check_port": action_check_port,
    "ask_ollama": action_ask_ollama,
}


def post_result(issue_number: int, action: str, status: str, output: str) -> None:
    safe_output = output[:MAX_OUTPUT_CHARS]
    body = (
        "## N GEO Local Bridge Result\n\n"
        f"- Status: **{status}**\n"
        f"- Action: `{action}`\n"
        f"- Computer: `{socket.gethostname()}`\n"
        f"- Workspace: `{WORKSPACE}`\n\n"
        "```text\n"
        f"{safe_output}\n"
        "```"
    )
    run_checked(
        ["gh", "issue", "comment", str(issue_number), "--repo", REPO, "--body", body],
        timeout=30,
    )
    run_checked(
        ["gh", "issue", "close", str(issue_number), "--repo", REPO, "--reason", "completed"],
        timeout=30,
    )


def process_once(processed: set[int]) -> int:
    handled = 0
    for issue in fetch_tasks():
        number = int(issue["number"])
        if number in processed:
            continue
        task = parse_task(str(issue.get("body", "")))
        action = task.get("ACTION", "").lower()
        print(f"Processing issue #{number}: {issue.get('title')}")
        try:
            handler = ACTIONS.get(action)
            if handler is None:
                allowed = ", ".join(sorted(ACTIONS))
                raise ValueError(f"Unsupported ACTION '{action}'. Allowed: {allowed}")
            output = handler(task)
            post_result(number, action, "SUCCESS", output)
            print(f"Completed issue #{number}")
        except Exception as exc:  # keep the bridge alive and report the failure
            message = f"{type(exc).__name__}: {exc}"
            try:
                post_result(number, action or "missing", "FAILED", message)
            except Exception as post_exc:
                print(f"Could not post failure for issue #{number}: {post_exc}", file=sys.stderr)
            print(f"Failed issue #{number}: {message}", file=sys.stderr)
        processed.add(number)
        save_state(processed)
        handled += 1
    return handled


def main() -> int:
    parser = argparse.ArgumentParser(description="Safe GitHub task bridge for N GEO Local JARVIS")
    parser.add_argument("--once", action="store_true", help="Check once and exit")
    args = parser.parse_args()

    try:
        ensure_ready()
    except RuntimeError as exc:
        print(f"Bridge setup error: {exc}", file=sys.stderr)
        return 1

    processed = load_state()
    print("N GEO Local GitHub Bridge")
    print(f"Repository: {REPO}")
    print(f"Authorized user: {AUTHORIZED_USER}")
    print(f"Workspace: {WORKSPACE}")
    print(f"Model: {MODEL}")
    print("Allowed actions: " + ", ".join(sorted(ACTIONS)))

    if args.once:
        count = process_once(processed)
        print(f"Processed {count} task(s).")
        return 0

    print(f"Polling every {POLL_SECONDS} seconds. Press Ctrl+C to stop.")
    try:
        while True:
            process_once(processed)
            time.sleep(POLL_SECONDS)
    except KeyboardInterrupt:
        print("\nBridge stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
