# Doc-Based Coding

Document-driven governance workflow platform for VS Code.

## Features

- **Constraint Dashboard** — Real-time C1-C8 governance constraint status
- **Pack Explorer** — View loaded pack topology
- **MCP Integration** — Connects to the Python governance runtime via MCP protocol

## Getting Started

1. Open a workspace with a `.codex/platform.json` file
2. The extension auto-starts the MCP server
3. View constraints in the Activity Bar sidebar

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `docBasedCoding.pythonPath` | Python executable path | Auto-detect |
| `docBasedCoding.autoStart` | Auto-start MCP server | `true` |
| `docBasedCoding.serverArgs` | Extra MCP server arguments | `[]` |

## Commands

- **Doc-Based Coding: Refresh Constraints** — Refresh constraint status
- **Doc-Based Coding: Start MCP Server** — Start the governance server
- **Doc-Based Coding: Stop MCP Server** — Stop the governance server
