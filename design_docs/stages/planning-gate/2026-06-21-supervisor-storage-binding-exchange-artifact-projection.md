# Planning Gate - Supervisor Storage Binding ExchangeArtifact Projection

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/supervisor-storage-binding-evidence-followup-direction-analysis.md`
recommends making durable supervisor storage binding evidence consumable by the
coordination layer as a versioned intermediate product.

## Problem

`SupervisorStorageBindingEvidenceSummary` is durable and compact, but it is
still only an evidence readback product. Scheduler-adjacent agents need a stable
`ExchangeArtifact` shape that can be versioned, validated, referenced, and later
admitted without re-reading raw workflow internals or embedding the raw binding
payload.

## Scope

### Slice 1 - Projection Helper

Add a narrow helper that projects one
`SupervisorStorageBindingEvidenceSummary` into a compact `ExchangeArtifact`.

The artifact should:

1. use existing exchange primitives and validation rules;
2. include evidence product type/schema version/id/path/timestamp;
3. include binding id, supervisor/session/run/host/requester identity;
4. include agent/context-session identity;
5. include scheduler task/context/lane ids and runtime session ids;
6. include home registration id/audit state and scratch ids/count;
7. include source snapshot path, metadata, and authority facts;
8. reference the durable evidence file explicitly;
9. avoid embedding the raw `binding` payload.

### Slice 2 - Focused Tests

Add focused tests for:

1. projected artifact validates through `validate_exchange_artifact()`;
2. artifact id/version/producer/audience defaults and explicit overrides;
3. payload part types include scheduler-readable storage facts and an evidence
   reference;
4. compact structured data carries expected summary fields;
5. raw `binding` is absent from all payload data;
6. authority facts preserve the readback-only boundary.

## Non-Goals

This gate does not:

1. add scheduler admission;
2. add CLI, MCP, or Host UX surface;
3. mark artifacts consumed;
4. run live Qoder or any real provider;
5. create agent home directories;
6. create scratch directories;
7. write scratch manifests;
8. approve persistent home registration;
9. archive, promote, delete, or clean scratch content;
10. refresh scheduler projection;
11. mutate scheduler state;
12. mutate Local Work Trajectory from runtime/workflow code.

## Acceptance Criteria

The gate may close when:

1. `SupervisorStorageBindingEvidenceSummary` can be projected into a valid
   `ExchangeArtifact`;
2. the artifact contains compact summary, storage-manifest, evidence, and file
   reference payload parts;
3. the artifact scope is conservative and does not force lossy single task/lane
   choices when the summary contains multiple ids;
4. raw binding payload is not embedded in artifact parts;
5. focused and adjacent runtime tests pass;
6. review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-21.

Implemented:

1. `SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE` and
   `SUPERVISOR_STORAGE_BINDING_ARTIFACT_SCHEMA_VERSION`;
2. `supervisor_storage_binding_evidence_summary_to_artifact()`;
3. runtime exports from `src.runtime.orchestration`;
4. focused tests for default projection, explicit identity overrides,
   validation, JSON round-trip, exact-version store write, and raw binding
   exclusion.

The projection uses existing `ExchangeArtifact` primitives with:

1. `kind="retention"` and `intent="inform"`;
2. compact `structured` summary payload;
3. scheduler-readable `storage_manifest`;
4. `evidence` payload and file `ref` to the durable evidence JSON;
5. compact projection `log`.

The artifact scope is conservative: it fills single-value scope fields only
when the summary contains exactly one id. Full task/context/lane/runtime lists
remain in the structured payload.

## Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/supervisor_storage_binding_evidence.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_storage_binding_evidence or supervisor_dogfood_storage_binding or supervisor_agent_storage_binding or scheduler_supervisor_dogfood_workflow"
8 passed, 249 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_storage_binding_evidence or supervisor_dogfood_storage_binding or supervisor_agent_storage_binding or scheduler_supervisor_dogfood_workflow or agent_home_registration or scratch_manifest or cleanup_receipt or exchange_artifact_json_round_trip or exchange_artifact_version_store"
14 passed, 243 deselected

git diff --check -- src/runtime/orchestration/supervisor_storage_binding_evidence.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-exchange-artifact-projection.md
passed
```

`analyze_changes` over the changed runtime, test, and planning files reported
no dependency-graph impact nodes and no coupling alerts.

## Review Evidence

`review/supervisor-storage-binding-exchange-artifact-projection-2026-06-21.md`

## Preserved Non-Goals

This slice still did not:

1. add scheduler admission;
2. add CLI, MCP, or Host UX surface;
3. mark artifacts consumed;
4. run live Qoder or any real provider;
5. create agent home directories;
6. create scratch directories;
7. write scratch manifests;
8. approve persistent home registration;
9. archive, promote, delete, or clean scratch content;
10. refresh scheduler projection;
11. mutate scheduler state;
12. mutate Local Work Trajectory from runtime/workflow code.
