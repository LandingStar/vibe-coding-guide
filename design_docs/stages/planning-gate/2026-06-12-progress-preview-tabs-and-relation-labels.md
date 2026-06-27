# Planning Gate - Progress Preview Tabs And Relation Labels

> Date: 2026-06-12
> Status: COMPLETED
> Source: user-reported graph preview UI polish issues after compound/reliance UI binding
> Related UI requirements: `design_docs/progress-graph-local-work-trajectory-ui-requirements.md`

## Why This Exists

The current progress preview can render the global graph and Local Work
Trajectory, but several UI readings are still ambiguous:

1. Dependency relation labels are too symmetric. A dependency provider and a
   dependent work item need different endpoint language.
2. Projected dependencies in the parent graph need to distinguish whole visible
   event dependencies from precise internal child-event dependencies.
3. The `open lane` label does not clearly explain lane creation.
4. The right-side detail surface can clip long content.
5. The global graph and Local Work Trajectory should be peer views with short
   tab labels, controlled from a floating top bar.
6. UI/image work must be validated with screenshot-style evidence before
   acceptance.

## Scope

This gate covers a narrow read-only UI polish slice:

1. Make dependency relation labels and endpoint badges asymmetric.
2. Add visible wording for whole-node dependency versus internal child-endpoint
   dependency on parent-level relations.
3. Rename lane-opening relation display from ambiguous `open lane` wording to
   clearer lane-start wording.
4. Fix detail/sidebar scrolling so bottom content remains reachable.
5. Convert `Checklist` and `Trajectory` into peer tab panels.
6. Move preview controls into a floating top bar that appears on pointer
   proximity, with the panel show action renamed to `show panal` and placed last.
7. Add the screenshot-validation rule to project instruction surfaces.

## Non-Goals

This gate does not:

1. Change Local Work Trajectory JSON schema or MCP mutation semantics.
2. Change dependency ownership or scheduling semantics.
3. Add mutation/editing controls to Local Work Trajectory.
4. Redesign the graph renderer, force layout, or compound child navigation.
5. Replace the temporary read-only relation projection model with a different
   frontend model.

## UI Contract

### Dependency Relation Language

For `depends_on`, the source event remains the provider/upstream event and the
target event remains the dependent/downstream event.

Rendering rules:

1. Source endpoint badge uses provider language, such as `required by #N`.
2. Target endpoint badge uses dependent language, such as `depends on #N`.
3. Parent-level edge labels use dependency scope language:
   - `node dep` when the visible parent events are the dependency endpoints.
   - `inner dep` when `source_endpoint_*` or `target_endpoint_*` metadata points
     into child trajectories.
4. Relation details label the source and target roles differently.

### Lane Opening

Lane-opening relation display should make creation/start semantics clear.

Rendering rules:

1. `proposes_new_line` is displayed as `starts lane`.
2. `approves_new_line` remains approval-oriented, but should not be confused
   with ordinary dependency or merge edges.

### Preview Shell Tabs

The host preview presents two peer panels:

1. `Checklist` for the Knowledge Graph Engine / current project graph view.
2. `Trajectory` for Local Work Trajectory.

Rendering rules:

1. A floating top bar appears when the pointer approaches the top of the webview
   or when its controls receive focus.
2. The bar contains tab buttons first, then preview action buttons.
3. The panel show action is named exactly `show panal` and is the last button in
   the floating bar.

## Acceptance

This gate is complete when:

1. Dependency labels and endpoint badges are asymmetric.
2. Parent graph projected dependencies visibly distinguish whole-node and
   internal endpoint scopes.
3. Lane-opening label wording is clear.
4. The right detail/sidebar can scroll to the bottom.
5. `Checklist` and `Trajectory` are short peer tabs with controls in the
   floating top bar.
6. Focused tests cover the source changes.
7. Screenshot-style browser validation captures the tab shell and relation UI.

## Validation Plan

1. Run focused Local Work Trajectory and preview HTML tests.
2. Run extension build validation.
3. Render browser harness screenshots under `output/playwright/`.
4. Confirm screenshots show the floating bar/tabs and readable relation labels.

## Implementation Result

Completed on 2026-06-12.

1. `vscode-extension/src/webviews/localWorkTrajectory.tsx` now renders
   dependency relation graph labels as `node dep` or `inner dep`, uses
   asymmetric provider/dependent badges, and exposes provider/dependent relation
   detail language.
2. `proposes_new_line` now displays as `starts lane`.
3. `vscode-extension/src/views/progressGraphPreviewHtml.ts` now presents
   `Checklist` and `Trajectory` as peer tab panels, moves controls into a
   pointer-proximity floating top bar, and keeps the final action label exactly
   `show panal`.
4. The tab switch dispatches a resize event after panel visibility changes so
   React Flow can re-measure the previously hidden trajectory panel.
5. Right-side detail areas use scrollable containers so both the Knowledge Graph
   Engine detail rail and Local Work Trajectory relation detail can reach their
   bottom content.
6. The screenshot-validation rule was added to `AGENTS.md` and the generated
   instruction surface in `src/workflow/instructions_generator.py`.

## Validation Evidence

Commands:

1. `cd vscode-extension && npm test` -> `24 passed`
2. `python -m pytest tests/test_instructions_generator.py -q` -> `31 passed`;
   on this Windows/Python 3.12 environment the full-file run also printed a
   post-summary `Windows fatal exception: access violation` stack while still
   returning exit code 0. The directly touched generator test and the
   project/CLI tests named in that stack were rerun individually and passed
   cleanly.
3. `node output/playwright/progress-preview-tabs/capture.cjs` -> passed browser
   assertions

Screenshot artifacts:

1. `output/playwright/progress-preview-tabs/floating-bar-checklist.png`
2. `output/playwright/progress-preview-tabs/sidebar-bottom.png`
3. `output/playwright/progress-preview-tabs/trajectory-inner-dependency.png`
4. `output/playwright/progress-preview-tabs/relation-asymmetric-detail.png`
5. `output/playwright/progress-preview-tabs/trajectory-detail-bottom.png`
6. `output/playwright/progress-preview-tabs/collapsed-show-panal.png`

## Stop Condition

Stop after UI implementation, focused tests, build validation, screenshot
validation, and this gate writeback are complete. Do not expand into schema,
scheduler, or renderer replacement work.
