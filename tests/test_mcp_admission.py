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
    ExchangeArtifact,
    ExchangePayloadPart,
    ExchangeReference,
    JsonArtifactVersionStore,
    JsonExchangeArtifactAdmissionLedger,
    JsonlSchedulerEventLog,
    SandboxProfile,
    SchedulerTaskSubmission,
    SchedulerState,
    ScheduledTask,
    SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
    SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
    build_sandbox_allocation_receipt_evidence,
    inspect_exchange_artifact_admission_ledger,
    inspect_exchange_artifact_store,
    read_scheduler_state_snapshot,
    read_sandbox_allocation_receipt_evidence_summary,
    scheduler_task_submission_to_artifact,
    seed_scheduler_operator_binding_consumer_dogfood_fixture,
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


def _write_binding_ref_submission_artifacts(
    store_path: Path,
    *,
    artifact_id: str = "submission:mcp-binding-inspect",
    binding_ref_id: str = "binding:mcp",
) -> None:
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id=binding_ref_id,
            kind="retention",
            intent="inform",
            producer="agent:projection",
            version="v1",
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": binding_ref_id,
                    },
                ),
                ExchangePayloadPart(
                    part_type="storage_manifest",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": binding_ref_id,
                    },
                ),
            ),
        )
    )
    store.put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-mcp-binding-inspect",
                title="MCP binding inspect task",
                instruction="Inspect binding refs through MCP.",
                agent=AgentSpec(agent_id="agent:mcp-binding", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:mcp-binding"),
                input_artifact_refs=(
                    ExchangeReference(
                        ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                        ref_id=binding_ref_id,
                        version="v1",
                    ),
                ),
            ),
            artifact_id=artifact_id,
            version="v1",
        )
    )


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


def test_governance_tools_admit_exchange_artifact_can_mark_consumed(
    tmp_path: Path,
) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = tmp_path / ".codex" / "scheduler" / "scheduler-events.jsonl"
    _write_submission_artifact(
        store_path,
        artifact_id="submission:mcp-consume",
        task_id="task-mcp-consume",
    )
    tools = GovernanceTools(tmp_path, dry_run=True)

    result = tools.admit_exchange_artifact(
        artifact_id="submission:mcp-consume",
        version="v1",
        snapshot_path=str(snapshot_path),
        event_log_path=str(event_log_path),
        mark_consumed_on_success=True,
        actor="agent:mcp",
    )
    bundle = inspect_exchange_artifact_store(store_path).to_json_dict()

    assert result["ok"] is True
    assert result["consumption_state"]["requested"] is True
    assert result["consumption_state"]["consumed"] is True
    assert result["consumption_state"]["actor"] == "agent:mcp"
    assert result["authority_split"]["exchange_store_mutated"] is True
    assert bundle["summaries"][0]["lifecycle_state"] == "consumed"


