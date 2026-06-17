"""Sandbox provider contracts for orchestration-owned execution isolation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

from .scheduler import EditScopeLease, SandboxProfile, SandboxProfileKind

SandboxProviderKind = SandboxProfileKind
SandboxAllocationState = Literal["allocated", "rejected"]


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
    workspace_root: str = ""
    scratch_path: str = ""
    required_mounts: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


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
    lease = request.edit_lease
    if lease is not None and request.profile.mount_policy == "lease-scoped":
        mounts.extend(lease.allowed_artifacts)
    return tuple(dict.fromkeys(mounts))
