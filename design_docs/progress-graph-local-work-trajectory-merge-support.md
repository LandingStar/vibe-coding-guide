# Progress Graph Local Work Trajectory Merge Support

## Context

This document records the 2026-06-05 follow-up slice for Local Work Trajectory
multi-line support. The previous first multi-line slice added `addLane`; this
slice adds the minimal `merge` operation needed to test an open-lane and fan-in
loop end to end.

Authoritative UI/semantic background remains:

- `design_docs/progress-graph-local-work-trajectory-ui-requirements.md`
- `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`

## Current Semantics

1. `localTrajectory merge` requires a source lane through `sourceLaneId` or
   `laneId`.
2. The target lane defaults to `lane:main`.
3. The source event is selected from the source lane. If the source lane has no
   active, blocked, waiting, or pending event, the last completed event becomes
   the merge source.
4. The target event is `targetEventId` when provided; otherwise it is the current
   target-lane tail event.
5. Merge completes the selected source event when needed.
6. Merge completes the selected target anchor when needed, then appends an
   `in_progress` event of kind `merge` on the target lane.
7. The artifact records a target-lane `sequence` relation into the merge event.
8. The artifact records a cross-lane `merges_into` relation from the source
   event into the merge event.
9. The UI renders `merges_into` as a distinct dashed fan-in edge labelled
   `merge`.

## UI Layout Rules

The lane-first UI should not place every lane from the left edge. Later lanes
must preserve their birth and fan-in context:

1. Sequence events still move left to right inside each lane.
2. A `proposes_new_line` relation raises the new lane's first event to at least
   one column after the source event.
3. The new lane label is placed near the source event column, not at the global
   left edge.
4. A `merges_into` relation raises the target merge event to at least one column
   after the source event.
5. If one lane is shorter, empty visual columns are inserted into that lane by
   increasing event columns; the artifact schema is not changed.
6. `proposes_new_line` is labelled `open lane`; `merges_into` is labelled
   `merge`.

## Non-Goals

1. No dependency scheduler.
2. No conflict resolution.
3. No grouped review barrier.
4. No one-to-one claim between lanes and real parallel subagents.
5. No user-facing manual trajectory editor.

## Validation

Focused backend and MCP validation:

```powershell
python -m pytest tests/test_progress_graph_trajectory.py tests/test_mcp_tools.py -q
```

Result:

```text
68 passed, 1 skipped
```

Focused VS Code host validation:

```powershell
npm run build
node --test dist/test/localWorkTrajectory.test.js dist/test/aiChatToolLoop.test.js dist/test/aiChatViewIntegration.test.js
```

Result:

```text
build complete
9 passed
```

Manual-test workspace smoke:

- Workspace: `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test`
- Executed loop: `start -> addLane -> append(docs) -> advance(docs start) -> advance(docs conclusion) -> merge`
- Observed artifact before reset: 2 lanes, 4 events, 4 relations, including one `merges_into` relation and one in-progress `merge` event.
- Reset after smoke: durable empty lifecycle, 0 lanes, 0 events, 0 relations.
