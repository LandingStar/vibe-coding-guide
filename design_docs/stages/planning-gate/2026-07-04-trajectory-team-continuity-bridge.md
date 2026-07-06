# Planning Gate - Trajectory Team Continuity Bridge

Date: 2026-07-04

Status: COMPLETED / VERIFIED

## Purpose

Establish the minimum bridge that lets one Local Work Trajectory keep a
leader-worker team continuous across later trajectory nodes.

The important distinction is preserved:

- Local Work lanes describe work structure.
- Scheduler/dispatcher/delivery records describe actual worker dispatch.
- Continuous worker binding, lane ownership, and delivery lease records describe
  whether the same worker identity may be reused.

This gate adds the thin bridge between the first and third layers. It does not
claim that every Local Work lane automatically runs a worker.

## Contract

A trajectory team is represented by compact, project-owned evidence:

1. `trajectory_id`: the Local Work Trajectory that owns the team view.
2. `leader_id`: the leader/guide/supervisor identity responsible for roster
   decisions.
3. `lane_id`: the visible Local Work lane or lane-compatible context stream.
4. `worker_id`: the worker identity assigned to that lane.
5. `binding_id`: the continuous worker binding that carries provider/session
   selector, compact context refs, mailbox cursor refs, worker report refs, and
   private-storage refs.
6. `ownership_id`: the lane ownership record that decides whether that binding
   is selectable for future delivery on that lane.

Once assigned, later same-lane work should resolve the same binding until one
of these explicit events occurs:

- transfer to another binding;
- release ownership;
- fork into a new binding;
- suspend/resume ownership;
- no-continuity fallback with a recorded reason.

Silent worker replacement is forbidden.

## Implementation

Added `src/runtime/orchestration/trajectory_team_continuity.py`.

The module is intentionally thin and delegates durable lifecycle authority to
existing ledgers:

- `claim_continuous_worker_binding()`
- `claim_lane_ownership()`
- `activate_lane_ownership()`
- `transfer_lane_ownership()`
- `release_lane_ownership()`
- `inspect_continuous_worker_bindings()`
- `inspect_lane_ownerships()`

New bridge/readback surfaces:

- `assign_trajectory_lane_worker()`
- `resolve_trajectory_lane_worker()`
- `activate_trajectory_lane_worker()`
- `suspend_trajectory_lane_worker()`
- `resume_trajectory_lane_worker()`
- `transfer_trajectory_lane_worker()`
- `fork_trajectory_lane_worker()`
- `release_trajectory_lane_worker()`
- `record_trajectory_lane_no_continuity()`
- `JsonlTrajectoryTeamContinuityEventLog`

New compact event log:

```text
.codex/runtime/trajectory-team-continuity-events.jsonl
```

Event kinds:

- `trajectory_team_lane_worker_assigned`
- `trajectory_team_lane_worker_resolved`
- `trajectory_team_lane_worker_activated`
- `trajectory_team_lane_worker_suspended`
- `trajectory_team_lane_worker_resumed`
- `trajectory_team_lane_worker_transferred`
- `trajectory_team_lane_worker_forked`
- `trajectory_team_lane_worker_released`
- `trajectory_team_no_continuity_recorded`

The event log records `trajectory_id`, `lane_id`, `leader_id`, `worker_id`,
`binding_id`, `ownership_id`, replacement binding clues, task/delivery evidence
refs, and explicit no-continuity reason. It rejects raw transcript and
secret-like fields.

Public symbols are exported through `src/runtime/orchestration/__init__.py`.

Added scheduler audit-only visibility:

- `SchedulerEvent` now supports compact `metadata`.
- The scheduler event log accepts audit-only continuity event kinds and
  `replay_scheduler_events()` skips those events before task-state replay.
- `trajectory_team_continuity.py` can mirror team roster events into the
  scheduler event log without turning roster facts into scheduler task state.
- `leader_worker_codex_delivery.py` mirrors continuous-worker binding reuse and
  delivery lease reserve/start/complete/failure into the scheduler event log as
  audit-only events.

