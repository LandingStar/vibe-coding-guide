"""Host-facing runtime adapter registry wiring helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .exchange_store import InMemoryArtifactVersionStore, JsonlCoordinationEventLog
from .runtime_adapter import (
    AgentRuntimeAdapterRegistry,
    CodexCliAgentRuntimeAdapter,
    CodexCliClient,
    FakeAgentRuntimeAdapter,
    OpenCodeCliAgentRuntimeAdapter,
    OpenCodeCliClient,
    QoderAgentRuntimeAdapter,
    QoderQueryClient,
    RuntimeProviderKind,
)

RuntimeHostSurfaceKind = Literal[
    "mcp-scheduler-run-once",
    "cli-scheduler-run-once",
    "host-authorized-adapter",
]


@dataclass(frozen=True, slots=True)
class RuntimeProviderPermissionGrant:
    """Auditable host permission grant for registering a real runtime provider.

    The grant records that a host layer has approved injecting a runtime client.
    It is not stored in scheduler state and does not approve individual runtime
    tool, shell, network, or artifact permission requests.
    """

    grant_id: str
    provider: RuntimeProviderKind
    approved_by: str
    approved_at: str
    scope: str = ""
    allow_sdk_client: bool = False
    allow_process_spawn: bool = False
    allow_network: bool = False
    notes: str = ""


@dataclass(frozen=True, slots=True)
class RuntimeHostInvocation:
    """Host surface request to build a runtime registry for one invocation.

    This product records which host surface is asking for runtime wiring. It is
    not scheduler state and does not carry a live SDK client.
    """

    surface: RuntimeHostSurfaceKind
    invocation_id: str
    requested_providers: tuple[RuntimeProviderKind, ...] = ("fake",)
    requested_by: str = ""
    reason: str = ""


@dataclass(frozen=True, slots=True)
class RuntimeRegistryWiringConfig:
    """Configuration for building a runtime adapter registry.

    This is a host wiring product, not scheduler state. The scheduler should
    receive a registry instance after the host has decided which providers are
    allowed and how real runtime clients are injected.
    """

    providers: tuple[RuntimeProviderKind, ...] = ("fake",)
    timestamp: str = ""
    qoder_permission_grant: RuntimeProviderPermissionGrant | None = None
    codex_permission_grant: RuntimeProviderPermissionGrant | None = None
    opencode_permission_grant: RuntimeProviderPermissionGrant | None = None
    host_invocation: RuntimeHostInvocation | None = None
    opencode_session_ledger_path: str | Path = ""
    opencode_enable_session_lookup: bool = False
    continuous_worker_binding_ledger_path: str | Path = ""
    enable_continuous_worker_binding_lookup: bool = False
    continuous_worker_context_bundle_dir_path: str | Path = ""


@dataclass(frozen=True, slots=True)
class RuntimeRegistryWiringResult:
    """Built runtime registry plus compact host-facing wiring metadata."""

    registry: AgentRuntimeAdapterRegistry
    config: RuntimeRegistryWiringConfig
    registered_providers: tuple[RuntimeProviderKind, ...]


def build_runtime_registry_from_config(
    config: RuntimeRegistryWiringConfig | None = None,
    *,
    artifact_store: InMemoryArtifactVersionStore | None = None,
    coordination_event_log: JsonlCoordinationEventLog | None = None,
    qoder_query_client: QoderQueryClient | None = None,
    codex_cli_client: CodexCliClient | None = None,
    opencode_cli_client: OpenCodeCliClient | None = None,
) -> RuntimeRegistryWiringResult:
    """Build an instance-scoped runtime registry from explicit host config.

    The default registers only the deterministic fake runtime. A qoder adapter
    can be registered only when the host supplies a valid
    ``RuntimeProviderPermissionGrant`` and injects a ``QoderQueryClient``. This
    keeps real runtime authority outside scheduler state and avoids accidental
    SDK execution from smoke paths.
    """

    active_config = config or RuntimeRegistryWiringConfig()
    _validate_host_invocation(active_config)
    providers = _normalize_providers(active_config.providers)
    registry = AgentRuntimeAdapterRegistry()
    store = artifact_store or InMemoryArtifactVersionStore()

    for provider in providers:
        if provider == "fake":
            registry.register(
                FakeAgentRuntimeAdapter(
                    artifact_store=store,
                    event_log=coordination_event_log,
                    timestamp=active_config.timestamp,
                )
            )
            continue
        if provider == "qoder":
            _validate_qoder_permission_grant(active_config.qoder_permission_grant)
            if qoder_query_client is None:
                raise ValueError(
                    "runtime provider 'qoder' requires an injected QoderQueryClient; "
                    "the orchestration layer must not import or construct the real SDK client"
                )
            registry.register(
                QoderAgentRuntimeAdapter(
                    query_client=qoder_query_client,
                    timestamp=active_config.timestamp,
                )
            )
            continue
        if provider == "codex":
            _validate_codex_permission_grant(active_config.codex_permission_grant)
            if codex_cli_client is None:
                raise ValueError(
                    "runtime provider 'codex' requires an injected CodexCliClient; "
                    "the orchestration layer must not spawn Codex CLI directly"
                )
            registry.register(
                CodexCliAgentRuntimeAdapter(
                    cli_client=codex_cli_client,
                    timestamp=active_config.timestamp,
                )
            )
            continue
        if provider == "opencode":
            _validate_opencode_permission_grant(active_config.opencode_permission_grant)
            if opencode_cli_client is None:
                raise ValueError(
                    "runtime provider 'opencode' requires an injected OpenCodeCliClient; "
                    "the orchestration layer must not spawn OpenCode CLI directly"
                )
            registry.register(
                OpenCodeCliAgentRuntimeAdapter(
                    cli_client=opencode_cli_client,
                    timestamp=active_config.timestamp,
                    session_ledger_path=active_config.opencode_session_ledger_path,
                    enable_session_lookup=active_config.opencode_enable_session_lookup,
                    continuous_worker_binding_ledger_path=(
                        active_config.continuous_worker_binding_ledger_path
                    ),
                    enable_continuous_worker_binding_lookup=(
                        active_config.enable_continuous_worker_binding_lookup
                    ),
                    continuous_worker_context_bundle_dir_path=(
                        active_config.continuous_worker_context_bundle_dir_path
                    ),
                )
            )
            continue
        raise ValueError(f"unsupported runtime provider in registry wiring: {provider!r}")

    return RuntimeRegistryWiringResult(
        registry=registry,
        config=active_config,
        registered_providers=registry.providers(),
    )


def _normalize_providers(
    providers: tuple[RuntimeProviderKind, ...],
) -> tuple[RuntimeProviderKind, ...]:
    normalized: list[RuntimeProviderKind] = []
    for provider in providers:
        if provider not in ("fake", "qoder", "codex", "opencode"):
            raise ValueError(f"unsupported runtime provider in registry wiring: {provider!r}")
        if provider not in normalized:
            normalized.append(provider)
    if not normalized:
        raise ValueError("runtime registry wiring requires at least one provider")
    return tuple(normalized)


def _validate_host_invocation(config: RuntimeRegistryWiringConfig) -> None:
    invocation = config.host_invocation
    if invocation is None:
        return
    if not invocation.invocation_id:
        raise ValueError("runtime host invocation requires invocation_id")
    if not invocation.requested_providers:
        raise ValueError("runtime host invocation requires requested_providers")
    requested = _normalize_providers(invocation.requested_providers)
    configured = _normalize_providers(config.providers)
    if requested != configured:
        raise ValueError(
            "runtime host invocation requested_providers must match "
            "RuntimeRegistryWiringConfig.providers"
        )
    if invocation.surface in {"mcp-scheduler-run-once", "cli-scheduler-run-once"}:
        if configured != ("fake",):
            raise ValueError(
                f"runtime host surface {invocation.surface!r} is fake-only; "
                f"requested providers: {', '.join(configured)}"
            )
    elif invocation.surface == "host-authorized-adapter":
        return
    else:
        raise ValueError(f"unsupported runtime host surface: {invocation.surface!r}")


def _validate_qoder_permission_grant(
    grant: RuntimeProviderPermissionGrant | None,
) -> RuntimeProviderPermissionGrant:
    if grant is None:
        raise ValueError(
            "runtime provider 'qoder' requires a RuntimeProviderPermissionGrant; "
            "real runtime providers must be host-authorized before registry construction"
        )
    if grant.provider != "qoder":
        raise ValueError(
            f"runtime provider 'qoder' requires a qoder permission grant; got {grant.provider!r}"
        )
    if not grant.grant_id:
        raise ValueError("qoder permission grant requires grant_id")
    if not grant.approved_by:
        raise ValueError("qoder permission grant requires approved_by")
    if not grant.approved_at:
        raise ValueError("qoder permission grant requires approved_at")
    if not grant.allow_sdk_client:
        raise ValueError(
            "qoder permission grant must set allow_sdk_client=True before "
            "a QoderQueryClient can be registered"
        )
    return grant


def _validate_codex_permission_grant(
    grant: RuntimeProviderPermissionGrant | None,
) -> RuntimeProviderPermissionGrant:
    if grant is None:
        raise ValueError(
            "runtime provider 'codex' requires a RuntimeProviderPermissionGrant; "
            "process-spawning runtime providers must be host-authorized before registry construction"
        )
    if grant.provider != "codex":
        raise ValueError(
            f"runtime provider 'codex' requires a codex permission grant; got {grant.provider!r}"
        )
    if not grant.grant_id:
        raise ValueError("codex permission grant requires grant_id")
    if not grant.approved_by:
        raise ValueError("codex permission grant requires approved_by")
    if not grant.approved_at:
        raise ValueError("codex permission grant requires approved_at")
    if not grant.allow_process_spawn:
        raise ValueError(
            "codex permission grant must set allow_process_spawn=True before "
            "a CodexCliClient can be registered"
        )
    return grant


def _validate_opencode_permission_grant(
    grant: RuntimeProviderPermissionGrant | None,
) -> RuntimeProviderPermissionGrant:
    if grant is None:
        raise ValueError(
            "runtime provider 'opencode' requires a RuntimeProviderPermissionGrant; "
            "process-spawning runtime providers must be host-authorized before registry construction"
        )
    if grant.provider != "opencode":
        raise ValueError(
            f"runtime provider 'opencode' requires an opencode permission grant; got {grant.provider!r}"
        )
    if not grant.grant_id:
        raise ValueError("opencode permission grant requires grant_id")
    if not grant.approved_by:
        raise ValueError("opencode permission grant requires approved_by")
    if not grant.approved_at:
        raise ValueError("opencode permission grant requires approved_at")
    if not grant.allow_process_spawn:
        raise ValueError(
            "opencode permission grant must set allow_process_spawn=True before "
            "an OpenCodeCliClient can be registered"
        )
    return grant
