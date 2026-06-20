from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest

from src.mcp.server import create_server
from src.mcp.tools import GovernanceTools
from src.runtime.orchestration import (
    AgentSpec,
    ContextScope,
    EditLeaseLifecycleRecord,
    EditScopeLease,
    JsonArtifactVersionStore,
    JsonExchangeArtifactAdmissionLedger,
    JsonlSchedulerEventLog,
    SchedulerTaskSubmission,
    SchedulerState,
    ScheduledTask,
    build_sandbox_allocation_receipt_evidence,
    read_scheduler_state_snapshot,
    read_sandbox_allocation_receipt_evidence_summary,
    scheduler_task_submission_to_artifact,
    seed_scheduler_operator_dogfood_fixture,
    seed_scheduler_operator_multilane_dogfood_fixture,
    submit_scheduler_task_with_persistence,
    write_sandbox_allocation_receipt_evidence,
    write_scheduler_state_snapshot,
)


def _write_submission_artifact(
    store_path: Path,
    *,
    artifact_id: str,
    task_id: str,
) -> None:
    artifact = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id=task_id,
            title=f"Admit {task_id}",
            instruction="Admit through MCP.",
            agent=AgentSpec(agent_id="agent:mcp-admit", runtime_provider="fake"),
            context_scope=ContextScope(context_id="context:mcp-admit"),
            output_artifact_id=f"{task_id}:result",
        ),
        artifact_id=artifact_id,
        created_at="2026-06-19T05:45:00+08:00",
        version="v1",
    )
    JsonArtifactVersionStore(store_path).put(artifact)


def test_governance_tools_admit_exchange_artifact_uses_ledger_policy(tmp_path: Path) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    ledger_path = tmp_path / ".codex" / "orchestration" / "exchange-artifact-admissions.json"
    snapshot_path = tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = tmp_path / ".codex" / "scheduler" / "scheduler-events.jsonl"
    _write_submission_artifact(
        store_path,
        artifact_id="submission:mcp-admit",
        task_id="task-mcp-admit",
    )
    tools = GovernanceTools(tmp_path, dry_run=True)

    first = tools.admit_exchange_artifact(
        artifact_id="submission:mcp-admit",
        version="v1",
        snapshot_path=str(snapshot_path),
        event_log_path=str(event_log_path),
        actor="agent:guide",
    )
    duplicate = tools.admit_exchange_artifact(
        artifact_id="submission:mcp-admit",
        version="v1",
        snapshot_path=str(snapshot_path),
        event_log_path=str(event_log_path),
        replace_existing=True,
    )

    assert first["ok"] is True
    assert first["submitted_task_ids"] == ["task-mcp-admit"]
    assert first["admission_ledger_record_id"] == "exchange-artifact-admission-1"
    assert first["authority_split"]["provider_executed"] is False
    assert duplicate["ok"] is False
    assert duplicate["status"] == "rejected_duplicate"
    assert duplicate["duplicate_of"] == "exchange-artifact-admission-1"
    assert duplicate["scheduler_state_mutated"] is False
    assert duplicate["event_log_mutated"] is False
    assert len(read_scheduler_state_snapshot(snapshot_path).tasks) == 1
    assert len(JsonlSchedulerEventLog(event_log_path).read_all()) == 1
    records = JsonExchangeArtifactAdmissionLedger(ledger_path).read_all()
    assert [record.status for record in records] == ["admitted", "rejected_duplicate"]


