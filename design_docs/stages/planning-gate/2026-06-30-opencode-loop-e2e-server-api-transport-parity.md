# Planning Gate - OpenCode Loop/E2E Server/API Transport Parity

Date: 2026-06-30

## Context

The direct OpenCode server/API adapter is available as an
`OpenCodeCliClient`-compatible runtime client, and
`scheduler opencode-delivery-supervisor-once` can now explicitly select:

```text
--opencode-transport cli|server-api
```

The remaining stage-level transport gap is parity for the other bounded
OpenCode delivery surfaces:

- `scheduler opencode-delivery-e2e-smoke`
- `scheduler opencode-delivery-supervisor-loop`

Live concurrent smoke is deliberately excluded from this slice.

## Goal

Extend explicit OpenCode transport selection to bounded loop and E2E smoke
without changing default CLI behavior or the provider-parametric delivery state
machine.

## Scope

This slice implements:

1. Shared CLI parsing for OpenCode delivery server/API transport options:
   - `--opencode-transport cli|server-api`
   - `--server-api-base-url`
   - `--server-api-session-id`
   - `--server-api-health-path`
   - `--server-api-doc-path`
   - `--server-api-timeout-seconds`
   - `--server-api-username-env-var`
   - `--server-api-password-env-var`
2. Shared host wiring that can construct either:
   - `OpenCodeCliProcessClient(OpenCodeCliClientConfig(...))`; or
   - `OpenCodeServerApiClient(OpenCodeServerApiClientConfig(...))`.
3. Use of that shared host wiring in:
   - once delivery, preserving the completed Slice 1 behavior;
   - E2E smoke;
   - bounded supervisor loop.
4. Focused tests proving server/API transport works for E2E smoke and bounded
   loop through local/injected HTTP fixtures.

## Non-Goals

- Do not bind server/API transport into `live-opencode-concurrent-worker-smoke`.
- Do not start, stop, restart, supervise, or health-monitor `opencode serve`.
- Do not expose live OpenCode provider execution through MCP.
- Do not write server/API-created sessions into the OpenCode session ledger.
- Do not change Codex delivery behavior.
- Do not change the default OpenCode CLI transport behavior.
- Do not implement full continuous-worker lifecycle.

## Acceptance Criteria

1. `opencode-delivery-e2e-smoke --help` and
   `opencode-delivery-supervisor-loop --help` document `--opencode-transport`
   and server/API options.
2. Both commands default to `cli` and keep existing CLI options valid.
3. Both commands can use `--opencode-transport server-api` against a local fake
   HTTP endpoint.
4. Runtime invocation audit attempts include `transport=server-api` metadata
   for successful server/API delivery.
5. Explicit server/API session id still skips session creation.
6. Existing session/continuous worker lookup can still flow through
   `request.host_session` when no explicit server/API session id is provided.
7. Focused tests, `py_compile`, and `git diff --check` pass for touched files.

## Follow-Up

Next slices in the active stage:

1. Session ledger and continuous-worker binding policy alignment for
   server/API-created sessions.
2. Readiness/doctor/provisioning documentation and self-check alignment.
3. Live smoke or manual smoke guide for a real host-owned `opencode serve`
   endpoint.

## Completion Notes

Implemented on 2026-06-30.

CLI surfaces:

- `doc-based-coding scheduler opencode-delivery-e2e-smoke`
- `doc-based-coding scheduler opencode-delivery-supervisor-loop`

Both surfaces now accept the same server/API transport options as once
delivery:

```text
--opencode-transport cli|server-api
--server-api-base-url URL
--server-api-session-id ID
--server-api-health-path PATH
--server-api-doc-path PATH
--server-api-timeout-seconds N
--server-api-username-env-var NAME
--server-api-password-env-var NAME
```

Implementation notes:

- Default transport remains `cli`.
- Shared host wiring constructs `OpenCodeCliProcessClient` for `cli` and
  `OpenCodeServerApiClient` for `server-api`.
- The delivery state machine and runtime invocation audit path remain the same.
- Live OpenCode concurrent smoke is intentionally not changed in this slice.
- Server/API-created sessions are still not written to the session ledger.

Validation results:

- `python -m py_compile src\__main__.py src\runtime\orchestration\opencode_server_api_client.py src\runtime\orchestration\leader_worker_codex_delivery.py tests\test_cli.py tests\test_runtime_orchestration.py`
  passed.
- `python -m pytest tests/test_cli.py -k "opencode_delivery_supervisor or opencode_delivery_e2e_smoke or opencode_server_api_readiness" -q`
  passed: `22 passed, 148 deselected`.
- `python -m pytest tests/test_runtime_orchestration.py -k "opencode_server_api or opencode_delivery_supervisor" -q`
  passed: `15 passed, 395 deselected`.
