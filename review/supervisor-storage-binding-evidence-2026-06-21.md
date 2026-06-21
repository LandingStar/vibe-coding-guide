# Review - Supervisor Storage Binding Evidence

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-evidence.md`

## Scope Reviewed

This slice made `SupervisorAgentStorageBinding` durable as an explicit evidence
product while preserving the product/readback-only boundary.

Implemented:

1. Core runtime evidence product:
   - `src.runtime.orchestration.supervisor_storage_binding_evidence`
   - `SupervisorStorageBindingEvidence`
   - `SupervisorStorageBindingEvidenceWriteResult`
   - `SupervisorStorageBindingEvidenceSummary`
   - `build_supervisor_storage_binding_evidence()`
   - `default_supervisor_storage_binding_evidence_path()`
   - `write_supervisor_storage_binding_evidence()`
   - `read_supervisor_storage_binding_evidence_summary()`
2. Runtime exports from `src.runtime.orchestration`.
3. Existing Host Evidence readback compatibility:
   - `read_host_evidence_bundle()` recognizes
     `supervisor_storage_binding_evidence`;
   - `build_host_evidence_presentation()` can render a compact readback card for
     the new summary type.
4. Focused runtime and progress-graph tests.

The Host Evidence compatibility is read-only presentation compatibility for the
existing evidence bundle path. It does not add a new CLI command, MCP tool,
Host UX action, scheduler workflow, or runtime mutation.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/supervisor_storage_binding_evidence.py src/runtime/orchestration/__init__.py tools/progress_graph/host_evidence.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_storage_binding_evidence or supervisor_dogfood_storage_binding or supervisor_agent_storage_binding or scheduler_supervisor_dogfood_workflow"
6 passed, 249 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence_bundle_reads_supervisor_storage_binding_evidence or host_evidence_bundle_reads_scheduler_loop_evidence_summary or host_evidence_bundle_reads_sandbox_allocation_cleanup_evidence"
3 passed, 66 deselected
```

Adjacent validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_storage_binding_evidence or supervisor_dogfood_storage_binding or supervisor_agent_storage_binding or scheduler_supervisor_dogfood_workflow or sandbox_allocation_receipt_evidence or scheduler_loop_evidence_summary or host_scheduler_run_evidence_summary"
11 passed, 244 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence_bundle or host_evidence_presentation"
9 passed, 60 deselected

git diff --check -- src/runtime/orchestration/supervisor_storage_binding_evidence.py src/runtime/orchestration/__init__.py tools/progress_graph/host_evidence.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-evidence.md
passed
```

Change analysis:

```text
analyze_changes(...)
impact.direct = []
impact.transitive = []
coupling.alerts = []
```

## Behavioral Notes

The evidence JSON contains:

1. compact top-level identity fields;
2. scheduler task/context/lane/session facts;
3. home registration and scratch-space clues;
4. source snapshot path;
5. authority split facts;
6. embedded raw binding payload for audit/replay.

The summary helper intentionally omits the embedded raw `binding` payload. It
returns only compact facts suitable for readback, evidence bundle scanning, and
future resource surfaces.

The default evidence path uses `.codex/scheduler/evidence/<safe-id>.json`, where
unsafe id characters are replaced with `-`.

## Explicit Non-Goals Preserved

This slice did not:

1. add a new CLI command, MCP tool/resource, or Host UX action;
2. represent binding as an `ExchangeArtifact`;
3. run live Qoder or any real provider;
4. create agent home directories;
5. create scratch directories;
6. write scratch manifests;
7. approve persistent home registration;
8. archive, promote, delete, or clean scratch content;
9. refresh scheduler projection;
10. mutate scheduler state;
11. mutate Local Work Trajectory from runtime/workflow code.

The only durable write in scope is the explicitly requested evidence JSON file.

## Follow-Up

The next narrow backend slice should make the supervisor storage binding product
consumable by the agent coordination layer as a versioned intermediate product,
most likely through an `ExchangeArtifact` projection. Host UX should remain
downstream of that product contract.
