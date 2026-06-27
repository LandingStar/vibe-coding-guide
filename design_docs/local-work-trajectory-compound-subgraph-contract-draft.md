# Local Work Trajectory Compound Subgraph Contract Draft

> Date: 2026-06-11
> Status: IMPLEMENTED-SLICE-1
> Gate: `design_docs/stages/planning-gate/2026-06-11-local-work-trajectory-compound-subgraph-semantics.md`
> Scope: backend semantics only; no UI mutation controls, no scheduling runtime, no implementation in this document

## Goal

This contract defines the next backend semantics for Local Work Trajectory
compound subgraphs:

1. How to pack work that spans multiple lanes.
2. How to preserve child trajectory lane structure.
3. How to represent reliance whose precise endpoint is inside a compound child
   trajectory.
4. How to keep existing readers working while adding precise cross-compound
   endpoint semantics.

The contract is intentionally additive. Existing single-line `packRange`,
parent-level `TrajectoryRelation`, and read-only UI consumers remain valid.

## Existing Baseline

Current Local Work Trajectory data has:

1. Root trajectory with `lanes`, `events`, and `relations`.
2. Compound events represented by `kind="compound"` and
   `metadata.child_trajectory_id`.
3. Child trajectories stored under `child_trajectories`.
4. Relations whose `source_event_id` and `target_event_id` are event ids inside
   the same trajectory.
5. Single-line `packRange`, which packs a continuous interval from one lane into
   one child trajectory lane.

The baseline does not yet provide a first-class way to address:

1. An event inside a child trajectory from the parent trajectory.
2. A relation between events inside two different compound children.
3. One compound phase spanning multiple parent lanes.

Current implementation constraints that shape this contract:

1. `TrajectoryLane.metadata`, `TrajectoryEvent.metadata`, and
   `TrajectoryRelation.metadata` are currently `dict[str, str]`.
2. `child_trajectories` already stores recursive child trajectory objects under
   the parent trajectory.
3. `LocalWorkTrajectory.check_invariants()` currently validates only direct lane,
   relation, and child trajectory references; endpoint metadata, proxy-anchor
   consistency, and multi-line pack continuity are not yet validated.

The first implementation should therefore extend resolution and validation
around the existing model before changing the serialized schema.

## Contract Objects

### TrajectoryEndpoint

A `TrajectoryEndpoint` is the logical address of one event inside the root
trajectory tree.

```json
{
  "trajectory_id": "local-work:single-line-current",
  "event_id": "event:003",
  "parent_event_id": "",
  "compound_path": ""
}
```

Fields:

- `trajectory_id`: required. The trajectory containing `event_id`.
- `event_id`: required. The event inside `trajectory_id`.
- `parent_event_id`: optional. The immediate compound parent event when the
  endpoint is inside a child trajectory.
- `compound_path`: optional diagnostic path from root to the endpoint, encoded
  as `/`-separated parent compound event ids for metadata compatibility.

Resolution rule:

1. Start from the root trajectory.
2. Find the trajectory with matching `trajectory_id` by walking
   `child_trajectories` recursively.
3. Check that `event_id` exists in that trajectory.
4. If `parent_event_id` is present, verify that the parent event is a compound
   event whose child tree contains `trajectory_id`.
5. If `compound_path` is present, verify that it resolves to the same
   trajectory.

Invariant:

- `trajectory_id` values must be unique inside one root trajectory tree.

### Projected Relation

Existing `TrajectoryRelation` remains the visible/coarse relation shape:

```json
{
  "source_event_id": "event:010",
  "target_event_id": "event:020",
  "kind": "depends_on",
  "summary": "",
  "metadata": {}
}
```

For cross-compound reliance, `source_event_id` and `target_event_id` are not the
precise endpoints. They are the projection endpoints in the relation owner's
trajectory.

The precise endpoints are stored additively in metadata:

```json
{
  "source_endpoint_trajectory_id": "child:compound-event-010",
  "source_endpoint_event_id": "event:002",
  "source_endpoint_parent_event_id": "event:010",
  "source_endpoint_compound_path": "event:010",
  "target_endpoint_trajectory_id": "child:compound-event-020",
  "target_endpoint_event_id": "event:003",
  "target_endpoint_parent_event_id": "event:020",
  "target_endpoint_compound_path": "event:020",
  "relation_projection": "cross-compound"
}
```

This flat metadata form is the first implementation target because current
metadata is `dict[str, str]`. A future schema version may promote
`TrajectoryEndpoint` to first-class relation fields.

## Relation Ownership

A relation is stored in the lowest trajectory that can see both endpoints without
crossing upward through more than one parent boundary.

Rules:

