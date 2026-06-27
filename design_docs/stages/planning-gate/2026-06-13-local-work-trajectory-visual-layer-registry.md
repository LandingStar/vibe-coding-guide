# Planning Gate - Local Work Trajectory Visual Layer Registry

> Date: 2026-06-13
> Status: COMPLETED
> Source: user feedback after layer-level mismatch during visual validation
> Related UI requirements: `design_docs/progress-graph-local-work-trajectory-ui-requirements.md`

## Why This Exists

The Local Work Trajectory view currently spreads visual stacking rules across
React Flow node/edge class construction and CSS `z-index` selectors. This made
the recent layer-level mismatch hard to diagnose: the renderer could request a
visual role while tests or styles expected a different level, but the error did
not point to a clear owner or registration site.

This gate adds a small registerable visual layer interface for the current
Local Work Trajectory webview. The goal is not a new frontend model; it is a
replaceable layer registry that keeps node and edge stacking explicit and gives
actionable diagnostics when a layer id is missing.

## Scope

This gate covers only:

1. A Local Work Trajectory visual layer registry for node and edge layers.
2. Default layer registration for all currently rendered node and edge roles.
3. Builder integration so nodes and edges receive registered layer classes and
   CSS variable values from one facility.
4. Clear diagnostics for unknown layer ids, including owner/build function,
   known layer ids, and the expected registration fix.
5. Focused tests and screenshot-style validation.

## Non-Goals

This gate does not:

1. Change Local Work Trajectory JSON schema or MCP mutation semantics.
2. Change lane-first layout, dependency proxy placement, compound semantics, or
   relation ownership.
3. Add manual trajectory editing controls.
4. Replace React Flow or redesign the temporary relation projection model.
5. Introduce a global theme system for unrelated progress graph views.

## Interface Contract

The registry owns a small descriptor per visual layer:

1. `kind`: `node` or `edge`.
2. `id`: stable layer id local to that kind.
3. `className`: generated CSS class, for example
   `pg-lwt-layer-node-dependency-proxy`.
4. `zIndex`: numeric stacking value applied through `--pg-lwt-layer-z`.

Builders must ask the registry for a layer by id instead of embedding stacking
knowledge in ad hoc CSS selectors. Existing semantic classes remain in place for
styling and tests.

If a builder asks for an unknown layer id, the diagnostic must name:

1. the unknown layer id and expected kind;
2. the requesting owner/build function;
3. the known layer ids for that kind;
4. the likely fix: register the layer in
   `createDefaultTrajectoryVisualLayerRegistry()`.

## Acceptance

This gate is complete when:

1. Node and edge builders use the registry for currently stacked visual roles.
2. CSS consumes `--pg-lwt-layer-z` through layer classes or layer-aware
   selectors.
3. Unknown layer diagnostics are covered by focused tests and include enough
   context for a human or model to fix the mismatch.
4. Existing Local Work Trajectory behavior remains visually stable in the
   screenshot harness.

## Validation Plan

1. Run `cd vscode-extension && npm test`.
2. Run the Local Work Trajectory Playwright screenshot harness.
3. Inspect representative screenshots before final writeback.

## Implementation Result

Completed on 2026-06-13.

1. `vscode-extension/src/webviews/localWorkTrajectory.tsx` now owns a small
   registerable visual layer registry:
   - `createTrajectoryVisualLayerRegistry(...)`
   - `registerTrajectoryVisualLayer(...)`
   - `createDefaultTrajectoryVisualLayerRegistry()`
   - `resolveTrajectoryVisualLayer(...)`
2. Current node layers are registered for lane, event, compound,
   compound-proxy, dependency-proxy, status-attention, active, and selected
   roles.
3. Current edge layers are registered for sequence, lane-opening, merge,
   reliance-overlay, dependency-proxy, and generic relation roles.
4. Node and edge builders now compose semantic classes with registered layer
   classes, and apply `--pg-lwt-layer-z` through the shared layer resolver.
5. Unknown layer diagnostics now include the unknown layer id, layer kind,
   requesting owner/build function, known layer ids, and the expected fix:
   register the missing layer in `createDefaultTrajectoryVisualLayerRegistry()`.
6. `vscode-extension/src/webviews/localWorkTrajectory.css` now consumes
   `--pg-lwt-layer-z` for layer-aware React Flow node and edge stacking while
   preserving existing semantic classes for styling.
7. `vscode-extension/src/test/localWorkTrajectory.test.ts` now locks the
   registry contract, default registrations, diagnostic text, builder usage,
   and CSS variable consumption.

## Validation Evidence

Commands:

1. `cd vscode-extension && npm test` -> `24 passed`
2. `npm install --prefix output\playwright\local-work-trajectory-compound playwright@1.60.0 --no-save`
3. `node output\playwright\local-work-trajectory-compound\capture.cjs` -> passed
4. Removed temporary
   `output\playwright\local-work-trajectory-compound\node_modules` and
   `package-lock.json` after screenshot validation.
5. `git diff --check -- vscode-extension/src/webviews/localWorkTrajectory.tsx vscode-extension/src/webviews/localWorkTrajectory.css vscode-extension/src/test/localWorkTrajectory.test.ts design_docs/stages/planning-gate/2026-06-13-local-work-trajectory-visual-layer-registry.md`
   -> no whitespace errors; only existing LF/CRLF warnings.

Screenshot artifacts inspected:

1. `output/playwright/local-work-trajectory-compound/parent-default.png`
2. `output/playwright/local-work-trajectory-compound/dependency-proxy-detail.png`
3. `output/playwright/local-work-trajectory-compound/child-endpoint.png`

## Boundary Confirmation

This slice did not change Local Work Trajectory JSON schema, MCP mutation
semantics, lane-first layout, dependency proxy placement, compound semantics, or
relation ownership. The registry is intentionally local to the current React
Flow Local Work Trajectory webview and can be replaced later if the frontend
model is redesigned.

## Stop Condition

Completed after implementation, focused tests, screenshot validation, and this
gate writeback. Do not expand this closed gate into schema, MCP, scheduler, or
frontend model redesign.
