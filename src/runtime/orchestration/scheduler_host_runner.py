"""Host-authorized one-shot scheduler runner adapter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from .artifact_paths import DEFAULT_DBC_SCRATCH_ROOT
from .exchange_store import InMemoryArtifactVersionStore, JsonlCoordinationEventLog
from .runtime_adapter import QoderQueryClient
from .runtime_wiring import RuntimeRegistryWiringConfig, build_runtime_registry_from_config
from .sandbox import GitWorktreeSandboxProvider, SandboxAllocation, SandboxProviderRegistry, SharedProcessSandboxProvider
from .sandbox_allocation_evidence import (
    SandboxAllocationReceiptEvidenceWriteResult,
    build_sandbox_allocation_receipt_evidence,
    default_sandbox_allocation_receipt_evidence_path,
    write_sandbox_allocation_receipt_evidence,
)
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
    scratch_root: str = DEFAULT_DBC_SCRATCH_ROOT
    git_worktree_sandbox_root: str | Path | None = None
    sandbox_allocation_evidence_id: str = ""
    sandbox_allocation_evidence_path: str | Path | None = None
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
    sandbox_allocation_evidence_write: SandboxAllocationReceiptEvidenceWriteResult | None = None
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

        sandbox_allocation_evidence_path = (
            ""
            if self.sandbox_allocation_evidence_write is None
            else str(self.sandbox_allocation_evidence_write.evidence_path)
        )

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
            "git_worktree_sandbox_opt_in": self.request.git_worktree_sandbox_root is not None,
            "git_worktree_sandbox_root": (
                ""
                if self.request.git_worktree_sandbox_root is None
                else str(Path(self.request.git_worktree_sandbox_root))
            ),
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
            "sandbox_allocation_evidence_written": self.sandbox_allocation_evidence_write is not None,
            "sandbox_allocation_evidence_path": sandbox_allocation_evidence_path,
            "local_trajectory_mutated": self.local_trajectory_mutated,
            "authority_split": {
                "scheduler_state_authority": "scheduler_snapshot_and_event_log",
                "scheduler_projection_role": "read-only-view",
                "local_work_trajectory_role": "agent-owned",
                "local_work_trajectory_mutated": self.local_trajectory_mutated,
                "sandbox_provider_authority": "host-explicit-opt-in",
                "sandbox_allocation_evidence_written": self.sandbox_allocation_evidence_write is not None,
                "sandbox_allocation_evidence_path": sandbox_allocation_evidence_path,
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

    active_sandbox_registry = _sandbox_registry_for_request(
        request,
        sandbox_registry=sandbox_registry,
    )
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
    evidence_write = _write_sandbox_allocation_evidence_if_requested(
        request,
        _sandbox_allocations_from_run(run),
    )
    return HostSchedulerRunResult(
        run=run,
        request=request,
        sandbox_allocation_evidence_write=evidence_write,
    )


def _default_sandbox_registry() -> SandboxProviderRegistry:
    registry = SandboxProviderRegistry()
    registry.register(SharedProcessSandboxProvider())
    return registry


def _sandbox_registry_for_request(
    request: HostSchedulerRunRequest,
    *,
    sandbox_registry: SandboxProviderRegistry | None,
) -> SandboxProviderRegistry:
    _validate_git_worktree_opt_in(request)
    if sandbox_registry is not None:
        return sandbox_registry
    registry = _default_sandbox_registry()
    if request.git_worktree_sandbox_root is None:
        return registry
    registry.register(GitWorktreeSandboxProvider(request.git_worktree_sandbox_root))
    return registry


def _validate_git_worktree_opt_in(request: HostSchedulerRunRequest) -> None:
    if request.git_worktree_sandbox_root is None:
        return
    if not str(request.git_worktree_sandbox_root):
        raise ValueError("git-worktree host-run opt-in requires git_worktree_sandbox_root")
    if not request.workspace_root:
        raise ValueError("git-worktree host-run opt-in requires workspace_root source repository")
    if not request.sandbox_allocation_evidence_id:
        raise ValueError("git-worktree host-run opt-in requires sandbox_allocation_evidence_id")


def _sandbox_allocations_from_run(
    run: PersistedSchedulerRunOnceResult,
) -> tuple[SandboxAllocation, ...]:
    return run.drain.sandbox_allocations


def _write_sandbox_allocation_evidence_if_requested(
    request: HostSchedulerRunRequest,
    allocations: tuple[SandboxAllocation, ...],
) -> SandboxAllocationReceiptEvidenceWriteResult | None:
    if not request.sandbox_allocation_evidence_id:
        return None
    target = (
        Path(request.sandbox_allocation_evidence_path)
        if request.sandbox_allocation_evidence_path is not None
        else default_sandbox_allocation_receipt_evidence_path(
            _evidence_project_root(request),
            request.sandbox_allocation_evidence_id,
        )
    )
    invocation = request.runtime_config.host_invocation
    metadata = {
        "surface": "host-authorized-scheduler-run-once",
        "host_invocation_id": "" if invocation is None else invocation.invocation_id,
        "git_worktree_sandbox_opt_in": request.git_worktree_sandbox_root is not None,
        "git_worktree_sandbox_root": (
            ""
            if request.git_worktree_sandbox_root is None
            else str(Path(request.git_worktree_sandbox_root))
        ),
    }
    return write_sandbox_allocation_receipt_evidence(
        build_sandbox_allocation_receipt_evidence(
            allocations,
            evidence_id=request.sandbox_allocation_evidence_id,
            timestamp=request.timestamp,
            evidence_path=target,
            metadata=metadata,
        ),
        target,
    )


def _evidence_project_root(request: HostSchedulerRunRequest) -> Path:
    if request.workspace_root:
        return Path(request.workspace_root)
    snapshot = Path(request.snapshot_path)
    parts = snapshot.parts
    if ".codex" in parts:
        index = parts.index(".codex")
        if index > 0:
            return Path(*parts[:index])
    return snapshot.parent