def test_governance_tools_scheduler_binding_reference_inspect_is_read_only(
    tmp_path: Path,
) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = tmp_path / ".codex" / "scheduler" / "scheduler-events.jsonl"
    _write_binding_ref_submission_artifacts(store_path)
    tools = GovernanceTools(tmp_path, dry_run=True)

    result = tools.scheduler_binding_reference_inspect(
        artifact_id="submission:mcp-binding-inspect",
        version="v1",
    )
    missing = tools.scheduler_binding_reference_inspect(
        artifact_id="submission:missing",
        version="v1",
    )

    assert result["ok"] is True
    assert result["submission_product_type"] == "scheduler_task_submission"
    assert result["task_count"] == 1
    assert result["binding_ref_count"] == 1
    assert result["checked_ref_count"] == 1
    assert result["tasks"][0]["binding_refs"][0]["ref_id"] == "binding:mcp"
    assert result["authority_split"]["scheduler_state_mutated"] is False
    assert result["authority_split"]["exchange_store_mutated"] is False
    assert result["authority_split"]["raw_evidence_json_read"] is False
    assert missing["ok"] is False
    assert "submission:missing" in missing["errors"][0]
    assert not snapshot_path.exists()
    assert not event_log_path.exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_mcp_server_exposes_and_routes_admit_exchange_artifact(tmp_path: Path) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = tmp_path / ".codex" / "scheduler" / "scheduler-events.jsonl"
    _write_submission_artifact(
        store_path,
        artifact_id="submission:server-admit",
        task_id="task-server-admit",
    )
    _write_binding_ref_submission_artifacts(
        store_path,
        artifact_id="submission:server-binding-inspect",
        binding_ref_id="binding:server",
    )
    server = create_server(tmp_path, dry_run=True)

    async def exercise_server() -> None:
        list_result = await server.request_handlers[ListToolsRequest](ListToolsRequest())
        tools = list_result.root.tools
        names = {tool.name for tool in tools}
        assert "admitExchangeArtifact" in names
        assert "schedulerBindingReferenceInspect" in names
        admit_tool = next(tool for tool in tools if tool.name == "admitExchangeArtifact")
        assert admit_tool.inputSchema["required"] == [
            "artifactId",
            "version",
            "snapshotPath",
            "eventLogPath",
        ]
        assert "allowDuplicateAdmission" in admit_tool.inputSchema["properties"]
        assert "replaceExisting" in admit_tool.inputSchema["properties"]
        assert "markConsumedOnSuccess" in admit_tool.inputSchema["properties"]
        inspect_tool = next(
            tool for tool in tools if tool.name == "schedulerBindingReferenceInspect"
        )
        assert inspect_tool.inputSchema["required"] == ["artifactId", "version"]
        assert "artifactStorePath" in inspect_tool.inputSchema["properties"]
        assert "Read-only inspection" in inspect_tool.description
        assert "raw evidence JSON" in inspect_tool.description

        call_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="admitExchangeArtifact",
                    arguments={
                        "artifactId": "submission:server-admit",
                        "version": "v1",
                        "snapshotPath": str(snapshot_path),
                        "eventLogPath": str(event_log_path),
                        "markConsumedOnSuccess": True,
                        "actor": "agent:server",
                    },
                )
            )
        )
        payload = json.loads(call_result.root.content[0].text)
        assert payload["ok"] is True
        assert payload["submitted_task_ids"] == ["task-server-admit"]
        assert payload["admission_ledger_record_id"] == "exchange-artifact-admission-1"
        assert payload["consumption_state"]["consumed"] is True
        assert payload["authority_split"]["exchange_store_mutated"] is True

        inspect_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerBindingReferenceInspect",
                    arguments={
                        "artifactId": "submission:server-binding-inspect",
                        "version": "v1",
                    },
                )
            )
        )
        inspect_payload = json.loads(inspect_result.root.content[0].text)
        assert inspect_payload["ok"] is True
        assert inspect_payload["tasks"][0]["task_id"] == "task-mcp-binding-inspect"
        assert inspect_payload["tasks"][0]["binding_refs"][0]["ref_id"] == "binding:server"
        assert inspect_payload["authority_split"]["scheduler_state_mutated"] is False

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
        assert "inspectBindingRefs" in workflow_tool.inputSchema["properties"]
        assert "runLoop" in workflow_tool.inputSchema["properties"]
        assert "refreshProjection" in workflow_tool.inputSchema["properties"]
        assert "markConsumedOnSuccess" in workflow_tool.inputSchema["properties"]

        call_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerOperatorWorkflow",
                    arguments={
                        "artifactId": "fixture:scheduler-operator-multilane-dogfood",
                        "version": "v1",
                        "admit": True,
                        "markConsumedOnSuccess": True,
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
        assert payload["request"]["mark_consumed_on_success"] is True
        assert payload["admission_result"]["consumption_state"]["consumed"] is True
        assert payload["authority_split"]["exchange_store_mutated"] is True
        assert payload["authority_split"]["local_work_trajectory_mutated"] is False

    asyncio.run(exercise_server())


def test_mcp_scheduler_operator_workflow_inspects_binding_refs(tmp_path: Path) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    _write_binding_ref_submission_artifacts(
        store_path,
        artifact_id="submission:mcp-operator-binding",
        binding_ref_id="binding:mcp-operator",
    )
    server = create_server(tmp_path, dry_run=True)

    async def exercise_server() -> None:
        call_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerOperatorWorkflow",
                    arguments={
                        "artifactId": "submission:mcp-operator-binding",
                        "version": "v1",
                        "inspectBindingRefs": True,
                        "admit": True,
                    },
                )
            )
        )
        payload = json.loads(call_result.root.content[0].text)
        assert payload["ok"] is True
        assert payload["steps"][1]["name"] == "inspectBindingRefs"
        assert payload["steps"][1]["status"] == "completed"
        assert payload["binding_reference_inspection"]["ok"] is True
        assert payload["binding_reference_inspection"]["tasks"][0]["binding_refs"][0][
            "ref_id"
        ] == "binding:mcp-operator"
        assert payload["admission_result"]["submitted_task_ids"] == [
            "task-mcp-binding-inspect",
        ]
        assert payload["authority_split"]["scheduler_state_mutated"] is True
        assert payload["authority_split"]["provider_executed"] is False
        assert payload["authority_split"]["local_work_trajectory_mutated"] is False

    asyncio.run(exercise_server())


