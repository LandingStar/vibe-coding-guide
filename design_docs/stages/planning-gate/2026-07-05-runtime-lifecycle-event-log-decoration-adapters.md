# Planning Gate - Runtime Lifecycle Event Log Decoration Adapters

Date: 2026-07-05

Status: COMPLETED / VERIFIED

## Purpose

Expand the bottom-layer log decoration adapter coverage to existing runtime
lifecycle event records.

Runtime invocation audit and agent exchange history now have concrete readback
wiring. The remaining runtime lifecycle logs still need a common way to enter
the decoration pipeline before higher-level readbacks decide whether to expose
decoration evidence.

## Scope

Add read-only adapters for:

1. `ContinuousWorkerBindingEventRecord`
2. `LaneOwnershipEventRecord`
3. `DeliveryLeaseEventRecord`
4. `LeaderWorkerDeliveryEventRecord`
5. `TrajectoryTeamContinuityEventRecord`

Each adapter should:

- preserve source record kind and stable ids;
- include lifecycle/status transition fields;
- expose metadata keys only, not freeform metadata values;
- return `LogDecorationRecord` without mutating source logs or ledgers.

## Non-Goals

This gate does not:

1. add readback wiring for every event log;
2. add CLI/MCP flags;
3. rewrite existing event JSONL records;
4. change lifecycle transition semantics;
5. copy raw/freeform metadata payload values into decoration records.

## Acceptance Criteria

This gate closes only when:

1. All scoped lifecycle event records have adapter functions.
2. Adapter functions are exported from `src.runtime.orchestration`.
3. Focused tests show each adapter can run through `LogDecorationPipeline`.
4. Tests prove metadata values are not copied into projected fields.
5. Documentation lists the adapter coverage and remaining readback-wiring
   boundary.

## Implementation

Runtime:

- Added lifecycle event projection helpers to
  `src/runtime/orchestration/log_decoration_adapters.py`.
- Exported the helpers from `src/runtime/orchestration/__init__.py`.

Docs:

- Updated `docs/runtime-log-decoration-contract.md` adapter list.

Tests:

- Added focused lifecycle adapter coverage in
  `tests/test_runtime_orchestration.py`.

## Verification

```text
python -m py_compile src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

python -m pytest tests/test_runtime_orchestration.py -k "log_decoration_adapters_project_runtime_lifecycle_events or log_decoration" -q
7 passed, 467 deselected

python -m pytest tests/test_runtime_orchestration.py -k "runtime_invocation_log_inspection or log_decoration" -q
9 passed, 465 deselected

python -m pytest tests/test_runtime_orchestration_agent_communication.py -k "agent_exchange_history" -q
4 passed, 24 deselected

git diff --check -- src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py docs/runtime-log-decoration-contract.md design_docs/stages/planning-gate/2026-07-05-runtime-lifecycle-event-log-decoration-adapters.md "design_docs/Project Master Checklist.md"
passed with Windows LF-to-CRLF warnings only
```

## Notes

This gate expands low-level adapter coverage only. It deliberately does not
wire every event-log readback surface yet; that should be done surface by
surface where consumers need decoration evidence.
