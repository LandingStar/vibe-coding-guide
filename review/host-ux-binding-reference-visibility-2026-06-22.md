# Review - Host UX Binding Reference Visibility

> Date: 2026-06-22
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-22-host-ux-binding-reference-visibility.md`

## Scope Reviewed

This slice connected the compact backend binding read model to Scheduler
Operator Host UX.

Implemented:

1. typed Host UX read models for compact binding references, task summaries,
   readiness, and latest admission summaries;
2. `bindingReferenceReadiness` and `latestBindingReferenceSummary` on
   `SchedulerOperatorExchangeCandidate`;
3. Scheduler Operator candidate card rendering for current `Binding readiness`
   and `Latest binding admission`;
4. task-level chips for input binding refs and checked refs;
5. binding-aware admission button wiring via `inspectBindingRefs`, mapped to
   the existing shared `scheduler operator-workflow --inspect-binding-refs`
   flag;
6. focused HTML/contract/panel/lifecycle tests;
7. screenshot-style browser validation.

## Evidence

Focused validation:

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

Screenshot validation:

```text
output/playwright/host-ux-binding-reference-visibility/binding-reference-visibility.png
Width=1400 Height=2164 sampled_unique_colors=23
Browser text check included "Binding readiness" and "Latest binding admission".
```

Change analysis:

```text
analyze_changes
impact.direct=[]
impact.transitive=[]
coupling.alerts=[]
```

Wide extension regression note:

```text
node --test "dist/test/**/*.test.js"
64 passed, 1 failed
```

The failing test is a pre-existing dirty `aiChatToolLoop.test.ts` prompt-wording
assertion mismatch outside this gate's scoped changes. The focused Scheduler
Operator / Progress Graph Preview tests passed.

## Behavioral Notes

The candidate card now distinguishes:

1. current exact-version binding readiness from the ExchangeArtifact bundle;
2. latest binding-aware admission summary from the latest compact ledger-backed
   projection.

When a candidate carries `bindingReferenceReadiness`, the Admit button sends
`inspectBindingRefs: true`; the shared Host UX contract maps this to
`--inspect-binding-refs`. This keeps the UI consistent with the backend
binding-aware path without adding new runtime semantics.

## Explicit Non-Goals Preserved

This slice did not:

1. add a new MCP seed tool;
2. add new runtime scheduler/admission semantics;
3. mutate ExchangeArtifact lifecycle state;
4. mark candidates consumed;
5. run live providers;
6. read raw supervisor storage binding evidence JSON;
7. expose raw admission ledger records in Host UX;
8. mutate agent-owned Local Work Trajectory from Host UX.

## Follow-Up

The Host UX now exposes binding readiness and latest binding admission results.
The next useful step should move back to backend/operator semantics, because UI
readback for the current binding path is now complete enough for dogfood.
