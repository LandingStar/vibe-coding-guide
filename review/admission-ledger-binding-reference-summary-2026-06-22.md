# Review - Admission Ledger Binding Reference Summary

> Date: 2026-06-22
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-22-admission-ledger-binding-reference-summary.md`

## Scope Reviewed

This slice made binding-ref-aware scheduler admissions durable after the
decision by adding compact validation summaries to admission ledger records and
readback payloads.

Implemented:

1. optional `ExchangeArtifactAdmissionRecord.binding_reference_summary`;
2. JSON serialize/deserialize support with old-record compatibility;
3. compact summary generation from the existing binding-ref inspection product;
4. success and failed-preflight admission result payload summaries;
5. durable ledger summaries for binding-aware admitted/failed attempts;
6. CLI/MCP readback coverage through existing ledger inspection surfaces;
7. scheduler MCP prompt and MCP tool surface audit updates.

## Evidence

Focused validation:

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

## Behavioral Notes

`binding_reference_summary` is generated only when
`validate_binding_artifact_refs=True` is explicitly enabled. Old admission
ledger records deserialize with an empty summary and serialize without the
field.

The summary includes enabled/ok flags, source artifact id/version, submission
product type, task/ref counts, readable errors, and compact per-task task/ref
clues. It does not contain raw supervisor storage binding evidence JSON or raw
binding payloads.

Failed binding-ref preflight now writes a failed admission ledger record with
the compact summary while preserving fail-closed behavior before scheduler
snapshot or event-log mutation.

## Explicit Non-Goals Preserved

This slice did not:

1. change the binding-ref validator;
2. admit unless existing explicit admission paths are called;
3. run providers;
4. refresh projection;
5. mark ExchangeArtifact versions consumed;
6. read raw supervisor storage binding evidence JSON;
7. create agent home directories;
8. create scratch directories;
9. write scratch manifests;
10. add Host UX controls;
11. mutate agent-owned Local Work Trajectory from runtime/CLI/MCP code;
12. change scheduler execution semantics.

## Follow-Up

The next narrow backend-facing candidate is a deterministic supervisor storage
binding consumer fixture. It would let CLI/MCP/manual smoke tests seed a
binding artifact plus a scheduler task that consumes it, then exercise
`inspectBindingRefs + admit + ledger summary` without hand-building fixture
payloads in each test or dogfood session.
