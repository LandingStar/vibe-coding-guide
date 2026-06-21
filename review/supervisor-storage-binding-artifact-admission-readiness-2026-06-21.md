# Review - Supervisor Storage Binding Artifact Admission Readiness

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-artifact-admission-readiness.md`

## Scope Reviewed

This slice added exact-version readiness checks for downstream scheduler task
submissions that reference projected supervisor storage binding artifacts.

Implemented:

1. `SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND`;
2. `BindingArtifactReferenceValidation`;
3. `validate_supervisor_storage_binding_artifact_refs()`;
4. optional `validate_binding_artifact_refs` preflight on
   `admit_exchange_artifact_version_to_scheduler()`;
5. runtime exports from `src.runtime.orchestration`;
6. focused runtime tests and adjacent CLI/MCP admission regression coverage.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_submission.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_storage_binding_artifact_refs or supervisor_storage_binding_evidence or admit_exchange_artifact_version"
15 passed, 246 deselected
```

Adjacent validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_storage_binding_artifact_refs or supervisor_storage_binding_evidence or admit_exchange_artifact_version or scheduler_task_submission"
17 passed, 244 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "admit or operator_workflow or seed_dogfood_fixture"
10 passed, 35 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "admit or scheduler_operator_workflow"
3 passed, 10 deselected

git diff --check -- src/runtime/orchestration/scheduler_submission.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-artifact-admission-readiness.md
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

Downstream task submissions can now declare an exact supervisor storage binding
artifact input with:

```text
ExchangeReference(
    ref_kind="supervisor_storage_binding_artifact",
    ref_id="<artifact id>",
    version="<exact version>",
)
```

`validate_supervisor_storage_binding_artifact_refs()` reads the existing
artifact store, validates exact artifact existence, and confirms the referenced
artifact has exactly one compact `supervisor_storage_binding_artifact`
structured payload. It reports readable errors for missing versions, missing
artifacts, wrong product types, and ambiguous product payloads.

`admit_exchange_artifact_version_to_scheduler()` preserves default compatibility
and only runs this preflight when `validate_binding_artifact_refs=True`.

## Explicit Non-Goals Preserved

This slice did not:

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

## Follow-Up

The next narrow slice should make this readiness visible to operator surfaces or
automation without changing scheduler execution semantics. The strongest
backend-first candidate is an MCP/CLI read-only inspection surface for binding
artifact references in stored scheduler submissions.
