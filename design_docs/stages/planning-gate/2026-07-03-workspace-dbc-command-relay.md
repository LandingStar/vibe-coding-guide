# Workspace DBC Command Relay

## Problem

The current workspace-level MCP registration can point each project at its own
doc-based-coding checkout or virtual environment, but CLI guidance and smoke
procedures still encourage agents to run the bare `doc-based-coding` command.
That bare command is resolved by host `PATH`, so it can silently use an old
global package instead of the package selected by the workspace MCP config.

This is a product logic issue, not an installation-state issue. The platform
must support multiple workspaces using different DBC packages side by side.

## Decision

Add a per-agent workspace DBC command relay as an MCP tool.

Each agent uses the relay exposed by its own MCP session. The relay runs DBC
commands through the same Python package instance that hosts that MCP server,
with the MCP project root as the default working directory. Agents therefore do
not need to reason about global PATH, virtual environments, or checkout paths.

## Contract

- Tool name: `workspaceDbcCommand`.
- Input:
  - `argv`: DBC CLI argument vector without the executable name.
  - `mode`: `read` by default; `mutate` requires explicit opt-in.
  - `timeoutSeconds`: bounded subprocess timeout.
- Execution:
  - Uses `[sys.executable, "-m", "src", *argv]`.
  - Runs with `cwd=<MCP project root>`.
  - Adds the current package root to `PYTHONPATH` so source-checkout MCP
    installs can relay to the same checkout even when the host shell PATH points
    elsewhere.
- Safety:
  - It is not a generic shell.
  - Read mode allows only read/diagnostic DBC commands.
  - Mutating commands are denied unless `mode="mutate"`.
  - Output is bounded and secret-safe by policy; no raw transcript or token
    value is intentionally collected.

## Non-Goals

- Do not update or require the global `doc-based-coding` install.
- Do not require agents to call a fixed `.venv-mcp` executable path.
- Do not turn MCP into a general command runner.
- Do not replace direct MCP tools such as `localTrajectory`; prefer structured
  MCP tools when a dedicated tool exists.

## Validation

- Unit tests prove the relay uses `sys.executable -m src` rather than bare
  `doc-based-coding`.
- MCP server tests prove `workspaceDbcCommand` is exposed and routed.
- Generated instructions mention the relay as the preferred CLI-equivalent
  surface when MCP is available.
