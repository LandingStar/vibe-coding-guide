# Planning Gate - Supervisor Storage Binding Reference Inspection Surface

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/supervisor-storage-binding-artifact-admission-readiness-followup-direction-analysis.md`
recommends exposing the existing exact-version binding reference validation as
a non-mutating operator/tool inspection surface before any scheduler admission.

## Problem

Scheduler submissions can now reference exact supervisor storage binding
artifacts, and admission can opt into validation. Operators and tool callers
still need a safe read-only way to inspect a stored scheduler submission
artifact before deciding whether to admit it.

Without that surface, the only convenient validation path is tied to admission,
which is intentionally a mutating scheduler operation.

## Scope

### Slice 1 - Inspection Product

Define a compact read-only inspection product for one exact stored scheduler
submission artifact version.

The product should report:

1. source artifact id and version;
2. detected submission product type;
3. task count;
4. per-task supervisor storage binding artifact refs;
5. per-task checked ref count and readable validation errors;
6. aggregate error count and `ok`;
7. explicit authority split showing no scheduler, store, ledger, provider,
   evidence, projection, or Local Work Trajectory mutation.

### Slice 2 - Runtime Helper

Add a helper that:

1. reads one exact artifact version from `JsonArtifactVersionStore`;
2. accepts only `scheduler_task_submission` and
   `scheduler_task_batch_submission`;
3. parses the stored submission with the existing parsers;
4. reuses `validate_supervisor_storage_binding_artifact_refs()` for each task;
5. does not read raw supervisor storage binding evidence JSON;
6. does not write scheduler snapshots, event logs, admission ledgers, exchange
   stores, projections, evidence, or trajectory files.

### Slice 3 - CLI / MCP Readback Surface

Expose the same runtime product through:

1. `doc-based-coding scheduler inspect-binding-refs`;
2. an MCP read-only tool.

Both surfaces should return the same JSON-safe product and return a failing
status/result when validation errors exist.

## Non-Goals

This gate does not:

1. admit scheduler submissions;
2. submit scheduler tasks;
3. write scheduler snapshots or event logs;
4. mutate ExchangeArtifact stores;
5. mutate admission ledgers;
6. mark any artifact consumed;
7. read raw supervisor storage binding evidence JSON;
8. create agent home or scratch directories;
9. write scratch manifests;
10. run fake or real providers;
11. refresh scheduler projections;
12. add Host UX controls;
13. mutate Local Work Trajectory from runtime, CLI, or MCP implementation code.

## Acceptance Criteria

The gate may close when:

1. a runtime read-only inspection helper returns a compact product for valid
   single and batch scheduler submissions;
2. invalid, missing, wrong-product, and ambiguous cases return readable errors
   without scheduler/store/ledger mutation;
3. CLI and MCP surfaces expose the runtime product;
4. focused runtime, CLI, and MCP tests cover success and failure paths;
5. review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-22.

Implemented:

1. `BindingArtifactReferenceTaskInspection`;
2. `BindingArtifactReferenceInspection`;
3. `inspect_supervisor_storage_binding_artifact_refs_for_submission()`;
4. runtime exports from `src.runtime.orchestration`;
5. CLI `doc-based-coding scheduler inspect-binding-refs`;
6. MCP tool `schedulerBindingReferenceInspect`;
7. scheduler MCP prompt guidance and MCP tool surface audit entry;
8. focused runtime, CLI, MCP, and prompt tests.

The inspection helper reads one exact stored scheduler submission artifact from
`JsonArtifactVersionStore`, parses either `scheduler_task_submission` or
`scheduler_task_batch_submission`, and reuses
`validate_supervisor_storage_binding_artifact_refs()` per task. It returns a
compact JSON-safe product with source artifact identity, submission product
type, per-task binding refs, checked ref counts, readable errors, aggregate
counts, `ok`, and read-only authority flags.

The CLI and MCP surfaces expose the same product:

```text
doc-based-coding scheduler inspect-binding-refs --artifact-id ID --version VERSION
schedulerBindingReferenceInspect
```

Both surfaces return non-success status when validation errors exist while still
printing/returning the structured inspection product.

## Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_submission.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "binding_reference_inspection or supervisor_storage_binding_artifact_refs or supervisor_storage_binding_evidence or admit_exchange_artifact_version or scheduler_task_submission"
20 passed, 244 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "inspect_binding_refs or admit or operator_workflow or seed_dogfood_fixture"
13 passed, 35 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "binding_reference_inspect or admit or scheduler_operator_workflow"
4 passed, 10 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py -k "admitExchangeArtifact or schedulerSubmitTasks or scheduler_projection"
13 passed, 73 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke"
passed

git diff --check
passed
```

`analyze_changes` reported no dependency-graph impact nodes. It raised the
expected must-sync alert for MCP tool registration after `src/mcp/tools.py`
changed; `src/mcp/server.py` list/routing registration and MCP server route
tests were updated in the same slice.

## Review Evidence

`review/supervisor-storage-binding-reference-inspection-surface-2026-06-22.md`

## Preserved Non-Goals

This slice still did not:

1. admit scheduler submissions;
2. submit scheduler tasks;
3. write scheduler snapshots or event logs;
4. mutate ExchangeArtifact stores;
5. mutate admission ledgers;
6. mark artifacts consumed;
7. read raw supervisor storage binding evidence JSON;
8. create agent home or scratch directories;
9. write scratch manifests;
10. run fake or real providers;
11. refresh scheduler projections;
12. add Host UX controls;
13. mutate Local Work Trajectory from runtime, CLI, or MCP implementation code.
