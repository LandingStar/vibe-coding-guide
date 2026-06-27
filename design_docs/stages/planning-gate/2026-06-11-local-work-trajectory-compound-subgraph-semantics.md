# Planning Gate - Local Work Trajectory Compound Subgraph Semantics

> Date: 2026-06-11
> Status: IMPLEMENTED-SLICE-1
> Source: user-approved trajectory backend follow-up after Local Work Trajectory UI/compound display work
> Related UI requirement: `design_docs/progress-graph-local-work-trajectory-ui-requirements.md`
> Contract draft: `design_docs/local-work-trajectory-compound-subgraph-contract-draft.md`
> Current active graph integration gate remains: `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`

## Why this exists

Local Work Trajectory now has practical support for lanes, relations, merge events,
compound parent nodes, `packRange`, and child trajectories. The current UI can
display the first compound/pack shape, but the backend semantics are still closer
to "single-lane interval packing" than to a complete local subgraph model.

The next important backend gap is not another UI pass. It is defining how a
compound event represents a local subgraph when that subgraph spans multiple
lanes, and how reliance between events should be represented when either endpoint
lives inside a compound child trajectory.

## Current problem

Current `packRange` semantics are intentionally narrow:

1. It accepts a continuous event interval from one lane.
2. It moves those events into a child trajectory.
3. It rewires parent-level cross-boundary non-sequence relations to the compound
   parent event.
4. It preserves child-local internal relations.

This is enough for single-line folding, but it is insufficient for the next
trajectory model:

1. A real phase/pack can cover multiple lanes at once.
2. Each packed lane segment should remain a lane inside the child trajectory,
   not be flattened into one lane.
3. Cross-pack reliance may refer to compound nodes at the parent level, or to
   precise events inside child trajectories.
4. The current `TrajectoryRelation` only addresses event ids inside one
   trajectory, so it cannot safely express an endpoint such as "event X inside
   child trajectory of compound A".
5. Without a contract, future UI and agent behavior will guess differently about
   whether a relation should be parent-level, child-level, or cross-compound.

## Working terms

- `compound event`: a parent trajectory event with `kind="compound"` and
  `metadata.child_trajectory_id`.
- `child trajectory`: the local trajectory represented by one compound event.
- `single-line pack`: current `packRange` behavior: one continuous same-lane
  event interval becomes one compound event and one child lane.
- `multi-line pack`: a future pack operation that groups continuous intervals
  from multiple parent lanes into one compound child trajectory.
- `parent-level reliance`: a relation whose endpoints are parent trajectory
  events, often compound events.
- `child-local reliance`: a relation whose endpoints are events in the same
  child trajectory.
- `cross-compound reliance`: a relation where at least one endpoint is inside a
  child trajectory and the other endpoint is outside that same child trajectory.

## Scope

This gate defines the backend semantic contract for:

1. Multi-line pack shape:
   - input selection model,
   - parent event replacement rules,
   - child trajectory lane preservation,
   - parent/child metadata required to reconstruct provenance.
2. Cross-compound relation endpoints:
   - how to identify parent events,
   - how to identify child events,
   - how to avoid ambiguous event ids across recursive child trajectories.
3. Relation layering:
   - when a relation remains child-local,
   - when a relation becomes parent-level,
   - when a relation must preserve precise cross-compound endpoint metadata.
4. Validation rules:
   - per-lane continuity for multi-line packs,
   - compound parent/child consistency,
   - relation endpoint resolvability,
   - no dangling nested child trajectory after pack.
5. First implementation slice proposal:
   - minimal data model/API extension,
   - invariant tests,
   - no UI changes unless needed for test fixtures.

## Explicit non-goals

This gate does not:

1. Implement multi-line pack immediately.
2. Rework React Flow UI layout.
3. Add graph editing controls to the webview.
4. Define global graph-to-trajectory registry.
5. Define agent cluster scheduling or sandbox isolation.
6. Replace current `packRange` behavior for the single-line case.
7. Require current Local Work Trajectory JSON consumers to render cross-compound
   precise endpoints in the first implementation slice.

## Current contract baseline

The current contract-first baseline is captured in
`design_docs/local-work-trajectory-compound-subgraph-contract-draft.md`.

That draft narrows the previously open semantic choices as follows:

1. Cross-compound precise endpoints should be represented additively through
   flat relation metadata in the first implementation slice, while preserving
   existing `source_event_id` / `target_event_id` as parent-visible projection
   endpoints.
2. Relation ownership should use the lowest common trajectory that can project
   both endpoints without making existing parent-level UI consumers understand
   nested endpoints.
3. Multi-line pack should be modeled as lane-local continuous ranges grouped
   into one child trajectory, not as one global continuous event range.
