# Planning Gate - Local Work Trajectory Global Anchor Navigation

> Date: 2026-06-13
> Status: COMPLETED
> Source: user request for observing and navigating Local Work Trajectory anchors from the global map

## Why this exists

Local Work Trajectory already carries `sourceGraphId` and `sourceNodeId`, but the progress preview does not expose that anchor in the global map. As a result, users cannot see which global node owns the current trajectory, cannot jump from the global map into the trajectory, and cannot jump from the trajectory back to its parent node.

The anchor may change as work advances, so the mutation surface must be agent-owned through `localTrajectory`, not a manual UI-only action.

## Scope

This slice implements one current-trajectory anchor loop:

1. `localTrajectory` exposes an action for setting or moving the current trajectory anchor.
2. The root `LocalWorkTrajectory.sourceGraphId/sourceNodeId` fields are the canonical anchor fields.
3. The global graph payload marks nodes that currently host the active local trajectory.
4. The global graph UI shows an observable trajectory marker on anchored nodes.
5. Selecting/opening an anchored global node can switch to the Trajectory tab.
6. The Trajectory tab exposes a button to locate its parent node in the global graph.

## Non-Goals

1. This does not create a multi-trajectory registry.
2. This does not make trajectory anchoring a scheduler or ownership model.
3. This does not infer anchor moves automatically from event advancement.
4. This does not support several active trajectories attached to several global nodes in one artifact.
5. This does not change the global graph source-of-truth or introduce graph-to-work mutation semantics.

## Contract

- `LocalWorkTrajectory.sourceGraphId`: selected global graph id.
- `LocalWorkTrajectory.sourceNodeId`: selected global graph node id.
- `localTrajectory setAnchor`: updates the two fields and records optional summary/reason metadata.
- Global graph node projection adds:
  - `hasLocalTrajectory: boolean`
  - `localTrajectoryId: string | null`
- Webview-local navigation commands:
  - `showTrajectoryForNode(nodeId)`: switch to Trajectory tab when the selected node matches the current trajectory anchor.
  - `locateTrajectoryParent()`: switch to Checklist tab and select/focus the anchored graph node.

## Validation

- Backend trajectory tests cover anchor mutation and persistence.
- MCP / AI tool tests cover `setAnchor` exposure.
- Preview HTML / renderer tests cover anchor marker and navigation surfaces.
- Playwright screenshot validation is required before delivery because this is UI work.

## Completion Notes

Implemented on 2026-06-13:

1. `tools.progress_graph.set_local_work_trajectory_anchor(...)` updates or clears root `source_graph_id/source_node_id` and records anchor metadata.
2. MCP `localTrajectory` and VS Code AI chat `localTrajectory` now expose `setAnchor`.
3. Instruction generation now tells work agents to use `localTrajectory setAnchor` when the current trajectory moves under a global progress-map node.
4. `ProgressGraphPreviewPanel` reads Local Work Trajectory before building the V2 graph payload, so the selected global graph node can be marked with `hasLocalTrajectory/localTrajectoryId`.
5. The graph renderer highlights anchored nodes, adds an `Open trajectory` detail action, and listens for host node-selection events.
6. The Local Work Trajectory toolbar has `Locate parent`, which switches back to Checklist and selects the anchored global node.

Validation evidence:

1. `vscode-extension/npm run build` passed.
2. `node --test dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js dist/test/aiChatTools.test.js` passed, 15 tests.
3. `python -m pytest tests/test_progress_graph_trajectory.py tests/test_mcp_tools.py tests/test_instructions_generator.py -q` passed, 121 passed and 1 skipped.
4. `node output/playwright/progress-preview-tabs/capture.cjs` passed and captured `shared-height-checklist-resized.png`, `shared-height-trajectory-resized.png`, and `trajectory-locate-parent.png`.
