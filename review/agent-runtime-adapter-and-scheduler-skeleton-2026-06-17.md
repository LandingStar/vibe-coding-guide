# Agent Runtime Adapter And Scheduler Skeleton Evidence Review — 2026-06-17

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-16-agent-runtime-adapter-and-scheduler-skeleton.md`.

Verdict: ready for close review.

The implementation evidence satisfies the gate acceptance criteria. The gate
should not be treated as a full production scheduler yet: real Qoder execution,
real process isolation, daemon scheduling, retry/timeout enforcement, full
ExchangeArtifact persistence, and UI rendering remain explicit non-goals or
later slices.

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Adapter contract can map to Qoder and fake runtime without changing scheduler objects. | `src/runtime/orchestration/runtime_adapter.py` defines the provider-neutral adapter contract, fake adapter, mockable Qoder adapter, registry, Qoder request/result shapes, and response/error normalization. `src/runtime/orchestration/runtime_wiring.py` adds host-owned provider wiring and permission grants. Tests include `test_qoder_capability_mapping_is_runtime_not_scheduler`, `test_runtime_registry_wiring_can_register_authorized_mock_qoder_client`, `test_scheduler_runs_qoder_adapter_through_registry_with_mock_client`, and `test_run_persisted_scheduler_once_with_host_authorized_qoder_wiring`. | Met |
| Scheduler state can represent at least a three-task graph with dependencies. | `SchedulerState`, `ScheduledTask`, and `TaskDependency` are snapshot-owned objects in `src/runtime/orchestration/scheduler.py`; batch submission lives in `scheduler_submission.py`. Tests include `test_scheduler_state_snapshot_round_trips_task_graph`, `test_scheduler_task_batch_submission_adds_multiple_tasks_and_dependencies`, `test_scheduler_task_batch_submission_graph_can_drain_after_submission`, and drain dependency-chain tests. | Met |
| A fake runtime task can complete through the adapter boundary. | `FakeAgentRuntimeAdapter` consumes versioned `ExchangeArtifact` refs and produces a result artifact through `RuntimeRunResult`. Scheduler execution paths include `run_ready_task`, `run_scheduled_task_with_registry`, `run_preflighted_task`, and persisted runner helpers. Tests include `test_fake_runtime_consumes_input_artifact_and_produces_result_artifact`, `test_scheduler_runs_ready_task_through_fake_runtime`, `test_scheduler_runs_ready_task_through_registry_runtime`, and `test_run_persisted_scheduler_once_recovers_drains_and_writes_snapshot`. | Met |
| Edit lease conflict detection has focused tests. | `evaluate_task_admission()` blocks conflicting write leases against ready or running tasks. Tests include `test_scheduler_blocks_conflicting_write_leases_against_ready_or_running_tasks` and `test_drain_ready_tasks_reports_blocked_admission_without_running`. | Met |
| Context scope, edit lease, and sandbox profile are first-class data objects. | `ContextScope`, `EditScopeLease`, and `SandboxProfile` are scheduler dataclasses and round-trip through snapshots and submission artifacts. `src/runtime/orchestration/sandbox.py` and `preflight.py` provide provider and preflight contracts. Tests include `test_orchestration_preflight_bundle_assembles_runtime_sandbox_and_scratch`, `test_scheduler_state_snapshot_round_trips_task_graph`, and submission round-trip tests. | Met |
| Documentation preserves that orchestration state is authority and Local Work Trajectory is projection. | The gate's projection and preview consumption contract explicitly separates `.codex/progress-graph/local-work-trajectory.json` from `.codex/progress-graph/scheduler-work-trajectory.json`. `tools/progress_graph/scheduler_projection.py` implements one-way projection. Tests include `test_scheduler_mcp_submit_project_run_smoke_keeps_authority_split`, `test_scheduler_projection_writes_separate_artifact_from_snapshot_and_history`, and scheduler projection tests. | Met |
| Scheduler skeleton can reference exchange artifact IDs/placeholders without treating prose transcript as authority. | `ExchangeReference`, `ExchangeArtifact`, scheduler submission artifacts, fake runtime inputs, output artifact refs, and scheduler events carry artifact IDs and versions. The `log` payload part stores compact history clues, not raw transcript authority. Tests include `test_exchange_blocker_with_relation_part_is_scheduler_readable`, `test_exchange_log_part_is_compact_history_not_raw_transcript`, `test_scheduler_task_submission_artifact_round_trips_to_structured_request`, and `test_scheduler_task_batch_submission_adds_multiple_tasks_and_dependencies`. | Met |

## Validation

Focused validation run on 2026-06-17:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "exchange_log_part or scheduler_task_submission_artifact_round_trips or scheduler_task_batch_submission"
7 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py -k "scheduler_submit_tasks"
4 passed

pack_verify
2 ok
```

Earlier same-gate validation recorded in the active work context:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_mcp_tools.py
202 passed
```

## Residual Risk

The following items remain outside this gate and should not block close review:

1. Real Qoder SDK import and execution.
2. Real opencode adapter behavior.
3. Real process, Docker, remote VM, or git-worktree isolation.
4. Scheduler daemon behavior, parallel execution, retry loops, cancellation, and timeout enforcement.
5. Full ExchangeArtifact persistence and UI rendering.
6. Persistent Agent Home storage.
7. Event-log truncation or rotation policy.

## Close Recommendation

Move the planning gate from `DRAFT` to `READY-FOR-CLOSE-REVIEW`.

The next step should be a narrow close writeback bundle: update the active gate
summary, decide the immediate follow-up direction, and then synchronize the
project status surfaces only if the user accepts formal close.