4. The child trajectory should preserve selected lanes and provenance metadata.
5. The parent projection should use one anchor compound event plus proxy
   compound events on non-anchor lanes, so parent lane topology stays legible.

This gate remains contract-first: the next code-bearing slice should start with
endpoint resolution and invariant validation over hand-built fixtures, not with a
new user-facing `packMultiLine` mutation API.

## Initial semantic direction

### Multi-line pack

Multi-line pack should not mean "one global continuous event range." Instead, it
should mean a set of lane-local continuous ranges that together form one compound
phase.

Minimum contract:

1. Each selected lane contributes zero or one continuous event interval.
2. At least one selected interval is required.
3. Every event in a selected interval is moved into the child trajectory.
4. Child trajectory preserves one lane per selected parent lane.
5. Child lane metadata records the original parent lane id.
6. The parent trajectory receives one compound event on an explicit anchor lane.
7. Parent lane sequence is rebuilt around the compound event for the anchor lane.
8. Non-anchor lanes must either:
   - receive an explicit placeholder/packed marker, or
   - have their packed segment removed with clear metadata showing that the
     segment is represented by the anchor compound.

The first implementation should prefer the conservative option that is easiest
to validate. If placeholder markers are chosen, they must not masquerade as
independent work events.

### Cross-pack reliance

Reliance should have three layers:

1. Parent-level reliance:
   - endpoints are parent events;
   - compound-to-compound reliance is the default display surface.
2. Child-local reliance:
   - endpoints are inside the same child trajectory;
   - it remains wholly inside that child trajectory.
3. Cross-compound reliance:
   - endpoints may be inside different child trajectories, or one endpoint may
     be parent-level and the other child-level;
   - it requires explicit endpoint addressing, not just plain event ids.

Candidate endpoint shape:

```json
{
  "trajectory_id": "local-work:single-line-current",
  "event_id": "event:003"
}
```

For child endpoints:

```json
{
  "trajectory_id": "child:compound-event-003",
  "event_id": "event:002",
  "parent_event_id": "event:003"
}
```

Open design decision: whether this should be introduced as a new
`TrajectoryEndpoint` structure on `TrajectoryRelation`, or as relation metadata
while preserving old `source_event_id` / `target_event_id` as coarse parent-level
projection. The first implementation should maintain backward compatibility for
existing UI consumers.

## Proposed first slice

The first slice should be contract-first and validation-heavy:

1. Treat `design_docs/local-work-trajectory-compound-subgraph-contract-draft.md`
   as the implementation reference for:
   - multi-line pack input,
   - endpoint addressing,
   - relation layering,
   - parent projection fallback.
2. Add endpoint parsing/resolution helpers only as needed by validation.
3. Add invariant checks for endpoint metadata and compound proxy consistency.
4. Add tests that model valid and invalid shapes without changing UI:
   - valid single-line pack remains valid,
   - valid multi-line compound child shape,
   - invalid non-continuous per-lane selection,
   - invalid relation endpoint to missing child trajectory,
   - valid cross-compound relation with coarse parent projection.
5. Add model helpers only if needed to make tests readable.
6. Keep existing `packRange` and `relate` APIs stable unless the contract shows a
   safe additive extension.

## Acceptance and validation

This planning gate is complete when:

1. The multi-line pack contract is written clearly enough to implement.
2. The cross-compound endpoint contract is written clearly enough to implement.
3. The first implementation slice is narrowed to additive model/validation work.
4. Explicit non-goals remain intact.
5. The result is written back to the Local Work Trajectory requirements or a
   dedicated backend contract document.

## 2026-06-11 Implementation Result

The first backend slice has been implemented against the contract draft:

1. Multi-line pack is available as `pack_local_work_subgraph(...)` and MCP
   `localTrajectory action="packSubgraph"`.
2. Multi-line pack uses lane-local continuous ranges, preserves child lanes, and
   projects parent-level anchor/proxy compound events.
3. Cross-pack reliance is available through `add_local_work_relation(...)`
   endpoint arguments and MCP `relate` endpoint fields.
4. Validation now checks endpoint metadata and compound proxy/anchor consistency.
5. No React Flow layout or global graph renderer changes were made.

Validation evidence:

1. `python -m pytest tests/test_progress_graph_trajectory.py tests/test_mcp_tools.py::TestLocalTrajectory -q`
   passed: `36 passed, 1 skipped`.
2. `npm run build` passed in `vscode-extension`.
3. `node --test dist/test/aiChatTools.test.js dist/test/aiChatToolLoop.test.js`
   passed: `7 passed`.

## Stop condition

Stop after the semantic contract and first implementation slice are approved or
ready for review. Do not start implementing multi-line pack or cross-compound
relations inside this planning gate unless the user explicitly asks to proceed
from contract into implementation.