1. If both precise endpoints are in the same trajectory, store the relation in
   that trajectory. No projection metadata is required.
2. If one endpoint is parent-level and one endpoint is inside a direct child,
   store the relation in the parent trajectory. Project the child endpoint to
   the compound event.
3. If both endpoints are inside different child trajectories under the same
   parent, store the relation in the parent trajectory. Project each endpoint to
   its compound parent event.
4. If endpoints are nested more deeply, store the relation in their lowest common
   ancestor trajectory. Project each endpoint to the child/compound visible from
   that ancestor.

Parent-level relation without endpoint metadata remains a coarse relation.

## Multi-Line Pack Contract

### Input Shape

Future multi-line pack should use an explicit input object, not two global event
ids:

```json
{
  "title": "Implementation phase",
  "anchor_lane_id": "lane:main",
  "ranges": [
    {
      "lane_id": "lane:main",
      "range_start_event_id": "event:003",
      "range_end_event_id": "event:006"
    },
    {
      "lane_id": "lane:validation",
      "range_start_event_id": "event:011",
      "range_end_event_id": "event:012"
    }
  ]
}
```

Rules:

1. `ranges` must contain at least one range.
2. Each range must refer to one existing lane.
3. Each range must be continuous within its lane after ordering by
   `(order, event_id)`.
4. The same event cannot appear in more than one range.
5. `anchor_lane_id` must be one of the selected lanes.
6. All selected events are removed from the parent trajectory and copied into
   the child trajectory.

### Child Trajectory Shape

The child trajectory preserves the selected lane structure:

1. It has one child lane per selected parent lane.
2. Child lane ids should preserve parent lane ids when possible.
3. Each child lane must record:
   - `source_lane_id`
   - `packed_from_trajectory_id`
   - `packed_into_event_id`
4. Packed child events preserve their original event ids when possible.
5. Packed child events record:
   - `packed_from_trajectory_id`
   - `packed_from_lane_id`
   - `packed_from_event_id`
   - `packed_into_event_id`
   - `packed_at`

### Parent Projection Shape

The parent trajectory receives one anchor compound event in `anchor_lane_id`.

For non-anchor selected lanes, the first implementation should use projection
proxy events instead of silently removing the packed segment.

Proxy event contract:

```json
{
  "kind": "compound",
  "status": "completed",
  "metadata": {
    "compound_mode": "packed-multi-line",
    "compound_role": "proxy",
    "anchor_compound_event_id": "event:020",
    "child_trajectory_id": "child:compound-event-020",
    "packed_lane_id": "lane:validation"
  }
}
```

Rules:

1. The anchor event uses `metadata.compound_role="anchor"`.
2. Proxy events use `metadata.compound_role="proxy"`.
3. Proxy events point to the same `child_trajectory_id` as the anchor event.
4. Proxy events are not independent work. They exist to preserve lane continuity
   and parent-level readability.
5. UI consumers may render proxies as compound entry points, but should be able
   to distinguish them from the anchor by metadata.

This proxy strategy is preferred over silent removal because it keeps parent
lane topology legible and gives future UI a stable alignment surface.

## Relation Rewriting During Multi-Line Pack

When multi-line pack moves events into a child trajectory:

1. Relations with both endpoints inside the selected ranges move into the child
   trajectory.
2. Relations with one endpoint inside and one outside remain in the parent
   trajectory as projected relations.
3. Relations with endpoints inside different selected lanes still move into the
   child trajectory, because both precise endpoints are now in the same child
   trajectory.
4. Existing child trajectories nested under packed events move with their parent
   events into the new child trajectory.

Projected cross-boundary relation rule:

- `source_event_id` and `target_event_id` point to the nearest parent-visible
  projection events.
- metadata records exact `source_endpoint_*` and `target_endpoint_*` fields.
- `relation_projection` is:
  - `cross-boundary` when one side is inside the packed child and one side is
    outside;
  - `cross-compound` when both sides are inside different compound children;
  - omitted for ordinary same-trajectory relations.

## Validation Rules

The backend validator should eventually check:

1. Every `child_trajectory_id` referenced by a compound event exists.
2. Every child trajectory id is unique in the root trajectory tree.
3. Every endpoint metadata group resolves to an existing event.
4. Every projected relation endpoint is either:
   - the exact precise endpoint, or
   - a compound/proxy event that contains the precise endpoint.
5. Multi-line pack ranges are continuous per lane.
6. Anchor and proxy compound events for one multi-line pack point to the same
   child trajectory.
7. A proxy event must have `anchor_compound_event_id`.
8. A proxy event must not be the only event pointing to a child trajectory; an
   anchor event must exist.
9. Relations cannot point directly to events that have been removed from the
   parent trajectory by packing.
