"""Read-only promotion candidates for server/API-created worker sessions."""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from pathlib import Path

from .runtime_invocation_audit import JsonlRuntimeInvocationLog, RuntimeInvocationRecord


@dataclass(frozen=True, slots=True)
class WorkerBindingPromotionCandidate:
    """One copyable promotion candidate discovered from runtime audit."""

    candidate_id: str
    source_audit_ref: str
    runtime_invocation_log_path: Path
    invocation_id: str
    attempt_index: int
    provider: str
    session_selector_source: str
    attach_url: str
    session_id: str
    task_id: str = ""
    agent_id: str = ""
    lane_id: str = ""
    suggested_worker_id: str = ""
    suggested_scope_kind: str = "lane"
    suggested_scope_id: str = ""
    suggested_command: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "source_audit_ref": self.source_audit_ref,
            "runtime_invocation_log_path": str(self.runtime_invocation_log_path),
            "invocation_id": self.invocation_id,
            "attempt_index": self.attempt_index,
            "provider": self.provider,
            "session_selector_source": self.session_selector_source,
            "attach_url": self.attach_url,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "lane_id": self.lane_id,
            "suggested_worker_id": self.suggested_worker_id,
            "suggested_scope_kind": self.suggested_scope_kind,
            "suggested_scope_id": self.suggested_scope_id,
            "suggested_command": list(self.suggested_command),
            "suggested_command_text": _command_text(self.suggested_command),
            "authority_split": {
                "read_model_only": True,
                "continuous_worker_binding_ledger_mutated": False,
                "provider_executed": False,
                "session_created": False,
                "delivery_state_mutated": False,
                "scheduler_state_mutated": False,
                "runtime_invocation_log_mutated": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_exposed": False,
                "secret_value_exposed": False,
            },
        }


@dataclass(frozen=True, slots=True)
class WorkerBindingPromotionCandidateReadbackRequest:
    """Read-only request for promotion candidates."""

    runtime_invocation_log_path: str | Path
    latest_limit: int = 100
    include_incomplete: bool = False
    command_prefix: tuple[str, ...] = ("doc-based-coding",)


@dataclass(frozen=True, slots=True)
class WorkerBindingPromotionCandidateReadbackResult:
    """Read-only promotion candidate result."""

    path: Path
    exists: bool
    scanned_record_count: int = 0
    candidate_count: int = 0
    candidates: tuple[WorkerBindingPromotionCandidate, ...] = ()
    errors: tuple[str, ...] = ()
    skipped_count: int = 0
    skip_reasons: dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "path": str(self.path),
            "exists": self.exists,
            "scanned_record_count": self.scanned_record_count,
            "candidate_count": self.candidate_count,
            "candidates": [candidate.to_json_dict() for candidate in self.candidates],
            "errors": list(self.errors),
            "skipped_count": self.skipped_count,
            "skip_reasons": dict(self.skip_reasons),
            "authority_split": {
                "read_model_only": True,
                "continuous_worker_binding_ledger_mutated": False,
                "provider_executed": False,
                "session_created": False,
                "delivery_state_mutated": False,
                "scheduler_state_mutated": False,
                "runtime_invocation_log_mutated": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_exposed": False,
                "secret_value_exposed": False,
            },
        }


def inspect_worker_binding_promotion_candidates(
    request: WorkerBindingPromotionCandidateReadbackRequest,
) -> WorkerBindingPromotionCandidateReadbackResult:
    """Read compact runtime invocation audit and suggest explicit promotions."""

    path = Path(request.runtime_invocation_log_path)
    if not path.exists():
        return WorkerBindingPromotionCandidateReadbackResult(path=path, exists=False)
    try:
        records = JsonlRuntimeInvocationLog(path).read_all()
    except Exception as exc:
        return WorkerBindingPromotionCandidateReadbackResult(
            path=path,
            exists=True,
            errors=(str(exc),),
        )
    selected_records = records[-request.latest_limit:] if request.latest_limit >= 0 else records
    candidates: list[WorkerBindingPromotionCandidate] = []
    skip_reasons: dict[str, int] = {}
    for record in selected_records:
        candidate, reason = _candidate_from_record(
            path,
            record,
            command_prefix=request.command_prefix,
            include_incomplete=request.include_incomplete,
        )
        if candidate is not None:
            candidates.append(candidate)
            continue
        skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
    return WorkerBindingPromotionCandidateReadbackResult(
        path=path,
        exists=True,
        scanned_record_count=len(selected_records),
        candidate_count=len(candidates),
        candidates=tuple(candidates),
        skipped_count=len(selected_records) - len(candidates),
        skip_reasons=dict(sorted(skip_reasons.items())),
    )


