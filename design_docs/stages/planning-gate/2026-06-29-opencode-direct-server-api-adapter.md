# Planning Gate - OpenCode Direct Server/API Adapter

Date: 2026-06-29

## Context

OpenCode already has a host-owned CLI runtime path in this repository:

- `OpenCodeCliProcessClient` invokes `opencode run`;
- delivery supervisors accept an injected `OpenCodeCliClient` seam;
- serve readiness, serve lifecycle receipts, session ledger, stale-session
  recovery, and continuous worker binding are already modeled around
  host-owned OpenCode serve/session facts.

The remaining OpenCode-specific gap is a direct HTTP server/API adapter for a
running `opencode serve` instance.

Official OpenCode docs establish the external contract:

- `opencode serve` runs a headless HTTP server;
- default host/port are `127.0.0.1:4096`;
- HTTP basic auth is controlled by `OPENCODE_SERVER_PASSWORD` and optional
  `OPENCODE_SERVER_USERNAME`;
- `/global/health` reports server health and version;
- `/doc` exposes the OpenAPI 3.1 spec;
- sessions are created through `POST /session`;
- prompts can be sent through `POST /session/:id/message`.

## Goal

Add the first Python-side direct OpenCode server/API adapter without replacing
the existing CLI adapter or changing scheduler behavior.

## Scope

This slice implements:

1. `OpenCodeServerApiClientConfig`;
2. `OpenCodeServerApiClient`, structurally compatible with the existing
   `OpenCodeCliClient.exec(OpenCodeCliRequest) -> OpenCodeCliResult` seam;
3. read-only server/API readiness:
   - health endpoint check;
   - optional `/doc` OpenAPI endpoint check;
   - credential-safe evidence;
4. prompt execution over HTTP:
   - create a session when no session id is supplied;
   - reuse explicit config or request host-session ids when supplied;
   - send the existing normalized scheduler prompt body to
     `POST /session/{id}/message`;
   - normalize message/parts response into `OpenCodeCliResult`;
5. focused unit tests using injected HTTP openers only;
6. exports and a narrow CLI readiness surface:
   `doc-based-coding opencode server-api-readiness`.

## Non-Goals

- Do not start, stop, restart, or supervise `opencode serve`.
- Do not migrate scheduler `opencode-delivery-*` CLI commands to server/API
  transport yet.
- Do not expose live OpenCode provider execution through MCP.
- Do not add JS/TS SDK dependency.
- Do not persist raw transcript or secret values.
- Do not replace the existing `OpenCodeCliProcessClient`.
- Do not design long-lived worker ownership beyond the already documented
  continuous worker binding direction.

## Acceptance Criteria

1. Runtime tests prove:
   - health readiness succeeds through injected response;
   - readiness reports unreachable/auth failures without leaking secret values;
   - `/doc` OpenAPI discovery reports version/path evidence when available;
   - `OpenCodeServerApiClient.exec()` creates a session and sends a prompt;
   - explicit session id skips session creation and sends to that session;
   - non-2xx HTTP failures become `OpenCodeCliRuntimeError`.
2. CLI tests prove:
   - `opencode server-api-readiness --help` documents host-owned/read-only
     boundary;
   - JSON output is credential-safe and uses the new readiness report shape.
3. Existing OpenCode CLI adapter tests remain valid.
4. `py_compile` passes for touched runtime/CLI files.
5. Focused runtime/CLI tests pass.
6. `git diff --check` passes for touched files.

## Follow-Up

The next narrow gate should bind this adapter into host-owned OpenCode delivery
surfaces, probably as an explicit transport option:

- `--opencode-transport cli|server-api`
- `--server-api-base-url`
- `--server-api-session-id`
- `--server-api-doc-path`

That follow-up must decide how server/API transport interacts with the existing
OpenCode session ledger and continuous worker binding ledger.

## Completion Notes

Implemented on 2026-06-29.

Runtime surface:

- `OpenCodeServerApiClientConfig`
- `OpenCodeServerApiReadinessReport`
- `OpenCodeServerApiClient`
- `inspect_opencode_server_api_readiness()`

CLI surface:

- `doc-based-coding opencode server-api-readiness`

Boundary preserved:

- The direct server/API client is structurally compatible with the existing
  `OpenCodeCliClient.exec(OpenCodeCliRequest) -> OpenCodeCliResult` seam.
- Existing OpenCode CLI adapter remains unchanged.
- Scheduler `opencode-delivery-*` commands still use the CLI process client;
  transport selection is intentionally left to the follow-up gate.
- The readiness command is read-only and does not start/stop/supervise
  `opencode serve`, run provider tasks, mutate scheduler/delivery state, write
  runtime invocation logs, or mutate Local Work Trajectory.

Validation results:

- `python -m py_compile src/runtime/orchestration/opencode_server_api_client.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py`
  passed.
- `python -m pytest tests/test_runtime_orchestration.py -k "opencode_server_api" -q`
  passed: `5 passed, 403 deselected`.
- `python -m pytest tests/test_cli.py -k "opencode_server_api_readiness or opencode_help" -q`
  passed: `3 passed, 162 deselected`.
