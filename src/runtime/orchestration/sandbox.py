"""Sandbox provider contracts for orchestration-owned execution isolation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

from .scheduler import EditLeaseLifecycleRecord, EditScopeLease, SandboxProfile, SandboxProfileKind

SandboxProviderKind = SandboxProfileKind
SandboxAllocationState = Literal["allocated", "rejected"]
SandboxLeaseAuthorizationState = Literal["not_required", "authorized", "rejected"]


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
            notes="placeholder only; provider implementation is not available",
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
