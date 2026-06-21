# Review - Supervisor Storage Binding ExchangeArtifact Projection

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-exchange-artifact-projection.md`

## Scope Reviewed

This slice projected compact supervisor storage binding evidence readback into
an `ExchangeArtifact` without adding scheduler admission or operator surfaces.

Implemented:

1. `SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE`;
2. `SUPERVISOR_STORAGE_BINDING_ARTIFACT_SCHEMA_VERSION`;
3. `supervisor_storage_binding_evidence_summary_to_artifact()`;
4. runtime exports from `src.runtime.orchestration`;
5. focused runtime tests for artifact shape, validation, JSON round-trip,
   exact-version store write, explicit identity overrides, and raw binding
   exclusion.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/supervisor_storage_binding_evidence.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_storage_binding_evidence or supervisor_dogfood_storage_binding or supervisor_agent_storage_binding or scheduler_supervisor_dogfood_workflow"
8 passed, 249 deselected
```

Adjacent validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "supervisor_storage_binding_evidence or supervisor_dogfood_storage_binding or supervisor_agent_storage_binding or scheduler_supervisor_dogfood_workflow or agent_home_registration or scratch_manifest or cleanup_receipt or exchange_artifact_json_round_trip or exchange_artifact_version_store"
14 passed, 243 deselected

git diff --check -- src/runtime/orchestration/supervisor_storage_binding_evidence.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-exchange-artifact-projection.md
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

The projection returns a retention/inform `ExchangeArtifact` with:

1. compact `structured` data for evidence, supervisor, scheduler, storage,
   metadata, and authority facts;
2. a scheduler-readable `storage_manifest`;
3. an `evidence` payload pointing at the durable evidence product;
4. a file `ref` for exact evidence JSON readback;
5. a compact projection `log`.

`ExchangeScope` only fills task/context/lane/runtime fields when the summary has
exactly one id for that field. Multi-id facts stay in the structured payload to
avoid inventing a lossy primary id.

The raw `binding` payload remains only in the durable evidence JSON. It is not
embedded into the projected artifact payload parts.

## Explicit Non-Goals Preserved

This slice did not:

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

## Follow-Up

The next narrow backend slice should decide how this artifact becomes useful to
downstream coordination without widening this helper: either exact-version
scheduler admission readiness for binding artifacts, or read-only MCP resource
readback for projected binding artifacts.
