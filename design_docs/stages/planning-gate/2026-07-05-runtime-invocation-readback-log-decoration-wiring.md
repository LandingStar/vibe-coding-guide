# Planning Gate - Runtime Invocation Readback Log Decoration Wiring

Date: 2026-07-05

Status: COMPLETED / VERIFIED

## Purpose

Wire the runtime log decoration pipeline into an existing bottom-layer readback
path so the contract is not only available as standalone adapters.

The first practical target is runtime invocation audit readback because it is
host-owned, compact, already used by CLI/status/monitoring paths, and close to
the runtime foundation the log decoration contract is meant to support.

## Scope

1. Extend `inspect_runtime_invocation_log()` with optional decoration pipeline
   support.
2. Keep default readback behavior unchanged when no pipeline is provided.
3. Return decoration evidence for latest records only, matching the existing
   `latest_limit` readback boundary.
4. Preserve runtime invocation JSONL authority and read-model-only semantics.
5. Add tests proving decorated readback is side-effect free and does not copy
   raw/freeform metadata into the neutral projected record.

## Non-Goals

This gate does not:

1. add CLI flags;
2. rewrite persisted runtime invocation records;
3. make decoration evidence authoritative storage;
4. decorate scheduler/exchange/legacy audit readback paths;
5. expose raw runtime transcripts.

## Acceptance Criteria

This gate closes only when:

1. `inspect_runtime_invocation_log()` accepts an optional
   `LogDecorationPipeline`.
2. `RuntimeInvocationLogSummary.to_json_dict()` includes decoration evidence
   when provided and remains compatible when it is not.
3. Existing runtime invocation readback tests and CLI tests continue to pass.
4. New tests verify required-field validation and append-only decoration over
   runtime invocation records.
5. Validation confirms no runtime invocation log mutation occurs during
   decorated readback.

## Implementation

Runtime:

- `RuntimeInvocationLogSummary` now carries
  `latest_decoration_results`.
- `inspect_runtime_invocation_log()` accepts optional
  `decoration_pipeline`.
- Runtime invocation records are projected through
  `runtime_invocation_record_to_decoration_record()` before decoration.

Docs:

- `docs/runtime-log-decoration-contract.md` documents the runtime invocation
  readback integration and authority split.

Tests:

- Added decorated runtime invocation inspection coverage to
  `tests/test_runtime_orchestration.py`.

## Verification

```text
python -m py_compile src/runtime/orchestration/runtime_invocation_audit.py src/runtime/orchestration/log_decoration.py src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

python -m pytest tests/test_runtime_orchestration.py -k "runtime_invocation_log_inspection or log_decoration" -q
8 passed, 465 deselected

python -m pytest tests/test_cli.py -k "inspect_runtime_invocations or inspect_monitoring_snapshot" -q
1 passed, 180 deselected

git diff --check -- src/runtime/orchestration/runtime_invocation_audit.py src/runtime/orchestration/log_decoration.py src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py docs/runtime-log-decoration-contract.md design_docs/stages/planning-gate/2026-07-05-runtime-invocation-readback-log-decoration-wiring.md "design_docs/Project Master Checklist.md"
passed with Windows LF-to-CRLF warnings only
```

## Notes

This gate is the first actual runtime readback wiring. It still does not expose
CLI flags or migrate persisted logs; it proves that a real bottom-layer audit
inspection path can run the common decoration pipeline and return evidence
without taking ownership away from the runtime invocation JSONL store.
