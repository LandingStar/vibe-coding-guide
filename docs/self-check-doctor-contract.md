# Self-Check / Doctor Contract

## Purpose

`doc-based-coding doctor` is the unified, scriptable self-check entry for
host-facing installation, configuration, and readiness diagnostics.

It exists to keep checks such as Codex MCP exposure, provider host readiness,
bootstrap follow-up, scheduler storage visibility, and future adapter checks on
one shared contract instead of spreading bespoke JSON shapes across subcommands.

Doctor checks are diagnostic. They do not replace:

- `validate`, which checks governance/project constraints;
- `check`, which performs operator-oriented constraint/state readback;
- provider execution commands, which may run live runtimes;
- bootstrap, which scaffolds project files.

## Default Safety Standard

Every doctor check is safe by default:

- read-only;
- no provider task execution;
- no MCP tool calls;
- no MCP server startup unless an individual future check explicitly documents
  that exception and remains opt-in;
- no mutation of Codex, VS Code, project, scheduler, or user config;
- no secret value reads beyond presence checks, and no secret value output;
- no raw transcript output;
- testable with injected runner, `which`, environment, path provider, and
  timeout.

If a future check needs mutation or live execution, it must not be registered in
the default doctor path. It needs a separate command or explicit opt-in flag.

## Profiles

The first standard profiles are:

- `codex`: Codex host entry, project trust, project `.codex/config.toml`, and
  Codex-visible MCP registration.
- `vscode`: VS Code / Copilot host registration and workspace `mcp.json`
  checks. First version may register no checks.
- `opencode`: OpenCode host entry and CLI availability checks.
- `runtime`: platform runtime package and CLI availability checks.
- `scheduler`: scheduler storage/readback checks. First version may register no
  checks.
- `mcp`: generic MCP registration/exposure checks. First version may register
  no checks beyond checks also included in `codex`.
- `all`: all registered checks.

Profiles are filters over registered check IDs. A check may belong to multiple
profiles.

## Runtime Registry

Each check is registered with:

- `check_id`: stable machine-readable ID, for example
  `codex.mcp_exposure`.
- `profiles`: one or more profile names.
- `title`: short human-readable label.
- `description`: one-sentence check intent.
- `run(context) -> SelfCheckResult`: read-only execution function.

The registry must allow unit tests to construct a private registry with fake
checks and fake context. Default production registry construction must be a
separate helper so future packages can add checks without changing the runner.

## Context

`SelfCheckContext` provides:

- `project_root`;
- `environment`;
- `runner`;
- `which`;
- `timeout_seconds`;
- `user_config_path`;
- `metadata`.

Checks should use these dependencies instead of directly reading global process
state when practical. This keeps checks deterministic and testable.

## Result Schema

Doctor report:

```json
{
  "schema_version": "self-check-report/v1",
  "profile": "codex",
  "project_root": "...",
  "overall_status": "ok",
  "counts": {
    "ok": 1,
    "warning": 0,
    "failed": 0,
    "skipped": 0
  },
  "checks": [],
  "next_actions": [],
  "authority_split": {
    "read_only": true,
    "provider_executed": false,
    "mcp_server_started": false,
    "mcp_tool_called": false,
    "config_mutated": false,
    "secret_material_read": false
  }
}
```

Single check result:

```json
{
  "check_id": "codex.mcp_exposure",
  "profile": ["codex", "mcp"],
  "title": "Codex MCP Exposure",
  "status": "ok",
  "summary": "Codex can see an enabled doc-based-coding MCP server.",
  "evidence": {},
  "suspected_problem": "",
  "remediation": [],
  "authority_split": {
    "read_only": true,
    "provider_executed": false,
    "mcp_server_started": false,
    "mcp_tool_called": false,
    "config_mutated": false,
    "secret_material_read": false
  },
  "secret_safe": true,
  "duration_ms": 12
}
```

Statuses:

- `ok`: check passed.
- `warning`: check found a likely configuration or environment issue but did
  not prove the target is unusable.
- `failed`: check failed because an expected invariant was definitely broken or
  the check itself could not complete in a way that preserves the contract.
- `skipped`: check was intentionally not run, usually because a prerequisite is
  absent.

Aggregation:

- `failed` dominates `warning`.
- `warning` dominates `skipped`.
- If all checks are skipped, `overall_status` is `skipped`.
- Otherwise all checks `ok` means `overall_status=ok`.

Exit codes:

- `0`: `overall_status` is `ok`, `warning`, or `skipped`.
- `1`: runtime/usage error in the doctor command itself.
- `2`: `overall_status=failed`.

Warnings stay exit-code zero so install scripts can surface guidance without
treating every missing optional host as a hard failure.

## Compatibility

Existing readiness commands should not invent new long-term schemas. They may
remain as compatibility wrappers, but new checks should register with the
doctor framework first.

Current first compatibility rule:

- `doc-based-coding codex readiness` keeps its existing top-level Codex CLI
  readiness fields and exposes the doctor-derived Codex MCP result under
  `mcp_exposure` for compatibility.

## Initial Required Check

The first registered check is:

- `workspace.dbc_command_relay`
- profiles: `codex`, `mcp`, `runtime`
- source behavior: reports the per-agent `workspaceDbcCommand` MCP relay
  contract
- purpose: make the workspace-bound DBC command surface explicit so agents do
  not fall back to a global `doc-based-coding` command when an MCP session is
  available.

It must remain read-only and must not execute the relay during doctor. The
relay itself is the execution surface.

Operational usage and troubleshooting guidance lives in
`docs/workspace-dbc-command-relay.md`.

The first host exposure check is:

- `codex.mcp_exposure`
- profiles: `codex`, `mcp`
- source behavior: current Codex MCP exposure diagnostic
- purpose: distinguish package/server exposure problems from Codex
  trust/project-config/restart problems.

It must remain read-only and must not call `localTrajectory` or any MCP tool.

The next standard checks are:

- `opencode.cli_readiness`
  - profiles: `opencode`, `runtime`
  - purpose: report whether the OpenCode CLI executable is available without
    running an OpenCode task or reading secrets.
- `opencode.server_api_readiness`
  - profiles: `opencode`, `runtime`
  - purpose: report whether a host-owned `opencode serve` HTTP endpoint is
    reachable without creating sessions, sending prompts, running provider
    tasks, starting/stopping the server, or reading secret values.
- `scheduler.storage_visibility`
  - profile: `scheduler`
  - purpose: report whether default `.dbc/scheduler` storage artifacts are
    present and readable without recovering, compacting, ticking, or mutating
    scheduler
    state.
  - compatibility: if legacy `.codex/scheduler` exists while `.dbc/scheduler`
    is missing, the check reports a warning with legacy evidence instead of
    treating `.codex/scheduler` as the current default.
