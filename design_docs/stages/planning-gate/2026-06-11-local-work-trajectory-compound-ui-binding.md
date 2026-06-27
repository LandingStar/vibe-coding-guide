# Planning Gate - Local Work Trajectory Compound UI Binding

> Date: 2026-06-11
> Status: COMPLETED
> Source: user-approved UI follow-up after compound subgraph backend semantics
> Backend contract: `design_docs/local-work-trajectory-compound-subgraph-contract-draft.md`
> Related UI requirement: `design_docs/progress-graph-local-work-trajectory-ui-requirements.md`

## Why this exists

Local Work Trajectory now supports multi-line compound packs through one anchor
compound plus proxy compound events, and cross-pack reliance through parent-level
projection relations with precise endpoint metadata.

The current read-only React Flow UI can enter compound child trajectories, but it
does not yet make these new semantics readable:

1. Anchor and proxy compound events are visually too similar.
2. Parent-level projected reliance does not expose whether a relation is
   cross-boundary or cross-compound.
3. Precise child endpoints exist in relation metadata but are not inspectable in
   the UI.
4. Users need a way to jump from a projected relation to the precise child
   endpoint without expanding nested graphs inline.

## Scope

This gate covers a narrow read-only UI binding slice:

1. Render compound anchors and proxies with distinct visual weight.
2. Highlight all visible compound events that share the same child trajectory
   when one member of the group is selected.
3. Style projected cross-boundary and cross-compound relations distinctly from
   ordinary sequence/merge/dependency edges.
4. Show projection metadata and precise endpoint metadata in the detail panel.
5. Provide read-only jump actions from relation details into the source or target
   child trajectory when precise endpoint metadata names a child event.
6. Preserve the existing lane-first layout and child trajectory navigation.

## Non-Goals

This gate does not:

1. Add mutation controls to the Local Work Trajectory UI.
2. Add inline expansion of child trajectories in the parent graph.
3. Rewrite the lane-first layout model.
4. Change Local Work Trajectory JSON schema.
5. Change MCP or VS Code AI tool mutation semantics.
6. Define scheduling, sandboxing, or agent cluster behavior.

## UI Contract

### Parent compound rendering

Anchor compound events remain the primary visual representation of a packed
phase. Proxy compound events are projection placeholders that preserve non-anchor
lane topology and must not look like independent work.

Rendering rules:

1. `metadata.compound_role="anchor"` uses the normal compound visual weight.
2. `metadata.compound_role="proxy"` uses a lighter/dashed visual style.
3. The node body should expose the role label in compact form.
4. Selecting an anchor or proxy highlights all nodes in the current view whose
   `metadata.child_trajectory_id` matches.
5. Both anchor and proxy nodes may enter the same child trajectory.

### Child trajectory view

Child trajectory navigation remains recursive and read-only.

Rendering rules:

1. Child trajectories keep lane-first rendering.
2. Breadcrumbs remain the navigation mechanism back to parents.
3. The detail panel may show packed lane/event metadata, but lane labels should
   stay short.

### Projected reliance display

Parent-level projection edges remain the primary graph surface for cross-pack
reliance.

Rendering rules:

1. `metadata.relation_projection="cross-boundary"` and
   `metadata.relation_projection="cross-compound"` receive distinct edge
   styling.
2. The graph does not draw edges that pierce directly into hidden child views.
3. Selecting a projected relation shows:
   - parent-visible source and target events;
   - projection type;
   - source precise endpoint fields if present;
   - target precise endpoint fields if present.
4. When an endpoint references a child trajectory that is available in the
   payload, the detail panel offers a jump action into that child and selects the
   precise event.

## Acceptance

This gate is complete when:

1. The read-only React Flow UI distinguishes anchor/proxy compound roles.
2. Selecting one compound member highlights visible siblings sharing the same
   child trajectory.
3. Cross-boundary and cross-compound relations are visually distinct and
   inspectable.
4. Relation detail can display precise endpoint metadata and navigate to a child
   endpoint.
5. Focused automated tests cover the new mapping behavior.
6. A screenshot-based browser check verifies the parent and child views render
   coherently.

## Validation Plan

1. Run focused VS Code webview tests for Local Work Trajectory.
2. Run extension build validation.
3. Render a fixture with multi-line pack and cross-compound reliance in a browser
   harness.
4. Capture parent and child screenshots under `output/playwright/`.

## 2026-06-11 Implementation Result

The read-only UI binding slice has been implemented.

Implemented behavior:

1. Compound anchor/proxy semantics are now mapped into React Flow node metadata
   and CSS classes.
2. Proxy compounds render with lighter dashed styling while preserving parent
   lane topology.
3. Selecting an anchor or proxy highlights visible sibling compound events that
   share the same `child_trajectory_id`.
4. Parent-level projected relations now keep stable relation selection ids, so
   clicking a relation opens relation details instead of only selecting nodes.
5. `cross-boundary` and `cross-compound` relations receive projection-specific
   edge classes and styling.
6. Relation details show parent-visible projection endpoints plus precise
   `source_endpoint_*` / `target_endpoint_*` metadata.
7. Relation details can jump into a referenced child trajectory and select the
   precise endpoint event.
8. The existing lane-first layout, child breadcrumb navigation, MiniMap behavior,
   and read-only UI boundary remain intact.

Validation evidence:

1. `npm test` in `vscode-extension` passed: `24 passed`.
2. Browser screenshot harness:
   `output/playwright/local-work-trajectory-compound/capture.cjs`.
3. Captured screenshots:
   - `output/playwright/local-work-trajectory-compound/parent-default.png`
   - `output/playwright/local-work-trajectory-compound/parent-compound-selected.png`
   - `output/playwright/local-work-trajectory-compound/relation-detail.png`
   - `output/playwright/local-work-trajectory-compound/child-endpoint.png`
4. Harness DOM checks confirmed:
   - parent view: 4 compound nodes, 2 proxy nodes, 1 cross-compound projection
     edge;
   - selected compound group: 2 highlighted group nodes;
   - relation detail: 2 endpoint cards;
   - child endpoint jump: breadcrumb entered `child:phase-020` and selected
     `event:003`.

No schema, MCP mutation, scheduler, or inline expansion changes were made.

## Stop Condition

Stop after the read-only UI binding, focused tests, screenshot validation, and
document writeback are complete. Do not expand this gate into editing controls,
inline expansion, or scheduler design.
