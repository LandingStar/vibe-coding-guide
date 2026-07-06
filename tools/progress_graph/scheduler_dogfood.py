"""Host-runtime dogfood harness for scheduler projection evidence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from src.runtime.orchestration.artifact_paths import dbc_artifact_path
from src.runtime.orchestration.exchange_store import InMemoryArtifactVersionStore, JsonlCoordinationEventLog
from src.runtime.orchestration.runtime_adapter import QoderQueryClient
from src.runtime.orchestration.runtime_wiring import RuntimeRegistryWiringConfig
from src.runtime.orchestration.scheduler import SchedulerRunPolicy
from src.runtime.orchestration.scheduler_dogfood import (
    HostSchedulerRunEvidenceWriteResult,
    build_host_scheduler_run_evidence,
    default_host_scheduler_run_evidence_path,
    write_host_scheduler_run_evidence,
)
from src.runtime.orchestration.scheduler_host_runner import HostSchedulerRunRequest

from .scheduler_projection import HostSchedulerRunProjectionRefreshResult, run_host_authorized_scheduler_once_and_refresh_projection


@dataclass(frozen=True, slots=True)
class HostRuntimeDogfoodHarnessResult:
    """Result of running a host-runtime dogfood pass and writing evidence."""

    run_projection: HostSchedulerRunProjectionRefreshResult
    evidence: HostSchedulerRunEvidenceWriteResult

    def to_json_dict(self) -> dict[str, object]:
        payload = self.evidence.to_json_dict()
        payload["projection_path"] = str(self.run_projection.projection_path)
        return payload


def run_host_runtime_dogfood_harness(
    project_root: str | Path,
    *,
    snapshot_path: str | Path,
    event_log_path: str | Path,
    runtime_config: RuntimeRegistryWiringConfig,
    evidence_id: str,
    evidence_output_path: str | Path | None = None,
    merge_gate_event_log_path: str | Path | None = None,
    projection_output_path: str | Path | None = None,
    policy: SchedulerRunPolicy | None = None,
    max_runs: int | None = None,
    workspace_root: str = "",
    scratch_root: str = dbc_artifact_path("scratch"),
    created_at: str = "",
    expires_at: str = "",
    timestamp: str = "",
    strict_recovery: bool = True,
    history_summary: Mapping[str, object] | None = None,
    evidence_metadata: Mapping[str, object] | None = None,
    artifact_store: InMemoryArtifactVersionStore | None = None,
    coordination_event_log: JsonlCoordinationEventLog | None = None,
    qoder_query_client: QoderQueryClient | None = None,
    trajectory_id: str = "local-work:scheduler-projection",
    title: str = "Scheduler Local Work Trajectory",
    recorded_at: str = "",
    guide_context: str = "",
    source_graph_id: str = "",
    source_node_id: str = "",
) -> HostRuntimeDogfoodHarnessResult:
    """Run one host-authorized scheduler dogfood pass and write evidence JSON.

    The harness composes existing host-runner and projection helpers. It does
    not schedule tasks itself and does not mutate agent-owned Local Work
    Trajectory artifacts.
    """

    _validate_real_runtime_client_ready(runtime_config, qoder_query_client)

    request = HostSchedulerRunRequest(
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        runtime_config=runtime_config,
        merge_gate_event_log_path=merge_gate_event_log_path,
        projection_output_path=projection_output_path,
        policy=policy,
        max_runs=max_runs,
        workspace_root=workspace_root,
        scratch_root=scratch_root,
        created_at=created_at,
        expires_at=expires_at,
        timestamp=timestamp,
        strict_recovery=strict_recovery,
        history_summary={} if history_summary is None else history_summary,
    )
    run_projection = run_host_authorized_scheduler_once_and_refresh_projection(
        project_root,
        request,
        artifact_store=artifact_store,
        coordination_event_log=coordination_event_log,
        qoder_query_client=qoder_query_client,
        trajectory_id=trajectory_id,
        title=title,
        recorded_at=recorded_at,
        guide_context=guide_context,
        source_graph_id=source_graph_id,
        source_node_id=source_node_id,
    )
    target = (
        Path(evidence_output_path)
        if evidence_output_path is not None
        else default_host_scheduler_run_evidence_path(project_root, evidence_id)
    )
    evidence = build_host_scheduler_run_evidence(
        run_projection.host_run,
        evidence_id=evidence_id,
        timestamp=timestamp,
        evidence_path=target,
        metadata={} if evidence_metadata is None else evidence_metadata,
    )
    written = write_host_scheduler_run_evidence(evidence, target)
    return HostRuntimeDogfoodHarnessResult(run_projection=run_projection, evidence=written)


def _validate_real_runtime_client_ready(
    runtime_config: RuntimeRegistryWiringConfig,
    qoder_query_client: QoderQueryClient | None,
) -> None:
    if "qoder" not in runtime_config.providers or qoder_query_client is None:
        return
    validator = getattr(qoder_query_client, "validate_host_ready", None)
    if callable(validator):
        validator()