def _candidate_from_record(
    path: Path,
    record: RuntimeInvocationRecord,
    *,
    command_prefix: tuple[str, ...],
    include_incomplete: bool,
) -> tuple[WorkerBindingPromotionCandidate | None, str]:
    if record.provider != "opencode":
        return None, "provider_not_opencode"
    if record.status != "succeeded" and not include_incomplete:
        return None, "record_not_succeeded"
    attempt = _latest_server_api_created_attempt(record)
    if attempt is None:
        return None, "not_server_api_created"
    metadata = dict(attempt.metadata)
    attach_url = str(metadata.get("base_url", "")).rstrip("/")
    session_id = str(metadata.get("session_id", ""))
    if not attach_url:
        return None, "missing_attach_url"
    if not session_id:
        return None, "missing_session_id"
    lane_id = str(record.metadata.get("lane_id", ""))
    suggested_worker_id = _suggest_worker_id(record, lane_id)
    suggested_scope_id = lane_id or str(record.task_id or record.agent_id)
    candidate_id = f"worker-binding-promotion:{record.invocation_id}:attempt-{attempt.attempt_index}"
    source_ref = f"{path}#{record.invocation_id}:attempt-{attempt.attempt_index}"
    command = _suggested_command(
        command_prefix,
        worker_id=suggested_worker_id,
        scope_kind="lane" if lane_id else "task",
        scope_id=suggested_scope_id,
        lane_id=lane_id,
        attach_url=attach_url,
        session_id=session_id,
        audit_ref=source_ref,
    )
    return (
        WorkerBindingPromotionCandidate(
            candidate_id=candidate_id,
            source_audit_ref=source_ref,
            runtime_invocation_log_path=path,
            invocation_id=record.invocation_id,
            attempt_index=attempt.attempt_index,
            provider=record.provider,
            session_selector_source="server_api_created",
            attach_url=attach_url,
            session_id=session_id,
            task_id=record.task_id,
            agent_id=record.agent_id,
            lane_id=lane_id,
            suggested_worker_id=suggested_worker_id,
            suggested_scope_kind="lane" if lane_id else "task",
            suggested_scope_id=suggested_scope_id,
            suggested_command=command,
        ),
        "",
    )


def _latest_server_api_created_attempt(record: RuntimeInvocationRecord):
    for attempt in reversed(record.attempts):
        metadata = dict(attempt.metadata)
        if metadata.get("session_selector_source") != "server_api_created":
            continue
        if metadata.get("created_session") is not True:
            continue
        return attempt
    return None


def _suggest_worker_id(record: RuntimeInvocationRecord, lane_id: str) -> str:
    if lane_id:
        safe_lane = lane_id.replace(":", "-").replace("/", "-")
        return f"worker:{safe_lane}"
    if record.agent_id:
        return f"worker:{record.agent_id.replace(':', '-')}"
    if record.task_id:
        return f"worker:{record.task_id.replace(':', '-')}"
    return "worker:opencode-server-api"


def _suggested_command(
    command_prefix: tuple[str, ...],
    *,
    worker_id: str,
    scope_kind: str,
    scope_id: str,
    lane_id: str,
    attach_url: str,
    session_id: str,
    audit_ref: str,
) -> tuple[str, ...]:
    command = [
        *command_prefix,
        "worker-binding",
        "promote-server-api-session",
        "--worker-id",
        worker_id,
        "--scope-kind",
        scope_kind,
        "--scope-id",
        scope_id,
        "--attach-url",
        attach_url,
        "--session-id",
        session_id,
        "--audit-ref",
        audit_ref,
    ]
    if lane_id:
        command.extend(["--lane-id", lane_id])
    return tuple(command)


def _command_text(command: tuple[str, ...]) -> str:
    return " ".join(shlex.quote(part) for part in command)


__all__ = [
    "WorkerBindingPromotionCandidate",
    "WorkerBindingPromotionCandidateReadbackRequest",
    "WorkerBindingPromotionCandidateReadbackResult",
    "inspect_worker_binding_promotion_candidates",
]
