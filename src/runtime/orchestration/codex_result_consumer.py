"""Durable consumption of successful Codex runtime results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .exchange_store import ArtifactVersionRecord, JsonArtifactVersionStore
from .runtime_adapter import RuntimeRunResult
from .scheduler import ScheduledTask, SchedulerEvent
from .scheduler_store import JsonlSchedulerEventLog


@dataclass(frozen=True, slots=True)
class CodexResultConsumerRequest:
    """Request for consuming one successful Codex runtime result."""

    artifact_store_path: str | Path
    scheduler_event_log_path: str | Path
    timestamp: str = ""
    event_id_prefix: str = "codex-result"
    actor: str = "host:codex-result-consumer"
    replace_existing_artifact: bool = False


@dataclass(frozen=True, slots=True)
class CodexResultConsumerResult:
    """Durable facts written for one successful Codex result."""

    artifact_store_path: Path
    scheduler_event_log_path: Path
    task_id: str
    run_id: str
    session_id: str
    artifact_id: str
    artifact_version: str
    scheduler_event_id: str
    artifact_record: ArtifactVersionRecord
    scheduler_event: SchedulerEvent

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible result payload."""

        return {
            "artifact_store_path": str(self.artifact_store_path),
            "scheduler_event_log_path": str(self.scheduler_event_log_path),
            "task_id": self.task_id,
            "run_id": self.run_id,
            "session_id": self.session_id,
            "output_artifact_ref": {
                "ref_kind": "exchange_artifact",
                "ref_id": self.artifact_id,
                "version": self.artifact_version,
            },
            "scheduler_event_id": self.scheduler_event_id,
            "exchange_store_mutated": True,
            "scheduler_event_log_mutated": True,
            "scheduler_state_mutated": False,
        }


def consume_successful_codex_result(
    request: CodexResultConsumerRequest,
    *,
    task: ScheduledTask,
    run_result: RuntimeRunResult,
) -> CodexResultConsumerResult:
    """Store a successful Codex result and append scheduler completion.

    Scheduler snapshots are intentionally not written here. Consumers should use
    ``recover_scheduler_state()`` to read snapshot plus event log.
    """

    artifact_store_path = Path(request.artifact_store_path)
    scheduler_event_log_path = Path(request.scheduler_event_log_path)
    artifact_record = JsonArtifactVersionStore(artifact_store_path).put(
        run_result.output_artifact,
        replace_existing=request.replace_existing_artifact,
    )
    event = SchedulerEvent(
        event_id=_scheduler_completion_event_id(
            request.event_id_prefix,
            task.task_id,
            run_result.run_handle.run_id,
        ),
        event_kind="task_completed",
        timestamp=request.timestamp,
        task_id=task.task_id,
        from_state="running",
        to_state="complete",
        run_id=run_result.run_handle.run_id,
        session_id=run_result.run_handle.session_id,
        output_artifact_id=run_result.output_artifact.artifact_id,
        output_artifact_version=run_result.output_artifact.version,
        related_artifact_ids=(run_result.output_artifact.artifact_id,),
    )
    appended_event = JsonlSchedulerEventLog(scheduler_event_log_path).append(event)
    return CodexResultConsumerResult(
        artifact_store_path=artifact_store_path,
        scheduler_event_log_path=scheduler_event_log_path,
        task_id=task.task_id,
        run_id=run_result.run_handle.run_id,
        session_id=run_result.run_handle.session_id,
        artifact_id=artifact_record.artifact_id,
        artifact_version=artifact_record.version,
        scheduler_event_id=appended_event.event_id,
        artifact_record=artifact_record,
        scheduler_event=appended_event,
    )


def _scheduler_completion_event_id(
    event_id_prefix: str,
    task_id: str,
    run_id: str,
) -> str:
    return ":".join(
        part
        for part in (
            event_id_prefix or "codex-result",
            "task-completed",
            task_id,
            run_id,
        )
        if part
    )


__all__ = [
    "CodexResultConsumerRequest",
    "CodexResultConsumerResult",
    "consume_successful_codex_result",
]