10. Child-local relations cannot reference parent-only events.

## Backward Compatibility

Existing consumers remain valid because:

1. `source_event_id` and `target_event_id` stay present on every relation.
2. The parent-level projected relation is still renderable by current UI.
3. Precise endpoint fields are additive metadata.
4. Existing single-line `packRange` remains a special case of multi-line pack
   with one selected lane and no proxy events.
5. Current child trajectory rendering can ignore endpoint metadata and still
   display a coherent parent graph.

## First-Slice Defaults

The following choices are fixed for the first implementation slice:

1. Keep `schema_version` unchanged unless validation code needs to advertise a
   new optional capability.
2. Keep precise cross-compound endpoints in flat metadata fields rather than
   adding first-class relation fields.
3. Keep `kind="compound"` for both anchor and proxy events; distinguish them by
   `metadata.compound_role`.
4. Do not add a user-facing `packMultiLine` or `packSubgraph` MCP action yet.
5. Do not change the read-only Local Work Trajectory UI in this backend slice.
6. Prefer hand-built test fixtures over mutation helpers for the first
   validation pass, so the contract can be tested before creation semantics are
   exposed.

These defaults keep the next slice additive and reversible while still making
cross-pack reliance and multi-line pack shapes machine-checkable.

## First Implementation Slice

The first implementation should not implement a full user-facing `packMultiLine`
operation yet. It should establish the model foundation:

1. Add endpoint parsing/resolution helpers.
2. Add validator checks for endpoint metadata and compound proxy consistency.
3. Add tests with hand-built trajectory fixtures:
   - valid same-child relation;
   - valid parent-to-child projected relation;
   - valid child-to-child cross-compound projected relation;
   - invalid missing child trajectory endpoint;
   - invalid proxy without anchor;
   - invalid non-continuous multi-line pack selection fixture.
4. Keep UI unchanged.
5. Keep MCP `localTrajectory` mutation actions unchanged unless a helper-only
   validation action is explicitly introduced later.

## 2026-06-11 Slice 1 Implementation Notes

Slice 1 is now implemented as an additive backend surface:

1. `TrajectoryEndpoint` exists as a backend dataclass and can be serialized into
   flat `source_endpoint_*` / `target_endpoint_*` relation metadata.
2. `LocalWorkTrajectory.check_invariants()` now validates:
   - recursive child trajectory id uniqueness,
   - endpoint metadata resolvability,
   - projection events containing precise endpoints,
   - compound proxy/anchor consistency.
3. `pack_local_work_subgraph(...)` implements multi-line pack over lane-local
   continuous ranges:
   - the child trajectory preserves selected parent lane ids,
   - the parent layer receives one anchor compound plus proxy compounds on
     non-anchor lanes,
   - internal selected-range relations move into the child trajectory,
   - cross-boundary relations stay parent-visible with precise endpoint
     metadata.
4. `add_local_work_relation(...)` now supports optional `source_endpoint` and
   `target_endpoint` arguments. When precise endpoints live inside compound
   children, the relation is stored at the lowest common trajectory and projected
   to parent-visible compound events.
5. MCP `localTrajectory` now exposes `packSubgraph` plus endpoint fields for
   cross-pack `relate`.
6. The VS Code internal AI tool bridge mirrors the same action and endpoint
   fields so the Host UX thin layer remains aligned with MCP.

Focused validation:

1. `python -m pytest tests/test_progress_graph_trajectory.py tests/test_mcp_tools.py::TestLocalTrajectory -q`
   passed: `36 passed, 1 skipped`.
2. `npm run build` passed in `vscode-extension`.
3. `node --test dist/test/aiChatTools.test.js dist/test/aiChatToolLoop.test.js`
   passed: `7 passed`.

The original no-change boundary still holds for UI layout, global graph
renderer, and scheduling/sandbox semantics.

## Open Questions

These questions remain open for later slices and do not block the validation-only
first slice:

1. Should `TrajectoryEndpoint` become first-class relation fields in
   `schema_version=1.1`, or remain metadata through the first few iterations?
2. Should proxy events use `kind="compound"` permanently, or should a later
   event kind such as `compound_proxy` be introduced?
3. Should multi-line pack creation be one MCP action (`packSubgraph`) or two
   steps (`addCompound` then attach lane ranges)?
4. Should parent-level reliance between compound anchors be auto-created when a
   precise cross-compound relation is added, or should it remain one relation
   with projection metadata?

## No-Change Boundary

This contract does not change:

1. The current read-only Local Work Trajectory UI.
2. Existing single-line lifecycle operations.
3. Existing `packRange` behavior.
4. The global progress graph / knowledge graph renderer.
5. Agent scheduling or sandbox semantics.
