"""Host-owned Qoder smoke runner helper.

This module is a host-side convenience wrapper around the existing scheduler
dogfood harness. It does not expose Qoder through MCP and does not create a
second scheduler execution path.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.runtime.orchestration import (
    AgentSpec,
    ContextScope,
    InMemoryArtifactVersionStore,
    JsonlCoordinationEventLog,
    QoderQueryClient,
    QoderSDKQueryClient,
    QoderSDKQueryClientConfig,
    RuntimeHostInvocation,
    RuntimeProviderPermissionGrant,
    RuntimeRegistryWiringConfig,
    SchedulerRunPolicy,
    SchedulerState,
    ScheduledTask,
    write_scheduler_state_snapshot,
)

from .scheduler_dogfood import HostRuntimeDogfoodHarnessResult, run_host_runtime_dogfood_harness


@dataclass(frozen=True, slots=True)
class QoderSmokeTaskConfig:
    """Single scheduler task used by the host-owned Qoder smoke runner."""

    task_id: str = "qoder-smoke"
    title: str = "Qoder SDK smoke"
    instruction: str = "Return a compact confirmation that the Qoder SDK smoke task ran."
    lane_id: str = "lane:qoder-smoke"
    context_id: str = "context:qoder-smoke"
    agent_id: str = "agent:qoder-smoke"
    agent_display_name: str = "Qoder smoke agent"
    model: str = ""
    max_turns: int | None = 1
    acceptance: tuple[str, ...] = (
        "Return a concise normalized response.",
        "Do not request tool, shell, file, or network permissions in this smoke task.",
        "Do not include secrets or raw credential material in output.",
    )
    output_artifact_id: str = "qoder-smoke:result"


@dataclass(frozen=True, slots=True)
class HostOwnedQoderSmokeRunConfig:
    """Host-owned configuration for one repeatable Qoder smoke run."""

    evidence_id: str = "qoder-smoke"
    timestamp: str = ""
    snapshot_path: str | Path = ".codex/scheduler/qoder-smoke-state.json"
    event_log_path: str | Path = ".codex/scheduler/qoder-smoke-events.jsonl"
    evidence_output_path: str | Path | None = None
    projection_output_path: str | Path | None = None
    initialize_snapshot: bool = True
    reset_snapshot: bool = False
    task: QoderSmokeTaskConfig = field(default_factory=QoderSmokeTaskConfig)
    qoder_client_config: QoderSDKQueryClientConfig = field(default_factory=QoderSDKQueryClientConfig)
    host_invocation_id: str = "host-owned-qoder-smoke"
    requested_by: str = "host:qoder-smoke"
    reason: str = "host-owned Qoder SDK smoke run"
    grant_id: str = "grant-host-owned-qoder-smoke"
    approved_by: str = "host:qoder-smoke"
    approved_at: str = ""
    grant_scope: str = "qoder-smoke"
    allow_network: bool = True
    policy: SchedulerRunPolicy | None = field(
        default_factory=lambda: SchedulerRunPolicy(max_runs=1, continue_on_failure=False)
    )
    workspace_root: str = ""
    scratch_root: str = ".codex/scratch"
    created_at: str = ""
    expires_at: str = ""
    strict_recovery: bool = True
    history_summary: Mapping[str, object] = field(default_factory=dict)
    evidence_metadata: Mapping[str, object] = field(default_factory=dict)
    trajectory_id: str = "local-work:scheduler-projection"
    title: str = "Scheduler Local Work Trajectory"
    recorded_at: str = ""
    guide_context: str = "host-owned-qoder-smoke"
    source_graph_id: str = ""
    source_node_id: str = ""


@dataclass(frozen=True, slots=True)
class HostOwnedQoderSmokeRunResult:
    """Result of one host-owned Qoder smoke runner invocation."""

    harness: HostRuntimeDogfoodHarnessResult
    snapshot_path: Path
    event_log_path: Path
    initialized_snapshot: bool

    def to_json_dict(self) -> dict[str, object]:
        payload = self.harness.to_json_dict()
        payload["snapshot_path"] = str(self.snapshot_path)
        payload["event_log_path"] = str(self.event_log_path)
        payload["initialized_snapshot"] = self.initialized_snapshot
        return payload


def default_qoder_smoke_snapshot_path(project_root: str | Path) -> Path:
    """Return the default scheduler snapshot path for host-owned Qoder smoke."""

    return Path(project_root) / ".codex/scheduler/qoder-smoke-state.json"


def default_qoder_smoke_event_log_path(project_root: str | Path) -> Path:
    """Return the default scheduler event-log path for host-owned Qoder smoke."""

    return Path(project_root) / ".codex/scheduler/qoder-smoke-events.jsonl"


def build_qoder_smoke_scheduler_state(
    task: QoderSmokeTaskConfig | None = None,
) -> SchedulerState:
    """Build a minimal scheduler snapshot for one Qoder smoke task."""

    active_task = task or QoderSmokeTaskConfig()
    agent = AgentSpec(
        agent_id=active_task.agent_id,
        runtime_provider="qoder",
        display_name=active_task.agent_display_name,
        model=active_task.model,
        max_turns=active_task.max_turns,
    )
    scheduled_task = ScheduledTask(
        task_id=active_task.task_id,
        title=active_task.title,
        instruction=active_task.instruction,
        agent=agent,
        context_scope=ContextScope(
            context_id=active_task.context_id,
            lane_id=active_task.lane_id,
            session_policy="single-smoke-run",
            redaction_policy="no-secrets",
        ),
        acceptance=active_task.acceptance,
        output_artifact_id=active_task.output_artifact_id,
    )
    return SchedulerState(tasks={scheduled_task.task_id: scheduled_task})


def ensure_qoder_smoke_scheduler_snapshot(
    project_root: str | Path,
    *,
    config: HostOwnedQoderSmokeRunConfig | None = None,
) -> tuple[Path, bool]:
    """Create or reset the smoke scheduler snapshot when requested."""

    active_config = config or HostOwnedQoderSmokeRunConfig()
    snapshot_path = _project_path(project_root, active_config.snapshot_path)
    if not active_config.initialize_snapshot:
        return snapshot_path, False
    if snapshot_path.exists() and not active_config.reset_snapshot:
        return snapshot_path, False
    write_scheduler_state_snapshot(
        build_qoder_smoke_scheduler_state(active_config.task),
        snapshot_path,
    )
    return snapshot_path, True


def run_host_owned_qoder_smoke(
    project_root: str | Path,
    *,
    config: HostOwnedQoderSmokeRunConfig | None = None,
    qoder_query_client: QoderQueryClient | None = None,
    sdk_importer: Callable[[str], Any] | None = None,
    environment: Mapping[str, str] | None = None,
    artifact_store: InMemoryArtifactVersionStore | None = None,
    coordination_event_log: JsonlCoordinationEventLog | None = None,
) -> HostOwnedQoderSmokeRunResult:
    """Run one host-owned Qoder smoke pass through the dogfood harness.

    When ``qoder_query_client`` is omitted, the helper constructs the optional
    ``QoderSDKQueryClient`` from host-provided config. SDK readiness is still
    checked by the dogfood harness before scheduler execution.
    """

    active_config = config or HostOwnedQoderSmokeRunConfig()
    snapshot_path, initialized_snapshot = ensure_qoder_smoke_scheduler_snapshot(
        project_root,
        config=active_config,
    )
    event_log_path = _project_path(project_root, active_config.event_log_path)
    client = qoder_query_client or QoderSDKQueryClient(
        active_config.qoder_client_config,
        sdk_importer=sdk_importer,
        environment=environment if environment is not None else os.environ,
    )
    runtime_config = _runtime_config(active_config)
    harness = run_host_runtime_dogfood_harness(
        project_root,
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        runtime_config=runtime_config,
        evidence_id=active_config.evidence_id,
        evidence_output_path=(
            None
            if active_config.evidence_output_path is None
            else _project_path(project_root, active_config.evidence_output_path)
        ),
        projection_output_path=(
            None
            if active_config.projection_output_path is None
            else _project_path(project_root, active_config.projection_output_path)
        ),
        policy=active_config.policy,
        workspace_root=active_config.workspace_root,
        scratch_root=active_config.scratch_root,
        created_at=active_config.created_at,
        expires_at=active_config.expires_at,
        timestamp=active_config.timestamp,
        strict_recovery=active_config.strict_recovery,
        history_summary=active_config.history_summary,
        evidence_metadata=_evidence_metadata(active_config),
        artifact_store=artifact_store,
        coordination_event_log=coordination_event_log,
        qoder_query_client=client,
        trajectory_id=active_config.trajectory_id,
        title=active_config.title,
        recorded_at=active_config.recorded_at,
        guide_context=active_config.guide_context,
        source_graph_id=active_config.source_graph_id,
        source_node_id=active_config.source_node_id,
    )
    return HostOwnedQoderSmokeRunResult(
        harness=harness,
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        initialized_snapshot=initialized_snapshot,
    )


def _runtime_config(config: HostOwnedQoderSmokeRunConfig) -> RuntimeRegistryWiringConfig:
    timestamp = config.timestamp
    approved_at = config.approved_at or timestamp
    return RuntimeRegistryWiringConfig(
        providers=("qoder",),
        timestamp=timestamp,
        host_invocation=RuntimeHostInvocation(
            surface="host-authorized-adapter",
            invocation_id=config.host_invocation_id,
            requested_providers=("qoder",),
            requested_by=config.requested_by,
            reason=config.reason,
        ),
        qoder_permission_grant=RuntimeProviderPermissionGrant(
            grant_id=config.grant_id,
            provider="qoder",
            approved_by=config.approved_by,
            approved_at=approved_at,
            scope=config.grant_scope,
            allow_sdk_client=True,
            allow_network=config.allow_network,
        ),
    )


def _evidence_metadata(config: HostOwnedQoderSmokeRunConfig) -> dict[str, object]:
    metadata = {
        "runner": "host-owned-qoder-smoke",
        "task_id": config.task.task_id,
        "sdk_module_name": config.qoder_client_config.sdk_module_name,
        "permission_request_policy": config.qoder_client_config.permission_request_policy,
    }
    metadata.update(dict(config.evidence_metadata))
    return metadata


def _project_path(project_root: str | Path, path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(project_root) / candidate
