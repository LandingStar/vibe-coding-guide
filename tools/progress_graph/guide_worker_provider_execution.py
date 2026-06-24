"""Host-owned guide-worker provider execution wrapper.

This helper composes the scheduler-owned guide-worker local orchestration with
host-authorized runtime wiring. It is intentionally outside MCP: MCP remains
fake-only while hosts can inject provider clients and write compact evidence.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.runtime.orchestration import (
    GuideWorkerInstruction,
    GuideWorkerLocalOrchestrationRequest,
    GuideWorkerLocalOrchestrationResult,
    InMemoryArtifactVersionStore,
    JsonArtifactVersionStore,
    QoderQueryClient,
    QoderSDKQueryClient,
    QoderSDKQueryClientConfig,
    RuntimeHostInvocation,
    RuntimeProviderKind,
    RuntimeProviderPermissionGrant,
    RuntimeRegistryWiringConfig,
    build_runtime_registry_from_config,
    default_exchange_artifact_admission_ledger_path,
    default_exchange_artifact_store_path,
    run_guide_worker_local_trajectory_orchestration,
)

GUIDE_WORKER_PROVIDER_EXECUTION_EVIDENCE_PRODUCT_TYPE = (
    "host_guide_worker_provider_execution_evidence"
)
GUIDE_WORKER_PROVIDER_EXECUTION_EVIDENCE_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class HostOwnedGuideWorkerProviderExecutionConfig:
    """Host-owned configuration for one guide-worker provider run."""

    evidence_id: str = "guide-worker-provider-execution"
    timestamp: str = ""
    artifact_store_path: str | Path = ".codex/orchestration/exchange-artifacts.json"
    admission_ledger_path: str | Path = ".codex/orchestration/exchange-artifact-admissions.json"
    snapshot_path: str | Path = ".codex/scheduler/guide-worker-provider-execution-state.json"
    event_log_path: str | Path = ".codex/scheduler/guide-worker-provider-execution-events.jsonl"
    evidence_output_path: str | Path | None = None
    trajectory_id: str = "local-work:current"
    guide_agent_id: str = "agent:guide"
    worker_agent_id: str = "agent:qoder-worker"
    artifact_id_prefix: str = "guide-worker-provider-execution"
    worker_instructions: tuple[GuideWorkerInstruction, ...] = field(
        default_factory=lambda: (
            GuideWorkerInstruction(
                task_id="task/guide-worker-provider/client",
                title="Qoder client worker",
                instruction=(
                    "Act as the client-lane worker. Complete the bounded "
                    "guide-assigned client task and return compact result evidence."
                ),
                lane_id="lane:client",
                worker_agent_id="agent:qoder-client-worker",
                worker_runtime_provider="qoder",
                acceptance=(
                    "Return a compact result summary.",
                    "Do not include secrets or raw credential material.",
                ),
                output_artifact_id="task/guide-worker-provider/client:result",
            ),
            GuideWorkerInstruction(
                task_id="task/guide-worker-provider/server",
                title="Qoder server worker",
                instruction=(
                    "Act as the server-lane worker. Complete the bounded "
                    "guide-assigned server task and return compact result evidence."
                ),
                lane_id="lane:server",
                worker_agent_id="agent:qoder-server-worker",
                worker_runtime_provider="qoder",
                acceptance=(
                    "Return a compact result summary.",
                    "Do not include secrets or raw credential material.",
                ),
                output_artifact_id="task/guide-worker-provider/server:result",
            ),
        )
    )
    providers: tuple[RuntimeProviderKind, ...] = ("qoder",)
    qoder_client_config: QoderSDKQueryClientConfig = field(default_factory=QoderSDKQueryClientConfig)
    host_invocation_id: str = "host-owned-guide-worker-provider-execution"
    requested_by: str = "host:guide-worker-provider-execution"
    reason: str = "host-owned guide-worker provider execution"
    grant_id: str = "grant-host-owned-guide-worker-provider-execution"
    approved_by: str = "host:guide-worker-provider-execution"
    approved_at: str = ""
    grant_scope: str = "guide-worker-provider-execution"
    allow_network: bool = True
    max_parallel_lanes: int = 2
    max_waves: int = 1
    wave_execution_mode: str = "threaded"
    replace_existing: bool = True
    allow_duplicate_admission: bool = True
    workspace_root: str = ""
    scratch_root: str = ".codex/scratch"
    evidence_metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HostOwnedGuideWorkerProviderExecutionEvidence:
    """Compact evidence for one host-owned guide-worker provider execution."""

    evidence_id: str
    timestamp: str
    result: GuideWorkerLocalOrchestrationResult
    registered_providers: tuple[RuntimeProviderKind, ...]
    host_invocation: RuntimeHostInvocation
    evidence_path: str | Path | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)
    product_type: str = GUIDE_WORKER_PROVIDER_EXECUTION_EVIDENCE_PRODUCT_TYPE
    schema_version: str = GUIDE_WORKER_PROVIDER_EXECUTION_EVIDENCE_SCHEMA_VERSION

    def to_json_dict(self) -> dict[str, object]:
        result_payload = self.result.to_json_dict()
        authority_split = dict(result_payload["authority_split"])
        authority_split.update(
            {
                "workflow_surface": "host-owned-guide-worker-provider-execution",
                "runtime_registry_authority": "host_runtime_wiring",
                "mcp_live_provider_surface": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_persisted": False,
            }
        )
        return {
            "product_type": self.product_type,
            "schema_version": self.schema_version,
            "evidence_id": self.evidence_id,
            "timestamp": self.timestamp,
            "workflow_surface": "host-owned-guide-worker-provider-execution",
            "runtime_providers": list(self.registered_providers),
            "worker_runtime_providers": result_payload["scenario"][
                "worker_runtime_providers"
            ],
            "host_invocation": {
                "surface": self.host_invocation.surface,
                "invocation_id": self.host_invocation.invocation_id,
                "requested_by": self.host_invocation.requested_by,
                "reason": self.host_invocation.reason,
            },
            "paths": result_payload["paths"],
            "artifacts": result_payload["artifacts"],
            "submitted_task_ids": result_payload["submitted_task_ids"],
            "lane_ids": result_payload["lane_ids"],
            "parallel_waves": result_payload["parallel_waves"],
            "wave_execution_results": result_payload["wave_execution_results"],
            "run_task_ids": result_payload["run_task_ids"],
            "task_states": result_payload["task_states"],
            "output_artifact_refs": _output_artifact_refs(self.result),
            "authority_split": authority_split,
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_json_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ) + "\n"


@dataclass(frozen=True, slots=True)
class HostOwnedGuideWorkerProviderExecutionResult:
    """Result of a host-owned guide-worker provider execution run."""

    orchestration: GuideWorkerLocalOrchestrationResult
    evidence: HostOwnedGuideWorkerProviderExecutionEvidence
    evidence_path: Path | None = None

    def to_json_dict(self) -> dict[str, object]:
        payload = self.evidence.to_json_dict()
        payload["ok"] = self.orchestration.ok
        payload["evidence_path"] = "" if self.evidence_path is None else str(self.evidence_path)
        payload["orchestration"] = self.orchestration.to_json_dict()
        return payload


def default_guide_worker_provider_execution_evidence_path(
    project_root: str | Path,
    evidence_id: str,
) -> Path:
    """Return default compact evidence path for guide-worker provider execution."""

    safe_id = "".join(
        character if character.isalnum() or character in {"-", "_"} else "-"
        for character in evidence_id
    )
    safe_id = safe_id.strip("-") or "guide-worker-provider-execution"
    return Path(project_root) / ".codex/scheduler/evidence" / f"{safe_id}.json"


def run_host_owned_guide_worker_provider_execution(
    project_root: str | Path,
    *,
    config: HostOwnedGuideWorkerProviderExecutionConfig | None = None,
    qoder_query_client: QoderQueryClient | None = None,
    sdk_importer: Callable[[str], Any] | None = None,
    environment: Mapping[str, str] | None = None,
    artifact_store: InMemoryArtifactVersionStore | None = None,
) -> HostOwnedGuideWorkerProviderExecutionResult:
    """Run guide-worker provider execution through host-owned runtime wiring."""

    active_config = config or HostOwnedGuideWorkerProviderExecutionConfig()
    providers = _normalize_providers(active_config.providers)
    _validate_requested_worker_providers(active_config, providers)
    client = qoder_query_client
    if "qoder" in providers and client is None:
        client = QoderSDKQueryClient(
            active_config.qoder_client_config,
            sdk_importer=sdk_importer,
            environment=environment if environment is not None else os.environ,
        )
    _validate_real_runtime_client_ready(providers, client)

    host_invocation = _host_invocation(active_config, providers)
    runtime_config = _runtime_config(active_config, providers, host_invocation)
    store = artifact_store or InMemoryArtifactVersionStore()
    _seed_in_memory_store_from_json(
        store,
        _project_path(project_root, active_config.artifact_store_path),
    )
    wiring = build_runtime_registry_from_config(
        runtime_config,
        artifact_store=store,
        qoder_query_client=client,
    )
    request = GuideWorkerLocalOrchestrationRequest(
        artifact_store_path=_project_path(project_root, active_config.artifact_store_path),
        admission_ledger_path=_project_path(project_root, active_config.admission_ledger_path),
        snapshot_path=_project_path(project_root, active_config.snapshot_path),
        event_log_path=_project_path(project_root, active_config.event_log_path),
        trajectory_id=active_config.trajectory_id,
        guide_agent_id=active_config.guide_agent_id,
        worker_agent_id=active_config.worker_agent_id,
        artifact_id_prefix=active_config.artifact_id_prefix,
        timestamp=active_config.timestamp,
        worker_instructions=active_config.worker_instructions,
        max_parallel_lanes=active_config.max_parallel_lanes,
        max_waves=active_config.max_waves,
        replace_existing=active_config.replace_existing,
        allow_duplicate_admission=active_config.allow_duplicate_admission,
        workspace_root=active_config.workspace_root or str(project_root),
        scratch_root=active_config.scratch_root,
        wave_execution_mode=_normalize_wave_execution_mode(
            active_config.wave_execution_mode
        ),
    )
    orchestration = run_guide_worker_local_trajectory_orchestration(
        request,
        runtime_registry=wiring.registry,
        artifact_store=store,
    )
    evidence = HostOwnedGuideWorkerProviderExecutionEvidence(
        evidence_id=active_config.evidence_id,
        timestamp=active_config.timestamp,
        result=orchestration,
        registered_providers=wiring.registered_providers,
        host_invocation=host_invocation,
        metadata=_evidence_metadata(active_config),
    )
    evidence_path = (
        None
        if active_config.evidence_output_path is None
        else _project_path(project_root, active_config.evidence_output_path)
    )
    if evidence_path is None and active_config.evidence_id:
        evidence_path = default_guide_worker_provider_execution_evidence_path(
            project_root,
            active_config.evidence_id,
        )
    if evidence_path is not None:
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(evidence.to_json(), encoding="utf-8")
        evidence = HostOwnedGuideWorkerProviderExecutionEvidence(
            evidence_id=evidence.evidence_id,
            timestamp=evidence.timestamp,
            result=evidence.result,
            registered_providers=evidence.registered_providers,
            host_invocation=evidence.host_invocation,
            evidence_path=evidence_path,
            metadata=evidence.metadata,
        )
    return HostOwnedGuideWorkerProviderExecutionResult(
        orchestration=orchestration,
        evidence=evidence,
        evidence_path=evidence_path,
    )


def default_guide_worker_provider_execution_config(
    project_root: str | Path,
    *,
    evidence_id: str = "guide-worker-provider-execution",
    timestamp: str = "",
) -> HostOwnedGuideWorkerProviderExecutionConfig:
    """Build the default config with project-local exchange store paths."""

    return HostOwnedGuideWorkerProviderExecutionConfig(
        evidence_id=evidence_id,
        timestamp=timestamp,
        artifact_store_path=default_exchange_artifact_store_path(project_root),
        admission_ledger_path=default_exchange_artifact_admission_ledger_path(project_root),
    )


def _runtime_config(
    config: HostOwnedGuideWorkerProviderExecutionConfig,
    providers: tuple[RuntimeProviderKind, ...],
    host_invocation: RuntimeHostInvocation,
) -> RuntimeRegistryWiringConfig:
    approved_at = config.approved_at or config.timestamp
    grant = None
    if "qoder" in providers:
        grant = RuntimeProviderPermissionGrant(
            grant_id=config.grant_id,
            provider="qoder",
            approved_by=config.approved_by,
            approved_at=approved_at,
            scope=config.grant_scope,
            allow_sdk_client=True,
            allow_network=config.allow_network,
        )
    return RuntimeRegistryWiringConfig(
        providers=providers,
        timestamp=config.timestamp,
        host_invocation=host_invocation,
        qoder_permission_grant=grant,
    )


def _host_invocation(
    config: HostOwnedGuideWorkerProviderExecutionConfig,
    providers: tuple[RuntimeProviderKind, ...],
) -> RuntimeHostInvocation:
    return RuntimeHostInvocation(
        surface="host-authorized-adapter",
        invocation_id=config.host_invocation_id,
        requested_providers=providers,
        requested_by=config.requested_by,
        reason=config.reason,
    )


def _normalize_providers(
    providers: tuple[RuntimeProviderKind, ...],
) -> tuple[RuntimeProviderKind, ...]:
    normalized: list[RuntimeProviderKind] = []
    for provider in providers:
        if provider not in {"fake", "qoder"}:
            raise ValueError(f"unsupported guide-worker provider: {provider!r}")
        if provider not in normalized:
            normalized.append(provider)
    if not normalized:
        raise ValueError("guide-worker provider execution requires at least one provider")
    return tuple(normalized)


def _normalize_wave_execution_mode(value: str) -> str:
    mode = (value or "serial").strip().lower()
    if mode not in {"serial", "threaded"}:
        raise ValueError(
            "guide-worker provider execution wave_execution_mode must be "
            "'serial' or 'threaded'"
        )
    return mode


def _validate_requested_worker_providers(
    config: HostOwnedGuideWorkerProviderExecutionConfig,
    providers: tuple[RuntimeProviderKind, ...],
) -> None:
    available = set(providers)
    for index, instruction in enumerate(config.worker_instructions):
        provider = instruction.worker_runtime_provider or "fake"
        if provider not in available:
            raise ValueError(
                "guide-worker provider execution worker instruction "
                f"{index} requests provider {provider!r}, but configured providers are "
                f"{', '.join(providers)}"
            )


def _validate_real_runtime_client_ready(
    providers: tuple[RuntimeProviderKind, ...],
    qoder_query_client: QoderQueryClient | None,
) -> None:
    if "qoder" not in providers or qoder_query_client is None:
        return
    validator = getattr(qoder_query_client, "validate_host_ready", None)
    if callable(validator):
        validator()


def _seed_in_memory_store_from_json(
    store: InMemoryArtifactVersionStore,
    path: Path,
) -> None:
    if not path.exists():
        return
    for record in JsonArtifactVersionStore(path).list_records():
        try:
            store.put(record.artifact)
        except ValueError as exc:
            if "already exists" not in str(exc):
                raise


def _output_artifact_refs(
    result: GuideWorkerLocalOrchestrationResult,
) -> list[dict[str, object]]:
    return [
        {
            "task_id": record.task_id,
            "run_id": record.run_id,
            "artifact_id": record.output_artifact_id,
            "version": record.output_artifact_version,
            "state": record.state,
        }
        for record in result.final_state.run_records
    ]


def _evidence_metadata(
    config: HostOwnedGuideWorkerProviderExecutionConfig,
) -> dict[str, object]:
    metadata = {
        "runner": "host-owned-guide-worker-provider-execution",
        "sdk_module_name": config.qoder_client_config.sdk_module_name,
        "permission_request_policy": config.qoder_client_config.permission_request_policy,
    }
    metadata.update(dict(config.evidence_metadata))
    return metadata


def _project_path(project_root: str | Path, path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(project_root) / candidate
