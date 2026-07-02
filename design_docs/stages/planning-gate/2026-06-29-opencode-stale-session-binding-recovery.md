# Planning Gate - OpenCode Stale Session Binding Recovery

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

OpenCode delivery can now consume active session ledger bindings, but stale
receipts could remain active indefinitely. That would make future same-lane
delivery attempts attach to a dead or expired host-owned OpenCode session.

## Scope

Add an explicit, auditable stale binding recovery surface:

1. expire active bindings whose `expires_at` is not later than `--now`;
2. optionally expire bindings whose attach target health check fails;
3. expose CLI:
   `doc-based-coding opencode session recover-stale`;
4. return compact checked/expired counts and stale reasons;
5. mutate only the OpenCode session ledger;
6. preserve no provider execution, no server lifecycle ownership, no raw
   transcript persistence, no secret value persistence, no scheduler/delivery
   mutation, and no Local Work Trajectory mutation.

## Non-Goals

This gate does not:

1. create replacement OpenCode sessions;
2. restart, stop, or supervise `opencode serve`;
3. retry failed delivery records automatically;
4. call OpenCode's task HTTP API directly;
5. expose live OpenCode provider execution through MCP;
6. delete provider-side session data;
7. rename historical provider-parametric `CodexDelivery...` product types.

## Implementation

Completed stale binding recovery:

1. added `OpenCodeSessionRecoverStaleRequest`;
2. added `recover_stale_opencode_session_bindings()`;
3. extended session ledger results with `checked_count`, `expired_count`, and
   `stale_reasons`;
4. added CLI `doc-based-coding opencode session recover-stale`;
5. default recovery expires only elapsed `expires_at` bindings;
6. `--expire-unhealthy` opt-in probes attach target health through the existing
   credential-safe serve readiness helper;
7. updated runtime exports and session CLI tests.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_session_recover_stale or opencode_session_ledger" -q
5 passed, 376 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_session" -q
5 passed, 145 deselected
```

No screenshot validation is required because this gate does not implement UI.

## Remaining OpenCode Work

OpenCode now has active session registration, delivery-time lookup, and
explicit stale receipt recovery. Remaining parity work:

1. optional host-owned `opencode serve` start/stop receipt contract;
2. direct server adapter, only after session lifecycle semantics stabilize;
3. provider-generic naming cleanup for historical `CodexDelivery...` product
   types.
