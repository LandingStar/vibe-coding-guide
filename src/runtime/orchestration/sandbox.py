"""Sandbox provider contracts for orchestration-owned execution isolation."""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal, Protocol

from .scheduler import EditLeaseLifecycleRecord, EditScopeLease, SandboxProfile, SandboxProfileKind

SandboxProviderKind = SandboxProfileKind
SandboxAllocationState = Literal["allocated", "rejected"]
SandboxLeaseAuthorizationState = Literal["not_required", "authorized", "rejected"]
GitWorktreeCleanupState = Literal["not_required", "required", "completed", "failed"]


@dataclass(frozen=True, slots=True)
class SandboxCapability:
    """Capability metadata advertised by one sandbox provider."""

    provider: SandboxProviderKind
    supports_process_isolation: bool = False
    supports_filesystem_isolation: bool = False
    supports_network_policy: bool = False
    supports_secret_policy: bool = False
    supports_mount_policy: bool = False
    supports_cleanup: bool = False
    notes: str = ""


@dataclass(frozen=True, slots=True)
class SandboxRequest:
    """Scheduler-owned request for an execution isolation allocation."""

    task_id: str
    profile: SandboxProfile
    edit_lease: EditScopeLease | None = None
    edit_lease_lifecycle: EditLeaseLifecycleRecord | None = None
    workspace_root: str = ""
    scratch_path: str = ""
    required_mounts: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SandboxLeaseMountAuthorization:
    """Metadata describing which mounts were authorized by one edit lease."""

    lease_id: str = ""
    task_id: str = ""
    lifecycle_state: str = ""
    authorized_mounts: tuple[str, ...] = ()
    denied_mounts: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class GitWorktreeCommandReceipt:
    """Command receipt captured by the git-worktree sandbox provider."""

    command: tuple[str, ...] = ()
    returncode: int | None = None
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True, slots=True)
class GitWorktreeSandboxReceipt:
    """Inspectable receipt for one git-worktree sandbox allocation."""

    source_repository_root: str = ""
    sandbox_root: str = ""
    worktree_path: str = ""
    branch_name: str = ""
    base_ref: str = "HEAD"
    authorized_writable_paths: tuple[str, ...] = ()
    denied_writable_paths: tuple[str, ...] = ()
    cleanup_state: GitWorktreeCleanupState = "not_required"
    allocation: GitWorktreeCommandReceipt = field(default_factory=GitWorktreeCommandReceipt)
    cleanup: GitWorktreeCommandReceipt = field(default_factory=GitWorktreeCommandReceipt)
    branch_cleanup: GitWorktreeCommandReceipt = field(default_factory=GitWorktreeCommandReceipt)


@dataclass(frozen=True, slots=True)
class SandboxAllocation:
    """Metadata describing an admitted sandbox allocation."""

    allocation_id: str
    provider: SandboxProviderKind
    task_id: str
    profile: SandboxProfile
    state: SandboxAllocationState = "allocated"
    workspace_root: str = ""
    scratch_path: str = ""
    visible_mounts: tuple[str, ...] = ()
    network_policy: str = ""
    secret_policy: str = ""
    cleanup_required: bool = False
    lease_authorized_mounts: tuple[SandboxLeaseMountAuthorization, ...] = ()
    lease_authorization_state: SandboxLeaseAuthorizationState = "not_required"
    lease_authorization_reason: str = ""
    git_worktree_receipt: GitWorktreeSandboxReceipt | None = None
    reason: str = ""


class SandboxProvider(Protocol):
    """Contract implemented by execution isolation providers."""

    def capability(self) -> SandboxCapability:
        """Return provider capability metadata."""
        ...

    def allocate(self, request: SandboxRequest) -> SandboxAllocation:
        """Allocate or reject an execution sandbox for a scheduled task."""
        ...


