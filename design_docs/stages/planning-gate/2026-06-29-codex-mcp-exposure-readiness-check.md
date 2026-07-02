# Codex MCP Exposure Readiness Check

Date: 2026-06-29

## Context

Codex MCP exposure can fail even when the `doc-based-coding-mcp` package and
server tool declarations are healthy. The observed failure mode was:

1. the project-local `.codex/config.toml` registered the MCP server;
2. a real MCP stdio `tools/list` against the same command included
   `localTrajectory`;
3. but `codex mcp list` and `codex doctor` reported zero MCP servers because
   the project was not trusted in user-level Codex configuration.

The installation documentation now describes this troubleshooting path. The
next narrow slice is to expose a lightweight, scriptable readiness signal so
installation/bootstrap checks can point users at the trusted-project/config
layer without requiring manual diagnosis.

## Goal

Add a read-only Codex MCP exposure diagnostic to the existing
`doc-based-coding codex readiness` surface.

The diagnostic should:

- run without executing provider tasks;
- avoid printing token values, auth JSON, raw transcript, or secret material;
- check whether a project-local `.codex/config.toml` exists;
- check whether user-level Codex config marks the current project trusted;
- run `codex -C <project> mcp list` when Codex CLI is available;
- summarize whether a doc-based-coding MCP server appears enabled;
- emit actionable next steps when the symptom is `MCP servers 0` or no
  doc-based-coding server in `mcp list`.

## Non-Goals

- Do not mutate `~/.codex/config.toml`.
- Do not call `codex mcp add`.
- Do not start or inspect the DBC MCP server through a live MCP handshake in
  the default readiness path.
- Do not change MCP server tool declarations, `localTrajectory` semantics, or
  approval rules.
- Do not make bootstrap depend on Codex being installed.

## Design

Add a small runtime helper dedicated to credential-safe Codex MCP exposure
readback. The helper should accept injectable `runner`, `which`, and config
path providers for tests. CLI wiring should add the result as an
`mcp_exposure` field under `codex readiness`.

The helper is intentionally a host interaction diagnostic, not platform core
semantics. It belongs beside Codex host provisioning/readiness code rather than
inside the MCP server.

## Acceptance Criteria

1. `doc-based-coding codex readiness` returns the existing Codex CLI readiness
   fields plus an `mcp_exposure` object.
2. When Codex CLI is missing, the MCP diagnostic reports
   `diagnostic_status=skipped` with a safe reason.
3. When project-local `.codex/config.toml` exists but the user-level config
   does not trust the project, the diagnostic includes a remediation mentioning
   trusted project configuration and restart.
4. When `codex mcp list` output contains an enabled doc-based-coding server,
   the diagnostic reports `doc_based_coding_server_visible=true`.
5. Focused tests cover missing CLI, untrusted project config, and visible
   server output without depending on the developer machine's Codex state.
6. Documentation points users from installation troubleshooting to the
   readiness command.

## Validation

Run focused tests:

```powershell
python -m pytest tests/test_runtime_orchestration.py -k codex_mcp_exposure
python -m pytest tests/test_cli.py -k codex_readiness
```

Run whitespace check for touched files:

```powershell
git diff --check -- src/runtime/orchestration/codex_mcp_diagnostics.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py docs/installation-guide.md docs/codex-entry-contract.md design_docs/stages/planning-gate/2026-06-29-codex-mcp-exposure-readiness-check.md
```

## Completion Notes

Implemented on 2026-06-29.

Runtime surface:

- `inspect_codex_mcp_exposure(project_root, ...)`
- `CodexMcpExposureDiagnostic`

CLI surface:

- `doc-based-coding codex readiness`
  now includes a credential-safe `mcp_exposure` object.

Validation results:

- `python -m pytest tests/test_runtime_orchestration.py -k codex_mcp_exposure`
  passed: `3 passed, 393 deselected`.
- `python -m pytest tests/test_cli.py -k codex_readiness`
  passed: `1 passed, 156 deselected`.
- `python -m src codex readiness` on the development workspace reported
  `mcp_exposure.diagnostic_status=ok` and
  `doc_based_coding_server_enabled=true`.
- `git diff --check` on touched files reported no whitespace errors; only
  Windows line-ending warnings were emitted.

The diagnostic remains read-only: it does not start the MCP server, call MCP
tools, mutate Codex config, run providers, or read secret material.
