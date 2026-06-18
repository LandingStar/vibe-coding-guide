# Planning Gate — ExchangeArtifact Exact-Version Scheduler Admission

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-19-exchange-artifact-store-inspection-and-admission-prep.md`
has reached `COMPLETED`.

The close review recommends the next narrow line:

- `review/exchange-artifact-store-inspection-and-admission-prep-2026-06-19.md`

## Problem

The local `ExchangeArtifact` store can now be inspected through
`dbc://exchange-artifacts/bundle`, including exact artifact versions and
admission-prep candidates. The next missing step is a controlled runtime helper
that admits one exact stored artifact version into scheduler-owned state.

This must not make the artifact store the scheduler authority. The store should
provide the exact submitted coordination product; the scheduler snapshot and
event log remain the task-contract recovery authority after admission.

## Scope

### Slice 1 — Exact-Version Admission Helper

Add a runtime helper that accepts:

```text
artifact_store_path
artifact_id
version
scheduler snapshot_path
scheduler event_log_path
replace_existing
timestamp
```

The helper should:

1. Load the exact `(artifact_id, version)` from `JsonArtifactVersionStore`.
2. Verify that the stored artifact contains exactly one scheduler submission
   product:
   - `scheduler_task_submission`
   - `scheduler_task_batch_submission`
3. Submit task contracts through the existing scheduler submission adapters.
4. Append `task_submitted` audit events.
5. Write the scheduler snapshot through the existing snapshot writer.
6. Return source artifact identity, product type, submitted task IDs,
   submission event IDs, dependency IDs, and path/count metadata.

### Slice 2 — Rejection And Error Clarity

The helper should fail clearly when:

1. The exact artifact version is missing.
2. The store file is malformed or has an unsupported schema.
3. The artifact is not a scheduler submission product.
4. The artifact has ambiguous multiple scheduler submission product payloads.
5. The existing scheduler submission parser rejects malformed task contracts.

### Slice 3 — Guidance And Prompt Surface

Update scheduler prompt guidance to distinguish:

1. Inspection resource: read-only candidate discovery.
2. Exact-version admission helper: controlled Python/runtime helper that writes
   scheduler snapshot and event log.
3. MCP scheduler submit tool: direct batch payload submission surface.

## Non-Goals

This gate does not:

1. Add an MCP write/admission tool for stored artifacts.
2. Add a daemon, watcher, durable queue, provider execution, or scheduler run.
3. Mark exchange artifacts consumed, accepted, rejected, or superseded.
4. Refresh scheduler-derived trajectory projection.
5. Mutate agent-owned Local Work Trajectory.
6. Add UI binding.
7. Replace scheduler snapshot authority with the artifact store.

## Acceptance Criteria

The gate may close when:

1. Exact stored single-task submissions persist into scheduler snapshot and
   event log.
2. Exact stored batch submissions persist into scheduler snapshot and event
   log.
3. Missing exact versions fail with a readable error.
4. Non-submission artifacts are rejected before scheduler mutation.
5. Malformed stores fail with the existing readable store error.
6. Admission does not create Local Work Trajectory or scheduler projection
   artifacts.
7. Focused runtime / MCP / doc-loop prompt tests pass.
8. Status docs and review record the authority split.

## Implementation Notes

### 2026-06-19 — Runtime Helper And Persistence Path

Added:

```text
PersistedSchedulerTaskSubmissionResult
PersistedExchangeArtifactAdmissionResult
submit_scheduler_task_with_persistence()
admit_exchange_artifact_version_to_scheduler()
```

The admission helper reads one exact `(artifact_id, version)` from
`JsonArtifactVersionStore`, rejects missing versions, malformed stores,
non-submission artifacts, and ambiguous multiple scheduler submission payloads,
then delegates to the existing single or batch scheduler submission adapters.

For single-task submissions, `submit_scheduler_task_with_persistence()` now
matches the existing batch persistence shape: submit task contract, append
`task_submitted` audit event, write scheduler snapshot. Both single and batch
paths share the same private event-writing helper.

The helper returns `PersistedExchangeArtifactAdmissionResult`, including source
artifact identity, product type, submitted task IDs, dependency IDs, submission
event IDs, snapshot/event-log paths, state counts, and explicit authority clues:

```text
scheduler_state_authority = scheduler_snapshot
exchange_store_role = exact-version-coordination-product-source
provider_executed = false
scheduler_projection_refreshed = false
local_work_trajectory_mutated = false
```

Updated:

- `src/runtime/orchestration/scheduler_submission.py`
- `src/runtime/orchestration/__init__.py`
- `tests/test_runtime_orchestration.py`
- `tests/test_doc_loop_prompts.py`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "admit_exchange_artifact_version or submit_scheduler_task_batch_with_persistence"
7 passed, 145 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "admit_exchange_artifact_version or json_artifact_version_store or exchange_artifact_store_inspection or scheduler_task_submission or scheduler_task_batch_submission" tests/test_doc_loop_prompts.py -k "scheduler"
60 passed, 110 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
249 passed
```

The final focused pytest run returned exit code 0 after reporting `249 passed`,
but the same Windows/Python access-violation printout observed in the previous
slice appeared after pytest had reported success. This remains a residual
test-process signal rather than a failed assertion.
