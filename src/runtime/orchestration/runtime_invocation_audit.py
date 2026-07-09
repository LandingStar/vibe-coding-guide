"""Compact runtime invocation audit and retry helpers."""

from __future__ import annotations

import json
import re
import threading
import time
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, TypeVar

from .artifact_paths import dbc_artifact_path
from .log_decoration import LogDecorationPipeline, LogDecorationPipelineResult
from .log_readback import LogRecordRef

RuntimeInvocationStatus = Literal["succeeded", "failed"]

R = TypeVar("R")

RUNTIME_INVOCATION_LOG_SCHEMA_VERSION = "runtime-invocation-log.v1"
DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH = dbc_artifact_path(
    "runtime",
    "invocations.jsonl",
)
DEFAULT_RUNTIME_INVOCATION_ARCHIVE_RELATIVE_PATH = dbc_artifact_path(
    "runtime",
    "archive",
    "invocations.pre-compaction.jsonl",
)


@dataclass(frozen=True, slots=True)
class RuntimeRetryPolicy:
    """Retry policy for host-owned runtime invocation wrappers."""

    max_attempts: int = 1
    backoff_seconds: float = 0.0

    def normalized(self) -> "RuntimeRetryPolicy":
        if self.max_attempts < 1:
            raise ValueError("runtime retry policy max_attempts must be >= 1")
        if self.backoff_seconds < 0:
            raise ValueError("runtime retry policy backoff_seconds must be >= 0")
        return self

    def to_json_dict(self) -> dict[str, object]:
        return {
            "max_attempts": self.max_attempts,
            "backoff_seconds": self.backoff_seconds,
        }


@dataclass(frozen=True, slots=True)
class RuntimeAttemptRecord:
    """One compact runtime invocation attempt."""

    attempt_index: int
    started_at: str
    ended_at: str
    status: RuntimeInvocationStatus
    retryable: bool = False
    error_kind: str = ""
    raw_error_type: str = ""
    summary: str = ""
    stdout_bytes: int | None = None
    stderr_bytes: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "attempt_index": self.attempt_index,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "status": self.status,
            "retryable": self.retryable,
            "error_kind": self.error_kind,
            "raw_error_type": self.raw_error_type,
            "summary": self.summary,
            "metadata": dict(self.metadata),
        }
        if self.stdout_bytes is not None:
            payload["stdout_bytes"] = self.stdout_bytes
        if self.stderr_bytes is not None:
            payload["stderr_bytes"] = self.stderr_bytes
        return payload


