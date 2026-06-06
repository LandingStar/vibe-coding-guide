# Doc-Based Coding

VS Code Host UX extension for the Doc-Based Coding platform. It consumes the shared Python runtime and MCP governance server to enforce project constraints, manage pack topology, and provide AI-assisted governance inside VS Code.

Codex remains a first-class supported entry through `AGENTS.md` + MCP + CLI/validation. This extension is the VS Code / Copilot host surface over the same backend; it does not replace or redefine the Codex mainline.

## Features

### Governance Enforcement

- **File Save Interception** — Checks governance policy before every file save; blocked saves open a Review Panel for approval
- **File Lifecycle Protection** — Intercepts file create, delete, and rename operations
- **Terminal Command Monitor** — Monitors shell commands via Shell Integration and warns/kills blocked commands
- **Review Panel** — WebView panel with approve/reject workflow for governance overrides

### Visibility & Status

- **Constraint Dashboard** — Real-time C1-C8 governance constraint status (Activity Bar)
- **Pack Explorer** — View loaded pack topology with scope, provides, and descriptions
- **Decision Log Viewer** — Recent governance decisions with intent, outcome, and trace IDs
- **Status Bar** — Violation count indicator with quick access to constraint details

### AI Integration

Current default provider: GitHub Copilot. The extension command layer is provider-abstracted so future runtimes can plug in without rewriting governance commands.

- **Intent Classification** — Classify user input via the active extension model provider
- **BLOCK Explanation** — AI-generated explanation and fix suggestions when governance blocks an action
- **Pack Description Generator** — AI-assisted pack description authoring
- **Pack Rules Generator** — AI-generated governance rules from natural language requirements

### Infrastructure

- **MCP Client** — stdio-based connection to the Python governance runtime
- **Setup Wizard** — Guided first-run configuration

## Getting Started

1. Open a workspace with a `.codex/platform.json` file
2. The extension auto-starts the MCP server (requires Python environment with `doc-based-coding` runtime)
3. View constraints and packs in the Activity Bar sidebar
4. Governance enforcement is active automatically for file saves, terminal commands, and file operations

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `docBasedCoding.pythonPath` | Python executable path | Auto-detect |
| `docBasedCoding.autoStart` | Auto-start MCP server | `true` |
| `docBasedCoding.serverArgs` | Extra MCP server arguments | `[]` |
| `docBasedCoding.terminal.killOnBlock` | Auto-kill blocked terminal commands | `false` |

## Commands

| Command | Description |
|---------|-------------|
| Refresh Constraints | Refresh C1-C8 constraint status |
| Start MCP Server | Start the governance runtime |
| Stop MCP Server | Stop the governance runtime |
| Setup Wizard | Guided first-run configuration |
| Refresh Packs | Reload pack topology |
| Refresh Decision Logs | Reload recent decisions |
| Classify Intent | Classify text via the active extension model provider |
| Generate Pack Description | AI-assisted pack description |
| Generate Pack Rules | AI-assisted governance rules |
| Open Governance Review Panel | Info about the review workflow |

## Requirements

- VS Code 1.93 or later
- Python 3.10+ with `doc-based-coding` runtime installed
- Shell Integration enabled in terminal (for terminal governance)
- GitHub Copilot extension (optional, current default provider for AI features)

## Release Notes

### 0.1.0

Initial release with full governance enforcement (P0-P6+), AI integration, and WebView review workflow.
