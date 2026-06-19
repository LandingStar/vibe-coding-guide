"""Host-authorized scheduler daemon loop adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from .exchange_store import InMemoryArtifactVersionStore, JsonlCoordinationEventLog
from .runtime_adapter import QoderQueryClient
from .runtime_wiring import RuntimeRegistryWiringConfig, build_runtime_registry_from_config
from .sandbox import SandboxProviderRegistry, SharedProcessSandboxProvider
from .scheduler_daemon import (
    SchedulerDaemonLoopResult,
    SchedulerDaemonLoopStopPolicy,
    run_scheduler_daemon_loop,
)
from .scheduler_loop_evidence import (
    SchedulerLoopEvidenceWriteResult,
    build_scheduler_loop_evidence,
    default_scheduler_loop_evidence_path,
    write_scheduler_loop_evidence,
)


@dataclass(frozen=True, slots=True)
class HostSchedulerDaemonLoopRequest:
    """Project-owned request for one host-authorized scheduler daemon loop."""

    snapshot_path: str | Path
    event_log_path: str | Path
    runtime_config: RuntimeRegistryWiringConfig = field(default_factory=RuntimeRegistryWiringConfig)
    stop_policy: SchedulerDaemonLoopStopPolicy = field(default_factory=SchedulerDaemonLoopStopPolicy)
    evidence_id: str = ""
    evidence_path: str | Path | None = None
    workspace_root: str = ""
    scratch_root: str = ".codex/scratch"
    created_at: str = ""
    expires_at: str = ""
    timestamp: str = ""
    strict_recovery: bool = True
    continue_on_failure: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HostSchedulerDaemonLoopResult:
    """Compact host-facing daemon-loop result plus optional evidence write."""

    loop: SchedulerDaemonLoopResult
    request: HostSchedulerDaemonLoopRequest
    runtime_registry_providers: tuple[str, ...]
    runtime_host_surface: str = ""
    evidence_write: SchedulerLoopEvidenceWriteResult | None = None
    local_work_trajectory_mutated: bool = False
    scheduler_projection_refreshed: bool = False

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-serializable compact host daemon-loop result."""

        loop_payload = self.loop.to_json_dict()
        invocation = self.request.runtime_config.host_invocation
        evidence_path = (
            ""
            if self.evidence_write is None
            else str(self.evidence_write.evidence_path)
        )
        payload: dict[str, object] = {
            "ok": True,
            "snapshot_path": loop_payload["snapshot_path"],
            "event_log_path": loop_payload["event_log_path"],
            "runtime_provider": loop_payload["runtime_provider"],
            "runtime_registry_providers": list(self.runtime_registry_providers),
            "runtime_host_surface": self.runtime_host_surface,
            "host_invocation_id": "" if invocation is None else invocation.invocation_id,
            "host_requested_by": "" if invocation is None else invocation.requested_by,
            "tick_count": loop_payload["tick_count"],
            "total_run_count": loop_payload["total_run_count"],
            "stop_reason": loop_payload["stop_reason"],
            "stop_detail": loop_payload["stop_detail"],
            "scheduler_event_count": loop_payload["scheduler_event_count"],
            "ran_tasks": loop_payload["ran_tasks"],
            "refreshed_projection": self.scheduler_projection_refreshed,
            "iterations": loop_payload["iterations"],
            "final_queue_summary": loop_payload["final_queue_summary"],
            "evidence_written": self.evidence_write is not None,
            "evidence_path": evidence_path,
            "metadata": dict(self.request.metadata),
            "authority_split": {
                "scheduler_state_authority": "scheduler_snapshot_and_event_log",
                "scheduler_state_mutated": loop_payload["authority_split"]["scheduler_state_mutated"],
                "provider_executed": loop_payload["authority_split"]["provider_executed"],
                "runtime_registry_authority": "host_runtime_wiring",
                "runtime_registry_providers": list(self.runtime_registry_providers),
                "runtime_host_surface": self.runtime_host_surface,
                "evidence_written": self.evidence_write is not None,
                "evidence_path": evidence_path,
                "scheduler_projection_refreshed": self.scheduler_projection_refreshed,
                "local_work_trajectory_mutated": self.local_work_trajectory_mutated,
                "exchange_artifact_store_mutated": False,
                "admission_ledger_mutated": False,
            },
        }
        return payload


