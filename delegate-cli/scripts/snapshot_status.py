#!/usr/bin/env python3
"""Capture git working-tree state before or after delegated CLI work."""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def _git(repo: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )


def snapshot(repo: str | Path = ".") -> dict[str, Any]:
    repo_path = Path(repo).resolve()
    inside = _git(repo_path, ["rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return {
            "repo": str(repo_path),
            "is_git_repo": False,
            "branch": None,
            "status_short": "",
            "diff_stat": "",
            "error": inside.stderr.strip(),
        }

    branch = _git(repo_path, ["branch", "--show-current"])
    if branch.stdout.strip():
        branch_name = branch.stdout.strip()
    else:
        head = _git(repo_path, ["rev-parse", "--short", "HEAD"])
        branch_name = f"detached:{head.stdout.strip()}" if head.returncode == 0 else "detached"

    status = _git(repo_path, ["status", "--short"])
    diff_stat = _git(repo_path, ["diff", "--stat"])
    return {
        "repo": str(repo_path),
        "is_git_repo": True,
        "branch": branch_name,
        "status_short": status.stdout,
        "diff_stat": diff_stat.stdout,
        "status_exit_code": status.returncode,
        "diff_stat_exit_code": diff_stat.returncode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit a JSON snapshot of git working-tree state.")
    parser.add_argument("repo", nargs="?", default=".", help="Repository path to inspect")
    parser.add_argument("--output", help="Optional path to write the JSON snapshot")
    args = parser.parse_args()

    report = snapshot(args.repo)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["is_git_repo"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
