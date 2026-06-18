# Planning Gate - Stored-Artifact MCP Admission Tool

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/exchange-artifact-admission-ledger-followup-direction-analysis.md`
recommends exposing a narrow MCP write tool after the durable admission ledger
has made duplicate/audit semantics explicit.

## Problem

The current operator workflow can admit an exact stored scheduler submission
artifact through CLI and record the attempt in
`.codex/orchestration/exchange-artifact-admissions.json`. MCP hosts can inspect
stored artifacts through `dbc://exchange-artifacts/bundle`, but they still lack
a direct, structured tool for admitting one exact stored artifact version.

Shelling out to CLI is workable for humans and host scripts, but agent-facing
or host-facing MCP flows should be able to use the same admission behavior
without bypassing the ledger duplicate policy.

## Scope

### Slice 1 - Tool Contract

Add one MCP tool surface on `GovernanceTools`:

```text
admit_exchange_artifact
```

Required inputs:

```text
artifact_id
version
snapshot_path
event_log_path
```

Optional inputs:

```text
artifact_store_path
admission_ledger_path
allow_duplicate_admission
replace_existing
actor
timestamp
```

Input aliases may follow the existing MCP camelCase normalization style where
appropriate, but the canonical returned payload should use snake_case.

### Slice 2 - Runtime Reuse

The tool must reuse the same exact-version admission behavior as CLI:

1. Read the exact `(artifact_id, version)` from `JsonArtifactVersionStore`.
2. Require exactly one `scheduler_task_submission` or
   `scheduler_task_batch_submission` payload.
3. Write scheduler snapshot and event-log state only through existing
   scheduler submission adapters.
4. Append an admission ledger record.
5. Reject duplicate exact artifact/version admission by default before
   scheduler mutation when a previous `admitted` record exists.
6. Permit explicit duplicate admission only when
   `allow_duplicate_admission=true`.
7. Keep duplicate admission policy separate from scheduler
   `replace_existing` semantics.

### Slice 3 - Output Contract

Successful output must include at least:

```text
ok
artifact_store_path
admission_ledger_path
admission_ledger_record_id
product_type
source_artifact_id
source_artifact_version
snapshot_path
event_log_path
submitted_task_ids
dependency_ids
submission_event_ids
task_count
dependency_count
state_written
ran_tasks
refreshed_projection
authority_split
```

Duplicate rejection must return a structured non-throwing payload with:

```text
ok=false
error
admission_ledger_path
admission_ledger_record_id
duplicate_of
artifact_id
version
scheduler_state_mutated=false
event_log_mutated=false
authority_split
```

Other failures may return structured error payloads, and should append a
`failed` ledger record when artifact identity and path context are available.

### Slice 4 - Tests And Guidance

Add focused tests for:

1. Successful MCP exact-version admission writes scheduler state and ledger.
2. Duplicate admission is rejected before scheduler mutation.
3. `allow_duplicate_admission=true` permits explicit duplicate admission.
4. `replace_existing` remains separate from duplicate policy.
5. Failure paths do not run providers, refresh projection, or mutate Local Work
   Trajectory.
6. Prompt guidance mentions the MCP tool and ledger policy.

## Non-Goals

This gate does not:

1. Add scheduler daemon behavior or durable queue processing.
2. Run fake, Qoder, or any other provider.
3. Refresh scheduler-derived projection automatically.
4. Add UI binding.
5. Mark exchange artifacts consumed inside the exchange artifact store.
6. Redesign scheduler snapshot/event-log authority.
7. Mutate `.codex/progress-graph/local-work-trajectory.json` from the scheduler
   admission tool.
8. Add broad artifact write/update tools beyond exact scheduler admission.

## Acceptance Criteria

The gate may close when:

1. MCP `admit_exchange_artifact` is implemented and returns compact authority
   clues.
2. Successful admission appends an `admitted` ledger record.
3. Duplicate exact artifact/version admission is rejected by default before
   scheduler mutation and records `rejected_duplicate`.
4. `allow_duplicate_admission=true` permits explicit duplicate admission while
   recording `allow_duplicate=true`.
5. `replace_existing` remains separate from duplicate admission policy.
6. Focused MCP/runtime/CLI/doc-loop tests pass.
7. Review and status docs record that daemon, provider execution, UI binding,
   projection refresh, and exchange-store consumed marking remain deferred.

## Implementation Summary

This gate closed the stored-artifact MCP admission gap by adding one narrow MCP
write tool:

```text
admitExchangeArtifact
```

Implemented behavior:

1. `GovernanceTools.admit_exchange_artifact()` validates the required MCP
   inputs and resolves relative paths under the MCP project root.
2. MCP `admitExchangeArtifact` is registered in `src/mcp/server.py` with
   camelCase input fields and snake_case output payloads.
3. CLI and MCP admission now share
   `admit_exchange_artifact_version_with_ledger()`, so duplicate/audit policy
   has one runtime implementation.
4. Duplicate exact artifact/version admission is rejected by default before
   scheduler mutation and records `rejected_duplicate`.
5. `allowDuplicateAdmission=true` permits intentional replay and records
   `allow_duplicate=true`.
6. `replaceExisting` remains scheduler task replacement semantics only; it does
   not bypass admission-ledger duplicate policy.
7. Scheduler smoke prompts now describe both CLI and MCP admission surfaces.

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py::TestAdmitExchangeArtifact tests/test_cli.py::test_scheduler_admit_exchange_artifact_cli_submits_exact_single_task tests/test_cli.py::test_scheduler_admit_exchange_artifact_cli_rejects_duplicate_before_scheduler_mutation tests/test_cli.py::test_scheduler_admit_exchange_artifact_cli_allows_explicit_duplicate_admission
8 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py
18 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py::TestAdmitExchangeArtifact
5 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
279 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py::test_admit_exchange_artifact_version_with_ledger_rejects_duplicate_before_scheduler_mutation
1 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
198 passed
```

Note: `tests/test_mcp_tools.py` is a local ignored MCP test harness in this
workspace. The committed regression surface for this gate is
`tests/test_mcp_admission.py` plus the existing tracked CLI/runtime/doc-loop
tests.

## Close Notes

This gate does not execute providers, refresh scheduler projection
automatically, launch a daemon, bind UI, mutate exchange-store consumed state,
or mutate agent-owned Local Work Trajectory from the scheduler admission tool.