def run_host_authorized_scheduler_daemon_loop(
    request: HostSchedulerDaemonLoopRequest,
    *,
    artifact_store: InMemoryArtifactVersionStore | None = None,
    coordination_event_log: JsonlCoordinationEventLog | None = None,
    qoder_query_client: QoderQueryClient | None = None,
    sandbox_registry: SandboxProviderRegistry | None = None,
) -> HostSchedulerDaemonLoopResult:
    """Run a bounded daemon loop through explicit host runtime wiring."""

    runtime_wiring = build_runtime_registry_from_config(
        request.runtime_config,
        artifact_store=artifact_store,
        coordination_event_log=coordination_event_log,
        qoder_query_client=qoder_query_client,
    )
    active_sandbox_registry = sandbox_registry or _default_sandbox_registry()
    provider = _select_loop_runtime_provider(runtime_wiring.registered_providers)
    loop = run_scheduler_daemon_loop(
        _loop_request(request, runtime_provider=provider),
        runtime_registry=runtime_wiring.registry,
        sandbox_registry=active_sandbox_registry,
        artifact_store=artifact_store,
    )
    evidence_write = _write_loop_evidence_if_requested(
        request,
        loop,
        runtime_host_surface=(
            ""
            if runtime_wiring.config.host_invocation is None
            else runtime_wiring.config.host_invocation.surface
        ),
    )
    return HostSchedulerDaemonLoopResult(
        loop=loop,
        request=request,
        runtime_registry_providers=runtime_wiring.registered_providers,
        runtime_host_surface=(
            ""
            if runtime_wiring.config.host_invocation is None
            else runtime_wiring.config.host_invocation.surface
        ),
        evidence_write=evidence_write,
    )


def _loop_request(
    request: HostSchedulerDaemonLoopRequest,
    *,
    runtime_provider: str,
) -> "SchedulerDaemonLoopRequest":
    from .scheduler_daemon import SchedulerDaemonLoopRequest

    return SchedulerDaemonLoopRequest(
        snapshot_path=request.snapshot_path,
        event_log_path=request.event_log_path,
        stop_policy=request.stop_policy,
        runtime_provider=runtime_provider,
        timestamp=request.timestamp,
        workspace_root=request.workspace_root,
        scratch_root=request.scratch_root,
        created_at=request.created_at,
        expires_at=request.expires_at,
        strict_recovery=request.strict_recovery,
        continue_on_failure=request.continue_on_failure,
    )


def _select_loop_runtime_provider(providers: tuple[str, ...]) -> str:
    if len(providers) == 1:
        return providers[0]
    if not providers:
        raise ValueError("host scheduler daemon loop runtime registry has no supported provider")
    raise ValueError(
        "host scheduler daemon loop currently requires exactly one runtime provider; "
        f"got: {', '.join(providers)}"
    )


def _write_loop_evidence_if_requested(
    request: HostSchedulerDaemonLoopRequest,
    loop: SchedulerDaemonLoopResult,
    *,
    runtime_host_surface: str,
) -> SchedulerLoopEvidenceWriteResult | None:
    if not request.evidence_id:
        return None
    target = (
        Path(request.evidence_path)
        if request.evidence_path is not None
        else default_scheduler_loop_evidence_path(
            _evidence_project_root(request),
            request.evidence_id,
        )
    )
    invocation = request.runtime_config.host_invocation
    metadata = {
        "surface": "host-authorized-scheduler-daemon-loop",
        "runtime_host_surface": runtime_host_surface,
        "host_invocation_id": "" if invocation is None else invocation.invocation_id,
    }
    metadata.update(dict(request.metadata))
    return write_scheduler_loop_evidence(
        build_scheduler_loop_evidence(
            loop,
            evidence_id=request.evidence_id,
            timestamp=request.timestamp,
            evidence_path=target,
            metadata=metadata,
        ),
        target,
    )


def _evidence_project_root(request: HostSchedulerDaemonLoopRequest) -> Path:
    if request.workspace_root:
        return Path(request.workspace_root)
    snapshot = Path(request.snapshot_path)
    parts = snapshot.parts
    if ".codex" in parts:
        index = parts.index(".codex")
        if index > 0:
            return Path(*parts[:index])
    return snapshot.parent


def _default_sandbox_registry() -> SandboxProviderRegistry:
    registry = SandboxProviderRegistry()
    registry.register(SharedProcessSandboxProvider())
    return registry