def test_mcp_server_exposes_and_routes_admit_exchange_artifact(tmp_path: Path) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = tmp_path / ".codex" / "scheduler" / "scheduler-events.jsonl"
    _write_submission_artifact(
        store_path,
        artifact_id="submission:server-admit",
        task_id="task-server-admit",
    )
    server = create_server(tmp_path, dry_run=True)

    async def exercise_server() -> None:
        list_result = await server.request_handlers[ListToolsRequest](ListToolsRequest())
        tools = list_result.root.tools
        names = {tool.name for tool in tools}
        assert "admitExchangeArtifact" in names
        admit_tool = next(tool for tool in tools if tool.name == "admitExchangeArtifact")
        assert admit_tool.inputSchema["required"] == [
            "artifactId",
            "version",
            "snapshotPath",
            "eventLogPath",
        ]
        assert "allowDuplicateAdmission" in admit_tool.inputSchema["properties"]
        assert "replaceExisting" in admit_tool.inputSchema["properties"]

        call_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="admitExchangeArtifact",
                    arguments={
                        "artifactId": "submission:server-admit",
                        "version": "v1",
                        "snapshotPath": str(snapshot_path),
                        "eventLogPath": str(event_log_path),
                        "actor": "agent:server",
                    },
                )
            )
        )
        payload = json.loads(call_result.root.content[0].text)
        assert payload["ok"] is True
        assert payload["submitted_task_ids"] == ["task-server-admit"]
        assert payload["admission_ledger_record_id"] == "exchange-artifact-admission-1"

    asyncio.run(exercise_server())


def test_mcp_server_exposes_and_routes_scheduler_operator_workflow(tmp_path: Path) -> None:
    seed_scheduler_operator_multilane_dogfood_fixture(tmp_path)
    server = create_server(tmp_path, dry_run=True)

    async def exercise_server() -> None:
        list_result = await server.request_handlers[ListToolsRequest](ListToolsRequest())
        tools = list_result.root.tools
        names = {tool.name for tool in tools}
        assert "schedulerOperatorWorkflow" in names
        workflow_tool = next(tool for tool in tools if tool.name == "schedulerOperatorWorkflow")
        assert "admit" in workflow_tool.inputSchema["properties"]
        assert "runLoop" in workflow_tool.inputSchema["properties"]
        assert "refreshProjection" in workflow_tool.inputSchema["properties"]

        call_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerOperatorWorkflow",
                    arguments={
                        "artifactId": "fixture:scheduler-operator-multilane-dogfood",
                        "version": "v1",
                        "admit": True,
                        "runLoop": True,
                        "refreshProjection": True,
                        "maxTicks": 4,
                        "maxRunsPerTick": 2,
                        "evidenceId": "mcp-operator-workflow",
                        "timestamp": "2026-06-19T11:45:00+08:00",
                    },
                )
            )
        )
        payload = json.loads(call_result.root.content[0].text)
        assert payload["ok"] is True
        assert payload["admission_result"]["submitted_task_ids"] == [
            "dogfood:api-design",
            "dogfood:data-schema",
            "dogfood:client-integration",
            "dogfood:integration-verify",
        ]
        assert payload["admission_result"]["dependency_count"] == 4
        assert payload["loop_result"]["tick_count"] == 2
        assert payload["loop_result"]["total_run_count"] == 4
        assert payload["projection_result"]["lane_count"] == 4
        assert payload["projection_result"]["event_count"] == 6
        assert payload["host_evidence_presentation"]["card_count"] == 1
        assert payload["authority_split"]["local_work_trajectory_mutated"] is False

    asyncio.run(exercise_server())


