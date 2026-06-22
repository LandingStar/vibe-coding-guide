# Host UX Operator Dogfood Closure Control

> Date: 2026-06-22
> Status: COMPLETED
> Scope: Host UX invocation and presentation for the existing operator dogfood closure product.

## Trigger

`design_docs/operator-dogfood-closure-mcp-surface-followup-direction-analysis.md`
recommends adding a product-facing Host UX control after the deterministic
operator dogfood closure became available through runtime, CLI, and MCP.

The existing shared closure product already performs:

```text
seed fixture
-> binding-ref inspection
-> exact admission
-> consumed lifecycle marking
-> bounded fake scheduler loop
-> scheduler projection refresh
-> Host Evidence presentation readback
```

This gate only makes that product visible and runnable from the VS Code Host UX
layer.

## Goal

Add a Scheduler Operator Host UX control that invokes:

```text
doc-based-coding scheduler operator-dogfood-closure
```

and displays the compact closure summary / authority split returned by the
shared product.

## In Scope

1. Add a typed Host UX scheduler operator action for the closure command.
2. Route the action through the existing extension CLI invocation path.
3. Preserve deterministic fake-runtime defaults:
   - `fixture = binding-consumer`
   - `runtime-provider = fake`
   - bounded loop settings
   - explicit artifact/admission/scheduler/projection/evidence paths
4. Render one visible control in the Scheduler Operator panel.
5. Summarize `closure_summary` and `authority_split` in the last-action area.
6. Add focused TypeScript contract / HTML / panel tests.
7. Validate the rendered UI with screenshot evidence.
8. Update review evidence and status boards after validation.

## Out of Scope

- No backend closure semantic changes.
- No reimplementation of seed/admit/run/project steps in frontend code.
- No live Qoder or other real runtime provider.
- No daemon service, timer, watcher, or background process.
- No cleanup runner behavior changes.
- No agent home or scratch directory creation.
- No Local Work Trajectory mutation from the Host UX closure control.
- No change to graph renderer layout or Local Work Trajectory UI.

## Interface Draft

Webview action:

```ts
{ command: 'schedulerOperatorAction', action: 'operatorDogfoodClosure' }
```

Generated CLI args:

```text
scheduler operator-dogfood-closure
--fixture binding-consumer
--artifact-store-path .codex/orchestration/exchange-artifacts.json
--admission-ledger-path .codex/orchestration/exchange-artifact-admissions.json
--snapshot-path .codex/scheduler/scheduler-state.json
--event-log-path .codex/scheduler/scheduler-events.jsonl
--projection-output-path .codex/progress-graph/scheduler-work-trajectory.json
--runtime-provider fake
--max-ticks 3
--max-runs-per-tick 1
--evidence-id vscode-operator-closure-<timestamp>
--evidence-path .codex/scheduler/evidence/vscode-operator-closure-<timestamp>.json
--actor vscode-scheduler-operator
--guide-context vscode-scheduler-operator
```

Expected display:

- workflow surface and ok status;
- fixture and final lifecycle state;
- binding summary ok / loop evidence / Host Evidence card count;
- compact authority facts, especially provider execution,
  scheduler/projection mutation, ExchangeArtifact mutation, and
  Local Work Trajectory non-mutation.

## Validation Plan

Focused validation:

```text
cd vscode-extension
npm run build
node --test dist/test/schedulerOperatorContracts.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js
```

Screenshot validation:

```text
output/playwright/host-ux-operator-dogfood-closure-control/
```

Finish with scoped `git diff --check` and `analyze_changes` for touched files.

## Completion Criteria

- The Scheduler Operator panel exposes a closure control.
- Clicking the control routes through the shared closure CLI product.
- The UI does not issue MCP `localTrajectory`, `callTool`, or write-resource
  mutations.
- Last-action rendering shows compact closure and authority facts.
- Focused tests and screenshot validation pass.
- Review evidence and status boards record the completed slice.

## Completion Notes

Completed on 2026-06-22.

Review evidence:

- `review/host-ux-operator-dogfood-closure-control-2026-06-22.md`

Implemented:

- `schedulerOperatorContracts.ts` now accepts
  `operatorDogfoodClosure` webview messages and maps them to
  `doc-based-coding scheduler operator-dogfood-closure`.
- `schedulerOperatorWorkflow.ts` summarizes closure result payloads using
  compact `closure_summary` and `authority_split` facts.
- `progressGraphPreviewHtml.ts` renders a Scheduler Operator
  `Run dogfood closure` control and structured closure readback in the
  last-action area.

Validation:

```text
VS Code extension build passed
Focused Scheduler Operator / Progress Graph Preview node tests: 43 passed
Screenshot fixture generated:
  output/playwright/host-ux-operator-dogfood-closure-control/operator-dogfood-closure-control.html
Screenshot captured:
  output/playwright/host-ux-operator-dogfood-closure-control/operator-dogfood-closure-control.png
Scoped git diff --check passed with Windows line-ending warnings only
analyze_changes: no impact nodes and no coupling alerts
```
