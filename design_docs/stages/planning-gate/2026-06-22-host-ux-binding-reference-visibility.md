# Planning Gate - Host UX Binding Reference Visibility

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`design_docs/exchange-store-binding-admission-summary-projection-followup-direction-analysis.md`
recommends making the newly projected binding readiness and latest
binding-aware admission summary visible in Scheduler Operator Host UX.

## Problem

The backend now exposes a compact read model through
`dbc://exchange-artifacts/bundle`:

```text
ExchangeArtifact admission candidate
-> binding_reference_readiness
-> latest_binding_reference_summary
```

Operators should not have to inspect raw CLI/MCP JSON to know whether a
candidate is ready for binding-aware admission or what the latest binding-aware
admission attempt recorded. The Host UX candidate card is the existing surface
where this compact status belongs.

## Scope

### Slice 1 - State Projection

Thread the backend fields into `SchedulerOperatorExchangeCandidate`:

1. compact current `binding_reference_readiness`;
2. compact `latest_binding_reference_summary`;
3. no raw ledger records, raw binding payloads, or raw evidence JSON.

### Slice 2 - Candidate Rendering

Render a compact binding section on each Scheduler Operator candidate:

1. current readiness status and counts;
2. latest binding-aware admission status and ledger clue when available;
3. task-level binding refs and checked refs as concise chips;
4. error summaries when readiness or latest admission is not ok.

### Slice 3 - Validation

Use deterministic test data matching the `binding-consumer` fixture to validate:

1. candidate cards render readiness before admission;
2. candidate cards render latest binding summary after admission;
3. existing no-candidate and non-binding candidate states remain readable;
4. screenshot-style validation is captured for the UI change.

## Non-Goals

This gate does not:

1. add a new MCP seed tool;
2. add new runtime scheduler/admission semantics;
3. mutate ExchangeArtifact lifecycle state;
4. mark candidates consumed;
5. run live providers;
6. read raw supervisor storage binding evidence JSON;
7. expose raw admission ledger records in Host UX;
8. mutate agent-owned Local Work Trajectory from Host UX.

## Acceptance Criteria

The gate may close when:

1. Host UX reads `binding_reference_readiness` and
   `latest_binding_reference_summary` from the existing exchange bundle;
2. Scheduler Operator candidate cards visibly distinguish current readiness from
   latest binding admission summary;
3. focused extension HTML tests cover the rendering contract;
4. screenshot-style validation artifact demonstrates the rendered card;
5. review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-22.

Implemented:

1. `SchedulerOperatorExchangeCandidate.bindingReferenceReadiness`;
2. `SchedulerOperatorExchangeCandidate.latestBindingReferenceSummary`;
3. compact binding-ref task/ref read models in Host UX state;
4. Scheduler Operator candidate card sections for `Binding readiness` and
   `Latest binding admission`;
5. automatic `inspectBindingRefs` webview action flag for candidates that have
   binding readiness, causing the existing shared workflow to include
   `--inspect-binding-refs` before admission;
6. focused HTML/contract/panel/lifecycle tests and screenshot-style validation.

The UI consumes only the compact bundle fields. It does not read raw admission
ledger records, raw binding payloads, or raw supervisor storage binding
evidence JSON.

## Validation

```text
npm run build
passed

node --test dist/test/schedulerOperatorContracts.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphSchedulerOperatorLifecycle.test.js
44 passed

.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/exchange_store.py src/runtime/orchestration/exchange_admission_ledger.py src/runtime/orchestration/scheduler_operator_fixture.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_cli.py tests/test_mcp_admission.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "exchange_artifacts_bundle_cli_projects_binding_summary or scheduler_binding_consumer_fixture_cli_inspects_admits_and_reads_summary"
2 passed, 50 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "exchange_artifacts_bundle_projects_binding_summary or consumes_binding_consumer_fixture"
2 passed, 16 deselected
```

Screenshot-style validation:

```text
output/playwright/host-ux-binding-reference-visibility/binding-reference-visibility.png
Width=1400 Height=2164 sampled_unique_colors=23
Browser text check included "Binding readiness" and "Latest binding admission".
```

Wide extension regression note:

```text
node --test "dist/test/**/*.test.js"
64 passed, 1 failed
```

The single failure is the pre-existing dirty
`aiChatToolLoop.test.ts` assertion mismatch against already-modified
Local Work Trajectory prompt wording. It is outside this gate's changed files.

Change analysis:

```text
analyze_changes
impact.direct=[]
impact.transitive=[]
coupling.alerts=[]
```

## Review Evidence

`review/host-ux-binding-reference-visibility-2026-06-22.md`

## Preserved Non-Goals

This slice did not:

1. add a new MCP seed tool;
2. add new runtime scheduler/admission semantics;
3. mutate ExchangeArtifact lifecycle state;
4. mark candidates consumed;
5. run live providers;
6. read raw supervisor storage binding evidence JSON;
7. expose raw admission ledger records in Host UX;
8. mutate agent-owned Local Work Trajectory from Host UX.