class SandboxProviderRegistry:
    """Provider-keyed registry for sandbox allocation backends."""

    def __init__(self) -> None:
        self._providers: dict[SandboxProviderKind, SandboxProvider] = {}

    def register(
        self,
        provider: SandboxProvider,
        *,
        provider_kind: SandboxProviderKind | None = None,
        replace_existing: bool = False,
    ) -> SandboxProvider:
        """Register a sandbox provider under its advertised provider kind."""

        capability_provider = provider.capability().provider
        key = provider_kind or capability_provider
        if key != capability_provider:
            raise ValueError(
                f"sandbox provider mismatch: key {key!r} does not match "
                f"capability provider {capability_provider!r}"
            )
        if key in self._providers and not replace_existing:
            raise ValueError(f"sandbox provider already registered for {key!r}")
        self._providers[key] = provider
        return provider

    def get(self, provider: SandboxProviderKind) -> SandboxProvider:
        """Return a registered sandbox provider or raise a readable KeyError."""

        try:
            return self._providers[provider]
        except KeyError as exc:
            available = ", ".join(sorted(self._providers)) or "(none)"
            raise KeyError(
                f"no sandbox provider registered for {provider!r}; "
                f"available providers: {available}"
            ) from exc

    def providers(self) -> tuple[SandboxProviderKind, ...]:
        """Return registered provider kinds in deterministic order."""

        return tuple(sorted(self._providers))


class SharedProcessSandboxProvider:
    """Metadata-only provider for the current shared process environment."""

    def capability(self) -> SandboxCapability:
        return SandboxCapability(
            provider="shared-process",
            supports_process_isolation=False,
            supports_filesystem_isolation=False,
            supports_network_policy=False,
            supports_secret_policy=True,
            supports_mount_policy=True,
            supports_cleanup=False,
            notes="metadata-only shared process allocation; no process isolation",
        )

    def allocate(self, request: SandboxRequest) -> SandboxAllocation:
        profile = request.profile
        if profile.profile_kind != "shared-process":
            return SandboxAllocation(
                allocation_id=f"rejected:{request.task_id}:{profile.profile_id}",
                provider="shared-process",
                task_id=request.task_id,
                profile=profile,
                state="rejected",
                reason=(
                    "SharedProcessSandboxProvider can only allocate "
                    "profile_kind='shared-process'"
                ),
            )
        lease_authorization = _lease_mount_authorization_from_request(request)
        if lease_authorization.denied_mounts:
            return SandboxAllocation(
                allocation_id=f"rejected:{request.task_id}:{profile.profile_id}",
                provider="shared-process",
                task_id=request.task_id,
                profile=profile,
                state="rejected",
                workspace_root=request.workspace_root,
                scratch_path=request.scratch_path,
                visible_mounts=tuple(dict.fromkeys(request.required_mounts)),
                network_policy=profile.network_policy,
                secret_policy=profile.secret_policy,
                cleanup_required=False,
                lease_authorized_mounts=(lease_authorization,),
                lease_authorization_state="rejected",
                lease_authorization_reason=lease_authorization.reason,
                reason=lease_authorization.reason,
            )
        lease_authorized_mounts = (
            (lease_authorization,)
            if lease_authorization.lifecycle_state == "acquired"
            else ()
        )
        return SandboxAllocation(
            allocation_id=f"shared-process:{request.task_id}:{profile.profile_id}",
            provider="shared-process",
            task_id=request.task_id,
            profile=profile,
            workspace_root=request.workspace_root,
            scratch_path=request.scratch_path,
            visible_mounts=_visible_mounts_from_request(request),
            network_policy=profile.network_policy,
            secret_policy=profile.secret_policy,
            cleanup_required=False,
            lease_authorized_mounts=lease_authorized_mounts,
            lease_authorization_state=(
                "authorized" if lease_authorized_mounts else "not_required"
            ),
            lease_authorization_reason=lease_authorization.reason,
        )


