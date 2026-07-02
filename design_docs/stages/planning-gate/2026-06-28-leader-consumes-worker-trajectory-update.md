# Planning Gate - Leader Consumes Worker Trajectory Update

> Date: 2026-06-28
> Status: COMPLETED

## Trigger

The completed Local Trajectory Worker Report Ownership Guard moved worker-side
Local Work Trajectory write-back into `Subagent Report.trajectory_update` and
blocked explicit worker/subagent `localTrajectory` calls at the MCP layer.

The remaining gap is leader-side consumption: a leader/main/supervisor needs a
small, auditable way to review a worker report and turn the advisory
`trajectory_update` into a leader-owned Local Work Trajectory mutation.

## Scope

This gate adds the first narrow consumer:

1. read one worker `Subagent Report` JSON file;
2. validate the whole report against `docs/specs/subagent-report.schema.json`;
3. consume only the safe first-version `trajectory_update.suggested_action`
   values: `append`, `advance`, `block`, `wait`, `resume`, `close`, and `none`;
4. keep the consumer leader/main/supervisor/guide authority only;
5. map `lane_id`, `summary`, `task_id`, `evidence_refs`, and `leader_notes`
   into the trajectory mutation/result audit without guessing hidden event ids;
6. expose the consumer through runtime, CLI, and MCP surfaces;
7. return an auditable payload that says whether it consumed, skipped, failed
   validation, or was denied before mutation.

## Non-Goals

This gate does not:

1. let workers/subagents directly mutate Local Work Trajectory;
2. consume pack/merge/relate/anchor/child-trajectory operations from worker
   reports;
3. invent event ids or lane ids not already present in the report or current
   trajectory;
4. mark worker reports consumed in ExchangeArtifact state;
5. run providers, scheduler tasks, or delivery supervisors;
6. change worker report schema beyond the already completed
   `trajectory_update` field;
7. automatically integrate this consumer into every Codex delivery supervisor
   loop.

## Acceptance Criteria

This gate may close when:

1. invalid worker reports are rejected before Local Work Trajectory mutation;
2. reports without `trajectory_update`, or with `suggested_action=none`, return
   a skipped/non-consumed audit payload without mutation;
3. explicit worker/subagent caller roles are denied before mutation and point
   back to `docs/worker-trajectory-update-reporting.md`;
4. leader/main/supervisor/guide caller roles can consume supported actions;
5. `append` can create the first trajectory event when no lifecycle trajectory
   exists, while other actions require an existing lifecycle trajectory and
   return a clear diagnostic if it is missing;
6. runtime, CLI, and MCP surfaces expose the same authority split;
7. focused runtime/CLI/MCP tests pass.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/worker_trajectory_report_consumer.py src/runtime/orchestration/__init__.py src/mcp/tools.py src/mcp/server.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "worker_trajectory_report" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "worker_trajectory_report" -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "worker_trajectory_report" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
git diff --check -- src/runtime/orchestration/worker_trajectory_report_consumer.py src/runtime/orchestration/__init__.py src/mcp/tools.py src/mcp/server.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py docs/worker-trajectory-update-reporting.md docs/subagent-schemas.md docs/subagent-management.md design_docs/Project\ Master\ Checklist.md design_docs/stages/planning-gate/2026-06-28-leader-consumes-worker-trajectory-update.md
```

## Implementation Summary

Completed on 2026-06-28.

Implemented the first leader-side `trajectory_update` consumer:

1. Added runtime helper
   `src/runtime/orchestration/worker_trajectory_report_consumer.py` with
   `WorkerTrajectoryReportConsumerRequest`,
   `WorkerTrajectoryReportConsumerResult`, and
   `consume_worker_trajectory_report()`.
2. The consumer reads one worker `Subagent Report` JSON file, validates it
   against `docs/specs/subagent-report.schema.json`, and refuses mutation before
   schema-valid evidence exists.
3. Supported actions are intentionally limited to `append`, `advance`, `block`,
   `wait`, `resume`, `close`, and `none`.
4. Worker/subagent caller roles are rejected before mutation and directed back
   to `docs/worker-trajectory-update-reporting.md`.
5. `append` may create the first lifecycle-owned Local Work Trajectory event
   when no trajectory exists or when the trajectory is the explicit empty
   lifecycle artifact; other actions require an existing trajectory/current
   event context.
6. Added CLI surface:
   `doc-based-coding scheduler consume-worker-trajectory-report`.
7. Added MCP surface: `consumeWorkerTrajectoryReport`.
8. Updated worker/report docs and MCP tool surface audit to document the
   worker-report-to-leader-consumer path.

## Validation Evidence

Validated on 2026-06-28:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/worker_trajectory_report_consumer.py src/runtime/orchestration/__init__.py src/mcp/tools.py src/mcp/server.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_admission.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "worker_trajectory_report" -q
4 passed, 340 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "worker_trajectory_report" -q
2 passed, 105 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "worker_trajectory_report" -q
1 passed, 32 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "worker_trajectory_update_reporting" -q
1 passed, 23 deselected

.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
passed

git diff --check -- <touched non-runtime files>
passed with Windows line-ending warnings only
```

## Residual Risk After Close

This gate provides an explicit leader-side consumer but does not yet integrate
it automatically into Codex delivery supervisor loops or ExchangeArtifact
lifecycle consumption. A later gate should decide where report consumption sits
in the live supervisor pipeline and how accepted/consumed worker report artifacts
are tracked.
