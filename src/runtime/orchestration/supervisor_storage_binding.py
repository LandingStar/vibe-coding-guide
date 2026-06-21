"""Supervisor-run binding products for agent-private storage context."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .agent_storage import AgentHomeRegistration, AgentScratchSpace
from .scheduler import SchedulerState


DEFAULT_SUPERVISOR_BINDING_SCRATCH_ROOT = ".codex/scratch"
DEFAULT_SUPERVISOR_BINDING_HOME_ROOT = ".codex/agents"


@dataclass(frozen=True, slots=True)
class SupervisorAgentStorageBindingRequest:
    """Request to bind one supervisor run to storage-context products."""

    supervisor_id: str
    session_id: str
    run_id: str
    host_id: str = ""
    requested_by: str = ""
    agent_id: str = ""
    context_session_id: str = ""
    scratch_root: str = DEFAULT_SUPERVISOR_BINDING_SCRATCH_ROOT
    home_root: str = DEFAULT_SUPERVISOR_BINDING_HOME_ROOT
    created_at: str = ""
    expires_at: str = ""
    purpose: str = "Bind supervisor run to agent-private storage context."
    capability_domain: str = "scheduler-supervisor"


@dataclass(frozen=True, slots=True)
class SupervisorAgentStorageBinding:
    """Readback product connecting supervisor identity to storage products."""

    binding_id: str
    supervisor_id: str
    session_id: str
    run_id: str
    host_id: str
    requested_by: str
    agent_id: str
    context_session_id: str
    scheduler_task_ids: tuple[str, ...] = ()
    scheduler_context_ids: tuple[str, ...] = ()
    scheduler_lane_ids: tuple[str, ...] = ()
    runtime_session_ids: tuple[str, ...] = ()
    home_registration: AgentHomeRegistration | None = None
    scratch_spaces: tuple[AgentScratchSpace, ...] = ()
    source_snapshot_path: str = ""
    authority: dict[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-compatible binding readback."""

        return {
            "binding_id": self.binding_id,
            "supervisor_id": self.supervisor_id,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "host_id": self.host_id,
            "requested_by": self.requested_by,
            "agent_id": self.agent_id,
            "context_session_id": self.context_session_id,
            "scheduler_task_ids": list(self.scheduler_task_ids),
            "scheduler_context_ids": list(self.scheduler_context_ids),
            "scheduler_lane_ids": list(self.scheduler_lane_ids),
            "runtime_session_ids": list(self.runtime_session_ids),
            "home_registration": (
                None
                if self.home_registration is None
                else _agent_home_registration_data(self.home_registration)
            ),
            "scratch_spaces": [_scratch_space_data(scratch) for scratch in self.scratch_spaces],
            "source_snapshot_path": self.source_snapshot_path,
            "authority_split": dict(self.authority),
        }


def build_supervisor_agent_storage_binding(
    request: SupervisorAgentStorageBindingRequest,
    state: SchedulerState,
    *,
    source_snapshot_path: str | Path = "",
) -> SupervisorAgentStorageBinding:
    """Build a storage-context binding from supervisor identity and scheduler state.

    This helper is product-only: it does not create directories, persist home
    registrations, write scratch manifests, clean scratch, refresh projections,
    or mutate Local Work Trajectory.
    """

    _validate_binding_request(request)
    agent_id = request.agent_id or f"agent:{_slug(request.supervisor_id)}"
    context_session_id = request.context_session_id or _default_context_session_id(request)
    scratch_spaces = _scratch_spaces_for_state(
        state,
        scratch_root=request.scratch_root,
        supervisor_run_id=request.run_id,
        created_at=request.created_at,
        expires_at=request.expires_at,
    )
    home_registration = AgentHomeRegistration(
        registration_id=f"home-reg:{_slug(context_session_id)}",
        agent_id=agent_id,
        requested_by=request.requested_by or request.supervisor_id,
        purpose=request.purpose,
        capability_domain=request.capability_domain,
        requested_path_hint=_join_path(request.home_root, _slug(agent_id)),
        retention_policy="review-before-persisting-agent-private-memory",
        allowed_content_types=("notes", "checklist", "deidentified-summary"),
        allowed_sources=("reviewed-scratch", "operator-approved-context"),
        audit_state="requested",
        created_at=request.created_at,
        updated_at=request.created_at,
    )
    return SupervisorAgentStorageBinding(
        binding_id=f"supervisor-storage-binding:{_slug(context_session_id)}",
        supervisor_id=request.supervisor_id,
        session_id=request.session_id,
        run_id=request.run_id,
        host_id=request.host_id,
        requested_by=request.requested_by,
        agent_id=agent_id,
        context_session_id=context_session_id,
        scheduler_task_ids=tuple(sorted(state.tasks)),
        scheduler_context_ids=_unique_sorted(
            task.context_scope.context_id for task in state.tasks.values()
        ),
        scheduler_lane_ids=_unique_sorted(
            task.context_scope.lane_id for task in state.tasks.values() if task.context_scope.lane_id
        ),
        runtime_session_ids=_unique_sorted(
            record.session_id for record in state.run_records if record.session_id
        ),
        home_registration=home_registration,
        scratch_spaces=scratch_spaces,
        source_snapshot_path=str(source_snapshot_path),
        authority={
            "binding_authority": "supervisor-agent-storage-binding-product",
            "supervisor_authority": "host-owned-daemon-supervisor-contract",
            "scheduler_state_authority": "scheduler_snapshot",
            "agent_home_registration_persisted": False,
            "agent_home_directory_created": False,
            "scratch_directories_created": False,
            "scratch_manifest_written": False,
            "cleanup_executed": False,
            "scheduler_projection_refreshed": False,
            "local_work_trajectory_mutated": False,
        },
    )


