# Planning Gate - Log-Like Record Batch Decoration

Date: 2026-07-05

Status: COMPLETED / VERIFIED

## Purpose

Add a small batch utility for decorating existing log-like records through the
common projection adapter dispatcher.

Practical readback wiring showed a gap: each readback surface would otherwise
hand-roll loops, unsupported-record handling, and error evidence. This gate
keeps the core `LogDecorationPipeline` focused on neutral records while adding
adapter-layer batch handling for existing runtime/audit record types.

## Scope

1. Add a batch result shape for log-like record decoration.
2. Add a helper that:
   - projects supported records through `log_like_record_to_decoration_record`;
   - runs a provided `LogDecorationPipeline`;
   - returns per-record evidence;
   - records unsupported-record errors without mutating source logs.
3. Refactor existing runtime invocation and exchange history readback wiring to
   use the helper where suitable.
4. Keep persistence, scheduler, exchange, provider, and Local Work authority
   unchanged.

## Non-Goals

This gate does not:

1. add persistence for decoration results;
2. add CLI/MCP flags;
3. make unsupported records best-effort serializable;
4. rewrite existing logs;
5. change decorator semantics.

## Acceptance Criteria

This gate closes only when:

1. Batch decoration returns successful pipeline results for supported records.
2. Unsupported records produce readable errors and do not stop supported records
   from being decorated.
3. Existing wired readbacks still return their decoration evidence.
4. Focused tests cover success, unsupported-record handling, and existing
   readback compatibility.

## Implementation

Runtime:

- Added `LogLikeRecordBatchDecorationResult`.
- Added `decorate_log_like_records()`.
- Refactored runtime invocation inspection decoration to use the batch helper.
- Kept exchange history source-aware decoration loop in place because each log
  entry needs per-entry artifact/version fields.

Docs:

- Updated `docs/runtime-log-decoration-contract.md`.

Tests:

- Added batch helper coverage to `tests/test_runtime_orchestration.py`.

## Verification

```text
python -m py_compile src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/runtime_invocation_audit.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

python -m pytest tests/test_runtime_orchestration.py -k "decorate_log_like_records or log_like_record_to_decoration_record or runtime_invocation_log_inspection or log_decoration" -q
12 passed, 465 deselected

python -m pytest tests/test_runtime_orchestration_agent_communication.py -k "agent_exchange_history" -q
4 passed, 24 deselected

git diff --check -- src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/runtime_invocation_audit.py src/runtime/orchestration/agent_exchange_history.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py tests/test_runtime_orchestration_agent_communication.py docs/runtime-log-decoration-contract.md design_docs/stages/planning-gate/2026-07-05-log-like-record-batch-decoration.md "design_docs/Project Master Checklist.md"
passed with Windows LF-to-CRLF warnings only
```

## Notes

This gate is a cautious pipeline improvement discovered during adoption. The
core pipeline still decorates one neutral record; the adapter layer owns
projection and batch error isolation for existing concrete log records.
