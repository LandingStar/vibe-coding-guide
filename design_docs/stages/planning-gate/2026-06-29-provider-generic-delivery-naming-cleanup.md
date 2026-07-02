# Planning Gate - Provider-Generic Delivery Naming Cleanup

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

OpenCode now matches Codex for the host-owned worker runtime path and has
OpenCode-specific serve/session receipt surfaces. The remaining recurring
friction is historical naming: shared delivery products are still exposed
mostly as `CodexDelivery...` even when `runtime_provider="opencode"`.

That naming was acceptable while Codex was the only live CLI worker provider,
but it now obscures the provider-parametric contract and makes OpenCode parity
look weaker than it is.

## Scope

Add provider-generic names without breaking existing Codex callers:

1. introduce `ProviderDelivery...` aliases for shared delivery request,
   result, record, status, and patch publication products;
2. introduce generic helper aliases for shared provider delivery execution and
   smoke/loop products where the behavior is already provider-parametric;
3. keep existing `CodexDelivery...` classes/functions as compatibility names;
4. update exports so new callers can use provider-generic names;
5. add focused tests proving generic names are exported and point to the same
   compatible runtime products;
6. document that this is compatibility-first naming cleanup, not a state
   schema migration.

## Non-Goals

This gate does not:

1. rename source files;
2. rewrite all existing tests/callers to generic names;
3. change JSON output compatibility fields such as historical
   `codex_delivery`;
4. change scheduler/delivery/runtime behavior;
5. alter Codex or OpenCode CLI invocation semantics;
6. expose live provider execution through MCP;
7. mutate Local Work Trajectory.

## Acceptance Criteria

This gate may close when:

1. provider-generic aliases are exported from `src.runtime.orchestration`;
2. generic aliases are identity-compatible with the historical Codex names;
3. focused tests pass for the alias surface;
4. docs/checklist identify remaining naming work, if any, as deeper file/API
   migration rather than a functional OpenCode parity blocker.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "provider_generic_delivery_naming or opencode_delivery_supervisor or codex_delivery_supervisor" -q
```

No screenshot validation is required because this gate does not implement UI.

## Implementation

Completed the compatibility-first provider-generic naming cleanup:

1. added provider-generic aliases for delivery supervisor products:
   `ProviderDeliverySupervisorRequest`,
   `ProviderDeliverySupervisorResult`,
   `ProviderDeliverySupervisorRecord`,
   `ProviderDeliverySupervisorRecordStatus`, and
   `ProviderDeliveryWorkerPatchReviewPublication`;
2. added provider-generic aliases for E2E smoke and bounded loop products:
   `ProviderDeliveryE2ESmokeRequest`,
   `ProviderDeliveryE2ESmokeResult`,
   `ProviderDeliveryBoundedLoopRequest`,
   `ProviderDeliveryBoundedLoopResult`, and related iteration/stop names;
3. added helper aliases for provider-specific execution entry points:
   `run_provider_delivery_supervisor_once_for_codex()`,
   `run_provider_delivery_supervisor_once_for_opencode()`,
   `run_provider_delivery_e2e_smoke_for_codex()`,
   `run_provider_delivery_e2e_smoke_for_opencode()`,
   `run_bounded_provider_delivery_supervisor_loop_for_codex()`, and
   `run_bounded_provider_delivery_supervisor_loop_for_opencode()`;
4. exported the generic aliases from `src.runtime.orchestration`;
5. kept historical `CodexDelivery...` names and JSON fields intact for
   compatibility.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/codex_delivery_smoke.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "provider_generic_delivery_naming or opencode_delivery_supervisor or codex_delivery_supervisor" -q
22 passed, 362 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "provider_generic_delivery_naming or opencode_delivery_supervisor or opencode_bounded or live_opencode_concurrent_worker_smoke or opencode_runtime_status or opencode_serve_lifecycle or opencode_session_ledger or opencode_session_recover_stale" -q
18 passed, 366 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_delivery_supervisor or opencode_delivery_e2e_smoke or opencode_delivery_supervisor_loop or live_opencode_concurrent_worker_smoke or opencode_runtime_status or opencode_serve_lifecycle or opencode_session" -q
28 passed, 125 deselected
```

## Remaining OpenCode Work

OpenCode now has provider-generic delivery naming aliases for the shared worker
runtime path. Remaining OpenCode-specific work is a direct server/API adapter,
only after lifecycle semantics remain stable.
