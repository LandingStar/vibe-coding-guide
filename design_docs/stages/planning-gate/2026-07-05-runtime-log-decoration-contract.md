# Planning Gate - Runtime Log Decoration Contract

Date: 2026-07-05

Status: COMPLETED / VERIFIED

## Purpose

Create a bottom-layer runtime log decoration contract that can be reused by
ordinary logs, compact audit logs, agent communication history, review records,
lane-splitting records, and later advisory product pools.

This gate responds to the gap that the repository has several event-log and
audit-log stores, but no shared decorator pipeline for attaching, validating,
redacting, rewriting, or summarizing log metadata.

## Scope

Implement the first runtime foundation:

1. `LogDecorationRecord`: neutral log/event record shape.
2. `LogDecorationResult`: per-decorator result and validation errors.
3. `LogDecorator`: protocol for append-only or rewrite-capable decorators.
4. `LogDecorationPipeline`: ordered pipeline that applies decorators and records
   evidence.
5. Built-in decorators:
   - field append decorator;
   - bounded text redaction/rewrite decorator;
   - required-field validator decorator.

## Acceptance Criteria

This gate closes only when:

1. A record can receive append-only metadata without changing its message.
2. A rewrite-capable decorator can redact bounded text and report that it
   rewrote the record.
3. A validator decorator can reject missing required fields with readable
   errors.
4. A pipeline can run multiple decorators and expose stable evidence showing
   decorator ids, operation kind, rewrite flag, and validation errors.
5. The contract is exported from `src.runtime.orchestration`.
6. Focused tests cover append, rewrite, validation, and pipeline evidence.

## Non-Goals

This gate does not:

1. migrate existing audit/event logs;
2. add persistence;
3. expose CLI or MCP surfaces;
4. bind advisory product pools;
5. bind scheduler, Local Work Trajectory, runtime invocation audit, or UI;
6. implement LLM summarization;
7. store raw transcripts.

## Design Inputs

- `src/audit/audit_logger.py`
- `src/runtime/orchestration/exchange.py`
- `src/runtime/orchestration/exchange_store.py`
- `src/runtime/orchestration/runtime_invocation_audit.py`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `docs/advisory-product-pool.md`

## Implementation

Runtime:

- `src/runtime/orchestration/log_decoration.py`
- exported from `src/runtime/orchestration/__init__.py`

Docs:

- `docs/runtime-log-decoration-contract.md`
- `docs/README.md`

Tests:

- `tests/test_runtime_orchestration.py`

## Verification

```text
python -m py_compile src/runtime/orchestration/log_decoration.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py

python -m pytest tests/test_runtime_orchestration.py -k "log_decoration" -q
4 passed, 466 deselected

python -m pytest tests/test_runtime_orchestration.py -k "log_decoration or advisory_product or exchange_" -q
46 passed, 424 deselected

git diff --check -- <touched files>
passed with Windows LF-to-CRLF warnings only

MCP GovernanceTools.analyze_changes for touched files:
impact direct/transitive empty; coupling alerts empty.
```

Note: the local tool invocation also printed an existing pack-lock warning:
`Pack 'doc-loop-vibe-coding' content changed since lock was recorded`. This is
not from the runtime log decoration files and is not treated as this gate's
validation failure.
