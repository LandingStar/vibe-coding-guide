# Scheduler Native Merge Gate Design Record

> Date: 2026-06-17
> Status: design record / skeleton implemented

## Context

The scheduler projection can already show multi-dependency fan-in as a
projection-only merge event in Local Work Trajectory. That is useful for reading
the graph, but it is not a scheduler lifecycle primitive.

The remaining question is whether the scheduler itself needs a native merge
gate / fan-in lifecycle state.

Related documents:

- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `design_docs/stages/planning-gate/2026-06-16-agent-runtime-adapter-and-scheduler-skeleton.md`
- `tools/progress_graph/scheduler_projection.py`
- `src/runtime/orchestration/scheduler.py`

## Current Boundary

Current scheduler authority is still:

```text
SchedulerState
- ScheduledTask
- TaskDependency
- TaskRunRecord
```

Current Local Work Trajectory projection is read-only:

```text
SchedulerState -> build_scheduler_work_trajectory() -> LocalWorkTrajectory view
```

The synthetic `merge` event produced by the projector is only a display summary.
It does not create a scheduler task, does not change readiness, and does not
resolve dependencies.

## Decision

Do not promote every multi-dependency fan-in into a scheduler-native merge gate.

Default behavior should remain dependency-only:

1. A task with two or more dependencies waits until all required source tasks
   reach their required state.
2. Once all dependencies are satisfied, normal admission decides whether the
   target task can run.
3. Local Work Trajectory may summarize the fan-in with a synthetic merge event,
   but the scheduler does not treat that synthetic event as state.

Introduce a scheduler-native merge gate only when there is real scheduler work at
the join point.

## When A Native Merge Gate Is Needed

A native merge gate is justified when fan-in requires one or more of these:

1. A human or guide-agent review before downstream execution.
2. Combining multiple upstream outputs into a new artifact.
3. Choosing one branch result among alternatives.
4. Checking compatibility between branch results.
5. Resolving edit-lease or authority-doc conflicts across branches.
6. Recording an explicit fan-in decision as scheduler-owned audit state.
7. Pausing downstream tasks until a merge decision is approved or rejected.

If none of these are true, `TaskDependency` is sufficient.

## Proposed Product Shape

The first scheduler-native merge gate should be a separate product, not an
overloaded `ScheduledTask`.

Recommended first contract:

```text
SchedulerMergeGate
- gate_id
- title
- target_task_id
- source_task_ids
- dependency_ids
- gate_kind
- state
- required_review
- input_artifact_refs
- output_artifact_id
- decision_artifact_ref
- blocked_reason
- created_at
- resolved_at
```

Recommended `gate_kind` values:

```text
join_only
review
artifact_merge
branch_choice
compatibility_check
conflict_resolution
```

Recommended `state` values:

```text
proposed
waiting
ready
review_required
complete
blocked
cancelled
```

## Scheduler Semantics

For the first implementation slice, a merge gate should behave like a gate
between upstream tasks and one downstream task:

1. A gate waits until every referenced dependency is satisfied.
2. A ready gate may either auto-complete or enter `review_required`, depending
   on `gate_kind` and `required_review`.
3. The downstream target task should not become ready until the gate is
   `complete`.
4. Gate completion may produce `decision_artifact_ref` or `output_artifact_id`.
5. Gate rejection / failure blocks the gate and keeps the target waiting or
   blocked according to policy.

This keeps the scheduler authority clear:

```text
upstream tasks -> dependencies -> merge gate -> target task
```

## Event History

Native merge gates should have dedicated scheduler event kinds instead of being
encoded only through task events.

Recommended first event kinds:

```text
merge_gate_submitted
merge_gate_waiting
merge_gate_ready
merge_gate_review_required
merge_gate_completed
merge_gate_blocked
merge_gate_cancelled
```

These events remain append-only history. The snapshot remains the contract
authority, and replay must not invent merge gate contracts from event history.

## Projection Semantics

Projection should distinguish two cases:

1. `projection-only fan-in summary`
   - Generated from plain multi-dependency targets.
   - Synthetic `merge` event metadata includes
     `scheduler_projection_role=fan-in-merge`.
   - It is not clickable as a scheduler-owned object.

2. `scheduler-owned merge gate`
   - Generated from `SchedulerMergeGate`.
   - Projected `merge` event metadata should include
     `scheduler_merge_gate_id`, `scheduler_merge_gate_state`, and
     `scheduler_merge_gate_kind`.
   - It is a real scheduler object and may support future review / jump /
     detail actions.
   - If merge-gate event history is supplied to the projector, the same
     projected event may include `scheduler_merge_gate_event_ids`,
     `scheduler_merge_gate_event_kinds`,
     `scheduler_merge_gate_event_timestamps`,
     `scheduler_merge_gate_event_sequences`, decision artifact clues, and a
     compact `scheduler_merge_gate_event_log` list. These fields are for
     historical communication management and UI inspection only; the snapshot
     remains authoritative.

