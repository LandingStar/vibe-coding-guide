"""Host-authorized one-shot scheduler runner adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from .exchange_store import InMemoryArtifactVersionStore, JsonlCoordinationEventLog
from .runtime_adapter import QoderQueryClient
from .runtime_wiring import RuntimeRegistryWiringConfig, build_runtime_registry_from_config
from .sandbox import SandboxProviderRegistry, SharedProcessSandboxProvider
from .scheduler import SchedulerRunPolicy
from .scheduler_runner import PersistedSchedulerRunOnceResult, run_persisted_scheduler_once_with_wiring


@dataclass(frozen=True, slots=True)
class HostSchedulerRunRequest:
    """Project-owned request for one host-authorized scheduler pass."""

    snapshot_path: str | Path
    event_log_path: str | Path
    runtime_config: RuntimeRegistryWiringConfig = field(default_factory=RuntimeRegistryWiringConfig)
    merge_gate_event_log_path: str | Path | None = None
    projection_output_path: str | Path | None = None
    policy: SchedulerRunPolicy | None = None
    max_runs: int | None = None
    workspace_root: str = ""
    scratch_root: str = ".codex/scratch"
    created_at: str = ""
    expires_at: str = ""
    timestamp: str = ""
    strict_recovery: bool = True
    history_summary: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HostSchedulerRunResult:
    """Compact host-facing result plus the full scheduler run object."""

    run: PersistedSchedulerRunOnceResult
    request: HostSchedulerRunRequest
    scheduler_projection_path: Path | None = None
    local_trajectory_mutated: bool = False

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-serializable compact host result."""

        drain = self.run.drain
        state = drain.state
        output_artifact_refs = []
        permission_review_task_ids: list[str] = []
        for task in sorted(state.tasks.values(), key=lambda item: item.task_id):
            if task.output_artifact_ref is not None:
                output_artifact_refs.append(
                    {
                        "task_id": task.task_id,
                        "artifact_id": task.output_artifact_ref.ref_id,
                        "version": task.output_artifact_ref.version,
                    }
                )
            if task.state == "review_required":
                permission_review_task_ids.append(task.task_id)

        run_ids = []
        session_ids = []
        for item in drain.preflight_results:
            handle = item.runtime_result.run_handle
            run_ids.append(handle.run_id)
            session_ids.append(handle.session_id)

        history_summary: dict[str, object] = {
            "scheduler_event_log_path": str(self.run.event_log_path),
            "merge_gate_event_log_path": (
                "" if self.request.merge_gate_event_log_path is None else str(Path(self.request.merge_gate_event_log_path))
            ),
            "projection_output_path": (
                "" if self.scheduler_projection_path is None else str(self.scheduler_projection_path)
            ),
            "run_ids": run_ids,
            "session_ids": session_ids,
        }
        history_summary.update(dict(self.request.history_summary))

        invocation = self.request.runtime_config.host_invocation
        return {
            "ok": True,
            "snapshot_path": str(self.run.snapshot_path),
            "event_log_path": str(self.run.event_log_path),
            "merge_gate_event_log_path": (
                "" if self.request.merge_gate_event_log_path is None else str(Path(self.request.merge_gate_event_log_path))
            ),
            "scheduler_projection_path": (
                "" if self.scheduler_projection_path is None else str(self.scheduler_projection_path)
            ),
            "runtime_registry_providers": list(self.run.runtime_registry_providers),
            "runtime_host_surface": self.run.runtime_host_surface,
            "host_invocation_id": "" if invocation is None else invocation.invocation_id,
            "host_requested_by": "" if invocation is None else invocation.requested_by,
            "run_count": len(drain.preflight_results),
            "stop_reason": drain.stop_reason,
            "stop_detail": drain.stop_detail,
            "ready_task_ids": list(drain.ready_task_ids),
            "blocked_task_ids": list(drain.blocked_task_ids),
            "failed_task_ids": list(drain.failed_task_ids),
            "permission_review_task_ids": permission_review_task_ids,
            "permission_review_count": len(permission_review_task_ids),
            "output_artifact_refs": output_artifact_refs,
            "state_written": self.run.state_written,
            "local_trajectory_mutated": self.local_trajectory_mutated,
            "authority_split": {
                "scheduler_state_authority": "scheduler_snapshot_and_event_log",
                "scheduler_projection_role": "read-only-view",
                "local_work_trajectory_role": "agent-owned",
                "local_work_trajectory_mutated": self.local_trajectory_mutated,
            },
            "history_summary": history_summary,
        }


def run_host_authorized_scheduler_once(
    request: HostSchedulerRunRequest,
    *,
    artifact_store: InMemoryArtifactVersionStore | None = None,
    coordination_event_log: JsonlCoordinationEventLog | None = None,
    qoder_query_client: QoderQueryClient | None = None,
    sandbox_registry: SandboxProviderRegistry | None = None,
) -> HostSchedulerRunResult:
    """Run one bounded scheduler pass through explicit host runtime wiring."""

    active_sandbox_registry = sandbox_registry or _default_sandbox_registry()
    runtime_wiring = build_runtime_registry_from_config(
        request.runtime_config,
        artifact_store=artifact_store,
        coordination_event_log=coordination_event_log,
        qoder_query_client=qoder_query_client,
    )
    run = run_persisted_scheduler_once_with_wiring(
        snapshot_path=request.snapshot_path,
        event_log_path=request.event_log_path,
        sandbox_registry=active_sandbox_registry,
        runtime_wiring=runtime_wiring,
        policy=request.policy,
        max_runs=request.max_runs,
        workspace_root=request.workspace_root,
        scratch_root=request.scratch_root,
        created_at=request.created_at,
        expires_at=request.expires_at,
        timestamp=request.timestamp,
        strict_recovery=request.strict_recovery,
    )
    return HostSchedulerRunResult(run=run, request=request)


def _default_sandbox_registry() -> SandboxProviderRegistry:
    registry = SandboxProviderRegistry()
    registry.register(SharedProcessSandboxProvider())
    return registry
