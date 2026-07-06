# Workspace DBC Command Relay

## Purpose

`workspaceDbcCommand` is the workspace-bound DBC command relay exposed through
the doc-based-coding MCP server.

It exists so each agent can run DBC CLI-equivalent diagnostics and operator
surfaces through the DBC package instance already selected by that agent's MCP
session. Agents should not resolve a bare global `doc-based-coding` executable,
virtualenv path, or checkout path when the relay is available.

## Mental Model

Each agent has its own MCP tool surface. When that surface includes
`workspaceDbcCommand`, the relay belongs to that agent and that workspace:

- it is provided by the agent's current doc-based-coding MCP server process;
- it uses the MCP project root as the command working directory;
- it runs through the same Python/package instance that hosts the MCP server;
- it is DBC-only, not a generic shell.

This keeps multiple workspaces free to use different DBC versions or checkouts
side by side.

## When To Use It

Prefer dedicated structured MCP tools when they exist. Examples:

- use `localTrajectory` for Local Work Trajectory mutation;
- use `get_next_action` for next-action recovery;
- use scheduler MCP tools for scheduler lifecycle operations that already have
  a dedicated tool.

Use `workspaceDbcCommand` when a DBC CLI surface is needed and no dedicated MCP
tool exists, for example:

```json
{
  "argv": ["doctor", "--profile", "codex"],
  "mode": "read"
}
```

The `argv` field is the DBC CLI argument vector without `doc-based-coding`.
Documentation examples such as `doc-based-coding doctor --profile codex` should
be read as `["doctor", "--profile", "codex"]` when using the relay.

## Modes

`mode="read"` is the default. It allows read-only or diagnostic command
families such as:

- `check`
- `codex`
- `doctor`
- `info`
- `opencode`
- `provider`
- `qoder`
- `resources`
- `validate`
- `worker-binding`

Commands that may mutate project or scheduler state require explicit
`mode="mutate"`. The relay denies mutating command families in read mode.

This mode split is a safety boundary, not a permission prompt replacement.
Project rules and host permissions still apply.

## Expected Self-Check

Run:

```powershell
doc-based-coding doctor --profile codex
```

or, from an MCP-enabled agent:

```json
{
  "argv": ["doctor", "--profile", "codex"],
  "mode": "read"
}
```

The report should include:

- `workspace.dbc_command_relay`
- `codex.mcp_exposure`

For `workspace.dbc_command_relay`, important evidence fields are:

- `tool_name`: should be `workspaceDbcCommand`
- `resolution_policy`: should say `per-agent MCP server package instance`
- `path_fallback_required`: should be `false`
- `generic_shell`: should be `false`

For a direct relay call, important result fields are:

- `schema_version`: `workspace-dbc-command-relay/v1`
- `command_preview`: should begin with the MCP server's Python executable,
  followed by `-m`, `src`, and the requested DBC argv
- `cwd`: should be the target workspace root
- `execution_strategy`: normally `in_process` for read commands
- `authority_split.generic_shell`: should be `false`
- `authority_split.workspace_bound`: should be `true`

## Installation Check

After MCP registration and host restart, check tool exposure:

1. Confirm the target workspace has the intended `.codex/config.toml` or host
   MCP registration.
2. Confirm the host can see the DBC MCP server, for example:
   `codex -C <target-repo> mcp list`.
3. Confirm tools/list includes both `workspaceDbcCommand` and expected
   structured tools such as `localTrajectory`.
4. Use `workspaceDbcCommand` for `["doctor", "--profile", "codex"]`.

If `workspaceDbcCommand` is missing but `localTrajectory` is present, the host
is likely connected to an older DBC MCP package. Restart the host after
updating the workspace MCP command.

If both are missing, troubleshoot MCP registration and workspace trust first.

## Troubleshooting

### Bare `doc-based-coding` resolves to the wrong package

This is exactly what the relay avoids. Do not fix this by forcing all workspaces
to share one global install. Prefer the workspace MCP registration and
`workspaceDbcCommand`.

### `workspaceDbcCommand` is not exposed

Likely causes:

- the MCP host is still running an old server process;
- the workspace `.codex/config.toml` points at an old DBC package;
- Codex did not load project-level config because the project is not trusted;
- the host was not restarted after MCP config changed.

Run `codex -C <target-repo> mcp list` and `doc-based-coding doctor --profile
codex` from the intended workspace package, then restart the host.

### Relay returns `denied`

Check:

- `argv[0]` is a supported DBC command family;
- mutating command families use `mode="mutate"`;
- `argv` does not include the executable name.

For example, use:

```json
{"argv": ["doctor", "--profile", "codex"], "mode": "read"}
```

not:

```json
{"argv": ["doc-based-coding", "doctor", "--profile", "codex"]}
```

### Relay returns `timeout`

Read commands normally run in-process to avoid nested stdio subprocess stalls.
If a command times out, inspect the returned `stderr`, command family, and
workspace pack initialization warnings. Do not switch to a global CLI as a
workaround; fix the workspace MCP package or the command being relayed.

### Pack warnings appear during MCP startup

Pack dependency or integrity warnings can be emitted while the MCP server is
initializing its workspace pipeline. They do not by themselves prove relay
failure. Use the relay result fields (`ok`, `status`, `stderr`, and
`execution_strategy`) to distinguish command failure from startup warnings.

## Agent Guidance

For agents:

1. Prefer dedicated MCP tools.
2. When only a DBC CLI surface exists, call `workspaceDbcCommand`.
3. If the relay is expected but unavailable, report an MCP/tool exposure
   problem instead of guessing paths.
4. Do not ask the user to manually run path-specific DBC commands merely to work
   around agent-side path uncertainty.

This applies separately to every agent. A leader and each worker should use the
relay exposed in their own active MCP session.