def test_mcp_scheduler_operator_workflow_writes_binding_summary_to_ledger(
    tmp_path: Path,
) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    ledger_path = tmp_path / ".codex" / "orchestration" / "exchange-artifact-admissions.json"
    _write_binding_ref_submission_artifacts(
        store_path,
        artifact_id="submission:mcp-ledger-binding",
        binding_ref_id="binding:mcp-ledger",
    )
    server = create_server(tmp_path, dry_run=True)

    async def exercise_server() -> None:
        call_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerOperatorWorkflow",
                    arguments={
                        "artifactId": "submission:mcp-ledger-binding",
                        "version": "v1",
                        "inspectBindingRefs": True,
                        "admit": True,
                    },
                )
            )
        )
        payload = json.loads(call_result.root.content[0].text)
        readback = inspect_exchange_artifact_admission_ledger(
            ledger_path,
            artifact_id="submission:mcp-ledger-binding",
            artifact_version="v1",
        ).to_json_dict()
        summary = readback["records"][0]["binding_reference_summary"]

        assert payload["ok"] is True
        assert payload["admission_result"]["binding_reference_summary"]["ok"] is True
        assert summary["enabled"] is True
        assert summary["ok"] is True
        assert summary["binding_ref_count"] == 1
        assert summary["tasks"][0]["binding_refs"][0]["ref_id"] == "binding:mcp-ledger"
        assert summary["raw_evidence_json_read"] is False

    asyncio.run(exercise_server())


def test_mcp_scheduler_operator_workflow_consumes_binding_consumer_fixture(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex" / "orchestration" / "exchange-artifact-admissions.json"
    seed_scheduler_operator_binding_consumer_dogfood_fixture(
        tmp_path,
        created_at="2026-06-22T02:30:00+08:00",
    )
    server = create_server(tmp_path, dry_run=True)

    async def exercise_server() -> None:
        call_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerOperatorWorkflow",
                    arguments={
                        "artifactId": "fixture:scheduler-operator-binding-consumer-dogfood",
                        "version": "v1",
                        "inspectBindingRefs": True,
                        "admit": True,
                        "timestamp": "2026-06-22T02:40:00+08:00",
                    },
                )
            )
        )
        payload = json.loads(call_result.root.content[0].text)
        readback = inspect_exchange_artifact_admission_ledger(
            ledger_path,
            artifact_id="fixture:scheduler-operator-binding-consumer-dogfood",
            artifact_version="v1",
        ).to_json_dict()
        summary = readback["records"][0]["binding_reference_summary"]

        assert payload["ok"] is True
        candidate_summary = next(
            item for item in payload["candidate_bundle"]["summaries"]
            if item["artifact_id"] == "fixture:scheduler-operator-binding-consumer-dogfood"
        )
        candidate = candidate_summary["admission_candidates"][0]
        assert candidate["binding_reference_readiness"]["ok"] is True
        assert candidate["binding_reference_readiness"]["binding_ref_count"] == 1
        assert payload["binding_reference_inspection"]["ok"] is True
        assert payload["binding_reference_inspection"]["binding_ref_count"] == 1
        assert payload["binding_reference_inspection"]["tasks"][0]["binding_refs"][0][
            "ref_id"
        ] == "fixture:supervisor-storage-binding-dogfood"
        assert payload["admission_result"]["submitted_task_ids"] == [
            "dogfood:binding-consumer",
        ]
        assert payload["admission_result"]["binding_reference_summary"]["enabled"] is True
        assert summary["ok"] is True
        assert summary["binding_ref_count"] == 1
        assert summary["checked_ref_count"] == 1
        assert summary["tasks"][0]["task_id"] == "dogfood:binding-consumer"
        assert summary["raw_evidence_json_read"] is False
        assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()

    asyncio.run(exercise_server())


