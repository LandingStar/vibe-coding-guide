# Planning Gate - Runtime Receipt Evidence Log Decoration Adapters

Date: 2026-07-05

Status: COMPLETED / VERIFIED

## Purpose

Extend the bottom-layer runtime log decoration adapter set to cover compact
receipt/evidence records that were found during the completion audit of the
existing log-like record adoption work.

The previous gates covered event logs, audit records, exchange history, runtime
invocation records, lifecycle events, and batch decoration. This gate closes the
nearby runtime-owned receipt/evidence gap without changing the core
`LogDecorationPipeline`.

## Scope

1. Add explicit read-only projection adapters for:
   - OpenCode serve lifecycle receipts;
   - agent scratch cleanup receipts;
   - git-worktree command receipts;
   - git-worktree sandbox receipts;
   - sandbox allocations;
   - sandbox allocation receipt evidence and compact summaries.
2. Register those adapters in the generic
   `log_like_record_to_decoration_record` dispatcher.
3. Export the adapters from the orchestration package.
4. Document the stricter receipt/evidence projection rule.
5. Add focused tests proving projection, dispatch, and no raw payload copying.

## Non-Goals

This gate does not:

1. mutate or rewrite any receipt/evidence stores;
2. add CLI or MCP flags;
3. persist decoration results;
4. decorate UI-only presentation cards or host evidence display models;
5. copy raw command stdout/stderr, metadata values, path lists, or embedded
   evidence payloads into decoration fields.

## Acceptance Criteria

This gate closes only when:

1. receipt/evidence adapters project through `LogDecorationPipeline`;
2. generic dispatch accepts the new runtime-owned receipt types;
3. projected fields contain ids/status/counts/key lists but not raw/bulky
   receipt payloads;
4. docs explain the receipt/evidence boundary;
5. focused tests and whitespace checks pass.

## Implementation

Runtime:

- Added receipt/evidence adapters in
  `src/runtime/orchestration/log_decoration_adapters.py`.
- Extended `log_like_record_to_decoration_record`.
- Exported adapters from `src/runtime/orchestration/__init__.py`.

Docs:

- Updated `docs/runtime-log-decoration-contract.md` with current
  receipt/evidence coverage and projection limits.

Tests:

- Added focused receipt/evidence adapter coverage to
  `tests/test_runtime_orchestration.py`.

## Verification

```text
python -m py_compile src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/__init__.py
passed

python -m pytest tests/test_runtime_orchestration.py -k "log_decoration_adapters_project_runtime_receipts_and_evidence or log_like_record_to_decoration_record_dispatches_supported_records or decorate_log_like_records_batches_supported_records_and_errors" -q
3 passed, 475 deselected

python -m py_compile src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

python -m pytest tests/test_runtime_orchestration.py -k "log_decoration or decorate_log_like_records or log_like_record_to_decoration_record or runtime_invocation_log_inspection" -q
13 passed, 465 deselected

python -m pytest tests/test_runtime_orchestration_agent_communication.py -k "agent_exchange_history" -q
4 passed, 24 deselected

python -m pytest tests/test_cli.py -k "inspect_runtime_invocations or inspect_monitoring_snapshot or agent_history" -q
2 passed, 179 deselected

git diff --check -- src/runtime/orchestration/log_decoration_adapters.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py docs/runtime-log-decoration-contract.md design_docs/stages/planning-gate/2026-07-05-runtime-receipt-evidence-log-decoration-adapters.md "design_docs/Project Master Checklist.md" .codex/progress-graph/local-work-trajectory.json
passed with Windows LF-to-CRLF warnings only

impact_analysis over the touched runtime/docs files returned no direct or
transitive impact nodes.
```

## Notes

This is intentionally still an adapter-layer improvement. The neutral core
pipeline continues to decorate one `LogDecorationRecord`; concrete runtime
receipt/evidence projection remains explicit and source-aware.

Completion audit notes:

- `RuntimeAttemptRecord` remains covered through `RuntimeInvocationRecord`
  inspection for now because attempts are embedded subrecords, not independent
  append-only log entries.
- `AgentExchangeHistoryLogEntry` remains covered by the existing
  source-aware exchange-history readback path because it needs per-entry
  artifact/version context.
- Host scheduler run evidence, scheduler loop evidence, supervisor storage
  binding evidence, scheduler authorization summaries, and monitoring/UI
  readbacks are not routed through the generic dispatcher in this gate. They
  either embed large run results, represent diagnostic/UI read models, or need
  a separate compact-summary policy before being treated as common log-like
  records.
