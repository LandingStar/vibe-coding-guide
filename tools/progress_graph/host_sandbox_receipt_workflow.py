"""Host workflow for git-worktree receipt allocate/read/cleanup/read.

This module composes existing host runner, daemon loop, cleanup runner, and
Host Evidence presentation products. It stays outside core orchestration
runtime because readback presentation is a host/operator surface concern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Mapping

from src.runtime.orchestration import (
    HostSchedulerDaemonLoopRequest,
    HostSchedulerRunRequest,
    InMemoryArtifactVersionStore,
    JsonlCoordinationEventLog,
    QoderQueryClient,
    SandboxAllocationReceiptEvidenceWriteResult,
    SandboxCleanupRunnerResult,
    SandboxProviderRegistry,
    read_sandbox_allocation_receipt_evidence_summary,
    run_host_authorized_scheduler_daemon_loop,
    run_host_authorized_scheduler_once,
    run_sandbox_allocation_cleanup_over_receipts,
)

from .host_evidence import HostEvidenceBundle, build_host_evidence_presentation


HostSandboxReceiptWorkflowMode = Literal["run_once", "daemon_loop"]
HostSandboxReceiptWorkflowStepStatus = Literal["completed", "skipped", "failed"]


@dataclass(frozen=True, slots=True)
class HostSandboxReceiptWorkflowRequest:
    """Request for explicit git-worktree receipt lifecycle workflow."""

    project_root: str | Path
    mode: HostSandboxReceiptWorkflowMode
    run_once_request: HostSchedulerRunRequest | None = None
    daemon_loop_request: HostSchedulerDaemonLoopRequest | None = None
    cleanup: bool = False
    cleanup_evidence_id: str = ""
    cleanup_evidence_path: str | Path | None = None
    timestamp: str = ""
    git_executable: str = "git"
    cleanup_metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HostSandboxReceiptWorkflowStep:
    """One workflow step with isolated status."""

    name: str
    status: HostSandboxReceiptWorkflowStepStatus
    mutated: bool = False
    error: str = ""
    result: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "mutated": self.mutated,
            "error": self.error,
            "result": dict(self.result),
        }


@dataclass(frozen=True, slots=True)
class HostSandboxReceiptWorkflowResult:
    """Result of explicit allocate/read/cleanup/read workflow."""

    request: HostSandboxReceiptWorkflowRequest
    project_root: Path
    allocation_evidence_path: Path
    cleanup_evidence_path: Path | None
    steps: tuple[HostSandboxReceiptWorkflowStep, ...]
    run_result: Mapping[str, object] = field(default_factory=dict)
    allocation_readback_presentation: Mapping[str, object] = field(default_factory=dict)
    cleanup_result: Mapping[str, object] = field(default_factory=dict)
    cleanup_readback_presentation: Mapping[str, object] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not any(step.status == "failed" for step in self.steps)

    @property
    def authority_split(self) -> dict[str, object]:
        cleanup_authority = _mapping(self.cleanup_result.get("authority_split"))
        return {
            "workflow_surface": "host-sandbox-receipt-workflow",
            "workflow_mode": self.request.mode,
            "host_run_executed": self.request.mode == "run_once",
            "host_daemon_loop_executed": self.request.mode == "daemon_loop",
            "allocation_evidence_written": _step_mutated(self.steps, "runHostSchedulerOnce")
            or _step_mutated(self.steps, "runHostSchedulerDaemonLoop"),
            "allocation_readback_performed": _step_completed(self.steps, "readAllocationEvidence"),
            "cleanup_requested": self.request.cleanup,
            "cleanup_executed": bool(cleanup_authority.get("cleanup_executed")),
            "cleanup_evidence_written": _step_mutated(self.steps, "cleanupReceipts"),
            "cleanup_readback_performed": _step_completed(self.steps, "readCleanupEvidence"),
            "local_work_trajectory_mutated": False,
        }

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "workflow_surface": "host-sandbox-receipt-workflow",
            "workflow_mode": self.request.mode,
            "project_root": str(self.project_root),
            "paths": {
                "allocation_evidence_path": str(self.allocation_evidence_path),
                "cleanup_evidence_path": (
                    "" if self.cleanup_evidence_path is None else str(self.cleanup_evidence_path)
                ),
            },
            "request": {
                "mode": self.request.mode,
                "cleanup": self.request.cleanup,
                "cleanup_evidence_id": self.request.cleanup_evidence_id,
                "timestamp": self.request.timestamp,
                "git_executable": self.request.git_executable,
            },
            "steps": [step.to_json_dict() for step in self.steps],
            "run_result": dict(self.run_result),
            "allocation_readback_presentation": dict(self.allocation_readback_presentation),
            "cleanup_result": dict(self.cleanup_result),
            "cleanup_readback_presentation": dict(self.cleanup_readback_presentation),
            "authority_split": self.authority_split,
        }


def run_host_sandbox_receipt_workflow(
    request: HostSandboxReceiptWorkflowRequest,
    *,
    artifact_store: InMemoryArtifactVersionStore | None = None,
    coordination_event_log: JsonlCoordinationEventLog | None = None,
    qoder_query_client: QoderQueryClient | None = None,
    sandbox_registry: SandboxProviderRegistry | None = None,
) -> HostSandboxReceiptWorkflowResult:
    """Run explicit allocate/read/cleanup/read workflow for host receipts."""

    _validate_request(request)
    project_root = Path(request.project_root).resolve()
    steps: list[HostSandboxReceiptWorkflowStep] = []

    run_payload, allocation_write = _run_host_allocation_step(
        request,
        artifact_store=artifact_store,
        coordination_event_log=coordination_event_log,
        qoder_query_client=qoder_query_client,
        sandbox_registry=sandbox_registry,
    )
    allocation_path = allocation_write.evidence_path
    steps.append(
        HostSandboxReceiptWorkflowStep(
            name=(
                "runHostSchedulerOnce"
                if request.mode == "run_once"
                else "runHostSchedulerDaemonLoop"
            ),
            status="completed",
            mutated=True,
            result=run_payload,
        )
    )

    allocation_readback = _focused_sandbox_evidence_presentation(
        project_root,
        allocation_path,
        generated_at=request.timestamp,
    )
    steps.append(
        HostSandboxReceiptWorkflowStep(
            name="readAllocationEvidence",
            status="completed",
            result=allocation_readback,
        )
    )

    cleanup_payload: Mapping[str, object] = {}
    cleanup_readback: Mapping[str, object] = {}
    cleanup_path: Path | None = None
    if request.cleanup:
        cleanup = run_sandbox_allocation_cleanup_over_receipts(
            allocation_path,
            output_evidence_path=request.cleanup_evidence_path,
            output_evidence_id=request.cleanup_evidence_id,
            timestamp=request.timestamp,
            git_executable=request.git_executable,
            metadata={
                "surface": "host-sandbox-receipt-workflow",
                "workflow_surface": "host-sandbox-receipt-workflow",
                "workflow_mode": request.mode,
                **dict(request.cleanup_metadata),
            },
        )
        cleanup_payload = cleanup.to_json_dict()
        cleanup_path = cleanup.output_evidence_path
        cleanup_ok = bool(cleanup_payload.get("ok"))
        steps.append(
            HostSandboxReceiptWorkflowStep(
                name="cleanupReceipts",
                status="completed" if cleanup_ok else "failed",
                mutated=True,
                error="" if cleanup_ok else "one or more cleanup receipts failed",
                result=cleanup_payload,
            )
        )
        cleanup_readback = _focused_sandbox_evidence_presentation(
            project_root,
            cleanup_path,
            generated_at=request.timestamp,
        )
        steps.append(
            HostSandboxReceiptWorkflowStep(
                name="readCleanupEvidence",
                status="completed",
                result=cleanup_readback,
            )
        )
    else:
        steps.append(_skipped("cleanupReceipts", "cleanup=false"))
        steps.append(_skipped("readCleanupEvidence", "cleanup=false"))

    return HostSandboxReceiptWorkflowResult(
        request=request,
        project_root=project_root,
        allocation_evidence_path=allocation_path,
        cleanup_evidence_path=cleanup_path,
        steps=tuple(steps),
        run_result=run_payload,
        allocation_readback_presentation=allocation_readback,
        cleanup_result=cleanup_payload,
        cleanup_readback_presentation=cleanup_readback,
    )


def _run_host_allocation_step(
    request: HostSandboxReceiptWorkflowRequest,
    *,
    artifact_store: InMemoryArtifactVersionStore | None,
    coordination_event_log: JsonlCoordinationEventLog | None,
    qoder_query_client: QoderQueryClient | None,
    sandbox_registry: SandboxProviderRegistry | None,
) -> tuple[Mapping[str, object], SandboxAllocationReceiptEvidenceWriteResult]:
    if request.mode == "run_once":
        assert request.run_once_request is not None
        result = run_host_authorized_scheduler_once(
            request.run_once_request,
            artifact_store=artifact_store,
            coordination_event_log=coordination_event_log,
            qoder_query_client=qoder_query_client,
            sandbox_registry=sandbox_registry,
        )
        if result.sandbox_allocation_evidence_write is None:
            raise ValueError("host sandbox receipt workflow requires allocation evidence write")
        return result.to_json_dict(), result.sandbox_allocation_evidence_write

    assert request.daemon_loop_request is not None
    result = run_host_authorized_scheduler_daemon_loop(
        request.daemon_loop_request,
        artifact_store=artifact_store,
        coordination_event_log=coordination_event_log,
        qoder_query_client=qoder_query_client,
        sandbox_registry=sandbox_registry,
    )
    if result.sandbox_allocation_evidence_write is None:
        raise ValueError("host sandbox receipt workflow requires allocation evidence write")
    return result.to_json_dict(), result.sandbox_allocation_evidence_write


def _validate_request(request: HostSandboxReceiptWorkflowRequest) -> None:
    if request.mode == "run_once":
        if request.run_once_request is None or request.daemon_loop_request is not None:
            raise ValueError("run_once workflow requires only run_once_request")
        _validate_allocation_request(
            request.run_once_request.git_worktree_sandbox_root,
            request.run_once_request.sandbox_allocation_evidence_id,
            label="run_once",
        )
    elif request.mode == "daemon_loop":
        if request.daemon_loop_request is None or request.run_once_request is not None:
            raise ValueError("daemon_loop workflow requires only daemon_loop_request")
        _validate_allocation_request(
            request.daemon_loop_request.git_worktree_sandbox_root,
            request.daemon_loop_request.sandbox_allocation_evidence_id,
            label="daemon_loop",
        )
    else:
        raise ValueError(f"unsupported host sandbox receipt workflow mode: {request.mode!r}")

    if not request.cleanup and (
        request.cleanup_evidence_id or request.cleanup_evidence_path is not None
    ):
        raise ValueError("cleanup evidence output requires cleanup=True")


def _validate_allocation_request(
    git_worktree_sandbox_root: object,
    sandbox_allocation_evidence_id: str,
    *,
    label: str,
) -> None:
    if git_worktree_sandbox_root is None:
        raise ValueError(f"{label} workflow requires git-worktree sandbox opt-in")
    if not sandbox_allocation_evidence_id:
        raise ValueError(f"{label} workflow requires sandbox_allocation_evidence_id")


def _focused_sandbox_evidence_presentation(
    project_root: Path,
    evidence_path: Path,
    *,
    generated_at: str,
) -> Mapping[str, object]:
    summary = read_sandbox_allocation_receipt_evidence_summary(evidence_path)
    return build_host_evidence_presentation(
        HostEvidenceBundle(
            project_root=project_root,
            evidence_dir=evidence_path.parent,
            summaries=(summary,),
        ),
        generated_at=generated_at,
    ).to_json_dict()


def _skipped(name: str, reason: str) -> HostSandboxReceiptWorkflowStep:
    return HostSandboxReceiptWorkflowStep(name=name, status="skipped", error=reason)


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _step_completed(
    steps: tuple[HostSandboxReceiptWorkflowStep, ...],
    name: str,
) -> bool:
    return any(step.name == name and step.status == "completed" for step in steps)


def _step_mutated(
    steps: tuple[HostSandboxReceiptWorkflowStep, ...],
    name: str,
) -> bool:
    return any(step.name == name and step.mutated for step in steps)
