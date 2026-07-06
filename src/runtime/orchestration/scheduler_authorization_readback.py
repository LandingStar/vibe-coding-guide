"""Read-only scheduler authorization diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from .artifact_paths import DEFAULT_DBC_SCRATCH_ROOT
from .sandbox import (
    GitWorktreeCommandReceipt,
    GitWorktreeSandboxReceipt,
    SandboxAllocation,
    SandboxLeaseMountAuthorization,
    SandboxRequest,
    SharedProcessSandboxProvider,
)
from .sandbox_allocation_evidence import read_sandbox_allocation_receipt_evidence_summary
from .scheduler import EditLeaseLifecycleRecord, SchedulerState, ScheduledTask
from .scheduler_store import read_scheduler_state_snapshot, recover_scheduler_state

SCHEDULER_AUTHORIZATION_READBACK_PRODUCT_TYPE = "scheduler_authorization_readback"
SCHEDULER_AUTHORIZATION_READBACK_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class LeaseLifecycleSummary:
    """JSON-safe summary of one scheduler-owned edit lease lifecycle record."""

    lease_id: str
    task_id: str
    state: str
    mode: str
    allowed_artifacts: tuple[str, ...] = ()
    denied_artifacts: tuple[str, ...] = ()
    conflict_policy: str = ""
    acquired_at: str = ""
    expires_at: str = ""
    released_at: str = ""
    reason: str = ""
    conflict_state: str = ""
    conflict_classification: str = ""
    conflict_left_task_id: str = ""
    conflict_right_task_id: str = ""
    conflict_left_path: str = ""
    conflict_right_path: str = ""

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-safe lifecycle summary."""

        return {
            "lease_id": self.lease_id,
            "task_id": self.task_id,
            "state": self.state,
            "mode": self.mode,
            "allowed_artifacts": list(self.allowed_artifacts),
            "denied_artifacts": list(self.denied_artifacts),
            "conflict_policy": self.conflict_policy,
            "acquired_at": self.acquired_at,
            "expires_at": self.expires_at,
            "released_at": self.released_at,
            "reason": self.reason,
            "conflict_state": self.conflict_state,
            "conflict_classification": self.conflict_classification,
            "conflict_left_task_id": self.conflict_left_task_id,
            "conflict_right_task_id": self.conflict_right_task_id,
            "conflict_left_path": self.conflict_left_path,
            "conflict_right_path": self.conflict_right_path,
        }


