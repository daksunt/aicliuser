# Capability Report Reference

`discover_cli.py` emits a JSON object with these fields:

- `name`: command name requested by Codex.
- `found`: whether the command exists on `PATH`.
- `path`: resolved executable path, or `null` when missing.
- `version`: captured result for `<cli> --version`, including command, exit code, stdout, stderr, and timeout state.
- `help`: captured result for `<cli> --help`.
- `inferred_capabilities`: best-effort booleans inferred from help text.

Inference is advisory only. A flag mentioned in help text may still require authentication, a project context, or different invocation syntax. Before running expensive or state-changing work, prefer a harmless smoke command or a review-only prompt.

Use these interpretation rules:

- `found: false`: do not attempt delegation to that CLI unless the user installs or exposes it.
- `version.exit_code != 0`: the CLI may still work, but authentication or runtime setup may be broken.
- `help.timed_out: true`: avoid long-running probes; try a shorter known-safe command if the user expects the CLI to exist.
- `accepts_prompt_flag: true`: look for prompt/message/instruction flags suitable for noninteractive use.
- `supports_print_mode: true`: look for flags such as `--print`, `--output`, or `--json` that make transcript capture easier.
- `mentions_noninteractive: true`: prefer the documented noninteractive mode over terminal automation.

If the help output is ambiguous, summarize the uncertainty and choose the safest bounded invocation that can produce useful output.