@dataclass(frozen=True, slots=True)
class RuntimeInvocationRecord:
    """Append-only compact audit record for one runtime invocation."""

    invocation_id: str
    provider: str
    status: RuntimeInvocationStatus
    started_at: str
    ended_at: str
    task_id: str = ""
    session_id: str = ""
    run_id: str = ""
    agent_id: str = ""
    runtime_surface: str = ""
    attempt_count: int = 0
    retry_policy: RuntimeRetryPolicy = field(default_factory=RuntimeRetryPolicy)
    attempts: tuple[RuntimeAttemptRecord, ...] = ()
    final_error_kind: str = ""
    final_summary: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": RUNTIME_INVOCATION_LOG_SCHEMA_VERSION,
            "invocation_id": self.invocation_id,
            "provider": self.provider,
            "status": self.status,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "runtime_surface": self.runtime_surface,
            "attempt_count": self.attempt_count,
            "retry_policy": self.retry_policy.to_json_dict(),
            "attempts": [attempt.to_json_dict() for attempt in self.attempts],
            "final_error_kind": self.final_error_kind,
            "final_summary": self.final_summary,
            "metadata": dict(self.metadata),
            "authority_split": {
                "runtime_invocation_authority": "host_owned_wrapper",
                "raw_transcript_persisted": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class RuntimeInvocationReadbackEnvelope:
    """Human/audit-oriented readback projection for a runtime invocation."""

    schema_version: str
    record_id: str
    record_kind: str
    timestamp: str
    actor: str
    action: str
    status: str
    summary: str
    reason: str = ""
    run_id: str = ""
    correlation_id: str = ""
    subject_refs: tuple[LogRecordRef, ...] = ()
    input_refs: tuple[LogRecordRef, ...] = ()
    output_refs: tuple[LogRecordRef, ...] = ()
    evidence_refs: tuple[LogRecordRef, ...] = ()
    related_record_ids: tuple[str, ...] = ()
    next_hint: str = ""
    sensitivity: str = "internal"
    redaction_state: str = "contains_no_raw_secret"
    raw_payload_persisted: bool = False
    provider: str = ""
    runtime_surface: str = ""
    attempt_count: int = 0
    max_attempts: int = 1
    retryable: bool = False
    retry_exhausted: bool = False
    final_error_kind: str = ""
    stdout_bytes: int = 0
    stderr_bytes: int = 0

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "record_kind": self.record_kind,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "status": self.status,
            "summary": self.summary,
            "reason": self.reason,
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "subject_refs": [ref.to_json_dict() for ref in self.subject_refs],
            "input_refs": [ref.to_json_dict() for ref in self.input_refs],
            "output_refs": [ref.to_json_dict() for ref in self.output_refs],
            "evidence_refs": [ref.to_json_dict() for ref in self.evidence_refs],
            "related_record_ids": list(self.related_record_ids),
            "next_hint": self.next_hint,
            "sensitivity": self.sensitivity,
            "redaction_state": self.redaction_state,
            "raw_payload_persisted": self.raw_payload_persisted,
            "provider": self.provider,
            "runtime_surface": self.runtime_surface,
            "attempt_count": self.attempt_count,
            "max_attempts": self.max_attempts,
            "retryable": self.retryable,
            "retry_exhausted": self.retry_exhausted,
            "final_error_kind": self.final_error_kind,
            "stdout_bytes": self.stdout_bytes,
            "stderr_bytes": self.stderr_bytes,
        }


