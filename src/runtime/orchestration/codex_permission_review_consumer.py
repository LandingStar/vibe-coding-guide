"""Durable consumption of Codex permission-review runtime results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .exchange_store import ArtifactVersionRecord, JsonArtifactVersionStore
from .runtime_adapter import PermissionRequest, RuntimeRunResult
from .scheduler import ScheduledTask, SchedulerEvent
from .scheduler_store import JsonlSchedulerEventLog


@dataclass(frozen=True, slots=True)
class CodexPermissionReviewConsumerRequest:
    """Request for recording one Codex permission-review outcome."""

    artifact_store_path: str | Path
    scheduler_event_log_path: str | Path
    timestamp: str = ""
    event_id_prefix: str = "codex-review"
    actor: str = "host:codex-permission-review-consumer"
    replace_existing_artifact: bool = False


@dataclass(frozen=True, slots=True)
class CodexPermissionReviewConsumerResult:
    """Durable facts written for one permission-review outcome."""

    artifact_store_path: Path
    scheduler_event_log_path: Path
    task_id: str
    run_id: str
    session_id: str
    artifact_id: str
    artifact_version: str
    scheduler_event_id: str
    reason: str
    permission_requests: tuple[PermissionRequest, ...]
    artifact_record: ArtifactVersionRecord
    scheduler_event: SchedulerEvent

    @property
    def permission_request_count(self) -> int:
        return len(self.permission_requests)

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible result payload."""

        return {
            "artifact_store_path": str(self.artifact_store_path),
            "scheduler_event_log_path": str(self.scheduler_event_log_path),
            "task_id": self.task_id,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "output_artifact_ref": {
                "ref_kind": "exchange_artifact" if self.artifact_id else "",
                "ref_id": self.artifact_id,
                "version": self.artifact_version,
            },
            "scheduler_event_id": self.scheduler_event_id,
            "reason": self.reason,
            "permission_request_count": self.permission_request_count,
            "permission_requests": [
                _permission_request_to_json_dict(request)
                for request in self.permission_requests
            ],
            "scheduler_event_log_mutated": True,
            "scheduler_state_mutated": False,
            "exchange_store_mutated": True,
        }


def consume_codex_permission_review_result(
    request: CodexPermissionReviewConsumerRequest,
    *,
    task: ScheduledTask,
    run_result: RuntimeRunResult,
) -> CodexPermissionReviewConsumerResult:
    """Append scheduler review-required state for a permission-requesting run."""

    if not run_result.permission_requests:
        raise ValueError(
            "Codex permission review consumer requires at least one permission request"
        )
    artifact_store_path = Path(request.artifact_store_path)
    scheduler_event_log_path = Path(request.scheduler_event_log_path)
    reason = _permission_review_reason(run_result.permission_requests)
    artifact_record = JsonArtifactVersionStore(artifact_store_path).put(
        run_result.output_artifact,
        replace_existing=request.replace_existing_artifact,
    )
    event = SchedulerEvent(
        event_id=_scheduler_review_event_id(
            request.event_id_prefix,
            task.task_id,
            run_result.run_handle.run_id,
        ),
        event_kind="task_review_required",
        timestamp=request.timestamp,
        task_id=task.task_id,
        from_state="running",
        to_state="review_required",
        reason=reason,
        run_id=run_result.run_handle.run_id,
        session_id=run_result.run_handle.session_id,
        output_artifact_id=run_result.output_artifact.artifact_id,
        output_artifact_version=run_result.output_artifact.version,
        related_artifact_ids=(run_result.output_artifact.artifact_id,),
    )
    appended_event = JsonlSchedulerEventLog(scheduler_event_log_path).append(event)
    return CodexPermissionReviewConsumerResult(
        artifact_store_path=artifact_store_path,
        scheduler_event_log_path=scheduler_event_log_path,
        task_id=task.task_id,
        run_id=run_result.run_handle.run_id,
        session_id=run_result.run_handle.session_id,
        artifact_id=run_result.output_artifact.artifact_id,
        artifact_version=run_result.output_artifact.version,
        scheduler_event_id=appended_event.event_id,
        reason=reason,
        permission_requests=tuple(run_result.permission_requests),
        artifact_record=artifact_record,
        scheduler_event=appended_event,
    )


def _scheduler_review_event_id(
    event_id_prefix: str,
    task_id: str,
    run_id: str,
) -> str:
    return ":".join(
        part
        for part in (
            event_id_prefix or "codex-review",
            "task-review-required",
            task_id,
            run_id,
        )
        if part
    )


def _permission_review_reason(
    permission_requests: tuple[PermissionRequest, ...],
) -> str:
    if len(permission_requests) == 1:
        request = permission_requests[0]
        return f"permission review required: {request.request_kind} {request.target}".rstrip()
    return f"permission review required: {len(permission_requests)} requests"


def _permission_request_to_json_dict(
    request: PermissionRequest,
) -> dict[str, object]:
    return {
        "request_id": request.request_id,
        "request_kind": request.request_kind,
        "run_id": request.run_id,
        "summary": request.summary,
        "target": request.target,
    }


__all__ = [
    "CodexPermissionReviewConsumerRequest",
    "CodexPermissionReviewConsumerResult",
    "consume_codex_permission_review_result",
]
