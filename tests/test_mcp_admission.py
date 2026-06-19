from __future__ import annotations

import asyncio
import json
from pathlib import Path

from mcp.types import CallToolRequest, CallToolRequestParams, ListToolsRequest

from src.mcp.server import create_server
from src.mcp.tools import GovernanceTools
from src.runtime.orchestration import (
    AgentSpec,
    ContextScope,
    JsonArtifactVersionStore,
    JsonExchangeArtifactAdmissionLedger,
    JsonlSchedulerEventLog,
    SchedulerTaskSubmission,
    read_scheduler_state_snapshot,
    scheduler_task_submission_to_artifact,
    seed_scheduler_operator_dogfood_fixture,
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
    seed_scheduler_operator_dogfood_fixture(tmp_path)
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
                        "artifactId": "fixture:scheduler-operator-dogfood",
                        "version": "v1",
                        "admit": True,
                        "runLoop": True,
                        "refreshProjection": True,
                        "evidenceId": "mcp-operator-workflow",
                        "timestamp": "2026-06-19T11:45:00+08:00",
                    },
                )
            )
        )
        payload = json.loads(call_result.root.content[0].text)
        assert payload["ok"] is True
        assert payload["admission_result"]["submitted_task_ids"] == [
            "dogfood:prepare",
            "dogfood:verify",
        ]
        assert payload["loop_result"]["total_run_count"] == 2
        assert payload["projection_result"]["event_count"] == 2
        assert payload["host_evidence_presentation"]["card_count"] == 1
        assert payload["authority_split"]["local_work_trajectory_mutated"] is False

    asyncio.run(exercise_server())