def test_governance_tools_scheduler_lifecycle_control_and_run_once(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    control_path = tmp_path / "scheduler-daemon-control.json"
    submit_scheduler_task_with_persistence(
        SchedulerState(),
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-lifecycle-mcp",
                title="Lifecycle MCP task",
                instruction="Complete through lifecycle MCP run-once.",
                agent=AgentSpec(agent_id="agent:lifecycle-mcp", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:lifecycle-mcp"),
                output_artifact_id="task-lifecycle-mcp:result",
            ),
            artifact_id="submission:lifecycle-mcp",
        ),
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-20T00:20:00+00:00",
    )
    tools = GovernanceTools(tmp_path, dry_run=True)

    start = tools.scheduler_lifecycle_control(
        action="start",
        control_path=str(control_path),
        snapshot_path=str(snapshot_path),
        event_log_path=str(event_log_path),
        daemon_id="daemon-mcp",
        run_id="run-mcp",
        timestamp="2026-06-20T00:21:00+00:00",
    )
    paused = tools.scheduler_lifecycle_control(
        action="pause",
        control_path=str(control_path),
        timestamp="2026-06-20T00:22:00+00:00",
    )
    skipped = tools.scheduler_lifecycle_run_once(
        control_path=str(control_path),
        max_ticks=2,
        timestamp="2026-06-20T00:23:00+00:00",
    )
    resumed = tools.scheduler_lifecycle_control(
        action="resume",
        control_path=str(control_path),
        timestamp="2026-06-20T00:24:00+00:00",
    )
    ran = tools.scheduler_lifecycle_run_once(
        control_path=str(control_path),
        max_ticks=2,
        timestamp="2026-06-20T00:25:00+00:00",
    )
    rejected = tools.scheduler_lifecycle_run_once(
        control_path=str(control_path),
        runtime_provider="qoder",
    )

    assert start["ok"] is True
    assert start["control"]["daemon_id"] == "daemon-mcp"
    assert start["control"]["run_id"] == "run-mcp"
    assert paused["state"] == "paused"
    assert skipped["ok"] is True
    assert skipped["skipped"] is True
    assert skipped["authority_split"]["scheduler_state_mutated"] is False
    assert resumed["state"] == "running"
    assert ran["ok"] is True
    assert ran["skipped"] is False
    assert ran["loop"]["total_run_count"] == 1
    assert ran["authority_split"]["provider_executed"] is True
    assert ran["authority_split"]["scheduler_projection_refreshed"] is False
    assert rejected["ok"] is False
    assert rejected["runtime_provider"] == "qoder"
    assert "runtimeProvider='fake' only" in rejected["error"]
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()


def test_mcp_server_exposes_and_routes_scheduler_lifecycle_tools(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    control_path = tmp_path / "scheduler-daemon-control.json"
    submit_scheduler_task_with_persistence(
        SchedulerState(),
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-server-lifecycle",
                title="Server lifecycle task",
                instruction="Complete through server lifecycle tool.",
                agent=AgentSpec(agent_id="agent:server-lifecycle", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:server-lifecycle"),
                output_artifact_id="task-server-lifecycle:result",
            ),
            artifact_id="submission:server-lifecycle",
        ),
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-20T00:30:00+00:00",
    )
    server = create_server(tmp_path, dry_run=True)

    async def exercise_server() -> None:
        list_result = await server.request_handlers[ListToolsRequest](ListToolsRequest())
        tools = list_result.root.tools
        names = {tool.name for tool in tools}
        assert "schedulerLifecycleControl" in names
        assert "schedulerLifecycleRunOnce" in names
        control_tool = next(tool for tool in tools if tool.name == "schedulerLifecycleControl")
        run_tool = next(tool for tool in tools if tool.name == "schedulerLifecycleRunOnce")
        assert control_tool.inputSchema["required"] == ["action", "controlPath"]
        assert "daemonId" in control_tool.inputSchema["properties"]
        assert "local-work-trajectory.json" in control_tool.description
        assert run_tool.inputSchema["required"] == ["controlPath"]
        assert (
            "only 'fake' is accepted"
            in run_tool.inputSchema["properties"]["runtimeProvider"]["description"]
        )
        assert "cancellation is consumed before provider execution" in run_tool.description

        start_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerLifecycleControl",
                    arguments={
                        "action": "start",
                        "controlPath": str(control_path),
                        "snapshotPath": str(snapshot_path),
                        "eventLogPath": str(event_log_path),
                        "daemonId": "daemon-server",
                    },
                )
            )
        )
        start_payload = json.loads(start_result.root.content[0].text)
        assert start_payload["ok"] is True
        assert start_payload["control"]["state"] == "running"

        run_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerLifecycleRunOnce",
                    arguments={
                        "controlPath": str(control_path),
                        "runtimeProvider": "fake",
                        "maxTicks": 2,
                        "timestamp": "2026-06-20T00:31:00+00:00",
                    },
                )
            )
        )
        run_payload = json.loads(run_result.root.content[0].text)
        assert run_payload["ok"] is True
        assert run_payload["skipped"] is False
        assert run_payload["loop"]["total_run_count"] == 1
        assert run_payload["runtime_provider"] == "fake"

    asyncio.run(exercise_server())


