# Planning Gate - Supervisor Storage Binding Artifact Admission Readiness

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/supervisor-storage-binding-exchange-artifact-projection-followup-direction-analysis.md`
recommends defining how downstream scheduler submissions can depend on exact
supervisor storage binding artifact versions.

## Problem

`supervisor_storage_binding_evidence_summary_to_artifact()` can produce a valid,
versioned `ExchangeArtifact`, but scheduler task submissions currently treat
all `input_artifact_refs` as generic references. A downstream task can carry a
reference, yet there is no narrow contract check that proves the reference is:

1. exact-versioned;
2. present in the local artifact store;
3. a supervisor storage binding artifact projection;
4. compact and not a raw evidence/binding payload dependency.

## Scope

### Slice 1 - Binding Artifact Reference Contract

Define the first stable reference convention for task submissions that consume
supervisor storage binding artifacts:

1. reference kind;
2. required artifact id and version fields;
3. accepted projected product type;
4. compact validation result shape.

### Slice 2 - Read-Only Store Validation

Add a helper that validates supervisor storage binding artifact refs against an
existing exact-version `JsonArtifactVersionStore`.

The helper should:

1. accept a `SchedulerTaskSubmission` or parsed task submission refs;
2. read only the exact referenced artifact versions;
3. confirm the referenced artifact contains one compact
   `supervisor_storage_binding_artifact` structured payload;
4. report missing versions, missing/ambiguous product payloads, and wrong
   product types with readable messages;
5. avoid reading raw evidence JSON or embedded raw binding payloads.

### Slice 3 - Optional Admission Preflight

Thread the validator into exact-version scheduler admission as an explicit
opt-in parameter. Default admission behavior must stay compatible.

## Non-Goals

This gate does not:

1. automatically schedule downstream work;
2. mark binding artifacts consumed;
3. change the scheduler runtime execution contract;
4. add CLI, MCP, or Host UX surface;
5. read raw evidence JSON;
6. create agent home directories;
7. create scratch directories;
8. write scratch manifests;
9. approve persistent home registration;
10. archive, promote, delete, or clean scratch content;
11. refresh scheduler projection;
12. mutate Local Work Trajectory from runtime/workflow code.

## Acceptance Criteria

The gate may close when:

1. task submissions can carry an exact supervisor storage binding artifact ref
   using a documented stable convention;
2. a read-only helper validates valid/missing/wrong-product/ambiguous binding
   artifact references;
3. exact-version scheduler admission can opt into this validation before
   scheduler snapshot mutation;
4. focused tests prove validation success and fail-closed behavior;
5. review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-21.

Implemented:

1. `SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND`;
2. `BindingArtifactReferenceValidation`;
3. `validate_supervisor_storage_binding_artifact_refs()`;
4. optional `validate_binding_artifact_refs` preflight on
   `admit_exchange_artifact_version_to_scheduler()`;
5. runtime exports from `src.runtime.orchestration`;
6. focused tests for valid, missing-version, missing-artifact, wrong-product,
   ambiguous-product, and admission fail-closed behavior.

The reference convention is exact-versioned and read-only:

```text
ExchangeReference(
    ref_kind="supervisor_storage_binding_artifact",
    ref_id="<binding artifact id>",
    version="<exact artifact version>",
)
```

The validator only reads the existing `JsonArtifactVersionStore`. It checks the
referenced artifact has exactly one compact
`supervisor_storage_binding_artifact` structured payload and does not read raw
evidence JSON.

## Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_submission.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_storage_binding_artifact_refs or supervisor_storage_binding_evidence or admit_exchange_artifact_version"
15 passed, 246 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_storage_binding_artifact_refs or supervisor_storage_binding_evidence or admit_exchange_artifact_version or scheduler_task_submission"
17 passed, 244 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "admit or operator_workflow or seed_dogfood_fixture"
10 passed, 35 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "admit or scheduler_operator_workflow"
3 passed, 10 deselected

git diff --check -- src/runtime/orchestration/scheduler_submission.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-artifact-admission-readiness.md
passed
```

`analyze_changes` over the changed runtime, test, and planning files reported
no dependency-graph impact nodes and no coupling alerts.

## Review Evidence

`review/supervisor-storage-binding-artifact-admission-readiness-2026-06-21.md`

## Preserved Non-Goals

This slice still did not:

1. automatically schedule downstream work;
2. mark binding artifacts consumed;
3. change the scheduler runtime execution contract;
4. add CLI, MCP, or Host UX surface;
5. read raw evidence JSON;
6. create agent home directories;
7. create scratch directories;
8. write scratch manifests;
9. approve persistent home registration;
10. archive, promote, delete, or clean scratch content;
11. refresh scheduler projection;
12. mutate Local Work Trajectory from runtime/workflow code.
