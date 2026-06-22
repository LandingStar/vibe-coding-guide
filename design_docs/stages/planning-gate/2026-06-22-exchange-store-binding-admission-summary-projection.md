# Planning Gate - Exchange Store Binding Admission Summary Projection

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`design_docs/supervisor-storage-binding-consumer-fixture-followup-direction-analysis.md`
recommends projecting compact binding readiness/admission facts into the
ExchangeArtifact store inspection bundle before moving to Host UX.

## Problem

The `binding-consumer` dogfood fixture makes the binding-aware path repeatable:

```text
seed binding-consumer fixture
-> schedulerOperatorWorkflow(inspectBindingRefs=true, admit=true)
-> inspect-admissions binding_reference_summary readback
```

Operators still need to inspect multiple readback surfaces to understand both
the current candidate readiness and the latest binding-aware admission summary.
`inspect_exchange_artifact_store()` already lists candidates and their
admission state, so it is the right compact read model to enrich first.

## Scope

### Slice 1 - Candidate Binding Projection

For scheduler admission candidates, add optional compact fields to
`ExchangeArtifactAdmissionCandidate`:

1. `binding_reference_readiness` from read-only binding-ref inspection over the
   current exact artifact version;
2. `latest_binding_reference_summary` from the latest admission ledger record
   for that exact artifact version that carries a compact
   `binding_reference_summary`.

### Slice 2 - Readback Surfaces

Ensure existing readback surfaces that reuse `inspect_exchange_artifact_store()`
show the new compact fields:

1. runtime bundle JSON;
2. CLI `doc-based-coding resources read dbc://exchange-artifacts/bundle`;
3. MCP resource `dbc://exchange-artifacts/bundle`;
4. operator workflow candidate bundle.

### Slice 3 - Focused Validation

Use the deterministic `binding-consumer` fixture to validate:

1. before admission, bundle candidate contains current
   `binding_reference_readiness`;
2. after `inspectBindingRefs + admit`, bundle candidate contains
   `latest_binding_reference_summary`;
3. malformed admission ledger remains isolated as bundle errors;
4. no raw ledger array, raw binding payload, or raw evidence JSON is projected.

## Non-Goals

This gate does not:

1. add Host UX controls;
2. add a new MCP seed tool;
3. run providers;
4. refresh projection;
5. mark ExchangeArtifacts consumed;
6. read raw supervisor storage binding evidence JSON;
7. write raw supervisor storage binding evidence JSON;
8. duplicate raw admission ledger records into the store bundle;
9. mutate agent-owned Local Work Trajectory from runtime/CLI/MCP code;
10. change scheduler execution semantics.

## Acceptance Criteria

The gate may close when:

1. store inspection projects binding readiness for the `binding-consumer`
   admission candidate before admission;
2. store inspection projects latest compact binding admission summary after
   binding-aware admission;
3. CLI/MCP resource readback surfaces expose the same fields through existing
   bundle payloads;
4. focused runtime, CLI, MCP, and operator workflow tests pass;
5. review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-22.

Implemented:

1. optional `binding_reference_readiness` on
   `ExchangeArtifactAdmissionCandidate`;
2. optional `latest_binding_reference_summary` on
   `ExchangeArtifactAdmissionCandidate`;
3. read-only readiness projection from the exact stored artifact version using
   existing binding-ref inspection;
4. latest compact binding summary projection from admission ledger records;
5. CLI/MCP resource and operator workflow coverage through existing
   `inspect_exchange_artifact_store()` consumers;
6. focused runtime, CLI, and MCP tests.

The projection remains compact. It includes counts, task ids, compact ref
clues, errors, and latest ledger metadata. It does not embed raw admission
ledger arrays, raw binding payloads, or raw supervisor storage binding evidence
JSON.

## Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/exchange_store.py src/runtime/orchestration/exchange_admission_ledger.py src/runtime/orchestration/scheduler_operator_fixture.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "binding_readiness_before_admission or latest_binding_summary_after_admission"
2 passed, 272 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "exchange_artifacts_bundle_cli_projects_binding_summary"
1 passed, 51 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "exchange_artifacts_bundle_projects_binding_summary or consumes_binding_consumer_fixture"
2 passed, 16 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "exchange_artifact_store_inspection or binding_consumer_fixture or binding_summary"
11 passed, 263 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "resources or seed_dogfood_fixture or operator_workflow or inspect_admissions and binding_reference_summary"
6 passed, 46 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "operator_workflow or binding_summary or binding_reference_inspect or exchange_artifacts_bundle"
6 passed, 12 deselected
```

## Review Evidence

`review/exchange-store-binding-admission-summary-projection-2026-06-22.md`

## Preserved Non-Goals

This slice still did not:

1. add Host UX controls;
2. add a new MCP seed tool;
3. run providers;
4. refresh projection;
5. mark ExchangeArtifacts consumed;
6. read raw supervisor storage binding evidence JSON;
7. write raw supervisor storage binding evidence JSON;
8. duplicate raw admission ledger records into the store bundle;
9. mutate agent-owned Local Work Trajectory from runtime/CLI/MCP code;
10. change scheduler execution semantics.
