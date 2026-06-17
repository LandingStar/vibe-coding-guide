"""One-shot runner for persisted scheduler state."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .preflight import PreflightDrainResult, drain_preflighted_ready_tasks
from .runtime_adapter import AgentRuntimeAdapterRegistry
from .runtime_wiring import RuntimeRegistryWiringResult
from .sandbox import SandboxProviderRegistry
from .scheduler import SchedulerRunPolicy
from .scheduler_store import (
    JsonlSchedulerEventLog,
    SchedulerRecoveryResult,
    recover_scheduler_state,
    write_scheduler_state_snapshot,
)


@dataclass(frozen=True, slots=True)
class PersistedSchedulerRunOnceResult:
    """Result of one bounded run over persisted scheduler state."""

    recovery: SchedulerRecoveryResult
    drain: PreflightDrainResult
    snapshot_path: Path
    event_log_path: Path
    state_written: bool = False
    runtime_registry_providers: tuple[str, ...] = ()
    runtime_host_surface: str = ""


def run_persisted_scheduler_once(
    *,
    snapshot_path: str | Path,
    event_log_path: str | Path,
    sandbox_registry: SandboxProviderRegistry,
    runtime_registry: AgentRuntimeAdapterRegistry,
    policy: SchedulerRunPolicy | None = None,
    max_runs: int | None = None,
    workspace_root: str = "",
    scratch_root: str = ".codex/scratch",
    created_at: str = "",
    expires_at: str = "",
    timestamp: str = "",
    strict_recovery: bool = True,
) -> PersistedSchedulerRunOnceResult:
    """Recover, drain ready tasks once, and persist the resulting state.

    This is a command-style helper for local orchestration tests and host
    adapters. It is deliberately bounded and does not start a daemon.
    """

    recovery = recover_scheduler_state(
        snapshot_path,
        event_log_path,
        strict=strict_recovery,
    )
    event_log = JsonlSchedulerEventLog(event_log_path)
    drain = drain_preflighted_ready_tasks(
        recovery.recovered_state,
        sandbox_registry=sandbox_registry,
        runtime_registry=runtime_registry,
        policy=policy,
        max_runs=max_runs,
        workspace_root=workspace_root,
        scratch_root=scratch_root,
        created_at=created_at,
        expires_at=expires_at,
        event_log=event_log,
        timestamp=timestamp,
    )
    written = write_scheduler_state_snapshot(drain.state, snapshot_path)
    return PersistedSchedulerRunOnceResult(
        recovery=recovery,
        drain=drain,
        snapshot_path=written,
        event_log_path=Path(event_log_path),
        state_written=True,
        runtime_registry_providers=runtime_registry.providers(),
    )


def run_persisted_scheduler_once_with_wiring(
    *,
    snapshot_path: str | Path,
    event_log_path: str | Path,
    sandbox_registry: SandboxProviderRegistry,
    runtime_wiring: RuntimeRegistryWiringResult,
    policy: SchedulerRunPolicy | None = None,
    max_runs: int | None = None,
    workspace_root: str = "",
    scratch_root: str = ".codex/scratch",
    created_at: str = "",
    expires_at: str = "",
    timestamp: str = "",
    strict_recovery: bool = True,
) -> PersistedSchedulerRunOnceResult:
    """Run persisted scheduler state through a host-wired runtime registry."""

    _validate_host_wired_runtime_run(runtime_wiring)
    result = run_persisted_scheduler_once(
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        sandbox_registry=sandbox_registry,
        runtime_registry=runtime_wiring.registry,
        policy=policy,
        max_runs=max_runs,
        workspace_root=workspace_root,
        scratch_root=scratch_root,
        created_at=created_at,
        expires_at=expires_at,
        timestamp=timestamp,
        strict_recovery=strict_recovery,
    )
    invocation = runtime_wiring.config.host_invocation
    return PersistedSchedulerRunOnceResult(
        recovery=result.recovery,
        drain=result.drain,
        snapshot_path=result.snapshot_path,
        event_log_path=result.event_log_path,
        state_written=result.state_written,
        runtime_registry_providers=runtime_wiring.registered_providers,
        runtime_host_surface="" if invocation is None else invocation.surface,
    )


def _validate_host_wired_runtime_run(runtime_wiring: RuntimeRegistryWiringResult) -> None:
    providers = runtime_wiring.registered_providers
    if providers == ("fake",):
        return
    invocation = runtime_wiring.config.host_invocation
    if invocation is None:
        raise ValueError(
            "host-wired scheduler run with non-fake runtime providers requires RuntimeHostInvocation"
        )
    if invocation.surface != "host-authorized-adapter":
        raise ValueError(
            "host-wired scheduler run with non-fake runtime providers requires "
            "RuntimeHostInvocation(surface='host-authorized-adapter')"
        )
