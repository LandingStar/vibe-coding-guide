# Planning Gate - OpenCode Delivery Supervisor Once Server/API Transport

Date: 2026-06-30

## Context

The first OpenCode direct server/API adapter slice is complete:

- `OpenCodeServerApiClient` is compatible with the existing
  `OpenCodeCliClient.exec(OpenCodeCliRequest) -> OpenCodeCliResult` seam.
- `doc-based-coding opencode server-api-readiness` provides a read-only,
  credential-safe readiness check for a host-owned `opencode serve` endpoint.
- `scheduler opencode-delivery-supervisor-once` still constructs
  `OpenCodeCliProcessClient` directly, so delivery cannot yet opt into the
  server/API transport.

This slice binds the direct server/API client into only the once delivery
surface. Bounded loop, E2E smoke, live smoke, and broader continuous-worker
policy remain follow-up slices.

## Goal

Add explicit transport selection to
`doc-based-coding scheduler opencode-delivery-supervisor-once`:

```text
--opencode-transport cli|server-api
```

The default remains `cli`.

## Scope

This slice implements:

1. CLI parsing and help text for:
   - `--opencode-transport cli|server-api`
   - `--server-api-base-url`
   - `--server-api-session-id`
   - `--server-api-health-path`
   - `--server-api-doc-path`
   - `--server-api-timeout-seconds`
   - `--server-api-username-env-var`
   - `--server-api-password-env-var`
2. Host wiring that constructs:
   - `OpenCodeCliProcessClient(OpenCodeCliClientConfig(...))` for `cli`;
   - `OpenCodeServerApiClient(OpenCodeServerApiClientConfig(...))` for
     `server-api`.
3. Preservation of existing OpenCode CLI behavior when no transport flag is
   passed.
4. Session selector priority for server/API execution through the existing
   seam:
   - explicit `--server-api-session-id`;
   - request `host_session` resolved from continuous-worker/session ledgers;
   - server/API-created session when neither selector exists.
5. Focused tests for parser/help/default compatibility and server/API
   execution through the once supervisor.

## Non-Goals

- Do not change Codex delivery behavior.
- Do not change default OpenCode CLI transport behavior.
- Do not bind server/API transport into bounded loop, E2E smoke, or live smoke
  yet.
- Do not start, stop, restart, supervise, or health-monitor `opencode serve`.
- Do not expose live OpenCode provider execution through MCP.
- Do not persist raw transcript or secret values.
- Do not add session-ledger writes for server/API-created sessions in this
  slice; that belongs to the session-ledger/continuous-worker alignment slice.

## Acceptance Criteria

1. `opencode-delivery-supervisor-once --help` documents the transport flag and
   server/API options while still showing the CLI options.
2. The default path still constructs and uses the CLI process client.
3. `--opencode-transport server-api` constructs and uses
   `OpenCodeServerApiClient`.
4. Explicit `--server-api-session-id` skips session creation.
5. Existing request `host_session` from continuous-worker/session ledger lookup
   is still available to the server/API client when no explicit server/API
   session id is passed.
6. With no session selector, server/API execution creates a session before
   sending the message.
7. HTTP/server/API failures flow through the existing delivery supervisor
   failure/audit path as `OpenCodeCliRuntimeError`.
8. Runtime invocation metadata can distinguish `transport=server-api`.
9. Focused tests, `py_compile`, and `git diff --check` pass for touched files.

## Follow-Up

Next slices in the active stage:

1. Extend the same transport selection to bounded loop and E2E smoke.
2. Align server/API transport with session ledger and continuous worker binding
   policy, including whether server/API-created sessions need explicit
   host-owned ledger writes.
3. Add readiness/doctor/provisioning documentation for server/API transport.
4. Run live smoke or document a manual smoke when a real host-owned
   `opencode serve` endpoint is available.

## Completion Notes

Implemented on 2026-06-30.

CLI surface:

- `doc-based-coding scheduler opencode-delivery-supervisor-once`
  now accepts `--opencode-transport cli|server-api`.
- The default remains `cli` and still constructs `OpenCodeCliProcessClient`.
- `server-api` constructs `OpenCodeServerApiClient` with the explicit
  `--server-api-*` options.

Boundary preserved:

- Delivery supervisor runtime/state-machine code still uses the existing
  injected `OpenCodeCliClient.exec(OpenCodeCliRequest) -> OpenCodeCliResult`
  seam.
- Server/API execution remains host-owned; dbc does not start, stop, restart,
  supervise, or health-monitor `opencode serve`.
- No live OpenCode provider execution was exposed through MCP.
- No server/API-created session is written into the session ledger in this
  slice.
- Codex delivery behavior and default OpenCode CLI transport behavior are
  unchanged.

Validation results:

- `python -m py_compile src\__main__.py src\runtime\orchestration\opencode_server_api_client.py src\runtime\orchestration\leader_worker_codex_delivery.py tests\test_cli.py tests\test_runtime_orchestration.py`
  passed.
- `python -m pytest tests/test_runtime_orchestration.py -k "opencode_server_api or opencode_delivery_supervisor" -q`
  passed: `15 passed, 395 deselected`.
- `python -m pytest tests/test_cli.py -k "opencode_delivery_supervisor or opencode_server_api_readiness" -q`
  passed: `16 passed, 152 deselected`.
