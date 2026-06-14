#!/usr/bin/env python3
"""Discover basic capabilities for an installed CLI agent."""

import argparse
import json
import shutil
import subprocess
from typing import Any


def _capture(command: list[str], timeout_seconds: float = 10) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return {
            "command": command,
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "exit_code": None,
            "stdout": exc.stdout or "",
            "stderr": f"Command timed out after {timeout_seconds} seconds",
            "timed_out": True,
        }


def _infer_capabilities(help_text: str) -> dict[str, bool]:
    lowered = help_text.lower()
    return {
        "accepts_prompt_flag": any(flag in lowered for flag in ("--prompt", "--message", "--instruction")),
        "supports_print_mode": any(flag in lowered for flag in ("--print", "--output", "--json")),
        "mentions_noninteractive": any(term in lowered for term in ("non-interactive", "noninteractive", "batch")),
        "mentions_review": "review" in lowered,
    }


def discover(name: str, timeout_seconds: float = 10) -> dict[str, Any]:
    path = shutil.which(name)
    if path is None:
        return {
            "name": name,
            "found": False,
            "path": None,
            "version": None,
            "help": None,
            "inferred_capabilities": {},
        }

    version = _capture([path, "--version"], timeout_seconds=timeout_seconds)
    help_report = _capture([path, "--help"], timeout_seconds=timeout_seconds)
    help_text = f"{help_report.get('stdout', '')}\n{help_report.get('stderr', '')}"
    return {
        "name": name,
        "found": True,
        "path": path,
        "version": version,
        "help": help_report,
        "inferred_capabilities": _infer_capabilities(help_text),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover an installed CLI and emit a JSON capability report.")
    parser.add_argument("name", help="CLI command name to discover")
    parser.add_argument("--timeout", type=float, default=10, help="Seconds to allow for each probe")
    parser.add_argument("--output", help="Optional path to write the JSON report")
    args = parser.parse_args()

    report = discover(args.name, timeout_seconds=args.timeout)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        from pathlib import Path

        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["found"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
