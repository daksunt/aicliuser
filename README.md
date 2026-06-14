# delegate-cli

A generic, auditable protocol that lets any AI host agent or CLI discover and delegate bounded work to other model-powered CLIs. This repo currently packages it as a Codex-compatible skill.

`delegate-cli` lets a host agent scan the local machine for installed coding CLIs, require the user to choose which one(s) to use, delegate bounded implementation or review work, capture transcripts, and verify changes before trusting the result.

The host agent can be Codex or any assistant that can run local commands. Delegated CLIs can include tools such as Codex, Claude Code, Cursor Agent, Gemini CLI, or another command discovered at runtime.

## Why this exists

Modern coding agents are good at different things. Instead of hard-coding one assistant, this protocol gives the host agent a repeatable way to find available CLIs and use them as collaborators while preserving accountability in the main session.

The core rule: external CLIs can help, but their output is untrusted until the host agent reviews diffs and verifies results.

## What it does

- Scans common model/agent CLI names on `PATH`.
- Captures `--version` and `--help` output for each discovered tool.
- Infers basic capabilities such as noninteractive mode, print/json output, and review support.
- Requires the user to select which discovered CLI(s) to use before delegation, unless the request already names the CLI.
- Captures pre/post git state for delegated runs.
- Runs bounded delegation commands with transcript capture and timeout handling.
- Supports implementation, research, debugging, stuck-task escalation, and independent code review workflows.

## Packaging

The reusable part is the protocol: discover, choose, bound, delegate, capture, verify. The repo ships that protocol as a Codex-compatible skill because Codex can load `SKILL.md` folders directly.

Other hosts can still use the host-agnostic pieces:

- `delegate-cli/SKILL.md` for the workflow.
- `delegate-cli/references/delegation-prompts.md` for prompt templates.
- `delegate-cli/scripts/discover_cli.py` for local CLI discovery.
- `delegate-cli/scripts/run_delegation.py` for transcript capture.
- `delegate-cli/scripts/snapshot_status.py` for pre/post git state.

## Install in Codex

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
```

Validate the skill if you have Codex's skill-creator utilities installed:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py delegate-cli
```

Use it in Codex after installation:

```text
Use delegate-cli to discover available model CLIs, ask me to select which one(s) to use, then run a review.
```

## Permission model

Delegation crosses permission boundaries, so the host agent should be explicit about what kind of action it is taking.

- Local discovery: inspecting `PATH`, `--version`, and `--help` is local-only and usually safe.
- Local execution: running helper scripts or tests may require sandbox approval in restricted environments.
- External delegation: sending repo content to Claude, Cursor, Gemini, or another cloud-backed CLI may disclose code to a third party. Ask for explicit user approval unless the user has already opted in.
- Direct edits: delegated CLIs may edit the working tree only when the task allows it; always capture pre/post git state and review diffs.
- Destructive or credential-sensitive work: never delegate secrets, production access, resets, deletes, deploys, or broad filesystem authority without explicit approval.

If a host sandbox blocks a helper script, run the equivalent manual commands and keep the same evidence trail.

## Safety model

Delegation is useful, but it is not trust transfer.

Before delegated work, the skill captures the repo state. After delegated work, the host agent must inspect `git status`, review diffs, run relevant tests, and summarize what was accepted or rejected.

The skill tells agents not to delegate secrets, credentials, destructive commands, production changes, or broad filesystem authority without explicit user approval.

## Included scripts

- `delegate-cli/scripts/discover_cli.py`: scan or inspect installed model/agent CLIs.
- `delegate-cli/scripts/run_delegation.py`: run a bounded command and write a JSON transcript.
- `delegate-cli/scripts/snapshot_status.py`: capture branch, short status, and diff stats.

## Public status

This is an early protocol prototype. The useful launch angle is not that it automates every CLI perfectly; it is that it gives agents a generic, auditable handoff protocol for using other agents.
