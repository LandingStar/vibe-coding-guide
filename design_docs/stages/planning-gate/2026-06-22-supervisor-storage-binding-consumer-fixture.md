# Planning Gate - Supervisor Storage Binding Consumer Fixture

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`design_docs/admission-ledger-binding-reference-summary-followup-direction-analysis.md`
recommends making the completed binding-ref inspection and admission ledger
summary path easier to dogfood by adding one deterministic consumer fixture.

## Problem

The backend path can now inspect supervisor storage binding artifact refs,
fail-close admission preflight, and persist compact binding summaries in the
admission ledger. Current tests and manual sessions still have to hand-build a
matching binding artifact plus a scheduler submission that consumes it.

## Scope

### Slice 1 - Runtime Fixture

Add a deterministic `binding-consumer` scheduler operator fixture that seeds:

1. one compact supervisor storage binding `ExchangeArtifact`;
2. one scheduler task batch submission `ExchangeArtifact` that references the
   binding artifact through `ref_kind="supervisor_storage_binding_artifact"`;
3. compact fixture metadata naming the submission artifact/version, binding
   artifact/version, task ids, lane ids, dependency ids, and recommended
   operator workflow options.

The fixture should reuse the existing ExchangeArtifact store and dogfood
fixture helpers.

### Slice 2 - CLI / MCP-Reusable Surface

Expose the fixture through the existing CLI seed path:

```text
doc-based-coding scheduler seed-dogfood-fixture --fixture binding-consumer
```

Keep MCP validation on the existing operator workflow surface:

```text
schedulerOperatorWorkflow(inspectBindingRefs=true, admit=true)
```

No new MCP seed tool is required in this slice unless the existing server
surface already has a shared seed route.

### Slice 3 - Focused Validation

Add focused tests that prove:

1. the runtime fixture writes both compact binding artifact and consumer
   scheduler submission;
2. CLI seed output reports the binding fixture metadata;
3. CLI seed -> operator workflow `--inspect-binding-refs --admit` -> admission
   readback records a compact `binding_reference_summary`;
4. MCP operator workflow can consume the seeded fixture and write the same
   durable summary.

## Non-Goals

This gate does not:

1. run providers;
2. refresh projection by default;
3. create real agent home directories;
4. create real scratch directories;
5. write scratch manifests;
6. write raw supervisor storage binding evidence JSON;
7. read raw supervisor storage binding evidence JSON;
8. mark ExchangeArtifact versions consumed;
9. add Host UX controls;
10. mutate agent-owned Local Work Trajectory from runtime/CLI/MCP code;
11. change scheduler execution semantics.

## Acceptance Criteria

The gate may close when:

1. `binding-consumer` fixture can be seeded deterministically through runtime
   and CLI;
2. the seeded submission contains at least one exact
   `supervisor_storage_binding_artifact` input ref;
3. `inspectBindingRefs + admit` over the seeded fixture succeeds and writes an
   admission ledger record with `binding_reference_summary.enabled=true`;
4. focused runtime, CLI, MCP, and prompt/help tests pass;
5. review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-22.

Implemented:

1. deterministic `binding-consumer` fixture runtime helpers;
2. compact supervisor storage binding artifact seeding;
3. one scheduler task batch submission that consumes the binding artifact via
   exact `supervisor_storage_binding_artifact` ref;
4. CLI seed support through
   `doc-based-coding scheduler seed-dogfood-fixture --fixture binding-consumer`;
5. prompt and MCP tool surface audit updates;
6. runtime, CLI, MCP, and prompt tests.

The fixture writes only ExchangeArtifact store records. It does not write raw
supervisor storage binding evidence JSON, create home/scratch directories, run
providers, refresh projection, or mutate agent-owned Local Work Trajectory.

## Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_operator_fixture.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "binding_consumer_fixture"
2 passed, 270 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "binding_consumer_fixture or seed_dogfood_fixture_help"
2 passed, 49 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "binding_consumer_fixture"
1 passed, 16 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke"
1 passed, 19 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_operator and fixture or binding_refs or binding_summary"
11 passed, 261 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "seed_dogfood_fixture or operator_workflow or inspect_binding_refs or inspect_admissions and binding_reference_summary"
9 passed, 42 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "operator_workflow or binding_summary or binding_reference_inspect"
5 passed, 12 deselected
```

## Review Evidence

`review/supervisor-storage-binding-consumer-fixture-2026-06-22.md`

## Preserved Non-Goals

This slice still did not:

1. run providers;
2. refresh projection by default;
3. create real agent home directories;
4. create real scratch directories;
5. write scratch manifests;
6. write raw supervisor storage binding evidence JSON;
7. read raw supervisor storage binding evidence JSON;
8. mark ExchangeArtifact versions consumed;
9. add Host UX controls;
10. mutate agent-owned Local Work Trajectory from runtime/CLI/MCP code;
11. change scheduler execution semantics;
12. add a new MCP seed tool.