@dataclass(frozen=True, slots=True)
class SandboxLeaseAuthorizationSummary:
    """JSON-safe summary of one sandbox lease mount authorization decision."""

    lease_id: str = ""
    task_id: str = ""
    lifecycle_state: str = ""
    authorized_mounts: tuple[str, ...] = ()
    denied_mounts: tuple[str, ...] = ()
    reason: str = ""

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-safe sandbox lease authorization summary."""

        return {
            "lease_id": self.lease_id,
            "task_id": self.task_id,
            "lifecycle_state": self.lifecycle_state,
            "authorized_mounts": list(self.authorized_mounts),
            "denied_mounts": list(self.denied_mounts),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class GitWorktreeCommandReceiptSummary:
    """JSON-safe summary of one git-worktree command receipt."""

    command: tuple[str, ...] = ()
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-safe command receipt summary."""

        return {
            "command": list(self.command),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


@dataclass(frozen=True, slots=True)
class GitWorktreeReceiptSummary:
    """JSON-safe summary of one git-worktree sandbox receipt."""

    source_repository_root: str = ""
    sandbox_root: str = ""
    worktree_path: str = ""
    branch_name: str = ""
    base_ref: str = ""
    authorized_writable_paths: tuple[str, ...] = ()
    denied_writable_paths: tuple[str, ...] = ()
    cleanup_state: str = ""
    cleanup_required: bool = False
    cleanup_owner: str = ""
    cleanup_policy: str = ""
    allocation: GitWorktreeCommandReceiptSummary = field(
        default_factory=GitWorktreeCommandReceiptSummary
    )
    cleanup: GitWorktreeCommandReceiptSummary = field(
        default_factory=GitWorktreeCommandReceiptSummary
    )
    branch_cleanup: GitWorktreeCommandReceiptSummary = field(
        default_factory=GitWorktreeCommandReceiptSummary
    )

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-safe git-worktree receipt summary."""

        return {
            "source_repository_root": self.source_repository_root,
            "sandbox_root": self.sandbox_root,
            "worktree_path": self.worktree_path,
            "branch_name": self.branch_name,
            "base_ref": self.base_ref,
            "authorized_writable_paths": list(self.authorized_writable_paths),
            "denied_writable_paths": list(self.denied_writable_paths),
            "cleanup_state": self.cleanup_state,
            "cleanup_required": self.cleanup_required,
            "cleanup_owner": self.cleanup_owner,
            "cleanup_policy": self.cleanup_policy,
            "allocation": self.allocation.to_json_dict(),
            "cleanup": self.cleanup.to_json_dict(),
            "branch_cleanup": self.branch_cleanup.to_json_dict(),
        }


@dataclass(frozen=True, slots=True)
class SandboxAuthorizationSummary:
    """JSON-safe task sandbox authorization readback."""

    profile_id: str
    profile_kind: str
    mount_policy: str
    allocation_state: str
    allocation_reason: str = ""
    visible_mounts: tuple[str, ...] = ()
    lease_authorization_state: str = "not_required"
    lease_authorization_reason: str = ""
    lease_authorizations: tuple[SandboxLeaseAuthorizationSummary, ...] = ()
    git_worktree_receipt: GitWorktreeReceiptSummary | None = None

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-safe sandbox authorization summary."""

        return {
            "profile_id": self.profile_id,
            "profile_kind": self.profile_kind,
            "mount_policy": self.mount_policy,
            "allocation_state": self.allocation_state,
            "allocation_reason": self.allocation_reason,
            "visible_mounts": list(self.visible_mounts),
            "lease_authorization_state": self.lease_authorization_state,
            "lease_authorization_reason": self.lease_authorization_reason,
            "lease_authorizations": [
                item.to_json_dict()
                for item in self.lease_authorizations
            ],
            "git_worktree_receipt": (
                self.git_worktree_receipt.to_json_dict()
                if self.git_worktree_receipt is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class TaskAuthorizationSummary:
    """JSON-safe authorization summary for one scheduler task."""

    task_id: str
    title: str
    state: str
    agent_id: str
    runtime_provider: str
    has_edit_lease: bool
    lease_id: str = ""
    lease_mode: str = ""
    allowed_artifacts: tuple[str, ...] = ()
    denied_artifacts: tuple[str, ...] = ()
    conflict_policy: str = ""
    lease_expires_at: str = ""
    lifecycle_missing: bool = False
    lifecycle: LeaseLifecycleSummary | None = None
    sandbox_authorization: SandboxAuthorizationSummary | None = None

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-safe task authorization summary."""

        return {
            "task_id": self.task_id,
            "title": self.title,
            "state": self.state,
            "agent_id": self.agent_id,
            "runtime_provider": self.runtime_provider,
            "has_edit_lease": self.has_edit_lease,
            "lease_id": self.lease_id,
            "lease_mode": self.lease_mode,
            "allowed_artifacts": list(self.allowed_artifacts),
            "denied_artifacts": list(self.denied_artifacts),
            "conflict_policy": self.conflict_policy,
            "lease_expires_at": self.lease_expires_at,
            "lifecycle_missing": self.lifecycle_missing,
            "lifecycle": (
                self.lifecycle.to_json_dict()
                if self.lifecycle is not None
                else None
            ),
            "sandbox_authorization": (
                self.sandbox_authorization.to_json_dict()
                if self.sandbox_authorization is not None
                else None
            ),
        }


@dataclass(frozen=True, slots=True)
class SchedulerAuthorizationReadback:
    """Read-only scheduler authorization diagnostic product."""

    tasks: tuple[TaskAuthorizationSummary, ...]
    lifecycle_records: tuple[LeaseLifecycleSummary, ...] = ()
    orphan_lifecycle_records: tuple[LeaseLifecycleSummary, ...] = ()
    snapshot_path: str = ""
    scheduler_event_log_path: str = ""
    recovered_from_event_log: bool = False
    strict_replay: bool = True
    product_type: str = SCHEDULER_AUTHORIZATION_READBACK_PRODUCT_TYPE
    schema_version: str = SCHEDULER_AUTHORIZATION_READBACK_SCHEMA_VERSION
    metadata: Mapping[str, object] = field(default_factory=dict)

    @property
    def task_count(self) -> int:
        """Return total scheduler task count."""

        return len(self.tasks)

    @property
    def edit_lease_task_count(self) -> int:
        """Return task count with static edit lease declarations."""

        return sum(1 for task in self.tasks if task.has_edit_lease)

    @property
    def lifecycle_record_count(self) -> int:
        """Return total scheduler-owned lifecycle record count."""

        return len(self.lifecycle_records)

    @property
    def lifecycle_state_counts(self) -> dict[str, int]:
        """Return lifecycle record counts by lifecycle state."""

        counts: dict[str, int] = {}
        for record in self.lifecycle_records:
            counts[record.state] = counts.get(record.state, 0) + 1
        return dict(sorted(counts.items()))

    @property
    def sandbox_authorization_state_counts(self) -> dict[str, int]:
        """Return task sandbox authorization counts by allocation state."""

        counts: dict[str, int] = {}
        for task in self.tasks:
            authorization = task.sandbox_authorization
            state = authorization.allocation_state if authorization is not None else "missing"
            counts[state] = counts.get(state, 0) + 1
        return dict(sorted(counts.items()))

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-safe readback product."""

        return {
            "product_type": self.product_type,
            "schema_version": self.schema_version,
            "snapshot_path": self.snapshot_path,
            "scheduler_event_log_path": self.scheduler_event_log_path,
            "recovered_from_event_log": self.recovered_from_event_log,
            "strict_replay": self.strict_replay,
            "task_count": self.task_count,
            "edit_lease_task_count": self.edit_lease_task_count,
            "lifecycle_record_count": self.lifecycle_record_count,
            "lifecycle_state_counts": self.lifecycle_state_counts,
            "sandbox_authorization_state_counts": self.sandbox_authorization_state_counts,
            "tasks": [task.to_json_dict() for task in self.tasks],
            "lifecycle_records": [
                record.to_json_dict()
                for record in self.lifecycle_records
            ],
            "orphan_lifecycle_records": [
                record.to_json_dict()
                for record in self.orphan_lifecycle_records
            ],
            "orphan_lifecycle_record_count": len(self.orphan_lifecycle_records),
            "authority_split": {
                "scheduler_state_read": True,
                "scheduler_event_log_read": self.recovered_from_event_log,
                "scheduler_state_mutated": False,
                "scheduler_projection_refreshed": False,
                "runtime_provider_executed": False,
                "sandbox_metadata_evaluated": True,
                "real_sandbox_provider_executed": False,
                "exchange_artifact_store_mutated": False,
                "admission_ledger_mutated": False,
                "local_work_trajectory_mutated": False,
            },
            "metadata": dict(self.metadata),
        }


def inspect_scheduler_authorization(
    state: SchedulerState,
    *,
    workspace_root: str = "",
    scratch_root: str = DEFAULT_DBC_SCRATCH_ROOT,
    sandbox_allocations: Mapping[str, SandboxAllocation] | None = None,
    snapshot_path: str = "",
    scheduler_event_log_path: str = "",
    recovered_from_event_log: bool = False,
    strict_replay: bool = True,
    metadata: Mapping[str, object] | None = None,
) -> SchedulerAuthorizationReadback:
    """Build a read-only authorization summary from scheduler state."""

    lifecycle_records = tuple(
        _lease_lifecycle_summary(record)
        for record in sorted(
            state.edit_lease_lifecycle.values(),
            key=lambda item: (item.task_id, item.lease_id),
        )
    )
    task_summaries = tuple(
        _task_authorization_summary(
            task,
            lifecycle=(
                state.edit_lease_lifecycle.get(task.edit_lease.lease_id)
                if task.edit_lease is not None
                else None
            ),
            workspace_root=workspace_root,
            scratch_root=scratch_root,
            sandbox_allocation=(
                sandbox_allocations.get(task.task_id)
                if sandbox_allocations is not None
                else None
            ),
        )
        for task in sorted(state.tasks.values(), key=lambda item: item.task_id)
    )
    task_ids = set(state.tasks)
    task_lease_ids = {
        task.edit_lease.lease_id
        for task in state.tasks.values()
        if task.edit_lease is not None
    }
    orphan_records = tuple(
        summary
        for summary in lifecycle_records
        if summary.task_id not in task_ids or summary.lease_id not in task_lease_ids
    )
    return SchedulerAuthorizationReadback(
        tasks=task_summaries,
        lifecycle_records=lifecycle_records,
        orphan_lifecycle_records=orphan_records,
        snapshot_path=snapshot_path,
        scheduler_event_log_path=scheduler_event_log_path,
        recovered_from_event_log=recovered_from_event_log,
        strict_replay=strict_replay,
        metadata={} if metadata is None else metadata,
    )


def inspect_scheduler_authorization_snapshot(
    snapshot_path: str | Path,
    *,
    scheduler_event_log_path: str | Path | None = None,
    sandbox_allocation_evidence_path: str | Path | None = None,
    strict: bool = True,
    workspace_root: str = "",
    scratch_root: str = DEFAULT_DBC_SCRATCH_ROOT,
) -> SchedulerAuthorizationReadback:
    """Build authorization readback from persisted scheduler snapshot inputs."""

    snapshot = Path(snapshot_path)
    event_log = Path(scheduler_event_log_path) if scheduler_event_log_path else None
    if event_log is None:
        state = read_scheduler_state_snapshot(snapshot)
    else:
        state = recover_scheduler_state(snapshot, event_log, strict=strict).recovered_state
    allocation_evidence = (
        read_sandbox_allocation_receipt_evidence_summary(sandbox_allocation_evidence_path)
        if sandbox_allocation_evidence_path is not None
        else None
    )
    metadata: dict[str, object] = {}
    if allocation_evidence is not None:
        metadata["sandbox_allocation_evidence_path"] = str(allocation_evidence.evidence_path)
        metadata["sandbox_allocation_evidence_id"] = allocation_evidence.evidence_id
        metadata["sandbox_allocation_evidence_allocation_count"] = (
            allocation_evidence.allocation_count
        )
    return inspect_scheduler_authorization(
        state,
        workspace_root=workspace_root,
        scratch_root=scratch_root,
        sandbox_allocations=(
            allocation_evidence.allocations_by_task_id
            if allocation_evidence is not None
            else None
        ),
        snapshot_path=str(snapshot),
        scheduler_event_log_path="" if event_log is None else str(event_log),
        recovered_from_event_log=event_log is not None,
        strict_replay=strict,
        metadata=metadata,
    )


def _task_authorization_summary(
    task: ScheduledTask,
    *,
    lifecycle: EditLeaseLifecycleRecord | None,
    workspace_root: str,
    scratch_root: str,
    sandbox_allocation: SandboxAllocation | None = None,
) -> TaskAuthorizationSummary:
    lease = task.edit_lease
    lifecycle_summary = _lease_lifecycle_summary(lifecycle) if lifecycle is not None else None
    allocation = (
        sandbox_allocation
        if sandbox_allocation is not None
        else _sandbox_allocation_for_task(
            task,
            lifecycle=lifecycle,
            workspace_root=workspace_root,
            scratch_root=scratch_root,
        )
    )
    if lease is None:
        return TaskAuthorizationSummary(
            task_id=task.task_id,
            title=task.title,
            state=task.state,
            agent_id=task.agent.agent_id,
            runtime_provider=task.agent.runtime_provider,
            has_edit_lease=False,
            lifecycle_missing=False,
            sandbox_authorization=_sandbox_authorization_summary(allocation),
        )
    return TaskAuthorizationSummary(
        task_id=task.task_id,
        title=task.title,
        state=task.state,
        agent_id=task.agent.agent_id,
        runtime_provider=task.agent.runtime_provider,
        has_edit_lease=True,
        lease_id=lease.lease_id,
        lease_mode=lease.lease_mode,
        allowed_artifacts=lease.allowed_artifacts,
        denied_artifacts=lease.denied_artifacts,
        conflict_policy=lease.conflict_policy,
        lease_expires_at=lease.expires_at,
        lifecycle_missing=lifecycle is None,
        lifecycle=lifecycle_summary,
        sandbox_authorization=_sandbox_authorization_summary(allocation),
    )


def _sandbox_allocation_for_task(
    task: ScheduledTask,
    *,
    lifecycle: EditLeaseLifecycleRecord | None,
    workspace_root: str,
    scratch_root: str,
) -> SandboxAllocation:
    provider = SharedProcessSandboxProvider()
    return provider.allocate(
        SandboxRequest(
            task_id=task.task_id,
            profile=task.sandbox_profile,
            edit_lease=task.edit_lease,
            edit_lease_lifecycle=lifecycle,
            workspace_root=workspace_root,
            scratch_path=_scratch_path_for_task(task, scratch_root=scratch_root),
            required_mounts=_required_mounts_for_task(task),
            metadata={
                "context_id": task.context_scope.context_id,
                "lane_id": task.context_scope.lane_id,
                "agent_id": task.agent.agent_id,
                "readback_only": True,
            },
        )
    )


def _sandbox_authorization_summary(
    allocation: SandboxAllocation,
) -> SandboxAuthorizationSummary:
    return SandboxAuthorizationSummary(
        profile_id=allocation.profile.profile_id,
        profile_kind=allocation.profile.profile_kind,
        mount_policy=allocation.profile.mount_policy,
        allocation_state=allocation.state,
        allocation_reason=allocation.reason,
        visible_mounts=allocation.visible_mounts,
        lease_authorization_state=allocation.lease_authorization_state,
        lease_authorization_reason=allocation.lease_authorization_reason,
        lease_authorizations=tuple(
            _lease_authorization_summary(item)
            for item in allocation.lease_authorized_mounts
        ),
        git_worktree_receipt=_git_worktree_receipt_summary(allocation),
    )


def _lease_authorization_summary(
    authorization: SandboxLeaseMountAuthorization,
) -> SandboxLeaseAuthorizationSummary:
    return SandboxLeaseAuthorizationSummary(
        lease_id=authorization.lease_id,
        task_id=authorization.task_id,
        lifecycle_state=authorization.lifecycle_state,
        authorized_mounts=authorization.authorized_mounts,
        denied_mounts=authorization.denied_mounts,
        reason=authorization.reason,
    )


def _git_worktree_receipt_summary(
    allocation: SandboxAllocation,
) -> GitWorktreeReceiptSummary | None:
    receipt = allocation.git_worktree_receipt
    if receipt is None:
        return None
    cleanup_required = allocation.cleanup_required or receipt.cleanup_state == "required"
    return GitWorktreeReceiptSummary(
        source_repository_root=receipt.source_repository_root,
        sandbox_root=receipt.sandbox_root,
        worktree_path=receipt.worktree_path,
        branch_name=receipt.branch_name,
        base_ref=receipt.base_ref,
        authorized_writable_paths=receipt.authorized_writable_paths,
        denied_writable_paths=receipt.denied_writable_paths,
        cleanup_state=receipt.cleanup_state,
        cleanup_required=cleanup_required,
        cleanup_owner=(
            "host-or-daemon"
            if cleanup_required
            else "none"
        ),
        cleanup_policy=(
            "explicit-cleanup-required"
            if cleanup_required
            else "no-cleanup-required"
        ),
        allocation=_git_worktree_command_receipt_summary(receipt.allocation),
        cleanup=_git_worktree_command_receipt_summary(receipt.cleanup),
        branch_cleanup=_git_worktree_command_receipt_summary(receipt.branch_cleanup),
    )


def _git_worktree_command_receipt_summary(
    receipt: GitWorktreeCommandReceipt,
) -> GitWorktreeCommandReceiptSummary:
    return GitWorktreeCommandReceiptSummary(
        command=receipt.command,
        returncode=receipt.returncode,
        stdout=receipt.stdout,
        stderr=receipt.stderr,
    )


def _lease_lifecycle_summary(
    record: EditLeaseLifecycleRecord,
) -> LeaseLifecycleSummary:
    conflict = record.conflict_decision
    return LeaseLifecycleSummary(
        lease_id=record.lease_id,
        task_id=record.task_id,
        state=record.state,
        mode=record.mode,
        allowed_artifacts=record.allowed_artifacts,
        denied_artifacts=record.denied_artifacts,
        conflict_policy=record.conflict_policy,
        acquired_at=record.acquired_at,
        expires_at=record.expires_at,
        released_at=record.released_at,
        reason=record.reason,
        conflict_state=conflict.state if conflict is not None else "",
        conflict_classification=(
            conflict.classification
            if conflict is not None
            else ""
        ),
        conflict_left_task_id=conflict.left_task_id if conflict is not None else "",
        conflict_right_task_id=conflict.right_task_id if conflict is not None else "",
        conflict_left_path=conflict.left_path if conflict is not None else "",
        conflict_right_path=conflict.right_path if conflict is not None else "",
    )


def _required_mounts_for_task(task: ScheduledTask) -> tuple[str, ...]:
    mounts = [
        ref.path
        for ref in (*task.context_scope.required_refs, *task.input_artifact_refs)
        if ref.path
    ]
    return tuple(dict.fromkeys(mounts))


def _scratch_path_for_task(task: ScheduledTask, *, scratch_root: str) -> str:
    normalized_root = scratch_root.rstrip("/\\")
    return f"{normalized_root}/{task.task_id}" if normalized_root else task.task_id
