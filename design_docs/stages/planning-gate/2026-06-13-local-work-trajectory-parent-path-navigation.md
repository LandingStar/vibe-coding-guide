# Planning Gate - Local Work Trajectory Parent Path Navigation

> Date: 2026-06-13
> Status: COMPLETED
> Source: user request for a Windows file-browser-like parent path button
> Related UI requirements: `design_docs/progress-graph-local-work-trajectory-ui-requirements.md`

## Why This Exists

The Local Work Trajectory breadcrumb already had a `Back` button, but that
button represents navigation history. Users also need a separate hierarchy
operation: return from the current child trajectory to its parent path, similar
to the parent-folder button in a file browser.

Without a separate control, history navigation and hierarchy navigation are easy
to confuse when moving between compound parent views and child trajectory views.

## Scope

This gate covers only:

1. Add a parent-path button immediately to the right of the existing history
   `Back` button.
2. Keep `Back` as history navigation.
3. Make `Up` remove only the current deepest breadcrumb segment.
4. Preserve history when `Up` is used, so `Back` can return to the child path.
5. Validate the control with focused tests and screenshot-style Playwright
   evidence.

## Non-Goals

This gate does not:

1. Change Local Work Trajectory schema or MCP mutation semantics.
2. Redesign breadcrumb path modeling.
3. Add manual trajectory editing controls.
4. Change compound, dependency proxy, or relation projection semantics.

## Implementation Result

Completed on 2026-06-13.

1. `vscode-extension/src/webviews/localWorkTrajectory.tsx` now passes
   `canGoUp` and `onGoUp` into `TrajectoryBreadcrumb`.
2. The new `Up` button appears directly after `Back`.
3. `Up` is enabled only when the current breadcrumb has a parent path.
4. `Up` clears child-local selection, removes the deepest trajectory from the
   current path, and records the previous state in navigation history.
5. `Back` remains a history operation and can restore the child path after an
   `Up` navigation.
6. `vscode-extension/src/webviews/localWorkTrajectory.css` adds a distinct
   `.pg-lwt-breadcrumb-up` style and disabled state.
7. `vscode-extension/src/test/localWorkTrajectory.test.ts` locks the
   Back/Up contract at source assertion level.
8. `output/playwright/local-work-trajectory-compound/capture.cjs` now captures
   and validates the parent-path round trip:
   child path -> `Up` to parent path -> `Back` to child path.

## Validation Evidence

Commands:

1. `cd vscode-extension && npm test` -> `24 passed`
2. `npm install --prefix output\playwright\local-work-trajectory-compound playwright@1.60.0 --no-save`
3. `node output\playwright\local-work-trajectory-compound\capture.cjs` -> passed
4. Removed temporary
   `output\playwright\local-work-trajectory-compound\node_modules` and
   `package-lock.json` after screenshot validation.

Screenshot artifacts inspected:

1. `output/playwright/local-work-trajectory-compound/up-parent-return.png`
2. `output/playwright/local-work-trajectory-compound/up-back-child-return.png`

The first screenshot confirms that `Up` returns to the parent breadcrumb and is
disabled at the root path. The second confirms that `Back` can restore the child
path after `Up`, with the child endpoint selection and detail restored.

## Boundary Confirmation

This slice changes only the Local Work Trajectory breadcrumb navigation surface
and its focused validation harness. It does not change model schema, MCP tools,
relation semantics, or layout algorithms.

## Stop Condition

Completed after implementation, focused tests, screenshot validation, temporary
dependency cleanup, and this gate writeback.