def test_mcp_server_exposes_and_routes_scheduler_operator_dogfood_closure(
    tmp_path: Path,
) -> None:
    server = create_server(tmp_path, dry_run=True)

    async def exercise_server() -> None:
        list_result = await server.request_handlers[ListToolsRequest](ListToolsRequest())
        tools = list_result.root.tools
        names = {tool.name for tool in tools}
        assert "schedulerOperatorDogfoodClosure" in names
        closure_tool = next(
            tool for tool in tools if tool.name == "schedulerOperatorDogfoodClosure"
        )
        assert "fixture" in closure_tool.inputSchema["properties"]
        assert "inspectBindingRefs" in closure_tool.inputSchema["properties"]
        assert "markConsumedOnSuccess" in closure_tool.inputSchema["properties"]
        assert "runtimeProvider" in closure_tool.inputSchema["properties"]
        assert "Local Work Trajectory" in closure_tool.description

        call_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerOperatorDogfoodClosure",
                    arguments={
                        "timestamp": "2026-06-22T14:10:00+08:00",
                        "createdAt": "2026-06-22T14:09:00+08:00",
                        "maxTicks": 3,
                        "evidenceId": "mcp-operator-dogfood-closure",
                    },
                )
            )
        )
        payload = json.loads(call_result.root.content[0].text)

        assert payload["ok"] is True
        assert payload["workflow_surface"] == "scheduler-operator-dogfood-closure"
        assert payload["request"]["fixture"] == "binding-consumer"
        assert payload["request"]["inspect_binding_refs"] is True
        assert payload["request"]["mark_consumed_on_success"] is True
        assert [step["name"] for step in payload["steps"]] == [
            "seedFixture",
            "operatorWorkflow",
            "readClosureSummary",
        ]
        assert payload["closure_summary"]["artifact_id"] == (
            "fixture:scheduler-operator-binding-consumer-dogfood"
        )
        assert payload["closure_summary"]["binding_summary_ok"] is True
        assert payload["closure_summary"]["consumed"] is True
        assert payload["closure_summary"]["scheduler_projection_event_count"] == 1
        assert payload["workflow_result"]["loop_result"]["total_run_count"] == 1
        assert payload["authority_split"]["exchange_store_mutated"] is True
        assert payload["authority_split"]["admission_ledger_mutated"] is True
        assert payload["authority_split"]["provider_executed"] is True
        assert payload["authority_split"]["local_work_trajectory_mutated"] is False
        assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()

    asyncio.run(exercise_server())


def test_mcp_scheduler_operator_dogfood_closure_rejects_live_provider(
    tmp_path: Path,
) -> None:
    server = create_server(tmp_path, dry_run=True)

    async def exercise_server() -> None:
        call_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerOperatorDogfoodClosure",
                    arguments={"runtimeProvider": "qoder"},
                )
            )
        )
        payload = json.loads(call_result.root.content[0].text)

        assert payload["ok"] is False
        assert payload["workflow_surface"] == "scheduler-operator-dogfood-closure"
        assert payload["runtime_provider"] == "qoder"
        assert "runtimeProvider='fake' only" in payload["error"]
        assert payload["authority_split"]["fixture_seeded"] is False
        assert payload["authority_split"]["exchange_store_mutated"] is False
        assert payload["authority_split"]["scheduler_state_mutated"] is False
        assert payload["authority_split"]["provider_executed"] is False
        assert payload["authority_split"]["local_work_trajectory_mutated"] is False
        assert not (
            tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
        ).exists()
        assert not (
            tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
        ).exists()
        assert not (
            tmp_path / ".codex" / "progress-graph" / "scheduler-work-trajectory.json"
        ).exists()

    asyncio.run(exercise_server())


def test_mcp_exchange_artifacts_bundle_projects_binding_summary(
    tmp_path: Path,
) -> None:
    seed_scheduler_operator_binding_consumer_dogfood_fixture(tmp_path)
    tools = GovernanceTools(tmp_path, dry_run=True)
    workflow = tools.scheduler_operator_workflow(
        artifact_id="fixture:scheduler-operator-binding-consumer-dogfood",
        version="v1",
        inspect_binding_refs=True,
        admit=True,
    )
    bundle_text = tools.read_resource("dbc://exchange-artifacts/bundle")

    assert workflow["ok"] is True
    assert isinstance(bundle_text, str)
    bundle = json.loads(bundle_text)
    summary = next(
        item for item in bundle["summaries"]
        if item["artifact_id"] == "fixture:scheduler-operator-binding-consumer-dogfood"
    )
    candidate = summary["admission_candidates"][0]
    readiness = candidate["binding_reference_readiness"]
    latest = candidate["latest_binding_reference_summary"]

    assert readiness["ok"] is True
    assert readiness["checked_ref_count"] == 1
    assert latest["status"] == "admitted"
    assert latest["ok"] is True
    assert latest["tasks"][0]["binding_refs"][0]["ref_id"] == (
        "fixture:supervisor-storage-binding-dogfood"
    )
    assert latest["raw_evidence_json_read"] is False
    assert "records" not in candidate
    assert "binding" not in latest
    assert bundle["authority_split"]["local_work_trajectory_mutated"] is False


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


