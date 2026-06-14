# delegate-cli

A Codex skill for discovering and delegating work to model-powered CLIs.

`delegate-cli` lets a host agent scan the local machine for installed coding CLIs, ask which one to use, delegate bounded implementation or review work, capture transcripts, and verify changes before trusting the result.

The host agent can be Codex or any assistant that can run local commands. The delegated CLI can be Codex, Claude Code, Cursor Agent, Gemini CLI, Aider, Goose, or another command discovered at runtime.

## Why this exists

Modern coding agents are good at different things. Instead of hard-coding one assistant, this skill gives Codex a repeatable protocol for finding available CLIs and using them as collaborators while preserving accountability in the main session.

The core rule: external CLIs can help, but their output is untrusted until the host agent reviews diffs and verifies results.

## What it does

- Scans common model/agent CLI names on `PATH`.
- Captures `--version` and `--help` output for each discovered tool.
- Infers basic capabilities such as noninteractive mode, print/json output, and review support.
- Asks the user which discovered CLI(s) to use when multiple options are available.
- Captures pre/post git state for delegated runs.
- Runs bounded delegation commands with transcript capture and timeout handling.
- Supports implementation, research, debugging, stuck-task escalation, and independent code review workflows.

## Install locally

From this repo:

```bash
mkdir -p ~/.codex/skills
rm -rf ~/.codex/skills/delegate-cli
cp -R delegate-cli ~/.codex/skills/
```

Start a fresh Codex session so the skill registry is reloaded.

## Try it

Discover available CLIs:

```bash
python3 delegate-cli/scripts/discover_cli.py --scan --timeout 5
```

Discover a specific CLI:

```bash
python3 delegate-cli/scripts/discover_cli.py agent --timeout 5
```

Run tests:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_delegate_cli_scripts.py -v
PYTHONDONTWRITEBYTECODE=1 python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py delegate-cli
```

Use it in Codex after installation:

```text
Use delegate-cli to discover available model CLIs and ask me which one to use for a review.
```

## Safety model

Delegation is useful, but it is not trust transfer.

Before delegated work, the skill captures the repo state. After delegated work, the host agent must inspect `git status`, review diffs, run relevant tests, and summarize what was accepted or rejected.

The skill tells agents not to delegate secrets, credentials, destructive commands, production changes, or broad filesystem authority without explicit user approval.

## Included scripts

- `delegate-cli/scripts/discover_cli.py`: scan or inspect installed model/agent CLIs.
- `delegate-cli/scripts/run_delegation.py`: run a bounded command and write a JSON transcript.
- `delegate-cli/scripts/snapshot_status.py`: capture branch, short status, and diff stats.

## Public status

This is an early skill prototype. The useful launch angle is not that it automates every CLI perfectly; it is that it gives agents a generic, auditable handoff protocol for using other agents.
