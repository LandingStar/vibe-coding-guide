# Planning Gate - Supervisor Storage Binding Evidence

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/supervisor-agent-home-session-binding-followup-direction-analysis.md`
recommends persisting the supervisor storage/context binding product as durable
evidence before adding Host UX or ExchangeArtifact lifecycle integration.

## Problem

`Supervisor Agent Home Session Binding` created a readback-only product that
connects supervisor run identity to context-session, `AgentHomeRegistration`,
and task-derived `AgentScratchSpace` facts.

That product is not durable. Later Host UX, MCP resources, and audit/replay
surfaces should not reconstruct binding facts from raw workflow internals or
scheduler snapshots. They need a stable evidence product and compact summary
readback.

## Scope

### Slice 1 - Durable Evidence Product

Add a runtime evidence module for supervisor storage binding with:

1. product type and schema version constants;
2. evidence dataclass containing one `SupervisorAgentStorageBinding`;
3. JSON serialization;
4. explicit authority facts.

### Slice 2 - Write And Read Summary Helpers

Add helpers for:

1. default evidence path under `.codex/scheduler/evidence`;
2. build evidence from a binding product;
3. write evidence JSON to an explicit path;
4. read a compact summary without embedding raw binding internals.

Existing Host Evidence bundle/readback may recognize the new evidence product
type so that `.codex/scheduler/evidence/*.json` scanning does not treat it as
an unsupported artifact. This is readback/presentation compatibility only; it
does not add a new MCP tool, CLI command, Host UX action, or scheduler workflow.

### Slice 3 - Focused Tests

Add focused tests for:

1. build/write/read-summary round trip;
2. product type / schema validation errors;
3. authority facts showing no scheduler mutation, no projection refresh, no
   cleanup, and no Local Work Trajectory mutation;
4. adjacent supervisor workflow + binding + evidence path.

## Non-Goals

This gate does not:

1. Add CLI, MCP, or Host UX surface.
2. Represent binding as an `ExchangeArtifact`.
3. Run live Qoder or any real provider.
4. Create agent home directories.
5. Create scratch directories.
6. Write scratch manifests.
7. Approve persistent home registration.
8. Archive, promote, delete, or clean scratch content.
9. Refresh scheduler projection.
10. Mutate scheduler state.
11. Mutate Local Work Trajectory from runtime/workflow code.

The only durable write in scope is the explicitly requested evidence JSON file.

## Acceptance Criteria

The gate may close when:

1. supervisor storage binding evidence can be built and written;
2. summary readback exposes evidence id, timestamp, supervisor/context identity,
   task/context/lane/session ids, home registration clue, scratch count, source
   snapshot path, metadata, and authority facts;
3. malformed product type / schema version are rejected with clear messages;
4. focused tests pass;
5. review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-21.

Implemented:

1. `src.runtime.orchestration.supervisor_storage_binding_evidence`
   - product type and schema version constants;
   - `SupervisorStorageBindingEvidence`;
   - `SupervisorStorageBindingEvidenceWriteResult`;
   - `SupervisorStorageBindingEvidenceSummary`;
   - build, default path, write, and compact summary read helpers.
2. Runtime exports from `src.runtime.orchestration`.
3. Existing Host Evidence bundle/readback compatibility:
   - product dispatch for `supervisor_storage_binding_evidence`;
   - a compact presentation card over existing `HostEvidencePresentation`.
4. Focused runtime and progress-graph tests.

The raw evidence JSON embeds the full binding payload for audit/replay. The
summary readback intentionally omits that embedded payload and exposes compact
identity, scheduler, storage, metadata, and authority facts.

## Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/supervisor_storage_binding_evidence.py src/runtime/orchestration/__init__.py tools/progress_graph/host_evidence.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_storage_binding_evidence or supervisor_dogfood_storage_binding or supervisor_agent_storage_binding or scheduler_supervisor_dogfood_workflow"
6 passed, 249 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence_bundle_reads_supervisor_storage_binding_evidence or host_evidence_bundle_reads_scheduler_loop_evidence_summary or host_evidence_bundle_reads_sandbox_allocation_cleanup_evidence"
3 passed, 66 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_storage_binding_evidence or supervisor_dogfood_storage_binding or supervisor_agent_storage_binding or scheduler_supervisor_dogfood_workflow or sandbox_allocation_receipt_evidence or scheduler_loop_evidence_summary or host_scheduler_run_evidence_summary"
11 passed, 244 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence_bundle or host_evidence_presentation"
9 passed, 60 deselected

git diff --check -- src/runtime/orchestration/supervisor_storage_binding_evidence.py src/runtime/orchestration/__init__.py tools/progress_graph/host_evidence.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-evidence.md
passed
```

`analyze_changes` over the changed runtime, progress-graph, test, and planning
files reported no dependency-graph impact nodes and no coupling alerts.

## Review Evidence

`review/supervisor-storage-binding-evidence-2026-06-21.md`

## Preserved Non-Goals

This slice still did not:

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

The only durable write introduced by this slice is the explicitly requested
supervisor storage binding evidence JSON file.
