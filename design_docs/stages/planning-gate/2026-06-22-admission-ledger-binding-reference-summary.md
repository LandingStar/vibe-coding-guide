# Planning Gate - Admission Ledger Binding Reference Summary

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`design_docs/operator-workflow-binding-reference-inspection-step-followup-direction-analysis.md`
recommends making binding-ref-aware admissions durable after the decision by
recording compact validation summaries in the admission ledger/readback
surface.

## Problem

The shared operator workflow can now inspect supervisor storage binding refs
before explicit admission. The actual admission ledger still records only the
admission status and an error summary. When binding-ref preflight is enabled,
operators cannot tell from the durable ledger whether the preflight checked
binding refs, how many refs were checked, or which task/ref caused a failure
without rerunning inspection.

## Scope

### Slice 1 - Compact Ledger Summary

Add an optional compact binding-reference validation summary to admission
ledger records when `validate_binding_artifact_refs=True` is explicitly used.

The summary should include:

1. whether binding-ref validation was enabled;
2. source artifact id/version;
3. submission product type;
4. task count;
5. binding ref count;
6. checked ref count;
7. error count;
8. readable errors;
9. compact per-task task id/title/count/error clues.

The summary must not include raw supervisor storage binding evidence JSON or
raw binding payloads.

### Slice 2 - Admission Payload / Readback

Expose the same compact summary in:

1. `admit_exchange_artifact_version_with_ledger()` result payloads;
2. `inspect_exchange_artifact_admission_ledger()` record readback;
3. CLI `doc-based-coding scheduler inspect-admissions`;
4. MCP routes that reuse admission ledger readback.

### Slice 3 - Focused Validation

Add focused tests for:

1. admitted records with valid binding refs;
2. failed preflight records with missing/invalid binding refs;
3. old ledger records without the summary still deserializing as empty summary;
4. CLI/MCP readback preserving the compact summary.

## Non-Goals

This gate does not:

1. change the binding-ref validator;
2. admit unless existing explicit admission paths are called;
3. run providers;
4. refresh projection;
5. mark ExchangeArtifact versions consumed;
6. read raw supervisor storage binding evidence JSON;
7. create agent home or scratch directories;
8. write scratch manifests;
9. add Host UX controls;
10. mutate agent-owned Local Work Trajectory from runtime/CLI/MCP code;
11. change scheduler execution semantics.

## Acceptance Criteria

The gate may close when:

1. explicit binding-ref-aware admission writes compact validation summary on
   success;
2. explicit binding-ref-aware failed preflight writes compact validation
   summary without scheduler state/event-log mutation;
3. admission ledger inspection returns the summary for records and remains
   backward compatible for old records;
4. focused runtime, CLI, MCP, and prompt/readback tests pass;
5. review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-22.

Implemented:

1. optional `ExchangeArtifactAdmissionRecord.binding_reference_summary`;
2. JSON serialize/deserialize support with old-record compatibility;
3. compact summary generation from
   `inspect_supervisor_storage_binding_artifact_refs_for_submission()`;
4. success and failed-preflight admission result payload summaries;
5. durable ledger summaries for admitted, failed, and duplicate-rejected
   binding-aware admission attempts;
6. CLI/MCP readback coverage through existing admission ledger inspection
   surfaces;
7. prompt and MCP tool surface audit updates.

The compact summary is generated only when
`validate_binding_artifact_refs=True` is explicitly enabled. It includes
enabled/ok flags, source artifact id/version, submission product type, task
count, binding ref count, checked ref count, error count, readable errors, and
compact per-task task/ref/error clues. It intentionally does not store raw
supervisor storage binding evidence JSON or raw binding payloads.

Failed binding-ref preflight now writes a failed admission ledger record with
the compact summary before returning a structured failure payload, while still
avoiding scheduler state and event-log mutation.

## Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/exchange_admission_ledger.py src/runtime/orchestration/scheduler_submission.py tools/progress_graph/scheduler_operator_workflow.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "admission_ledger and binding_summary or with_ledger_records_binding_summary"
3 passed, 267 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "inspect_admissions and binding_reference_summary"
1 passed, 49 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "binding_summary_to_ledger"
1 passed, 15 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "exchange_artifact_admission_ledger or with_ledger or binding_refs or scheduler_operator_workflow"
14 passed, 256 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "inspect_admissions or operator_workflow or inspect_binding_refs or admit"
17 passed, 33 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "admit or binding_reference_inspect or operator_workflow or binding_summary"
6 passed, 10 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke"
1 passed, 19 deselected
```

## Review Evidence

`review/admission-ledger-binding-reference-summary-2026-06-22.md`

## Preserved Non-Goals

This slice still did not:

1. change the binding-ref validator;
2. admit unless existing explicit admission paths are called;
3. run providers;
4. refresh projection;
5. mark ExchangeArtifact versions consumed;
6. read raw supervisor storage binding evidence JSON;
7. create agent home or scratch directories;
8. write scratch manifests;
9. add Host UX controls;
10. mutate agent-owned Local Work Trajectory from runtime/CLI/MCP code;
11. change scheduler execution semantics.
