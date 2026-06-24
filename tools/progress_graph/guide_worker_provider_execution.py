"""Host-owned guide-worker provider execution wrapper.

This helper composes the scheduler-owned guide-worker local orchestration with
host-authorized runtime wiring. It is intentionally outside MCP: MCP remains
fake-only while hosts can inject provider clients and write compact evidence.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

from src.runtime.orchestration import (
    CodexCliClient,
    CodexCliClientConfig,
    CodexCliProcessClient,
    GuideWorkerInstruction,
    GuideWorkerLocalOrchestrationRequest,
    GuideWorkerLocalOrchestrationResult,
    GuideWorkerPlanningRequest,
    InMemoryArtifactVersionStore,
    JsonArtifactVersionStore,
    QoderQueryClient,
    QoderSDKQueryClient,
    QoderSDKQueryClientConfig,
    RuntimeHostInvocation,
    RuntimeProviderKind,
    RuntimeProviderPermissionGrant,
    RuntimeRegistryWiringConfig,
    SandboxAllocation,
    SandboxProviderRegistry,
    SharedProcessSandboxProvider,
    GitWorktreeSandboxProvider,
    WorkerPatchReviewArtifact,
    build_sandbox_allocation_receipt_evidence,
    default_sandbox_allocation_receipt_evidence_path,
    build_worker_patch_review_artifacts,
    build_runtime_registry_from_config,
    default_exchange_artifact_admission_ledger_path,
    default_exchange_artifact_store_path,
    resolve_guide_worker_instructions,
    run_guide_worker_local_trajectory_orchestration,
    write_sandbox_allocation_receipt_evidence,
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
    worker_instructions: tuple[GuideWorkerInstruction, ...] = ()
    planning_request: GuideWorkerPlanningRequest = field(
        default_factory=GuideWorkerPlanningRequest
    )
    planner_worker_runtime_provider: str = ""
    providers: tuple[RuntimeProviderKind, ...] = ("qoder",)
    qoder_client_config: QoderSDKQueryClientConfig = field(default_factory=QoderSDKQueryClientConfig)
    codex_cli_client_config: CodexCliClientConfig = field(default_factory=CodexCliClientConfig)
    host_invocation_id: str = "host-owned-guide-worker-provider-execution"
    requested_by: str = "host:guide-worker-provider-execution"
    reason: str = "host-owned guide-worker provider execution"
    grant_id: str = "grant-host-owned-guide-worker-provider-execution"
    approved_by: str = "host:guide-worker-provider-execution"
    approved_at: str = ""
    grant_scope: str = "guide-worker-provider-execution"
    allow_network: bool = True
    allow_process_spawn: bool = True
    max_parallel_lanes: int = 2
    max_waves: int = 1
    wave_execution_mode: str = "threaded"
    replace_existing: bool = True
    allow_duplicate_admission: bool = True
    workspace_root: str = ""
    scratch_root: str = ".codex/scratch"
    git_worktree_sandbox_root: str | Path | None = None
    sandbox_allocation_evidence_id: str = ""
    sandbox_allocation_evidence_path: str | Path | None = None
    git_executable: str = "git"
    evidence_metadata: Mapping[str, object] = field(default_factory=dict)
    publish_worker_patch_artifacts: bool = True
    worker_patch_target_task_id: str = ""


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
    worker_patch_artifacts: tuple[WorkerPatchReviewArtifact, ...] = ()
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
                "sandbox_allocation_evidence_written": bool(
                    self.metadata.get("sandbox_allocation_evidence_path")
                ),
                "auto_merge_performed": False,
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
            "planning": result_payload["planning"],
            "planned_worker_instructions": result_payload["planned_worker_instructions"],
            "wave_execution_results": result_payload["wave_execution_results"],
            "run_task_ids": result_payload["run_task_ids"],
            "task_states": result_payload["task_states"],
            "output_artifact_refs": _output_artifact_refs(self.result),
            "worker_execution_receipts": _worker_execution_receipts(self.result),
            "worker_writeback_receipts": _worker_writeback_receipts(
                self.result,
                self.worker_patch_artifacts,
            ),
            "worker_patch_artifact_refs": [
                artifact.to_receipt_ref()
                for artifact in self.worker_patch_artifacts
            ],
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
    codex_cli_client: CodexCliClient | None = None,
    sdk_importer: Callable[[str], Any] | None = None,
    environment: Mapping[str, str] | None = None,
    artifact_store: InMemoryArtifactVersionStore | None = None,
) -> HostOwnedGuideWorkerProviderExecutionResult:
    """Run guide-worker provider execution through host-owned runtime wiring."""

    active_config = config or HostOwnedGuideWorkerProviderExecutionConfig()
    providers = _normalize_providers(active_config.providers)
    _validate_requested_worker_providers(active_config, providers)
    qoder_client = qoder_query_client
    if "qoder" in providers and qoder_client is None:
        qoder_client = QoderSDKQueryClient(
            active_config.qoder_client_config,
            sdk_importer=sdk_importer,
            environment=environment if environment is not None else os.environ,
        )
    codex_client = codex_cli_client
    if "codex" in providers and codex_client is None:
        codex_client = CodexCliProcessClient(active_config.codex_cli_client_config)
    _validate_real_runtime_client_ready(providers, qoder_client, codex_client)

    host_invocation = _host_invocation(active_config, providers)
    runtime_config = _runtime_config(active_config, providers, host_invocation)
    planning_request = _effective_planning_request(active_config, providers)
    worker_instructions = _effective_worker_instructions(active_config)
    store = artifact_store or InMemoryArtifactVersionStore()
    _seed_in_memory_store_from_json(
        store,
        _project_path(project_root, active_config.artifact_store_path),
    )
    wiring = build_runtime_registry_from_config(
        runtime_config,
        artifact_store=store,
        qoder_query_client=qoder_client,
        codex_cli_client=codex_client,
    )
    sandbox_registry = _sandbox_registry(project_root, active_config)
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
        planning_request=planning_request,
        worker_instructions=worker_instructions,
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
        sandbox_registry=sandbox_registry,
        artifact_store=store,
    )
    sandbox_write = _write_sandbox_allocation_evidence(
        project_root,
        active_config,
        orchestration,
    )
    worker_patch_artifacts = _publish_worker_patch_artifacts(
        project_root,
        active_config,
        orchestration,
    )
    evidence = HostOwnedGuideWorkerProviderExecutionEvidence(
        evidence_id=active_config.evidence_id,
        timestamp=active_config.timestamp,
        result=orchestration,
        registered_providers=wiring.registered_providers,
        host_invocation=host_invocation,
        metadata=_evidence_metadata(active_config, sandbox_write_path=sandbox_write),
        worker_patch_artifacts=worker_patch_artifacts,
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
            worker_patch_artifacts=evidence.worker_patch_artifacts,
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
    qoder_grant = None
    if "qoder" in providers:
        qoder_grant = RuntimeProviderPermissionGrant(
            grant_id=config.grant_id,
            provider="qoder",
            approved_by=config.approved_by,
            approved_at=approved_at,
            scope=config.grant_scope,
            allow_sdk_client=True,
            allow_network=config.allow_network,
        )
    codex_grant = None
    if "codex" in providers:
        codex_grant = RuntimeProviderPermissionGrant(
            grant_id=config.grant_id,
            provider="codex",
            approved_by=config.approved_by,
            approved_at=approved_at,
            scope=config.grant_scope,
            allow_process_spawn=config.allow_process_spawn,
            allow_network=config.allow_network,
        )
    return RuntimeRegistryWiringConfig(
        providers=providers,
        timestamp=config.timestamp,
        host_invocation=host_invocation,
        qoder_permission_grant=qoder_grant,
        codex_permission_grant=codex_grant,
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
        if provider not in {"fake", "qoder", "codex"}:
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
    instructions, _ = resolve_guide_worker_instructions(
        _provider_validation_request(config)
    )
    for index, instruction in enumerate(instructions):
        provider = instruction.worker_runtime_provider or "fake"
        if provider not in available:
            raise ValueError(
                "guide-worker provider execution worker instruction "
                f"{index} requests provider {provider!r}, but configured providers are "
                f"{', '.join(providers)}"
            )


def _provider_validation_request(
    config: HostOwnedGuideWorkerProviderExecutionConfig,
) -> GuideWorkerLocalOrchestrationRequest:
    providers = _normalize_providers(config.providers)
    return GuideWorkerLocalOrchestrationRequest(
        artifact_store_path=Path(config.artifact_store_path),
        admission_ledger_path=Path(config.admission_ledger_path),
        snapshot_path=Path(config.snapshot_path),
        event_log_path=Path(config.event_log_path),
        trajectory_id=config.trajectory_id,
        guide_agent_id=config.guide_agent_id,
        worker_agent_id=config.worker_agent_id,
        artifact_id_prefix=config.artifact_id_prefix,
        timestamp=config.timestamp,
        planning_request=_effective_planning_request(config, providers),
        worker_instructions=_effective_worker_instructions(config),
        workspace_root=config.workspace_root,
        scratch_root=config.scratch_root,
    )


def _effective_planning_request(
    config: HostOwnedGuideWorkerProviderExecutionConfig,
    providers: tuple[RuntimeProviderKind, ...],
) -> GuideWorkerPlanningRequest:
    planning = config.planning_request
    if not planning.lane_specs:
        return planning
    default_provider = config.planner_worker_runtime_provider.strip()
    if not default_provider and len(providers) == 1:
        default_provider = providers[0]
    if not default_provider:
        return planning
    return replace(
        planning,
        lane_specs=tuple(
            replace(
                spec,
                worker_agent_id=spec.worker_agent_id or config.worker_agent_id,
                worker_runtime_provider=spec.worker_runtime_provider or default_provider,
            )
            for spec in planning.lane_specs
        ),
    )


def _effective_worker_instructions(
    config: HostOwnedGuideWorkerProviderExecutionConfig,
) -> tuple[GuideWorkerInstruction, ...]:
    if config.worker_instructions:
        return config.worker_instructions
    if config.planning_request.lane_specs:
        return ()
    default_provider = config.providers[0] if len(config.providers) == 1 else "qoder"
    return _default_worker_instructions(default_provider)


def _default_worker_instructions(
    provider: RuntimeProviderKind = "qoder",
) -> tuple[GuideWorkerInstruction, ...]:
    label = "Codex CLI" if provider == "codex" else "Qoder"
    provider_slug = "codex" if provider == "codex" else "qoder"
    return (
        GuideWorkerInstruction(
            task_id="task/guide-worker-provider/client",
            title=f"{label} client worker",
            instruction=(
                "Act as the client-lane worker. Complete the bounded "
                "guide-assigned client task and return compact result evidence."
            ),
            lane_id="lane:client",
            worker_agent_id=f"agent:{provider_slug}-client-worker",
            worker_runtime_provider=provider,
            acceptance=(
                "Return a compact result summary.",
                "Do not include secrets or raw credential material.",
            ),
            output_artifact_id="task/guide-worker-provider/client:result",
        ),
        GuideWorkerInstruction(
            task_id="task/guide-worker-provider/server",
            title=f"{label} server worker",
            instruction=(
                "Act as the server-lane worker. Complete the bounded "
                "guide-assigned server task and return compact result evidence."
            ),
            lane_id="lane:server",
            worker_agent_id=f"agent:{provider_slug}-server-worker",
            worker_runtime_provider=provider,
            acceptance=(
                "Return a compact result summary.",
                "Do not include secrets or raw credential material.",
            ),
            output_artifact_id="task/guide-worker-provider/server:result",
        ),
    )


def _validate_real_runtime_client_ready(
    providers: tuple[RuntimeProviderKind, ...],
    qoder_query_client: QoderQueryClient | None,
    codex_cli_client: CodexCliClient | None,
) -> None:
    if "qoder" in providers and qoder_query_client is not None:
        validator = getattr(qoder_query_client, "validate_host_ready", None)
        if callable(validator):
            validator()
    if "codex" in providers and codex_cli_client is not None:
        validator = getattr(codex_cli_client, "validate_host_ready", None)
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


def _worker_execution_receipts(
    result: GuideWorkerLocalOrchestrationResult,
) -> list[dict[str, object]]:
    run_records_by_task_id = {
        record.task_id: record
        for record in result.final_state.run_records
    }
    receipts: list[dict[str, object]] = []
    for instruction in result.planned_worker_instructions:
        task = result.final_state.tasks.get(instruction.task_id)
        record = run_records_by_task_id.get(instruction.task_id)
        output_ref = task.output_artifact_ref if task is not None else None
        receipts.append(
            {
                "task_id": instruction.task_id,
                "lane_id": instruction.lane_id,
                "title": instruction.title,
                "worker_agent_id": (
                    instruction.worker_agent_id or result.request.worker_agent_id
                ),
                "runtime_provider": instruction.worker_runtime_provider or "fake",
                "task_state": "" if task is None else task.state,
                "run_id": "" if record is None else record.run_id,
                "session_id": "" if record is None else record.session_id,
                "output_artifact_id": (
                    instruction.output_artifact_id
                    or f"{instruction.task_id}:result"
                ),
                "output_artifact_ref": (
                    {}
                    if output_ref is None
                    else {
                        "ref_kind": output_ref.ref_kind,
                        "ref_id": output_ref.ref_id,
                        "version": output_ref.version,
                    }
                ),
                "acceptance": list(instruction.acceptance),
            }
        )
    return receipts


def _worker_writeback_receipts(
    result: GuideWorkerLocalOrchestrationResult,
    patch_artifacts: tuple[WorkerPatchReviewArtifact, ...] = (),
) -> list[dict[str, object]]:
    """Return review-only writeback receipts for worker runtime outputs."""

    instruction_by_task_id = {
        instruction.task_id: instruction
        for instruction in result.planned_worker_instructions
    }
    patch_ref_by_task_id = {
        str(
            _first_structured_value(
                artifact.artifact,
                "task_id",
            )
        ): artifact.to_receipt_ref()
        for artifact in patch_artifacts
    }
    receipts: list[dict[str, object]] = []
    for run in result.run_results:
        task_id = run.preflight.task.task_id
        instruction = instruction_by_task_id.get(task_id)
        allocation = run.preflight.sandbox_allocation
        delta = run.runtime_result.artifact_delta
        output_ref = run.runtime_result.output_artifact
        receipts.append(
            {
                "task_id": task_id,
                "lane_id": run.preflight.task.context_scope.lane_id,
                "worker_agent_id": run.preflight.task.agent.agent_id,
                "runtime_provider": run.preflight.task.agent.runtime_provider,
                "sandbox_provider": allocation.provider,
                "sandbox_allocation_id": allocation.allocation_id,
                "sandbox_state": allocation.state,
                "sandbox_workspace_root": allocation.workspace_root,
                "sandbox_scratch_path": allocation.scratch_path,
                "cleanup_required": allocation.cleanup_required,
                "output_artifact_ref": {
                    "ref_kind": "exchange_artifact",
                    "ref_id": output_ref.artifact_id,
                    "version": output_ref.version,
                },
                "artifact_delta": {
                    "artifact_id": delta.artifact_id,
                    "version": delta.version,
                    "summary": delta.summary,
                    "changed_refs": [
                        {
                            "ref_kind": ref.ref_kind,
                            "ref_id": ref.ref_id,
                            "version": ref.version,
                            "path": ref.path,
                            "label": ref.label,
                        }
                        for ref in delta.changed_refs
                    ],
                },
                "allowed_artifacts": (
                    [] if instruction is None else list(instruction.allowed_artifacts)
                ),
                "merge_review_state": "review_required",
                "auto_merge_performed": False,
                "patch_artifact_ref": patch_ref_by_task_id.get(task_id, {}),
            }
        )
    return receipts


def _first_structured_value(
    artifact: object,
    key: str,
) -> object:
    for part in getattr(artifact, "parts", ()):
        if getattr(part, "part_type", "") == "structured":
            data = getattr(part, "data", {})
            if key in data:
                return data[key]
    return ""


def _publish_worker_patch_artifacts(
    project_root: str | Path,
    config: HostOwnedGuideWorkerProviderExecutionConfig,
    result: GuideWorkerLocalOrchestrationResult,
) -> tuple[WorkerPatchReviewArtifact, ...]:
    if not config.publish_worker_patch_artifacts:
        return ()
    patch_artifacts = build_worker_patch_review_artifacts(
        result.run_results,
        timestamp=config.timestamp,
        guide_agent_id=config.guide_agent_id,
        target_task_id=config.worker_patch_target_task_id,
        git_executable=config.git_executable,
    )
    if not patch_artifacts:
        return ()
    store = JsonArtifactVersionStore(
        _project_path(project_root, config.artifact_store_path)
    )
    for patch_artifact in patch_artifacts:
        store.put(
            patch_artifact.artifact,
            replace_existing=config.replace_existing,
        )
    return patch_artifacts


def _sandbox_allocations(
    result: GuideWorkerLocalOrchestrationResult,
) -> tuple[SandboxAllocation, ...]:
    return tuple(run.preflight.sandbox_allocation for run in result.run_results)


def _sandbox_registry(
    project_root: str | Path,
    config: HostOwnedGuideWorkerProviderExecutionConfig,
) -> SandboxProviderRegistry:
    registry = SandboxProviderRegistry()
    registry.register(SharedProcessSandboxProvider())
    if config.git_worktree_sandbox_root is not None:
        registry.register(
            GitWorktreeSandboxProvider(
                _project_path(project_root, config.git_worktree_sandbox_root),
                git_executable=config.git_executable,
            )
        )
    return registry


def _write_sandbox_allocation_evidence(
    project_root: str | Path,
    config: HostOwnedGuideWorkerProviderExecutionConfig,
    result: GuideWorkerLocalOrchestrationResult,
) -> Path | None:
    allocations = _sandbox_allocations(result)
    if not allocations or not config.sandbox_allocation_evidence_id:
        return None
    target = (
        _project_path(project_root, config.sandbox_allocation_evidence_path)
        if config.sandbox_allocation_evidence_path is not None
        else default_sandbox_allocation_receipt_evidence_path(
            project_root,
            config.sandbox_allocation_evidence_id,
        )
    )
    write = write_sandbox_allocation_receipt_evidence(
        build_sandbox_allocation_receipt_evidence(
            allocations,
            evidence_id=config.sandbox_allocation_evidence_id,
            timestamp=config.timestamp,
            evidence_path=target,
            metadata={
                "surface": "host-owned-guide-worker-provider-execution",
                "host_invocation_id": config.host_invocation_id,
                "git_worktree_sandbox_opt_in": config.git_worktree_sandbox_root is not None,
                "git_worktree_sandbox_root": (
                    ""
                    if config.git_worktree_sandbox_root is None
                    else str(config.git_worktree_sandbox_root)
                ),
            },
        ),
        target,
    )
    return write.evidence_path


def _evidence_metadata(
    config: HostOwnedGuideWorkerProviderExecutionConfig,
    *,
    sandbox_write_path: Path | None = None,
) -> dict[str, object]:
    metadata = {
        "runner": "host-owned-guide-worker-provider-execution",
        "sdk_module_name": config.qoder_client_config.sdk_module_name,
        "permission_request_policy": config.qoder_client_config.permission_request_policy,
        "codex_cli_executable": config.codex_cli_client_config.executable,
        "codex_cli_sandbox": config.codex_cli_client_config.sandbox,
        "codex_cli_ask_for_approval": config.codex_cli_client_config.ask_for_approval,
        "planner_worker_runtime_provider": config.planner_worker_runtime_provider,
        "git_worktree_sandbox_opt_in": config.git_worktree_sandbox_root is not None,
        "git_worktree_sandbox_root": (
            "" if config.git_worktree_sandbox_root is None else str(config.git_worktree_sandbox_root)
        ),
        "sandbox_allocation_evidence_id": config.sandbox_allocation_evidence_id,
        "sandbox_allocation_evidence_path": "" if sandbox_write_path is None else str(sandbox_write_path),
        "publish_worker_patch_artifacts": config.publish_worker_patch_artifacts,
        "worker_patch_target_task_id": config.worker_patch_target_task_id,
    }
    metadata.update(dict(config.evidence_metadata))
    return metadata


def _project_path(project_root: str | Path, path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(project_root) / candidate
