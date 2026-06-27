"""Targeted tests for local work trajectory projection."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from src.runtime.orchestration import (
    AgentSpec,
    ArtifactDelta,
    CodexCliRequest,
    CodexCliResult,
    AgentRuntimeAdapterRegistry,
    ContextScope,
    GuideWorkerInstruction,
    GuideWorkerPlannerLaneSpec,
    GuideWorkerPlanningRequest,
    GitWorktreeCommandReceipt,
    GitWorktreeSandboxReceipt,
    EditScopeLease,
    ExchangeReference,
    FakeAgentRuntimeAdapter,
    HostSchedulerRunEvidenceSummary,
    HostSchedulerRunRequest,
    InMemoryArtifactVersionStore,
    JsonlSchedulerEventLog,
    JsonlSchedulerMergeGateEventLog,
    RuntimeHostInvocation,
    RuntimeProviderPermissionGrant,
    RuntimeRegistryWiringConfig,
    HostSchedulerDaemonLoopRequest,
    SchedulerLoopEvidenceSummary,
    QoderSDKQueryClient,
    QoderQueryRequest,
    QoderQueryResult,
    QoderRuntimeError,
    SchedulerEvent,
    SchedulerMergeGate,
    SchedulerMergeGateEvent,
    SchedulerDaemonLoopStopPolicy,
    SchedulerRunPolicy,
    SchedulerTaskBatchSubmission,
    SchedulerTaskSubmission,
    SandboxProfile,
    SandboxProviderRegistry,
    ScheduledTask,
    ScheduledTaskState,
    SchedulerState,
    SandboxAllocation,
    SandboxLeaseMountAuthorization,
    SharedProcessSandboxProvider,
    TaskDependency,
    TaskRunRecord,
    build_sandbox_allocation_receipt_evidence,
    build_supervisor_storage_binding_evidence,
    default_supervisor_storage_binding_evidence_path,
    GitWorktreeSandboxProvider,
    run_persisted_scheduler_once,
    read_sandbox_allocation_receipt_evidence_summary,
    read_scheduler_state_snapshot,
    scheduler_task_batch_submission_to_artifact,
    submit_scheduler_task_batch_with_persistence,
    write_sandbox_allocation_receipt_evidence,
    write_scheduler_state_snapshot,
    write_supervisor_storage_binding_evidence,
    JsonArtifactVersionStore,
    JsonlRuntimeInvocationLog,
)
from src.runtime.orchestration.agent_exchange_action_candidates import (
    inspect_agent_exchange_action_candidates,
)
from src.workflow.checkpoint import write_checkpoint
from tools.progress_graph import (
    LocalWorkTrajectory,
    TrajectoryEvent,
    TrajectoryEndpoint,
    TrajectoryLane,
    TrajectoryRelation,
    HostOwnedQoderSmokeRunConfig,
    HostOwnedGuideWorkerProviderExecutionConfig,
    add_local_work_compound,
    add_local_work_lane,
    add_local_work_lanes,
    add_local_work_relation,
    advance_local_work_child_event,
    advance_single_line_event,
    append_local_work_child_event,
    append_single_line_event,
    block_single_line_event,
    build_checkpoint_work_trajectory,
    build_scheduler_work_trajectory,
    build_scheduler_work_trajectory_from_history,
    clear_single_line_trajectory,
    close_local_work_child_trajectory,
    close_single_line_trajectory,
    load_local_work_trajectory,
    merge_local_work_lane,
    pack_local_work_range,
    pack_local_work_subgraph,
    QoderSmokeTaskConfig,
    HostEvidenceBundle,
    HostEvidenceReadError,
    SchedulerSupervisorDogfoodWorkflowRequest,
    build_supervisor_dogfood_storage_binding,
    host_scheduler_evidence_dir,
    build_host_evidence_presentation,
    read_host_evidence_bundle,
    read_trajectory_artifacts_bundle,
    resume_single_line_event,
    run_host_authorized_scheduler_daemon_loop_and_refresh_projection,
    run_host_authorized_scheduler_once_and_refresh_projection,
    run_host_owned_guide_worker_provider_execution,
    run_host_owned_qoder_smoke,
    run_host_runtime_dogfood_harness,
    run_persisted_scheduler_once_and_refresh_projection,
    run_scheduler_supervisor_dogfood_workflow,
    scheduler_work_trajectory_json_path,
    set_local_work_trajectory_anchor,
    start_single_line_trajectory,
    update_single_line_event,
    write_checkpoint_work_trajectory,
    write_local_work_trajectory_artifact,
    write_scheduler_work_trajectory_artifact,
)

DBC_TEST_WORKSPACE = Path(r"C:\Users\16329\OneDrive\Desktop\tmp\dbc-test")


def test_build_checkpoint_work_trajectory_projects_single_lane_todos(tmp_path: Path) -> None:
    write_checkpoint(
        tmp_path,
        phase="Post-v1.0 graph work",
        planning_gate="design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md",
        todos=[
            {"title": "记录 UI 需求", "status": "done"},
            {"title": "实现单线后端轨迹", "status": "in-progress"},
            {"title": "后续接入 UI", "status": "not-started"},
        ],
    )

    trajectory = build_checkpoint_work_trajectory(tmp_path)

    assert trajectory.summary() == {
        "trajectory_id": "local-work:checkpoint-current",
        "title": "Checkpoint Local Work Trajectory",
        "lane_count": 1,
        "event_count": 3,
        "relation_count": 2,
        "source_graph_id": "checkpoint-current",
        "source_node_id": "milestone:current-phase",
    }
    assert trajectory.guide_context == (
        "design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md"
    )
    assert list(trajectory.lanes) == ["lane:main"]
    lane = trajectory.lanes["lane:main"]
    assert lane.label == "2026 05 27 knowledge gra"
    assert lane.status == "active"
    assert [event.title for event in trajectory.events.values()] == [
        "记录 UI 需求",
        "实现单线后端轨迹",
        "后续接入 UI",
    ]
    assert [event.status for event in trajectory.events.values()] == [
        "completed",
        "in_progress",
        "pending",
    ]
    assert [
        (relation.source_event_id, relation.target_event_id, relation.kind)
        for relation in trajectory.relations
    ] == [
        ("event:001", "event:002", "sequence"),
        ("event:002", "event:003", "sequence"),
    ]


def test_write_checkpoint_work_trajectory_round_trips_json(tmp_path: Path) -> None:
    write_checkpoint(
        tmp_path,
        phase="Single line trajectory",
        todos=[
            {"title": "Alpha", "status": "done"},
            {"title": "Beta", "status": "not-started"},
        ],
    )

    path = write_checkpoint_work_trajectory(tmp_path)
    loaded = load_local_work_trajectory(tmp_path)

    assert path == tmp_path / ".codex/progress-graph/local-work-trajectory.json"
    assert loaded.trajectory_id == "local-work:checkpoint-current"
    assert list(loaded.events) == ["event:001", "event:002"]
    assert loaded.events["event:001"].metadata["checkpoint_todo_id"] == "todo:001"
    assert loaded.relations[0].kind == "sequence"


def test_build_scheduler_work_trajectory_projects_lanes_tasks_dependencies_and_runs() -> None:
    state = SchedulerState(
        tasks={
            "api/task": _scheduler_projection_task(
                "api/task",
                lane_id="lane:server",
                state="complete",
                run_id="run-api-1",
                output_ref=ExchangeReference(
                    ref_kind="exchange_artifact",
                    ref_id="api-result",
                    version="v1",
                ),
            ),
            "ui task": _scheduler_projection_task(
                "ui task",
                lane_id="lane:client",
                state="waiting",
                blocked_reason="waiting for api/task to reach complete",
            ),
            "qa/task": _scheduler_projection_task(
                "qa/task",
                lane_id="lane:client",
                state="blocked",
                blocked_reason="edit lease conflict with ui task",
                edit_lease=EditScopeLease(
                    lease_id="lease-qa",
                    task_id="qa/task",
                    allowed_artifacts=("tests/test_maze.py",),
                    lease_mode="write",
                ),
            ),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-api-ui",
                source_task_id="api/task",
                target_task_id="ui task",
                dependency_kind="depends_on",
                required_state="complete",
            ),
        ),
        run_records=(
            TaskRunRecord(
                task_id="api/task",
                run_id="run-api-1",
                session_id="session-api-1",
                output_artifact_id="api-result",
                output_artifact_version="v1",
                state="complete",
            ),
        ),
    )

    trajectory = build_scheduler_work_trajectory(
        state,
        recorded_at="2026-06-16T18:30:00+08:00",
        guide_context="design_docs/stages/planning-gate/2026-06-16-agent-runtime-adapter-and-scheduler-skeleton.md",
    )

    assert trajectory.metadata["projection"] == "scheduler-state"
    assert trajectory.metadata["authority"] == "scheduler"
    assert trajectory.metadata["trajectory_role"] == "read-only-view"
    assert trajectory.metadata["task_count"] == "3"
    assert trajectory.recorded_at == "2026-06-16T18:30:00+08:00"
    assert set(trajectory.lanes) == {"lane:client", "lane:server"}
    assert trajectory.lanes["lane:client"].status == "blocked"
    assert trajectory.lanes["lane:server"].status == "done"

    api_event = trajectory.events["scheduler-task:api-task"]
    ui_event = trajectory.events["scheduler-task:ui-task"]
    qa_event = trajectory.events["scheduler-task:qa-task"]
    assert api_event.status == "completed"
    assert api_event.metadata["run_id"] == "run-api-1"
    assert api_event.metadata["run_record_run_ids"] == "run-api-1"
    assert api_event.metadata["output_artifact_id"] == "api-result"
    assert ui_event.kind == "wait"
    assert ui_event.status == "waiting"
    assert ui_event.summary == "waiting for api/task to reach complete"
    assert qa_event.status == "blocked"
    assert qa_event.metadata["edit_lease_allowed_artifacts"] == "tests/test_maze.py"

    depends = [
        relation for relation in trajectory.relations
        if relation.kind == "depends_on"
    ]
    assert len(depends) == 1
    assert depends[0].source_event_id == "scheduler-task:api-task"
    assert depends[0].target_event_id == "scheduler-task:ui-task"
    assert depends[0].metadata["scheduler_dependency_id"] == "dep-api-ui"
    assert trajectory.check_invariants() == []


def test_build_scheduler_work_trajectory_keeps_unique_event_ids_after_task_id_normalization() -> None:
    state = SchedulerState(
        tasks={
            "a/b": _scheduler_projection_task("a/b", lane_id="lane:main"),
            "a b": _scheduler_projection_task("a b", lane_id="lane:main"),
        }
    )

    trajectory = build_scheduler_work_trajectory(state)

    assert set(trajectory.events) == {
        "scheduler-task:a-b",
        "scheduler-task:a-b:2",
    }
    assert trajectory.check_invariants() == []


def test_build_scheduler_work_trajectory_projects_empty_scheduler_as_read_only_view() -> None:
    trajectory = build_scheduler_work_trajectory(SchedulerState())

    assert trajectory.metadata["projection"] == "scheduler-state"
    assert trajectory.metadata["task_count"] == "0"
    assert trajectory.lanes["lane:scheduler"].status == "pending"
    assert trajectory.events == {}
    assert trajectory.relations == []
    assert trajectory.check_invariants() == []


def test_persisted_scheduler_runner_result_is_visible_in_scheduler_projection(tmp_path: Path) -> None:
    artifact_store = InMemoryArtifactVersionStore()
    runtime_registry = AgentRuntimeAdapterRegistry()
    runtime_registry.register(
        FakeAgentRuntimeAdapter(
            artifact_store=artifact_store,
            timestamp="2026-06-17T01:30:00+08:00",
        )
    )
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    batch_artifact = scheduler_task_batch_submission_to_artifact(
        SchedulerTaskBatchSubmission(
            batch_id="projection-smoke",
            tasks=(
                SchedulerTaskSubmission(
                    task_id="server-contract",
                    title="Write server contract",
                    instruction="Produce the deterministic server contract artifact.",
                    agent=AgentSpec(agent_id="agent:server", runtime_provider="fake"),
                    context_scope=ContextScope(
                        context_id="context:server",
                        lane_id="lane:server",
                    ),
                    sandbox_profile=SandboxProfile(
                        profile_id="shared-server",
                        profile_kind="shared-process",
                    ),
                    acceptance=("server contract artifact is produced",),
                    output_artifact_id="server-contract:result",
                ),
                SchedulerTaskSubmission(
                    task_id="client-uses-contract",
                    title="Use server contract",
                    instruction="Consume the server contract result.",
                    agent=AgentSpec(agent_id="agent:client", runtime_provider="fake"),
                    context_scope=ContextScope(
                        context_id="context:client",
                        lane_id="lane:client",
                    ),
                    sandbox_profile=SandboxProfile(
                        profile_id="shared-client",
                        profile_kind="shared-process",
                    ),
                    acceptance=("client result artifact is produced",),
                    output_artifact_id="client-uses-contract:result",
                    dependencies=(
                        TaskDependency(
                            dependency_id="dep-server-client",
                            source_task_id="server-contract",
                            target_task_id="client-uses-contract",
                            dependency_kind="depends_on",
                            required_state="complete",
                        ),
                    ),
                ),
            ),
            title="Projection smoke batch",
        ),
        artifact_id="scheduler-task-batch-submission:projection-smoke",
        created_at="2026-06-17T01:29:00+08:00",
        version="v1",
    )
    submit_scheduler_task_batch_with_persistence(
        SchedulerState(),
        batch_artifact,
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-17T01:29:30+08:00",
    )

    run = run_persisted_scheduler_once(
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        sandbox_registry=sandbox_registry,
        runtime_registry=runtime_registry,
        policy=SchedulerRunPolicy(max_runs=2),
        workspace_root=str(tmp_path),
        timestamp="2026-06-17T01:30:00+08:00",
    )
    trajectory = build_scheduler_work_trajectory(
        run.drain.state,
        recorded_at="2026-06-17T01:31:00+08:00",
        guide_context="design_docs/stages/planning-gate/2026-06-16-agent-runtime-adapter-and-scheduler-skeleton.md",
    )

    assert run.state_written is True
    assert run.drain.stop_reason == "no_ready_tasks"
    assert trajectory.metadata["projection"] == "scheduler-state"
    assert trajectory.metadata["authority"] == "scheduler"
    assert trajectory.metadata["trajectory_role"] == "read-only-view"
    assert trajectory.metadata["task_count"] == "2"
    assert trajectory.metadata["dependency_count"] == "1"
    assert trajectory.metadata["run_record_count"] == "2"
    assert trajectory.lanes["lane:server"].status == "done"
    assert trajectory.lanes["lane:client"].status == "done"

    server_event = trajectory.events["scheduler-task:server-contract"]
    client_event = trajectory.events["scheduler-task:client-uses-contract"]
    assert server_event.status == "completed"
    assert client_event.status == "completed"
    assert server_event.metadata["run_record_run_ids"] == "fake-run-1"
    assert client_event.metadata["run_record_run_ids"] == "fake-run-2"
    assert server_event.metadata["output_artifact_id"] == "server-contract:result"
    assert server_event.metadata["output_artifact_version"] == "v1"
    assert client_event.metadata["output_artifact_id"] == "client-uses-contract:result"
    assert client_event.metadata["output_artifact_version"] == "v1"

    depends = [
        relation for relation in trajectory.relations
        if relation.kind == "depends_on"
    ]
    assert [(relation.source_event_id, relation.target_event_id) for relation in depends] == [
        ("scheduler-task:server-contract", "scheduler-task:client-uses-contract"),
    ]
    assert depends[0].metadata["scheduler_dependency_id"] == "dep-server-client"
    assert trajectory.check_invariants() == []


def test_build_scheduler_work_trajectory_can_include_scheduler_event_log_clues() -> None:
    state = SchedulerState(
        tasks={
            "api/task": _scheduler_projection_task(
                "api/task",
                lane_id="lane:server",
                state="complete",
                run_id="run-api-1",
            ),
        },
    )
    events = (
        SchedulerEvent(
            event_id="scheduler-event-2",
            event_kind="task_completed",
            timestamp="2026-06-17T01:40:02+08:00",
            task_id="api/task",
            from_state="running",
            to_state="complete",
            run_id="run-api-1",
            session_id="session-api-1",
            output_artifact_id="api-result",
            output_artifact_version="v1",
            sequence=2,
        ),
        SchedulerEvent(
            event_id="scheduler-event-1",
            event_kind="task_running",
            timestamp="2026-06-17T01:40:01+08:00",
            task_id="api/task",
            from_state="ready",
            to_state="running",
            run_id="run-api-1",
            session_id="session-api-1",
            sequence=1,
        ),
        SchedulerEvent(
            event_id="scheduler-event-orphan",
            event_kind="task_completed",
            timestamp="2026-06-17T01:40:03+08:00",
            task_id="unknown-task",
            sequence=3,
        ),
    )

    trajectory = build_scheduler_work_trajectory(state, scheduler_events=events)

    assert set(trajectory.events) == {"scheduler-task:api-task"}
    event = trajectory.events["scheduler-task:api-task"]
    assert event.metadata["scheduler_event_ids"] == "scheduler-event-1\nscheduler-event-2"
    assert event.metadata["scheduler_event_kinds"] == "task_running\ntask_completed"
    assert event.metadata["scheduler_event_timestamps"] == (
        "2026-06-17T01:40:01+08:00\n2026-06-17T01:40:02+08:00"
    )
    assert event.metadata["scheduler_event_sequences"] == "1\n2"
    assert trajectory.check_invariants() == []


def test_build_scheduler_work_trajectory_from_history_reads_jsonl_logs(tmp_path: Path) -> None:
    state = SchedulerState(
        tasks={
            "api/task": _scheduler_projection_task(
                "api/task",
                lane_id="lane:server",
                state="complete",
                run_id="run-api-1",
            ),
            "client-integration": _scheduler_projection_task(
                "client-integration",
                lane_id="lane:client",
                state="waiting",
            ),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-api-client",
                source_task_id="api/task",
                target_task_id="client-integration",
            ),
        ),
        merge_gates=(
            SchedulerMergeGate(
                gate_id="merge-client-inputs",
                title="Review client integration inputs",
                target_task_id="client-integration",
                source_task_ids=("api/task",),
                dependency_ids=("dep-api-client",),
                gate_kind="review",
                state="complete",
                required_review=True,
            ),
        ),
    )
    scheduler_event_log_path = tmp_path / "scheduler-events.jsonl"
    merge_gate_event_log_path = tmp_path / "merge-gate-events.jsonl"
    scheduler_event_log = JsonlSchedulerEventLog(scheduler_event_log_path)
    merge_gate_event_log = JsonlSchedulerMergeGateEventLog(merge_gate_event_log_path)

    scheduler_event_log.append(
        SchedulerEvent(
            event_id="scheduler-event-1",
            event_kind="task_completed",
            timestamp="2026-06-17T01:40:02+08:00",
            task_id="api/task",
            from_state="running",
            to_state="complete",
            run_id="run-api-1",
            session_id="session-api-1",
            output_artifact_id="api-result",
            output_artifact_version="v1",
            sequence=1,
        )
    )
    merge_gate_event_log.append(
        SchedulerMergeGateEvent(
            event_id="merge-gate-event-1",
            event_kind="merge_gate_completed",
            timestamp="2026-06-17T02:16:00+08:00",
            gate_id="merge-client-inputs",
            target_task_id="client-integration",
            from_state="review_required",
            to_state="complete",
            reason="guide approved merge inputs",
            decision_artifact_id="merge-client-inputs:decision",
            decision_artifact_version="v2",
            sequence=1,
        )
    )

    trajectory = build_scheduler_work_trajectory_from_history(
        state,
        scheduler_event_log_path=scheduler_event_log_path,
        merge_gate_event_log_path=merge_gate_event_log_path,
        recorded_at="2026-06-17T02:20:00+08:00",
    )

    assert trajectory.metadata["scheduler_event_log_path"] == str(scheduler_event_log_path)
    assert trajectory.metadata["scheduler_event_log_count"] == "1"
    assert trajectory.metadata["scheduler_merge_gate_event_log_path"] == str(merge_gate_event_log_path)
    assert trajectory.metadata["scheduler_merge_gate_event_log_count"] == "1"
    task_event = trajectory.events["scheduler-task:api-task"]
    assert task_event.metadata["scheduler_event_ids"] == "scheduler-event-1"
    assert task_event.metadata["scheduler_event_timestamps"] == "2026-06-17T01:40:02+08:00"
    gate_event = trajectory.events[
        "scheduler-task:client-integration:merge-gate:merge-client-inputs"
    ]
    assert gate_event.metadata["scheduler_merge_gate_event_log"] == (
        "timestamp=2026-06-17T02:16:00+08:00 | "
        "kind=merge_gate_completed | id=merge-gate-event-1 | sequence=1 | "
        "state=review_required->complete | reason=guide approved merge inputs | "
        "decision_artifact=merge-client-inputs:decision@v2"
    )
    assert trajectory.check_invariants() == []


def test_scheduler_work_trajectory_projects_compact_history_timeline() -> None:
    state = SchedulerState(
        tasks={
            "api/task": _scheduler_projection_task(
                "api/task",
                lane_id="lane:server",
                state="complete",
                run_id="run-api-1",
            ),
        },
        merge_gates=(
            SchedulerMergeGate(
                gate_id="merge-client-inputs",
                title="Review client integration inputs",
                target_task_id="api/task",
                source_task_ids=("api/task",),
                gate_kind="review",
                state="complete",
                required_review=True,
            ),
        ),
    )

    trajectory = build_scheduler_work_trajectory(
        state,
        scheduler_events=(
            SchedulerEvent(
                event_id="scheduler-event-2",
                event_kind="task_completed",
                timestamp="2026-06-17T01:40:02+08:00",
                task_id="api/task",
                from_state="running",
                to_state="complete",
                run_id="run-api-1",
                session_id="session-api-1",
                output_artifact_id="api-result",
                output_artifact_version="v1",
                sequence=2,
            ),
            SchedulerEvent(
                event_id="scheduler-event-orphan",
                event_kind="task_blocked",
                timestamp="2026-06-17T01:40:03+08:00",
                task_id="unknown-task",
                from_state="ready",
                to_state="blocked",
                reason="runtime failed",
                sequence=4,
            ),
        ),
        merge_gate_events=(
            SchedulerMergeGateEvent(
                event_id="merge-gate-event-1",
                event_kind="merge_gate_completed",
                timestamp="2026-06-17T01:40:01+08:00",
                gate_id="merge-client-inputs",
                target_task_id="api/task",
                from_state="review_required",
                to_state="complete",
                reason="guide approved merge inputs",
                decision_artifact_id="merge-client-inputs:decision",
                decision_artifact_version="v2",
                related_task_ids=("api/task",),
                sequence=1,
            ),
        ),
    )

    assert trajectory.metadata["scheduler_history_timeline_count"] == "3"
    assert trajectory.metadata["scheduler_history_timeline_limit"] == "40"
    assert trajectory.metadata["scheduler_history_timeline_truncated"] == "false"
    assert trajectory.metadata["scheduler_history_timeline"] == "\n".join((
        "timestamp=2026-06-17T01:40:01+08:00 | kind=merge_gate_completed | "
        "id=merge-gate-event-1 | gate=merge-client-inputs | target=api/task | "
        "sequence=1 | state=review_required->complete | "
        "reason=guide approved merge inputs | decision_artifact=merge-client-inputs:decision@v2 | "
        "tasks=api/task",
        "timestamp=2026-06-17T01:40:02+08:00 | kind=task_completed | "
        "id=scheduler-event-2 | task=api/task | sequence=2 | "
        "state=running->complete | run=run-api-1 | session=session-api-1 | "
        "output_artifact=api-result@v1",
        "timestamp=2026-06-17T01:40:03+08:00 | kind=task_blocked | "
        "id=scheduler-event-orphan | task=unknown-task | sequence=4 | "
        "state=ready->blocked | reason=runtime failed",
    ))
    assert "scheduler-event-orphan" not in (
        trajectory.events["scheduler-task:api-task"].metadata.get("scheduler_event_ids", "")
    )
    assert trajectory.check_invariants() == []


def test_scheduler_work_trajectory_history_timeline_is_bounded() -> None:
    state = SchedulerState(
        tasks={
            "api/task": _scheduler_projection_task(
                "api/task",
                lane_id="lane:server",
                state="complete",
            ),
        },
    )
    scheduler_events = tuple(
        SchedulerEvent(
            event_id=f"scheduler-event-{index}",
            event_kind="task_running",
            timestamp=f"2026-06-17T01:40:{index:02d}+08:00",
            task_id="api/task",
            from_state="ready",
            to_state="running",
            sequence=index,
        )
        for index in range(1, 46)
    )

    trajectory = build_scheduler_work_trajectory(state, scheduler_events=scheduler_events)

    timeline = trajectory.metadata["scheduler_history_timeline"].splitlines()
    assert trajectory.metadata["scheduler_history_timeline_count"] == "45"
    assert trajectory.metadata["scheduler_history_timeline_limit"] == "40"
    assert trajectory.metadata["scheduler_history_timeline_truncated"] == "true"
    assert len(timeline) == 40
    assert timeline[0].startswith("timestamp=2026-06-17T01:40:01+08:00")
    assert timeline[-1].startswith("timestamp=2026-06-17T01:40:40+08:00")
    assert "scheduler-event-45" not in trajectory.metadata["scheduler_history_timeline"]
    assert trajectory.check_invariants() == []


def test_write_scheduler_work_trajectory_artifact_uses_separate_default_path(tmp_path: Path) -> None:
    state = SchedulerState(
        tasks={
            "api/task": _scheduler_projection_task(
                "api/task",
                lane_id="lane:server",
                state="complete",
            ),
        },
    )
    scheduler_event_log_path = tmp_path / "scheduler-events.jsonl"
    JsonlSchedulerEventLog(scheduler_event_log_path).append(
        SchedulerEvent(
            event_id="scheduler-event-1",
            event_kind="task_completed",
            timestamp="2026-06-17T01:40:02+08:00",
            task_id="api/task",
            from_state="running",
            to_state="complete",
            sequence=1,
        )
    )
    start_single_line_trajectory(
        tmp_path,
        first_event_title="agent owned work",
        lane_label="agent",
    )

    path = write_scheduler_work_trajectory_artifact(
        tmp_path,
        state,
        scheduler_event_log_path=scheduler_event_log_path,
    )

    assert path == scheduler_work_trajectory_json_path(tmp_path)
    assert path == tmp_path / ".codex/progress-graph/scheduler-work-trajectory.json"
    scheduler_projection = LocalWorkTrajectory.from_json(path.read_text(encoding="utf-8"))
    assert scheduler_projection.trajectory_id == "local-work:scheduler-projection"
    assert scheduler_projection.metadata["projection_artifact_path"] == str(path)
    assert scheduler_projection.metadata["scheduler_event_log_count"] == "1"
    assert scheduler_projection.events["scheduler-task:api-task"].metadata["scheduler_event_ids"] == (
        "scheduler-event-1"
    )

    local_trajectory = load_local_work_trajectory(tmp_path)
    assert local_trajectory.trajectory_id == "local-work:single-line-current"
    assert [event.title for event in local_trajectory.events.values()] == ["agent owned work"]


def test_write_scheduler_work_trajectory_artifact_accepts_explicit_output_path(tmp_path: Path) -> None:
    state = SchedulerState(
        tasks={
            "api/task": _scheduler_projection_task(
                "api/task",
                lane_id="lane:server",
                state="complete",
            ),
        },
    )
    output_path = tmp_path / "artifacts" / "custom-scheduler-trajectory.json"

    path = write_scheduler_work_trajectory_artifact(
        tmp_path,
        state,
        output_path=output_path,
        trajectory_id="local-work:custom-scheduler-projection",
        title="Custom Scheduler Projection",
        recorded_at="2026-06-17T03:00:00+08:00",
    )

    assert path == output_path
    loaded = LocalWorkTrajectory.from_json(path.read_text(encoding="utf-8"))
    assert loaded.trajectory_id == "local-work:custom-scheduler-projection"
    assert loaded.title == "Custom Scheduler Projection"
    assert loaded.recorded_at == "2026-06-17T03:00:00+08:00"
    assert loaded.metadata["projection_artifact_path"] == str(output_path)
    assert not scheduler_work_trajectory_json_path(tmp_path).exists()


def test_run_persisted_scheduler_once_and_refresh_projection_writes_scheduler_view(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    batch = SchedulerTaskBatchSubmission(
        batch_id="batch-run-project",
        tasks=(
            SchedulerTaskSubmission(
                task_id="task-a",
                title="Task A",
                instruction="Complete A.",
                agent=AgentSpec(agent_id="agent:a", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:a", lane_id="lane:a"),
                output_artifact_id="task-a:result",
            ),
            SchedulerTaskSubmission(
                task_id="task-b",
                title="Task B",
                instruction="Complete B after A.",
                agent=AgentSpec(agent_id="agent:b", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:b", lane_id="lane:b"),
                output_artifact_id="task-b:result",
                dependencies=(
                    TaskDependency(
                        dependency_id="dep-a-b",
                        source_task_id="task-a",
                        target_task_id="task-b",
                        required_state="complete",
                    ),
                ),
            ),
        ),
    )
    submit_scheduler_task_batch_with_persistence(
        SchedulerState(),
        scheduler_task_batch_submission_to_artifact(
            batch,
            artifact_id="submission:run-project-batch",
        ),
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-17T04:00:00+08:00",
    )
    start_single_line_trajectory(
        tmp_path,
        first_event_title="agent owned work",
        lane_label="agent",
    )
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    runtime_registry = AgentRuntimeAdapterRegistry()
    runtime_registry.register(
        FakeAgentRuntimeAdapter(
            artifact_store=InMemoryArtifactVersionStore(),
            timestamp="2026-06-17T04:01:00+08:00",
        )
    )

    result = run_persisted_scheduler_once_and_refresh_projection(
        tmp_path,
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        sandbox_registry=sandbox_registry,
        runtime_registry=runtime_registry,
        timestamp="2026-06-17T04:01:00+08:00",
        guide_context="run-once-projection-test",
    )

    assert result.run.state_written is True
    assert result.run.drain.stop_reason == "no_ready_tasks"
    assert result.projection_path == scheduler_work_trajectory_json_path(tmp_path)
    assert result.projection.metadata["projection_artifact_path"] == str(result.projection_path)
    assert result.projection.metadata["scheduler_event_log_count"] == "9"
    assert result.projection.metadata["scheduler_history_timeline_count"] == "9"
    assert "kind=task_submitted" in result.projection.metadata["scheduler_history_timeline"]
    assert "kind=task_completed" in result.projection.metadata["scheduler_history_timeline"]
    assert result.projection.events["scheduler-task:task-a"].status == "completed"
    assert result.projection.events["scheduler-task:task-b"].status == "completed"
    assert result.projection.events["scheduler-task:task-a"].metadata["run_record_run_ids"] == "fake-run-1"
    assert result.projection.events["scheduler-task:task-b"].metadata["output_artifact_id"] == "task-b:result"

    local_trajectory = load_local_work_trajectory(tmp_path)
    assert [event.title for event in local_trajectory.events.values()] == ["agent owned work"]


def test_host_authorized_scheduler_run_and_refresh_projection_preserves_agent_trajectory(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduler_projection_task(
                    "task-a",
                    lane_id="lane:host",
                    output_artifact_id="task-a:result",
                ),
            },
        ),
        snapshot_path,
    )
    start_single_line_trajectory(
        tmp_path,
        first_event_title="agent-owned anchor",
        lane_label="agent",
    )

    result = run_host_authorized_scheduler_once_and_refresh_projection(
        tmp_path,
        HostSchedulerRunRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("fake",),
                timestamp="2026-06-17T19:20:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-fake-projection",
                    requested_providers=("fake",),
                    requested_by="host:test",
                ),
            ),
            timestamp="2026-06-17T19:20:00+08:00",
        ),
        artifact_store=InMemoryArtifactVersionStore(),
        guide_context="host-authorized-projection-test",
    )
    payload = result.host_run.to_json_dict()

    assert result.host_run.run.state_written is True
    assert payload["scheduler_projection_path"] == str(scheduler_work_trajectory_json_path(tmp_path))
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert result.projection.metadata["scheduler_event_log_count"] == "3"
    assert result.projection.events["scheduler-task:task-a"].status == "completed"
    assert result.projection.events["scheduler-task:task-a"].metadata["output_artifact_id"] == "task-a:result"

    local_trajectory = load_local_work_trajectory(tmp_path)
    assert [event.title for event in local_trajectory.events.values()] == ["agent-owned anchor"]


def test_host_scheduler_daemon_loop_and_refresh_projection_preserves_agent_trajectory(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduler_projection_task(
                    "task-a",
                    lane_id="lane:host",
                    output_artifact_id="task-a:result",
                ),
                "task-b": _scheduler_projection_task(
                    "task-b",
                    lane_id="lane:host",
                    output_artifact_id="task-b:result",
                ),
            },
            dependencies=(
                TaskDependency(
                    dependency_id="dep-a-b",
                    source_task_id="task-a",
                    target_task_id="task-b",
                    required_state="complete",
                ),
            ),
        ),
        snapshot_path,
    )
    start_single_line_trajectory(
        tmp_path,
        first_event_title="agent-owned anchor",
        lane_label="agent",
    )

    result = run_host_authorized_scheduler_daemon_loop_and_refresh_projection(
        tmp_path,
        HostSchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=3, max_runs_per_tick=1),
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("fake",),
                timestamp="2026-06-19T16:00:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-loop-projection-fake",
                    requested_providers=("fake",),
                    requested_by="host:test",
                ),
            ),
            timestamp="2026-06-19T16:00:00+08:00",
        ),
        artifact_store=InMemoryArtifactVersionStore(),
        guide_context="host-loop-projection-test",
    )
    payload = result.to_json_dict()

    assert result.host_loop.loop.total_run_count == 2
    assert result.host_loop.scheduler_projection_refreshed is True
    assert result.projection_path == scheduler_work_trajectory_json_path(tmp_path)
    assert payload["scheduler_projection_path"] == str(result.projection_path)
    assert payload["refreshed_projection"] is True
    assert payload["authority_split"]["scheduler_projection_refreshed"] is True
    assert payload["authority_split"]["scheduler_projection_role"] == "read-only-view"
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert payload["projection_summary"]["event_count"] == 2
    assert result.projection.metadata["scheduler_event_log_count"] == "7"
    assert result.projection.events["scheduler-task:task-a"].status == "completed"
    assert result.projection.events["scheduler-task:task-b"].status == "completed"
    assert result.projection.events["scheduler-task:task-a"].metadata["output_artifact_id"] == "task-a:result"

    local_trajectory = load_local_work_trajectory(tmp_path)
    assert [event.title for event in local_trajectory.events.values()] == ["agent-owned anchor"]


def test_host_scheduler_daemon_loop_projection_enriches_evidence_metadata(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / ".codex/scheduler/evidence/host-loop-fake.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduler_projection_task(
                    "task-a",
                    lane_id="lane:host",
                    output_artifact_id="task-a:result",
                ),
            },
        ),
        snapshot_path,
    )

    result = run_host_authorized_scheduler_daemon_loop_and_refresh_projection(
        tmp_path,
        HostSchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("fake",),
                timestamp="2026-06-19T17:10:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-loop-projection-fake-evidence",
                    requested_providers=("fake",),
                    requested_by="host:test",
                ),
            ),
            evidence_id="host-loop:projection-fake",
            evidence_path=evidence_path,
            timestamp="2026-06-19T17:10:00+08:00",
            metadata={"scenario": "fake-host-loop-projection"},
        ),
        artifact_store=InMemoryArtifactVersionStore(),
        guide_context="host-loop-projection-fake-evidence-test",
    )
    bundle = read_host_evidence_bundle(tmp_path)
    presentation = build_host_evidence_presentation(bundle).to_json_dict()
    summary = bundle.summaries[0]
    metadata = dict(summary.metadata)
    card = presentation["cards"][0]

    assert result.host_loop.evidence_write is not None
    assert result.host_loop.evidence_write.evidence_path == evidence_path
    assert metadata["surface"] == "host-loop-projection-workflow"
    assert metadata["workflow_surface"] == "host-loop-projection-workflow"
    assert metadata["runtime_host_surface"] == "host-authorized-adapter"
    assert metadata["host_invocation_id"] == "host-loop-projection-fake-evidence"
    assert metadata["scheduler_projection_path"] == str(result.projection_path)
    assert metadata["scheduler_projection_role"] == "read-only-view"
    assert metadata["scheduler_projection_refreshed"] is True
    assert metadata["scheduler_projection_summary"]["event_count"] == 1
    assert metadata["scheduler_projection_summary"]["relation_count"] == 0
    assert metadata["scenario"] == "fake-host-loop-projection"
    assert summary.authority_split["scheduler_projection_refreshed"] is False
    assert card["metadata"]["scheduler_projection_path"] == str(result.projection_path)
    assert card["metadata"]["scheduler_projection_refreshed"] == "true"
    assert {
        "label": "Scheduler projection refreshed",
        "value": "true",
    } in card["authority_clues"]
    assert any(ref["label"] == "Scheduler projection" for ref in card["refs"])

    payload = result.to_json_dict()
    assert payload["projection_summary"]["event_count"] == 1
    assert payload["evidence_written"] is True
    assert payload["evidence_path"] == str(evidence_path)


def test_host_scheduler_daemon_loop_projection_mock_qoder_preserves_evidence(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / ".codex/scheduler/evidence/host-loop-qoder.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-q": _scheduler_projection_task(
                    "task-q",
                    lane_id="lane:qoder",
                    agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
                    output_artifact_id="task-q:result",
                ),
            },
        ),
        snapshot_path,
    )

    result = run_host_authorized_scheduler_daemon_loop_and_refresh_projection(
        tmp_path,
        HostSchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("qoder",),
                timestamp="2026-06-19T16:05:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-loop-projection-qoder",
                    requested_providers=("qoder",),
                    requested_by="host:test",
                ),
                qoder_permission_grant=RuntimeProviderPermissionGrant(
                    grant_id="grant-qoder-projection",
                    provider="qoder",
                    approved_by="host:test",
                    approved_at="2026-06-19T16:04:00+08:00",
                    allow_sdk_client=True,
                ),
            ),
            evidence_id="host-loop:projection-qoder",
            evidence_path=evidence_path,
            timestamp="2026-06-19T16:05:00+08:00",
            metadata={"scenario": "mock-qoder-host-loop-projection"},
        ),
        qoder_query_client=_RecordingQoderClient(
            QoderQueryResult(summary="Qoder daemon projection completed.", output_text="done")
        ),
        guide_context="host-loop-projection-qoder-test",
    )
    payload = result.to_json_dict()
    bundle = read_host_evidence_bundle(tmp_path)

    assert payload["runtime_registry_providers"] == ["qoder"]
    assert payload["runtime_provider"] == "qoder"
    assert payload["scheduler_projection_path"] == str(scheduler_work_trajectory_json_path(tmp_path))
    assert payload["evidence_written"] is True
    assert payload["evidence_path"] == str(evidence_path)
    assert payload["authority_split"]["evidence_written"] is True
    assert payload["authority_split"]["scheduler_projection_refreshed"] is True
    assert result.projection.events["scheduler-task:task-q"].status == "completed"
    assert result.projection.events["scheduler-task:task-q"].metadata["runtime_provider"] == "qoder"
    assert len(bundle.errors) == 0
    assert len(bundle.summaries) == 1
    assert bundle.summaries[0].evidence_id == "host-loop:projection-qoder"
    assert bundle.summaries[0].product_type == "scheduler_loop_evidence"
    assert bundle.summaries[0].metadata["surface"] == "host-loop-projection-workflow"
    assert bundle.summaries[0].metadata["workflow_surface"] == "host-loop-projection-workflow"
    assert bundle.summaries[0].metadata["scheduler_projection_path"] == str(result.projection_path)
    assert bundle.summaries[0].metadata["scheduler_projection_refreshed"] is True
    assert bundle.summaries[0].metadata["scheduler_projection_summary"]["event_count"] == 1


def test_host_runtime_dogfood_harness_fake_writes_evidence_and_projection(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / ".codex/scheduler/evidence/fake-run.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduler_projection_task(
                    "task-a",
                    lane_id="lane:dogfood",
                    output_artifact_id="task-a:result",
                ),
            },
        ),
        snapshot_path,
    )
    start_single_line_trajectory(
        tmp_path,
        first_event_title="agent-owned anchor",
        lane_label="agent",
    )

    result = run_host_runtime_dogfood_harness(
        tmp_path,
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        runtime_config=RuntimeRegistryWiringConfig(
            providers=("fake",),
            timestamp="2026-06-17T20:10:00+08:00",
            host_invocation=RuntimeHostInvocation(
                surface="host-authorized-adapter",
                invocation_id="dogfood-fake",
                requested_providers=("fake",),
                requested_by="host:test",
                reason="fake dogfood evidence",
            ),
        ),
        evidence_id="dogfood-fake",
        evidence_output_path=evidence_path,
        timestamp="2026-06-17T20:10:00+08:00",
        artifact_store=InMemoryArtifactVersionStore(),
        guide_context="dogfood-harness-test",
    )
    payload = result.to_json_dict()

    assert result.run_projection.projection_path == scheduler_work_trajectory_json_path(tmp_path)
    assert result.evidence.evidence_path == evidence_path
    assert payload["product_type"] == "host_scheduler_run_evidence"
    assert payload["runtime_providers"] == ["fake"]
    assert payload["host_invocation"]["reason"] == "fake dogfood evidence"
    assert payload["run_count"] == 1
    assert payload["scheduler_projection_path"] == str(scheduler_work_trajectory_json_path(tmp_path))
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert result.run_projection.projection.events["scheduler-task:task-a"].status == "completed"
    assert evidence_path.exists()

    local_trajectory = load_local_work_trajectory(tmp_path)
    assert [event.title for event in local_trajectory.events.values()] == ["agent-owned anchor"]


def test_host_evidence_bundle_reads_compact_summaries(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / ".codex/scheduler/evidence/fake-run.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduler_projection_task(
                    "task-a",
                    lane_id="lane:dogfood",
                    output_artifact_id="task-a:result",
                ),
            },
        ),
        snapshot_path,
    )
    run_host_runtime_dogfood_harness(
        tmp_path,
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        runtime_config=RuntimeRegistryWiringConfig(
            providers=("fake",),
            timestamp="2026-06-18T00:20:00+08:00",
            host_invocation=RuntimeHostInvocation(
                surface="host-authorized-adapter",
                invocation_id="dogfood-fake-summary",
                requested_providers=("fake",),
                requested_by="host:test",
                reason="fake dogfood evidence summary",
            ),
        ),
        evidence_id="dogfood-fake-summary",
        evidence_output_path=evidence_path,
        timestamp="2026-06-18T00:20:00+08:00",
        artifact_store=InMemoryArtifactVersionStore(),
        guide_context="dogfood-harness-summary-test",
    )

    bundle = read_host_evidence_bundle(tmp_path)
    payload = bundle.to_json_dict()

    assert bundle.evidence_dir == host_scheduler_evidence_dir(tmp_path)
    assert payload["evidence_count"] == 1
    assert payload["summaries"][0]["evidence_id"] == "dogfood-fake-summary"
    assert payload["summaries"][0]["runtime_providers"] == ["fake"]
    assert payload["summaries"][0]["host_invocation"]["reason"] == "fake dogfood evidence summary"
    assert payload["summaries"][0]["output_artifact_refs"] == [
        {
            "task_id": "task-a",
            "artifact_id": "task-a:result",
            "version": "v1",
        }
    ]
    assert "host_result" not in payload["summaries"][0]


def test_host_evidence_bundle_reads_scheduler_loop_evidence_summary(tmp_path: Path) -> None:
    evidence_dir = tmp_path / ".codex/scheduler/evidence"
    evidence_path = evidence_dir / "loop-run.json"
    evidence_dir.mkdir(parents=True)
    evidence_path.write_text(
        """{
  "authority_split": {
    "local_work_trajectory_mutated": false,
    "provider_executed": true,
    "scheduler_projection_refreshed": false,
    "scheduler_state_authority": "scheduler_snapshot_and_event_log",
    "scheduler_state_mutated": true
  },
  "event_log_path": "scheduler-events.jsonl",
  "evidence_id": "loop-run",
  "final_queue_summary": {
    "blocked_task_ids": [],
    "completed_task_ids": ["task-a"],
    "failed_task_ids": [],
    "ready_task_ids": []
  },
  "iterations": [
    {
      "queue_summary": {
        "blocked_task_ids": [],
        "completed_task_ids": ["task-a"],
        "failed_task_ids": [],
        "ready_task_ids": []
      },
      "run_count": 1,
      "scheduler_event_count": 4,
      "tick_index": 1,
      "tick_stop_reason": "no_ready_tasks"
    }
  ],
  "metadata": {"surface": "test"},
  "product_type": "scheduler_loop_evidence",
  "runtime_provider": "fake",
  "schema_version": "1",
  "scheduler_event_count": 4,
  "snapshot_path": "scheduler-state.json",
  "stop_detail": "no ready tasks remain",
  "stop_policy": {
    "cancelled": false,
    "max_runs_per_tick": 1,
    "max_runtime_failures": 1,
    "max_ticks": 2
  },
  "stop_reason": "no_ready_tasks",
  "tick_count": 1,
  "timestamp": "2026-06-19T12:00:00+08:00",
  "total_run_count": 1
}
""",
        encoding="utf-8",
    )

    bundle = read_host_evidence_bundle(tmp_path)
    payload = bundle.to_json_dict()

    assert payload["evidence_count"] == 1
    assert payload["summaries"][0]["product_type"] == "scheduler_loop_evidence"
    assert payload["summaries"][0]["evidence_id"] == "loop-run"
    assert payload["summaries"][0]["tick_count"] == 1
    assert payload["summaries"][0]["total_run_count"] == 1
    assert "loop_result" not in payload["summaries"][0]

    presentation = build_host_evidence_presentation(bundle)
    presentation_payload = presentation.to_json_dict()
    card = presentation_payload["cards"][0]

    assert presentation_payload["status"] == "ok"
    assert card["id"] == "loop-run"
    assert card["title"] == "Scheduler loop evidence loop-run"
    assert card["status"] == "completed"
    assert card["host_surface"] == "scheduler-daemon-loop"
    assert card["runtime_providers"] == ["fake"]
    assert card["run_count"] == 1
    assert {"label": "Ticks", "value": "1"} in card["key_facts"]
    assert {"label": "Provider executed", "value": "true"} in card["authority_clues"]
    assert card["metadata"]["evidence_product_type"] == "scheduler_loop_evidence"


def test_host_evidence_bundle_reads_sandbox_allocation_cleanup_evidence(
    tmp_path: Path,
) -> None:
    allocation = _git_worktree_allocation_fixture(
        cleanup_required=False,
        cleanup_state="completed",
        cleanup_returncode=0,
        branch_cleanup_returncode=0,
    )
    evidence_path = tmp_path / ".codex/scheduler/evidence/cleanup.json"
    write_sandbox_allocation_receipt_evidence(
        build_sandbox_allocation_receipt_evidence(
            (allocation,),
            evidence_id="allocation-cleanup",
            timestamp="2026-06-21T07:05:00+08:00",
            evidence_path=evidence_path,
            metadata={
                "surface": "cli:scheduler cleanup-receipts",
                "source_evidence_id": "allocation",
                "source_evidence_path": str(
                    tmp_path / ".codex/scheduler/evidence/allocation.json"
                ),
            },
            authority_split={
                "sandbox_provider_executed": True,
                "cleanup_executed": True,
                "evidence_written": True,
                "local_work_trajectory_mutated": False,
            },
        ),
        evidence_path,
    )

    bundle = read_host_evidence_bundle(tmp_path)
    payload = bundle.to_json_dict()
    presentation = build_host_evidence_presentation(bundle)
    presentation_payload = presentation.to_json_dict()
    card = presentation_payload["cards"][0]

    assert payload["evidence_count"] == 1
    assert payload["summaries"][0]["product_type"] == "sandbox_allocation_receipt_evidence"
    assert payload["summaries"][0]["evidence_id"] == "allocation-cleanup"
    assert payload["summaries"][0]["allocation_count"] == 1
    assert presentation_payload["status"] == "ok"
    assert card["id"] == "allocation-cleanup"
    assert card["title"] == "Sandbox cleanup evidence allocation-cleanup"
    assert card["status"] == "completed"
    assert card["host_surface"] == "cli:scheduler cleanup-receipts"
    assert card["runtime_providers"] == ["git-worktree"]
    assert card["stop_reason"] == "cleanup_settled"
    assert {"label": "Cleanup completed", "value": "1"} in card["key_facts"]
    assert {"label": "Cleanup executed", "value": "true"} in card["authority_clues"]
    assert card["metadata"]["evidence_product_type"] == "sandbox_allocation_receipt_evidence"
    assert card["metadata"]["cleanup_state_counts"] == {"completed": 1}
    assert card["metadata"]["cleanup_completed_allocation_ids"] == [
        "git-worktree:task-1:worktree"
    ]
    assert any(ref["label"] == "Source evidence" for ref in card["refs"])
    assert any(ref["label"] == "Worktree task-1" for ref in card["refs"])


def test_host_evidence_bundle_reads_supervisor_storage_binding_evidence(
    tmp_path: Path,
) -> None:
    workflow = run_scheduler_supervisor_dogfood_workflow(
        SchedulerSupervisorDogfoodWorkflowRequest(
            project_root=tmp_path,
            timestamp="2026-06-21T11:45:00+00:00",
            supervisor_id="supervisor:host-evidence",
            session_id="session:host-evidence",
            run_id="run:host-evidence",
            host_id="host:host-evidence",
            requested_by="agent:guide",
        )
    )
    binding = build_supervisor_dogfood_storage_binding(
        workflow,
        agent_id="agent:host-evidence",
        context_session_id="context-session:host-evidence",
    )
    evidence = build_supervisor_storage_binding_evidence(
        binding,
        evidence_id="supervisor-binding:host-evidence",
        timestamp="2026-06-21T11:45:01+00:00",
        metadata={"workflow_surface": "supervisor-dogfood-workflow"},
    )
    evidence_path = default_supervisor_storage_binding_evidence_path(
        tmp_path,
        evidence.evidence_id,
    )
    write_supervisor_storage_binding_evidence(evidence, evidence_path)

    bundle = read_host_evidence_bundle(tmp_path)
    payload = bundle.to_json_dict()
    presentation = build_host_evidence_presentation(bundle)
    presentation_payload = presentation.to_json_dict()
    card = presentation_payload["cards"][0]

    assert payload["evidence_count"] == 1
    assert payload["summaries"][0]["product_type"] == "supervisor_storage_binding_evidence"
    assert payload["summaries"][0]["evidence_id"] == "supervisor-binding:host-evidence"
    assert payload["summaries"][0]["agent_id"] == "agent:host-evidence"
    assert payload["summaries"][0]["context_session_id"] == "context-session:host-evidence"
    assert "binding" not in payload["summaries"][0]
    assert presentation_payload["status"] == "ok"
    assert card["id"] == "supervisor-binding:host-evidence"
    assert card["title"] == (
        "Supervisor storage binding evidence supervisor-binding:host-evidence"
    )
    assert card["status"] == "completed"
    assert card["host_surface"] == "supervisor-dogfood-workflow"
    assert card["stop_reason"] == "readback_available"
    assert card["run_count"] == 1
    assert card["output_count"] == 2
    assert {"label": "Agent", "value": "agent:host-evidence"} in card["key_facts"]
    assert {"label": "Scratch spaces", "value": "2"} in card["key_facts"]
    assert {
        "label": "Local trajectory mutated",
        "value": "false",
    } in card["authority_clues"]
    assert card["metadata"]["evidence_product_type"] == "supervisor_storage_binding_evidence"
    assert card["metadata"]["scheduler_task_ids"] == ["dogfood:prepare", "dogfood:verify"]
    assert any(ref["label"] == "Source snapshot" for ref in card["refs"])
    assert any(ref["ref_kind"] == "agent_home_registration" for ref in card["refs"])


def test_host_evidence_cleanup_evidence_failed_state_takes_precedence(
    tmp_path: Path,
) -> None:
    allocation = _git_worktree_allocation_fixture(
        cleanup_required=True,
        cleanup_state="failed",
        cleanup_returncode=1,
    )
    evidence_path = tmp_path / ".codex/scheduler/evidence/cleanup-failed.json"
    write_sandbox_allocation_receipt_evidence(
        build_sandbox_allocation_receipt_evidence(
            (allocation,),
            evidence_id="allocation-cleanup-failed",
            timestamp="2026-06-21T07:10:00+08:00",
            evidence_path=evidence_path,
            authority_split={
                "sandbox_provider_executed": True,
                "cleanup_executed": True,
                "evidence_written": True,
                "local_work_trajectory_mutated": False,
            },
        ),
        evidence_path,
    )

    presentation = build_host_evidence_presentation(read_host_evidence_bundle(tmp_path))
    card = presentation.to_json_dict()["cards"][0]

    assert card["status"] == "failed"
    assert card["stop_reason"] == "cleanup_failed"
    assert card["metadata"]["cleanup_failed_allocation_ids"] == [
        "git-worktree:task-1:worktree"
    ]
    assert card["metadata"]["cleanup_required_allocation_ids"] == []
    assert {"label": "Cleanup failed", "value": "1"} in card["key_facts"]


def test_host_evidence_bundle_missing_directory_is_empty(tmp_path: Path) -> None:
    bundle = read_host_evidence_bundle(tmp_path)

    assert bundle.evidence_dir == host_scheduler_evidence_dir(tmp_path)
    assert bundle.summaries == ()
    assert bundle.to_json_dict()["evidence_count"] == 0
    assert bundle.to_json_dict()["error_count"] == 0
    assert bundle.to_json_dict()["errors"] == []

    presentation = build_host_evidence_presentation(
        bundle,
        generated_at="2026-06-18T12:30:00+08:00",
    )
    payload = presentation.to_json_dict()

    assert payload["status"] == "empty"
    assert payload["card_count"] == 0
    assert payload["error_count"] == 0
    assert payload["cards"] == []
    assert payload["error_rows"] == []
    assert payload["empty_message"] == "No host scheduler run evidence has been recorded."


def test_host_evidence_bundle_isolates_malformed_artifacts(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_dir = tmp_path / ".codex/scheduler/evidence"
    valid_path = evidence_dir / "valid-run.json"
    malformed_path = evidence_dir / "malformed.json"
    wrong_product_path = evidence_dir / "wrong-product.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduler_projection_task(
                    "task-a",
                    lane_id="lane:dogfood",
                    output_artifact_id="task-a:result",
                ),
            },
        ),
        snapshot_path,
    )
    run_host_runtime_dogfood_harness(
        tmp_path,
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        runtime_config=RuntimeRegistryWiringConfig(
            providers=("fake",),
            timestamp="2026-06-18T01:40:00+08:00",
            host_invocation=RuntimeHostInvocation(
                surface="host-authorized-adapter",
                invocation_id="dogfood-valid-summary",
                requested_providers=("fake",),
                requested_by="host:test",
                reason="valid dogfood evidence summary",
            ),
        ),
        evidence_id="dogfood-valid-summary",
        evidence_output_path=valid_path,
        timestamp="2026-06-18T01:40:00+08:00",
        artifact_store=InMemoryArtifactVersionStore(),
        guide_context="dogfood-harness-error-isolation-test",
    )
    malformed_path.write_text("{not json", encoding="utf-8")
    wrong_product_path.write_text(
        '{"product_type": "wrong", "schema_version": "1"}',
        encoding="utf-8",
    )

    bundle = read_host_evidence_bundle(tmp_path)
    payload = bundle.to_json_dict()

    assert payload["evidence_count"] == 1
    assert payload["summaries"][0]["evidence_id"] == "dogfood-valid-summary"
    assert payload["error_count"] == 2
    assert {Path(error["evidence_path"]).name for error in payload["errors"]} == {
        "malformed.json",
        "wrong-product.json",
    }
    assert {error["error_kind"] for error in payload["errors"]} == {"invalid_evidence"}
    assert all("raw" not in error for error in payload["errors"])

    presentation = build_host_evidence_presentation(bundle)
    presentation_payload = presentation.to_json_dict()

    assert presentation_payload["status"] == "degraded"
    assert presentation_payload["card_count"] == 1
    assert presentation_payload["error_count"] == 2
    assert presentation_payload["cards"][0]["status"] == "completed"
    assert {Path(error["evidence_path"]).name for error in presentation_payload["error_rows"]} == {
        "malformed.json",
        "wrong-product.json",
    }
    assert {error["status"] for error in presentation_payload["error_rows"]} == {"read-error"}


def test_host_evidence_presentation_builds_completed_card_with_refs_and_authority(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / ".codex/scheduler/evidence/fake-run.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduler_projection_task(
                    "task-a",
                    lane_id="lane:dogfood",
                    output_artifact_id="task-a:result",
                ),
            },
        ),
        snapshot_path,
    )
    run_host_runtime_dogfood_harness(
        tmp_path,
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        runtime_config=RuntimeRegistryWiringConfig(
            providers=("fake",),
            timestamp="2026-06-18T02:20:00+08:00",
            host_invocation=RuntimeHostInvocation(
                surface="host-authorized-adapter",
                invocation_id="presentation-fake",
                requested_providers=("fake",),
                requested_by="host:test",
                reason="presentation contract smoke",
            ),
        ),
        evidence_id="presentation-fake",
        evidence_output_path=evidence_path,
        timestamp="2026-06-18T02:20:00+08:00",
        artifact_store=InMemoryArtifactVersionStore(),
        guide_context="host-evidence-presentation-test",
    )

    presentation = build_host_evidence_presentation(
        read_host_evidence_bundle(tmp_path),
        generated_at="2026-06-18T02:21:00+08:00",
    )
    payload = presentation.to_json_dict()
    card = payload["cards"][0]

    assert payload["generated_at"] == "2026-06-18T02:21:00+08:00"
    assert payload["status"] == "ok"
    assert payload["card_count"] == 1
    assert card["id"] == "presentation-fake"
    assert card["title"] == "Host evidence presentation-fake"
    assert card["status"] == "completed"
    assert card["severity"] == "info"
    assert card["runtime_providers"] == ["fake"]
    assert card["host_surface"] == "host-authorized-adapter"
    assert card["invocation_id"] == "presentation-fake"
    assert card["requested_by"] == "host:test"
    assert card["stop_reason"] == "no_ready_tasks"
    assert card["run_count"] == 1
    assert card["output_count"] == 1
    assert {"label": "Outputs", "value": "1"} in card["key_facts"]
    assert any(ref["ref_kind"] == "exchange_artifact" for ref in card["refs"])
    assert {"label": "Local trajectory mutated", "value": "false"} in card["authority_clues"]
    assert card["metadata"]["reason"] == "presentation contract smoke"
    assert "host_result" not in card


def test_scheduler_loop_evidence_presentation_surfaces_host_projection_clues(tmp_path: Path) -> None:
    summary = SchedulerLoopEvidenceSummary(
        evidence_path=tmp_path / ".codex/scheduler/evidence/loop.json",
        evidence_id="loop-host-projection",
        timestamp="2026-06-19T16:40:00+08:00",
        product_type="scheduler_loop_evidence",
        snapshot_path=".codex/scheduler/scheduler-state.json",
        event_log_path=".codex/scheduler/scheduler-events.jsonl",
        runtime_provider="qoder",
        stop_policy={"max_ticks": 2, "max_runs_per_tick": 1},
        tick_count=1,
        total_run_count=1,
        stop_reason="no_ready_tasks",
        stop_detail="no ready tasks remain",
        scheduler_event_count=4,
        iterations=(
            {
                "tick_index": 1,
                "run_count": 1,
                "tick_stop_reason": "no_ready_tasks",
            },
        ),
        final_queue_summary={
            "completed_task_ids": ["task-q"],
            "ready_task_ids": [],
            "blocked_task_ids": [],
            "failed_task_ids": [],
        },
        authority_split={
            "scheduler_state_authority": "scheduler_snapshot_and_event_log",
            "scheduler_state_mutated": True,
            "provider_executed": True,
            "scheduler_projection_refreshed": True,
            "scheduler_projection_role": "read-only-view",
            "scheduler_projection_path": ".codex/progress-graph/scheduler-work-trajectory.json",
            "local_work_trajectory_mutated": False,
        },
        metadata={
            "surface": "host-authorized-scheduler-daemon-loop",
            "runtime_host_surface": "host-authorized-adapter",
            "host_invocation_id": "host-loop-projection-qoder",
            "scheduler_projection_path": ".codex/progress-graph/scheduler-work-trajectory.json",
        },
    )

    payload = build_host_evidence_presentation(
        HostEvidenceBundle(
            project_root=tmp_path,
            evidence_dir=tmp_path / ".codex/scheduler/evidence",
            summaries=(summary,),
        )
    ).to_json_dict()
    card = payload["cards"][0]

    assert payload["status"] == "ok"
    assert card["runtime_providers"] == ["qoder"]
    assert card["host_surface"] == "host-authorized-adapter"
    assert card["invocation_id"] == "host-loop-projection-qoder"
    assert card["run_count"] == 1
    assert {"label": "Runtime provider", "value": "qoder"} in card["key_facts"]
    assert {"label": "Host surface", "value": "host-authorized-adapter"} in card["key_facts"]
    assert {"label": "Host invocation", "value": "host-loop-projection-qoder"} in card["key_facts"]
    assert {
        "label": "Scheduler projection path",
        "value": ".codex/progress-graph/scheduler-work-trajectory.json",
    } in card["key_facts"]
    assert {
        "label": "Scheduler projection role",
        "value": "read-only-view",
    } in card["key_facts"]
    assert any(ref["label"] == "Scheduler projection" for ref in card["refs"])
    assert {
        "label": "Scheduler projection refreshed",
        "value": "true",
    } in card["authority_clues"]
    assert {
        "label": "Local trajectory mutated",
        "value": "false",
    } in card["authority_clues"]
    assert card["metadata"]["scheduler_projection_path"] == ".codex/progress-graph/scheduler-work-trajectory.json"


def test_scheduler_loop_evidence_presentation_keeps_legacy_metadata_compatible(tmp_path: Path) -> None:
    summary = SchedulerLoopEvidenceSummary(
        evidence_path=tmp_path / ".codex/scheduler/evidence/loop.json",
        evidence_id="loop-legacy",
        timestamp="2026-06-19T16:45:00+08:00",
        product_type="scheduler_loop_evidence",
        snapshot_path="state.json",
        event_log_path="events.jsonl",
        runtime_provider="fake",
        stop_policy={"max_ticks": 1},
        tick_count=1,
        total_run_count=0,
        stop_reason="no_ready_tasks",
        stop_detail="no ready tasks remain",
        scheduler_event_count=0,
        iterations=(
            {
                "tick_index": 1,
                "run_count": 0,
                "tick_stop_reason": "no_ready_tasks",
            },
        ),
        final_queue_summary={
            "completed_task_ids": [],
            "ready_task_ids": [],
            "blocked_task_ids": [],
            "failed_task_ids": [],
        },
        authority_split={
            "scheduler_state_authority": "scheduler_snapshot_and_event_log",
            "scheduler_projection_refreshed": False,
            "local_work_trajectory_mutated": False,
        },
        metadata={},
    )

    card = build_host_evidence_presentation(
        HostEvidenceBundle(
            project_root=tmp_path,
            evidence_dir=tmp_path / ".codex/scheduler/evidence",
            summaries=(summary,),
        )
    ).to_json_dict()["cards"][0]

    assert card["host_surface"] == "scheduler-daemon-loop"
    assert card["invocation_id"] == "loop-legacy"
    assert {"label": "Host invocation", "value": "loop-legacy"} in card["key_facts"]
    assert card["metadata"]["scheduler_projection_path"] == ""
    assert not any(ref["label"] == "Scheduler projection" for ref in card["refs"])


def test_host_evidence_presentation_derives_non_completed_statuses(tmp_path: Path) -> None:
    permission = _host_evidence_summary_fixture(
        tmp_path / "permission.json",
        evidence_id="permission",
        stop_reason="no_ready_tasks",
        permission_review_count=1,
        permission_review_task_ids=("task-permission",),
    )
    failed = _host_evidence_summary_fixture(
        tmp_path / "failed.json",
        evidence_id="failed",
        stop_reason="task_failed",
        failed_task_ids=("task-failed",),
    )
    partial = _host_evidence_summary_fixture(
        tmp_path / "partial.json",
        evidence_id="partial",
        stop_reason="max_runs_reached",
        blocked_task_ids=("task-waiting",),
    )
    presentation = build_host_evidence_presentation(
        HostEvidenceBundle(
            project_root=tmp_path,
            evidence_dir=tmp_path / ".codex/scheduler/evidence",
            summaries=(permission, failed, partial),
        )
    )
    payload = presentation.to_json_dict()
    cards = {card["id"]: card for card in payload["cards"]}

    assert payload["status"] == "failed"
    assert cards["permission"]["status"] == "permission-review"
    assert cards["permission"]["severity"] == "warning"
    assert cards["permission"]["permission_review_count"] == 1
    assert cards["failed"]["status"] == "failed"
    assert cards["failed"]["severity"] == "error"
    assert cards["partial"]["status"] == "partial"
    assert cards["partial"]["severity"] == "warning"


def test_host_evidence_presentation_reports_error_only_bundle_as_degraded(tmp_path: Path) -> None:
    bundle = HostEvidenceBundle(
        project_root=tmp_path,
        evidence_dir=tmp_path / ".codex/scheduler/evidence",
        summaries=(),
        errors=(
            HostEvidenceReadError(
                evidence_path=tmp_path / ".codex/scheduler/evidence/bad.json",
                error_kind="invalid_evidence",
                message="bad evidence",
            ),
        ),
    )

    payload = build_host_evidence_presentation(bundle).to_json_dict()

    assert payload["status"] == "degraded"
    assert payload["card_count"] == 0
    assert payload["error_count"] == 1
    assert payload["empty_message"] == ""
    assert payload["error_rows"] == [
        {
            "id": "host-evidence-error:1",
            "status": "read-error",
            "severity": "error",
            "evidence_path": str(tmp_path / ".codex/scheduler/evidence/bad.json"),
            "error_kind": "invalid_evidence",
            "message": "bad evidence",
        }
    ]


def test_host_runtime_dogfood_harness_mock_qoder_writes_same_evidence_shape(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / ".codex/scheduler/evidence/qoder-run.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-q": _scheduler_projection_task(
                    "task-q",
                    lane_id="lane:qoder",
                    agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
                    output_artifact_id="task-q:result",
                ),
            },
        ),
        snapshot_path,
    )
    client = _RecordingQoderClient(
        QoderQueryResult(summary="mock qoder dogfood complete", output_text="done")
    )

    result = run_host_runtime_dogfood_harness(
        tmp_path,
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        runtime_config=RuntimeRegistryWiringConfig(
            providers=("qoder",),
            timestamp="2026-06-17T20:15:00+08:00",
            host_invocation=RuntimeHostInvocation(
                surface="host-authorized-adapter",
                invocation_id="dogfood-qoder",
                requested_providers=("qoder",),
                requested_by="host:test",
                reason="mock qoder dogfood evidence",
            ),
            qoder_permission_grant=RuntimeProviderPermissionGrant(
                grant_id="grant-qoder-dogfood",
                provider="qoder",
                approved_by="host:test",
                approved_at="2026-06-17T20:14:00+08:00",
                allow_sdk_client=True,
            ),
        ),
        evidence_id="dogfood-qoder",
        evidence_output_path=evidence_path,
        timestamp="2026-06-17T20:15:00+08:00",
        qoder_query_client=client,
    )
    payload = result.to_json_dict()

    assert len(client.requests) == 1
    assert client.requests[0].task.task_id == "task-q"
    assert payload["runtime_providers"] == ["qoder"]
    assert payload["host_invocation"]["surface"] == "host-authorized-adapter"
    assert payload["host_invocation"]["reason"] == "mock qoder dogfood evidence"
    assert payload["run_count"] == 1
    assert payload["output_artifact_refs"] == [
        {
            "task_id": "task-q",
            "artifact_id": "task-q:result",
            "version": "v1",
        }
    ]
    assert payload["authority_split"]["scheduler_state_authority"] == "scheduler_snapshot_and_event_log"
    assert result.run_projection.projection.events["scheduler-task:task-q"].status == "completed"


def test_host_runtime_dogfood_harness_mock_qoder_requires_host_grant(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-q": _scheduler_projection_task(
                    "task-q",
                    lane_id="lane:qoder",
                    agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
                ),
            },
        ),
        snapshot_path,
    )

    with pytest.raises(ValueError, match="RuntimeProviderPermissionGrant"):
        run_host_runtime_dogfood_harness(
            tmp_path,
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("qoder",),
                timestamp="2026-06-17T20:20:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="dogfood-qoder-missing-grant",
                    requested_providers=("qoder",),
                ),
            ),
            evidence_id="dogfood-qoder-missing-grant",
            qoder_query_client=_RecordingQoderClient(QoderQueryResult(summary="unused")),
        )


def test_host_runtime_dogfood_harness_real_qoder_wrapper_auth_failure_fails_closed(
    tmp_path: Path,
) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / ".codex/scheduler/evidence/qoder-auth-fail.json"
    projection_path = scheduler_work_trajectory_json_path(tmp_path)
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-q": _scheduler_projection_task(
                    "task-q",
                    lane_id="lane:qoder",
                    agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
                    output_artifact_id="task-q:result",
                ),
            },
        ),
        snapshot_path,
    )
    client = QoderSDKQueryClient(
        sdk_importer=lambda name: _NeverUsedQoderSDK(),
        environment={},
    )

    with pytest.raises(QoderRuntimeError) as raised:
        run_host_runtime_dogfood_harness(
            tmp_path,
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("qoder",),
                timestamp="2026-06-17T21:00:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="dogfood-qoder-auth-fail",
                    requested_providers=("qoder",),
                    requested_by="host:test",
                    reason="real qoder wrapper negative-path evidence",
                ),
                qoder_permission_grant=RuntimeProviderPermissionGrant(
                    grant_id="grant-qoder-auth-fail",
                    provider="qoder",
                    approved_by="host:test",
                    approved_at="2026-06-17T20:59:00+08:00",
                    allow_sdk_client=True,
                ),
            ),
            evidence_id="dogfood-qoder-auth-fail",
            evidence_output_path=evidence_path,
            timestamp="2026-06-17T21:00:00+08:00",
            qoder_query_client=client,
        )

    assert raised.value.error_kind == "authentication_failed"
    assert "QODER_PERSONAL_ACCESS_TOKEN" in raised.value.summary
    assert evidence_path.exists() is False
    assert projection_path.exists() is False
    restored = read_scheduler_state_snapshot(snapshot_path)
    assert restored.tasks["task-q"].state == "proposed"
    assert restored.tasks["task-q"].run_id == ""


def test_host_owned_qoder_smoke_runner_initializes_snapshot_and_writes_evidence(
    tmp_path: Path,
) -> None:
    evidence_path = tmp_path / ".codex/scheduler/evidence/qoder-smoke.json"
    client = _RecordingQoderClient(
        QoderQueryResult(summary="qoder smoke complete", output_text="ok")
    )

    result = run_host_owned_qoder_smoke(
        tmp_path,
        config=HostOwnedQoderSmokeRunConfig(
            evidence_id="qoder-smoke",
            timestamp="2026-06-17T23:50:00+08:00",
            evidence_output_path=evidence_path,
            reset_snapshot=True,
            task=QoderSmokeTaskConfig(
                task_id="task-qoder-smoke",
                instruction="Return ok for the smoke test.",
                output_artifact_id="task-qoder-smoke:result",
            ),
            host_invocation_id="qoder-smoke-test",
            requested_by="host:test",
            reason="repeatable qoder smoke helper test",
            grant_id="grant-qoder-smoke-test",
            approved_by="host:test",
        ),
        qoder_query_client=client,
    )
    payload = result.to_json_dict()

    assert result.initialized_snapshot is True
    assert result.snapshot_path == tmp_path / ".codex/scheduler/qoder-smoke-state.json"
    assert result.event_log_path == tmp_path / ".codex/scheduler/qoder-smoke-events.jsonl"
    assert len(client.requests) == 1
    assert client.requests[0].task.task_id == "task-qoder-smoke"
    assert client.requests[0].acceptance[-1] == "Do not include secrets or raw credential material in output."
    assert payload["runtime_providers"] == ["qoder"]
    assert payload["host_invocation"]["invocation_id"] == "qoder-smoke-test"
    assert payload["host_invocation"]["reason"] == "repeatable qoder smoke helper test"
    assert payload["run_count"] == 1
    assert payload["output_artifact_refs"] == [
        {
            "task_id": "task-qoder-smoke",
            "artifact_id": "task-qoder-smoke:result",
            "version": "v1",
        }
    ]
    assert payload["metadata"]["runner"] == "host-owned-qoder-smoke"
    assert evidence_path.exists()
    assert result.harness.run_projection.projection.events[
        "scheduler-task:task-qoder-smoke"
    ].status == "completed"


def test_host_owned_qoder_smoke_runner_auth_failure_fails_before_state_pollution(
    tmp_path: Path,
) -> None:
    evidence_path = tmp_path / ".codex/scheduler/evidence/qoder-smoke-auth-fail.json"
    projection_path = scheduler_work_trajectory_json_path(tmp_path)

    with pytest.raises(QoderRuntimeError) as raised:
        run_host_owned_qoder_smoke(
            tmp_path,
            config=HostOwnedQoderSmokeRunConfig(
                evidence_id="qoder-smoke-auth-fail",
                timestamp="2026-06-17T23:55:00+08:00",
                evidence_output_path=evidence_path,
                reset_snapshot=True,
                task=QoderSmokeTaskConfig(task_id="task-qoder-smoke-auth-fail"),
            ),
            sdk_importer=lambda name: _NeverUsedQoderSDK(),
            environment={},
        )

    assert raised.value.error_kind == "authentication_failed"
    assert evidence_path.exists() is False
    assert projection_path.exists() is False
    restored = read_scheduler_state_snapshot(
        tmp_path / ".codex/scheduler/qoder-smoke-state.json"
    )
    assert restored.tasks["task-qoder-smoke-auth-fail"].state == "proposed"
    assert restored.tasks["task-qoder-smoke-auth-fail"].run_id == ""


def test_host_owned_guide_worker_provider_execution_runs_mock_qoder_wave(
    tmp_path: Path,
) -> None:
    evidence_path = tmp_path / ".codex/scheduler/evidence/guide-worker-provider.json"
    client = _RecordingQoderClient(
        QoderQueryResult(summary="guide-worker qoder complete", output_text="ok")
    )

    result = run_host_owned_guide_worker_provider_execution(
        tmp_path,
        config=HostOwnedGuideWorkerProviderExecutionConfig(
            evidence_id="guide-worker-provider",
            timestamp="2026-06-24T08:30:00+08:00",
            evidence_output_path=evidence_path,
            host_invocation_id="guide-worker-provider-test",
            requested_by="host:test",
            reason="mock qoder guide-worker provider execution test",
            grant_id="grant-guide-worker-provider-test",
            approved_by="host:test",
        ),
        qoder_query_client=client,
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["workflow_surface"] == "host-owned-guide-worker-provider-execution"
    assert payload["runtime_providers"] == ["qoder"]
    assert payload["worker_runtime_providers"] == ["qoder"]
    assert payload["host_invocation"]["invocation_id"] == "guide-worker-provider-test"
    assert payload["submitted_task_ids"] == [
        "task/guide-worker-provider/client",
        "task/guide-worker-provider/server",
    ]
    assert payload["lane_ids"] == ["lane:client", "lane:server"]
    assert payload["wave_execution_results"][0]["mode"] == "threaded"
    assert payload["wave_execution_results"][0]["completed_task_ids"] == [
        "task/guide-worker-provider/client",
        "task/guide-worker-provider/server",
    ]
    assert payload["authority_split"]["runtime_registry_authority"] == "host_runtime_wiring"
    assert payload["authority_split"]["mcp_live_provider_surface"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert payload["metadata"]["runner"] == "host-owned-guide-worker-provider-execution"
    assert len(client.requests) == 2
    assert {request.agent.runtime_provider for request in client.requests} == {"qoder"}
    assert evidence_path.exists()
    state = read_scheduler_state_snapshot(
        tmp_path / ".codex/scheduler/guide-worker-provider-execution-state.json"
    )
    assert state.tasks["task/guide-worker-provider/client"].agent.runtime_provider == "qoder"
    assert state.tasks["task/guide-worker-provider/server"].agent.runtime_provider == "qoder"
    assert not (tmp_path / ".codex/progress-graph/local-work-trajectory.json").exists()


def test_host_owned_guide_worker_provider_execution_auth_failure_writes_no_state(
    tmp_path: Path,
) -> None:
    evidence_path = tmp_path / ".codex/scheduler/evidence/guide-worker-auth-fail.json"

    with pytest.raises(QoderRuntimeError) as raised:
        run_host_owned_guide_worker_provider_execution(
            tmp_path,
            config=HostOwnedGuideWorkerProviderExecutionConfig(
                evidence_id="guide-worker-auth-fail",
                timestamp="2026-06-24T08:35:00+08:00",
                evidence_output_path=evidence_path,
            ),
            sdk_importer=lambda name: _NeverUsedQoderSDK(),
            environment={},
        )

    assert raised.value.error_kind == "authentication_failed"
    assert evidence_path.exists() is False
    assert (
        tmp_path / ".codex/scheduler/guide-worker-provider-execution-state.json"
    ).exists() is False
    assert (
        tmp_path / ".codex/orchestration/exchange-artifacts.json"
    ).exists() is False
    assert not (tmp_path / ".codex/progress-graph/local-work-trajectory.json").exists()


def test_host_owned_guide_worker_provider_execution_mixed_fake_and_qoder_workers(
    tmp_path: Path,
) -> None:
    client = _RecordingQoderClient(
        QoderQueryResult(summary="mixed qoder worker complete", output_text="ok")
    )

    result = run_host_owned_guide_worker_provider_execution(
        tmp_path,
        config=HostOwnedGuideWorkerProviderExecutionConfig(
            evidence_id="guide-worker-mixed-provider",
            timestamp="2026-06-24T08:45:00+08:00",
            providers=("fake", "qoder"),
            worker_instructions=(
                GuideWorkerInstruction(
                    task_id="task/mixed/fake",
                    title="Fake worker lane",
                    instruction="Complete this fake worker task.",
                    lane_id="lane:fake",
                    worker_runtime_provider="fake",
                    output_artifact_id="task/mixed/fake:result",
                ),
                GuideWorkerInstruction(
                    task_id="task/mixed/qoder",
                    title="Qoder worker lane",
                    instruction="Complete this qoder worker task.",
                    lane_id="lane:qoder",
                    worker_runtime_provider="qoder",
                    output_artifact_id="task/mixed/qoder:result",
                ),
            ),
        ),
        qoder_query_client=client,
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["runtime_providers"] == ["fake", "qoder"]
    assert payload["worker_runtime_providers"] == ["fake", "qoder"]
    assert payload["orchestration"]["scenario"]["runtime_provider"] == "mixed"
    assert payload["task_states"]["task/mixed/fake"] == "complete"
    assert payload["task_states"]["task/mixed/qoder"] == "complete"
    assert len(client.requests) == 1


def test_host_owned_guide_worker_provider_execution_audits_and_retries_qoder_invocation(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / ".codex/runtime/provider-invocations.jsonl"
    client = _FlakyQoderClient()

    result = run_host_owned_guide_worker_provider_execution(
        tmp_path,
        config=HostOwnedGuideWorkerProviderExecutionConfig(
            evidence_id="guide-worker-runtime-audit",
            timestamp="2026-06-25T08:45:00+08:00",
            worker_instructions=(
                GuideWorkerInstruction(
                    task_id="task/runtime/audit",
                    title="Runtime audit worker",
                    instruction="Complete this qoder worker task.",
                    lane_id="lane:audit",
                    worker_runtime_provider="qoder",
                    output_artifact_id="task/runtime/audit:result",
                ),
            ),
            runtime_invocation_log_path=log_path,
            runtime_invocation_max_attempts=2,
            runtime_invocation_backoff_seconds=0,
        ),
        qoder_query_client=client,
    )
    records = JsonlRuntimeInvocationLog(log_path).read_all()
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["metadata"]["runtime_invocation_log_path"] == str(log_path)
    assert payload["metadata"]["runtime_invocation_max_attempts"] == 2
    assert payload["authority_split"]["runtime_invocation_audit_enabled"] is True
    assert len(client.requests) == 2
    assert len(records) == 1
    record = records[0]
    assert record.provider == "qoder"
    assert record.status == "succeeded"
    assert record.task_id == "task/runtime/audit"
    assert record.session_id == "qoder-session-1"
    assert record.agent_id == "agent:qoder-worker"
    assert record.runtime_surface == "host-owned-guide-worker-provider-execution"
    assert record.attempt_count == 2
    assert [attempt.status for attempt in record.attempts] == ["failed", "succeeded"]
    assert record.attempts[0].retryable is True
    assert "OPENAI_API_KEY=[redacted]" in record.attempts[0].summary
    assert "secret-token" not in record.attempts[0].summary
    assert record.metadata["lane_id"] == "lane:audit"
    assert record.to_json_dict()["authority_split"]["raw_transcript_persisted"] is False


def test_host_owned_guide_worker_provider_execution_runs_planned_qoder_workers(
    tmp_path: Path,
) -> None:
    client = _RecordingQoderClient(
        QoderQueryResult(summary="planned qoder worker complete", output_text="ok")
    )

    result = run_host_owned_guide_worker_provider_execution(
        tmp_path,
        config=HostOwnedGuideWorkerProviderExecutionConfig(
            evidence_id="guide-worker-planned-provider",
            timestamp="2026-06-24T18:30:00+08:00",
            worker_instructions=(),
            planning_request=GuideWorkerPlanningRequest(
                task_title="Build maze game",
                task_summary="Split browser client and server API work.",
                lane_specs=(
                    GuideWorkerPlannerLaneSpec(
                        lane_id="lane:client",
                        label="Client UI",
                        focus="browser maze controls and CLI-like test hooks",
                        allowed_artifacts=("client", "web"),
                    ),
                    GuideWorkerPlannerLaneSpec(
                        lane_id="lane:server",
                        label="Server API",
                        focus="state API and port boundary",
                        allowed_artifacts=("server", "api"),
                    ),
                ),
            ),
            planner_worker_runtime_provider="qoder",
        ),
        qoder_query_client=client,
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["planning"]["source"] == "planning_request"
    assert payload["planning"]["worker_count"] == 2
    assert payload["submitted_task_ids"] == [
        "task/guide-worker-provider-execution/client",
        "task/guide-worker-provider-execution/server",
    ]
    assert payload["worker_runtime_providers"] == ["qoder"]
    assert payload["planned_worker_instructions"][0]["worker_runtime_provider"] == "qoder"
    assert payload["worker_execution_receipts"] == [
        {
            "task_id": "task/guide-worker-provider-execution/client",
            "lane_id": "lane:client",
            "title": "Client UI",
            "worker_agent_id": "agent:qoder-worker",
            "runtime_provider": "qoder",
            "task_state": "complete",
            "run_id": "qoder-run-1",
            "session_id": "qoder-session-1",
            "output_artifact_id": "task/guide-worker-provider-execution/client:result",
            "output_artifact_ref": {
                "ref_kind": "exchange_artifact",
                "ref_id": "task/guide-worker-provider-execution/client:result",
                "version": "v1",
            },
            "acceptance": [
                "Client UI lane result artifact exists.",
                "Result records concrete validation evidence or a clear blocker.",
            ],
        },
        {
            "task_id": "task/guide-worker-provider-execution/server",
            "lane_id": "lane:server",
            "title": "Server API",
            "worker_agent_id": "agent:qoder-worker",
            "runtime_provider": "qoder",
            "task_state": "complete",
            "run_id": "qoder-run-2",
            "session_id": "qoder-session-2",
            "output_artifact_id": "task/guide-worker-provider-execution/server:result",
            "output_artifact_ref": {
                "ref_kind": "exchange_artifact",
                "ref_id": "task/guide-worker-provider-execution/server:result",
                "version": "v1",
            },
            "acceptance": [
                "Server API lane result artifact exists.",
                "Result records concrete validation evidence or a clear blocker.",
            ],
        },
    ]
    assert len(client.requests) == 2
    assert [request.task.title for request in client.requests] == [
        "Client UI",
        "Server API",
    ]
    assert not (tmp_path / ".codex/progress-graph/local-work-trajectory.json").exists()


def test_host_owned_guide_worker_provider_execution_explicit_workers_override_planner(
    tmp_path: Path,
) -> None:
    client = _RecordingQoderClient(
        QoderQueryResult(summary="explicit qoder worker complete", output_text="ok")
    )

    result = run_host_owned_guide_worker_provider_execution(
        tmp_path,
        config=HostOwnedGuideWorkerProviderExecutionConfig(
            evidence_id="guide-worker-explicit-overrides-planner",
            timestamp="2026-06-24T18:35:00+08:00",
            providers=("qoder",),
            worker_instructions=(
                GuideWorkerInstruction(
                    task_id="task/explicit/qoder",
                    title="Explicit qoder worker",
                    instruction="Run only this explicit worker.",
                    lane_id="lane:explicit",
                    worker_runtime_provider="qoder",
                    output_artifact_id="task/explicit/qoder:result",
                ),
            ),
            planning_request=GuideWorkerPlanningRequest(
                task_title="Ignored planner",
                lane_specs=(
                    GuideWorkerPlannerLaneSpec(
                        lane_id="lane:ignored",
                        label="Ignored",
                        focus="This lane must not run.",
                        worker_runtime_provider="fake",
                    ),
                ),
            ),
        ),
        qoder_query_client=client,
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["planning"]["source"] == "explicit_worker_instructions"
    assert payload["submitted_task_ids"] == ["task/explicit/qoder"]
    assert len(client.requests) == 1


def test_host_owned_guide_worker_provider_execution_rejects_unconfigured_planner_provider(
    tmp_path: Path,
) -> None:
    evidence_path = tmp_path / ".codex/scheduler/evidence/planner-provider-fail.json"

    with pytest.raises(ValueError, match="requests provider 'qoder'"):
        run_host_owned_guide_worker_provider_execution(
            tmp_path,
            config=HostOwnedGuideWorkerProviderExecutionConfig(
                evidence_id="planner-provider-fail",
                evidence_output_path=evidence_path,
                providers=("fake",),
                worker_instructions=(),
                planning_request=GuideWorkerPlanningRequest(
                    task_title="Provider guard",
                    lane_specs=(
                        GuideWorkerPlannerLaneSpec(
                            lane_id="lane:qoder",
                            label="Qoder lane",
                            focus="Should be rejected before writes.",
                            worker_runtime_provider="qoder",
                        ),
                    ),
                ),
            ),
        )

    assert evidence_path.exists() is False
    assert (
        tmp_path / ".codex/scheduler/guide-worker-provider-execution-state.json"
    ).exists() is False
    assert (
        tmp_path / ".codex/orchestration/exchange-artifacts.json"
    ).exists() is False


def test_host_owned_guide_worker_provider_execution_runs_planned_codex_workers(
    tmp_path: Path,
) -> None:
    client = _RecordingCodexCliClient(
        CodexCliResult(summary="planned codex worker complete", output_text="ok")
    )

    result = run_host_owned_guide_worker_provider_execution(
        tmp_path,
        config=HostOwnedGuideWorkerProviderExecutionConfig(
            evidence_id="guide-worker-planned-codex-provider",
            timestamp="2026-06-24T22:30:00+08:00",
            providers=("codex",),
            worker_agent_id="agent:codex-worker",
            worker_instructions=(),
            planning_request=GuideWorkerPlanningRequest(
                task_title="Build maze game",
                task_summary="Split browser client and server API work.",
                lane_specs=(
                    GuideWorkerPlannerLaneSpec(
                        lane_id="lane:client",
                        label="Client UI",
                        focus="browser maze controls and CLI-like test hooks",
                    ),
                    GuideWorkerPlannerLaneSpec(
                        lane_id="lane:server",
                        label="Server API",
                        focus="state API and port boundary",
                    ),
                ),
            ),
            planner_worker_runtime_provider="codex",
        ),
        codex_cli_client=client,
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["planning"]["source"] == "planning_request"
    assert payload["runtime_providers"] == ["codex"]
    assert payload["worker_runtime_providers"] == ["codex"]
    assert payload["submitted_task_ids"] == [
        "task/guide-worker-provider-execution/client",
        "task/guide-worker-provider-execution/server",
    ]
    assert [receipt["runtime_provider"] for receipt in payload["worker_execution_receipts"]] == [
        "codex",
        "codex",
    ]
    assert [receipt["run_id"] for receipt in payload["worker_execution_receipts"]] == [
        "codex-run-1",
        "codex-run-2",
    ]
    assert len(client.requests) == 2
    assert [request.task.title for request in client.requests] == [
        "Client UI",
        "Server API",
    ]
    assert client.requests[0].agent.runtime_provider == "codex"
    assert not (tmp_path / ".codex/progress-graph/local-work-trajectory.json").exists()


def test_host_owned_guide_worker_provider_execution_writes_codex_sandbox_receipts(
    tmp_path: Path,
) -> None:
    repo = _git_repo(tmp_path)
    client = _RecordingCodexCliClient(
        CodexCliResult(summary="codex worktree worker complete", output_text="ok")
    )
    allocation_path = tmp_path / ".codex/scheduler/evidence/codex-sandbox-allocation.json"

    result = run_host_owned_guide_worker_provider_execution(
        tmp_path,
        config=HostOwnedGuideWorkerProviderExecutionConfig(
            evidence_id="guide-worker-codex-sandbox",
            timestamp="2026-06-24T23:35:00+08:00",
            providers=("codex",),
            worker_agent_id="agent:codex-worker",
            workspace_root=str(repo),
            git_worktree_sandbox_root=tmp_path / "sandboxes",
            sandbox_allocation_evidence_id="codex-worker-sandbox-allocation",
            sandbox_allocation_evidence_path=allocation_path,
            worker_instructions=(
                GuideWorkerInstruction(
                    task_id="task/codex/worktree",
                    title="Codex worktree worker",
                    instruction="Run the worker in a git-worktree sandbox.",
                    lane_id="lane:client",
                    worker_runtime_provider="codex",
                    allowed_artifacts=("client/app.js",),
                    sandbox_profile=SandboxProfile(
                        profile_id="codex-worktree",
                        profile_kind="git-worktree",
                    ),
                    output_artifact_id="task/codex/worktree:result",
                ),
            ),
        ),
        codex_cli_client=client,
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert allocation_path.exists()
    assert payload["metadata"]["sandbox_allocation_evidence_path"] == str(allocation_path)
    assert payload["authority_split"]["sandbox_allocation_evidence_written"] is True
    receipt = payload["worker_writeback_receipts"][0]
    assert receipt["task_id"] == "task/codex/worktree"
    assert receipt["runtime_provider"] == "codex"
    assert receipt["sandbox_provider"] == "git-worktree"
    assert receipt["sandbox_allocation_id"] == "git-worktree:task/codex/worktree:codex-worktree"
    assert receipt["cleanup_required"] is True
    assert receipt["merge_review_state"] == "review_required"
    assert receipt["auto_merge_performed"] is False
    assert client.requests[0].task.runtime_workspace_root
    assert "sandboxes" in client.requests[0].task.runtime_workspace_root
    summary = read_sandbox_allocation_receipt_evidence_summary(allocation_path)
    assert summary.evidence_id == "codex-worker-sandbox-allocation"
    assert summary.allocation_count == 1
    allocation = summary.allocations[0]
    assert allocation.provider == "git-worktree"
    assert allocation.git_worktree_receipt is not None
    assert Path(allocation.git_worktree_receipt.worktree_path).exists()

    GitWorktreeSandboxProvider(tmp_path / "sandboxes").cleanup(allocation)


def test_host_owned_guide_worker_provider_execution_publishes_patch_review_candidate(
    tmp_path: Path,
) -> None:
    repo = _git_repo(tmp_path)

    def write_worker_change(request: CodexCliRequest) -> CodexCliResult:
        app = Path(request.task.runtime_workspace_root) / "client" / "app.js"
        app.parent.mkdir(parents=True, exist_ok=True)
        app.write_text("console.log('worker patch');\n", encoding="utf-8")
        return CodexCliResult(
            summary="codex worker changed client app",
            output_text="changed client/app.js",
            artifact_delta=ArtifactDelta(
                artifact_id="task/codex/worktree:result",
                version="v1",
                summary="client app changed in worker worktree",
                changed_refs=(
                    ExchangeReference(
                        ref_kind="file",
                        ref_id="client/app.js",
                        path="client/app.js",
                    ),
                ),
            ),
        )

    client = _RecordingCodexCliClient(write_worker_change)

    result = run_host_owned_guide_worker_provider_execution(
        tmp_path,
        config=HostOwnedGuideWorkerProviderExecutionConfig(
            evidence_id="guide-worker-codex-patch-review",
            timestamp="2026-06-24T23:55:00+08:00",
            providers=("codex",),
            worker_agent_id="agent:codex-worker",
            workspace_root=str(repo),
            git_worktree_sandbox_root=tmp_path / "sandboxes",
            worker_instructions=(
                GuideWorkerInstruction(
                    task_id="task/codex/worktree",
                    title="Codex worktree worker",
                    instruction="Change the client app in a git-worktree sandbox.",
                    lane_id="lane:client",
                    worker_runtime_provider="codex",
                    allowed_artifacts=("client/app.js",),
                    sandbox_profile=SandboxProfile(
                        profile_id="codex-worktree",
                        profile_kind="git-worktree",
                    ),
                    output_artifact_id="task/codex/worktree:result",
                ),
            ),
        ),
        codex_cli_client=client,
    )
    payload = result.to_json_dict()
    artifact_store_path = tmp_path / ".codex/orchestration/exchange-artifacts.json"
    assert len(payload["worker_patch_artifact_refs"]) == 1
    patch_ref = payload["worker_patch_artifact_refs"][0]
    patch_record = JsonArtifactVersionStore(artifact_store_path).get(
        patch_ref["ref_id"],
        patch_ref["version"],
    )
    candidates = inspect_agent_exchange_action_candidates(
        artifact_store_path,
        candidate_type="merge_candidate",
    )

    assert payload["ok"] is True
    assert patch_ref["patch_state"] == "has_patch"
    assert patch_ref["changed_paths"] == ["client/app.js"]
    assert payload["worker_writeback_receipts"][0]["patch_artifact_ref"] == patch_ref
    assert patch_record.artifact.intent == "request_merge"
    assert "worker patch" in patch_record.artifact.parts[3].data["git_diff"]
    assert candidates.candidate_type_counts == {"merge_candidate": 1}
    assert candidates.candidates[0].artifact_id == patch_ref["ref_id"]
    assert candidates.candidates[0].suggested_next_surface == "workerPatchReview"
    assert (repo / "client" / "app.js").read_text(encoding="utf-8") == (
        "console.log('ok');\n"
    )

    allocation = result.orchestration.run_results[0].preflight.sandbox_allocation
    GitWorktreeSandboxProvider(tmp_path / "sandboxes").cleanup(allocation)


def test_read_trajectory_artifacts_bundle_reports_missing_artifacts(tmp_path: Path) -> None:
    bundle = read_trajectory_artifacts_bundle(tmp_path)

    assert bundle.local.role == "agent"
    assert bundle.local.exists is False
    assert bundle.local.ok is False
    assert bundle.scheduler.role == "scheduler"
    assert bundle.scheduler.exists is False
    assert bundle.scheduler.ok is False
    assert bundle.summary()["local"]["path"].endswith("local-work-trajectory.json")
    assert bundle.summary()["scheduler"]["path"].endswith("scheduler-work-trajectory.json")


def test_read_trajectory_artifacts_bundle_isolates_parse_errors(tmp_path: Path) -> None:
    local_path = tmp_path / ".codex/progress-graph/local-work-trajectory.json"
    local_path.parent.mkdir(parents=True)
    local_path.write_text("{not-json", encoding="utf-8")
    state = SchedulerState(
        tasks={
            "api/task": _scheduler_projection_task(
                "api/task",
                lane_id="lane:server",
                state="complete",
            ),
        },
    )
    write_scheduler_work_trajectory_artifact(tmp_path, state)

    bundle = read_trajectory_artifacts_bundle(tmp_path)

    assert bundle.local.exists is True
    assert bundle.local.ok is False
    assert bundle.local.trajectory is None
    assert bundle.local.error
    assert bundle.scheduler.exists is True
    assert bundle.scheduler.ok is True
    assert bundle.scheduler.trajectory is not None
    assert bundle.scheduler.trajectory.trajectory_id == "local-work:scheduler-projection"


def test_read_trajectory_artifacts_bundle_summarizes_both_payloads(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        first_event_title="agent owned trajectory",
        lane_label="agent",
    )
    state = SchedulerState(
        tasks={
            "api/task": _scheduler_projection_task(
                "api/task",
                lane_id="lane:server",
                state="complete",
            ),
        },
    )
    write_scheduler_work_trajectory_artifact(tmp_path, state)

    bundle = read_trajectory_artifacts_bundle(tmp_path)
    summary = bundle.summary()

    assert bundle.local.ok is True
    assert bundle.scheduler.ok is True
    assert summary["local"]["trajectory_id"] == "local-work:single-line-current"
    assert summary["local"]["event_count"] == 1
    assert summary["scheduler"]["trajectory_id"] == "local-work:scheduler-projection"
    assert summary["scheduler"]["event_count"] == 1


def test_build_scheduler_work_trajectory_projects_fan_in_dependencies_as_merge_event() -> None:
    state = SchedulerState(
        tasks={
            "server-api": _scheduler_projection_task(
                "server-api",
                lane_id="lane:server",
                state="complete",
            ),
            "database-schema": _scheduler_projection_task(
                "database-schema",
                lane_id="lane:data",
                state="complete",
            ),
            "client-integration": _scheduler_projection_task(
                "client-integration",
                lane_id="lane:client",
                state="waiting",
                blocked_reason="waiting for server-api and database-schema",
            ),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-api-client",
                source_task_id="server-api",
                target_task_id="client-integration",
                dependency_kind="depends_on",
                required_state="complete",
            ),
            TaskDependency(
                dependency_id="dep-db-client",
                source_task_id="database-schema",
                target_task_id="client-integration",
                dependency_kind="depends_on",
                required_state="complete",
            ),
        ),
    )

    trajectory = build_scheduler_work_trajectory(state)

    merge_event_id = "scheduler-task:client-integration:fan-in-merge"
    assert merge_event_id in trajectory.events
    merge_event = trajectory.events[merge_event_id]
    assert merge_event.kind == "merge"
    assert merge_event.lane_id == "lane:client"
    assert merge_event.status == "waiting"
    assert merge_event.order < trajectory.events["scheduler-task:client-integration"].order
    assert merge_event.metadata["scheduler_projection_role"] == "fan-in-merge"
    assert merge_event.metadata["scheduler_target_task_id"] == "client-integration"
    assert merge_event.metadata["scheduler_dependency_ids"] == "dep-api-client\ndep-db-client"
    assert merge_event.metadata["scheduler_source_task_ids"] == "server-api\ndatabase-schema"

    target_event = trajectory.events["scheduler-task:client-integration"]
    assert target_event.metadata["scheduler_fan_in_dependency_ids"] == "dep-api-client\ndep-db-client"
    assert target_event.metadata["scheduler_fan_in_source_task_ids"] == "server-api\ndatabase-schema"

    fan_in_source_relations = [
        relation for relation in trajectory.relations
        if relation.metadata.get("relation_role") == "fan-in-source"
    ]
    assert {
        (relation.source_event_id, relation.target_event_id, relation.kind)
        for relation in fan_in_source_relations
    } == {
        ("scheduler-task:server-api", merge_event_id, "depends_on"),
        ("scheduler-task:database-schema", merge_event_id, "depends_on"),
    }
    merge_target_relations = [
        relation for relation in trajectory.relations
        if relation.metadata.get("relation_role") == "fan-in-merge-target"
    ]
    assert len(merge_target_relations) == 1
    assert merge_target_relations[0].source_event_id == merge_event_id
    assert merge_target_relations[0].target_event_id == "scheduler-task:client-integration"
    assert merge_target_relations[0].kind == "merges_into"
    assert not any(
        relation.source_event_id == "scheduler-task:client-integration"
        and relation.target_event_id == merge_event_id
        and relation.kind == "sequence"
        for relation in trajectory.relations
    )

    original_depends = [
        relation for relation in trajectory.relations
        if relation.kind == "depends_on"
        and relation.metadata.get("relation_role") != "fan-in-source"
    ]
    assert {
        (relation.source_event_id, relation.target_event_id)
        for relation in original_depends
    } == {
        ("scheduler-task:server-api", "scheduler-task:client-integration"),
        ("scheduler-task:database-schema", "scheduler-task:client-integration"),
    }
    assert trajectory.check_invariants() == []


def test_build_scheduler_work_trajectory_projects_scheduler_owned_merge_gate() -> None:
    state = SchedulerState(
        tasks={
            "server-api": _scheduler_projection_task(
                "server-api",
                lane_id="lane:server",
                state="complete",
            ),
            "database-schema": _scheduler_projection_task(
                "database-schema",
                lane_id="lane:data",
                state="complete",
            ),
            "client-integration": _scheduler_projection_task(
                "client-integration",
                lane_id="lane:client",
                state="waiting",
            ),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-api-client",
                source_task_id="server-api",
                target_task_id="client-integration",
            ),
            TaskDependency(
                dependency_id="dep-db-client",
                source_task_id="database-schema",
                target_task_id="client-integration",
            ),
        ),
        merge_gates=(
            SchedulerMergeGate(
                gate_id="merge-client-inputs",
                title="Review client integration inputs",
                target_task_id="client-integration",
                source_task_ids=("server-api", "database-schema"),
                dependency_ids=("dep-api-client", "dep-db-client"),
                gate_kind="review",
                state="review_required",
                required_review=True,
                output_artifact_id="merge-client-inputs:decision",
                decision_artifact_ref=ExchangeReference(
                    ref_kind="exchange_artifact",
                    ref_id="merge-client-inputs:decision",
                    version="v1",
                ),
                blocked_reason="waiting for guide review",
                created_at="2026-06-17T02:10:00+08:00",
            ),
        ),
    )

    trajectory = build_scheduler_work_trajectory(state)

    gate_event_id = "scheduler-task:client-integration:merge-gate:merge-client-inputs"
    assert gate_event_id in trajectory.events
    assert "scheduler-task:client-integration:fan-in-merge" not in trajectory.events
    gate_event = trajectory.events[gate_event_id]
    assert gate_event.kind == "merge"
    assert gate_event.status == "in_progress"
    assert gate_event.order < trajectory.events["scheduler-task:client-integration"].order
    assert gate_event.summary == "waiting for guide review"
    assert gate_event.metadata["scheduler_projection_role"] == "scheduler-owned-merge-gate"
    assert gate_event.metadata["scheduler_merge_gate_id"] == "merge-client-inputs"
    assert gate_event.metadata["scheduler_merge_gate_kind"] == "review"
    assert gate_event.metadata["scheduler_merge_gate_state"] == "review_required"
    assert gate_event.metadata["required_review"] == "true"
    assert gate_event.metadata["decision_artifact_id"] == "merge-client-inputs:decision"
    assert gate_event.metadata["decision_artifact_version"] == "v1"

    target_event = trajectory.events["scheduler-task:client-integration"]
    assert target_event.metadata["scheduler_merge_gate_ids"] == "merge-client-inputs"
    assert target_event.metadata["scheduler_merge_gate_states"] == "review_required"
    assert target_event.metadata["scheduler_merge_gate_kinds"] == "review"

    gate_source_relations = [
        relation for relation in trajectory.relations
        if relation.metadata.get("relation_role") == "scheduler-merge-gate-source"
    ]
    assert {
        (relation.source_event_id, relation.target_event_id, relation.kind)
        for relation in gate_source_relations
    } == {
        ("scheduler-task:server-api", gate_event_id, "depends_on"),
        ("scheduler-task:database-schema", gate_event_id, "depends_on"),
    }
    gate_target_relations = [
        relation for relation in trajectory.relations
        if relation.metadata.get("relation_role") == "scheduler-merge-gate-target"
    ]
    assert len(gate_target_relations) == 1
    assert gate_target_relations[0].source_event_id == gate_event_id
    assert gate_target_relations[0].target_event_id == "scheduler-task:client-integration"
    assert gate_target_relations[0].kind == "merges_into"
    assert not any(
        relation.source_event_id == "scheduler-task:client-integration"
        and relation.target_event_id == gate_event_id
        and relation.kind == "sequence"
        for relation in trajectory.relations
    )
    assert trajectory.check_invariants() == []


def test_build_scheduler_work_trajectory_projects_merge_gate_event_history_log() -> None:
    state = SchedulerState(
        tasks={
            "server-api": _scheduler_projection_task(
                "server-api",
                lane_id="lane:server",
                state="complete",
            ),
            "database-schema": _scheduler_projection_task(
                "database-schema",
                lane_id="lane:data",
                state="complete",
            ),
            "client-integration": _scheduler_projection_task(
                "client-integration",
                lane_id="lane:client",
                state="waiting",
            ),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-api-client",
                source_task_id="server-api",
                target_task_id="client-integration",
            ),
            TaskDependency(
                dependency_id="dep-db-client",
                source_task_id="database-schema",
                target_task_id="client-integration",
            ),
        ),
        merge_gates=(
            SchedulerMergeGate(
                gate_id="merge-client-inputs",
                title="Review client integration inputs",
                target_task_id="client-integration",
                source_task_ids=("server-api", "database-schema"),
                dependency_ids=("dep-api-client", "dep-db-client"),
                gate_kind="review",
                state="complete",
                required_review=True,
                decision_artifact_ref=ExchangeReference(
                    ref_kind="exchange_artifact",
                    ref_id="merge-client-inputs:decision",
                    version="v2",
                ),
                created_at="2026-06-17T02:10:00+08:00",
                resolved_at="2026-06-17T02:16:00+08:00",
            ),
        ),
    )
    events = (
        SchedulerMergeGateEvent(
            event_id="merge-gate-event-2",
            event_kind="merge_gate_completed",
            timestamp="2026-06-17T02:16:00+08:00",
            gate_id="merge-client-inputs",
            target_task_id="client-integration",
            from_state="review_required",
            to_state="complete",
            reason="guide approved merge inputs",
            decision_artifact_id="merge-client-inputs:decision",
            decision_artifact_version="v2",
            sequence=2,
        ),
        SchedulerMergeGateEvent(
            event_id="merge-gate-event-1",
            event_kind="merge_gate_review_required",
            timestamp="2026-06-17T02:12:00+08:00",
            gate_id="merge-client-inputs",
            target_task_id="client-integration",
            from_state="ready",
            to_state="review_required",
            reason="requires guide review before client work",
            sequence=1,
        ),
        SchedulerMergeGateEvent(
            event_id="merge-gate-event-orphan",
            event_kind="merge_gate_blocked",
            timestamp="2026-06-17T02:11:00+08:00",
            gate_id="other-gate",
            target_task_id="other-task",
            sequence=0,
        ),
    )

    trajectory = build_scheduler_work_trajectory(state, merge_gate_events=events)

    gate_event = trajectory.events[
        "scheduler-task:client-integration:merge-gate:merge-client-inputs"
    ]
    assert gate_event.metadata["scheduler_merge_gate_event_ids"] == (
        "merge-gate-event-1\nmerge-gate-event-2"
    )
    assert gate_event.metadata["scheduler_merge_gate_event_kinds"] == (
        "merge_gate_review_required\nmerge_gate_completed"
    )
    assert gate_event.metadata["scheduler_merge_gate_event_timestamps"] == (
        "2026-06-17T02:12:00+08:00\n2026-06-17T02:16:00+08:00"
    )
    assert gate_event.metadata["scheduler_merge_gate_event_sequences"] == "1\n2"
    assert gate_event.metadata["scheduler_merge_gate_event_decision_artifact_ids"] == (
        "merge-client-inputs:decision"
    )
    assert gate_event.metadata["scheduler_merge_gate_event_decision_artifact_versions"] == "v2"
    assert gate_event.metadata["scheduler_merge_gate_event_log"] == (
        "timestamp=2026-06-17T02:12:00+08:00 | "
        "kind=merge_gate_review_required | id=merge-gate-event-1 | sequence=1 | "
        "state=ready->review_required | reason=requires guide review before client work\n"
        "timestamp=2026-06-17T02:16:00+08:00 | "
        "kind=merge_gate_completed | id=merge-gate-event-2 | sequence=2 | "
        "state=review_required->complete | reason=guide approved merge inputs | "
        "decision_artifact=merge-client-inputs:decision@v2"
    )
    assert "merge-gate-event-orphan" not in gate_event.metadata["scheduler_merge_gate_event_log"]
    assert trajectory.check_invariants() == []


def test_set_local_work_trajectory_anchor_updates_and_clears_parent_node(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        lane_label="main",
        first_event_title="start anchored work",
    )

    set_local_work_trajectory_anchor(
        tmp_path,
        source_graph_id="planning-gates-index",
        source_node_id="gate:anchor",
        summary="move under active planning node",
        reason="task context moved",
    )
    loaded = load_local_work_trajectory(tmp_path)

    assert loaded.source_graph_id == "planning-gates-index"
    assert loaded.source_node_id == "gate:anchor"
    assert loaded.metadata["anchor_state"] == "set"
    assert loaded.metadata["anchor_graph_id"] == "planning-gates-index"
    assert loaded.metadata["anchor_node_id"] == "gate:anchor"
    assert loaded.metadata["anchor_summary"] == "move under active planning node"
    assert loaded.metadata["anchor_reason"] == "task context moved"

    set_local_work_trajectory_anchor(tmp_path)
    cleared = load_local_work_trajectory(tmp_path)

    assert cleared.source_graph_id == ""
    assert cleared.source_node_id == ""
    assert cleared.metadata["anchor_state"] == "cleared"
    assert "anchor_graph_id" not in cleared.metadata
    assert "anchor_node_id" not in cleared.metadata


def test_set_local_work_trajectory_anchor_requires_pair(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        lane_label="main",
        first_event_title="start anchored work",
    )

    with pytest.raises(ValueError, match="requires source_graph_id and source_node_id together"):
        set_local_work_trajectory_anchor(
            tmp_path,
            source_graph_id="planning-gates-index",
        )


def test_start_single_line_trajectory_can_attach_initial_anchor(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        lane_label="main",
        first_event_title="start anchored work",
        source_graph_id="planning-gates-index",
        source_node_id="gate:anchor",
    )

    loaded = load_local_work_trajectory(tmp_path)

    assert loaded.source_graph_id == "planning-gates-index"
    assert loaded.source_node_id == "gate:anchor"
    assert loaded.metadata["anchor_state"] == "set"
    assert loaded.metadata["anchor_graph_id"] == "planning-gates-index"
    assert loaded.metadata["anchor_node_id"] == "gate:anchor"


def test_start_single_line_trajectory_requires_anchor_pair(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="start anchor requires source_graph_id and source_node_id together"):
        start_single_line_trajectory(
            tmp_path,
            lane_label="main",
            first_event_title="start half-anchored work",
            source_graph_id="planning-gates-index",
        )


def test_local_work_trajectory_validates_lane_and_relation_references() -> None:
    trajectory = LocalWorkTrajectory(
        trajectory_id="local-work:test",
        title="Test",
    )
    trajectory.add_lane(TrajectoryLane(id="lane:main", label="Main"))
    trajectory.add_event(
        TrajectoryEvent(
            id="event:001",
            lane_id="lane:missing",
            title="Invalid lane",
        )
    )
    trajectory.add_relation(
        TrajectoryRelation(
            source_event_id="event:001",
            target_event_id="event:404",
        )
    )

    with pytest.raises(ValueError, match="unknown lane.*event:404"):
        trajectory.validate()


def test_single_line_lifecycle_creates_appends_and_advances_events(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="单线闭环测试",
        lane_label="接口适配",
        first_event_title="生成初始线和首节点",
        guide_context="design_docs/progress-graph-local-work-trajectory-ui-requirements.md",
    )
    started = load_local_work_trajectory(tmp_path)
    assert started.source_graph_id == ""
    assert started.source_node_id == ""
    append_single_line_event(
        tmp_path,
        title="生成后续节点",
        kind="task",
        summary="追加一个待推进节点。",
    )
    append_single_line_event(
        tmp_path,
        title="完成节点推进闭环",
        kind="validation",
    )

    trajectory = load_local_work_trajectory(tmp_path)
    assert trajectory.metadata["projection"] == "single-lane-lifecycle"
    assert [event.status for event in trajectory.events.values()] == [
        "in_progress",
        "pending",
        "pending",
    ]
    assert [
        (relation.source_event_id, relation.target_event_id, relation.kind)
        for relation in trajectory.relations
    ] == [
        ("event:001", "event:002", "sequence"),
        ("event:002", "event:003", "sequence"),
    ]

    advance_single_line_event(tmp_path)
    trajectory = load_local_work_trajectory(tmp_path)

    assert trajectory.lanes["lane:main"].status == "active"
    assert [event.status for event in trajectory.events.values()] == [
        "completed",
        "in_progress",
        "pending",
    ]
    assert "completed_at" in trajectory.events["event:001"].metadata
    assert "activated_at" in trajectory.events["event:002"].metadata


def test_refresh_artifact_preserves_single_line_lifecycle_state(tmp_path: Path) -> None:
    write_checkpoint(
        tmp_path,
        phase="Checkpoint fallback",
        todos=[
            {"title": "Checkpoint todo should not overwrite lifecycle", "status": "not-started"},
        ],
    )
    start_single_line_trajectory(
        tmp_path,
        first_event_title="显式生命周期首节点",
        lane_label="单线",
    )
    append_single_line_event(tmp_path, title="显式生命周期后续节点")

    write_local_work_trajectory_artifact(tmp_path)
    trajectory = load_local_work_trajectory(tmp_path)

    assert trajectory.trajectory_id == "local-work:single-line-current"
    assert [event.title for event in trajectory.events.values()] == [
        "显式生命周期首节点",
        "显式生命周期后续节点",
    ]


def test_refresh_artifact_resets_legacy_checkpoint_projection_to_empty_lifecycle(tmp_path: Path) -> None:
    write_checkpoint(
        tmp_path,
        phase="Legacy checkpoint fallback",
        todos=[
            {"title": "Old checkpoint todo should not reappear", "status": "in-progress"},
        ],
    )
    write_checkpoint_work_trajectory(tmp_path)

    write_local_work_trajectory_artifact(tmp_path)
    trajectory = load_local_work_trajectory(tmp_path)

    assert trajectory.trajectory_id == "local-work:single-line-current"
    assert trajectory.metadata["projection"] == "single-lane-lifecycle"
    assert trajectory.metadata["lifecycle_state"] == "empty"
    assert trajectory.lanes == {}
    assert trajectory.events == {}
    assert trajectory.relations == []


def test_clear_single_line_trajectory_writes_durable_empty_state(tmp_path: Path) -> None:
    clear_single_line_trajectory(tmp_path)

    trajectory = load_local_work_trajectory(tmp_path)

    assert trajectory.source_graph_id == ""
    assert trajectory.source_node_id == ""
    assert trajectory.metadata["projection"] == "single-lane-lifecycle"
    assert trajectory.metadata["lane_mode"] == "single"
    assert trajectory.metadata["lifecycle_state"] == "empty"
    assert trajectory.summary()["event_count"] == 0


def test_advance_single_line_event_reports_unknown_event(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        first_event_title="首节点",
    )

    with pytest.raises(ValueError, match="unknown trajectory event: event:404"):
        advance_single_line_event(tmp_path, current_event_id="event:404")


def test_single_line_lifecycle_updates_blocks_resumes_and_closes(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="单线状态控制",
        lane_label="实现",
        first_event_title="初始节点",
    )
    append_single_line_event(tmp_path, title="验证节点", kind="validation")

    update_single_line_event(
        tmp_path,
        title="更新后的当前节点",
        summary="补充当前节点说明。",
    )
    trajectory = load_local_work_trajectory(tmp_path)
    assert trajectory.events["event:001"].title == "更新后的当前节点"
    assert trajectory.events["event:001"].summary == "补充当前节点说明。"
    assert "updated_at" in trajectory.events["event:001"].metadata

    block_single_line_event(tmp_path, reason="等待外部输入。", waiting=True)
    trajectory = load_local_work_trajectory(tmp_path)
    assert trajectory.events["event:001"].status == "waiting"
    assert trajectory.lanes["lane:main"].status == "waiting"
    assert trajectory.events["event:001"].metadata["waiting_reason"] == "等待外部输入。"

    resume_single_line_event(tmp_path, summary="输入已到位。")
    trajectory = load_local_work_trajectory(tmp_path)
    assert trajectory.events["event:001"].status == "in_progress"
    assert trajectory.lanes["lane:main"].status == "active"
    assert trajectory.events["event:001"].summary == "输入已到位。"
    assert "resumed_at" in trajectory.events["event:001"].metadata

    close_single_line_trajectory(tmp_path, summary="单线任务完成。")
    trajectory = load_local_work_trajectory(tmp_path)
    assert trajectory.events["event:001"].status == "completed"
    assert trajectory.events["event:001"].summary == "单线任务完成。"
    assert trajectory.events["event:002"].status == "archived"
    assert trajectory.lanes["lane:main"].status == "done"


def test_local_work_lifecycle_adds_second_lane_and_appends_within_it(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="多线第一步",
        lane_label="主线",
        first_event_title="主线起点",
    )

    add_local_work_lane(
        tmp_path,
        lane_label="验证",
        first_event_title="验证线起点",
        first_event_kind="validation",
        source_event_id="event:001",
        lane_id="lane:validation",
    )
    append_single_line_event(
        tmp_path,
        title="验证线后续",
        kind="task",
        lane_id="lane:validation",
    )

    trajectory = load_local_work_trajectory(tmp_path)

    assert trajectory.metadata["lane_mode"] == "multi"
    assert set(trajectory.lanes) == {"lane:main", "lane:validation"}
    validation_events = [
        event for event in trajectory.events.values()
        if event.lane_id == "lane:validation"
    ]
    assert [event.title for event in validation_events] == [
        "验证线起点",
        "验证线后续",
    ]
    assert [event.order for event in validation_events] == [1, 2]
    assert any(
        relation.source_event_id == "event:001"
        and relation.target_event_id == validation_events[0].id
        and relation.kind == "proposes_new_line"
        for relation in trajectory.relations
    )
    assert any(
        relation.source_event_id == validation_events[0].id
        and relation.target_event_id == validation_events[1].id
        and relation.kind == "sequence"
        for relation in trajectory.relations
    )


def test_local_work_lifecycle_adds_multiple_lanes_from_one_source(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Batch fanout",
        lane_label="main",
        first_event_title="decide split",
    )

    add_local_work_lanes(
        tmp_path,
        source_event_id="event:001",
        lanes=[
            {
                "laneLabel": "server",
                "firstEventTitle": "server contract",
                "eventKind": "task",
            },
            {
                "laneLabel": "client",
                "firstEventTitle": "client shell",
                "eventKind": "task",
                "laneId": "lane:client",
            },
            {
                "laneLabel": "tests",
                "firstEventTitle": "test harness",
                "eventKind": "validation",
            },
        ],
    )

    trajectory = load_local_work_trajectory(tmp_path)
    opening_relations = [
        relation for relation in trajectory.relations
        if relation.source_event_id == "event:001"
        and relation.kind == "proposes_new_line"
    ]

    assert trajectory.metadata["lane_mode"] == "multi"
    assert len(trajectory.lanes) == 4
    assert len(opening_relations) == 3
    assert {trajectory.events[relation.target_event_id].title for relation in opening_relations} == {
        "server contract",
        "client shell",
        "test harness",
    }
    assert {relation.metadata["batch_open_count"] for relation in opening_relations} == {"3"}
    assert [relation.metadata["batch_open_index"] for relation in opening_relations] == [
        "1",
        "2",
        "3",
    ]
    client_event = next(
        event for event in trajectory.events.values()
        if event.title == "client shell"
    )
    assert client_event.lane_id == "lane:client"


def test_local_work_lifecycle_merges_second_lane_into_main(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Multi-line merge",
        lane_label="main",
        first_event_title="main start",
    )
    add_local_work_lane(
        tmp_path,
        lane_label="docs",
        first_event_title="docs start",
        first_event_kind="task",
        source_event_id="event:001",
        lane_id="lane:docs",
    )
    append_single_line_event(
        tmp_path,
        title="docs conclusion",
        kind="validation",
        lane_id="lane:docs",
    )
    advance_single_line_event(tmp_path, current_event_id="event:002")
    advance_single_line_event(tmp_path, current_event_id="event:003")

    merge_local_work_lane(
        tmp_path,
        source_lane_id="lane:docs",
        target_lane_id="lane:main",
        title="merge docs conclusion",
        summary="docs lane rejoins the main lane",
    )

    trajectory = load_local_work_trajectory(tmp_path)
    merge_events = [
        event for event in trajectory.events.values()
        if event.lane_id == "lane:main" and event.kind == "merge"
    ]

    assert trajectory.metadata["lane_mode"] == "multi"
    assert len(merge_events) == 1
    assert merge_events[0].status == "in_progress"
    assert merge_events[0].title == "merge docs conclusion"
    assert merge_events[0].metadata["source_lane_id"] == "lane:docs"
    assert merge_events[0].metadata["target_lane_id"] == "lane:main"
    assert any(
        relation.source_event_id == "event:003"
        and relation.target_event_id == merge_events[0].id
        and relation.kind == "merges_into"
        for relation in trajectory.relations
    )
    assert any(
        relation.source_event_id == "event:001"
        and relation.target_event_id == merge_events[0].id
        and relation.kind == "sequence"
        for relation in trajectory.relations
    )


def test_local_work_lifecycle_adds_explicit_cross_lane_relation(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Relation map",
        lane_label="main",
        first_event_title="main start",
    )
    add_local_work_lane(
        tmp_path,
        lane_label="validation",
        first_event_title="validation start",
        lane_id="lane:validation",
        source_event_id="event:001",
    )

    add_local_work_relation(
        tmp_path,
        source_event_id="event:001",
        target_event_id="event:002",
        relation_kind="depends_on",
        summary="validation depends on main setup",
    )
    add_local_work_relation(
        tmp_path,
        source_event_id="event:001",
        target_event_id="event:002",
        relation_kind="depends_on",
        summary="validation depends on updated main setup",
    )

    trajectory = load_local_work_trajectory(tmp_path)
    matching_relations = [
        relation for relation in trajectory.relations
        if relation.source_event_id == "event:001"
        and relation.target_event_id == "event:002"
        and relation.kind == "depends_on"
    ]

    assert trajectory.metadata["lane_mode"] == "multi"
    assert len(matching_relations) == 1
    assert matching_relations[0].summary == "validation depends on updated main setup"
    assert matching_relations[0].metadata["source_lane_id"] == "lane:main"
    assert matching_relations[0].metadata["target_lane_id"] == "lane:validation"


def test_local_work_lifecycle_adds_planned_compound_with_child_trajectory(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Compound map",
        lane_label="main",
        first_event_title="main start",
    )

    add_local_work_compound(
        tmp_path,
        title="implementation phase",
        summary="planned compound work",
        first_child_event_title="define internal acceptance",
        first_child_event_kind="review",
        child_lane_label="implementation internals",
    )

    trajectory = load_local_work_trajectory(tmp_path)
    compound = trajectory.events["event:002"]
    child_trajectory_id = compound.metadata["child_trajectory_id"]
    child_trajectory = trajectory.child_trajectories[child_trajectory_id]

    assert compound.kind == "compound"
    assert compound.status == "in_progress"
    assert compound.summary == "planned compound work"
    assert compound.metadata["compound_mode"] == "planned"
    assert child_trajectory.source_graph_id == trajectory.trajectory_id
    assert child_trajectory.source_node_id == compound.id
    assert child_trajectory.metadata["parent_event_id"] == compound.id
    assert child_trajectory.metadata["compound_mode"] == "planned"
    assert child_trajectory.lanes["lane:main"].label == "implementation internals"
    assert child_trajectory.events["event:001"].title == "define internal acceptance"
    assert child_trajectory.events["event:001"].kind == "review"
    assert child_trajectory.events["event:001"].status == "in_progress"
    assert any(
        relation.source_event_id == "event:001"
        and relation.target_event_id == "event:002"
        and relation.kind == "sequence"
        for relation in trajectory.relations
    )

    round_tripped = LocalWorkTrajectory.from_json(trajectory.to_json())
    assert child_trajectory_id in round_tripped.child_trajectories
    assert round_tripped.events["event:002"].kind == "compound"


def test_local_work_lifecycle_adds_empty_planned_compound(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Compound map",
        lane_label="main",
        first_event_title="main start",
    )

    add_local_work_compound(
        tmp_path,
        title="empty future phase",
    )

    trajectory = load_local_work_trajectory(tmp_path)
    compound = trajectory.events["event:002"]
    child_trajectory = trajectory.child_trajectories[compound.metadata["child_trajectory_id"]]

    assert compound.kind == "compound"
    assert compound.status == "pending"
    assert child_trajectory.lanes == {}
    assert child_trajectory.events == {}
    assert trajectory.lanes["lane:main"].status == "active"


def test_local_work_lifecycle_appends_advances_and_closes_child_trajectory(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Compound child map",
        lane_label="main",
        first_event_title="main start",
    )
    add_local_work_compound(
        tmp_path,
        title="implementation phase",
        first_child_event_title="define internals",
        child_lane_label="internals",
    )
    append_local_work_child_event(
        tmp_path,
        parent_event_id="event:002",
        title="implement internals",
        kind="task",
    )

    trajectory = load_local_work_trajectory(tmp_path)
    compound = trajectory.events["event:002"]
    child = trajectory.child_trajectories[compound.metadata["child_trajectory_id"]]

    assert compound.status == "in_progress"
    assert [event.title for event in child.events.values()] == [
        "define internals",
        "implement internals",
    ]
    assert [event.status for event in child.events.values()] == [
        "in_progress",
        "pending",
    ]

    advance_local_work_child_event(tmp_path, parent_event_id="event:002")
    trajectory = load_local_work_trajectory(tmp_path)
    compound = trajectory.events["event:002"]
    child = trajectory.child_trajectories[compound.metadata["child_trajectory_id"]]
    assert compound.status == "in_progress"
    assert [event.status for event in child.events.values()] == [
        "completed",
        "in_progress",
    ]

    close_local_work_child_trajectory(
        tmp_path,
        parent_event_id="event:002",
        summary="child work done",
    )
    trajectory = load_local_work_trajectory(tmp_path)
    compound = trajectory.events["event:002"]
    child = trajectory.child_trajectories[compound.metadata["child_trajectory_id"]]
    assert compound.status == "completed"
    assert child.lanes["lane:main"].status == "done"
    assert child.events["event:002"].status == "completed"
    assert child.events["event:002"].summary == "child work done"


def test_local_work_lifecycle_packs_continuous_range_into_compound(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Pack map",
        lane_label="main",
        first_event_title="setup",
    )
    append_single_line_event(tmp_path, title="design", kind="task")
    append_single_line_event(tmp_path, title="implement", kind="task")
    append_single_line_event(tmp_path, title="validate", kind="validation")
    append_single_line_event(tmp_path, title="deliver", kind="writeback")
    advance_single_line_event(tmp_path, current_event_id="event:001")
    advance_single_line_event(tmp_path, current_event_id="event:002")
    add_local_work_relation(
        tmp_path,
        source_event_id="event:002",
        target_event_id="event:004",
        relation_kind="depends_on",
        summary="internal dependency",
    )
    add_local_work_relation(
        tmp_path,
        source_event_id="event:005",
        target_event_id="event:003",
        relation_kind="waits_for",
        summary="delivery waits for implementation",
    )

    pack_local_work_range(
        tmp_path,
        title="build phase",
        range_start_event_id="event:002",
        range_end_event_id="event:004",
        summary="packed implementation interval",
        child_lane_label="build internals",
    )

    trajectory = load_local_work_trajectory(tmp_path)
    parent_events = sorted(trajectory.events.values(), key=lambda event: event.order)
    compound = next(event for event in parent_events if event.kind == "compound")
    child = trajectory.child_trajectories[compound.metadata["child_trajectory_id"]]

    assert [event.title for event in parent_events] == ["setup", "build phase", "deliver"]
    assert [event.order for event in parent_events] == [1, 2, 3]
    assert compound.status == "in_progress"
    assert compound.summary == "packed implementation interval"
    assert compound.metadata["compound_mode"] == "packed-range"
    assert compound.metadata["packed_event_ids"] == "event:002,event:003,event:004"
    assert child.lanes["lane:main"].label == "build internals"
    assert [event.title for event in child.events.values()] == [
        "design",
        "implement",
        "validate",
    ]
    assert [event.order for event in child.events.values()] == [1, 2, 3]
    assert any(
        relation.source_event_id == "event:002"
        and relation.target_event_id == "event:004"
        and relation.kind == "depends_on"
        for relation in child.relations
    )
    assert any(
        relation.source_event_id == "event:001"
        and relation.target_event_id == compound.id
        and relation.kind == "sequence"
        for relation in trajectory.relations
    )
    assert any(
        relation.source_event_id == compound.id
        and relation.target_event_id == "event:005"
        and relation.kind == "sequence"
        for relation in trajectory.relations
    )
    assert any(
        relation.source_event_id == "event:005"
        and relation.target_event_id == compound.id
        and relation.kind == "waits_for"
        and relation.metadata["rewired_from_packed_range"] == "true"
        for relation in trajectory.relations
    )


def test_local_work_lifecycle_pack_range_rejects_cross_lane_events(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Pack map",
        lane_label="main",
        first_event_title="setup",
    )
    add_local_work_lane(
        tmp_path,
        lane_label="docs",
        first_event_title="docs start",
        lane_id="lane:docs",
        source_event_id="event:001",
    )

    with pytest.raises(ValueError, match="same lane"):
        pack_local_work_range(
            tmp_path,
            title="invalid pack",
            range_start_event_id="event:001",
            range_end_event_id="event:002",
        )


def test_local_work_lifecycle_pack_range_moves_nested_compound_children(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Nested pack map",
        lane_label="main",
        first_event_title="setup",
    )
    add_local_work_compound(
        tmp_path,
        title="inner phase",
        first_child_event_title="inner first",
    )
    append_single_line_event(tmp_path, title="tail")

    before = load_local_work_trajectory(tmp_path)
    inner_child_id = before.events["event:002"].metadata["child_trajectory_id"]

    pack_local_work_range(
        tmp_path,
        title="outer phase",
        range_start_event_id="event:002",
        range_end_event_id="event:003",
    )

    trajectory = load_local_work_trajectory(tmp_path)
    outer = next(event for event in trajectory.events.values() if event.kind == "compound")
    outer_child = trajectory.child_trajectories[outer.metadata["child_trajectory_id"]]

    assert inner_child_id not in trajectory.child_trajectories
    assert inner_child_id in outer_child.child_trajectories
    assert outer_child.events["event:002"].kind == "compound"
    assert outer_child.events["event:002"].metadata["child_trajectory_id"] == inner_child_id


def test_local_work_lifecycle_packs_multi_line_subgraph_with_proxy_projection(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Multi-line pack map",
        lane_label="main",
        first_event_title="main setup",
    )
    append_single_line_event(tmp_path, title="main design")
    append_single_line_event(tmp_path, title="main implement")
    add_local_work_lane(
        tmp_path,
        lane_label="validation",
        first_event_title="validation setup",
        lane_id="lane:validation",
        source_event_id="event:001",
    )
    append_single_line_event(
        tmp_path,
        title="validation execute",
        kind="validation",
        lane_id="lane:validation",
    )
    add_local_work_relation(
        tmp_path,
        source_event_id="event:002",
        target_event_id="event:005",
        relation_kind="depends_on",
        summary="validation follows main design",
    )

    pack_local_work_subgraph(
        tmp_path,
        title="implementation phase",
        anchor_lane_id="lane:main",
        ranges=[
            {
                "lane_id": "lane:main",
                "range_start_event_id": "event:002",
                "range_end_event_id": "event:003",
            },
            {
                "lane_id": "lane:validation",
                "range_start_event_id": "event:004",
                "range_end_event_id": "event:005",
            },
        ],
        summary="packed multi-line implementation",
    )

    trajectory = load_local_work_trajectory(tmp_path)
    anchor = next(
        event for event in trajectory.events.values()
        if event.metadata.get("compound_role") == "anchor"
    )
    proxy = next(
        event for event in trajectory.events.values()
        if event.metadata.get("compound_role") == "proxy"
    )
    child = trajectory.child_trajectories[anchor.metadata["child_trajectory_id"]]

    assert anchor.kind == "compound"
    assert anchor.metadata["compound_mode"] == "packed-multi-line"
    assert anchor.metadata["compound_role"] == "anchor"
    assert proxy.kind == "compound"
    assert proxy.metadata["compound_role"] == "proxy"
    assert proxy.metadata["anchor_compound_event_id"] == anchor.id
    assert proxy.metadata["child_trajectory_id"] == anchor.metadata["child_trajectory_id"]
    assert set(child.lanes) == {"lane:main", "lane:validation"}
    assert child.lanes["lane:main"].metadata["source_lane_id"] == "lane:main"
    assert child.lanes["lane:validation"].metadata["source_lane_id"] == "lane:validation"
    child_main_events = sorted(
        (event for event in child.events.values() if event.lane_id == "lane:main"),
        key=lambda event: (event.order, event.id),
    )
    child_validation_events = sorted(
        (event for event in child.events.values() if event.lane_id == "lane:validation"),
        key=lambda event: (event.order, event.id),
    )
    assert [event.title for event in child_main_events] == [
        "main design",
        "main implement",
    ]
    assert [event.title for event in child_validation_events] == [
        "validation setup",
        "validation execute",
    ]
    assert any(
        relation.source_event_id == "event:002"
        and relation.target_event_id == "event:005"
        and relation.kind == "depends_on"
        for relation in child.relations
    )
    assert any(
        relation.source_event_id == "event:001"
        and relation.target_event_id == anchor.id
        and relation.kind == "sequence"
        for relation in trajectory.relations
    )
    assert any(
        relation.source_event_id == "event:001"
        and relation.target_event_id == proxy.id
        and relation.kind == "proposes_new_line"
        and relation.metadata["relation_projection"] == "cross-boundary"
        and relation.metadata["target_endpoint_trajectory_id"] == child.trajectory_id
        and relation.metadata["target_endpoint_event_id"] == "event:004"
        for relation in trajectory.relations
    )


def test_local_work_lifecycle_pack_subgraph_rejects_non_anchor_lane(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Multi-line pack map",
        lane_label="main",
        first_event_title="main setup",
    )
    append_single_line_event(tmp_path, title="main design")

    with pytest.raises(ValueError, match="anchor_lane_id must be one of the selected lanes"):
        pack_local_work_subgraph(
            tmp_path,
            title="bad pack",
            anchor_lane_id="lane:missing",
            ranges=[
                {
                    "lane_id": "lane:main",
                    "range_start_event_id": "event:001",
                    "range_end_event_id": "event:002",
                }
            ],
        )


def test_local_work_lifecycle_rejects_invalid_compound_proxy_fixture() -> None:
    trajectory = LocalWorkTrajectory(
        trajectory_id="local-work:test",
        title="proxy fixture",
        metadata={"projection": "single-lane-lifecycle", "lane_mode": "multi"},
    )
    trajectory.add_lane(TrajectoryLane(id="lane:main", label="main"))
    trajectory.add_event(
        TrajectoryEvent(
            id="event:001",
            lane_id="lane:main",
            title="orphan proxy",
            kind="compound",
            metadata={
                "compound_mode": "packed-multi-line",
                "compound_role": "proxy",
                "child_trajectory_id": "child:missing",
            },
        )
    )

    with pytest.raises(ValueError, match="unknown child trajectory.*does not reference an anchor"):
        trajectory.validate()


def test_local_work_lifecycle_adds_cross_compound_projected_relation(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Cross-pack map",
        lane_label="main",
        first_event_title="setup",
    )
    append_single_line_event(tmp_path, title="alpha task")
    append_single_line_event(tmp_path, title="beta task")
    pack_local_work_range(
        tmp_path,
        title="alpha pack",
        range_start_event_id="event:002",
        range_end_event_id="event:002",
    )
    pack_local_work_range(
        tmp_path,
        title="beta pack",
        range_start_event_id="event:003",
        range_end_event_id="event:003",
    )

    trajectory = load_local_work_trajectory(tmp_path)
    compounds = [
        event for event in sorted(trajectory.events.values(), key=lambda item: item.order)
        if event.kind == "compound"
    ]
    alpha, beta = compounds
    alpha_child_id = alpha.metadata["child_trajectory_id"]
    beta_child_id = beta.metadata["child_trajectory_id"]

    add_local_work_relation(
        tmp_path,
        source_event_id=alpha.id,
        target_event_id=beta.id,
        relation_kind="depends_on",
        summary="beta depends on alpha internal result",
        source_endpoint=TrajectoryEndpoint(
            trajectory_id=alpha_child_id,
            event_id="event:002",
            parent_event_id=alpha.id,
            compound_path=alpha.id,
        ),
        target_endpoint={
            "trajectory_id": beta_child_id,
            "event_id": "event:003",
            "parent_event_id": beta.id,
            "compound_path": beta.id,
        },
    )

    trajectory = load_local_work_trajectory(tmp_path)
    matching = [
        relation for relation in trajectory.relations
        if relation.source_event_id == alpha.id
        and relation.target_event_id == beta.id
        and relation.kind == "depends_on"
    ]

    assert len(matching) == 1
    relation = matching[0]
    assert relation.summary == "beta depends on alpha internal result"
    assert relation.metadata["relation_projection"] == "cross-compound"
    assert relation.metadata["source_endpoint_trajectory_id"] == alpha_child_id
    assert relation.metadata["source_endpoint_event_id"] == "event:002"
    assert relation.metadata["target_endpoint_trajectory_id"] == beta_child_id
    assert relation.metadata["target_endpoint_event_id"] == "event:003"


def test_local_work_lifecycle_rejects_invalid_cross_compound_endpoint(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        title="Cross-pack map",
        lane_label="main",
        first_event_title="setup",
    )
    append_single_line_event(tmp_path, title="alpha task")
    append_single_line_event(tmp_path, title="beta task")
    pack_local_work_range(
        tmp_path,
        title="alpha pack",
        range_start_event_id="event:002",
        range_end_event_id="event:002",
    )

    with pytest.raises(ValueError, match="unknown target endpoint trajectory"):
        trajectory = load_local_work_trajectory(tmp_path)
        alpha = next(event for event in trajectory.events.values() if event.kind == "compound")
        add_local_work_relation(
            tmp_path,
            source_event_id=alpha.id,
            target_event_id="event:003",
            relation_kind="depends_on",
            source_endpoint={
                "trajectory_id": alpha.metadata["child_trajectory_id"],
                "event_id": "event:002",
                "parent_event_id": alpha.id,
                "compound_path": alpha.id,
            },
            target_endpoint={
                "trajectory_id": "child:missing",
                "event_id": "event:999",
            },
        )


def test_local_work_lifecycle_rejects_invalid_explicit_relation(tmp_path: Path) -> None:
    start_single_line_trajectory(
        tmp_path,
        lane_label="main",
        first_event_title="main start",
    )

    with pytest.raises(ValueError, match="cannot use sequence"):
        add_local_work_relation(
            tmp_path,
            source_event_id="event:001",
            target_event_id="event:001",
            relation_kind="sequence",
        )

    with pytest.raises(ValueError, match="unknown target trajectory event"):
        add_local_work_relation(
            tmp_path,
            source_event_id="event:001",
            target_event_id="event:404",
            relation_kind="waits_for",
        )


def _scheduler_projection_task(
    task_id: str,
    *,
    lane_id: str,
    agent: AgentSpec | None = None,
    state: ScheduledTaskState = "proposed",
    blocked_reason: str = "",
    edit_lease: EditScopeLease | None = None,
    run_id: str = "",
    output_ref: ExchangeReference | None = None,
    output_artifact_id: str = "",
) -> ScheduledTask:
    return ScheduledTask(
        task_id=task_id,
        title=f"Task {task_id}",
        instruction=f"Instruction for {task_id}",
        agent=agent or AgentSpec(agent_id=f"agent:{task_id}", runtime_provider="fake"),
        state=state,
        context_scope=ContextScope(context_id=f"context:{lane_id}", lane_id=lane_id),
        edit_lease=edit_lease,
        sandbox_profile=SandboxProfile(profile_id="shared", profile_kind="shared-process"),
        blocked_reason=blocked_reason,
        run_id=run_id,
        output_artifact_id=output_artifact_id,
        output_artifact_ref=output_ref,
    )


def _git_repo(tmp_path: Path) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git executable is required for git-worktree sandbox provider tests")
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# test repo\n", encoding="utf-8")
    (repo / "client").mkdir()
    (repo / "client" / "app.js").write_text("console.log('ok');\n", encoding="utf-8")
    _run_git(repo, "init")
    _run_git(repo, "config", "user.email", "tests@example.invalid")
    _run_git(repo, "config", "user.name", "Doc Based Coding Tests")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-m", "initial")
    return repo


def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ("git", "-C", str(repo), *args),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed with {completed.returncode}: "
            f"{completed.stderr or completed.stdout}"
        )
    return completed


def _host_evidence_summary_fixture(
    evidence_path: Path,
    *,
    evidence_id: str,
    stop_reason: str,
    stop_detail: str = "",
    run_count: int = 1,
    blocked_task_ids: tuple[str, ...] = (),
    failed_task_ids: tuple[str, ...] = (),
    permission_review_task_ids: tuple[str, ...] = (),
    permission_review_count: int = 0,
) -> HostSchedulerRunEvidenceSummary:
    return HostSchedulerRunEvidenceSummary(
        evidence_path=evidence_path,
        evidence_id=evidence_id,
        timestamp="2026-06-18T02:30:00+08:00",
        runtime_providers=("fake",),
        host_invocation={
            "surface": "host-authorized-adapter",
            "invocation_id": evidence_id,
            "requested_by": "host:test",
            "reason": f"{evidence_id} fixture",
        },
        run_count=run_count,
        stop_reason=stop_reason,
        stop_detail=stop_detail,
        ready_task_ids=(),
        blocked_task_ids=blocked_task_ids,
        failed_task_ids=failed_task_ids,
        permission_review_task_ids=permission_review_task_ids,
        permission_review_count=permission_review_count,
        output_artifact_refs=(),
        snapshot_path="scheduler-state.json",
        event_log_path="scheduler-events.jsonl",
        scheduler_projection_path="scheduler-work-trajectory.json",
        authority_split={
            "scheduler_state_authority": "scheduler_snapshot_and_event_log",
            "scheduler_projection_role": "read-only-view",
            "local_work_trajectory_role": "agent-owned",
            "local_work_trajectory_mutated": False,
        },
        history_summary={},
        metadata={},
    )


def _git_worktree_allocation_fixture(
    *,
    cleanup_required: bool,
    cleanup_state: str,
    cleanup_returncode: int | None = None,
    branch_cleanup_returncode: int | None = None,
) -> SandboxAllocation:
    profile = SandboxProfile(
        profile_id="worktree",
        profile_kind="git-worktree",
        network_policy="disabled",
        secret_policy="deny",
        mount_policy="lease-scoped",
    )
    return SandboxAllocation(
        allocation_id="git-worktree:task-1:worktree",
        provider="git-worktree",
        task_id="task-1",
        profile=profile,
        state="allocated",
        workspace_root="E:/workspace/project",
        scratch_path=".codex/scratch/task-1",
        visible_mounts=("README.md", "src/app.py"),
        network_policy=profile.network_policy,
        secret_policy=profile.secret_policy,
        cleanup_required=cleanup_required,
        lease_authorized_mounts=(
            SandboxLeaseMountAuthorization(
                lease_id="lease-1",
                task_id="task-1",
                lifecycle_state="acquired",
                authorized_mounts=("src/app.py",),
                denied_mounts=(),
                reason="lease-scoped mounts authorized by acquired edit lease lease-1",
            ),
        ),
        lease_authorization_state="authorized",
        lease_authorization_reason="lease-scoped mounts authorized by acquired edit lease lease-1",
        git_worktree_receipt=GitWorktreeSandboxReceipt(
            source_repository_root="E:/workspace/project",
            sandbox_root="E:/workspace/sandboxes",
            worktree_path="E:/workspace/sandboxes/task-1-worktree",
            branch_name="dbc-sandbox/task-1-worktree",
            base_ref="HEAD",
            authorized_writable_paths=("src/app.py",),
            denied_writable_paths=(),
            cleanup_state=cleanup_state,
            allocation=GitWorktreeCommandReceipt(
                command=("git", "-C", "E:/workspace/project", "worktree", "add"),
                returncode=0,
                stdout="allocated",
            ),
            cleanup=GitWorktreeCommandReceipt(
                command=("git", "worktree", "remove", "--force")
                if cleanup_returncode is not None
                else (),
                returncode=cleanup_returncode,
            ),
            branch_cleanup=GitWorktreeCommandReceipt(
                command=("git", "branch", "-D")
                if branch_cleanup_returncode is not None
                else (),
                returncode=branch_cleanup_returncode,
            ),
        ),
    )


class _RecordingQoderClient:
    def __init__(self, result: QoderQueryResult) -> None:
        self.result = result
        self.requests: tuple[QoderQueryRequest, ...] = ()

    def query(self, request: QoderQueryRequest) -> QoderQueryResult:
        self.requests = self.requests + (request,)
        return self.result


class _FlakyQoderClient:
    def __init__(self) -> None:
        self.requests: tuple[QoderQueryRequest, ...] = ()

    def query(self, request: QoderQueryRequest) -> QoderQueryResult:
        self.requests = self.requests + (request,)
        if len(self.requests) == 1:
            raise QoderRuntimeError(
                error_kind="timeout",
                summary="temporary outage OPENAI_API_KEY=secret-token",
                retryable=True,
            )
        return QoderQueryResult(
            summary="retried qoder worker complete",
            output_text="ok",
        )


class _RecordingCodexCliClient:
    def __init__(self, result: CodexCliResult | object) -> None:
        self.result = result
        self.requests: tuple[CodexCliRequest, ...] = ()

    def exec(self, request: CodexCliRequest) -> CodexCliResult:
        self.requests = self.requests + (request,)
        if callable(self.result):
            return self.result(request)
        return self.result


class _NeverUsedQoderSDK:
    def access_token_from_env(self):  # pragma: no cover - auth gate fails first
        raise AssertionError("auth helper should not be reached without token")


@pytest.mark.skipif(
    os.environ.get("DBC_PROGRESS_GRAPH_SMOKE_REAL_WORKSPACE") != "1"
    or not DBC_TEST_WORKSPACE.exists(),
    reason="real dbc-test workspace smoke is opt-in to avoid dirtying manual test state",
)
def test_single_line_lifecycle_smoke_writes_user_dbc_test_workspace() -> None:
    start_single_line_trajectory(
        DBC_TEST_WORKSPACE,
        title="DBC Test Single-Line Local Work",
        lane_label="单线闭环",
        first_event_title="生成初始线和第一个节点",
        first_event_kind="start",
        guide_context="design_docs/progress-graph-local-work-trajectory-ui-requirements.md",
        metadata={"test_workspace": DBC_TEST_WORKSPACE.as_posix()},
    )
    append_single_line_event(
        DBC_TEST_WORKSPACE,
        title="生成后续节点",
        kind="task",
    )
    append_single_line_event(
        DBC_TEST_WORKSPACE,
        title="推进节点并进入验证",
        kind="validation",
    )
    advance_single_line_event(DBC_TEST_WORKSPACE)

    trajectory = load_local_work_trajectory(DBC_TEST_WORKSPACE)

    assert trajectory.title == "DBC Test Single-Line Local Work"
    assert list(trajectory.lanes) == ["lane:main"]
    assert [event.status for event in trajectory.events.values()] == [
        "completed",
        "in_progress",
        "pending",
    ]
    assert trajectory.relations[-1].source_event_id == "event:002"
    assert trajectory.relations[-1].target_event_id == "event:003"
