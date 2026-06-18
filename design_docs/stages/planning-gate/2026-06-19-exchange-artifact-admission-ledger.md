# Planning Gate - Exchange Artifact Admission Ledger

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/exchange-artifact-admission-after-workflow-polish-direction-analysis.md`
recommends adding a narrow admission ledger before exposing stored-artifact
admission through broader mutation surfaces such as MCP tools or daemon loops.

## Problem

The current operator workflow can inspect a stored scheduler submission
artifact, admit it into scheduler snapshot/event-log state, read back scheduler
state, and refresh scheduler-derived projection. However, it does not keep a
durable record that a specific `(artifact_id, version)` was already admitted.

That leaves repeated exact-version admission ambiguous:

1. It may be an accidental duplicate.
2. It may be an intentional replacement of scheduler task state.
3. It may be a deliberate re-admission for another scheduler state path.

Before an agent-callable MCP write tool or daemon loop exists, the project needs
a small, explicit admission ledger.

## Scope

### Slice 1 - Ledger Contract

Add a local admission ledger contract with records for exact stored-artifact
admission attempts.

Required fields:

```text
schema_version
ledger_id
artifact_store_path
artifact_id
artifact_version
product_type
surface
actor
timestamp
snapshot_path
event_log_path
status
submitted_task_ids
dependency_ids
submission_event_ids
error_summary
duplicate_of
allow_duplicate
```

First-version status values:

```text
admitted
rejected_duplicate
failed
```

### Slice 2 - Local Store

Add a project-local JSON ledger store, defaulting to:

```text
.codex/orchestration/exchange-artifact-admissions.json
```

The store should support:

1. Append/read all records.
2. Find previous successful admissions for exact `(artifact_id, version)`.
3. JSON round-trip tests.
4. Isolated, readable errors for malformed stores where appropriate.

### Slice 3 - Admission Integration

Integrate the ledger with CLI admission only in this gate.

Add CLI options:

```text
--admission-ledger-path PATH
--allow-duplicate-admission
--actor ACTOR
```

Behavior:

1. Default `--admission-ledger-path` to
   `.codex/orchestration/exchange-artifact-admissions.json`.
2. Before scheduler mutation, reject a duplicate exact artifact/version when a
   previous `admitted` record exists and `--allow-duplicate-admission` is not
   present.
3. On duplicate rejection, append a `rejected_duplicate` ledger record and do
   not mutate scheduler snapshot/event-log state.
4. On successful admission, append an `admitted` record after scheduler state is
   written.
5. On admission failure after duplicate preflight passes, append a `failed`
   record when enough artifact identity and path context is available.
6. Keep `--allow-duplicate-admission` distinct from `--replace-existing`:
   duplicate admission controls ledger replay policy, while replace-existing
   controls scheduler task replacement semantics.

### Slice 4 - Readback

Add a minimal CLI readback command:

```text
doc-based-coding scheduler inspect-admissions
```

Required / optional options:

```text
--admission-ledger-path PATH
--artifact-id ID
--version VERSION
```

Behavior:

1. Read ledger records.
2. Filter by artifact ID/version when provided.
3. Print compact JSON counts, statuses, exact record summaries, and authority
   clues.
4. Do not mutate scheduler state, exchange store, projection artifacts, or Local
   Work Trajectory.

## Non-Goals

This gate does not:

1. Add a stored-artifact MCP admission/write tool.
2. Add scheduler daemon behavior or durable queue processing.
3. Add UI binding.
4. Run fake, Qoder, or any other provider.
5. Mark exchange artifacts consumed inside the exchange artifact store.
6. Redesign scheduler snapshot/event-log authority.
7. Mutate `.codex/progress-graph/local-work-trajectory.json`.

## Acceptance Criteria

The gate may close when:

1. Ledger contract and default path are documented and exported.
2. Successful CLI admission appends an `admitted` ledger record.
3. Duplicate exact artifact/version admission is rejected by default before
   scheduler mutation and records `rejected_duplicate`.
4. `--allow-duplicate-admission` permits explicit duplicate admission while
   recording `allow_duplicate=true`.
5. `--replace-existing` remains separate from duplicate admission policy.
6. `inspect-admissions` reports ledger summaries without mutation.
7. Focused CLI/runtime/doc-loop tests pass.
8. Review and status docs record that MCP write exposure, daemon, UI, provider
   execution, and exchange-store consumed marking remain deferred.

## Implementation Summary

Completed on 2026-06-19.

Implemented:

1. `src/runtime/orchestration/exchange_admission_ledger.py`
   - `ExchangeArtifactAdmissionRecord`
   - `JsonExchangeArtifactAdmissionLedger`
   - `ExchangeArtifactAdmissionLedgerInspection`
   - `default_exchange_artifact_admission_ledger_path()`
   - `inspect_exchange_artifact_admission_ledger()`
2. CLI admission integration:
   - `doc-based-coding scheduler admit-exchange-artifact`
   - new options `--admission-ledger-path`, `--allow-duplicate-admission`,
     and `--actor`
   - default ledger path
     `.codex/orchestration/exchange-artifact-admissions.json`
   - duplicate exact artifact/version admission is rejected before scheduler
     mutation unless `--allow-duplicate-admission` is present
3. CLI readback:
   - `doc-based-coding scheduler inspect-admissions`
   - optional `--artifact-id` / `--version` filters
4. Prompt guidance synchronized in:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
   - `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
274 passed
```

## Close Notes

The ledger is an audit/readback product for exact stored-artifact admission
attempts. It does not make the exchange artifact store scheduler authority and
does not mark artifacts consumed inside the exchange store.

The next mutation surface remains out of scope. Stored-artifact MCP admission,
scheduler daemon processing, UI binding, provider execution, and
exchange-store lifecycle consumed marking require separate planning gates.
