"""Tests for MCP governance tools layer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mcp.tools import GovernanceTools
from src.runtime.orchestration import (
    AgentSpec,
    ContextScope,
    ExchangeArtifact,
    ExchangePayloadPart,
    ExchangeRelation,
    ExchangeReference,
    JsonArtifactVersionStore,
    JsonExchangeArtifactAdmissionLedger,
    JsonlSchedulerEventLog,
    JsonlSchedulerMergeGateEventLog,
    SchedulerTaskBatchSubmission,
    SchedulerTaskSubmission,
    ScheduledTask,
    SchedulerEvent,
    SchedulerMergeGate,
    SchedulerState,
    TaskDependency,
    VisibilityPolicy,
    read_scheduler_state_snapshot,
    scheduler_task_batch_submission_to_artifact,
    scheduler_task_submission_to_artifact,
    submit_scheduler_task_batch_with_persistence,
    write_scheduler_state_snapshot,
)
from tools.progress_graph import (
    LocalWorkTrajectory,
    load_local_work_trajectory,
    scheduler_work_trajectory_json_path,
    start_single_line_trajectory,
)

ROOT = Path(__file__).resolve().parent.parent


class TestGovernanceDecide:
    """governance_decide tool tests."""

    def test_decide_allow_on_valid_project(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.governance_decide("这是什么意思？")
        assert result["decision"] == "ALLOW"
        assert result["intent"] == "question"
        assert result["gate"] == "inform"
        assert "envelope" in result
        assert "execution" in result

    def test_decide_block_on_missing_planning_gate(self, tmp_path):
        """Should BLOCK when no planning-gate directory exists in active project."""
        # Create minimal pack structure
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )
        # Add checkpoint so project is NOT in initial state → C5 blocks
        cp_dir = tmp_path / ".codex" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "latest.md").write_text(
            "# Checkpoint\n## Current Phase\nPhase 1\n"
            "## Active Planning Gate\n—\n"
            "## Current Todo\n(none)\n"
            "## Pending User Decision\n(none)\n"
            "## Direction Candidates\n(none)\n"
            "## Key Context Files\n- a.md\n",
            encoding="utf-8",
        )
        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.governance_decide("实现新功能")
        assert result["decision"] == "BLOCK"
        assert "C5" in result["constraint_violated"]
        assert "required_action" in result

    def test_decide_allows_in_initial_state_without_planning_gate(self, tmp_path):
        """In initial state (no checkpoint), C5 warns instead of blocking."""
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )
        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.governance_decide("实现新功能")
        # Should NOT block — initial state → C5 is warn, not block
        assert result["decision"] == "ALLOW"

    def test_decide_correction_is_review(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.governance_decide("请修复这个 bug")
        assert result["decision"] == "ALLOW"
        assert result["intent"] == "correction"
        assert result["gate"] == "review"

    def test_decide_has_audit_count(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.governance_decide("测试")
        assert "audit_event_count" in result
        assert result["audit_event_count"] >= 1

    def test_decide_has_pack_info(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.governance_decide("测试")
        assert "pack_info" in result
        assert "packs" in result["pack_info"]
        # pack_info in governance_decide is a summary (name/version/kind only)
        for p in result["pack_info"]["packs"]:
            assert "name" in p
            assert "version" in p
            assert "kind" in p
        assert "merged_intents" in result["pack_info"]
        assert "merged_gates" in result["pack_info"]

    def test_decide_result_json_serializable(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.governance_decide("测试输入")
        # Must be JSON-serializable for MCP transport
        json.dumps(result, ensure_ascii=False, default=str)


class TestCheckConstraints:
    """check_constraints tool tests."""

    def test_check_constraints_real_project(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.check_constraints()
        assert "violations" in result
        assert "has_blocking" in result
        assert "files_to_reread" in result

    def test_check_constraints_no_blocking_on_valid_project(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.check_constraints()
        assert result["has_blocking"] is False

    def test_check_constraints_finds_key_files(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.check_constraints()
        reread = result["files_to_reread"]
        assert any("Checklist" in f for f in reread)

    def test_check_constraints_includes_checkpoint_file(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.check_constraints()
        assert ".codex/checkpoints/latest.md" in result["files_to_reread"]

    def test_check_constraints_reports_runtime_scope_boundary(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.check_constraints()
        assert result["machine_checked_constraints"][0]["constraint"] == "C4"
        assert any(
            item["constraint"] == "C1"
            for item in result["instruction_layer_constraints"]
        )
        assert result["runtime_enforcement_summary"].startswith(
            "Runtime currently machine-checks C4, C5."
        )

    def test_check_constraints_has_command_and_governance_status(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.check_constraints()
        assert result["command_status"] == "ok"
        assert result["governance_status"] == "passed"
        assert result["blocking_constraints"] == []

    def test_check_constraints_governance_blocked_in_active_project(self, tmp_path):
        """Governance status is blocked when C5 fires in active project."""
        # Add checkpoint so project is NOT in initial state
        cp_dir = tmp_path / ".codex" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "latest.md").write_text(
            "# Checkpoint\n## Current Phase\nPhase 1\n"
            "## Active Planning Gate\n—\n"
            "## Current Todo\n(none)\n"
            "## Pending User Decision\n(none)\n"
            "## Direction Candidates\n(none)\n"
            "## Key Context Files\n- a.md\n",
            encoding="utf-8",
        )
        from src.workflow.pipeline import _check_constraints
        result = _check_constraints(tmp_path)
        d = result.to_dict()
        assert d["command_status"] == "ok"
        assert d["governance_status"] == "blocked"
        assert "C5" in d["blocking_constraints"]

    def test_check_constraints_c5_warn_in_initial_state(self, tmp_path):
        """C5 is warn (not block) in initial state (no checkpoint)."""
        from src.workflow.pipeline import _check_constraints
        result = _check_constraints(tmp_path)
        d = result.to_dict()
        assert d["command_status"] == "ok"
        assert d["governance_status"] == "passed"
        assert d["blocking_constraints"] == []
        # C5 violation exists but as warn
        c5 = [v for v in d["violations"] if v["constraint"] == "C5"]
        assert len(c5) == 1
        assert c5[0]["severity"] == "warn"


class TestWorkspaceDbcCommandRelay:
    """workspaceDbcCommand MCP relay tests."""

    def test_mcp_server_exposes_and_routes_workspace_dbc_command(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "workspaceDbcCommand" in names
            relay_tool = next(tool for tool in tools if tool.name == "workspaceDbcCommand")
            assert relay_tool.inputSchema["required"] == ["argv"]
            assert "mode" in relay_tool.inputSchema["properties"]
            assert "not a generic shell" in relay_tool.description
            assert "global PATH" in relay_tool.description

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="workspaceDbcCommand",
                        arguments={
                            "argv": ["scheduler", "operator-dogfood-closure"],
                            "mode": "read",
                        },
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is False
            assert payload["status"] == "denied"
            assert "requires mode='mutate'" in payload["denied_reason"]
            assert payload["command_preview"][:3][1:] == ["-m", "src"]
            assert payload["authority_split"]["generic_shell"] is False
            assert payload["authority_split"]["workspace_bound"] is True

        asyncio.run(exercise_server())


class TestTrajectoryTeamContinuityMcp:
    """trajectoryTeamContinuity MCP tool tests."""

    def test_tools_method_assign_inspect_and_worker_rejection(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        assign = tools.trajectory_team_continuity(
            action="assign",
            trajectory_id="local-work:mcp-surface",
            lane_id="lane:server",
            leader_id="agent:guide",
            worker_id="worker:server",
            runtime_provider="opencode",
            session_id="session-server",
            compact_context_ref="dbc://context/server",
            mailbox_cursor_ref="dbc://mailbox/server@1",
            worker_report_refs=("report:server",),
            audit_refs=("audit:server",),
            scheduler_event_log_path=".dbc/scheduler/team-events.jsonl",
            timestamp="2026-07-04T12:00:00+00:00",
        )
        inspect = tools.trajectory_team_continuity(
            action="inspect",
            trajectory_id="local-work:mcp-surface",
            lane_id="lane:server",
            runtime_provider="opencode",
        )
        rejected = tools.trajectory_team_continuity(
            action="assign",
            caller_role="worker",
            trajectory_id="local-work:mcp-surface",
            lane_id="lane:client",
            worker_id="worker:client",
        )

        assert assign["ok"] is True
        assert assign["authority_split"]["provider_executed"] is False
        assert assign["authority_split"]["local_work_trajectory_mutated"] is False
        assert inspect["ok"] is True
        assert inspect["rows"][0]["binding_id"] == "continuous-worker:lane:lane-server"
        assert inspect["rows"][0]["worker_report_refs"] == ["report:server"]
        assert rejected["ok"] is False
        assert rejected["status"] == "caller_role_rejected"
        assert "docs/worker-trajectory-update-reporting.md" in rejected["message"]

    def test_mcp_server_exposes_and_routes_trajectory_team_continuity(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "trajectoryTeamContinuity" in names
            tool = next(tool for tool in tools if tool.name == "trajectoryTeamContinuity")
            assert tool.inputSchema["properties"]["action"]["enum"] == [
                "inspect",
                "resolve",
                "assign",
                "activate",
                "suspend",
                "resume",
                "transfer",
                "fork",
                "release",
                "noContinuity",
            ]
            assert "docs/worker-trajectory-update-reporting.md" in tool.description

            assign_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="trajectoryTeamContinuity",
                        arguments={
                            "action": "assign",
                            "trajectoryId": "local-work:mcp-server",
                            "laneId": "lane:server",
                            "leaderId": "agent:guide",
                            "workerId": "worker:server",
                            "runtimeProvider": "opencode",
                            "sessionId": "session-server",
                            "schedulerEventLogPath": ".dbc/scheduler/team-events.jsonl",
                        },
                    )
                )
            )
            assign_payload = json.loads(assign_result.root.content[0].text)
            assert assign_payload["ok"] is True
            assert assign_payload["rows"][0]["worker_id"] == "worker:server"

            inspect_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="trajectoryTeamContinuity",
                        arguments={
                            "action": "inspect",
                            "trajectoryId": "local-work:mcp-server",
                            "laneId": "lane:server",
                            "runtimeProvider": "opencode",
                        },
                    )
                )
            )
            inspect_payload = json.loads(inspect_result.root.content[0].text)
            assert inspect_payload["ok"] is True
            assert inspect_payload["rows"][0]["binding_id"] == (
                "continuous-worker:lane:lane-server"
            )

            worker_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="trajectoryTeamContinuity",
                        arguments={
                            "action": "assign",
                            "callerRole": "worker",
                            "trajectoryId": "local-work:mcp-server",
                            "laneId": "lane:client",
                            "workerId": "worker:client",
                        },
                    )
                )
            )
            worker_payload = json.loads(worker_result.root.content[0].text)
            assert worker_payload["ok"] is False
            assert "Subagent Report.trajectory_update" in worker_payload["message"]
            assert "docs/worker-trajectory-update-reporting.md" in worker_payload["message"]

        asyncio.run(exercise_server())


class TestGetNextAction:
    """get_next_action tool tests."""

    def test_next_action_has_instruction(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.get_next_action()
        assert "instruction" in result
        assert "files_to_reread" in result
        assert isinstance(result["instruction"], str)
        assert len(result["instruction"]) > 0

    def test_next_action_has_phase_info(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.get_next_action()
        assert "current_phase" in result
        assert "runtime_enforcement_summary" in result

    def test_next_action_blocked_project(self, tmp_path):
        """When constraints are violated, instruction says BLOCKED."""
        # Add checkpoint so project is NOT in initial state → C5 blocks
        cp_dir = tmp_path / ".codex" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "latest.md").write_text(
            "# Checkpoint\n## Current Phase\nPhase 1\n"
            "## Active Planning Gate\n—\n"
            "## Current Todo\n(none)\n"
            "## Pending User Decision\n(none)\n"
            "## Direction Candidates\n(none)\n"
            "## Key Context Files\n- a.md\n",
            encoding="utf-8",
        )
        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.get_next_action()
        assert "BLOCKED" in result["instruction"]
        assert result["ask_user"] is False

    def test_next_action_treats_em_dash_planning_gate_as_no_active_gate(self, tmp_path):
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test-pack",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )

        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "closed.md").write_text(
            "# Planning Gate\n\n- Status: **COMPLETED**\n",
            encoding="utf-8",
        )

        cp_dir = tmp_path / ".codex" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "latest.md").write_text(
            "# Checkpoint — 2026-04-10\n"
            "## Current Phase\n"
            "Phase 35\n"
            "## Active Planning Gate\n"
            "—\n"
            "## Current Todo\n"
            "(no todos)\n"
            "## Pending User Decision\n"
            "(none)\n"
            "## Direction Candidates\n"
            "(none)\n"
            "## Key Context Files\n"
            "- a.md\n",
            encoding="utf-8",
        )

        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.get_next_action()
        assert result["active_planning_gate"] == ""
        assert result["ask_user"] is True
        assert result["instruction"].startswith("No active planning gate found.")
        assert "structured_confirmation_tool" not in result["interaction_contract"]
        assert "analysis or recommendation first" in result["question_instruction"]

    def test_next_action_prefers_checklist_hot_state_over_stale_checkpoint(
        self,
        tmp_path,
    ):
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test-pack",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )

        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "old-active.md").write_text(
            "# Old Gate\n\n- Status: **ACTIVE**\n",
            encoding="utf-8",
        )
        latest_gate = gate_dir / "latest-completed.md"
        latest_gate.write_text(
            "# Latest Gate\n\n- Status: **COMPLETED**\n",
            encoding="utf-8",
        )

        checklist = tmp_path / "design_docs" / "Project Master Checklist.md"
        checklist.write_text(
            "# Project Master Checklist\n\n"
            "## Current Snapshot\n\n"
            "- Current Phase: `Post-v1.0 - current hot state`\n"
            "- Current Focus: `Latest completed gate`\n"
            "- Latest Completed Planning Gate:\n"
            "  `design_docs/stages/planning-gate/latest-completed.md`\n",
            encoding="utf-8",
        )
        (tmp_path / "design_docs" / "Global Phase Map and Current Position.md").write_text(
            "# Phase Map\n",
            encoding="utf-8",
        )
        cp_dir = tmp_path / ".codex" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "latest.md").write_text(
            "# Checkpoint — stale\n"
            "## Current Phase\n"
            "Old phase\n"
            "## Active Planning Gate\n"
            "design_docs/stages/planning-gate/old-active.md\n"
            "## Current Todo\n"
            "- stale\n"
            "## Pending User Decision\n"
            "(none)\n"
            "## Direction Candidates\n"
            "(none)\n"
            "## Key Context Files\n"
            "- design_docs/stages/planning-gate/old-active.md\n",
            encoding="utf-8",
        )

        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.get_next_action()

        assert result["state_source"] == "checklist"
        assert result["current_phase"] == "Post-v1.0 - current hot state"
        assert result["active_planning_gate"] == ""
        assert result["ask_user"] is True
        assert result["instruction"].startswith("No active planning gate found.")
        assert "completion_boundary_reminder" in result


class TestWritebackNotify:
    """writeback_notify tool tests."""

    def test_writeback_notify_returns_recommendation(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.writeback_notify("Phase 22 Slice 1 completed")
        assert "phase_completed" in result
        assert "auto_next" in result
        assert "instruction" in result["auto_next"]
        assert "files_to_update" in result["auto_next"]
        assert result["ask_user"] is True
        assert "structured_confirmation_tool" not in result["interaction_contract"]
        assert "analysis or recommendation first" in result["question_instruction"]
        assert result["safe_stop_writeback_bundle"]["bundle_name"] == "safe-stop-writeback"
        assert ".codex/checkpoints/latest.md" in result["safe_stop_writeback_bundle"]["files_to_update"]
        assert ".codex/checkpoints/latest.md" in result["auto_next"]["files_to_update"]

    def test_writeback_notify_includes_pending_gates(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.writeback_notify("test phase")
        # Our project has pending planning gates
        assert "pending_gates" in result["auto_next"]

    def test_writeback_notify_json_serializable(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.writeback_notify("test")
        json.dumps(result, ensure_ascii=False, default=str)

    def test_writeback_notify_only_returns_explicit_open_status_gates(self, tmp_path):
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test-pack",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )

        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "approved.md").write_text(
            "# Planning Gate\n\n- Status: **APPROVED**\n",
            encoding="utf-8",
        )
        (gate_dir / "closed.md").write_text(
            "# Planning Gate\n\n- Status: **CLOSED**\n",
            encoding="utf-8",
        )
        (gate_dir / "legacy-no-status.md").write_text(
            "# Planning Gate Candidate\n\nlegacy doc without status\n",
            encoding="utf-8",
        )
        (gate_dir / "README.md").write_text(
            "# README\n\n- Status: **APPROVED**\n",
            encoding="utf-8",
        )

        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.writeback_notify("test phase")

        assert result["auto_next"]["pending_gates"] == ["approved.md"]

    def test_writeback_notify_updates_checkpoint_when_live(self, tmp_path):
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test-pack",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )

        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "approved.md").write_text(
            "# Planning Gate\n\n- Status: **APPROVED**\n",
            encoding="utf-8",
        )

        cp_dir = tmp_path / ".codex" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "latest.md").write_text(
            "# Checkpoint — 2026-04-10\n"
            "## Current Phase\n"
            "Phase 27\n"
            "## Active Planning Gate\n"
            "design_docs/stages/planning-gate/approved.md\n"
            "## Current Todo\n"
            "(no todos)\n"
            "## Pending User Decision\n"
            "(none)\n"
            "## Direction Candidates\n"
            "(none)\n"
            "## Key Context Files\n"
            "- a.md\n",
            encoding="utf-8",
        )

        tools = GovernanceTools(tmp_path, dry_run=False)
        tools.writeback_notify("Phase 28: remediation completed")

        from src.workflow.checkpoint import read_checkpoint

        data = read_checkpoint(cp_dir / "latest.md")
        assert data["phase"] == "Phase 28: remediation completed"
        assert data["planning_gate"] == ""

    def test_writeback_notify_exposes_safe_stop_bundle_contract(self, tmp_path):
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test-pack",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )

        design_docs = tmp_path / "design_docs"
        design_docs.mkdir(parents=True)
        (design_docs / "direction-candidates-after-phase-35.md").write_text(
            "# Direction\n",
            encoding="utf-8",
        )

        gate_dir = design_docs / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)

        cp_dir = tmp_path / ".codex" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "latest.md").write_text(
            "# Checkpoint — 2026-04-12\n"
            "## Current Phase\n"
            "Phase 35\n"
            "## Active Planning Gate\n"
            "—\n"
            "## Current Todo\n"
            "(no todos)\n"
            "## Pending User Decision\n"
            "(none)\n"
            "## Direction Candidates\n"
            "(none)\n"
            "## Key Context Files\n"
            "- a.md\n",
            encoding="utf-8",
        )

        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.writeback_notify("test safe stop")

        bundle = result["safe_stop_writeback_bundle"]
        required_keys = {step["key"] for step in bundle["required_steps"]}
        assert "generate-canonical-handoff" in required_keys
        assert "sync-direction-candidates" in required_keys
        assert "design_docs/direction-candidates-after-phase-35.md" in bundle["files_to_update"]

    def test_writeback_notify_exposes_current_handoff_footprint(self, tmp_path):
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test-pack",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )

        current = tmp_path / ".codex" / "handoffs" / "CURRENT.md"
        current.parent.mkdir(parents=True, exist_ok=True)
        current.write_text(
            "---\n"
            "source_handoff_id: handoff-current\n"
            "source_path: .codex/handoffs/history/handoff-current.md\n"
            "scope_key: handoff-authority-doc-footprint\n"
            "created_at: 2026-04-15T21:20:00+08:00\n"
            "---\n",
            encoding="utf-8",
        )

        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.writeback_notify("test safe stop")

        assert result["safe_stop_writeback_bundle"]["current_handoff_footprint"] == {
            "handoff_id": "handoff-current",
            "source_path": ".codex/handoffs/history/handoff-current.md",
            "scope_key": "handoff-authority-doc-footprint",
            "created_at": "2026-04-15T21:20:00+08:00",
        }


class TestGetInfo:
    """get_pack_info tool tests."""

    def test_get_info_returns_packs(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.get_info()
        assert "packs" in result
        assert len(result["packs"]) >= 1
        assert result["packs"][0]["name"] == "doc-loop-vibe-coding"

    def test_get_info_has_merged_fields(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.get_info()
        assert "merged_intents" in result
        assert "merged_gates" in result
        assert "merged_document_types" in result
        assert "external_skill_interaction_contract" in result
        assert result["external_skill_interaction_contract"]["reference_implementation"]["family"] == "project-handoff-*"

    def test_get_info_refreshes_after_manifest_change(self, tmp_path):
        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "gate.md").write_text(
            "# Planning Gate\n\n- Status: **ACTIVE**\n",
            encoding="utf-8",
        )

        cp_dir = tmp_path / ".codex" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "latest.md").write_text(
            "# Checkpoint — 2026-04-11\n"
            "## Current Phase\n"
            "Phase 35\n"
            "## Active Planning Gate\n"
            "design_docs/stages/planning-gate/gate.md\n"
            "## Current Todo\n"
            "(no todos)\n"
            "## Pending User Decision\n"
            "(none)\n"
            "## Direction Candidates\n"
            "(none)\n"
            "## Key Context Files\n"
            "- a.md\n",
            encoding="utf-8",
        )

        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        manifest_path = pack_dir / "pack-manifest.json"
        manifest = {
            "name": "test-pack",
            "version": "0.1.0",
            "kind": "official-instance",
            "scope": "Test pack",
            "provides": ["prompts"],
            "document_types": [],
            "intents": ["question"],
            "gates": ["inform"],
            "always_on": [],
            "on_demand": [],
            "depends_on": [],
            "overrides": [],
            "prompts": [],
            "templates": [],
            "validators": [],
            "checks": [],
            "scripts": [],
            "triggers": [],
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        tools = GovernanceTools(tmp_path, dry_run=True, include_site_packages=False)
        first = tools.get_info()
        assert first["packs"][0]["version"] == "0.1.0"
        assert "correction" not in first["merged_intents"]

        manifest["version"] = "0.2.0"
        manifest["intents"] = ["question", "correction"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        second = tools.get_info()
        assert second["packs"][0]["version"] == "0.2.0"
        assert "correction" in second["merged_intents"]


class TestGovernanceOverride:
    """governance_override MCP tool tests."""

    def test_list_empty(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.governance_override("list")
        assert result["overrides"] == []
        assert "C1" in result["overridable_constraints"]

    def test_register_and_list(self, tmp_path):
        (tmp_path / ".codex").mkdir(exist_ok=True)
        tools = GovernanceTools(tmp_path, dry_run=True)
        reg = tools.governance_override(
            "register", constraint="C1", reason="skip question this turn", scope="turn"
        )
        assert reg["registered"] is True
        assert reg["override"]["constraint"] == "C1"

        listed = tools.governance_override("list")
        assert len(listed["overrides"]) == 1

    def test_register_non_overridable_rejected(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.governance_override(
            "register", constraint="C5", reason="bypass gate", scope="session"
        )
        assert result["registered"] is False
        assert "non-overridable" in result["error"]

    def test_revoke(self, tmp_path):
        (tmp_path / ".codex").mkdir(exist_ok=True)
        tools = GovernanceTools(tmp_path, dry_run=True)
        reg = tools.governance_override(
            "register", constraint="C2", reason="test", scope="session"
        )
        oid = reg["override"]["override_id"]

        rev = tools.governance_override("revoke", override_id=oid)
        assert rev["revoked"] is True

        listed = tools.governance_override("list")
        assert len(listed["overrides"]) == 0

    def test_unknown_action(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.governance_override("invalid")
        assert "error" in result

    def test_register_missing_fields(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.governance_override("register")
        assert "error" in result

    def test_override_appears_in_check_constraints(self):
        """Active overrides should show up in check_constraints output."""
        tools = GovernanceTools(ROOT, dry_run=True)
        from src.workflow.temporary_override import revoke_override, save_override

        override = save_override(ROOT, constraint="C1", reason="test appearance", scope="turn")
        try:
            result = tools.check_constraints()
            assert "active_overrides" in result
            assert any(o["constraint"] == "C1" for o in result["active_overrides"])
        finally:
            revoke_override(ROOT, override.override_id)


class TestImpactAnalysis:
    """impact_analysis MCP tool tests."""

    def test_impact_analysis_with_baseline(self):
        """Should return impact result using the real baseline graph."""
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.impact_analysis(
            changed_symbols=["src.interfaces.WorkerBackend"],
        )
        assert "error" not in result
        assert "direct" in result
        assert "transitive" in result
        all_impacted = set(result["direct"] + result["transitive"])
        assert len(all_impacted) >= 4

    def test_impact_analysis_empty_changeset(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.impact_analysis()
        assert result["direct"] == []
        assert result["transitive"] == []

    def test_impact_analysis_no_baseline(self, tmp_path):
        """Should return error when baseline graph is missing."""
        tools = GovernanceTools(ROOT, dry_run=True)
        # Temporarily point to nonexistent root
        tools._project_root = tmp_path
        result = tools.impact_analysis(changed_files=["foo.py"])
        assert "error" in result
        assert "Dependency impact propagation is unavailable" in result["suggestion"]
        assert "project-specific baseline generator" in result["suggestion"]
        assert "fabricate baseline_graph.json" in result["suggestion"]

    def test_impact_analysis_with_files(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.impact_analysis(changed_files=["src/interfaces.py"])
        assert "direct" in result
        # interfaces.py contains multiple symbols, should find dependents
        assert len(result["direct"]) >= 1


class TestCouplingCheck:
    """coupling_check MCP tool tests."""

    def test_coupling_check_file_trigger(self):
        """Should trigger coupling alert for pyproject.toml."""
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.coupling_check(changed_files=["pyproject.toml"])
        assert "alerts" in result
        assert len(result["alerts"]) >= 1
        ids = {a["annotation_id"] for a in result["alerts"]}
        assert "coupling-version-pyproject" in ids

    def test_coupling_check_symbol_trigger(self):
        """Should trigger coupling alert for ErrorInfo symbol."""
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.coupling_check(changed_symbols=["ErrorInfo"])
        assert "alerts" in result
        assert len(result["alerts"]) >= 1
        ids = {a["annotation_id"] for a in result["alerts"]}
        assert "coupling-errorinfo-docs" in ids

    def test_coupling_check_no_match(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.coupling_check(changed_files=["unrelated_file.txt"])
        assert result["alerts"] == []

    def test_coupling_check_no_annotations_file(self, tmp_path):
        """Should return empty alerts when annotations file is missing."""
        tools = GovernanceTools(ROOT, dry_run=True)
        tools._project_root = tmp_path
        result = tools.coupling_check(changed_files=["foo.py"])
        assert result["alerts"] == []

    def test_coupling_check_empty_input(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.coupling_check()
        assert result["alerts"] == []


class TestAnalyzeChanges:
    """analyze_changes unified tool tests."""

    def test_analyze_changes_returns_both_sections(self):
        """Should return both impact and coupling sections."""
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.analyze_changes(
            changed_symbols=["src.interfaces.WorkerBackend"],
        )
        assert "impact" in result
        assert "coupling" in result
        assert "direct" in result["impact"]
        assert "alerts" in result["coupling"]

    def test_analyze_changes_with_files(self):
        """Should propagate changed_files to both sub-tools."""
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.analyze_changes(changed_files=["pyproject.toml"])
        # coupling should fire for pyproject.toml
        assert len(result["coupling"]["alerts"]) >= 1
        ids = {a["annotation_id"] for a in result["coupling"]["alerts"]}
        assert "coupling-version-pyproject" in ids

    def test_analyze_changes_empty_input(self):
        """Empty changeset should return clean results from both."""
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.analyze_changes()
        assert result["impact"]["direct"] == []
        assert result["coupling"]["alerts"] == []

    def test_analyze_changes_max_depth(self):
        """max_depth should be forwarded to impact_analysis."""
        tools = GovernanceTools(ROOT, dry_run=True)
        result_shallow = tools.analyze_changes(
            changed_symbols=["src.interfaces.WorkerBackend"],
            max_depth=1,
        )
        result_deep = tools.analyze_changes(
            changed_symbols=["src.interfaces.WorkerBackend"],
            max_depth=5,
        )
        # deeper propagation should find >= as many nodes
        shallow_count = len(result_shallow["impact"]["direct"]) + len(result_shallow["impact"]["transitive"])
        deep_count = len(result_deep["impact"]["direct"]) + len(result_deep["impact"]["transitive"])
        assert deep_count >= shallow_count

    def test_analyze_changes_no_baseline(self, tmp_path):
        """Missing baseline graph should surface in impact section."""
        tools = GovernanceTools(ROOT, dry_run=True)
        tools._project_root = tmp_path
        result = tools.analyze_changes(changed_files=["foo.py"])
        assert "error" in result["impact"]
        # coupling should still work (returns empty)
        assert result["coupling"]["alerts"] == []

    def test_analyze_changes_symbol_coupling(self):
        """Should detect symbol-based coupling alerts."""
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.analyze_changes(changed_symbols=["ErrorInfo"])
        assert len(result["coupling"]["alerts"]) >= 1
        ids = {a["annotation_id"] for a in result["coupling"]["alerts"]}
        assert "coupling-errorinfo-docs" in ids


def _mcp_scheduler_task(task_id: str, *, lane_id: str = "lane:scheduler", state: str = "complete") -> ScheduledTask:
    return ScheduledTask(
        task_id=task_id,
        title=task_id,
        instruction=f"Run {task_id}",
        agent=AgentSpec(agent_id=f"agent:{task_id}", runtime_provider="fake"),
        context_scope=ContextScope(context_id=f"context:{task_id}", lane_id=lane_id),
        state=state,  # type: ignore[arg-type]
    )


class TestSchedulerSubmitTasks:
    """schedulerSubmitTasks MCP tool tests."""

    def test_scheduler_submit_tasks_writes_snapshot_and_submission_events(self, tmp_path):
        snapshot_path = tmp_path / "scheduler-state.json"
        event_log_path = tmp_path / "scheduler-events.jsonl"
        tools = GovernanceTools(tmp_path, dry_run=True)

        result = tools.scheduler_submit_tasks(
            snapshot_path=str(snapshot_path),
            event_log_path=str(event_log_path),
            batch_id="batch-submit",
            artifact_id="submission:batch-submit",
            timestamp="2026-06-17T06:00:00+08:00",
            tasks=[
                {
                    "taskId": "task-a",
                    "title": "Task A",
                    "instruction": "Prepare A.",
                    "agent": {"agentId": "agent:a", "runtimeProvider": "fake"},
                    "contextScope": {"contextId": "context:a", "laneId": "lane:a"},
                    "outputArtifactId": "task-a:result",
                },
                {
                    "taskId": "task-b",
                    "title": "Task B",
                    "instruction": "Use A.",
                    "agent": {"agentId": "agent:b", "runtimeProvider": "fake"},
                    "contextScope": {"contextId": "context:b", "laneId": "lane:b"},
                    "outputArtifactId": "task-b:result",
                    "dependencies": [
                        {
                            "dependencyId": "dep-a-b",
                            "sourceTaskId": "task-a",
                            "targetTaskId": "task-b",
                            "requiredState": "complete",
                        }
                    ],
                },
            ],
        )

        assert result["ok"] is True
        assert result["snapshot_existed"] is False
        assert result["source_artifact_id"] == "submission:batch-submit"
        assert result["submitted_task_ids"] == ["task-a", "task-b"]
        assert result["submission_event_ids"] == ["scheduler-event-1", "scheduler-event-2"]
        assert result["dependencies_added"] == ["dep-a-b"]
        assert result["task_count"] == 2
        assert result["dependency_count"] == 1
        assert result["state_task_count"] == 2
        assert result["state_dependency_count"] == 1
        assert result["ran_tasks"] is False
        assert result["refreshed_projection"] is False
        assert result["local_trajectory_mutated"] is False
        assert result["source_log"]["timestamp"] == "2026-06-17T06:00:00+08:00"
        assert result["source_log"]["action"] == "scheduler_task_batch_submitted"
        assert result["source_log"]["related_artifact_ids"] == ["submission:batch-submit"]

        restored = read_scheduler_state_snapshot(snapshot_path)
        events = JsonlSchedulerEventLog(event_log_path).read_all()
        assert set(restored.tasks) == {"task-a", "task-b"}
        assert restored.dependencies[0].dependency_id == "dep-a-b"
        assert tuple(event.task_id for event in events) == ("task-a", "task-b")
        assert events[0].timestamp == "2026-06-17T06:00:00+08:00"
        assert events[0].related_artifact_ids == ("submission:batch-submit",)

    def test_scheduler_submit_tasks_accepts_batch_payload_and_existing_snapshot(self, tmp_path):
        snapshot_path = tmp_path / "scheduler-state.json"
        event_log_path = tmp_path / "scheduler-events.jsonl"
        write_scheduler_state_snapshot(
            SchedulerState(tasks={"task-existing": _mcp_scheduler_task("task-existing")}),
            snapshot_path,
        )
        tools = GovernanceTools(tmp_path, dry_run=True)

        result = tools.scheduler_submit_tasks(
            snapshot_path=str(snapshot_path),
            event_log_path=str(event_log_path),
            batch={
                "batch_id": "batch-direct",
                "tasks": [
                    {
                        "task_id": "task-new",
                        "title": "Task New",
                        "instruction": "Add a task to existing state.",
                        "agent": {"agent_id": "agent:new", "runtime_provider": "fake"},
                        "context_scope": {"context_id": "context:new", "lane_id": "lane:new"},
                    }
                ],
            },
        )

        assert result["ok"] is True
        assert result["snapshot_existed"] is True
        assert result["submitted_task_ids"] == ["task-new"]
        assert result["state_task_count"] == 2
        assert result["source_log"]["timestamp"]
        restored = read_scheduler_state_snapshot(snapshot_path)
        assert set(restored.tasks) == {"task-existing", "task-new"}

    def test_scheduler_submit_tasks_reports_missing_or_bad_input(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        missing_snapshot = tools.scheduler_submit_tasks(
            snapshot_path="",
            event_log_path="scheduler-events.jsonl",
            batch_id="batch-x",
            tasks=[],
        )
        missing_log = tools.scheduler_submit_tasks(
            snapshot_path="scheduler-state.json",
            event_log_path="",
            batch_id="batch-x",
            tasks=[],
        )
        empty_tasks = tools.scheduler_submit_tasks(
            snapshot_path="scheduler-state.json",
            event_log_path="scheduler-events.jsonl",
            batch_id="batch-empty",
            tasks=[],
        )
        bad_provider = tools.scheduler_submit_tasks(
            snapshot_path="scheduler-state.json",
            event_log_path="scheduler-events.jsonl",
            batch_id="batch-bad-provider",
            tasks=[
                {
                    "taskId": "task-bad",
                    "title": "Bad provider",
                    "instruction": "Should fail.",
                    "agent": {"agentId": "agent:bad", "runtimeProvider": "unknown"},
                    "contextScope": {"contextId": "context:bad"},
                }
            ],
        )

        assert missing_snapshot["ok"] is False
        assert "requires snapshotPath" in missing_snapshot["error"]
        assert missing_log["ok"] is False
        assert "requires eventLogPath" in missing_log["error"]
        assert empty_tasks["ok"] is False
        assert "requires at least one task" in empty_tasks["error"]
        assert bad_provider["ok"] is False
        assert "unsupported agent.runtime_provider 'unknown'" in bad_provider["error"]

    def test_mcp_server_exposes_and_routes_scheduler_submit_tasks(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        snapshot_path = tmp_path / "scheduler-state.json"
        event_log_path = tmp_path / "scheduler-events.jsonl"
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "schedulerSubmitTasks" in names
            submit_tool = next(tool for tool in tools if tool.name == "schedulerSubmitTasks")
            assert submit_tool.inputSchema["required"] == ["snapshotPath", "eventLogPath"]
            assert "tasks" in submit_tool.inputSchema["properties"]
            assert "replaceExisting" in submit_tool.inputSchema["properties"]
            assert "does not run tasks" in submit_tool.description
            assert "local-work-trajectory.json" in submit_tool.description

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="schedulerSubmitTasks",
                        arguments={
                            "snapshotPath": str(snapshot_path),
                            "eventLogPath": str(event_log_path),
                            "batchId": "batch-server-submit",
                            "timestamp": "2026-06-17T06:10:00+08:00",
                            "tasks": [
                                {
                                    "taskId": "task-server-submit",
                                    "title": "Server submit",
                                    "instruction": "Submit through MCP server.",
                                    "agent": {
                                        "agentId": "agent:server-submit",
                                        "runtimeProvider": "fake",
                                    },
                                    "contextScope": {
                                        "contextId": "context:server-submit",
                                        "laneId": "lane:server-submit",
                                    },
                                }
                            ],
                        },
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["submitted_task_ids"] == ["task-server-submit"]
            assert payload["source_log"]["action"] == "scheduler_task_batch_submitted"
            assert Path(payload["snapshot_path"]).exists()
            assert Path(payload["event_log_path"]).exists()

        asyncio.run(exercise_server())

    def test_scheduler_mcp_submit_project_run_smoke_keeps_authority_split(self, tmp_path):
        snapshot_path = tmp_path / "scheduler-state.json"
        event_log_path = tmp_path / "scheduler-events.jsonl"
        tools = GovernanceTools(tmp_path, dry_run=True)
        start_single_line_trajectory(
            tmp_path,
            first_event_title="agent owned trajectory stays separate",
            lane_label="agent",
        )

        submitted = tools.scheduler_submit_tasks(
            snapshot_path=str(snapshot_path),
            event_log_path=str(event_log_path),
            batch_id="batch-e2e-smoke",
            artifact_id="submission:e2e-smoke",
            timestamp="2026-06-17T06:20:00+08:00",
            tasks=[
                {
                    "taskId": "task-a",
                    "title": "Task A",
                    "instruction": "Complete A.",
                    "agent": {"agentId": "agent:a", "runtimeProvider": "fake"},
                    "contextScope": {"contextId": "context:a", "laneId": "lane:a"},
                    "outputArtifactId": "task-a:result",
                },
                {
                    "taskId": "task-b",
                    "title": "Task B",
                    "instruction": "Complete after A.",
                    "agent": {"agentId": "agent:b", "runtimeProvider": "fake"},
                    "contextScope": {"contextId": "context:b", "laneId": "lane:b"},
                    "outputArtifactId": "task-b:result",
                    "dependencies": [
                        {
                            "dependencyId": "dep-a-b",
                            "sourceTaskId": "task-a",
                            "targetTaskId": "task-b",
                            "requiredState": "complete",
                        }
                    ],
                },
            ],
        )
        projected_before_run = tools.scheduler_projection(
            snapshot_path=str(snapshot_path),
            scheduler_event_log_path=str(event_log_path),
            title="Scheduler Before Run",
        )
        before = LocalWorkTrajectory.from_json(
            Path(projected_before_run["scheduler_projection_path"]).read_text(encoding="utf-8")
        )
        run = tools.scheduler_run_once_and_project(
            snapshot_path=str(snapshot_path),
            event_log_path=str(event_log_path),
            runtime_provider="fake",
            timestamp="2026-06-17T06:21:00+08:00",
            guide_context="scheduler-mcp-e2e-smoke",
        )
        after = LocalWorkTrajectory.from_json(
            Path(run["scheduler_projection_path"]).read_text(encoding="utf-8")
        )
        local = load_local_work_trajectory(tmp_path)
        events = JsonlSchedulerEventLog(event_log_path).read_all()

        assert submitted["ok"] is True
        assert submitted["ran_tasks"] is False
        assert submitted["refreshed_projection"] is False
        assert submitted["local_trajectory_mutated"] is False
        assert projected_before_run["ok"] is True
        assert before.events["scheduler-task:task-a"].status == "pending"
        assert before.events["scheduler-task:task-b"].status == "pending"
        assert run["ok"] is True
        assert run["runtime_provider"] == "fake"
        assert run["runtime_registry_providers"] == ["fake"]
        assert run["run_count"] == 2
        assert run["stop_reason"] == "no_ready_tasks"
        assert after.events["scheduler-task:task-a"].status == "completed"
        assert after.events["scheduler-task:task-b"].status == "completed"
        assert len(events) == 9
        assert events[0].event_kind == "task_submitted"
        assert events[-1].event_kind == "task_completed"
        assert local.trajectory_id == "local-work:single-line-current"
        assert [event.title for event in local.events.values()] == [
            "agent owned trajectory stays separate"
        ]


class TestAdmitExchangeArtifact:
    """admitExchangeArtifact MCP tool tests."""

    def test_admit_exchange_artifact_writes_scheduler_state_and_ledger(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        ledger_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifact-admissions.json"
        snapshot_path = tmp_path / ".dbc" / "scheduler" / "scheduler-state.json"
        event_log_path = tmp_path / ".dbc" / "scheduler" / "scheduler-events.jsonl"
        artifact = scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-mcp-admit",
                title="MCP admitted task",
                instruction="Admit through MCP.",
                agent=AgentSpec(agent_id="agent:mcp-admit", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:mcp-admit", lane_id="lane:mcp"),
                output_artifact_id="task-mcp-admit:result",
            ),
            artifact_id="submission:mcp-admit",
            created_at="2026-06-19T05:00:00+08:00",
            version="v1",
        )
        JsonArtifactVersionStore(store_path).put(artifact)
        start_single_line_trajectory(
            tmp_path,
            first_event_title="agent owned trajectory stays separate",
            lane_label="agent",
        )
        tools = GovernanceTools(tmp_path, dry_run=True)

        result = tools.admit_exchange_artifact(
            artifact_id="submission:mcp-admit",
            version="v1",
            snapshot_path=str(snapshot_path),
            event_log_path=str(event_log_path),
            timestamp="2026-06-19T05:01:00+08:00",
            actor="agent:guide",
        )

        assert result["ok"] is True
        assert result["artifact_store_path"] == str(store_path)
        assert result["admission_ledger_path"] == str(ledger_path)
        assert result["admission_ledger_record_id"] == "exchange-artifact-admission-1"
        assert result["product_type"] == "scheduler_task_submission"
        assert result["source_artifact_id"] == "submission:mcp-admit"
        assert result["source_artifact_version"] == "v1"
        assert result["submitted_task_ids"] == ["task-mcp-admit"]
        assert result["dependency_ids"] == []
        assert result["submission_event_ids"] == ["scheduler-event-1"]
        assert result["state_written"] is True
        assert result["ran_tasks"] is False
        assert result["refreshed_projection"] is False
        assert result["authority_split"]["scheduler_state_mutated"] is True
        assert result["authority_split"]["provider_executed"] is False
        assert result["authority_split"]["local_work_trajectory_mutated"] is False

        restored = read_scheduler_state_snapshot(snapshot_path)
        events = JsonlSchedulerEventLog(event_log_path).read_all()
        ledger_records = JsonExchangeArtifactAdmissionLedger(ledger_path).read_all()
        local = load_local_work_trajectory(tmp_path)
        assert restored.tasks["task-mcp-admit"].title == "MCP admitted task"
        assert [event.event_kind for event in events] == ["task_submitted"]
        assert events[0].timestamp == "2026-06-19T05:01:00+08:00"
        assert ledger_records[0].status == "admitted"
        assert ledger_records[0].actor == "agent:guide"
        assert ledger_records[0].submitted_task_ids == ("task-mcp-admit",)
        assert [event.title for event in local.events.values()] == [
            "agent owned trajectory stays separate"
        ]

    def test_admit_exchange_artifact_rejects_duplicate_before_scheduler_mutation(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        ledger_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifact-admissions.json"
        snapshot_path = tmp_path / ".dbc" / "scheduler" / "scheduler-state.json"
        event_log_path = tmp_path / ".dbc" / "scheduler" / "scheduler-events.jsonl"
        JsonArtifactVersionStore(store_path).put(
            scheduler_task_submission_to_artifact(
                SchedulerTaskSubmission(
                    task_id="task-mcp-dup",
                    title="MCP duplicate task",
                    instruction="Reject duplicate replay.",
                    agent=AgentSpec(agent_id="agent:mcp-dup", runtime_provider="fake"),
                    context_scope=ContextScope(context_id="context:mcp-dup"),
                    output_artifact_id="task-mcp-dup:result",
                ),
                artifact_id="submission:mcp-dup",
                created_at="2026-06-19T05:02:00+08:00",
                version="v1",
            )
        )
        tools = GovernanceTools(tmp_path, dry_run=True)

        first = tools.admit_exchange_artifact(
            artifact_id="submission:mcp-dup",
            version="v1",
            snapshot_path=str(snapshot_path),
            event_log_path=str(event_log_path),
        )
        duplicate = tools.admit_exchange_artifact(
            artifact_id="submission:mcp-dup",
            version="v1",
            snapshot_path=str(snapshot_path),
            event_log_path=str(event_log_path),
            replace_existing=True,
        )

        assert first["ok"] is True
        assert duplicate["ok"] is False
        assert duplicate["status"] == "rejected_duplicate"
        assert duplicate["duplicate_of"] == "exchange-artifact-admission-1"
        assert duplicate["scheduler_state_mutated"] is False
        assert duplicate["event_log_mutated"] is False
        assert "duplicate exact exchange artifact admission rejected" in duplicate["error"]
        assert len(read_scheduler_state_snapshot(snapshot_path).tasks) == 1
        assert len(JsonlSchedulerEventLog(event_log_path).read_all()) == 1
        records = JsonExchangeArtifactAdmissionLedger(ledger_path).read_all()
        assert [record.status for record in records] == ["admitted", "rejected_duplicate"]

    def test_admit_exchange_artifact_allows_explicit_duplicate_admission(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        ledger_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifact-admissions.json"
        snapshot_path = tmp_path / ".dbc" / "scheduler" / "scheduler-state.json"
        event_log_path = tmp_path / ".dbc" / "scheduler" / "scheduler-events.jsonl"
        JsonArtifactVersionStore(store_path).put(
            scheduler_task_submission_to_artifact(
                SchedulerTaskSubmission(
                    task_id="task-mcp-allowed-dup",
                    title="MCP explicit duplicate task",
                    instruction="Allow explicit replay.",
                    agent=AgentSpec(agent_id="agent:mcp-allowed-dup", runtime_provider="fake"),
                    context_scope=ContextScope(context_id="context:mcp-allowed-dup"),
                    output_artifact_id="task-mcp-allowed-dup:result",
                ),
                artifact_id="submission:mcp-allowed-dup",
                created_at="2026-06-19T05:03:00+08:00",
                version="v1",
            )
        )
        tools = GovernanceTools(tmp_path, dry_run=True)

        first = tools.admit_exchange_artifact(
            artifact_id="submission:mcp-allowed-dup",
            version="v1",
            snapshot_path=str(snapshot_path),
            event_log_path=str(event_log_path),
        )
        second = tools.admit_exchange_artifact(
            artifact_id="submission:mcp-allowed-dup",
            version="v1",
            snapshot_path=str(snapshot_path),
            event_log_path=str(event_log_path),
            allow_duplicate_admission=True,
            replace_existing=True,
        )

        assert first["ok"] is True
        assert second["ok"] is True
        assert second["allow_duplicate_admission"] is True
        assert second["admission_ledger_record_id"] == "exchange-artifact-admission-2"
        assert len(JsonlSchedulerEventLog(event_log_path).read_all()) == 2
        records = JsonExchangeArtifactAdmissionLedger(ledger_path).read_all()
        assert [record.status for record in records] == ["admitted", "admitted"]
        assert records[1].allow_duplicate is True

    def test_admit_exchange_artifact_reports_missing_inputs(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        missing_artifact = tools.admit_exchange_artifact(
            artifact_id="",
            version="v1",
            snapshot_path="scheduler-state.json",
            event_log_path="scheduler-events.jsonl",
        )
        missing_version = tools.admit_exchange_artifact(
            artifact_id="submission:missing",
            version="",
            snapshot_path="scheduler-state.json",
            event_log_path="scheduler-events.jsonl",
        )
        missing_snapshot = tools.admit_exchange_artifact(
            artifact_id="submission:missing",
            version="v1",
            snapshot_path="",
            event_log_path="scheduler-events.jsonl",
        )
        missing_log = tools.admit_exchange_artifact(
            artifact_id="submission:missing",
            version="v1",
            snapshot_path="scheduler-state.json",
            event_log_path="",
        )

        assert missing_artifact["ok"] is False
        assert "requires artifactId" in missing_artifact["error"]
        assert missing_version["ok"] is False
        assert "requires version" in missing_version["error"]
        assert missing_snapshot["ok"] is False
        assert "requires snapshotPath" in missing_snapshot["error"]
        assert missing_log["ok"] is False
        assert "requires eventLogPath" in missing_log["error"]

    def test_mcp_server_exposes_and_routes_admit_exchange_artifact(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        snapshot_path = tmp_path / ".dbc" / "scheduler" / "scheduler-state.json"
        event_log_path = tmp_path / ".dbc" / "scheduler" / "scheduler-events.jsonl"
        JsonArtifactVersionStore(store_path).put(
            scheduler_task_submission_to_artifact(
                SchedulerTaskSubmission(
                    task_id="task-server-admit",
                    title="Server admit",
                    instruction="Admit through MCP server.",
                    agent=AgentSpec(agent_id="agent:server-admit", runtime_provider="fake"),
                    context_scope=ContextScope(context_id="context:server-admit"),
                ),
                artifact_id="submission:server-admit",
                created_at="2026-06-19T05:04:00+08:00",
                version="v1",
            )
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
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
            assert "admission ledger" in admit_tool.description
            assert "does not run providers" in admit_tool.description
            assert "local-work-trajectory.json" in admit_tool.description

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
            assert Path(payload["snapshot_path"]).exists()
            assert Path(payload["event_log_path"]).exists()

        asyncio.run(exercise_server())


class TestAgentExchangeMailbox:
    """agentExchangeMailbox MCP tool tests."""

    def test_agent_exchange_mailbox_reads_agent_routes_without_mutation(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        store = JsonArtifactVersionStore(store_path)
        store.put(
            ExchangeArtifact(
                artifact_id="ex-inbox",
                version="v1",
                kind="query",
                intent="ask",
                producer="agent:guide",
                audience=("agent:client",),
                lifecycle_state="proposed",
                parts=(ExchangePayloadPart(part_type="text", text="Please review API v2."),),
            )
        )
        store.put(
            ExchangeArtifact(
                artifact_id="ex-outbox",
                version="v1",
                kind="message",
                intent="inform",
                producer="agent:client",
                parts=(ExchangePayloadPart(part_type="text", text="Client review complete."),),
            )
        )
        store.put(
            ExchangeArtifact(
                artifact_id="ex-related",
                version="v1",
                kind="message",
                intent="inform",
                producer="agent:server",
                parts=(
                    ExchangePayloadPart(
                        part_type="relation",
                        relation=ExchangeRelation(
                            relation_id="rel-client",
                            relation_kind="depends_on",
                            source=ExchangeReference(ref_kind="task", ref_id="task-server"),
                            target=ExchangeReference(ref_kind="agent", ref_id="agent:client"),
                        ),
                    ),
                ),
            )
        )
        store.put(
            ExchangeArtifact(
                artifact_id="ex-sensitive",
                version="v1",
                kind="message",
                intent="inform",
                producer="agent:guide",
                audience=("agent:client",),
                visibility_policy=VisibilityPolicy(
                    audience=("agent:client",),
                    contains_sensitive_content=True,
                    redaction_required=True,
                ),
                parts=(ExchangePayloadPart(part_type="text", text="hidden token"),),
            )
        )
        tools = GovernanceTools(tmp_path, dry_run=True)

        result = tools.agent_exchange_mailbox(agent_id="agent:client")

        assert result["ok"] is True
        assert result["agent_id"] == "agent:client"
        assert result["inbox_count"] == 2
        assert result["outbox_count"] == 1
        assert result["related_count"] == 1
        assert result["actionable_count"] == 1
        assert result["inbox"][0]["artifact_id"] == "ex-inbox"
        assert result["inbox"][0]["actionable"] is True
        assert result["outbox"][0]["artifact_id"] == "ex-outbox"
        assert result["related"][0]["artifact_id"] == "ex-related"
        assert result["inbox"][1]["preview"]["redacted"] is True
        assert "hidden token" not in json.dumps(result, ensure_ascii=False)
        assert result["authority_split"]["read_model_only"] is True
        assert not (tmp_path / ".dbc" / "scheduler").exists()

    def test_mcp_server_exposes_and_routes_agent_exchange_mailbox(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-server-mailbox",
                version="v1",
                kind="query",
                intent="ask",
                producer="agent:guide",
                audience=("agent:client",),
                parts=(ExchangePayloadPart(part_type="text", text="Review this MCP-routed item."),),
            )
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "agentExchangeMailbox" in names
            mailbox_tool = next(tool for tool in tools if tool.name == "agentExchangeMailbox")
            assert mailbox_tool.inputSchema["required"] == ["agentId"]
            assert "artifactStorePath" in mailbox_tool.inputSchema["properties"]
            assert "includeArchived" in mailbox_tool.inputSchema["properties"]
            assert "Sensitive/redaction-required" in mailbox_tool.description
            assert "does not mutate scheduler state" in mailbox_tool.description

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="agentExchangeMailbox",
                        arguments={"agentId": "agent:client"},
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["inbox_count"] == 1
            assert payload["inbox"][0]["artifact_id"] == "ex-server-mailbox"
            assert payload["authority_split"]["exchange_store_mutated"] is False

        asyncio.run(exercise_server())


class TestAgentExchangeHistory:
    """agentExchangeHistory MCP tool/resource tests."""

    def test_agent_exchange_history_reads_causality_logs_without_mutation(self, tmp_path):
        from src.runtime.orchestration import ExchangeCausality, ExchangeLog

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        store = JsonArtifactVersionStore(store_path)
        store.put(
            ExchangeArtifact(
                artifact_id="ex-history-question",
                version="v1",
                kind="query",
                intent="ask",
                producer="agent:guide",
                audience=("agent:client",),
                lifecycle_state="proposed",
                causality=ExchangeCausality(correlation_id="thread:mcp-history"),
                parts=(
                    ExchangePayloadPart(
                        part_type="log",
                        log=ExchangeLog(
                            timestamp="2026-06-22T22:30:00+08:00",
                            actor="agent:guide",
                            action="asked",
                            summary="asked via MCP",
                        ),
                    ),
                ),
            )
        )
        store.put(
            ExchangeArtifact(
                artifact_id="ex-history-answer",
                version="v1",
                kind="message",
                intent="inform",
                producer="agent:client",
                audience=("agent:guide",),
                lifecycle_state="accepted",
                causality=ExchangeCausality(
                    replies_to=("ex-history-question@v1",),
                    caused_by=("ex-history-question@v1",),
                    correlation_id="thread:mcp-history",
                ),
                visibility_policy=VisibilityPolicy(
                    audience=("agent:guide",),
                    contains_sensitive_content=True,
                    redaction_required=True,
                ),
                parts=(
                    ExchangePayloadPart(part_type="text", text="hidden MCP answer"),
                    ExchangePayloadPart(
                        part_type="log",
                        log=ExchangeLog(
                            timestamp="2026-06-22T22:30:01+08:00",
                            actor="agent:client",
                            action="answered",
                            summary="safe MCP answer summary",
                        ),
                    ),
                ),
            )
        )
        tools = GovernanceTools(tmp_path, dry_run=True)

        result = tools.agent_exchange_history(
            agent_id="agent:client",
            correlation_id="thread:mcp-history",
        )

        assert result["ok"] is True
        assert result["artifact_count"] == 2
        assert result["participant_counts"] == {"agent:client": 2, "agent:guide": 2}
        assert result["lifecycle_counts"] == {"accepted": 1, "proposed": 1}
        assert result["causality_edges"][0]["relation_kind"] == "replies_to"
        assert [entry["action"] for entry in result["log_entries"]] == ["asked", "answered"]
        assert result["log_entries"][1]["source_redacted"] is True
        assert "safe MCP answer summary" in json.dumps(result, ensure_ascii=False)
        assert "hidden MCP answer" not in json.dumps(result, ensure_ascii=False)
        assert result["authority_split"]["read_model_only"] is True
        assert not (tmp_path / ".dbc" / "scheduler").exists()

    def test_mcp_server_exposes_and_routes_agent_exchange_history(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server
        from src.runtime.orchestration import ExchangeLog

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-server-history",
                version="v1",
                kind="message",
                intent="inform",
                producer="agent:guide",
                audience=("agent:client",),
                parts=(
                    ExchangePayloadPart(
                        part_type="log",
                        log=ExchangeLog(
                            timestamp="2026-06-22T22:35:00+08:00",
                            actor="agent:guide",
                            action="history_recorded",
                        ),
                    ),
                ),
            )
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "agentExchangeHistory" in names
            history_tool = next(tool for tool in tools if tool.name == "agentExchangeHistory")
            assert "agentId" in history_tool.inputSchema["properties"]
            assert "correlationId" in history_tool.inputSchema["properties"]
            assert "raw sensitive payload" in history_tool.description
            assert "does not mutate scheduler state" in history_tool.description

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="agentExchangeHistory",
                        arguments={"agentId": "agent:client"},
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["artifact_count"] == 1
            assert payload["log_entries"][0]["action"] == "history_recorded"
            assert payload["authority_split"]["exchange_store_mutated"] is False

        asyncio.run(exercise_server())

    def test_agent_exchange_history_resource_is_listed_and_read_only(self, tmp_path):
        from src.runtime.orchestration import ExchangeLog

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-resource-history",
                version="v1",
                kind="message",
                intent="inform",
                producer="agent:guide",
                audience=("agent:client",),
                parts=(
                    ExchangePayloadPart(
                        part_type="log",
                        log=ExchangeLog(
                            timestamp="2026-06-22T22:40:00+08:00",
                            actor="agent:guide",
                            action="resource_history",
                        ),
                    ),
                ),
            )
        )
        tools = GovernanceTools(tmp_path, dry_run=True, include_site_packages=False)

        resource = next(
            item for item in tools.list_resources()
            if item["uri"] == "dbc://agent-exchange/history"
        )
        payload = json.loads(tools.read_resource("dbc://agent-exchange/history"))

        assert resource["name"] == "agent-exchange-history"
        assert resource["mimeType"] == "application/json"
        assert payload["exists"] is True
        assert payload["artifact_count"] == 1
        assert payload["log_entries"][0]["action"] == "resource_history"
        assert payload["authority_split"]["read_model_only"] is True
        assert not (tmp_path / ".dbc" / "scheduler").exists()


class TestAgentExchangeReplyAndTransition:
    """agentExchangeReply / agentExchangeTransition MCP tool tests."""

    def test_agent_exchange_reply_and_transition_round_trip(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-mcp-question",
                version="v1",
                kind="query",
                intent="ask",
                producer="agent:guide",
                audience=("agent:client",),
                lifecycle_state="proposed",
                parts=(ExchangePayloadPart(part_type="text", text="Can you take this MCP task?"),),
            )
        )
        tools = GovernanceTools(tmp_path, dry_run=True)

        reply = tools.agent_exchange_reply(
            source_artifact_id="ex-mcp-question",
            source_version="v1",
            reply_artifact_id="ex-mcp-answer",
            producer="agent:client",
            text="I can take it.",
            structured={"product_type": "agent_reply", "ok": True},
            created_at="2026-06-22T21:35:00+08:00",
        )
        transition = tools.agent_exchange_transition(
            artifact_id="ex-mcp-question",
            version="v1",
            target_state="accepted",
            actor="agent:guide",
            reason="reply accepted",
            timestamp="2026-06-22T21:36:00+08:00",
        )
        mailbox = tools.agent_exchange_mailbox(agent_id="agent:guide")

        assert reply["ok"] is True
        assert reply["reply_artifact_id"] == "ex-mcp-answer"
        assert reply["audience"] == ["agent:guide"]
        assert reply["authority_split"]["exchange_store_mutated"] is True
        assert transition["ok"] is True
        assert transition["previous_lifecycle_state"] == "proposed"
        assert transition["current_lifecycle_state"] == "accepted"
        assert transition["changed"] is True
        assert mailbox["inbox"][0]["artifact_id"] == "ex-mcp-answer"
        assert not (tmp_path / ".dbc" / "scheduler").exists()

    def test_mcp_server_exposes_and_routes_agent_exchange_reply_and_transition(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-server-question",
                version="v1",
                kind="query",
                intent="ask",
                producer="agent:guide",
                audience=("agent:client",),
                lifecycle_state="proposed",
                parts=(ExchangePayloadPart(part_type="text", text="Server route question."),),
            )
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "agentExchangeReply" in names
            assert "agentExchangeTransition" in names
            reply_tool = next(tool for tool in tools if tool.name == "agentExchangeReply")
            transition_tool = next(tool for tool in tools if tool.name == "agentExchangeTransition")
            assert reply_tool.inputSchema["required"] == [
                "sourceArtifactId",
                "sourceVersion",
                "replyArtifactId",
                "producer",
            ]
            assert transition_tool.inputSchema["required"] == [
                "artifactId",
                "version",
                "targetState",
                "actor",
            ]
            assert "local-work-trajectory.json" in reply_tool.description
            assert "local-work-trajectory.json" in transition_tool.description

            reply_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="agentExchangeReply",
                        arguments={
                            "sourceArtifactId": "ex-server-question",
                            "sourceVersion": "v1",
                            "replyArtifactId": "ex-server-answer",
                            "producer": "agent:client",
                            "text": "Server-routed reply.",
                        },
                    )
                )
            )
            transition_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="agentExchangeTransition",
                        arguments={
                            "artifactId": "ex-server-question",
                            "version": "v1",
                            "targetState": "accepted",
                            "actor": "agent:guide",
                        },
                    )
                )
            )
            reply_payload = json.loads(reply_result.root.content[0].text)
            transition_payload = json.loads(transition_result.root.content[0].text)
            assert reply_payload["ok"] is True
            assert reply_payload["reply_artifact_id"] == "ex-server-answer"
            assert transition_payload["ok"] is True
            assert transition_payload["current_lifecycle_state"] == "accepted"

        asyncio.run(exercise_server())


class TestAgentExchangeActionCandidates:
    """agentExchangeActionCandidates MCP tool/resource tests."""

    def test_agent_exchange_action_candidates_reads_without_mutation(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        store = JsonArtifactVersionStore(store_path)
        store.put(
            ExchangeArtifact(
                artifact_id="ex-mcp-action-task",
                version="v1",
                kind="request",
                intent="propose",
                producer="agent:guide",
                audience=("scheduler",),
                lifecycle_state="proposed",
                parts=(
                    ExchangePayloadPart(
                        part_type="structured",
                        data={
                            "product_type": "scheduler_task_submission",
                            "task_id": "task/mcp",
                            "title": "MCP task",
                        },
                    ),
                ),
            )
        )
        store.put(
            ExchangeArtifact(
                artifact_id="ex-mcp-action-review",
                version="v1",
                kind="review",
                intent="require_review",
                producer="agent:client",
                audience=("agent:guide",),
                visibility_policy=VisibilityPolicy(
                    audience=("agent:guide",),
                    contains_sensitive_content=True,
                    redaction_required=True,
                ),
                parts=(
                    ExchangePayloadPart(part_type="text", text="secret MCP review"),
                    ExchangePayloadPart(part_type="structured", data={"secret": "hidden"}),
                ),
            )
        )
        tools = GovernanceTools(tmp_path, dry_run=True)

        result = tools.agent_exchange_action_candidates(
            agent_id="agent:guide",
            candidate_type="review_candidate",
        )

        assert result["ok"] is True
        assert result["candidate_type_counts"] == {"review_candidate": 1}
        assert result["candidates"][0]["artifact_id"] == "ex-mcp-action-review"
        assert result["candidates"][0]["redaction_required"] is True
        assert result["authority_split"]["read_model_only"] is True
        assert result["authority_split"]["scheduler_mutated"] is False
        assert "secret MCP review" not in json.dumps(result, ensure_ascii=False)
        assert "hidden" not in json.dumps(result, ensure_ascii=False)
        assert not (tmp_path / ".dbc" / "scheduler").exists()

    def test_mcp_server_exposes_and_routes_agent_exchange_action_candidates(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-server-action-merge",
                version="v1",
                kind="proposal",
                intent="request_merge",
                producer="agent:client",
                audience=("agent:guide",),
                parts=(
                    ExchangePayloadPart(
                        part_type="relation",
                        relation=ExchangeRelation(
                            relation_id="rel-server-merge",
                            relation_kind="merges_into",
                            source=ExchangeReference(ref_kind="lane", ref_id="lane:client"),
                            target=ExchangeReference(ref_kind="lane", ref_id="lane:main"),
                        ),
                    ),
                ),
            )
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "agentExchangeActionCandidates" in names
            action_tool = next(tool for tool in tools if tool.name == "agentExchangeActionCandidates")
            assert "candidateType" in action_tool.inputSchema["properties"]
            assert "review state" in action_tool.description
            assert "local-work-trajectory.json" in action_tool.description

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="agentExchangeActionCandidates",
                        arguments={"candidateType": "merge_candidate"},
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["candidate_type_counts"] == {"merge_candidate": 1}
            assert payload["candidates"][0]["reasons"] == [
                "intent:request_merge",
                "relation:merges_into",
            ]
            assert payload["authority_split"]["exchange_store_mutated"] is False

        asyncio.run(exercise_server())

    def test_agent_exchange_action_candidates_resource_is_listed_and_read_only(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-resource-action-handoff",
                version="v1",
                kind="handoff",
                intent="inform",
                producer="agent:server",
                audience=("agent:client",),
                parts=(
                    ExchangePayloadPart(
                        part_type="relation",
                        relation=ExchangeRelation(
                            relation_id="rel-resource-hand",
                            relation_kind="hands_off",
                            source=ExchangeReference(ref_kind="agent", ref_id="agent:server"),
                            target=ExchangeReference(ref_kind="agent", ref_id="agent:client"),
                        ),
                    ),
                ),
            )
        )
        tools = GovernanceTools(tmp_path, dry_run=True, include_site_packages=False)

        resource = next(
            item for item in tools.list_resources()
            if item["uri"] == "dbc://agent-exchange/action-candidates"
        )
        payload = json.loads(tools.read_resource("dbc://agent-exchange/action-candidates"))

        assert resource["name"] == "agent-exchange-action-candidates"
        assert resource["mimeType"] == "application/json"
        assert payload["exists"] is True
        assert payload["candidate_type_counts"] == {"handoff_candidate": 1}
        assert payload["candidates"][0]["relation_clues"][0]["relation_kind"] == "hands_off"
        assert payload["authority_split"]["read_model_only"] is True
        assert not (tmp_path / ".dbc" / "scheduler").exists()

    def test_agent_exchange_action_candidate_decide_writes_disposition_only(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-mcp-decision-task",
                version="v1",
                kind="request",
                intent="propose",
                producer="agent:guide",
                audience=("scheduler",),
                lifecycle_state="proposed",
                parts=(
                    ExchangePayloadPart(
                        part_type="structured",
                        data={
                            "product_type": "scheduler_task_submission",
                            "task_id": "task/mcp-decision",
                        },
                    ),
                ),
            )
        )
        tools = GovernanceTools(tmp_path, dry_run=True)

        result = tools.agent_exchange_action_candidate_decide(
            candidate_id="ex-mcp-decision-task@v1:scheduler:0",
            disposition_artifact_id="ex-mcp-decision",
            actor="agent:guide",
            disposition="accept",
            target_surface="admitExchangeArtifact",
            reason="ready",
            timestamp="2026-06-22T23:25:00+08:00",
        )

        assert result["ok"] is True
        assert result["candidate_id"] == "ex-mcp-decision-task@v1:scheduler:0"
        assert result["authority_split"]["scheduler_mutated"] is False
        record = JsonArtifactVersionStore(store_path).get("ex-mcp-decision", "v1")
        structured = next(part for part in record.artifact.parts if part.part_type == "structured")
        assert structured.data["product_type"] == "agent_exchange_action_candidate_disposition"
        assert structured.data["target_surface"] == "admitExchangeArtifact"
        assert not (tmp_path / ".dbc" / "scheduler").exists()

    def test_mcp_server_exposes_and_routes_agent_exchange_action_candidate_decide(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-server-decision-task",
                version="v1",
                kind="request",
                intent="propose",
                producer="agent:guide",
                audience=("scheduler",),
                lifecycle_state="proposed",
                parts=(
                    ExchangePayloadPart(
                        part_type="structured",
                        data={
                            "product_type": "scheduler_task_submission",
                            "task_id": "task/server-decision",
                        },
                    ),
                ),
            )
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "agentExchangeActionCandidateDecide" in names
            decide_tool = next(tool for tool in tools if tool.name == "agentExchangeActionCandidateDecide")
            assert decide_tool.inputSchema["required"] == [
                "candidateId",
                "dispositionArtifactId",
                "actor",
                "disposition",
            ]
            assert "may mutate only" in decide_tool.description
            assert "local-work-trajectory.json" in decide_tool.description

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="agentExchangeActionCandidateDecide",
                        arguments={
                            "candidateId": "ex-server-decision-task@v1:scheduler:0",
                            "dispositionArtifactId": "ex-server-decision",
                            "actor": "agent:guide",
                            "disposition": "accept",
                            "targetSurface": "admitExchangeArtifact",
                        },
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["disposition_artifact_id"] == "ex-server-decision"
            assert payload["authority_split"]["review_state_mutated"] is False

        asyncio.run(exercise_server())

    def test_agent_exchange_accepted_scheduler_candidate_consume_admits_source(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        snapshot_path = tmp_path / ".dbc" / "scheduler" / "scheduler-state.json"
        event_log_path = tmp_path / ".dbc" / "scheduler" / "scheduler-events.jsonl"
        ledger_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifact-admissions.json"
        JsonArtifactVersionStore(store_path).put(
            scheduler_task_submission_to_artifact(
                SchedulerTaskSubmission(
                    task_id="task/mcp-consume",
                    title="MCP consume task",
                    instruction="Run from MCP accepted disposition.",
                    agent=AgentSpec(agent_id="agent:worker", runtime_provider="fake"),
                    context_scope=ContextScope(context_id="context:mcp-consume"),
                ),
                artifact_id="ex-mcp-consume-task",
                version="v1",
                producer="agent:guide",
            )
        )
        tools = GovernanceTools(tmp_path, dry_run=True)
        decision = tools.agent_exchange_action_candidate_decide(
            candidate_id="ex-mcp-consume-task@v1:scheduler:0",
            disposition_artifact_id="ex-mcp-consume-decision",
            actor="agent:guide",
            disposition="accept",
            target_surface="admitExchangeArtifact",
        )

        result = tools.agent_exchange_accepted_scheduler_candidate_consume(
            disposition_artifact_id="ex-mcp-consume-decision",
            disposition_version="v1",
            snapshot_path=str(snapshot_path),
            event_log_path=str(event_log_path),
            admission_ledger_path=str(ledger_path),
            actor="agent:guide",
        )

        assert decision["ok"] is True
        assert result["ok"] is True
        assert result["source_artifact_id"] == "ex-mcp-consume-task"
        assert result["admission_result"]["admission_ledger_record_id"]
        assert result["admission_result"]["submitted_task_ids"] == ["task/mcp-consume"]
        assert result["authority_split"]["scheduler_mutated"] is True
        assert read_scheduler_state_snapshot(snapshot_path).tasks["task/mcp-consume"].task_id == "task/mcp-consume"

    def test_agent_exchange_accepted_review_candidate_consume_registers_review(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-mcp-review",
                version="v1",
                kind="review",
                intent="require_review",
                producer="agent:worker",
                audience=("agent:guide",),
                parts=(
                    ExchangePayloadPart(
                        part_type="structured",
                        data={
                            "reason": "review MCP artifact",
                            "open_items": ["Check MCP review intake."],
                        },
                    ),
                ),
            )
        )
        tools = GovernanceTools(tmp_path, dry_run=True)
        decision = tools.agent_exchange_action_candidate_decide(
            candidate_id="ex-mcp-review@v1:review",
            disposition_artifact_id="ex-mcp-review-decision",
            actor="agent:guide",
            disposition="accept",
            target_surface="reviewIntake",
        )

        result = tools.agent_exchange_accepted_review_candidate_consume(
            disposition_artifact_id="ex-mcp-review-decision",
            disposition_version="v1",
            actor="agent:guide",
        )

        assert decision["ok"] is True
        assert result["ok"] is True
        assert result["source_artifact_id"] == "ex-mcp-review"
        assert result["dispatch_result"]["consumer_kind"] == "review_intake"
        assert result["review_pending"][0]["envelope_id"] == "agent-exchange-review-ex-mcp-review-v1"
        assert result["authority_split"]["review_state_mutated"] is True
        assert result["authority_split"]["scheduler_mutated"] is False

    def test_agent_exchange_accepted_handoff_candidate_consume_writes_handoff(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        handoff_dir = tmp_path / ".codex" / "handoffs"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-mcp-handoff",
                version="v1",
                kind="handoff",
                intent="inform",
                producer="agent:worker",
                audience=("agent:guide",),
                parts=(
                    ExchangePayloadPart(
                        part_type="structured",
                        data={
                            "reason": "handoff MCP artifact",
                            "to_role": "agent:guide",
                            "open_items": ["Check MCP handoff delivery."],
                        },
                    ),
                    ExchangePayloadPart(
                        part_type="relation",
                        relation=ExchangeRelation(
                            relation_id="rel-mcp-handoff",
                            relation_kind="hands_off",
                            source=ExchangeReference(ref_kind="agent", ref_id="agent:worker"),
                            target=ExchangeReference(ref_kind="agent", ref_id="agent:guide"),
                        ),
                    ),
                ),
            )
        )
        tools = GovernanceTools(tmp_path, dry_run=True)
        decision = tools.agent_exchange_action_candidate_decide(
            candidate_id="ex-mcp-handoff@v1:handoff",
            disposition_artifact_id="ex-mcp-handoff-decision",
            actor="agent:guide",
            disposition="accept",
            target_surface="handoffIntake",
        )

        result = tools.agent_exchange_accepted_handoff_candidate_consume(
            disposition_artifact_id="ex-mcp-handoff-decision",
            disposition_version="v1",
            handoff_dir=str(handoff_dir),
            actor="agent:guide",
        )

        assert decision["ok"] is True
        assert result["ok"] is True
        assert result["source_artifact_id"] == "ex-mcp-handoff"
        assert result["dispatch_result"]["consumer_kind"] == "handoff"
        assert result["authority_split"]["handoff_mutated"] is True
        handoff_path = handoff_dir / f"{result['handoff_payload']['handoff_id']}.json"
        assert handoff_path.exists()

    def test_agent_exchange_accepted_merge_candidate_consume_resolves_gate(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        snapshot_path = tmp_path / ".dbc" / "scheduler" / "scheduler-state.json"
        merge_log_path = tmp_path / ".dbc" / "scheduler" / "merge-gate-events.jsonl"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-mcp-merge",
                version="v1",
                kind="proposal",
                intent="request_merge",
                producer="agent:worker",
                audience=("agent:guide",),
                parts=(
                    ExchangePayloadPart(
                        part_type="relation",
                        relation=ExchangeRelation(
                            relation_id="rel-mcp-merge",
                            relation_kind="merges_into",
                            source=ExchangeReference(ref_kind="lane", ref_id="lane:worker"),
                            target=ExchangeReference(ref_kind="lane", ref_id="lane:main"),
                        ),
                    ),
                ),
            )
        )
        write_scheduler_state_snapshot(
            SchedulerState(
                tasks={
                    "task-c": ScheduledTask(
                        task_id="task-c",
                        title="C",
                        instruction="merge target",
                        agent=AgentSpec(agent_id="agent:c", runtime_provider="fake"),
                        state="waiting",
                    ),
                },
                merge_gates=(
                    SchedulerMergeGate(
                        gate_id="merge-mcp",
                        title="MCP merge",
                        target_task_id="task-c",
                        state="review_required",
                        gate_kind="review",
                        required_review=True,
                    ),
                ),
            ),
            snapshot_path,
        )
        tools = GovernanceTools(tmp_path, dry_run=True)
        decision = tools.agent_exchange_action_candidate_decide(
            candidate_id="ex-mcp-merge@v1:merge",
            disposition_artifact_id="ex-mcp-merge-decision",
            actor="agent:guide",
            disposition="accept",
            target_surface="mergeIntake",
        )

        result = tools.agent_exchange_accepted_merge_candidate_consume(
            disposition_artifact_id="ex-mcp-merge-decision",
            disposition_version="v1",
            snapshot_path=str(snapshot_path),
            merge_gate_event_log_path=str(merge_log_path),
            gate_id="merge-mcp",
            approved=True,
            reason="MCP approved merge",
            actor="agent:guide",
        )

        assert decision["ok"] is True
        assert result["ok"] is True
        assert result["current_gate_state"] == "complete"
        assert result["authority_split"]["merge_gate_mutated"] is True
        assert read_scheduler_state_snapshot(snapshot_path).merge_gates[0].state == "complete"

    def test_agent_exchange_accepted_blocker_candidate_consume_blocks_task(self, tmp_path):
        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        snapshot_path = tmp_path / ".dbc" / "scheduler" / "scheduler-state.json"
        event_log_path = tmp_path / ".dbc" / "scheduler" / "scheduler-events.jsonl"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-mcp-blocker",
                version="v1",
                kind="blocker",
                intent="declare_blocked",
                producer="agent:worker",
                audience=("agent:guide",),
                parts=(
                    ExchangePayloadPart(
                        part_type="relation",
                        relation=ExchangeRelation(
                            relation_id="rel-mcp-blocker",
                            relation_kind="blocks",
                            source=ExchangeReference(ref_kind="task", ref_id="task-blocked"),
                            target=ExchangeReference(ref_kind="task", ref_id="task-upstream"),
                        ),
                    ),
                ),
            )
        )
        write_scheduler_state_snapshot(
            SchedulerState(
                tasks={
                    "task-blocked": ScheduledTask(
                        task_id="task-blocked",
                        title="Blocked",
                        instruction="block me",
                        agent=AgentSpec(agent_id="agent:b", runtime_provider="fake"),
                        state="waiting",
                    ),
                },
            ),
            snapshot_path,
        )
        tools = GovernanceTools(tmp_path, dry_run=True)
        decision = tools.agent_exchange_action_candidate_decide(
            candidate_id="ex-mcp-blocker@v1:blocker",
            disposition_artifact_id="ex-mcp-blocker-decision",
            actor="agent:guide",
            disposition="accept",
            target_surface="blockerState",
        )

        result = tools.agent_exchange_accepted_blocker_candidate_consume(
            disposition_artifact_id="ex-mcp-blocker-decision",
            disposition_version="v1",
            snapshot_path=str(snapshot_path),
            event_log_path=str(event_log_path),
            task_id="task-blocked",
            reason="MCP accepted blocker",
            actor="agent:guide",
        )

        assert decision["ok"] is True
        assert result["ok"] is True
        assert result["current_task_state"] == "blocked"
        assert result["authority_split"]["blocker_state_mutated"] is True
        assert read_scheduler_state_snapshot(snapshot_path).tasks["task-blocked"].blocked_reason == (
            "MCP accepted blocker"
        )

    def test_mcp_server_exposes_and_routes_accepted_scheduler_candidate_consume(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            scheduler_task_submission_to_artifact(
                SchedulerTaskSubmission(
                    task_id="task/server-consume",
                    title="Server consume task",
                    instruction="Run from server accepted disposition.",
                    agent=AgentSpec(agent_id="agent:worker", runtime_provider="fake"),
                    context_scope=ContextScope(context_id="context:server-consume"),
                ),
                artifact_id="ex-server-consume-task",
                version="v1",
                producer="agent:guide",
            )
        )
        GovernanceTools(tmp_path, dry_run=True).agent_exchange_action_candidate_decide(
            candidate_id="ex-server-consume-task@v1:scheduler:0",
            disposition_artifact_id="ex-server-consume-decision",
            actor="agent:guide",
            disposition="accept",
            target_surface="admitExchangeArtifact",
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "agentExchangeAcceptedSchedulerCandidateConsume" in names
            consume_tool = next(
                tool for tool in tools
                if tool.name == "agentExchangeAcceptedSchedulerCandidateConsume"
            )
            assert consume_tool.inputSchema["required"] == [
                "dispositionArtifactId",
                "dispositionVersion",
                "snapshotPath",
                "eventLogPath",
            ]
            assert "admission ledger" in consume_tool.description
            assert "local-work-trajectory.json" in consume_tool.description

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="agentExchangeAcceptedSchedulerCandidateConsume",
                        arguments={
                            "dispositionArtifactId": "ex-server-consume-decision",
                            "dispositionVersion": "v1",
                            "snapshotPath": ".dbc/scheduler/scheduler-state.json",
                            "eventLogPath": ".dbc/scheduler/scheduler-events.jsonl",
                        },
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["admission_result"]["admission_ledger_record_id"]
            assert payload["admission_result"]["submitted_task_ids"] == ["task/server-consume"]
            assert payload["authority_split"]["handoff_mutated"] is False

        asyncio.run(exercise_server())

    def test_mcp_server_exposes_and_routes_accepted_review_candidate_consume(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-server-review-consume",
                version="v1",
                kind="review",
                intent="require_review",
                producer="agent:worker",
                audience=("agent:guide",),
                parts=(
                    ExchangePayloadPart(
                        part_type="structured",
                        data={"open_items": ["Server route review intake."]},
                    ),
                ),
            )
        )
        GovernanceTools(tmp_path, dry_run=True).agent_exchange_action_candidate_decide(
            candidate_id="ex-server-review-consume@v1:review",
            disposition_artifact_id="ex-server-review-consume-decision",
            actor="agent:guide",
            disposition="accept",
            target_surface="reviewIntake",
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "agentExchangeAcceptedReviewCandidateConsume" in names
            consume_tool = next(
                tool for tool in tools
                if tool.name == "agentExchangeAcceptedReviewCandidateConsume"
            )
            assert consume_tool.inputSchema["required"] == [
                "dispositionArtifactId",
                "dispositionVersion",
            ]
            assert "review intake" in consume_tool.description
            assert "local-work-trajectory.json" in consume_tool.description

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="agentExchangeAcceptedReviewCandidateConsume",
                        arguments={
                            "dispositionArtifactId": "ex-server-review-consume-decision",
                            "dispositionVersion": "v1",
                        },
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["source_artifact_id"] == "ex-server-review-consume"
            assert payload["review_pending"][0]["envelope_id"] == (
                "agent-exchange-review-ex-server-review-consume-v1"
            )
            assert payload["authority_split"]["handoff_mutated"] is False

        asyncio.run(exercise_server())

    def test_mcp_server_exposes_and_routes_accepted_handoff_candidate_consume(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-server-handoff-consume",
                version="v1",
                kind="handoff",
                intent="inform",
                producer="agent:worker",
                audience=("agent:guide",),
                parts=(
                    ExchangePayloadPart(
                        part_type="structured",
                        data={
                            "to_role": "agent:guide",
                            "open_items": ["Server route handoff delivery."],
                        },
                    ),
                    ExchangePayloadPart(
                        part_type="relation",
                        relation=ExchangeRelation(
                            relation_id="rel-server-handoff",
                            relation_kind="hands_off",
                            source=ExchangeReference(ref_kind="agent", ref_id="agent:worker"),
                            target=ExchangeReference(ref_kind="agent", ref_id="agent:guide"),
                        ),
                    ),
                ),
            )
        )
        GovernanceTools(tmp_path, dry_run=True).agent_exchange_action_candidate_decide(
            candidate_id="ex-server-handoff-consume@v1:handoff",
            disposition_artifact_id="ex-server-handoff-consume-decision",
            actor="agent:guide",
            disposition="accept",
            target_surface="handoffIntake",
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "agentExchangeAcceptedHandoffCandidateConsume" in names
            consume_tool = next(
                tool for tool in tools
                if tool.name == "agentExchangeAcceptedHandoffCandidateConsume"
            )
            assert consume_tool.inputSchema["required"] == [
                "dispositionArtifactId",
                "dispositionVersion",
                "handoffDir",
            ]
            assert "handoff delivery" in consume_tool.description
            assert "local-work-trajectory.json" in consume_tool.description

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="agentExchangeAcceptedHandoffCandidateConsume",
                        arguments={
                            "dispositionArtifactId": "ex-server-handoff-consume-decision",
                            "dispositionVersion": "v1",
                            "handoffDir": ".codex/handoffs",
                        },
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["source_artifact_id"] == "ex-server-handoff-consume"
            handoff_path = (
                tmp_path
                / ".codex"
                / "handoffs"
                / f"{payload['handoff_payload']['handoff_id']}.json"
            )
            assert handoff_path.exists()
            assert payload["authority_split"]["review_state_mutated"] is False

        asyncio.run(exercise_server())

    def test_mcp_server_exposes_and_routes_accepted_merge_candidate_consume(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        snapshot_path = tmp_path / ".dbc" / "scheduler" / "scheduler-state.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-server-merge-consume",
                version="v1",
                kind="proposal",
                intent="request_merge",
                producer="agent:worker",
                audience=("agent:guide",),
                parts=(
                    ExchangePayloadPart(
                        part_type="relation",
                        relation=ExchangeRelation(
                            relation_id="rel-server-merge",
                            relation_kind="merges_into",
                            source=ExchangeReference(ref_kind="lane", ref_id="lane:worker"),
                            target=ExchangeReference(ref_kind="lane", ref_id="lane:main"),
                        ),
                    ),
                ),
            )
        )
        write_scheduler_state_snapshot(
            SchedulerState(
                tasks={
                    "task-c": ScheduledTask(
                        task_id="task-c",
                        title="C",
                        instruction="merge target",
                        agent=AgentSpec(agent_id="agent:c", runtime_provider="fake"),
                        state="waiting",
                    ),
                },
                merge_gates=(
                    SchedulerMergeGate(
                        gate_id="merge-server",
                        title="Server merge",
                        target_task_id="task-c",
                        state="review_required",
                        gate_kind="review",
                        required_review=True,
                    ),
                ),
            ),
            snapshot_path,
        )
        GovernanceTools(tmp_path, dry_run=True).agent_exchange_action_candidate_decide(
            candidate_id="ex-server-merge-consume@v1:merge",
            disposition_artifact_id="ex-server-merge-consume-decision",
            actor="agent:guide",
            disposition="accept",
            target_surface="mergeIntake",
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "agentExchangeAcceptedMergeCandidateConsume" in names
            consume_tool = next(
                tool for tool in tools
                if tool.name == "agentExchangeAcceptedMergeCandidateConsume"
            )
            assert consume_tool.inputSchema["required"] == [
                "dispositionArtifactId",
                "dispositionVersion",
                "snapshotPath",
                "gateId",
                "approved",
            ]
            assert "does not infer a gate" in consume_tool.description
            assert "local-work-trajectory.json" in consume_tool.description

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="agentExchangeAcceptedMergeCandidateConsume",
                        arguments={
                            "dispositionArtifactId": "ex-server-merge-consume-decision",
                            "dispositionVersion": "v1",
                            "snapshotPath": ".dbc/scheduler/scheduler-state.json",
                            "gateId": "merge-server",
                            "approved": True,
                            "reason": "server approved merge",
                        },
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["current_gate_state"] == "complete"
            assert payload["authority_split"]["handoff_mutated"] is False
            assert read_scheduler_state_snapshot(snapshot_path).merge_gates[0].state == "complete"

        asyncio.run(exercise_server())

    def test_mcp_server_exposes_and_routes_accepted_blocker_candidate_consume(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        store_path = tmp_path / ".dbc" / "orchestration" / "exchange-artifacts.json"
        snapshot_path = tmp_path / ".dbc" / "scheduler" / "scheduler-state.json"
        JsonArtifactVersionStore(store_path).put(
            ExchangeArtifact(
                artifact_id="ex-server-blocker-consume",
                version="v1",
                kind="blocker",
                intent="declare_blocked",
                producer="agent:worker",
                audience=("agent:guide",),
                parts=(
                    ExchangePayloadPart(
                        part_type="relation",
                        relation=ExchangeRelation(
                            relation_id="rel-server-blocker",
                            relation_kind="blocks",
                            source=ExchangeReference(ref_kind="task", ref_id="task-blocked"),
                            target=ExchangeReference(ref_kind="task", ref_id="task-upstream"),
                        ),
                    ),
                ),
            )
        )
        write_scheduler_state_snapshot(
            SchedulerState(
                tasks={
                    "task-blocked": ScheduledTask(
                        task_id="task-blocked",
                        title="Blocked",
                        instruction="block me",
                        agent=AgentSpec(agent_id="agent:b", runtime_provider="fake"),
                        state="waiting",
                    ),
                },
            ),
            snapshot_path,
        )
        GovernanceTools(tmp_path, dry_run=True).agent_exchange_action_candidate_decide(
            candidate_id="ex-server-blocker-consume@v1:blocker",
            disposition_artifact_id="ex-server-blocker-consume-decision",
            actor="agent:guide",
            disposition="accept",
            target_surface="blockerState",
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "agentExchangeAcceptedBlockerCandidateConsume" in names
            consume_tool = next(
                tool for tool in tools
                if tool.name == "agentExchangeAcceptedBlockerCandidateConsume"
            )
            assert consume_tool.inputSchema["required"] == [
                "dispositionArtifactId",
                "dispositionVersion",
                "snapshotPath",
                "taskId",
                "reason",
            ]
            assert "does not infer a task" in consume_tool.description
            assert "local-work-trajectory.json" in consume_tool.description

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="agentExchangeAcceptedBlockerCandidateConsume",
                        arguments={
                            "dispositionArtifactId": "ex-server-blocker-consume-decision",
                            "dispositionVersion": "v1",
                            "snapshotPath": ".dbc/scheduler/scheduler-state.json",
                            "taskId": "task-blocked",
                            "reason": "server accepted blocker",
                        },
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["current_task_state"] == "blocked"
            assert payload["authority_split"]["merge_gate_mutated"] is False
            assert read_scheduler_state_snapshot(snapshot_path).tasks["task-blocked"].blocked_reason == (
                "server accepted blocker"
            )

        asyncio.run(exercise_server())


class TestSchedulerProjection:
    """schedulerProjection MCP tool tests."""

    def test_scheduler_projection_writes_separate_artifact_from_snapshot_and_history(self, tmp_path):
        state = SchedulerState(
            tasks={
                "api/task": _mcp_scheduler_task("api/task", lane_id="lane:server"),
            },
        )
        snapshot_path = tmp_path / "scheduler-state.json"
        event_log_path = tmp_path / "scheduler-events.jsonl"
        write_scheduler_state_snapshot(state, snapshot_path)
        JsonlSchedulerEventLog(event_log_path).append(
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
            first_event_title="agent owned trajectory",
            lane_label="agent",
        )

        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.scheduler_projection(
            snapshot_path=str(snapshot_path),
            scheduler_event_log_path=str(event_log_path),
        )

        assert result["ok"] is True
        assert result["scheduler_projection_path"] == str(scheduler_work_trajectory_json_path(tmp_path))
        assert result["event_count"] == 1
        assert result["metadata"]["scheduler_event_log_count"] == "1"
        written = LocalWorkTrajectory.from_json(
            Path(result["scheduler_projection_path"]).read_text(encoding="utf-8")
        )
        assert written.events["scheduler-task:api-task"].metadata["scheduler_event_ids"] == (
            "scheduler-event-1"
        )
        local = load_local_work_trajectory(tmp_path)
        assert local.trajectory_id == "local-work:single-line-current"
        assert [event.title for event in local.events.values()] == ["agent owned trajectory"]

    def test_scheduler_projection_reports_missing_snapshot(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        result = tools.scheduler_projection(snapshot_path="missing-scheduler-state.json")

        assert result["ok"] is False
        assert "missing-scheduler-state.json" in result["snapshot_path"]
        assert "scheduler_projection_path" in result

    def test_scheduler_run_once_and_project_runs_and_refreshes_projection(self, tmp_path):
        snapshot_path = tmp_path / "scheduler-state.json"
        event_log_path = tmp_path / "scheduler-events.jsonl"
        batch = SchedulerTaskBatchSubmission(
            batch_id="batch-mcp-run",
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
                artifact_id="submission:mcp-run",
            ),
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="2026-06-17T05:00:00+08:00",
        )

        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.scheduler_run_once_and_project(
            snapshot_path=str(snapshot_path),
            event_log_path=str(event_log_path),
            timestamp="2026-06-17T05:01:00+08:00",
            guide_context="mcp-run-once-test",
        )

        assert result["ok"] is True
        assert result["runtime_provider"] == "fake"
        assert result["runtime_registry_providers"] == ["fake"]
        assert result["state_written"] is True
        assert result["stop_reason"] == "no_ready_tasks"
        assert result["run_count"] == 2
        assert result["scheduler_projection_path"] == str(scheduler_work_trajectory_json_path(tmp_path))
        assert result["event_count"] == 2
        assert result["metadata"]["scheduler_event_log_count"] == "9"
        assert result["metadata"]["scheduler_history_timeline_count"] == "9"
        written = LocalWorkTrajectory.from_json(
            Path(result["scheduler_projection_path"]).read_text(encoding="utf-8")
        )
        assert written.events["scheduler-task:task-a"].status == "completed"
        assert written.events["scheduler-task:task-b"].metadata["output_artifact_id"] == "task-b:result"

    def test_scheduler_run_once_and_project_requires_paths(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        missing_snapshot = tools.scheduler_run_once_and_project(
            snapshot_path="",
            event_log_path="scheduler-events.jsonl",
        )
        missing_log = tools.scheduler_run_once_and_project(
            snapshot_path="scheduler-state.json",
            event_log_path="",
        )

        assert missing_snapshot["ok"] is False
        assert "requires snapshotPath" in missing_snapshot["error"]
        assert missing_snapshot["runtime_provider"] == "fake"
        assert missing_log["ok"] is False
        assert "requires eventLogPath" in missing_log["error"]
        assert missing_log["runtime_provider"] == "fake"

    def test_scheduler_run_once_and_project_rejects_non_fake_runtime_provider(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        result = tools.scheduler_run_once_and_project(
            snapshot_path="scheduler-state.json",
            event_log_path="scheduler-events.jsonl",
            runtime_provider="qoder",
        )

        assert result["ok"] is False
        assert result["runtime_provider"] == "qoder"
        assert "runtimeProvider='fake' only" in result["error"]
        assert "requested 'qoder'" in result["error"]
        assert "host permission" in result["error"]

    def test_scheduler_lifecycle_control_and_run_once_use_control_file(self, tmp_path):
        snapshot_path = tmp_path / "scheduler-state.json"
        event_log_path = tmp_path / "scheduler-events.jsonl"
        control_path = tmp_path / "scheduler-daemon-control.json"
        submit_scheduler_task_batch_with_persistence(
            SchedulerState(),
            scheduler_task_batch_submission_to_artifact(
                SchedulerTaskBatchSubmission(
                    batch_id="batch-lifecycle-mcp",
                    tasks=(
                        SchedulerTaskSubmission(
                            task_id="task-lifecycle-mcp",
                            title="Lifecycle MCP task",
                            instruction="Complete through lifecycle MCP run-once.",
                            agent=AgentSpec(agent_id="agent:lifecycle-mcp", runtime_provider="fake"),
                            context_scope=ContextScope(context_id="context:lifecycle-mcp"),
                            output_artifact_id="task-lifecycle-mcp:result",
                        ),
                    ),
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
        assert not (tmp_path / ".dbc" / "progress-graph" / "local-work-trajectory.json").exists()
        assert not (tmp_path / ".dbc" / "progress-graph" / "scheduler-work-trajectory.json").exists()

    def test_mcp_server_exposes_and_routes_scheduler_lifecycle_tools(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        snapshot_path = tmp_path / "scheduler-state.json"
        event_log_path = tmp_path / "scheduler-events.jsonl"
        control_path = tmp_path / "scheduler-daemon-control.json"
        submit_scheduler_task_batch_with_persistence(
            SchedulerState(),
            scheduler_task_batch_submission_to_artifact(
                SchedulerTaskBatchSubmission(
                    batch_id="batch-server-lifecycle",
                    tasks=(
                        SchedulerTaskSubmission(
                            task_id="task-server-lifecycle",
                            title="Server lifecycle task",
                            instruction="Complete through server lifecycle tool.",
                            agent=AgentSpec(agent_id="agent:server-lifecycle", runtime_provider="fake"),
                            context_scope=ContextScope(context_id="context:server-lifecycle"),
                            output_artifact_id="task-server-lifecycle:result",
                        ),
                    ),
                ),
                artifact_id="submission:server-lifecycle",
            ),
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="2026-06-20T00:30:00+00:00",
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
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
            assert "only 'fake' is accepted" in run_tool.inputSchema["properties"]["runtimeProvider"]["description"]
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

    def test_mcp_server_exposes_and_routes_scheduler_projection(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        state = SchedulerState(
            tasks={
                "api/task": _mcp_scheduler_task("api/task", lane_id="lane:server"),
            },
        )
        snapshot_path = tmp_path / "scheduler-state.json"
        write_scheduler_state_snapshot(state, snapshot_path)
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "schedulerProjection" in names
            projection_tool = next(tool for tool in tools if tool.name == "schedulerProjection")
            assert "scheduler-work-trajectory.json" in projection_tool.description
            assert "local-work-trajectory.json" in projection_tool.description
            assert projection_tool.inputSchema["required"] == ["snapshotPath"]
            assert "schedulerEventLogPath" in projection_tool.inputSchema["properties"]
            assert "mergeGateEventLogPath" in projection_tool.inputSchema["properties"]

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="schedulerProjection",
                        arguments={
                            "snapshotPath": str(snapshot_path),
                            "title": "Scheduler Projection From MCP",
                        },
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["title"] == "Scheduler Projection From MCP"
            assert payload["event_count"] == 1
            assert Path(payload["scheduler_projection_path"]).exists()

        asyncio.run(exercise_server())

    def test_mcp_server_exposes_and_routes_scheduler_run_once_projection(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        snapshot_path = tmp_path / "scheduler-state.json"
        event_log_path = tmp_path / "scheduler-events.jsonl"
        batch = SchedulerTaskBatchSubmission(
            batch_id="batch-server-run",
            tasks=(
                SchedulerTaskSubmission(
                    task_id="task-a",
                    title="Task A",
                    instruction="Complete A.",
                    agent=AgentSpec(agent_id="agent:a", runtime_provider="fake"),
                    context_scope=ContextScope(context_id="context:a", lane_id="lane:a"),
                    output_artifact_id="task-a:result",
                ),
            ),
        )
        submit_scheduler_task_batch_with_persistence(
            SchedulerState(),
            scheduler_task_batch_submission_to_artifact(
                batch,
                artifact_id="submission:mcp-server-run",
            ),
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="2026-06-17T05:10:00+08:00",
        )
        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "schedulerRunOnceAndProject" in names
            run_tool = next(tool for tool in tools if tool.name == "schedulerRunOnceAndProject")
            assert run_tool.inputSchema["required"] == ["snapshotPath", "eventLogPath"]
            assert "runtimeProvider" in run_tool.inputSchema["properties"]
            assert "fake runtime" in run_tool.description
            assert "only 'fake' is allowed" in run_tool.description

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="schedulerRunOnceAndProject",
                        arguments={
                            "snapshotPath": str(snapshot_path),
                            "eventLogPath": str(event_log_path),
                            "runtimeProvider": "fake",
                            "timestamp": "2026-06-17T05:11:00+08:00",
                            "guideContext": "mcp-server-run-once-test",
                        },
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["runtime_provider"] == "fake"
            assert payload["runtime_registry_providers"] == ["fake"]
            assert payload["run_count"] == 1
            assert payload["event_count"] == 1
            assert payload["metadata"]["scheduler_event_log_count"] == "4"
            assert Path(payload["scheduler_projection_path"]).exists()

            rejected_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="schedulerRunOnceAndProject",
                        arguments={
                            "snapshotPath": str(snapshot_path),
                            "eventLogPath": str(event_log_path),
                            "runtimeProvider": "qoder",
                        },
                    )
                )
            )
            rejected_payload = json.loads(rejected_result.root.content[0].text)
            assert rejected_payload["ok"] is False
            assert rejected_payload["runtime_provider"] == "qoder"
            assert "runtimeProvider='fake' only" in rejected_payload["error"]

        asyncio.run(exercise_server())


class TestLocalTrajectory:
    """localTrajectory MCP tool tests."""

    def test_local_trajectory_rejects_worker_caller_role_before_mutation(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        rejected = tools.local_trajectory(
            "start",
            lane_label="worker",
            first_event_title="worker should report",
            caller_role="worker",
        )

        assert rejected["ok"] is False
        assert "leader/main/supervisor authority" in rejected["error"]
        assert "Subagent Report.trajectory_update" in rejected["error"]
        assert "docs/worker-trajectory-update-reporting.md" in rejected["error"]
        assert rejected["callerRole"] == "worker"
        assert not (
            tmp_path / ".dbc" / "progress-graph" / "local-work-trajectory.json"
        ).exists()

    def test_local_trajectory_starts_appends_and_advances_single_line(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        started = tools.local_trajectory(
            "start",
            lane_label="P1005",
            first_event_title="读题与建模",
            guide_context="codex-mcp-agent",
        )
        assert started["ok"] is True
        assert started["action"] == "start"
        assert started["trajectory_id"] == "local-work:single-line-current"
        assert started["event_count"] == 1
        assert started["relation_count"] == 0
        assert started["active_event_id"] == "event:001"

        appended = tools.local_trajectory(
            "append",
            title="状态转移推导",
            event_kind="task",
            summary="追加一个待推进节点。",
        )
        assert appended["ok"] is True
        assert appended["event_count"] == 2
        assert appended["relation_count"] == 1
        assert appended["active_event_id"] == "event:001"

        advanced = tools.local_trajectory("advance")
        assert advanced["ok"] is True
        assert advanced["event_count"] == 2
        assert advanced["relation_count"] == 1
        assert advanced["active_event_id"] == "event:002"

        from tools.progress_graph import load_local_work_trajectory

        trajectory = load_local_work_trajectory(tmp_path)
        assert [event.status for event in trajectory.events.values()] == [
            "completed",
            "in_progress",
        ]
        assert trajectory.events["event:002"].title == "状态转移推导"

    def test_local_trajectory_validates_required_fields_and_event_kind(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        missing = tools.local_trajectory("start")
        assert missing["ok"] is False
        assert "requires firstEventTitle or title" in missing["error"]

        invalid_kind = tools.local_trajectory(
            "append",
            title="非法类型",
            event_kind="unknown-kind",
        )
        assert invalid_kind["ok"] is False
        assert "eventKind must be one of" in invalid_kind["error"]
        assert invalid_kind["eventKind"] == "unknown-kind"

        invalid_action = tools.local_trajectory("unknown")
        assert invalid_action["ok"] is False
        assert "packRange, packSubgraph, appendChild, advanceChild, closeChild, merge, relate, or setAnchor" in invalid_action["error"]

    def test_local_trajectory_sets_global_anchor(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)
        tools.local_trajectory(
            "start",
            lane_label="anchor",
            first_event_title="start anchored work",
        )

        anchored = tools.local_trajectory(
            "setAnchor",
            source_graph_id="planning-gates-index",
            source_node_id="gate:anchor",
            summary="anchor moved",
            reason="active work moved",
        )

        assert anchored["ok"] is True
        assert anchored["action"] == "setAnchor"
        assert anchored["metadata"]["anchor_state"] == "set"
        assert anchored["metadata"]["anchor_graph_id"] == "planning-gates-index"
        assert anchored["metadata"]["anchor_node_id"] == "gate:anchor"

        from tools.progress_graph import load_local_work_trajectory

        trajectory = load_local_work_trajectory(tmp_path)
        assert trajectory.source_graph_id == "planning-gates-index"
        assert trajectory.source_node_id == "gate:anchor"

    def test_local_trajectory_start_accepts_initial_global_anchor(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        started = tools.local_trajectory(
            "start",
            lane_label="anchor",
            first_event_title="start anchored work",
            source_graph_id="planning-gates-index",
            source_node_id="gate:anchor",
        )

        assert started["ok"] is True
        assert started["action"] == "start"
        assert started["metadata"]["anchor_state"] == "set"
        assert started["metadata"]["anchor_graph_id"] == "planning-gates-index"
        assert started["metadata"]["anchor_node_id"] == "gate:anchor"

        from tools.progress_graph import load_local_work_trajectory

        trajectory = load_local_work_trajectory(tmp_path)
        assert trajectory.source_graph_id == "planning-gates-index"
        assert trajectory.source_node_id == "gate:anchor"

    def test_local_trajectory_updates_waits_resumes_and_closes_single_line(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        tools.local_trajectory(
            "start",
            lane_label="状态",
            first_event_title="初始节点",
        )
        tools.local_trajectory("append", title="后续节点", event_kind="validation")

        updated = tools.local_trajectory(
            "update",
            title="更新后的节点",
            summary="更新当前节点说明。",
        )
        assert updated["ok"] is True

        waiting = tools.local_trajectory("wait", reason="等待验证环境。")
        assert waiting["ok"] is True
        assert waiting["active_event_id"] is None

        resumed = tools.local_trajectory("resume", summary="验证环境已恢复。")
        assert resumed["ok"] is True
        assert resumed["active_event_id"] == "event:001"

        closed = tools.local_trajectory("close", summary="单线完成。")
        assert closed["ok"] is True
        assert closed["active_event_id"] is None

        from tools.progress_graph import load_local_work_trajectory

        trajectory = load_local_work_trajectory(tmp_path)
        assert trajectory.lanes["lane:main"].status == "done"
        assert trajectory.events["event:001"].title == "更新后的节点"
        assert trajectory.events["event:001"].status == "completed"
        assert trajectory.events["event:002"].status == "archived"

    def test_local_trajectory_adds_second_lane_and_appends_to_lane(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        tools.local_trajectory(
            "start",
            lane_label="主线",
            first_event_title="主线起点",
        )
        added = tools.local_trajectory(
            "addLane",
            lane_label="验证",
            first_event_title="验证线起点",
            event_kind="validation",
            lane_id="lane:validation",
            source_event_id="event:001",
        )
        assert added["ok"] is True
        assert added["lane_count"] == 2
        assert added["active_event_ids"] == ["event:001", "event:002"]

        appended = tools.local_trajectory(
            "append",
            title="验证线后续",
            lane_id="lane:validation",
        )
        assert appended["ok"] is True
        assert appended["lane_count"] == 2

        from tools.progress_graph import load_local_work_trajectory

        trajectory = load_local_work_trajectory(tmp_path)
        assert trajectory.metadata["lane_mode"] == "multi"
        assert "lane:validation" in trajectory.lanes
        assert any(relation.kind == "proposes_new_line" for relation in trajectory.relations)

    def test_local_trajectory_adds_multiple_lanes_from_one_source(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        tools.local_trajectory(
            "start",
            lane_label="main",
            first_event_title="split decision",
        )
        added = tools.local_trajectory(
            "addLanes",
            source_event_id="event:001",
            lanes=[
                {
                    "laneLabel": "server",
                    "firstEventTitle": "server contract",
                },
                {
                    "laneLabel": "client",
                    "firstEventTitle": "client shell",
                },
                {
                    "laneLabel": "tests",
                    "firstEventTitle": "test harness",
                    "eventKind": "validation",
                },
            ],
        )

        assert added["ok"] is True
        assert added["action"] == "addLanes"
        assert added["lane_count"] == 4
        assert added["relation_count"] == 3
        assert added["active_event_ids"] == [
            "event:001",
            "event:002",
            "event:003",
            "event:004",
        ]

        from tools.progress_graph import load_local_work_trajectory

        trajectory = load_local_work_trajectory(tmp_path)
        opening_relations = [
            relation for relation in trajectory.relations
            if relation.source_event_id == "event:001"
            and relation.kind == "proposes_new_line"
        ]
        assert len(opening_relations) == 3
        assert {relation.metadata["batch_open_count"] for relation in opening_relations} == {"3"}

    def test_local_trajectory_add_lanes_requires_lane_specs(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        tools.local_trajectory(
            "start",
            lane_label="main",
            first_event_title="split decision",
        )

        missing = tools.local_trajectory("addLanes")

        assert missing["ok"] is False
        assert missing["error"] == "localTrajectory addLanes requires lanes."
        assert missing["action"] == "addLanes"

    def test_local_trajectory_merges_second_lane_into_main(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        tools.local_trajectory(
            "start",
            lane_label="main",
            first_event_title="main start",
        )
        tools.local_trajectory(
            "addLane",
            lane_label="docs",
            first_event_title="docs start",
            lane_id="lane:docs",
            source_event_id="event:001",
        )
        tools.local_trajectory(
            "append",
            title="docs conclusion",
            event_kind="validation",
            lane_id="lane:docs",
        )
        tools.local_trajectory("advance", current_event_id="event:002")
        tools.local_trajectory("advance", current_event_id="event:003")

        merged = tools.local_trajectory(
            "merge",
            source_lane_id="lane:docs",
            target_lane_id="lane:main",
            summary="docs lane rejoins main",
        )
        assert merged["ok"] is True
        assert merged["lane_count"] == 2
        assert merged["active_event_id"] == "event:004"
        assert merged["active_event_ids"] == ["event:004"]

        from tools.progress_graph import load_local_work_trajectory

        trajectory = load_local_work_trajectory(tmp_path)
        merge_event = trajectory.events["event:004"]
        assert merge_event.kind == "merge"
        assert merge_event.lane_id == "lane:main"
        assert merge_event.status == "in_progress"
        assert merge_event.title == "merge"
        assert trajectory.lanes["lane:docs"].status == "done"
        assert any(relation.kind == "merges_into" for relation in trajectory.relations)

    def test_local_trajectory_relates_existing_events(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        tools.local_trajectory(
            "start",
            lane_label="main",
            first_event_title="main start",
        )
        tools.local_trajectory(
            "addLane",
            lane_label="impl",
            first_event_title="impl start",
            lane_id="lane:impl",
            source_event_id="event:001",
        )

        related = tools.local_trajectory(
            "relate",
            source_event_id="event:001",
            target_event_id="event:002",
            relation_kind="depends_on",
            summary="impl needs main setup",
        )

        assert related["ok"] is True
        assert related["action"] == "relate"
        assert related["relation_count"] == 2

        invalid = tools.local_trajectory(
            "relate",
            source_event_id="event:001",
            target_event_id="event:002",
            relation_kind="sequence",
        )
        assert invalid["ok"] is False
        assert "relationKind must be one of" in invalid["error"]

        from tools.progress_graph import load_local_work_trajectory

        trajectory = load_local_work_trajectory(tmp_path)
        assert any(
            relation.source_event_id == "event:001"
            and relation.target_event_id == "event:002"
            and relation.kind == "depends_on"
            for relation in trajectory.relations
        )

    def test_local_trajectory_adds_planned_compound(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        tools.local_trajectory(
            "start",
            lane_label="main",
            first_event_title="main start",
        )

        added = tools.local_trajectory(
            "addCompound",
            title="implementation phase",
            first_child_event_title="define internals",
            event_kind="review",
            child_lane_label="phase internals",
            summary="planned compound",
        )

        assert added["ok"] is True
        assert added["action"] == "addCompound"
        assert added["event_count"] == 2
        assert added["child_trajectory_count"] == 1
        assert added["active_event_id"] == "event:001"
        assert added["active_event_ids"] == ["event:001", "event:002"]

        from tools.progress_graph import load_local_work_trajectory

        trajectory = load_local_work_trajectory(tmp_path)
        compound = trajectory.events["event:002"]
        child = trajectory.child_trajectories[compound.metadata["child_trajectory_id"]]

        assert compound.kind == "compound"
        assert compound.status == "in_progress"
        assert child.events["event:001"].title == "define internals"
        assert child.events["event:001"].kind == "review"
        assert child.lanes["lane:main"].label == "phase internals"

    def test_local_trajectory_packs_existing_range(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        tools.local_trajectory(
            "start",
            lane_label="main",
            first_event_title="setup",
        )
        tools.local_trajectory("append", title="design")
        tools.local_trajectory("append", title="implement")
        tools.local_trajectory("append", title="validate", event_kind="validation")

        packed = tools.local_trajectory(
            "packRange",
            title="build phase",
            range_start_event_id="event:002",
            range_end_event_id="event:004",
            child_lane_label="build internals",
        )

        assert packed["ok"] is True
        assert packed["action"] == "packRange"
        assert packed["event_count"] == 2
        assert packed["child_trajectory_count"] == 1
        assert packed["active_event_ids"] == ["event:001"]

        from tools.progress_graph import load_local_work_trajectory

        trajectory = load_local_work_trajectory(tmp_path)
        compound = trajectory.events["event:005"]
        child = trajectory.child_trajectories[compound.metadata["child_trajectory_id"]]

        assert compound.kind == "compound"
        assert compound.metadata["compound_mode"] == "packed-range"
        assert [event.title for event in child.events.values()] == [
            "design",
            "implement",
            "validate",
        ]

    def test_local_trajectory_packs_multi_line_subgraph(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        tools.local_trajectory(
            "start",
            lane_label="main",
            first_event_title="setup",
        )
        tools.local_trajectory("append", title="main design")
        tools.local_trajectory("append", title="main implement")
        tools.local_trajectory(
            "addLane",
            lane_label="validation",
            first_event_title="validation setup",
            lane_id="lane:validation",
            source_event_id="event:001",
        )
        tools.local_trajectory(
            "append",
            title="validation execute",
            event_kind="validation",
            lane_id="lane:validation",
        )

        packed = tools.local_trajectory(
            "packSubgraph",
            title="implementation phase",
            anchor_lane_id="lane:main",
            pack_ranges=[
                {
                    "laneId": "lane:main",
                    "rangeStartEventId": "event:002",
                    "rangeEndEventId": "event:003",
                },
                {
                    "laneId": "lane:validation",
                    "rangeStartEventId": "event:004",
                    "rangeEndEventId": "event:005",
                },
            ],
        )

        assert packed["ok"] is True
        assert packed["action"] == "packSubgraph"
        assert packed["child_trajectory_count"] == 1

        from tools.progress_graph import load_local_work_trajectory

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
        assert proxy.metadata["anchor_compound_event_id"] == anchor.id
        assert set(child.lanes) == {"lane:main", "lane:validation"}

    def test_local_trajectory_relates_cross_pack_endpoints(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        tools.local_trajectory("start", lane_label="main", first_event_title="setup")
        tools.local_trajectory("append", title="alpha task")
        tools.local_trajectory("append", title="beta task")
        tools.local_trajectory(
            "packRange",
            title="alpha pack",
            range_start_event_id="event:002",
            range_end_event_id="event:002",
        )
        tools.local_trajectory(
            "packRange",
            title="beta pack",
            range_start_event_id="event:003",
            range_end_event_id="event:003",
        )

        from tools.progress_graph import load_local_work_trajectory

        trajectory = load_local_work_trajectory(tmp_path)
        alpha, beta = [
            event for event in sorted(trajectory.events.values(), key=lambda item: item.order)
            if event.kind == "compound"
        ]
        related = tools.local_trajectory(
            "relate",
            source_event_id=alpha.id,
            target_event_id=beta.id,
            relation_kind="depends_on",
            source_endpoint_trajectory_id=alpha.metadata["child_trajectory_id"],
            source_endpoint_event_id="event:002",
            source_endpoint_parent_event_id=alpha.id,
            source_endpoint_compound_path=alpha.id,
            target_endpoint_trajectory_id=beta.metadata["child_trajectory_id"],
            target_endpoint_event_id="event:003",
            target_endpoint_parent_event_id=beta.id,
            target_endpoint_compound_path=beta.id,
        )

        assert related["ok"] is True
        trajectory = load_local_work_trajectory(tmp_path)
        relation = next(
            relation for relation in trajectory.relations
            if relation.source_event_id == alpha.id
            and relation.target_event_id == beta.id
            and relation.kind == "depends_on"
        )
        assert relation.metadata["relation_projection"] == "cross-compound"
        assert relation.metadata["source_endpoint_trajectory_id"] == alpha.metadata["child_trajectory_id"]
        assert relation.metadata["target_endpoint_trajectory_id"] == beta.metadata["child_trajectory_id"]

    def test_local_trajectory_continues_child_trajectory(self, tmp_path):
        tools = GovernanceTools(tmp_path, dry_run=True)

        tools.local_trajectory(
            "start",
            lane_label="main",
            first_event_title="setup",
        )
        tools.local_trajectory(
            "addCompound",
            title="implementation phase",
            first_child_event_title="define internals",
        )

        appended = tools.local_trajectory(
            "appendChild",
            parent_event_id="event:002",
            title="implement internals",
        )
        assert appended["ok"] is True
        assert appended["action"] == "appendChild"
        assert appended["active_event_ids"] == ["event:001", "event:002"]

        advanced = tools.local_trajectory(
            "advanceChild",
            parent_event_id="event:002",
        )
        assert advanced["ok"] is True
        assert advanced["active_event_ids"] == ["event:001", "event:002"]

        closed = tools.local_trajectory(
            "closeChild",
            parent_event_id="event:002",
            summary="child done",
        )
        assert closed["ok"] is True

        from tools.progress_graph import load_local_work_trajectory

        trajectory = load_local_work_trajectory(tmp_path)
        compound = trajectory.events["event:002"]
        child = trajectory.child_trajectories[compound.metadata["child_trajectory_id"]]
        assert compound.status == "completed"
        assert child.lanes["lane:main"].status == "done"

    def test_mcp_server_exposes_and_routes_local_trajectory(self, tmp_path):
        import asyncio

        from mcp.types import (
            CallToolRequest,
            CallToolRequestParams,
            ListToolsRequest,
        )
        from src.mcp.server import create_server

        server = create_server(tmp_path, dry_run=True)

        async def exercise_server():
            list_result = await server.request_handlers[ListToolsRequest](
                ListToolsRequest()
            )
            tools = list_result.root.tools
            names = {tool.name for tool in tools}
            assert "localTrajectory" in names

            local_tool = next(tool for tool in tools if tool.name == "localTrajectory")
            assert "validation or delivery" in local_tool.description
            assert "pending or in_progress" in local_tool.description
            assert "When starting a trajectory" in local_tool.description
            assert "Use setAnchor" in local_tool.description
            assert "sourceGraphId and sourceNodeId" in local_tool.description
            assert local_tool.inputSchema["properties"]["action"]["enum"] == [
                "start",
                "append",
                "advance",
                "update",
                "block",
                "wait",
                "resume",
                "close",
                "addLane",
                "addLanes",
                "addCompound",
                "packRange",
                "packSubgraph",
                "appendChild",
                "advanceChild",
                "closeChild",
                "merge",
                "relate",
                "setAnchor",
            ]
            assert local_tool.inputSchema["properties"]["relationKind"]["enum"] == [
                "depends_on",
                "waits_for",
                "unblocks",
                "hands_off",
                "syncs_from",
                "merges_into",
                "proposes_new_line",
                "approves_new_line",
            ]
            assert local_tool.inputSchema["properties"]["eventKind"]["enum"] == [
                "start",
                "task",
                "decision",
                "review",
                "wait",
                "validation",
                "writeback",
                "handoff",
                "compound",
                "merge",
                "close",
            ]
            assert "parentEventId" in local_tool.inputSchema["properties"]
            assert "childTrajectoryId" in local_tool.inputSchema["properties"]
            assert "lanes" in local_tool.inputSchema["properties"]
            assert "one source event opens multiple work contexts" in local_tool.inputSchema["properties"]["lanes"]["description"]
            assert "rangeStartEventId" in local_tool.inputSchema["properties"]
            assert "rangeEndEventId" in local_tool.inputSchema["properties"]
            assert "packRanges" in local_tool.inputSchema["properties"]
            assert "sourceGraphId" in local_tool.inputSchema["properties"]
            assert "sourceNodeId" in local_tool.inputSchema["properties"]
            assert "start or setAnchor" in local_tool.inputSchema["properties"]["sourceGraphId"]["description"]
            assert "start or setAnchor" in local_tool.inputSchema["properties"]["sourceNodeId"]["description"]
            assert "callerRole" in local_tool.inputSchema["properties"]
            assert "Subagent Report.trajectory_update" in local_tool.description
            assert "docs/worker-trajectory-update-reporting.md" in local_tool.description
            assert "Worker/subagent roles are rejected" in local_tool.inputSchema["properties"]["callerRole"]["description"]
            assert "docs/worker-trajectory-update-reporting.md" in local_tool.inputSchema["properties"]["callerRole"]["description"]
            assert "anchorLaneId" in local_tool.inputSchema["properties"]
            assert "sourceEndpointTrajectoryId" in local_tool.inputSchema["properties"]
            assert "targetEndpointTrajectoryId" in local_tool.inputSchema["properties"]

            call_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "start",
                            "laneLabel": "MCP",
                            "firstEventTitle": "MCP 起点",
                            "sourceGraphId": "planning-gates-index",
                            "sourceNodeId": "gate:start-anchor",
                        },
                    )
                )
            )
            payload = json.loads(call_result.root.content[0].text)
            assert payload["ok"] is True
            assert payload["action"] == "start"
            assert payload["active_event_id"] == "event:001"
            assert payload["metadata"]["anchor_node_id"] == "gate:start-anchor"

            worker_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "append",
                            "title": "Worker direct mutation",
                            "callerRole": "worker",
                        },
                    )
                )
            )
            worker_payload = json.loads(worker_result.root.content[0].text)
            assert worker_payload["ok"] is False
            assert "leader/main/supervisor authority" in worker_payload["error"]
            assert "Subagent Report.trajectory_update" in worker_payload["error"]
            assert "docs/worker-trajectory-update-reporting.md" in worker_payload["error"]

            anchor_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "setAnchor",
                            "sourceGraphId": "planning-gates-index",
                            "sourceNodeId": "gate:anchor",
                            "summary": "anchor from MCP",
                        },
                    )
                )
            )
            anchor_payload = json.loads(anchor_result.root.content[0].text)
            assert anchor_payload["ok"] is True
            assert anchor_payload["action"] == "setAnchor"
            assert anchor_payload["metadata"]["anchor_node_id"] == "gate:anchor"

            add_lane_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "addLane",
                            "laneLabel": "Docs",
                            "firstEventTitle": "Docs start",
                            "laneId": "lane:docs",
                            "sourceEventId": "event:001",
                        },
                    )
                )
            )
            add_lane_payload = json.loads(add_lane_result.root.content[0].text)
            assert add_lane_payload["ok"] is True
            assert add_lane_payload["lane_count"] == 2

            await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "append",
                            "title": "Docs conclusion",
                            "eventKind": "validation",
                            "laneId": "lane:docs",
                        },
                    )
                )
            )
            for event_id in ("event:002", "event:003"):
                await server.request_handlers[CallToolRequest](
                    CallToolRequest(
                        params=CallToolRequestParams(
                            name="localTrajectory",
                            arguments={
                                "action": "advance",
                                "currentEventId": event_id,
                            },
                        )
                    )
                )

            merge_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "merge",
                            "sourceLaneId": "lane:docs",
                            "targetLaneId": "lane:main",
                            "title": "Merge docs",
                        },
                    )
                )
            )
            merge_payload = json.loads(merge_result.root.content[0].text)
            assert merge_payload["ok"] is True
            assert merge_payload["action"] == "merge"
            assert merge_payload["active_event_id"] == "event:004"

            relate_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "relate",
                            "sourceEventId": "event:003",
                            "targetEventId": "event:004",
                            "relationKind": "syncs_from",
                            "summary": "merge syncs docs conclusion",
                        },
                    )
                )
            )
            relate_payload = json.loads(relate_result.root.content[0].text)
            assert relate_payload["ok"] is True
            assert relate_payload["action"] == "relate"

            compound_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "addCompound",
                            "title": "Compound phase",
                            "firstChildEventTitle": "Compound first child",
                            "eventKind": "task",
                        },
                    )
                )
            )
            compound_payload = json.loads(compound_result.root.content[0].text)
            assert compound_payload["ok"] is True
            assert compound_payload["action"] == "addCompound"
            assert compound_payload["child_trajectory_count"] == 1

            await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "append",
                            "title": "Pack target A",
                        },
                    )
                )
            )
            await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "append",
                            "title": "Pack target B",
                        },
                    )
                )
            )
            pack_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "packRange",
                            "title": "Packed targets",
                            "rangeStartEventId": "event:006",
                            "rangeEndEventId": "event:007",
                        },
                    )
                )
            )
            pack_payload = json.loads(pack_result.root.content[0].text)
            assert pack_payload["ok"] is True
            assert pack_payload["action"] == "packRange"
            assert pack_payload["child_trajectory_count"] == 2

            pack_subgraph_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "packSubgraph",
                            "title": "Packed multi-line",
                            "anchorLaneId": "lane:main",
                            "packRanges": [
                                {
                                    "laneId": "lane:main",
                                    "rangeStartEventId": "event:004",
                                    "rangeEndEventId": "event:004",
                                },
                                {
                                    "laneId": "lane:docs",
                                    "rangeStartEventId": "event:002",
                                    "rangeEndEventId": "event:003",
                                },
                            ],
                        },
                    )
                )
            )
            pack_subgraph_payload = json.loads(pack_subgraph_result.root.content[0].text)
            assert pack_subgraph_payload["ok"] is True
            assert pack_subgraph_payload["action"] == "packSubgraph"

            append_child_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "appendChild",
                            "parentEventId": "event:005",
                            "title": "Compound child follow-up",
                        },
                    )
                )
            )
            append_child_payload = json.loads(append_child_result.root.content[0].text)
            assert append_child_payload["ok"] is True
            assert append_child_payload["action"] == "appendChild"

            close_child_result = await server.request_handlers[CallToolRequest](
                CallToolRequest(
                    params=CallToolRequestParams(
                        name="localTrajectory",
                        arguments={
                            "action": "closeChild",
                            "parentEventId": "event:005",
                            "summary": "compound child complete",
                        },
                    )
                )
            )
            close_child_payload = json.loads(close_child_result.root.content[0].text)
            assert close_child_payload["ok"] is True
            assert close_child_payload["action"] == "closeChild"

        asyncio.run(exercise_server())