This gives one scheduler-log read path for task lifecycle, team assignment,
binding reuse, and lease evidence while preserving the existing split of
authority: scheduler task state, team roster, binding ledger, ownership ledger,
delivery lease ledger, runtime invocation log, and Local Work Trajectory remain
separate products.

## Verification

Focused tests added in `tests/test_runtime_orchestration.py`:

- `test_replay_scheduler_events_preserves_and_skips_trajectory_team_audit_events`
- `test_trajectory_team_continuity_reuses_worker_across_same_trajectory_nodes`
- `test_trajectory_team_continuity_records_transfer_release_and_no_continuity`
- `test_trajectory_team_continuity_records_suspend_resume_and_fork`
- `test_trajectory_team_continuity_records_successful_release`

The reuse smoke:

1. assigns one trajectory lane to an OpenCode continuous worker binding;
2. runs the first bounded OpenCode delivery;
3. activates lane ownership from successful delivery evidence;
4. resolves the same lane worker after the first node;
5. runs a second bounded OpenCode delivery on the same trajectory without
   reinitializing the fixture;
6. proves both deliveries use the same `session-team-opencode` host session and
   same binding id;
7. proves the scheduler event log contains audit-only team assignment,
   activation, resolution, binding reuse, and delivery lease reserve/start/
   complete events;
8. proves scheduler recovery skips audit-only events and still recovers task
   state correctly;
9. proves binding reuse, delivery lease, runtime invocation audit, and team
   event evidence are all present.

Focused validation:

```text
python -m pytest tests/test_runtime_orchestration.py -k "trajectory_team_continuity or preserves_and_skips_trajectory_team_audit_events" -q
5 passed, 453 deselected

python -m pytest tests/test_runtime_orchestration.py -k "trajectory_team_continuity or preserves_and_skips_trajectory_team_audit_events or active_promoted_lane_ownership or opencode_delivery_supervisor_uses_continuous_worker_binding or opencode_bounded_loop_reuses_same_continuous_worker or suspended_lane_ownership or active_delivery_lease or worker_trajectory_report_consumer" -q
15 passed, 443 deselected

python -m pytest tests/test_runtime_orchestration.py -k "replay_scheduler_events or recover_scheduler_state_reads_snapshot_and_jsonl_event_log or opencode_delivery_supervisor" -q
28 passed, 430 deselected

python -m py_compile src/runtime/orchestration/scheduler.py src/runtime/orchestration/scheduler_store.py src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/trajectory_team_continuity.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py

git diff --check -- src/runtime/orchestration/scheduler.py src/runtime/orchestration/scheduler_store.py src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/trajectory_team_continuity.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py design_docs/stages/planning-gate/2026-07-04-trajectory-team-continuity-bridge.md "design_docs/Project Master Checklist.md" .codex/progress-graph/local-work-trajectory.json
```

`git diff --check` reported only Windows LF-to-CRLF normalization warnings on
pre-existing tracked files and no whitespace errors.

## Current Limits

This gate does not:

1. make every Local Work lane automatically assign a worker;
2. add a CLI or MCP tool surface for the new bridge;
3. add monitoring UI;
4. implement full agent cluster scheduling;
5. create or manage long-term private storage directories;
6. add `llm-auto` compact;
7. make Codex CLI equivalent to OpenCode direct server/API long-session
   continuity.

The current bridge records `trajectory_id` at the team-continuity layer.
The lower-level continuous worker binding resolver still resolves by
task/agent/lane/lane_group, not by trajectory namespace. A future scheduler
policy gate should decide whether `trajectory_id` becomes a first-class
selection key or remains a higher-level audit/roster key.

## Next Recommended Work

The next narrow gate should expose a host/leader-owned CLI/MCP read/write
surface for this bridge so a leader can assign, inspect, transfer, release, and
record no-continuity without importing runtime Python directly.

Keep that gate separate from live provider execution and monitoring UI.
