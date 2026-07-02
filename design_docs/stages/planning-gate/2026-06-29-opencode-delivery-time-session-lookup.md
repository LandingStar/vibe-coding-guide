# Planning Gate - OpenCode Delivery-Time Session Lookup

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

OpenCode had a durable session binding ledger, but delivery execution did not
consume it. That meant same-lane OpenCode continuity still required manual
`--attach-url` and `--session-id` flags on each delivery command.

## Scope

Add the smallest delivery-time lookup layer:

1. let OpenCode runtime requests carry one resolved host session selector;
2. resolve active ledger bindings by `task`, then `agent`, then `lane`;
3. enable lookup by default on OpenCode delivery CLI surfaces;
4. keep explicit OpenCode attach/session CLI flags higher priority than the
   ledger;
5. expose `--session-ledger-path` and `--no-session-ledger-lookup`;
6. record compact audit metadata for selector source and binding scope;
7. keep scheduler, delivery, Local Work Trajectory, and ledger authority
   boundaries unchanged.

## Non-Goals

This gate does not:

1. create OpenCode sessions;
2. start, stop, restart, or supervise `opencode serve`;
3. validate that an OpenCode session is still healthy;
4. call OpenCode's HTTP API directly;
5. expose live OpenCode provider execution through MCP;
6. mutate Local Work Trajectory;
7. rename historical provider-parametric `CodexDelivery...` types.

## Implementation

Completed delivery-time session lookup:

1. added `OpenCodeHostSessionSelector` and `OpenCodeCliRequest.host_session`;
2. extended `OpenCodeCliAgentRuntimeAdapter` with optional
   `session_ledger_path` and `enable_session_lookup`;
3. wired OpenCode session lookup through `RuntimeRegistryWiringConfig` and
   `CodexDeliverySupervisorRequest`;
4. updated `OpenCodeCliProcessClient` so explicit config wins, otherwise a
   request-level host selector becomes `opencode run --attach --session`;
5. added CLI options to OpenCode delivery once, E2E smoke, bounded loop, and
   live smoke shared parser paths;
6. documented default task/agent/lane lookup behavior in
   `docs/opencode-host-provisioning-check-guide.md`;
7. added focused runtime and CLI tests.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/opencode_cli_client.py src/runtime/orchestration/runtime_wiring.py src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py src/runtime/orchestration/__init__.py src/__main__.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_cli_process_client_uses_host_session_selector or opencode_cli_process_client_explicit_session_overrides_host_selector or opencode_delivery_supervisor_uses_lane_session_ledger_binding or opencode_delivery_supervisor_prefers_task_binding_over_lane_binding or opencode_session_ledger" -q
6 passed, 372 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_delivery_supervisor_help or opencode_delivery_e2e_smoke_help or opencode_delivery_supervisor_loop_help or opencode_session" -q
6 passed, 142 deselected
```

No screenshot validation is required because this gate does not implement UI.

## Remaining OpenCode Work

OpenCode now has a usable durable receipt-to-delivery path for lane continuity.
Remaining parity work:

1. stale binding recovery/expiry policy;
2. optional host-owned `opencode serve` start/stop receipt contract;
3. direct server adapter, only after session lifecycle semantics stabilize;
4. provider-generic naming cleanup for historical `CodexDelivery...` product
   types.