## Non-Goals

This design record does not implement:

1. Merge gate runtime execution.
2. Review UI.
3. Daemon scheduling.
4. Real Qoder execution.
5. Parallel process execution.
6. Automatic branch conflict resolution.

## Recommended Next Slice

The first code slice has been implemented narrowly:

1. Add `SchedulerMergeGate` as a snapshot-owned data object.
2. Add JSON snapshot round-trip support.
3. Add a read-only projection path for scheduler-owned merge gates.
4. Add no runtime execution and no automatic merge resolution yet.

This gives the scheduler a native product when it is actually needed, without
turning every dependency fan-in into a heavier lifecycle object.

Current implementation:

```text
src/runtime/orchestration/scheduler.py
- SchedulerMergeGate
- SchedulerMergeGateKind
- SchedulerMergeGateState
- SchedulerMergeGateEvent
- SchedulerMergeGateEventKind
- SchedulerMergeGateEventSink
- SchedulerState.merge_gates
- merge-gate-aware target admission
- resolve_scheduler_merge_gate()

src/runtime/orchestration/scheduler_store.py
- merge_gates snapshot round-trip
- JsonlSchedulerMergeGateEventLog

tools/progress_graph/scheduler_projection.py
- scheduler-owned merge gate projection
- scheduler JSONL history projection helper
- scheduler projection artifact writer
```

Focused validation covers snapshot round-trip and projection behavior. The
projection distinguishes `scheduler-owned-merge-gate` from projection-only
`fan-in-merge` summaries and suppresses the synthetic fan-in summary when a real
gate exists for the same target task.

Target admission now respects scheduler-owned merge gates: after ordinary task
dependencies are satisfied, a target task waits while any merge gate targeting
it is not `complete`. Once the gate reaches `complete`, normal admission may
mark the target task ready. This is still not merge gate execution; it is only
target gating.

`resolve_scheduler_merge_gate()` provides the first external decision loop. A
guide / review surface can approve a non-terminal gate, which marks it
`complete`, stores an optional decision artifact reference, and re-evaluates the
target task. The same API can reject a non-terminal gate, which marks it
`blocked` and leaves the target waiting on that gate. This is still not an
automatic artifact merge or runtime execution path.

Merge-gate-specific event schema now exists separately from task scheduler
events. `SchedulerMergeGateEvent` covers gate lifecycle history such as
`merge_gate_completed` and `merge_gate_blocked`, and
`JsonlSchedulerMergeGateEventLog` persists those records as append-only JSONL.
`resolve_scheduler_merge_gate()` can optionally record completed / blocked
events through this sink.

Scheduler-owned merge gate projection can now include that history on the
projected merge event. It preserves ordered event IDs, kinds, timestamps,
sequences, decision artifact references, and a compact
`scheduler_merge_gate_event_log` line list so later readers can reconstruct the
communication timeline around the gate without opening the JSONL file first.

`build_scheduler_work_trajectory_from_history()` is the thin persisted-history
entrypoint. It reads optional scheduler task event JSONL and merge-gate event
JSONL logs, injects them into the read-only trajectory projection, and records
the source paths / event counts as trajectory metadata. This gives UI and review
surfaces one call for "snapshot plus known history" without changing scheduler
recovery semantics.

`write_scheduler_work_trajectory_artifact()` writes that read-only projection to
`.codex/progress-graph/scheduler-work-trajectory.json` by default. This path is
separate from agent-owned `.codex/progress-graph/local-work-trajectory.json`, so
refreshing scheduler visualization does not overwrite the Local Work Trajectory
lifecycle artifact maintained by agents.

MCP `schedulerProjection` now wraps the same artifact writer for host and agent
callers. It accepts a scheduler snapshot path and optional task / merge-gate
JSONL history paths, then returns the written projection path and compact counts.
This makes merge-gate history projection refreshable without granting the tool
authority to mutate scheduler contracts or agent-owned trajectory lifecycle
state.

`read_trajectory_artifacts_bundle()` now provides the non-visual consumption
contract for preview adapters. It reads the agent-owned local trajectory and the
scheduler-derived trajectory independently, preserving role, path, existence,
parse error, payload, and summary for each artifact. A broken local trajectory
therefore does not hide a valid scheduler projection, and vice versa.

This event log is history only. It is not replayed by `recover_scheduler_state()`
and must not create merge gate contracts from history; the scheduler snapshot
remains the authority.