def test_mcp_server_exposes_and_routes_scheduler_authorization_readback(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-server-readback": ScheduledTask(
                    task_id="task-server-readback",
                    title="Server readback task",
                    instruction="Inspect lease authorization.",
                    agent=AgentSpec(agent_id="agent:server-readback", runtime_provider="fake"),
                    context_scope=ContextScope(context_id="context:server-readback"),
                    edit_lease=EditScopeLease(
                        lease_id="lease-server-readback",
                        task_id="task-server-readback",
                        allowed_artifacts=("src/app.py",),
                        lease_mode="write",
                    ),
                    output_artifact_id="task-server-readback:result",
                )
            },
            edit_lease_lifecycle={
                "lease-server-readback": EditLeaseLifecycleRecord(
                    lease_id="lease-server-readback",
                    task_id="task-server-readback",
                    state="acquired",
                    mode="write",
                    allowed_artifacts=("src/app.py",),
                    acquired_at="2026-06-21T01:40:00+08:00",
                )
            },
        ),
        snapshot_path,
    )
    server = create_server(tmp_path, dry_run=True)

    async def exercise_server() -> None:
        list_result = await server.request_handlers[ListToolsRequest](ListToolsRequest())
        tools = list_result.root.tools
        names = {tool.name for tool in tools}
        assert "schedulerAuthorizationReadback" in names
        readback_tool = next(tool for tool in tools if tool.name == "schedulerAuthorizationReadback")
        assert readback_tool.inputSchema["required"] == ["snapshotPath"]
        assert "schedulerEventLogPath" in readback_tool.inputSchema["properties"]
        assert "metadata-only shared-process sandbox" in readback_tool.description

        result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerAuthorizationReadback",
                    arguments={
                        "snapshotPath": str(snapshot_path),
                        "workspaceRoot": str(tmp_path),
                    },
                )
            )
        )
        payload = json.loads(result.root.content[0].text)

        assert payload["ok"] is True
        assert payload["product_type"] == "scheduler_authorization_readback"
        assert payload["task_count"] == 1
        assert payload["lifecycle_state_counts"] == {"acquired": 1}
        assert payload["tasks"][0]["sandbox_authorization"]["lease_authorization_state"] == "authorized"
        assert payload["authority_split"]["scheduler_state_mutated"] is False
        assert payload["authority_split"]["runtime_provider_executed"] is False
        assert payload["authority_split"]["local_work_trajectory_mutated"] is False

    asyncio.run(exercise_server())