class GitWorktreeSandboxProvider:
    """Filesystem-isolating sandbox provider backed by ``git worktree``."""

    def __init__(
        self,
        sandbox_root: str | Path,
        *,
        git_executable: str = "git",
        base_ref: str = "HEAD",
        branch_prefix: str = "dbc-sandbox",
    ) -> None:
        if not str(sandbox_root):
            raise ValueError("git-worktree sandbox_root must be explicit")
        self._sandbox_root = Path(sandbox_root)
        self._git_executable = git_executable
        self._base_ref = base_ref
        self._branch_prefix = branch_prefix.strip("/") or "dbc-sandbox"

    def capability(self) -> SandboxCapability:
        return SandboxCapability(
            provider="git-worktree",
            supports_process_isolation=False,
            supports_filesystem_isolation=True,
            supports_network_policy=False,
            supports_secret_policy=True,
            supports_mount_policy=True,
            supports_cleanup=True,
            notes="git worktree filesystem isolation under an explicit sandbox root",
        )

    def allocate(self, request: SandboxRequest) -> SandboxAllocation:
        profile = request.profile
        if profile.profile_kind != "git-worktree":
            return SandboxAllocation(
                allocation_id=f"rejected:{request.task_id}:{profile.profile_id}",
                provider="git-worktree",
                task_id=request.task_id,
                profile=profile,
                state="rejected",
                reason=(
                    "GitWorktreeSandboxProvider can only allocate "
                    "profile_kind='git-worktree'"
                ),
            )

        lease_authorization = _lease_mount_authorization_from_request(request)
        receipt = self._receipt_for_request(
            request,
            lease_authorization=lease_authorization,
        )
        if lease_authorization.denied_mounts:
            return SandboxAllocation(
                allocation_id=f"rejected:{request.task_id}:{profile.profile_id}",
                provider="git-worktree",
                task_id=request.task_id,
                profile=profile,
                state="rejected",
                workspace_root=request.workspace_root,
                scratch_path=request.scratch_path,
                visible_mounts=tuple(dict.fromkeys(request.required_mounts)),
                network_policy=profile.network_policy,
                secret_policy=profile.secret_policy,
                cleanup_required=False,
                lease_authorized_mounts=(lease_authorization,),
                lease_authorization_state="rejected",
                lease_authorization_reason=lease_authorization.reason,
                git_worktree_receipt=receipt,
                reason=lease_authorization.reason,
            )

        source_root = Path(request.workspace_root) if request.workspace_root else None
        if source_root is None or not source_root.is_dir():
            reason = "git-worktree allocation requires an existing workspace_root git repository"
            return SandboxAllocation(
                allocation_id=f"rejected:{request.task_id}:{profile.profile_id}",
                provider="git-worktree",
                task_id=request.task_id,
                profile=profile,
                state="rejected",
                workspace_root=request.workspace_root,
                scratch_path=request.scratch_path,
                visible_mounts=tuple(dict.fromkeys(request.required_mounts)),
                network_policy=profile.network_policy,
                secret_policy=profile.secret_policy,
                cleanup_required=False,
                lease_authorized_mounts=(),
                lease_authorization_state=_authorization_state_for(lease_authorization),
                lease_authorization_reason=lease_authorization.reason,
                git_worktree_receipt=receipt,
                reason=reason,
            )

        worktree_path = Path(receipt.worktree_path)
        if worktree_path.exists():
            reason = f"git-worktree allocation target already exists: {worktree_path}"
            return SandboxAllocation(
                allocation_id=f"rejected:{request.task_id}:{profile.profile_id}",
                provider="git-worktree",
                task_id=request.task_id,
                profile=profile,
                state="rejected",
                workspace_root=request.workspace_root,
                scratch_path=request.scratch_path,
                visible_mounts=tuple(dict.fromkeys(request.required_mounts)),
                network_policy=profile.network_policy,
                secret_policy=profile.secret_policy,
                cleanup_required=False,
                lease_authorized_mounts=(),
                lease_authorization_state=_authorization_state_for(lease_authorization),
                lease_authorization_reason=lease_authorization.reason,
                git_worktree_receipt=receipt,
                reason=reason,
            )

        try:
            self._sandbox_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            reason = f"failed to create git-worktree sandbox root: {exc}"
            return SandboxAllocation(
                allocation_id=f"rejected:{request.task_id}:{profile.profile_id}",
                provider="git-worktree",
                task_id=request.task_id,
                profile=profile,
                state="rejected",
                workspace_root=request.workspace_root,
                scratch_path=request.scratch_path,
                visible_mounts=tuple(dict.fromkeys(request.required_mounts)),
                network_policy=profile.network_policy,
                secret_policy=profile.secret_policy,
                cleanup_required=False,
                lease_authorized_mounts=(),
                lease_authorization_state=_authorization_state_for(lease_authorization),
                lease_authorization_reason=lease_authorization.reason,
                git_worktree_receipt=receipt,
                reason=reason,
            )

        command = (
            self._git_executable,
            "-C",
            str(source_root),
            "worktree",
            "add",
            "-b",
            receipt.branch_name,
            receipt.worktree_path,
            self._base_ref,
        )
        result = self._run_git_command(command)
        receipt = replace(
            receipt,
            allocation=result,
            cleanup_state="required" if result.returncode == 0 else "not_required",
        )
        if result.returncode != 0:
            reason = result.stderr.strip() or result.stdout.strip() or "git worktree add failed"
            return SandboxAllocation(
                allocation_id=f"rejected:{request.task_id}:{profile.profile_id}",
                provider="git-worktree",
                task_id=request.task_id,
                profile=profile,
                state="rejected",
                workspace_root=request.workspace_root,
                scratch_path=request.scratch_path,
                visible_mounts=tuple(dict.fromkeys(request.required_mounts)),
                network_policy=profile.network_policy,
                secret_policy=profile.secret_policy,
                cleanup_required=False,
                lease_authorized_mounts=(),
                lease_authorization_state=_authorization_state_for(lease_authorization),
                lease_authorization_reason=lease_authorization.reason,
                git_worktree_receipt=receipt,
                reason=reason,
            )

        lease_authorized_mounts = (
            (lease_authorization,)
            if lease_authorization.lifecycle_state == "acquired"
            else ()
        )
        return SandboxAllocation(
            allocation_id=f"git-worktree:{request.task_id}:{profile.profile_id}",
            provider="git-worktree",
            task_id=request.task_id,
            profile=profile,
            workspace_root=request.workspace_root,
            scratch_path=request.scratch_path,
            visible_mounts=_visible_mounts_from_request(request),
            network_policy=profile.network_policy,
            secret_policy=profile.secret_policy,
            cleanup_required=True,
            lease_authorized_mounts=lease_authorized_mounts,
            lease_authorization_state=(
                "authorized" if lease_authorized_mounts else "not_required"
            ),
            lease_authorization_reason=lease_authorization.reason,
            git_worktree_receipt=receipt,
        )

    def cleanup(self, allocation: SandboxAllocation) -> SandboxAllocation:
        """Remove an allocated worktree and its deterministic branch."""

        receipt = allocation.git_worktree_receipt
        if allocation.provider != "git-worktree" or receipt is None:
            return allocation
        if (
            allocation.state != "allocated"
            or not allocation.cleanup_required
            or receipt.cleanup_state != "required"
        ):
            return allocation
        if not receipt.worktree_path:
            return replace(
                allocation,
                cleanup_required=False,
                git_worktree_receipt=replace(receipt, cleanup_state="not_required"),
            )

        remove_command = (
            self._git_executable,
            "-C",
            receipt.source_repository_root,
            "worktree",
            "remove",
            "--force",
            receipt.worktree_path,
        )
        remove_result = self._run_git_command(remove_command)
        branch_command = (
            self._git_executable,
            "-C",
            receipt.source_repository_root,
            "branch",
            "-D",
            receipt.branch_name,
        )
        branch_result = (
            self._run_git_command(branch_command)
            if remove_result.returncode == 0 and receipt.branch_name
            else GitWorktreeCommandReceipt()
        )
        cleanup_state: GitWorktreeCleanupState = (
            "completed"
            if remove_result.returncode == 0 and branch_result.returncode == 0
            else "failed"
        )
        updated_receipt = replace(
            receipt,
            cleanup_state=cleanup_state,
            cleanup=remove_result,
            branch_cleanup=branch_result,
        )
        return replace(
            allocation,
            cleanup_required=cleanup_state != "completed",
            git_worktree_receipt=updated_receipt,
            reason="" if cleanup_state == "completed" else "git-worktree cleanup failed",
        )

    def _receipt_for_request(
        self,
        request: SandboxRequest,
        *,
        lease_authorization: SandboxLeaseMountAuthorization,
    ) -> GitWorktreeSandboxReceipt:
        source_root = str(Path(request.workspace_root)) if request.workspace_root else ""
        slug = _stable_worktree_slug(request.task_id, request.profile.profile_id)
        worktree_path = self._sandbox_root / slug
        branch_name = f"{self._branch_prefix}/{slug}"
        return GitWorktreeSandboxReceipt(
            source_repository_root=source_root,
            sandbox_root=str(self._sandbox_root),
            worktree_path=str(worktree_path),
            branch_name=branch_name,
            base_ref=self._base_ref,
            authorized_writable_paths=lease_authorization.authorized_mounts,
            denied_writable_paths=lease_authorization.denied_mounts,
            cleanup_state="not_required",
        )

    @staticmethod
    def _run_git_command(command: tuple[str, ...]) -> GitWorktreeCommandReceipt:
        try:
            completed = subprocess.run(
                command,
                check=False,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as exc:
            return GitWorktreeCommandReceipt(
                command=command,
                returncode=-1,
                stderr=str(exc),
            )
        return GitWorktreeCommandReceipt(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


def sandbox_capability_placeholder(provider: SandboxProviderKind) -> SandboxCapability:
    """Return capability shape for providers not implemented in this slice."""

    if provider == "none":
        return SandboxCapability(
            provider="none",
            notes="no execution sandbox; incompatible with edit-lease tasks",
        )
    if provider == "git-worktree":
        return SandboxCapability(
            provider="git-worktree",
            supports_filesystem_isolation=True,
            supports_mount_policy=True,
            supports_cleanup=True,
            notes="provider implementation requires registration with an explicit sandbox root",
        )
    if provider == "docker":
        return SandboxCapability(
            provider="docker",
            supports_process_isolation=True,
            supports_filesystem_isolation=True,
            supports_network_policy=True,
            supports_secret_policy=True,
            supports_mount_policy=True,
            supports_cleanup=True,
            notes="placeholder only; provider implementation is not available",
        )
    if provider == "remote-vm":
        return SandboxCapability(
            provider="remote-vm",
            supports_process_isolation=True,
            supports_filesystem_isolation=True,
            supports_network_policy=True,
            supports_secret_policy=True,
            supports_mount_policy=True,
            supports_cleanup=True,
            notes="placeholder only; provider implementation is not available",
        )
    return SharedProcessSandboxProvider().capability()


def _stable_worktree_slug(task_id: str, profile_id: str) -> str:
    raw = f"{task_id}-{profile_id}"
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("._-") or "sandbox"
    slug = slug[:72].strip("._-") or "sandbox"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{slug}-{digest}"


def _authorization_state_for(
    lease_authorization: SandboxLeaseMountAuthorization,
) -> SandboxLeaseAuthorizationState:
    if lease_authorization.denied_mounts:
        return "rejected"
    if lease_authorization.lifecycle_state == "acquired":
        return "authorized"
    return "not_required"


def _visible_mounts_from_request(request: SandboxRequest) -> tuple[str, ...]:
    mounts = list(request.required_mounts)
    lease_authorization = _lease_mount_authorization_from_request(request)
    if lease_authorization.lifecycle_state == "acquired":
        mounts.extend(lease_authorization.authorized_mounts)
    return tuple(dict.fromkeys(mounts))


def _lease_mount_authorization_from_request(
    request: SandboxRequest,
) -> SandboxLeaseMountAuthorization:
    lease = request.edit_lease
    if lease is None or request.profile.mount_policy != "lease-scoped":
        return SandboxLeaseMountAuthorization(reason="lease-scoped mounts not required")

    lifecycle = request.edit_lease_lifecycle
    if lifecycle is None:
        return SandboxLeaseMountAuthorization(
            lease_id=lease.lease_id,
            task_id=request.task_id,
            lifecycle_state="missing",
            denied_mounts=lease.allowed_artifacts,
            reason=(
                f"lease-scoped mounts for task {request.task_id!r} require "
                f"acquired edit lease lifecycle record {lease.lease_id!r}"
            ),
        )

    if lifecycle.lease_id != lease.lease_id or lifecycle.task_id != request.task_id:
        return SandboxLeaseMountAuthorization(
            lease_id=lease.lease_id,
            task_id=request.task_id,
            lifecycle_state=lifecycle.state,
            denied_mounts=lease.allowed_artifacts,
            reason=(
                f"edit lease lifecycle record mismatch for task {request.task_id!r}: "
                f"expected lease {lease.lease_id!r}, got {lifecycle.lease_id!r}"
            ),
        )

    if lifecycle.state != "acquired":
        return SandboxLeaseMountAuthorization(
            lease_id=lease.lease_id,
            task_id=request.task_id,
            lifecycle_state=lifecycle.state,
            denied_mounts=lease.allowed_artifacts,
            reason=(
                f"lease-scoped mounts for task {request.task_id!r} require "
                f"acquired edit lease {lease.lease_id!r}; current lifecycle "
                f"state is {lifecycle.state!r}"
            ),
        )

    return SandboxLeaseMountAuthorization(
        lease_id=lease.lease_id,
        task_id=request.task_id,
        lifecycle_state="acquired",
        authorized_mounts=lifecycle.allowed_artifacts,
        reason=f"lease-scoped mounts authorized by acquired edit lease {lease.lease_id}",
    )
