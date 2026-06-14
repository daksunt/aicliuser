#!/usr/bin/env python3
"""Run a bounded external CLI delegation and capture a transcript."""

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Sequence


def run_delegation(
    command: Sequence[str],
    cwd: str | Path,
    transcript_path: str | Path,
    timeout_seconds: float,
) -> dict[str, Any]:
    started_at = time.time()
    cwd_path = Path(cwd).resolve()
    transcript = Path(transcript_path)
    transcript.parent.mkdir(parents=True, exist_ok=True)

    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd_path,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        result = {
            "command": list(command),
            "cwd": str(cwd_path),
            "exit_code": completed.returncode,
            "timed_out": False,
            "duration_seconds": round(time.time() - started_at, 3),
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        result = {
            "command": list(command),
            "cwd": str(cwd_path),
            "exit_code": None,
            "timed_out": True,
            "duration_seconds": round(time.time() - started_at, 3),
            "stdout": exc.stdout or "",
            "stderr": f"Command timed out after {timeout_seconds} seconds",
        }

    transcript.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a delegated CLI command and write a JSON transcript.")
    parser.add_argument("--cwd", default=".", help="Working directory for the delegated command")
    parser.add_argument("--transcript", required=True, help="Path to write the transcript JSON")
    parser.add_argument("--timeout", type=float, default=900, help="Seconds before terminating the command")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command to run after --")
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("provide a command after --")

    result = run_delegation(command, cwd=args.cwd, transcript_path=args.transcript, timeout_seconds=args.timeout)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["timed_out"]:
        return 124
    return int(result["exit_code"] or 0)


if __name__ == "__main__":
    raise SystemExit(main())
