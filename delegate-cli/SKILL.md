---
name: delegate-cli
description: Discover, evaluate, and delegate work to any installed external agent CLI. Use when Codex should outsource bounded implementation, research, debugging, stuck-task escalation, or independent code/PR review to tools such as another Codex CLI, Cursor CLI, Claude Code CLI, or any future CLI discovered at runtime.
---

# Delegate CLI

Use external agent CLIs as high-autonomy collaborators while keeping Codex responsible for command choice, safety, diff review, and final verification. Treat every external CLI as discoverable at runtime; do not assume vendor-specific flags until you have inspected the installed command.

## Core Workflow

1. Define the delegation goal in one sentence: implementation, review, research, debugging, or stuck-task escalation.
2. Discover the CLI before using it:
   - Prefer `scripts/discover_cli.py <name>`.
   - If the script is unavailable, run `command -v <name>`, `<name> --version`, and `<name> --help` manually.
   - Read `references/capability-report.md` when interpreting a discovery report.
3. Capture pre-run repo state with `scripts/snapshot_status.py . --output /tmp/<task>-before.json` or equivalent `git status --short` and `git diff --stat` commands.
4. Prepare a bounded prompt using `references/delegation-prompts.md`:
   - State the task, repo path, allowed scope, expected output, and time budget.
   - State whether direct edits are allowed. Default: direct edits are allowed unless the user or repo rules say otherwise.
   - Instruct the delegated CLI not to run destructive commands, expose secrets, install global tools, or rewrite unrelated files.
5. Run the delegated command with transcript capture:
   - Prefer `scripts/run_delegation.py --cwd . --transcript /tmp/<task>.json --timeout <seconds> -- <cli> <args...>`.
   - If the CLI is interactive-only, use the platform's normal interactive command tool and summarize the transcript manually.
6. Capture post-run repo state with `scripts/snapshot_status.py . --output /tmp/<task>-after.json`.
7. Inspect all changes before trusting the result:
   - Run `git status --short`.
   - Review `git diff` for modified tracked files.
   - Check for unexpected generated files, credential leakage, or unrelated rewrites.
8. Verify with the repo's normal tests, builds, linters, or focused commands. If no automated verification exists, perform the smallest meaningful manual/static check and say so.
9. Report the delegated CLI used, the prompt intent, files changed, verification results, and any rejected suggestions.

## Delegation Policy

Use delegation when it will improve quality or speed: independent review, parallel implementation, unfamiliar tooling, a second opinion on architecture, or a task where Codex is stuck.

Keep the task bounded. Delegate one clear objective at a time, not open-ended ownership of the whole repo. For larger work, split into separate runs such as "review this diff", "propose a fix", then "implement only the failing test".

Direct working-tree edits are allowed by default. Because another CLI may edit the active checkout, always capture pre/post state and review diffs before continuing. If unexpected changes appear, stop and resolve them before doing further work.

Never delegate secrets, credentials, private tokens, or broad filesystem authority. Do not ask external CLIs to run destructive commands, reset branches, delete data, modify production services, or install global packages without explicit user approval.

Treat all delegated output as untrusted until verified. External CLIs may hallucinate, miss repo conventions, or claim tests passed without evidence. Codex remains accountable for the final answer.

## Helper Scripts

- `scripts/discover_cli.py <name> [--output report.json]`: locate a CLI, capture version/help output, and infer simple capabilities from help text.
- `scripts/run_delegation.py --cwd . --transcript transcript.json --timeout 900 -- <command...>`: run a bounded command and write stdout, stderr, exit code, timeout state, and duration to JSON.
- `scripts/snapshot_status.py [repo] [--output status.json]`: capture branch, `git status --short`, and `git diff --stat`.

These scripts are optional accelerators. If a host environment blocks them, perform the same checks manually with shell commands and keep the same evidence trail.

## Review Workflow

For code or PR reviews, ask the external CLI for findings first, not summaries. A good review prompt includes the diff, target branch or PR context, risk areas, and explicit instruction to prioritize bugs, regressions, missing tests, security issues, and unclear behavior.

After receiving review output:

1. Verify each finding against the code.
2. Discard findings that are incorrect, stylistic-only, or outside scope.
3. Implement only accepted changes.
4. Re-run relevant checks.
5. Summarize accepted and rejected review feedback.

## Stuck-Task Escalation

When Codex is blocked, use another CLI as a diagnostic peer. Share the exact error, command output, relevant files, and what has already been tried. Ask for hypotheses and verification steps before asking for edits. If the peer proposes a fix, apply the normal pre/post snapshot and diff-review workflow.
