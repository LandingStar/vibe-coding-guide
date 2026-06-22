# Planning Gate - Operator Workflow Binding Reference Inspection Step

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`design_docs/supervisor-storage-binding-reference-inspection-surface-followup-direction-analysis.md`
recommends threading the read-only supervisor storage binding reference
inspection product into the shared scheduler operator workflow before exact
admission.

## Problem

`schedulerBindingReferenceInspect` and
`doc-based-coding scheduler inspect-binding-refs` can now validate supervisor
storage binding artifact refs in one stored scheduler submission. The higher
level `schedulerOperatorWorkflow` still shows candidate inspection and can
perform admission, loop execution, projection refresh, and Host Evidence
readback, but it cannot include the binding-ref readiness result in the same
operator payload.

That leaves tool callers with a two-step manual sequence before admission and
encourages host-specific glue.

## Scope

### Slice 1 - Shared Workflow Request / Result

Add an explicit optional read-only binding-ref inspection step to
`SchedulerOperatorWorkflowRequest`.

The workflow should:

1. keep existing default behavior compatible when the option is not enabled;
2. run the inspection after candidate inspection and before admission when the
   option is enabled;
3. require exact `artifact_id` and `version` for that enabled inspection;
4. expose the inspection product in the workflow result payload;
5. mark the inspection step failed when the inspection product reports
   validation errors;
6. skip dependent admission/loop/projection steps after inspection failure.

### Slice 2 - CLI / MCP Surface

Expose the option through:

1. `doc-based-coding scheduler operator-workflow --inspect-binding-refs`;
2. MCP `schedulerOperatorWorkflow` input `inspectBindingRefs`.

Both surfaces should return the shared workflow payload. CLI should exit
non-zero when the workflow is not `ok`, while still printing the structured
JSON result.

### Slice 3 - Prompt / Audit Docs

Update scheduler MCP prompt guidance and MCP tool surface audit so operators
know to prefer the shared workflow option when inspection should be bundled
with admission workflow context.

## Non-Goals

This gate does not:

1. change the underlying binding-ref validator;
2. admit unless `admit=true`;
3. submit scheduler tasks outside the existing explicit admission path;
4. run providers unless `runLoop=true`;
5. refresh projection unless `refreshProjection=true`;
6. mark ExchangeArtifact versions consumed;
7. read raw supervisor storage binding evidence JSON;
8. create agent home or scratch directories;
9. write scratch manifests;
10. add Host UX controls or screenshots;
11. mutate agent-owned Local Work Trajectory from workflow code;
12. change scheduler runtime execution semantics.

## Acceptance Criteria

The gate may close when:

1. workflow inspect-only succeeds for a valid stored scheduler submission and
   remains read-only;
2. workflow inspect+admit succeeds when binding refs are valid;
3. workflow inspection failure prevents admission, loop execution, and
   projection refresh;
4. CLI and MCP surfaces expose and route the option;
5. focused runtime, CLI, MCP, and prompt tests pass;
6. review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-22.

Implemented:

1. `SchedulerOperatorWorkflowRequest.inspect_binding_refs`;
2. workflow result field `binding_reference_inspection`;
3. optional workflow step `inspectBindingRefs`;
4. CLI flag `doc-based-coding scheduler operator-workflow --inspect-binding-refs`;
5. MCP `schedulerOperatorWorkflow` input `inspectBindingRefs`;
6. prompt guidance and MCP tool surface audit updates;
7. focused runtime, CLI, MCP, and prompt tests.

When enabled, the shared operator workflow now runs binding-ref inspection
after candidate inspection and before admission. The step reads only the
ExchangeArtifact store, reuses
`inspect_supervisor_storage_binding_artifact_refs_for_submission()`, and
returns the existing `supervisor_storage_binding_reference_inspection` product
inside the workflow payload.

Inspection failure marks the workflow not `ok` and skips dependent admission,
loop execution, and projection refresh. When inspection is enabled and
admission is requested, the admission wrapper also passes
`validate_binding_artifact_refs=True` into the existing fail-closed scheduler
admission preflight so the mutating path rechecks the same rule before state
mutation.

Default workflow behavior remains compatible: when `inspectBindingRefs` /
`--inspect-binding-refs` is not enabled, the existing five-step payload shape is
preserved.

## Validation

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

## Review Evidence

`review/operator-workflow-binding-reference-inspection-step-2026-06-22.md`

## Preserved Non-Goals

This slice still did not:

1. change the underlying binding-ref validator;
2. admit unless `admit=true`;
3. submit scheduler tasks outside the existing explicit admission path;
4. run providers unless `runLoop=true`;
5. refresh projection unless `refreshProjection=true`;
6. mark ExchangeArtifact versions consumed;
7. read raw supervisor storage binding evidence JSON;
8. create agent home or scratch directories;
9. write scratch manifests;
10. add Host UX controls or screenshots;
11. mutate agent-owned Local Work Trajectory from workflow code;
12. change scheduler runtime execution semantics.