def test_governance_tools_scheduler_cleanup_receipts_cleans_git_worktree(
    tmp_path: Path,
) -> None:
    repo = _git_repo(tmp_path)
    allocation = _allocated_git_worktree(tmp_path, repo)
    receipt = allocation.git_worktree_receipt
    assert receipt is not None
    input_path = tmp_path / ".codex" / "scheduler" / "evidence" / "allocation.json"
    output_path = tmp_path / ".codex" / "scheduler" / "evidence" / "cleanup.json"
    write_sandbox_allocation_receipt_evidence(
        build_sandbox_allocation_receipt_evidence(
            (allocation,),
            evidence_id="allocation",
            timestamp="2026-06-21T06:40:00+08:00",
            metadata={"surface": "mcp-tools-test"},
        ),
        input_path,
    )
    tools = GovernanceTools(tmp_path, dry_run=True)

    payload = tools.scheduler_cleanup_receipts(
        input_evidence_path=".codex/scheduler/evidence/allocation.json",
        output_evidence_path=".codex/scheduler/evidence/cleanup.json",
        output_evidence_id="cleanup",
        timestamp="2026-06-21T06:45:00+08:00",
    )

    assert payload["ok"] is True
    assert payload["cleaned_allocation_ids"] == ["git-worktree:task-1:worktree"]
    assert payload["authority_split"]["cleanup_executed"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert output_path.exists()
    summary = read_sandbox_allocation_receipt_evidence_summary(output_path)
    cleaned = summary.allocations_by_task_id["task-1"]
    assert cleaned.cleanup_required is False
    assert summary.metadata["surface"] == "mcp:schedulerCleanupReceipts"
    assert not Path(receipt.worktree_path).exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_mcp_server_exposes_and_routes_scheduler_cleanup_receipts(tmp_path: Path) -> None:
    repo = _git_repo(tmp_path)
    allocation = _allocated_git_worktree(tmp_path, repo)
    receipt = allocation.git_worktree_receipt
    assert receipt is not None
    input_path = tmp_path / ".codex" / "scheduler" / "evidence" / "allocation.json"
    output_path = tmp_path / ".codex" / "scheduler" / "evidence" / "cleanup.json"
    write_sandbox_allocation_receipt_evidence(
        build_sandbox_allocation_receipt_evidence(
            (allocation,),
            evidence_id="allocation",
            timestamp="2026-06-21T06:50:00+08:00",
        ),
        input_path,
    )
    server = create_server(tmp_path, dry_run=True)

    async def exercise_server() -> None:
        list_result = await server.request_handlers[ListToolsRequest](ListToolsRequest())
        tools = list_result.root.tools
        names = {tool.name for tool in tools}
        assert "schedulerCleanupReceipts" in names
        cleanup_tool = next(tool for tool in tools if tool.name == "schedulerCleanupReceipts")
        assert cleanup_tool.inputSchema["required"] == ["inputEvidencePath"]
        assert "outputEvidencePath" in cleanup_tool.inputSchema["properties"]
        assert "gitExecutable" in cleanup_tool.inputSchema["properties"]
        assert "local-work-trajectory.json" in cleanup_tool.description

        result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerCleanupReceipts",
                    arguments={
                        "inputEvidencePath": ".codex/scheduler/evidence/allocation.json",
                        "outputEvidencePath": ".codex/scheduler/evidence/cleanup.json",
                        "outputEvidenceId": "cleanup",
                        "timestamp": "2026-06-21T06:55:00+08:00",
                    },
                )
            )
        )
        payload = json.loads(result.root.content[0].text)
        assert payload["ok"] is True
        assert payload["selected_allocation_ids"] == ["git-worktree:task-1:worktree"]
        assert payload["cleaned_allocation_ids"] == ["git-worktree:task-1:worktree"]
        assert payload["authority_split"]["cleanup_executed"] is True
        assert payload["authority_split"]["scheduler_state_mutated"] is False
        assert payload["authority_split"]["local_work_trajectory_mutated"] is False

    asyncio.run(exercise_server())
    summary = read_sandbox_allocation_receipt_evidence_summary(output_path)
    assert summary.allocations_by_task_id["task-1"].cleanup_required is False
    assert not Path(receipt.worktree_path).exists()


def _allocated_git_worktree(project: Path, repo: Path):
    from src.runtime.orchestration import (
        GitWorktreeSandboxProvider,
        SandboxProfile,
        SandboxRequest,
    )

    provider = GitWorktreeSandboxProvider(project / "sandboxes")
    allocation = provider.allocate(
        SandboxRequest(
            task_id="task-1",
            profile=SandboxProfile(
                profile_id="worktree",
                profile_kind="git-worktree",
                network_policy="disabled",
                secret_policy="deny",
                mount_policy="lease-scoped",
            ),
            edit_lease=EditScopeLease(
                lease_id="lease-1",
                task_id="task-1",
                allowed_artifacts=("src/app.py",),
                lease_mode="write",
            ),
            edit_lease_lifecycle=EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-21T06:00:00+08:00",
            ),
            workspace_root=str(repo),
            scratch_path=".codex/scratch/task-1",
            required_mounts=("README.md",),
        )
    )
    assert allocation.state == "allocated"
    assert allocation.cleanup_required is True
    return allocation


def _git_repo(project: Path) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git executable is required for git-worktree cleanup tests")
    repo = project / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# test repo\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
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