def test_governance_tools_scheduler_lifecycle_harness_policy_surface(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    control_path = tmp_path / "scheduler-daemon-control.json"
    missing_control_path = tmp_path / "missing-control.json"
    submit_scheduler_task_with_persistence(
        SchedulerState(),
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-harness-mcp",
                title="Harness MCP task",
                instruction="Complete through lifecycle harness MCP.",
                agent=AgentSpec(agent_id="agent:harness-mcp", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:harness-mcp"),
                output_artifact_id="task-harness-mcp:result",
            ),
            artifact_id="submission:harness-mcp",
        ),
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-21T16:30:00+08:00",
    )
    tools = GovernanceTools(tmp_path, dry_run=True)

    cancelled = tools.scheduler_lifecycle_harness(
        control_path=str(missing_control_path),
        policy_cancelled=True,
        max_attempts=2,
    )
    deadline = tools.scheduler_lifecycle_harness(
        control_path=str(missing_control_path),
        deadline_epoch_seconds=200,
        now_epoch_seconds=200,
    )
    rejected = tools.scheduler_lifecycle_harness(
        control_path=str(control_path),
        runtime_provider="qoder",
    )

    start = tools.scheduler_lifecycle_control(
        action="start",
        control_path=str(control_path),
        snapshot_path=str(snapshot_path),
        event_log_path=str(event_log_path),
        daemon_id="daemon-harness-mcp",
        timestamp="2026-06-21T16:31:00+08:00",
    )
    ran = tools.scheduler_lifecycle_harness(
        control_path=str(control_path),
        max_cycles=2,
        max_ticks=2,
        timestamp="2026-06-21T16:32:00+08:00",
    )

    assert cancelled["ok"] is True
    assert cancelled["stop_reason"] == "cancelled"
    assert cancelled["attempt_count"] == 0
    assert cancelled["policy"]["max_attempts"] == 2
    assert deadline["ok"] is True
    assert deadline["stop_reason"] == "deadline_exceeded"
    assert deadline["attempt_count"] == 0
    assert not missing_control_path.exists()
    assert rejected["ok"] is False
    assert rejected["runtime_provider"] == "qoder"
    assert "runtimeProvider='fake' only" in rejected["error"]
    assert start["ok"] is True
    assert ran["ok"] is True
    assert ran["stop_reason"] == "harness_completed"
    assert ran["attempt_count"] == 1
    assert ran["total_run_count"] == 1
    assert ran["attempts"][0]["harness"]["stop_reason"] == "no_ready_tasks"
    assert ran["runtime_provider"] == "fake"
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-harness-mcp"].state == "complete"
    assert ran["authority_split"]["scheduler_projection_refreshed"] is False
    assert ran["authority_split"]["local_work_trajectory_mutated"] is False
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()


def test_governance_tools_scheduler_lifecycle_harness_retries_policy_stop_reason(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    control_path = tmp_path / "scheduler-daemon-control.json"
    submit_scheduler_task_with_persistence(
        SchedulerState(),
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-harness-retry-mcp",
                title="Harness retry MCP task",
                instruction="Remain proposed while lifecycle is paused.",
                agent=AgentSpec(agent_id="agent:harness-retry-mcp", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:harness-retry-mcp"),
                output_artifact_id="task-harness-retry-mcp:result",
            ),
            artifact_id="submission:harness-retry-mcp",
        ),
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-21T16:40:00+08:00",
    )
    tools = GovernanceTools(tmp_path, dry_run=True)

    tools.scheduler_lifecycle_control(
        action="start",
        control_path=str(control_path),
        snapshot_path=str(snapshot_path),
        event_log_path=str(event_log_path),
        daemon_id="daemon-harness-retry-mcp",
    )
    tools.scheduler_lifecycle_control(
        action="pause",
        control_path=str(control_path),
    )
    result = tools.scheduler_lifecycle_harness(
        control_path=str(control_path),
        max_attempts=2,
        retry_stop_reasons=["paused"],
    )

    assert result["ok"] is True
    assert result["stop_reason"] == "max_attempts_reached"
    assert result["attempt_count"] == 2
    assert [attempt["harness"]["stop_reason"] for attempt in result["attempts"]] == ["paused", "paused"]
    assert all(attempt["retryable"] for attempt in result["attempts"])
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-harness-retry-mcp"].state == "proposed"