@dataclass(frozen=True, slots=True)
class RuntimeInvocationLogSummary:
    """Readback summary for runtime invocation audit records."""

    path: Path
    exists: bool
    record_count: int = 0
    succeeded_count: int = 0
    failed_count: int = 0
    provider_counts: Mapping[str, int] = field(default_factory=dict)
    latest_records: tuple[RuntimeInvocationRecord, ...] = ()
    latest_decoration_results: tuple[LogDecorationPipelineResult, ...] = ()
    errors: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "exists": self.exists,
            "record_count": self.record_count,
            "succeeded_count": self.succeeded_count,
            "failed_count": self.failed_count,
            "provider_counts": dict(self.provider_counts),
            "latest_records": [record.to_json_dict() for record in self.latest_records],
            "latest_decoration_results": [
                result.to_json_dict()
                for result in self.latest_decoration_results
            ],
            "errors": list(self.errors),
            "authority_split": {
                "read_model_only": True,
                "raw_transcript_exposed": False,
                "runtime_invocation_log_mutated": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class RuntimeInvocationCompactionResult:
    """Result of compacting old runtime invocation records."""

    source_path: Path
    archive_path: Path
    retained_path: Path
    archived_count: int
    retained_count: int

    def to_json_dict(self) -> dict[str, object]:
        return {
            "source_path": str(self.source_path),
            "archive_path": str(self.archive_path),
            "retained_path": str(self.retained_path),
            "archived_count": self.archived_count,
            "retained_count": self.retained_count,
        }


class JsonlRuntimeInvocationLog:
    """Append-only JSONL store for compact runtime invocation records."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()

    def append(self, record: RuntimeInvocationRecord) -> RuntimeInvocationRecord:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record.to_json_dict(), ensure_ascii=False, default=str))
                handle.write("\n")
        return record

    def read_all(self) -> tuple[RuntimeInvocationRecord, ...]:
        if not self.path.exists():
            return ()
        records: list[RuntimeInvocationRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(runtime_invocation_record_from_json_dict(json.loads(stripped)))
                except Exception as exc:
                    raise ValueError(
                        f"invalid runtime invocation log line {line_number} in {self.path}: {exc}"
                    ) from exc
        return tuple(records)

    def write_all(self, records: Iterable[RuntimeInvocationRecord]) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record.to_json_dict(), ensure_ascii=False, default=str))
                handle.write("\n")
        return self.path


def run_with_runtime_invocation_audit(
    *,
    invocation_id: str,
    provider: str,
    operation: Callable[[], R],
    log: JsonlRuntimeInvocationLog | None = None,
    retry_policy: RuntimeRetryPolicy | None = None,
    task_id: str = "",
    session_id: str = "",
    run_id: str = "",
    agent_id: str = "",
    runtime_surface: str = "",
    metadata: Mapping[str, object] | None = None,
    timestamp_factory: Callable[[], str] | None = None,
    sleep: Callable[[float], None] | None = None,
) -> R:
    """Run one provider operation with compact attempt audit and retry."""

    policy = (retry_policy or RuntimeRetryPolicy()).normalized()
    now = timestamp_factory or utc_runtime_invocation_timestamp
    sleeper = sleep or time.sleep
    invocation_started_at = now()
    attempts: list[RuntimeAttemptRecord] = []
    last_error: BaseException | None = None

    for attempt_index in range(1, policy.max_attempts + 1):
        attempt_started_at = now()
        try:
            result = operation()
        except BaseException as exc:
            last_error = exc
            retryable = bool(getattr(exc, "retryable", False))
            error_kind = str(getattr(exc, "error_kind", "") or type(exc).__name__)
            attempt = RuntimeAttemptRecord(
                attempt_index=attempt_index,
                started_at=attempt_started_at,
                ended_at=now(),
                status="failed",
                retryable=retryable,
                error_kind=error_kind,
                raw_error_type=str(getattr(exc, "raw_error_type", "") or type(exc).__name__),
                summary=_bounded_redacted_summary(str(getattr(exc, "summary", "") or exc)),
            )
            attempts.append(attempt)
            if not retryable or attempt_index >= policy.max_attempts:
                record = RuntimeInvocationRecord(
                    invocation_id=invocation_id,
                    provider=provider,
                    status="failed",
                    started_at=invocation_started_at,
                    ended_at=now(),
                    task_id=task_id,
                    session_id=session_id,
                    run_id=run_id,
                    agent_id=agent_id,
                    runtime_surface=runtime_surface,
                    attempt_count=len(attempts),
                    retry_policy=policy,
                    attempts=tuple(attempts),
                    final_error_kind=error_kind,
                    final_summary=attempt.summary,
                    metadata=dict(metadata or {}),
                )
                if log is not None:
                    log.append(record)
                raise
            if policy.backoff_seconds:
                sleeper(policy.backoff_seconds)
            continue

        result_metadata = _result_metadata(result)
        attempts.append(
            RuntimeAttemptRecord(
                attempt_index=attempt_index,
                started_at=attempt_started_at,
                ended_at=now(),
                status="succeeded",
                summary=_bounded_redacted_summary(str(result_metadata.get("summary", ""))),
                stdout_bytes=_int_or_none(result_metadata.get("stdout_bytes")),
                stderr_bytes=_int_or_none(result_metadata.get("stderr_bytes")),
                metadata=result_metadata,
            )
        )
        record = RuntimeInvocationRecord(
            invocation_id=invocation_id,
            provider=provider,
            status="succeeded",
            started_at=invocation_started_at,
            ended_at=now(),
            task_id=task_id,
            session_id=session_id,
            run_id=run_id,
            agent_id=agent_id,
            runtime_surface=runtime_surface,
            attempt_count=len(attempts),
            retry_policy=policy,
            attempts=tuple(attempts),
            metadata=dict(metadata or {}),
        )
        if log is not None:
            log.append(record)
        return result

    if last_error is not None:
        raise last_error
    raise RuntimeError("runtime invocation audit runner exited without result")


def inspect_runtime_invocation_log(
    path: str | Path,
    *,
    latest_limit: int = 20,
    decoration_pipeline: LogDecorationPipeline | None = None,
) -> RuntimeInvocationLogSummary:
    """Read compact runtime invocation audit records without mutation."""

    log_path = Path(path)
    if not log_path.exists():
        return RuntimeInvocationLogSummary(path=log_path, exists=False)
    try:
        records = JsonlRuntimeInvocationLog(log_path).read_all()
    except Exception as exc:
        return RuntimeInvocationLogSummary(path=log_path, exists=True, errors=(str(exc),))
    provider_counts: dict[str, int] = {}
    succeeded = 0
    failed = 0
    for record in records:
        provider_counts[record.provider] = provider_counts.get(record.provider, 0) + 1
        if record.status == "succeeded":
            succeeded += 1
        else:
            failed += 1
    latest = records[-latest_limit:] if latest_limit >= 0 else records
    decoration_results: tuple[LogDecorationPipelineResult, ...] = ()
    if decoration_pipeline is not None:
        from .log_decoration_adapters import decorate_log_like_records

        decoration_results = decorate_log_like_records(
            latest,
            decoration_pipeline=decoration_pipeline,
        ).results
    return RuntimeInvocationLogSummary(
        path=log_path,
        exists=True,
        record_count=len(records),
        succeeded_count=succeeded,
        failed_count=failed,
        provider_counts=dict(sorted(provider_counts.items())),
        latest_records=tuple(latest),
        latest_decoration_results=decoration_results,
    )


def compact_runtime_invocation_log(
    source_path: str | Path,
    archive_path: str | Path,
    *,
    retain_latest: int = 100,
) -> RuntimeInvocationCompactionResult:
    """Archive older invocation records and retain only the latest records."""

    if retain_latest < 0:
        raise ValueError("retain_latest must be non-negative")
    source = Path(source_path)
    archive = Path(archive_path)
    records = JsonlRuntimeInvocationLog(source).read_all()
    archived = records[:-retain_latest] if retain_latest else records
    retained = records[-retain_latest:] if retain_latest else ()
    JsonlRuntimeInvocationLog(archive).write_all(archived)
    JsonlRuntimeInvocationLog(source).write_all(retained)
    return RuntimeInvocationCompactionResult(
        source_path=source,
        archive_path=archive,
        retained_path=source,
        archived_count=len(archived),
        retained_count=len(retained),
    )


def runtime_invocation_record_from_json_dict(payload: Mapping[str, Any]) -> RuntimeInvocationRecord:
    """Build a runtime invocation record from JSON payload."""

    if str(payload.get("schema_version", "")) != RUNTIME_INVOCATION_LOG_SCHEMA_VERSION:
        raise ValueError(
            "unsupported runtime invocation log version: "
            f"{payload.get('schema_version')!r}"
        )
    retry_payload = payload.get("retry_policy", {})
    if not isinstance(retry_payload, Mapping):
        retry_payload = {}
    attempts_payload = payload.get("attempts", ())
    if not isinstance(attempts_payload, list):
        raise ValueError("runtime invocation attempts must be a list")
    return RuntimeInvocationRecord(
        invocation_id=str(payload.get("invocation_id", "")),
        provider=str(payload.get("provider", "")),
        status=str(payload.get("status", "failed")),  # type: ignore[arg-type]
        started_at=str(payload.get("started_at", "")),
        ended_at=str(payload.get("ended_at", "")),
        task_id=str(payload.get("task_id", "")),
        session_id=str(payload.get("session_id", "")),
        run_id=str(payload.get("run_id", "")),
        agent_id=str(payload.get("agent_id", "")),
        runtime_surface=str(payload.get("runtime_surface", "")),
        attempt_count=int(payload.get("attempt_count", 0) or 0),
        retry_policy=RuntimeRetryPolicy(
            max_attempts=int(retry_payload.get("max_attempts", 1) or 1),
            backoff_seconds=float(retry_payload.get("backoff_seconds", 0.0) or 0.0),
        ).normalized(),
        attempts=tuple(_attempt_from_json_dict(item) for item in attempts_payload),
        final_error_kind=str(payload.get("final_error_kind", "")),
        final_summary=str(payload.get("final_summary", "")),
        metadata=dict(payload.get("metadata", {}) or {}),
    )


def utc_runtime_invocation_timestamp() -> str:
    """Return an ISO timestamp for runtime invocation audit records."""

    return datetime.now(UTC).isoformat()


def runtime_invocation_record_to_readback_envelope(
    record: RuntimeInvocationRecord,
    *,
    actor: str = "runtime-invocation-wrapper",
) -> RuntimeInvocationReadbackEnvelope:
    """Project a runtime invocation record into a draft readback envelope.

    This is a read-only projection. It does not change invocation JSONL
    persistence, retry behavior, compaction behavior, or provider execution.
    """

    retryable = any(attempt.retryable for attempt in record.attempts)
    retry_exhausted = (
        record.status == "failed"
        and retryable
        and record.attempt_count >= record.retry_policy.max_attempts
    )
    stdout_bytes = sum(
        attempt.stdout_bytes or 0
        for attempt in record.attempts
        if attempt.stdout_bytes is not None
    )
    stderr_bytes = sum(
        attempt.stderr_bytes or 0
        for attempt in record.attempts
        if attempt.stderr_bytes is not None
    )
    return RuntimeInvocationReadbackEnvelope(
        schema_version="runtime-invocation-readback-envelope.v1",
        record_id=record.invocation_id,
        record_kind="runtime_invocation",
        timestamp=record.ended_at or record.started_at,
        actor=record.agent_id or actor,
        action=f"run_provider_{record.status}",
        status=record.status,
        summary=_runtime_invocation_readback_summary(record),
        reason=_runtime_invocation_readback_reason(record, retryable=retryable),
        run_id=record.run_id,
        correlation_id=_runtime_invocation_correlation_id(record),
        subject_refs=_runtime_invocation_subject_refs(record),
        input_refs=_runtime_invocation_input_refs(record),
        output_refs=_runtime_invocation_output_refs(record),
        evidence_refs=_runtime_invocation_evidence_refs(record),
        related_record_ids=_runtime_invocation_related_record_ids(record),
        next_hint=_runtime_invocation_next_hint(record, retryable=retryable),
        raw_payload_persisted=False,
        provider=record.provider,
        runtime_surface=record.runtime_surface,
        attempt_count=record.attempt_count,
        max_attempts=record.retry_policy.max_attempts,
        retryable=retryable,
        retry_exhausted=retry_exhausted,
        final_error_kind=record.final_error_kind,
        stdout_bytes=stdout_bytes,
        stderr_bytes=stderr_bytes,
    )


def _attempt_from_json_dict(payload: Mapping[str, Any]) -> RuntimeAttemptRecord:
    return RuntimeAttemptRecord(
        attempt_index=int(payload.get("attempt_index", 0) or 0),
        started_at=str(payload.get("started_at", "")),
        ended_at=str(payload.get("ended_at", "")),
        status=str(payload.get("status", "failed")),  # type: ignore[arg-type]
        retryable=bool(payload.get("retryable", False)),
        error_kind=str(payload.get("error_kind", "")),
        raw_error_type=str(payload.get("raw_error_type", "")),
        summary=str(payload.get("summary", "")),
        stdout_bytes=_int_or_none(payload.get("stdout_bytes")),
        stderr_bytes=_int_or_none(payload.get("stderr_bytes")),
        metadata=dict(payload.get("metadata", {}) or {}),
    )


def _runtime_invocation_readback_summary(record: RuntimeInvocationRecord) -> str:
    target = _first_non_empty(record.task_id, record.agent_id, record.invocation_id)
    if record.status == "succeeded":
        summary = _first_non_empty(record.final_summary, _latest_attempt_summary(record))
        if summary:
            return f"Runtime provider {record.provider} completed {target}: {summary}"
        return f"Runtime provider {record.provider} completed {target}."
    summary = _first_non_empty(record.final_summary, _latest_attempt_summary(record))
    if summary:
        return f"Runtime provider {record.provider} failed for {target}: {summary}"
    return f"Runtime provider {record.provider} failed for {target}."


def _runtime_invocation_readback_reason(
    record: RuntimeInvocationRecord,
    *,
    retryable: bool,
) -> str:
    if record.status == "succeeded":
        if record.attempt_count > 1:
            return "Runtime invocation succeeded after one or more retry attempts."
        return "Runtime invocation completed successfully."
    parts: list[str] = []
    if record.final_error_kind:
        parts.append(f"Final error kind: {record.final_error_kind}.")
    if retryable:
        if record.attempt_count >= record.retry_policy.max_attempts:
            parts.append("Retryable failure exhausted the configured attempt limit.")
        else:
            parts.append("Failure was marked retryable by at least one attempt.")
    else:
        parts.append("Failure was not marked retryable by the runtime audit record.")
    summary = _first_non_empty(record.final_summary, _latest_attempt_summary(record))
    if summary:
        parts.append(f"Summary: {summary}")
    return " ".join(parts)


def _runtime_invocation_subject_refs(record: RuntimeInvocationRecord) -> tuple[LogRecordRef, ...]:
    refs: list[LogRecordRef] = [
        LogRecordRef(kind="runtime_invocation", id=record.invocation_id, role="subject")
    ]
    if record.task_id:
        refs.append(LogRecordRef(kind="task", id=record.task_id, role="subject"))
    if record.agent_id:
        refs.append(LogRecordRef(kind="worker", id=record.agent_id, role="subject"))
    if record.run_id:
        refs.append(LogRecordRef(kind="run", id=record.run_id, role="subject"))
    if record.session_id:
        refs.append(
            LogRecordRef(kind="provider_session", id=record.session_id, role="subject")
        )
    if record.provider:
        refs.append(LogRecordRef(kind="provider", id=record.provider, role="subject"))
    if record.runtime_surface:
        refs.append(
            LogRecordRef(
                kind="runtime_surface",
                id=record.runtime_surface,
                role="subject",
            )
        )
    return tuple(refs)


def _runtime_invocation_input_refs(record: RuntimeInvocationRecord) -> tuple[LogRecordRef, ...]:
    refs: list[LogRecordRef] = []
    lane_id = _metadata_text(record.metadata, "lane_id")
    if lane_id:
        refs.append(LogRecordRef(kind="lane", id=lane_id, role="input"))
    context_id = _metadata_text(record.metadata, "context_id")
    if context_id:
        refs.append(LogRecordRef(kind="context", id=context_id, role="input"))
    host_invocation_id = _metadata_text(record.metadata, "host_invocation_id")
    if host_invocation_id:
        refs.append(
            LogRecordRef(kind="host_invocation", id=host_invocation_id, role="input")
        )
    binding_id = _metadata_text(record.metadata, "continuous_worker_binding_id")
    if binding_id:
        refs.append(
            LogRecordRef(kind="continuous_worker_binding", id=binding_id, role="input")
        )
    worker_id = _metadata_text(record.metadata, "continuous_worker_id")
    if worker_id:
        refs.append(LogRecordRef(kind="continuous_worker", id=worker_id, role="input"))
    return tuple(refs)


def _runtime_invocation_output_refs(record: RuntimeInvocationRecord) -> tuple[LogRecordRef, ...]:
    refs: list[LogRecordRef] = []
    output_artifact_id = _metadata_text(record.metadata, "output_artifact_id")
    if output_artifact_id:
        refs.append(
            LogRecordRef(
                kind="artifact",
                id=output_artifact_id,
                version=_metadata_text(record.metadata, "output_artifact_version"),
                role="output",
            )
        )
    result_artifact_id = _metadata_text(record.metadata, "result_artifact_id")
    if result_artifact_id and result_artifact_id != output_artifact_id:
        refs.append(
            LogRecordRef(
                kind="artifact",
                id=result_artifact_id,
                version=_metadata_text(record.metadata, "result_artifact_version"),
                role="output",
            )
        )
    return tuple(refs)


def _runtime_invocation_evidence_refs(record: RuntimeInvocationRecord) -> tuple[LogRecordRef, ...]:
    refs: list[LogRecordRef] = [
        LogRecordRef(
            kind="runtime_invocation",
            id=record.invocation_id,
            label=record.status,
            role="evidence",
        )
    ]
    for attempt in record.attempts:
        label_parts = [attempt.status]
        if attempt.error_kind:
            label_parts.append(attempt.error_kind)
        if attempt.retryable:
            label_parts.append("retryable")
        byte_parts: list[str] = []
        if attempt.stdout_bytes is not None:
            byte_parts.append(f"stdout_bytes={attempt.stdout_bytes}")
        if attempt.stderr_bytes is not None:
            byte_parts.append(f"stderr_bytes={attempt.stderr_bytes}")
        if byte_parts:
            label_parts.append(", ".join(byte_parts))
        refs.append(
            LogRecordRef(
                kind="runtime_attempt",
                id=f"{record.invocation_id}:attempt-{attempt.attempt_index}",
                label="; ".join(label_parts),
                role="evidence",
            )
        )
    return tuple(refs)


def _runtime_invocation_related_record_ids(
    record: RuntimeInvocationRecord,
) -> tuple[str, ...]:
    related: list[str] = []
    for prefix, value in (
        ("task", record.task_id),
        ("agent", record.agent_id),
        ("provider_session", record.session_id),
        ("run", record.run_id),
        ("provider", record.provider),
        ("runtime_surface", record.runtime_surface),
    ):
        if value:
            related.append(_related_record_id(prefix, value))
    for key in (
        "lane_id",
        "context_id",
        "host_invocation_id",
        "continuous_worker_binding_id",
        "continuous_worker_id",
    ):
        value = _metadata_text(record.metadata, key)
        if value:
            related.append(_related_record_id(key.removesuffix("_id"), value))
    return tuple(related)


def _runtime_invocation_next_hint(
    record: RuntimeInvocationRecord,
    *,
    retryable: bool,
) -> str:
    if record.status == "failed":
        if retryable:
            return (
                f"Inspect delivery retry policy and runtime attempts for "
                f"invocation {record.invocation_id}."
            )
        if record.run_id:
            return f"Inspect scheduler and delivery records for run {record.run_id}."
        if record.task_id:
            return f"Inspect scheduler task and worker delivery state for {record.task_id}."
        return f"Inspect runtime invocation {record.invocation_id} failure context."
    outputs = _runtime_invocation_output_refs(record)
    if outputs:
        return f"Inspect output artifact {outputs[0].id}."
    if record.run_id:
        return f"Inspect scheduler run {record.run_id} and output artifacts."
    if record.task_id:
        return f"Inspect scheduler task {record.task_id} and delivery acknowledgement."
    return f"Inspect runtime invocation {record.invocation_id}."


def _runtime_invocation_correlation_id(record: RuntimeInvocationRecord) -> str:
    return _first_non_empty(
        record.run_id,
        _metadata_text(record.metadata, "host_invocation_id"),
        record.task_id,
        record.invocation_id,
    )


def _latest_attempt_summary(record: RuntimeInvocationRecord) -> str:
    if not record.attempts:
        return ""
    return record.attempts[-1].summary


def _metadata_text(metadata: Mapping[str, object], key: str) -> str:
    value = metadata.get(key, "")
    if value is None or isinstance(value, (list, tuple, dict, set)):
        return ""
    return str(value)


def _related_record_id(kind: str, value: str) -> str:
    if value.startswith(f"{kind}:"):
        return value
    return f"{kind}:{value}"


def _first_non_empty(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def _result_metadata(result: object) -> dict[str, object]:
    metadata = getattr(result, "metadata", None)
    if isinstance(metadata, Mapping):
        payload = dict(metadata)
    else:
        payload = {}
    summary = getattr(result, "summary", "")
    if summary:
        payload["summary"] = _bounded_redacted_summary(str(summary))
    return payload


def _int_or_none(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _bounded_redacted_summary(value: str, *, limit: int = 500) -> str:
    text = str(value or "").replace("\r\n", "\n").strip()
    redacted = text
    for marker in (
        "OPENAI_API_KEY",
        "CODEX_AUTH_TOKEN",
        "QODER_PERSONAL_ACCESS_TOKEN",
        "DASHSCOPE_API_KEY",
    ):
        redacted = re.sub(
            rf"{re.escape(marker)}\s*=\s*[^\s,;]+",
            f"{marker}=[redacted]",
            redacted,
        )
        redacted = re.sub(
            rf"\b{re.escape(marker)}\b(?!=\[redacted\])",
            f"{marker}[redacted]",
            redacted,
        )
    if len(redacted) <= limit:
        return redacted
    return redacted[: limit - 3].rstrip() + "..."
