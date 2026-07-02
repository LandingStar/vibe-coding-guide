# Planning Gate - OpenCode Server/API Session Ledger And Binding Alignment

Date: 2026-06-30

## Context

The OpenCode direct server/API adapter is now usable from the bounded delivery
surfaces:

- `scheduler opencode-delivery-supervisor-once`
- `scheduler opencode-delivery-e2e-smoke`
- `scheduler opencode-delivery-supervisor-loop`

All three surfaces keep `cli` as the default transport and can explicitly
select `server-api`. The remaining policy gap is how server/API session
selection relates to the existing OpenCode session ledger and the newer
provider-neutral continuous worker binding ledger.

## Goal

Make the session selection and persistence contract explicit for server/API
transport without implementing full continuous worker lifecycle.

## Scope

This slice implements:

1. Contract documentation for selector precedence:
   - explicit `--server-api-session-id` / client config;
   - request `host_session` from continuous worker binding lookup;
   - request `host_session` from OpenCode session ledger lookup;
   - server/API-created session when no selector exists.
2. Focused runtime evidence that server/API transport follows the same
   continuous-worker-first lookup policy as CLI transport.
3. Explicit result metadata showing that sessions created by the direct
   server/API client are not automatically persisted to either ledger.
4. Focused tests proving:
   - explicit server/API session id disables lookup and skips session creation;
   - continuous worker binding wins over the older session ledger;
   - server/API-created sessions remain metadata-only and do not create ledger
     files.
5. Documentation writeback in the OpenCode host provisioning guide.

## Non-Goals

- Do not add an automatic write from server/API-created sessions into
  `.codex/runtime/opencode-session-ledger.json`.
- Do not add an automatic write from server/API-created sessions into
  `.codex/runtime/continuous-worker-bindings.json`.
- Do not implement full continuous worker lifecycle, long-lived worker
  ownership, compaction cadence, mailbox replay, or lane ownership policy.
- Do not start, stop, restart, supervise, or health-monitor `opencode serve`.
- Do not expose live OpenCode provider execution through MCP.
- Do not change Codex behavior or OpenCode CLI default behavior.
- Do not persist raw transcripts or secret values.

## Policy

Selector precedence is:

```text
explicit server/API session id
-> continuous worker binding host_session
-> OpenCode session ledger host_session
-> server/API-created session
```

Server/API-created sessions are runtime metadata only. A created session may be
claimed later only through an explicit host-owned action such as
`doc-based-coding opencode session claim` or `doc-based-coding worker-binding
claim`; delivery itself does not silently decide scope, ownership, expiry, or
worker continuity.

Continuous worker binding reuse remains the only delivery-time ledger mutation
in this slice, and only when an existing continuous worker binding was selected
before delivery. That mutation records reuse/audit facts; it does not claim a
new binding from a newly-created server/API session.

## Acceptance Criteria

1. Server/API result metadata distinguishes `explicit_config`,
   `continuous_worker_binding`, `session_ledger`, and `server_api_created`.
2. Created server/API sessions include metadata stating that persistence is
   `not_persisted_by_delivery` and that explicit host-owned claim is required.
3. Existing continuous worker binding lookup takes precedence over the older
   OpenCode session ledger for server/API transport.
4. Explicit server/API session id bypasses both continuous worker binding and
   OpenCode session ledger lookup.
5. When no selector exists, server/API creates a session but does not create or
   mutate either ledger file.
6. Focused tests, `py_compile`, and `git diff --check` pass for touched files.

## Follow-Up

Later slices may add an explicit host-owned claim action that promotes a
server/API-created session into the OpenCode session ledger or a continuous
worker binding. That action should be separate from delivery execution and must
require explicit scope/owner/expiry inputs.

## Completion Notes

Implemented on 2026-06-30.

Behavior fixed and documented:

- Server/API-created sessions now report:
  - `session_selector_source=server_api_created`;
  - `session_persistence=not_persisted_by_delivery`;
  - `server_api_created_session_persisted=false`;
  - `server_api_created_session_persistence_authority=explicit_host_owned_claim_required`.
- Explicit server/API session selectors now suppress continuous-worker binding
  resolution in both runtime adapter lookup and delivery batch preparation.
  This prevents a delivery using `--server-api-session-id` from accidentally
  recording reuse on an unrelated continuous worker binding.
- Server/API transport follows continuous-worker-first lookup before the older
  OpenCode session ledger when no explicit selector is configured.
- Server/API-created sessions remain metadata-only and do not create or mutate
  `.codex/runtime/opencode-session-ledger.json`,
  `.codex/runtime/continuous-worker-bindings.json`, or the continuous worker
  event log.

Validation results:

- `python -m py_compile src\__main__.py src\runtime\orchestration\opencode_server_api_client.py src\runtime\orchestration\leader_worker_codex_delivery.py tests\test_cli.py tests\test_runtime_orchestration.py`
  passed.
- `python -m pytest tests/test_cli.py -k "opencode_delivery_supervisor or opencode_delivery_e2e_smoke or opencode_server_api_readiness" -q`
  passed: `22 passed, 148 deselected`.
- `python -m pytest tests/test_runtime_orchestration.py -k "opencode_server_api or opencode_delivery_supervisor or continuous_worker_binding" -q`
  passed: `22 passed, 391 deselected`.
