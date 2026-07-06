# Planning Gate - Runtime Log Decoration Existing Record Adoption

Date: 2026-07-05

Status: COMPLETED / VERIFIED

## Purpose

Adopt the runtime log decoration contract for existing log-like runtime and
audit records without migrating their storage systems.

The previous gate created the bottom-layer decoration contract. This gate
proves that existing compact logs can enter that common pipeline through stable
projection adapters while preserving each source log's authority and JSONL
semantics.

## Scope

First adoption slice:

1. Add adapter functions that project these records into `LogDecorationRecord`:
   - `ExchangeLog`
   - `CoordinationEvent`
   - `SchedulerEvent`
   - `RuntimeInvocationRecord`
   - legacy `AuditEvent`
2. Preserve source identity in compact fields/decorations:
   source record kind, source id, correlation/task/run/artifact ids, lifecycle
   status, and source channel.
3. Keep adapter functions read-only and side-effect free.
4. Add focused tests showing projected records can pass through the existing
   decoration pipeline.

## Non-Goals

This gate does not:

1. rewrite existing JSONL stores;
2. add CLI or MCP surfaces;
3. make decoration persistence authoritative;
4. migrate raw audit details or runtime metadata wholesale;
5. store raw runtime transcripts;
6. change scheduler, exchange, runtime invocation, audit, or Local Work
   Trajectory mutation authority.

## Acceptance Criteria

This gate closes only when:

1. Each scoped source record can be projected into a valid `LogDecorationRecord`.
2. Projection preserves source identity and important relation ids in bounded
   structured fields.
3. Projection deliberately avoids copying arbitrary freeform metadata/detail
   payloads into the neutral record.
4. The projected records can run through `LogDecorationPipeline` with required
   field validation and append-only decorators.
5. Tests verify that projection and decoration do not mutate existing
   persistence authority or source records.
6. `docs/runtime-log-decoration-contract.md` documents the current adapters and
   their limits.

## Implementation Plan

- Runtime:
  - `src/runtime/orchestration/log_decoration_adapters.py`
  - exports from `src/runtime/orchestration/__init__.py`
- Tests:
  - focused adapter tests in `tests/test_runtime_orchestration.py`
- Docs:
  - update `docs/runtime-log-decoration-contract.md`
  - update this gate with verification evidence

## Implementation

Runtime:

- Added `src/runtime/orchestration/log_decoration_adapters.py`.
- Exported adapter helpers from `src/runtime/orchestration/__init__.py`.

Tests:

- Added focused tests for exchange/coordination projection.
- Added focused tests for scheduler/runtime-invocation/legacy-audit projection.

Docs:

- Updated `docs/runtime-log-decoration-contract.md` with the current adapter
  list and limits.

## Verification

```text
python -m py_compile src/runtime/orchestration/log_decoration.py src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

python -m pytest tests/test_runtime_orchestration.py -k "log_decoration" -q
6 passed, 466 deselected

python -m pytest tests/test_runtime_orchestration.py -k "log_decoration or advisory_product or exchange_" -q
48 passed, 424 deselected

python -m pytest tests/test_audit_system.py -q
39 passed

git diff --check -- src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py docs/runtime-log-decoration-contract.md design_docs/stages/planning-gate/2026-07-05-runtime-log-decoration-existing-record-adoption.md "design_docs/Project Master Checklist.md"
passed with Windows LF-to-CRLF warnings only
```

## Notes

This gate intentionally leaves existing JSONL stores untouched. The adapters are
safe adoption points for later monitor/review/communication products that need a
shared log decoration pipeline without moving ownership away from scheduler,
exchange, runtime invocation audit, legacy audit, or Local Work Trajectory.