def test_governance_tools_scheduler_daemon_supervisor_step_surface(tmp_path: Path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    control_path = tmp_path / "scheduler-daemon-control.json"
    missing_control_path = tmp_path / "missing-control.json"
    submit_scheduler_task_with_persistence(
        SchedulerState(),
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-supervisor-mcp",
                title="Supervisor MCP task",
                instruction="Complete through supervisor MCP.",
                agent=AgentSpec(agent_id="agent:supervisor-mcp", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:supervisor-mcp"),
                output_artifact_id="task-supervisor-mcp:result",
            ),
            artifact_id="submission:supervisor-mcp",
        ),
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-21T17:30:00+08:00",
    )
    tools = GovernanceTools(tmp_path, dry_run=True)

    cancelled = tools.scheduler_daemon_supervisor_step(
        supervisor_id="supervisor-mcp",
        control_path=str(missing_control_path),
        policy_cancelled=True,
        cancellation_source="operator",
        cancellation_reason="manual stop",
        max_attempts=2,
    )
    deadline = tools.scheduler_daemon_supervisor_step(
        supervisor_id="supervisor-mcp",
        control_path=str(missing_control_path),
        deadline_epoch_seconds=200,
        now_epoch_seconds=200,
    )
    rejected = tools.scheduler_daemon_supervisor_step(
        supervisor_id="supervisor-mcp",
        control_path=str(control_path),
        runtime_provider="qoder",
    )
    missing_supervisor = tools.scheduler_daemon_supervisor_step(
        supervisor_id="",
        control_path=str(control_path),
    )

    start = tools.scheduler_lifecycle_control(
        action="start",
        control_path=str(control_path),
        snapshot_path=str(snapshot_path),
        event_log_path=str(event_log_path),
        daemon_id="daemon-supervisor-mcp",
        run_id="lifecycle-run-mcp",
        timestamp="2026-06-21T17:31:00+08:00",
    )
    ran = tools.scheduler_daemon_supervisor_step(
        supervisor_id="supervisor-mcp",
        session_id="session-mcp",
        run_id="supervisor-run-mcp",
        host_id="host-mcp",
        requested_by="agent:test",
        status_readback_at="2026-06-21T17:32:00+08:00",
        control_path=str(control_path),
        max_cycles=2,
        max_ticks=2,
        timestamp="2026-06-21T17:32:00+08:00",
    )

    assert cancelled["ok"] is True
    assert cancelled["stop_reason"] == "cancelled"
    assert cancelled["attempted_harness"] is False
    assert cancelled["attempt_count"] == 0
    assert "cancelled by operator" in cancelled["stop_detail"]
    assert deadline["ok"] is True
    assert deadline["stop_reason"] == "deadline_exceeded"
    assert deadline["attempt_count"] == 0
    assert not missing_control_path.exists()
    assert rejected["ok"] is False
    assert rejected["runtime_provider"] == "qoder"
    assert "runtimeProvider='fake' only" in rejected["error"]
    assert missing_supervisor["ok"] is False
    assert "requires supervisorId" in missing_supervisor["error"]
    assert start["ok"] is True
    assert ran["ok"] is True
    assert ran["supervisor_id"] == "supervisor-mcp"
    assert ran["session_id"] == "session-mcp"
    assert ran["run_id"] == "supervisor-run-mcp"
    assert ran["stop_reason"] == "harness_completed"
    assert ran["attempt_count"] == 1
    assert ran["total_run_count"] == 1
    assert ran["status_before"]["queue_summary"]["task_state_counts"] == {"proposed": 1}
    assert ran["status_after"]["queue_summary"]["task_state_counts"] == {"complete": 1}
    assert ran["harness_policy_result"]["attempts"][0]["harness"]["stop_reason"] == "no_ready_tasks"
    assert ran["runtime_provider"] == "fake"
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-supervisor-mcp"].state == "complete"
    assert ran["authority_split"]["scheduler_projection_refreshed"] is False
    assert ran["authority_split"]["local_work_trajectory_mutated"] is False
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
        assert "schedulerLifecycleHarness" in names
        assert "schedulerDaemonSupervisorStep" in names
        assert "schedulerSupervisorDogfoodWorkflow" in names
        control_tool = next(tool for tool in tools if tool.name == "schedulerLifecycleControl")
        run_tool = next(tool for tool in tools if tool.name == "schedulerLifecycleRunOnce")
        harness_tool = next(tool for tool in tools if tool.name == "schedulerLifecycleHarness")
        supervisor_tool = next(tool for tool in tools if tool.name == "schedulerDaemonSupervisorStep")
        supervisor_workflow_tool = next(
            tool for tool in tools if tool.name == "schedulerSupervisorDogfoodWorkflow"
        )
        assert control_tool.inputSchema["required"] == ["action", "controlPath"]
        assert "daemonId" in control_tool.inputSchema["properties"]
        assert "local-work-trajectory.json" in control_tool.description
        assert run_tool.inputSchema["required"] == ["controlPath"]
        assert (
            "only 'fake' is accepted"
            in run_tool.inputSchema["properties"]["runtimeProvider"]["description"]
        )
        assert "cancellation is consumed before provider execution" in run_tool.description
        assert harness_tool.inputSchema["required"] == ["controlPath"]
        assert "policyCancelled" in harness_tool.inputSchema["properties"]
        assert "deadlineEpochSeconds" in harness_tool.inputSchema["properties"]
        assert "retryStopReasons" in harness_tool.inputSchema["properties"]
        assert "policy-controlled bounded scheduler lifecycle harness" in harness_tool.description
        assert supervisor_tool.inputSchema["required"] == ["supervisorId", "controlPath"]
        assert "sessionId" in supervisor_tool.inputSchema["properties"]
        assert "cancellationSource" in supervisor_tool.inputSchema["properties"]
        assert "statusReadbackAt" in supervisor_tool.inputSchema["properties"]
        assert "policyCancelled" in supervisor_tool.inputSchema["properties"]
        assert "host-managed daemon supervisor step" in supervisor_tool.description
        assert "fixture" in supervisor_workflow_tool.inputSchema["properties"]
        assert "controlPath" in supervisor_workflow_tool.inputSchema["properties"]
        assert "scheduler projection" in supervisor_workflow_tool.description
        assert "local-work-trajectory.json" in supervisor_workflow_tool.description

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

        cancelled_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerLifecycleHarness",
                    arguments={
                        "controlPath": str(tmp_path / "missing-control.json"),
                        "policyCancelled": True,
                        "maxAttempts": 2,
                    },
                )
            )
        )
        cancelled_payload = json.loads(cancelled_result.root.content[0].text)
        assert cancelled_payload["ok"] is True
        assert cancelled_payload["stop_reason"] == "cancelled"
        assert cancelled_payload["attempt_count"] == 0
        assert cancelled_payload["policy"]["max_attempts"] == 2

        supervisor_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerDaemonSupervisorStep",
                    arguments={
                        "supervisorId": "supervisor-server",
                        "controlPath": str(control_path),
                        "runtimeProvider": "fake",
                        "sessionId": "session-server",
                        "runId": "run-server",
                        "statusReadbackAt": "2026-06-20T00:32:00+00:00",
                        "maxTicks": 2,
                        "timestamp": "2026-06-20T00:32:00+00:00",
                    },
                )
            )
        )
        supervisor_payload = json.loads(supervisor_result.root.content[0].text)
        assert supervisor_payload["ok"] is True
        assert supervisor_payload["supervisor_id"] == "supervisor-server"
        assert supervisor_payload["session_id"] == "session-server"
        assert supervisor_payload["runtime_provider"] == "fake"
        assert supervisor_payload["harness_policy_result"]["attempts"][0]["harness"]["stop_reason"] == "no_ready_tasks"
        assert supervisor_payload["status_before"]["lifecycle_state"] == "running"
        assert supervisor_payload["authority_split"]["local_work_trajectory_mutated"] is False

        supervisor_workflow_result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerSupervisorDogfoodWorkflow",
                    arguments={
                        "fixture": "simple",
                        "supervisorId": "supervisor-workflow-server",
                        "sessionId": "session-workflow-server",
                        "runId": "run-workflow-server",
                        "timestamp": "2026-06-20T00:33:00+00:00",
                        "replaceExisting": True,
                    },
                )
            )
        )
        workflow_payload = json.loads(supervisor_workflow_result.root.content[0].text)
        assert workflow_payload["ok"] is True
        assert workflow_payload["runtime_provider"] == "fake"
        assert workflow_payload["workflow_surface"] == "scheduler-supervisor-dogfood-workflow"
        assert workflow_payload["supervisor_result"]["supervisor_id"] == "supervisor-workflow-server"
        assert workflow_payload["supervisor_result"]["session_id"] == "session-workflow-server"
        assert workflow_payload["supervisor_result"]["total_run_count"] == 2
        assert workflow_payload["final_readback"]["queue_summary"]["task_state_counts"] == {
            "complete": 2
        }
        assert workflow_payload["authority_split"]["scheduler_projection_refreshed"] is False
        assert workflow_payload["authority_split"]["cleanup_executed"] is False
        assert workflow_payload["authority_split"]["local_work_trajectory_mutated"] is False

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