def _validate_binding_request(request: SupervisorAgentStorageBindingRequest) -> None:
    if not request.supervisor_id:
        raise ValueError("supervisor storage binding requires supervisor_id")
    if not request.session_id:
        raise ValueError("supervisor storage binding requires session_id")
    if not request.run_id:
        raise ValueError("supervisor storage binding requires run_id")


def _scratch_spaces_for_state(
    state: SchedulerState,
    *,
    scratch_root: str,
    supervisor_run_id: str,
    created_at: str,
    expires_at: str,
) -> tuple[AgentScratchSpace, ...]:
    run_by_task = {record.task_id: record for record in state.run_records}
    spaces: list[AgentScratchSpace] = []
    for task_id, task in sorted(state.tasks.items()):
        run_record = run_by_task.get(task_id)
        path = _join_path(scratch_root, task_id)
        spaces.append(
            AgentScratchSpace(
                scratch_id=f"scratch:{task_id}",
                agent_id=task.agent.agent_id,
                run_id=run_record.run_id if run_record is not None else supervisor_run_id,
                task_id=task_id,
                lane_id=task.context_scope.lane_id,
                context_id=task.context_scope.context_id,
                path=path,
                created_at=created_at,
                expires_at=expires_at,
                archive_policy="review-before-retention",
                cleanup_policy="archive-or-delete-on-task-close",
                manifest_path=f"{path}/manifest.json",
                audit_state="active",
            )
        )
    return tuple(spaces)


def _default_context_session_id(request: SupervisorAgentStorageBindingRequest) -> str:
    if request.session_id:
        return f"context-session:{request.session_id}"
    return f"context-session:{request.run_id}"


def _unique_sorted(values) -> tuple[str, ...]:
    return tuple(sorted({str(value) for value in values if str(value)}))


def _join_path(root: str, suffix: str) -> str:
    normalized_root = str(root).rstrip("/\\")
    if not normalized_root:
        return suffix
    return f"{normalized_root}/{suffix}"


def _slug(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "-" for ch in value.strip().lower())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned or "default"


def _agent_home_registration_data(registration: AgentHomeRegistration) -> dict[str, object]:
    return {
        "registration_id": registration.registration_id,
        "agent_id": registration.agent_id,
        "requested_by": registration.requested_by,
        "purpose": registration.purpose,
        "capability_domain": registration.capability_domain,
        "storage_scope": registration.storage_scope,
        "requested_path_hint": registration.requested_path_hint,
        "registered_path": registration.registered_path,
        "retention_policy": registration.retention_policy,
        "quota": registration.quota,
        "allowed_content_types": list(registration.allowed_content_types),
        "denied_content_types": list(registration.denied_content_types),
        "allowed_sources": list(registration.allowed_sources),
        "denied_sources": list(registration.denied_sources),
        "secret_policy": registration.secret_policy,
        "audit_state": registration.audit_state,
        "approved_by": registration.approved_by,
        "created_at": registration.created_at,
        "updated_at": registration.updated_at,
    }


def _scratch_space_data(scratch: AgentScratchSpace) -> dict[str, object]:
    return {
        "scratch_id": scratch.scratch_id,
        "agent_id": scratch.agent_id,
        "run_id": scratch.run_id,
        "task_id": scratch.task_id,
        "lane_id": scratch.lane_id,
        "context_id": scratch.context_id,
        "path": scratch.path,
        "created_at": scratch.created_at,
        "expires_at": scratch.expires_at,
        "archive_policy": scratch.archive_policy,
        "cleanup_policy": scratch.cleanup_policy,
        "manifest_path": scratch.manifest_path,
        "audit_state": scratch.audit_state,
    }
