# Worker Trajectory Update Reporting

## Purpose

This document is the fixed worker-facing reference for Local Work Trajectory
write-back handoff.

Workers and subagents do not mutate Local Work Trajectory directly. When a
worker needs to report progress, completion, waiting, blocking, or a suggested
trajectory action, it writes that information into
`Subagent Report.trajectory_update`. The leader/main/supervisor reviews the
report and performs any `localTrajectory` mutation.

If the worker accidentally calls `localTrajectory` and the MCP tool rejects the
call, recover by updating the worker report instead of retrying the tool call.

## Worker Action

Add or update this optional section in the worker report:

```json
{
  "trajectory_update": {
    "lane_id": "lane:<context>",
    "task_id": "task/<worker-task>",
    "event_status": "completed",
    "summary": "Worker completed the lane-scoped task and produced review evidence.",
    "suggested_action": "advance",
    "evidence_refs": [
      ".dbc/agent-output/report-worker.json"
    ],
    "leader_notes": [
      "Advance only after reviewing the changed artifacts and validation output."
    ]
  }
}
```

## Field Contract

- `lane_id`: lane or context id the worker report applies to.
- `task_id`: scheduler task, contract, or worker task id that produced the report.
- `event_status`: one of `completed`, `partial`, `blocked`, `waiting`, `in_progress`.
- `summary`: concise worker progress/status summary for the leader.
- `suggested_action`: one of `append`, `advance`, `block`, `wait`, `resume`, `close`, `none`.
- `evidence_refs`: optional artifact, command, report, or evidence refs.
- `leader_notes`: optional notes for the leader before trajectory mutation.

## Authority Boundary

`trajectory_update` is advisory evidence. It is not a Local Work Trajectory
mutation and does not claim completion of the overall task.

Allowed path:

1. Worker writes `Subagent Report.trajectory_update`.
2. Leader reviews the report, changed artifacts, validation, and unresolved items.
3. Leader consumes the report through `consumeWorkerTrajectoryReport`,
   `doc-based-coding scheduler consume-worker-trajectory-report`, or an
   equivalent host-owned runtime call.
4. Leader decides whether additional manual `localTrajectory` mutation is
   needed for complex pack/merge/anchor work.

## Leader Consumption

First-version automatic consumption is intentionally narrow. It accepts only:

- `append`
- `advance`
- `block`
- `wait`
- `resume`
- `close`
- `none`

It does not consume pack, merge, relate, child-trajectory, or anchor actions from
worker reports. Those remain leader-authored Local Work Trajectory decisions.

CLI example:

```text
doc-based-coding scheduler consume-worker-trajectory-report --report-path .dbc/agent-output/report-worker.json --caller-role leader
```

MCP tool:

```text
consumeWorkerTrajectoryReport
```

If the report suggests `append` and the current workspace has no lifecycle-owned
Local Work Trajectory, the consumer may create the first trajectory event. Other
actions require an existing trajectory or an explicit current event id.

Disallowed path:

1. Worker calls `localTrajectory` directly.
2. Worker edits `.dbc/progress-graph/local-work-trajectory.json` directly.
3. Worker creates a separate trajectory-update proposal artifact for this flow.

## Future Changes

If the worker-to-leader trajectory write-back flow changes later, update this
document first, then update the report schema, MCP rejection message, and
worker prompts to point at the revised procedure.
