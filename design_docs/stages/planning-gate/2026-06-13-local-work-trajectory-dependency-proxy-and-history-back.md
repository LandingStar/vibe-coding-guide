# Planning Gate - Local Work Trajectory Dependency Proxy And History Back

> Date: 2026-06-13
> Status: COMPLETED
> Source: user request for clearer dependence display and previous-path navigation
> Related UI requirements: `design_docs/progress-graph-local-work-trajectory-ui-requirements.md`

## Why This Exists

The current Local Work Trajectory UI can show parent-level projected dependency
relations and child-level external reliance badges, but the dependence reading
is still too abstract when a visible event depends on a precise endpoint inside
another child trajectory or graph.

The user requested a read-only visual form where the dependent event can show
one or more nearby proxy nodes representing the depended endpoints. Selecting
those proxy nodes should expose details and provide a jump to the actual
depended endpoint. The user also requested a back button beside the breadcrumb
path bar that returns to the previous navigation path, not merely to the parent.

## Scope

This gate covers a narrow UI slice:

1. Render depended-endpoint proxy nodes near the dependent event for projected
   `depends_on` relations with precise endpoint metadata.
2. Make proxy nodes selectable and show detail for the represented provider /
   depended endpoint.
3. Provide a jump action from proxy detail to the actual depended endpoint.
4. Add a breadcrumb-left back button that follows view navigation history.
5. Validate the result with focused tests, build, and screenshot-style browser
   evidence.

## Non-Goals

This gate does not:

1. Change Local Work Trajectory JSON schema or MCP mutation semantics.
2. Add manual trajectory editing controls.
3. Redesign relation ownership or scheduling semantics.
4. Replace the current temporary read-only projection model.
5. Solve the later frontend model redesign for cross-pack / cross-graph
   dependence.

## UI Contract

For `depends_on`, the relation source is the provider / depended endpoint and
the relation target is the dependent event.

Rendering rules:

1. If a `depends_on` relation has precise source endpoint metadata and its
   target event is visible in the current trajectory, render a proxy node near
   the target event.
2. The proxy node represents the depended source endpoint, not the dependent
   event.
3. Proxy nodes are placed above or below the dependent event to avoid drawing
   long cross-layer edges through the main flow.
4. Proxy nodes use short local connectors to the dependent event. They should
   not create a full cross-trajectory edge spaghetti layer.
5. Selecting a proxy node shows endpoint metadata, owner relation, represented
   event id, and an action to jump to the actual endpoint when its trajectory is
   available in the payload.
6. The breadcrumb-left back button pops the previous navigation state from a
   path history stack. It must restore the previous trajectory path and selected
   event/relation/proxy target when possible.

## Acceptance

This gate is complete when:

1. Dependent events show nearby depended-endpoint proxy nodes for projected
   precise `depends_on` relations.
2. Proxy selection opens a readable detail panel.
3. Proxy detail can jump to the actual endpoint.
4. Breadcrumb area contains a previous-path back button and does not confuse it
   with parent navigation.
5. Focused source tests cover proxy rendering and history navigation hooks.
6. Screenshot-style validation captures proxy nodes, proxy detail, endpoint
   jump behavior, and back-button presence.

## Validation Plan

1. Run focused Local Work Trajectory tests.
2. Run extension build validation.
3. Render browser harness screenshots under `output/playwright/`.
4. Inspect screenshots before final writeback.

## Implementation Result

Completed on 2026-06-13.

1. `vscode-extension/src/webviews/localWorkTrajectory.tsx` now derives
   read-only dependency proxy nodes from existing `depends_on` precise endpoint
   metadata. The proxy appears near the dependent visible event and represents
   the provider / depended endpoint.
2. Proxy nodes are selectable. Their detail panel shows represented endpoint,
   dependent event, relation scope, owner trajectory, origin, precise endpoint
   metadata, and actions to jump to the real endpoint or open the owner
   relation.
3. Existing child external reliance indicators remain intact. The new proxy
   layer complements them instead of duplicating parent relations inside child
   trajectories.
4. The breadcrumb path bar now always renders when a trajectory exists and has a
   left-side `Back` button. This button restores the previous navigation
   snapshot, including trajectory path and selected event / relation / proxy.
5. The initial fit viewport was made more conservative so dependency proxy
   nodes and dependent events stay visible without being pressed against the
   right detail panel.
6. `vscode-extension/src/webviews/localWorkTrajectory.css` adds proxy-node,
   proxy-edge, and breadcrumb-back styling while preserving the read-only
   React Flow surface.
7. `output/playwright/local-work-trajectory-compound/capture.cjs` now validates
   dependency proxy rendering, proxy detail, endpoint jump, history-back
   restoration, child external reliance detail, and parent relation return.

## Validation Evidence

Commands:

1. `cd vscode-extension && npm test` -> `24 passed`
2. `node output/playwright/local-work-trajectory-compound/capture.cjs` -> passed
   browser assertions

Screenshot artifacts:

1. `output/playwright/local-work-trajectory-compound/parent-default.png`
2. `output/playwright/local-work-trajectory-compound/dependency-proxy-detail.png`
3. `output/playwright/local-work-trajectory-compound/dependency-proxy-endpoint-jump.png`
4. `output/playwright/local-work-trajectory-compound/history-back-return.png`
5. `output/playwright/local-work-trajectory-compound/child-endpoint.png`
6. `output/playwright/local-work-trajectory-compound/parent-relation-return.png`

## Stop Condition

Stop after implementation, focused tests, build validation, screenshot
validation, and this gate writeback are complete. Do not expand into schema,
MCP, scheduler, or frontend model redesign.
