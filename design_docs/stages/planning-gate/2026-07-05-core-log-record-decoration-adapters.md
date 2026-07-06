# Planning Gate - Core Log Record Decoration Adapters

Date: 2026-07-05

Status: COMPLETED / VERIFIED

## Purpose

Add bottom-layer log decoration adapters for remaining core log-like records
that are not runtime lifecycle events.

This expands the common decoration entry point across scheduler merge-gate
events, leader-worker activation/dispatcher records, normalized runtime run
events, exchange admission ledger records, and legacy decision log entries.

## Scope

Add adapters for:

1. `SchedulerMergeGateEvent`
2. `AgentActivationEvent`
3. `LeaderWorkerDispatcherTickRecord`
4. `RunEvent`
5. `ExchangeArtifactAdmissionRecord`
6. legacy `DecisionLogEntry`

Adapters remain read-only projections. They may expose bounded ids, counts,
status fields, and key lists, but must not copy raw/freeform payload values.

## Non-Goals

This gate does not:

1. wire every readback surface;
2. add CLI/MCP flags;
3. mutate scheduler, dispatcher, admission, runtime, or decision logs;
4. persist decoration evidence as authoritative state;
5. copy raw/freeform metadata or merge conflict payloads into projection
   fields.

## Acceptance Criteria

This gate closes only when:

1. All scoped record types have adapter functions.
2. Adapter functions are exported from `src.runtime.orchestration` when the
   source type is runtime-owned.
3. Focused tests prove adapters run through `LogDecorationPipeline`.
4. Tests prove freeform metadata/payload values are omitted or reduced to keys
   and counts.
5. Documentation records the expanded adapter coverage and remaining boundary.

## Implementation

Runtime:

- Added adapters to `src/runtime/orchestration/log_decoration_adapters.py`.
- Added `log_like_record_to_decoration_record()` as the generic dispatcher for
  supported compact records.
- Exported runtime-owned adapter functions from
  `src/runtime/orchestration/__init__.py`.

Docs:

- Updated `docs/runtime-log-decoration-contract.md` with expanded adapter
  coverage and dispatcher behavior.

Tests:

- Added focused adapter and dispatcher tests to
  `tests/test_runtime_orchestration.py`.

## Verification

```text
python -m py_compile src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

python -m pytest tests/test_runtime_orchestration.py -k "log_decoration_adapters_project_core_log_records or log_like_record_to_decoration_record or log_decoration" -q
9 passed, 467 deselected

python -m pytest tests/test_runtime_orchestration.py -k "runtime_invocation_log_inspection or log_decoration" -q
10 passed, 466 deselected

python -m pytest tests/test_runtime_orchestration_agent_communication.py -k "agent_exchange_history" -q
4 passed, 24 deselected

python -m pytest tests/test_cli.py -k "inspect_runtime_invocations or inspect_monitoring_snapshot or agent_history" -q
2 passed, 179 deselected

git diff --check -- src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/agent_exchange_history.py src/runtime/orchestration/runtime_invocation_audit.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py tests/test_runtime_orchestration_agent_communication.py docs/runtime-log-decoration-contract.md design_docs/stages/planning-gate/2026-07-05-core-log-record-decoration-adapters.md "design_docs/Project Master Checklist.md"
passed with Windows LF-to-CRLF warnings only
```

## Notes

This gate still does not make every readback surface emit decoration evidence.
It establishes a common bottom-layer projection entry point so readback wiring
can be added deliberately and consistently.
