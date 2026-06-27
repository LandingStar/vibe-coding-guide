# Planning Gate - Local Work Trajectory Child External Reliance Indicators

> Date: 2026-06-11
> Status: COMPLETED
> Source: user-approved follow-up after compound UI binding validation
> Backend contract: `design_docs/local-work-trajectory-compound-subgraph-contract-draft.md`
> Related UI requirement: `design_docs/progress-graph-local-work-trajectory-ui-requirements.md`

## Why this exists

Cross-pack reliance is stored at the parent trajectory as a projected relation
when the precise endpoints live inside hidden child trajectories. This preserves
the relation ownership contract, but a user entering a child trajectory cannot
see that a selected child event participates in an external reliance relation.

The existing parent view is semantically correct. The missing piece is a
read-only child-view indicator that makes parent-level projected reliance
discoverable from the precise child endpoint.

## Scope

This gate covers one narrow UI binding slice:

1. Derive external reliance indicators for the current child trajectory from
   ancestor or parent-level projected relations.
2. Attach compact external reliance badges to precise child endpoint events.
3. Show external reliance cards in the event detail panel.
4. Provide a read-only action that returns to the relation owner trajectory and
   selects the projected relation.
5. Keep parent-level projection edges as the primary graph surface for
   cross-pack reliance.

## Non-Goals

This gate does not:

1. Copy cross-compound relations into child trajectory `relations`.
2. Draw edges that pierce from a child view into another hidden child or parent.
3. Change relation ownership, endpoint metadata, MCP mutation semantics, or JSON
   schema.
4. Add inline child expansion or mutation controls.
5. Redesign the lane-first layout or scheduling semantics.

## UI Contract

### External reliance derivation

When the current view is a child trajectory, the UI may scan the root payload for
relations whose precise endpoint metadata points into the current child:

- `source_endpoint_trajectory_id == current trajectory id`
- `target_endpoint_trajectory_id == current trajectory id`

Only relations owned by another trajectory are treated as external indicators.
Child-local relations remain normal child `relations`.

### Child endpoint rendering

For each matching endpoint:

1. The precise child event receives a compact external reliance badge.
2. The badge text uses the relation kind label plus an external marker.
3. The node may receive a subtle visual accent, but the child graph must remain
   lane-first and uncluttered.

### Detail panel behavior

When selecting a child event with external reliance indicators:

1. The detail panel lists each external relation.
2. Each card shows relation kind, projection type, endpoint role, owner
   trajectory, and summary when present.
3. Each card offers an `Open parent relation` action that navigates to the owner
   trajectory and selects the projected relation.

## Acceptance

This gate is complete when:

1. Child views visibly mark precise endpoint events for parent-level projected
   reliance.
2. Selecting such an event reveals external reliance details.
3. The user can return to the parent/owner relation detail from the child event.
4. Existing parent projection edge display and relation detail behavior still
   work.
5. Focused tests cover the new mapping behavior.
6. Screenshot-based validation captures child endpoint indicator and parent
   relation return behavior.

## Validation Plan

1. Run focused Local Work Trajectory webview tests.
2. Run extension build validation.
3. Reuse the compound screenshot harness with a cross-compound relation.
4. Capture child endpoint and parent relation-return screenshots under
   `output/playwright/local-work-trajectory-compound/`.

## 2026-06-11 Implementation Result

The read-only child external reliance indicator slice has been implemented.

Implemented behavior:

1. The Local Work Trajectory UI derives external reliance indicators from root
   payload relations whose precise endpoint metadata points into the current
   child trajectory.
2. Child endpoint nodes receive an external reliance badge and a subtle visual
   marker.
3. Selecting the endpoint shows an `External reliance` card in the detail panel.
4. The card exposes relation kind, projection type, endpoint role, owner
   trajectory, relation summary, and `Open parent relation`.
5. `Open parent relation` navigates back to the relation owner trajectory and
   selects the projected relation.
6. Parent-level projected edges remain the primary graph surface; no relation is
   copied into child trajectory `relations`.

Validation evidence:

1. `npm test` in `vscode-extension` passed: `24 passed`.
2. `npm run build` in `vscode-extension` passed.
3. Browser screenshot harness:
   `output/playwright/local-work-trajectory-compound/capture.cjs`.
4. Captured screenshots:
   - `output/playwright/local-work-trajectory-compound/child-endpoint.png`
   - `output/playwright/local-work-trajectory-compound/parent-relation-return.png`
   - refreshed parent/relation screenshots in the same directory.
5. Harness DOM checks confirmed:
   - parent view: 4 compound nodes, 2 proxy nodes, 1 cross-compound projection
     edge;
   - child endpoint view: 1 external badge and 1 external reliance card;
   - parent relation return: parent breadcrumb cleared and relation detail shows
     `Projectioncross-compound`.

No schema, MCP mutation, relation ownership, inline expansion, or scheduler
changes were made.

## Stop Condition

Stop after the read-only child external reliance indicators, focused tests,
screenshot validation, and document writeback are complete. Do not expand this
gate into relation ownership changes, inline expansion, or scheduler behavior.
