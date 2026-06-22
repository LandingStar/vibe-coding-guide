# Review - Operator Workflow Binding Reference Inspection Step

> Date: 2026-06-22
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-22-operator-workflow-binding-reference-inspection-step.md`

## Scope Reviewed

This slice threaded the read-only supervisor storage binding reference
inspection product into the shared scheduler operator workflow.

Implemented:

1. `SchedulerOperatorWorkflowRequest.inspect_binding_refs`;
2. workflow result field `binding_reference_inspection`;
3. optional workflow step `inspectBindingRefs`;
4. CLI flag `doc-based-coding scheduler operator-workflow --inspect-binding-refs`;
5. MCP `schedulerOperatorWorkflow` input `inspectBindingRefs`;
6. prompt and MCP tool surface audit guidance;
7. focused runtime, CLI, MCP, and prompt tests.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile tools/progress_graph/scheduler_operator_workflow.py src/runtime/orchestration/exchange_admission_ledger.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_operator_workflow and binding"
3 passed, 264 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "operator_workflow and binding"
1 passed, 48 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "operator_workflow and binding"
1 passed, 14 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_operator_workflow or admit_exchange_artifact_version_validates_binding_refs or supervisor_storage_binding_reference_inspection or supervisor_storage_binding_artifact_refs"
13 passed, 254 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "operator_workflow or inspect_binding_refs or admit or seed_dogfood_fixture"
14 passed, 35 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "operator_workflow or binding_reference_inspect or admit"
5 passed, 10 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke"
1 passed, 19 deselected
```

## Behavioral Notes

The shared workflow now preserves the old default five-step shape when
`inspectBindingRefs` / `--inspect-binding-refs` is not enabled.

When enabled, the workflow inserts `inspectBindingRefs` after
`inspectCandidates` and before `admit`. The step reuses
`inspect_supervisor_storage_binding_artifact_refs_for_submission()` and exposes
the same structured inspection product under `binding_reference_inspection`.

If inspection fails, admission, loop execution, and projection refresh are
skipped. If inspection succeeds and admission is requested, the admission
wrapper also passes `validate_binding_artifact_refs=True` into the mutating
admission preflight.

## Explicit Non-Goals Preserved

This slice did not:

1. change the underlying binding-ref validator;
2. admit unless `admit=true`;
3. submit scheduler tasks outside the existing explicit admission path;
4. run providers unless `runLoop=true`;
5. refresh projection unless `refreshProjection=true`;
6. mark ExchangeArtifact versions consumed;
7. read raw supervisor storage binding evidence JSON;
8. create agent home directories;
9. create scratch directories;
10. write scratch manifests;
11. add Host UX controls;
12. mutate agent-owned Local Work Trajectory from workflow code;
13. change scheduler runtime execution semantics.

## Follow-Up

The next narrow backend-facing candidate is to make admission ledger/readback
products carry compact binding-reference validation summaries when explicit
binding-ref preflight is enabled. That would let operators inspect the durable
reasoning around an admission decision without rerunning workflow inspection.