def test_mcp_server_exposes_and_routes_scheduler_sandbox_receipt_workflow(
    tmp_path: Path,
) -> None:
    repo = _git_repo(tmp_path)
    snapshot_path = tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = tmp_path / ".codex" / "scheduler" / "scheduler-events.jsonl"
    allocation_path = tmp_path / ".codex" / "scheduler" / "evidence" / "workflow-loop-allocation.json"
    cleanup_path = tmp_path / ".codex" / "scheduler" / "evidence" / "workflow-loop-cleanup.json"
    task = ScheduledTask(
        task_id="task-1",
        title="MCP workflow task",
        instruction="Produce fake runtime output.",
        agent=AgentSpec(agent_id="agent:mcp-workflow", runtime_provider="fake"),
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        sandbox_profile=SandboxProfile(
            profile_id="worktree",
            profile_kind="git-worktree",
            mount_policy="lease-scoped",
        ),
        context_scope=ContextScope(
            context_id="context:mcp-workflow",
            lane_id="lane-main",
            required_refs=(
                ExchangeReference(ref_kind="file", ref_id="readme", path="README.md"),
            ),
        ),
        output_artifact_id="task-1:result",
    )
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={task.task_id: task},
            edit_lease_lifecycle={
                "lease-1": EditLeaseLifecycleRecord(
                    lease_id="lease-1",
                    task_id=task.task_id,
                    state="acquired",
                    mode="write",
                    allowed_artifacts=("src/app.py",),
                    acquired_at="2026-06-21T09:45:00+08:00",
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
        assert "schedulerSandboxReceiptWorkflow" in names
        workflow_tool = next(tool for tool in tools if tool.name == "schedulerSandboxReceiptWorkflow")
        assert "mode" in workflow_tool.inputSchema["required"]
        assert "allocationEvidenceId" in workflow_tool.inputSchema["required"]
        assert "cleanupEvidencePath" in workflow_tool.inputSchema["properties"]
        assert "local-work-trajectory.json" in workflow_tool.description

        result = await server.request_handlers[CallToolRequest](
            CallToolRequest(
                params=CallToolRequestParams(
                    name="schedulerSandboxReceiptWorkflow",
                    arguments={
                        "mode": "daemon-loop",
                        "snapshotPath": ".codex/scheduler/scheduler-state.json",
                        "eventLogPath": ".codex/scheduler/scheduler-events.jsonl",
                        "workspaceRoot": "repo",
                        "gitWorktreeSandboxRoot": "sandboxes",
                        "allocationEvidenceId": "workflow-loop-allocation",
                        "allocationEvidencePath": ".codex/scheduler/evidence/workflow-loop-allocation.json",
                        "cleanup": True,
                        "cleanupEvidenceId": "workflow-loop-cleanup",
                        "cleanupEvidencePath": ".codex/scheduler/evidence/workflow-loop-cleanup.json",
                        "timestamp": "2026-06-21T09:50:00+08:00",
                    },
                )
            )
        )
        payload = json.loads(result.root.content[0].text)
        assert payload["ok"] is True
        assert payload["workflow_mode"] == "daemon_loop"
        assert [step["name"] for step in payload["steps"]] == [
            "runHostSchedulerDaemonLoop",
            "readAllocationEvidence",
            "cleanupReceipts",
            "readCleanupEvidence",
        ]
        assert payload["authority_split"]["host_daemon_loop_executed"] is True
        assert payload["authority_split"]["cleanup_executed"] is True
        assert payload["authority_split"]["local_work_trajectory_mutated"] is False

    asyncio.run(exercise_server())
    cleanup_summary = read_sandbox_allocation_receipt_evidence_summary(cleanup_path)
    cleaned = cleanup_summary.allocations_by_task_id["task-1"]
    assert cleaned.cleanup_required is False
    assert cleaned.git_worktree_receipt is not None
    assert cleaned.git_worktree_receipt.cleanup_state == "completed"
    assert not Path(cleaned.git_worktree_receipt.worktree_path).exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_governance_tools_scheduler_sandbox_receipt_workflow_rejects_cleanup_output_without_cleanup(
    tmp_path: Path,
) -> None:
    tools = GovernanceTools(tmp_path, dry_run=True)

    payload = tools.scheduler_sandbox_receipt_workflow(
        mode="run-once",
        snapshot_path=".codex/scheduler/scheduler-state.json",
        event_log_path=".codex/scheduler/scheduler-events.jsonl",
        workspace_root="repo",
        git_worktree_sandbox_root="sandboxes",
        allocation_evidence_id="workflow-allocation",
        cleanup_evidence_path=".codex/scheduler/evidence/workflow-cleanup.json",
    )

    assert payload["ok"] is False
    assert "cleanup evidence output requires cleanup=True" in payload["error"]
    assert payload["authority_split"]["cleanup_executed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False


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
