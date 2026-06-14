# Delegation Prompt Templates

Adapt these templates to the discovered CLI's invocation style. Keep prompts concise, bounded, and explicit about allowed writes.

## Implementation

```text
You are an external coding agent working in this repository: <absolute repo path>.
Task: <single concrete objective>.
Scope: edit only <allowed files/directories>. Do not rewrite unrelated files.
Direct edits are allowed for this task.
Do not run destructive commands, reset git state, expose secrets, install global tools, or contact production services.
Before finishing, report: files changed, commands run, verification result, and any uncertainty.
```

## Review

```text
Review the current diff in this repository: <absolute repo path>.
Prioritize bugs, regressions, missing tests, security issues, and behavior that contradicts the stated goal: <goal>.
Return findings only. For each finding, include severity, file/line when possible, why it matters, and a concrete fix direction.
Do not make file edits.
```

## Stuck-Task Escalation

```text
I am blocked on this task in repository: <absolute repo path>.
Goal: <goal>.
Observed failure: <error or failing command output>.
Already tried: <short list>.
Relevant files: <paths>.
Give likely causes and verification steps first. If you suggest code changes, keep them minimal and explain how to verify them.
```

## Research

```text
Investigate <question> for this repository: <absolute repo path>.
Use only local files and command output unless explicitly allowed to browse or install dependencies.
Return a concise recommendation, evidence from the repo, and any assumptions.
Do not make file edits.
```
