"""Projection adapters from existing compact logs to log decoration records."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import dataclass

from .agent_storage import CleanupReceipt
from .continuous_worker_binding import (
    ContinuousWorkerBindingEventRecord,
    DeliveryLeaseEventRecord,
    LaneOwnershipEventRecord,
)
from .exchange import ExchangeLog
from .exchange_admission_ledger import ExchangeArtifactAdmissionRecord
from .exchange_store import CoordinationEvent
from .leader_worker_activation import AgentActivationEvent
from .leader_worker_dispatcher import LeaderWorkerDispatcherTickRecord
from .leader_worker_delivery import LeaderWorkerDeliveryEventRecord
from .log_decoration import (
    LogDecorationPipeline,
    LogDecorationPipelineResult,
    LogDecorationRecord,
)
from .opencode_serve_lifecycle import OpenCodeServeLifecycleReceipt
from .runtime_adapter import RunEvent
from .runtime_invocation_audit import RuntimeInvocationRecord
from .sandbox import (
    GitWorktreeCommandReceipt,
    GitWorktreeSandboxReceipt,
    SandboxAllocation,
)
from .sandbox_allocation_evidence import (
    SandboxAllocationReceiptEvidence,
    SandboxAllocationReceiptEvidenceSummary,
)
from .scheduler import SchedulerEvent, SchedulerMergeGateEvent
from .trajectory_team_continuity import TrajectoryTeamContinuityEventRecord


@dataclass(frozen=True, slots=True)
class LogLikeRecordBatchDecorationResult:
    """Batch decoration evidence for existing compact log-like records."""

    results: tuple[LogDecorationPipelineResult, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors and all(result.ok for result in self.results)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "result_count": len(self.results),
            "error_count": len(self.errors),
            "results": [result.to_json_dict() for result in self.results],
            "errors": list(self.errors),
            "authority_split": {
                "read_model_only": True,
                "persistence_mutated": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "runtime_invocation_log_mutated": False,
                "local_work_trajectory_mutated": False,
                "provider_executed": False,
                "raw_transcript_persisted": False,
            },
        }


def decorate_log_like_records(
    records: object,
    *,
    decoration_pipeline: LogDecorationPipeline,
    fields: Mapping[str, object] | None = None,
) -> LogLikeRecordBatchDecorationResult:
    """Decorate supported log-like records while isolating projection errors."""

    results: list[LogDecorationPipelineResult] = []
    errors: list[str] = []
    for index, record in enumerate(_iter_records(records)):
        try:
            projected = log_like_record_to_decoration_record(record, fields=fields)
            results.append(decoration_pipeline.run(projected))
        except Exception as exc:
            errors.append(f"record[{index}] {type(record).__name__}: {exc}")
    return LogLikeRecordBatchDecorationResult(
        results=tuple(results),
        errors=tuple(errors),
    )


def log_like_record_to_decoration_record(
    record: object,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a supported compact log-like record into the decoration shape."""

    if isinstance(record, ExchangeLog):
        return exchange_log_to_decoration_record(record, fields=fields)
    if isinstance(record, CoordinationEvent):
        return coordination_event_to_decoration_record(record, fields=fields)
    if isinstance(record, SchedulerEvent):
        return scheduler_event_to_decoration_record(record, fields=fields)
    if isinstance(record, SchedulerMergeGateEvent):
        return scheduler_merge_gate_event_to_decoration_record(record, fields=fields)
    if isinstance(record, RuntimeInvocationRecord):
        return runtime_invocation_record_to_decoration_record(record, fields=fields)
    if isinstance(record, AgentActivationEvent):
        return agent_activation_event_to_decoration_record(record, fields=fields)
    if isinstance(record, LeaderWorkerDispatcherTickRecord):
        return leader_worker_dispatcher_tick_record_to_decoration_record(
            record,
            fields=fields,
        )
    if isinstance(record, RunEvent):
        return run_event_to_decoration_record(record, fields=fields)
    if isinstance(record, ExchangeArtifactAdmissionRecord):
        return exchange_artifact_admission_record_to_decoration_record(
            record,
            fields=fields,
        )
    if isinstance(record, ContinuousWorkerBindingEventRecord):
        return continuous_worker_binding_event_to_decoration_record(record, fields=fields)
    if isinstance(record, LaneOwnershipEventRecord):
        return lane_ownership_event_to_decoration_record(record, fields=fields)
    if isinstance(record, DeliveryLeaseEventRecord):
        return delivery_lease_event_to_decoration_record(record, fields=fields)
    if isinstance(record, LeaderWorkerDeliveryEventRecord):
        return leader_worker_delivery_event_to_decoration_record(record, fields=fields)
    if isinstance(record, TrajectoryTeamContinuityEventRecord):
        return trajectory_team_continuity_event_to_decoration_record(record, fields=fields)
    if isinstance(record, OpenCodeServeLifecycleReceipt):
        return opencode_serve_lifecycle_receipt_to_decoration_record(record, fields=fields)
    if isinstance(record, CleanupReceipt):
        return cleanup_receipt_to_decoration_record(record, fields=fields)
    if isinstance(record, GitWorktreeCommandReceipt):
        return git_worktree_command_receipt_to_decoration_record(record, fields=fields)
    if isinstance(record, GitWorktreeSandboxReceipt):
        return git_worktree_sandbox_receipt_to_decoration_record(record, fields=fields)
    if isinstance(record, SandboxAllocation):
        return sandbox_allocation_to_decoration_record(record, fields=fields)
    if isinstance(record, SandboxAllocationReceiptEvidence):
        return sandbox_allocation_receipt_evidence_to_decoration_record(
            record,
            fields=fields,
        )
    if isinstance(record, SandboxAllocationReceiptEvidenceSummary):
        return sandbox_allocation_receipt_evidence_summary_to_decoration_record(
            record,
            fields=fields,
        )
    if hasattr(record, "event_type") and hasattr(record, "trace_id"):
        return audit_event_to_decoration_record(record, fields=fields)
    if hasattr(record, "decision_id") and hasattr(record, "decision"):
        return decision_log_entry_to_decoration_record(record, fields=fields)
    raise TypeError(
        "unsupported log-like record for decoration projection: "
        f"{type(record).__module__}.{type(record).__qualname__}; "
        "add an explicit adapter before routing this record through the common "
        "log decoration pipeline"
    )


def exchange_log_to_decoration_record(
    log: ExchangeLog,
    *,
    record_id: str = "",
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project an exchange history log into the decoration pipeline shape."""

    source_record_id = record_id or _first_non_empty(
        _sequence_record_id("exchange_log", log.sequence),
        _joined_record_id("exchange_log", log.related_event_ids),
        _joined_record_id("exchange_log", log.related_artifact_ids),
        "exchange_log",
    )
    projected_fields: dict[str, object] = {
        "source_record_kind": "exchange_log",
        "clock": log.clock,
        "related_artifact_ids": list(log.related_artifact_ids),
        "related_event_ids": list(log.related_event_ids),
        "related_run_ids": list(log.related_run_ids),
    }
    if log.sequence is not None:
        projected_fields["sequence"] = log.sequence
    projected_fields.update(dict(fields or {}))
    return LogDecorationRecord(
        record_id=source_record_id,
        timestamp=log.timestamp,
        actor=log.actor,
        action=log.action,
        channel=log.channel or "exchange-log",
        message=log.summary,
        fields=projected_fields,
        decorations={"source_record_kind": "exchange_log"},
    )


def coordination_event_to_decoration_record(
    event: CoordinationEvent,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a coordination event into the decoration pipeline shape."""

    projected_fields: dict[str, object] = {
        "source_record_kind": "coordination_event",
        "event_id": event.event_id,
        "event_kind": event.event_kind,
        "artifact_id": event.artifact_id,
        "artifact_version": event.artifact_version,
        "related_artifact_ids": list(
            event.related_artifact_ids or ((event.artifact_id,) if event.artifact_id else ())
        ),
        "related_event_ids": list(event.related_event_ids or (event.event_id,)),
        "related_run_ids": list(event.related_run_ids),
    }
    if event.sequence is not None:
        projected_fields["sequence"] = event.sequence
    projected_fields.update(dict(fields or {}))
    return LogDecorationRecord(
        record_id=event.event_id,
        timestamp=event.timestamp,
        actor=event.actor,
        action=event.event_kind,
        channel="coordination-event-log",
        message=event.summary,
        fields=projected_fields,
        decorations={"source_record_kind": "coordination_event"},
    )


def scheduler_event_to_decoration_record(
    event: SchedulerEvent,
    *,
    actor: str = "scheduler",
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a scheduler event into the decoration pipeline shape."""

    projected_fields: dict[str, object] = {
        "source_record_kind": "scheduler_event",
        "event_id": event.event_id,
        "event_kind": event.event_kind,
        "task_id": event.task_id,
        "from_state": event.from_state,
        "to_state": event.to_state,
        "run_id": event.run_id,
        "session_id": event.session_id,
        "output_artifact_id": event.output_artifact_id,
        "output_artifact_version": event.output_artifact_version,
        "related_dependency_ids": list(event.related_dependency_ids),
        "related_artifact_ids": list(event.related_artifact_ids),
        "lease_id": event.lease_id,
        "metadata_keys": sorted(str(key) for key in event.metadata.keys()),
    }
    if event.sequence is not None:
        projected_fields["sequence"] = event.sequence
    projected_fields.update(dict(fields or {}))
    return LogDecorationRecord(
        record_id=event.event_id,
        timestamp=event.timestamp,
        actor=actor,
        action=event.event_kind,
        channel="scheduler-event-log",
        message=event.reason,
        fields=projected_fields,
        decorations={"source_record_kind": "scheduler_event"},
    )


def scheduler_merge_gate_event_to_decoration_record(
    event: SchedulerMergeGateEvent,
    *,
    actor: str = "scheduler",
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a scheduler merge-gate event into the decoration pipeline shape."""

    projected_fields: dict[str, object] = {
        "source_record_kind": "scheduler_merge_gate_event",
        "event_id": event.event_id,
        "event_kind": event.event_kind,
        "gate_id": event.gate_id,
        "target_task_id": event.target_task_id,
        "from_state": event.from_state,
        "to_state": event.to_state,
        "decision_artifact_id": event.decision_artifact_id,
        "decision_artifact_version": event.decision_artifact_version,
        "related_dependency_ids": list(event.related_dependency_ids),
        "related_task_ids": list(event.related_task_ids),
    }
    if event.sequence is not None:
        projected_fields["sequence"] = event.sequence
    projected_fields.update(dict(fields or {}))
    return LogDecorationRecord(
        record_id=event.event_id,
        timestamp=event.timestamp,
        actor=actor,
        action=event.event_kind,
        channel="scheduler-merge-gate-event-log",
        message=event.reason,
        fields=projected_fields,
        decorations={"source_record_kind": "scheduler_merge_gate_event"},
    )


def runtime_invocation_record_to_decoration_record(
    record: RuntimeInvocationRecord,
    *,
    actor: str = "runtime-invocation-wrapper",
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a runtime invocation audit record into the decoration pipeline shape."""

    projected_fields: dict[str, object] = {
        "source_record_kind": "runtime_invocation_record",
        "invocation_id": record.invocation_id,
        "provider": record.provider,
        "status": record.status,
        "task_id": record.task_id,
        "session_id": record.session_id,
        "run_id": record.run_id,
        "agent_id": record.agent_id,
        "runtime_surface": record.runtime_surface,
        "attempt_count": record.attempt_count,
        "max_attempts": record.retry_policy.max_attempts,
        "final_error_kind": record.final_error_kind,
        "metadata_keys": sorted(str(key) for key in record.metadata.keys()),
    }
    projected_fields.update(dict(fields or {}))
    return LogDecorationRecord(
        record_id=record.invocation_id,
        timestamp=record.ended_at or record.started_at,
        actor=record.agent_id or actor,
        action=f"runtime_invocation_{record.status}",
        channel="runtime-invocation-log",
        message=record.final_summary,
        fields=projected_fields,
        decorations={"source_record_kind": "runtime_invocation_record"},
    )


def agent_activation_event_to_decoration_record(
    event: AgentActivationEvent,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a leader/worker activation clue into the decoration pipeline."""

    return LogDecorationRecord(
        record_id=event.event_id,
        timestamp="",
        actor=event.agent_id,
        action=event.event_kind,
        channel="leader-worker-activation-read-model",
        message=event.reason,
        fields={
            "source_record_kind": "agent_activation_event",
            "event_id": event.event_id,
            "event_kind": event.event_kind,
            "agent_id": event.agent_id,
            "role": event.role,
            "lane_id": event.lane_id,
            "task_id": event.task_id,
            "source": event.source,
            "next_action": event.next_action,
            **dict(fields or {}),
        },
        decorations={"source_record_kind": "agent_activation_event"},
    )


def leader_worker_dispatcher_tick_record_to_decoration_record(
    record: LeaderWorkerDispatcherTickRecord,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a leader/worker dispatcher tick record into the log pipeline."""

    return LogDecorationRecord(
        record_id=record.tick_id,
        timestamp=record.timestamp,
        actor=record.dispatcher_id,
        action="leader_worker_dispatcher_tick",
        channel="leader-worker-dispatcher-event-log",
        message=(
            f"{record.decision_count} decision(s), "
            f"{record.activation_event_count} activation event(s)"
        ),
        fields={
            "source_record_kind": "leader_worker_dispatcher_tick_record",
            "tick_id": record.tick_id,
            "dispatcher_id": record.dispatcher_id,
            "scheduler_snapshot_path": record.scheduler_snapshot_path,
            "scheduler_event_log_path": record.scheduler_event_log_path,
            "artifact_store_path": record.artifact_store_path,
            "recovery_event_count": record.recovery_event_count,
            "exchange_record_count": record.exchange_record_count,
            "decision_count": record.decision_count,
            "suppressed_decision_count": record.suppressed_decision_count,
            "activation_event_count": record.activation_event_count,
            "lifecycle_count": record.lifecycle_count,
            "decision_ids": [decision.decision_id for decision in record.decisions],
            "policy_keys": sorted(str(key) for key in record.policy.keys()),
            "metadata_keys": sorted(str(key) for key in record.metadata.keys()),
            **dict(fields or {}),
        },
        decorations={"source_record_kind": "leader_worker_dispatcher_tick_record"},
    )


def run_event_to_decoration_record(
    event: RunEvent,
    *,
    actor: str = "runtime",
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a normalized runtime run event into the log pipeline."""

    return LogDecorationRecord(
        record_id=event.event_id,
        timestamp=event.timestamp,
        actor=actor,
        action=event.event_kind,
        channel="runtime-run-event",
        message=event.summary,
        fields={
            "source_record_kind": "run_event",
            "event_id": event.event_id,
            "event_kind": event.event_kind,
            "run_id": event.run_id,
            "task_id": event.task_id,
            "artifact_id": event.artifact_id,
            "artifact_version": event.artifact_version,
            **dict(fields or {}),
        },
        decorations={"source_record_kind": "run_event"},
    )


def exchange_artifact_admission_record_to_decoration_record(
    record: ExchangeArtifactAdmissionRecord,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project an exchange artifact admission ledger record into the log pipeline."""

    binding_summary = record.binding_reference_summary or {}
    return LogDecorationRecord(
        record_id=record.ledger_id,
        timestamp=record.timestamp,
        actor=record.actor,
        action=f"exchange_artifact_admission_{record.status}",
        channel="exchange-artifact-admission-ledger",
        message=record.error_summary,
        fields={
            "source_record_kind": "exchange_artifact_admission_record",
            "ledger_id": record.ledger_id,
            "artifact_id": record.artifact_id,
            "artifact_version": record.artifact_version,
            "product_type": record.product_type,
            "surface": record.surface,
            "status": record.status,
            "submitted_task_ids": list(record.submitted_task_ids),
            "dependency_ids": list(record.dependency_ids),
            "submission_event_ids": list(record.submission_event_ids),
            "duplicate_of": record.duplicate_of,
            "allow_duplicate": record.allow_duplicate,
            "binding_reference_summary_keys": sorted(
                str(key) for key in binding_summary.keys()
            ),
            **dict(fields or {}),
        },
        decorations={"source_record_kind": "exchange_artifact_admission_record"},
    )


def audit_event_to_decoration_record(
    event: object,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a legacy AuditEvent-like record into the decoration pipeline shape.

    The audit package predates the runtime orchestration package, so this
    adapter accepts an AuditEvent-like object instead of importing the legacy
    package from the runtime namespace.
    """

    event_id = _string_attr(event, "event_id")
    event_type = _string_attr(event, "event_type")
    phase = _string_attr(event, "phase")
    detail = _mapping_attr(event, "detail")
    projected_fields: dict[str, object] = {
        "source_record_kind": "audit_event",
        "event_id": event_id,
        "trace_id": _string_attr(event, "trace_id"),
        "event_type": event_type,
        "phase": phase,
        "parent_trace_id": _string_attr(event, "parent_trace_id"),
        "detail_keys": sorted(str(key) for key in detail.keys()),
    }
    projected_fields.update(dict(fields or {}))
    return LogDecorationRecord(
        record_id=event_id,
        timestamp=_string_attr(event, "timestamp"),
        actor=f"audit:{phase}" if phase else "audit",
        action=event_type,
        channel="legacy-audit-log",
        message=_bounded_audit_summary(detail),
        fields=projected_fields,
        decorations={"source_record_kind": "audit_event"},
    )


def decision_log_entry_to_decoration_record(
    entry: object,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a legacy DecisionLogEntry-like object into the log pipeline."""

    log_id = _string_attr(entry, "log_id")
    pack_names = tuple(str(item) for item in _sequence_attr(entry, "pack_names"))
    pack_versions = tuple(str(item) for item in _sequence_attr(entry, "pack_versions"))
    merge_conflicts = tuple(_sequence_attr(entry, "merge_conflicts"))
    return LogDecorationRecord(
        record_id=log_id,
        timestamp=_string_attr(entry, "timestamp"),
        actor="decision-log",
        action=f"decision_{_string_attr(entry, 'decision').lower()}",
        channel="legacy-decision-log",
        message=_string_attr(entry, "input_summary"),
        fields={
            "source_record_kind": "decision_log_entry",
            "log_id": log_id,
            "decision_id": _string_attr(entry, "decision_id"),
            "trace_id": _string_attr(entry, "trace_id"),
            "scope_path": _string_attr(entry, "scope_path"),
            "decision": _string_attr(entry, "decision"),
            "intent": _string_attr(entry, "intent"),
            "gate": _string_attr(entry, "gate"),
            "constraint_violated": list(
                str(item) for item in _sequence_attr(entry, "constraint_violated")
            ),
            "winning_rule": _string_attr(entry, "winning_rule"),
            "adoption_layer": _string_attr(entry, "adoption_layer"),
            "resolution_strategy": _string_attr(entry, "resolution_strategy"),
            "explicit_override": bool(getattr(entry, "explicit_override", False)),
            "pack_names": list(pack_names),
            "pack_versions": list(pack_versions),
            "pep_action_count": int(getattr(entry, "pep_action_count", 0) or 0),
            "final_state": _string_attr(entry, "final_state"),
            "audit_event_count": int(getattr(entry, "audit_event_count", 0) or 0),
            "merge_conflict_count": len(merge_conflicts),
            **dict(fields or {}),
        },
        decorations={"source_record_kind": "decision_log_entry"},
    )


def continuous_worker_binding_event_to_decoration_record(
    event: ContinuousWorkerBindingEventRecord,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a continuous worker binding lifecycle event into the log pipeline."""

    return _lifecycle_event_record(
        source_record_kind="continuous_worker_binding_event",
        record_id=event.event_id,
        timestamp=event.timestamp,
        actor=event.worker_id or event.binding_id or "continuous-worker-binding",
        action=event.event_kind,
        channel="continuous-worker-binding-event-log",
        message=event.reason,
        metadata=event.metadata,
        fields={
            "event_id": event.event_id,
            "event_kind": event.event_kind,
            "binding_id": event.binding_id,
            "worker_id": event.worker_id,
            "runtime_provider": event.runtime_provider,
            "scope_kind": event.scope_kind,
            "scope_id": event.scope_id,
            "previous_status": event.previous_status,
            "next_status": event.next_status,
            **dict(fields or {}),
        },
    )


def lane_ownership_event_to_decoration_record(
    event: LaneOwnershipEventRecord,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a lane ownership lifecycle event into the log pipeline."""

    return _lifecycle_event_record(
        source_record_kind="lane_ownership_event",
        record_id=event.event_id,
        timestamp=event.timestamp,
        actor=event.binding_id or event.ownership_id or "lane-ownership",
        action=event.event_kind,
        channel="lane-ownership-event-log",
        message=event.reason,
        metadata=event.metadata,
        fields={
            "event_id": event.event_id,
            "event_kind": event.event_kind,
            "ownership_id": event.ownership_id,
            "scope_kind": event.scope_kind,
            "scope_id": event.scope_id,
            "binding_id": event.binding_id,
            "previous_status": event.previous_status,
            "next_status": event.next_status,
            **dict(fields or {}),
        },
    )


def delivery_lease_event_to_decoration_record(
    event: DeliveryLeaseEventRecord,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a delivery lease lifecycle event into the log pipeline."""

    return _lifecycle_event_record(
        source_record_kind="delivery_lease_event",
        record_id=event.event_id,
        timestamp=event.timestamp,
        actor=event.binding_id or event.lease_id or "delivery-lease",
        action=event.event_kind,
        channel="delivery-lease-event-log",
        message=event.reason,
        metadata=event.metadata,
        fields={
            "event_id": event.event_id,
            "event_kind": event.event_kind,
            "lease_id": event.lease_id,
            "binding_id": event.binding_id,
            "task_id": event.task_id,
            "delivery_id": event.delivery_id,
            "previous_status": event.previous_status,
            "next_status": event.next_status,
            **dict(fields or {}),
        },
    )


def leader_worker_delivery_event_to_decoration_record(
    event: LeaderWorkerDeliveryEventRecord,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a leader/worker delivery event into the log pipeline."""

    return _lifecycle_event_record(
        source_record_kind="leader_worker_delivery_event",
        record_id=event.event_id,
        timestamp=event.timestamp,
        actor=event.agent_id or event.delivery_id or "leader-worker-delivery",
        action=event.event_kind,
        channel="leader-worker-delivery-event-log",
        message=event.failure_detail or event.failure_kind,
        metadata=event.metadata,
        fields={
            "event_id": event.event_id,
            "event_kind": event.event_kind,
            "delivery_id": event.delivery_id,
            "source_key": event.source_key,
            "decision_id": event.decision_id,
            "tick_id": event.tick_id,
            "dispatcher_id": event.dispatcher_id,
            "agent_id": event.agent_id,
            "role": event.role,
            "previous_state": event.previous_state,
            "next_state": event.next_state,
            "changed": event.changed,
            "runtime_provider": event.runtime_provider,
            "runtime_session_id": event.runtime_session_id,
            "runtime_run_id": event.runtime_run_id,
            "invocation_id": event.invocation_id,
            "failure_kind": event.failure_kind,
            **dict(fields or {}),
        },
    )


def trajectory_team_continuity_event_to_decoration_record(
    event: TrajectoryTeamContinuityEventRecord,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a trajectory team continuity event into the log pipeline."""

    return _lifecycle_event_record(
        source_record_kind="trajectory_team_continuity_event",
        record_id=event.event_id,
        timestamp=event.timestamp,
        actor=event.worker_id or event.leader_id or event.trajectory_id or "trajectory-team",
        action=event.event_kind,
        channel="trajectory-team-continuity-event-log",
        message=event.reason,
        metadata=event.metadata,
        fields={
            "event_id": event.event_id,
            "event_kind": event.event_kind,
            "trajectory_id": event.trajectory_id,
            "lane_id": event.lane_id,
            "worker_id": event.worker_id,
            "leader_id": event.leader_id,
            "binding_id": event.binding_id,
            "ownership_id": event.ownership_id,
            "action": event.action,
            "previous_binding_id": event.previous_binding_id,
            "replacement_binding_id": event.replacement_binding_id,
            "task_id": event.task_id,
            "delivery_id": event.delivery_id,
            "no_continuity_reason": event.no_continuity_reason,
            **dict(fields or {}),
        },
    )


def opencode_serve_lifecycle_receipt_to_decoration_record(
    receipt: OpenCodeServeLifecycleReceipt,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project an OpenCode serve lifecycle receipt into the log pipeline."""

    return LogDecorationRecord(
        record_id=receipt.receipt_id,
        timestamp=receipt.timestamp,
        actor=receipt.actor or "opencode-serve-lifecycle",
        action=f"opencode_serve_{receipt.action}_{receipt.status}",
        channel="opencode-serve-lifecycle-ledger",
        message=_bounded_text(receipt.reason or receipt.note),
        fields={
            "source_record_kind": "opencode_serve_lifecycle_receipt",
            "receipt_id": receipt.receipt_id,
            "serve_action": receipt.action,
            "status": receipt.status,
            "hostname": receipt.hostname,
            "port": receipt.port,
            "executable": _basename_str(receipt.executable),
            "attach_url_present": bool(receipt.attach_url),
            "command_preview_count": len(receipt.command_preview),
            "pid_present": bool(receipt.pid),
            "process_ref_present": bool(receipt.process_ref),
            "note_present": bool(receipt.note),
            "metadata_keys": sorted(str(key) for key in receipt.metadata.keys()),
            **dict(fields or {}),
        },
        decorations={"source_record_kind": "opencode_serve_lifecycle_receipt"},
    )


def cleanup_receipt_to_decoration_record(
    receipt: CleanupReceipt,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project an agent scratch cleanup receipt into the log pipeline."""

    return LogDecorationRecord(
        record_id=receipt.receipt_id,
        timestamp=receipt.cleaned_at,
        actor=receipt.reviewed_by or receipt.agent_id or "agent-storage-governance",
        action="agent_scratch_cleanup_recorded",
        channel="agent-storage-governance",
        message=_bounded_text(receipt.summary),
        fields={
            "source_record_kind": "cleanup_receipt",
            "receipt_id": receipt.receipt_id,
            "scratch_id": receipt.scratch_id,
            "agent_id": receipt.agent_id,
            "reviewed_by": receipt.reviewed_by,
            "archived_path_count": len(receipt.archived_paths),
            "promoted_path_count": len(receipt.promoted_paths),
            "deleted_path_count": len(receipt.deleted_paths),
            "retained_path_count": len(receipt.retained_paths),
            **dict(fields or {}),
        },
        decorations={"source_record_kind": "cleanup_receipt"},
    )


def git_worktree_command_receipt_to_decoration_record(
    receipt: GitWorktreeCommandReceipt,
    *,
    record_id: str = "",
    command_role: str = "git_worktree_command",
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a git-worktree command receipt without copying stdout/stderr."""

    status = _command_receipt_status(receipt)
    command_head = _basename_str(receipt.command[0]) if receipt.command else ""
    return LogDecorationRecord(
        record_id=record_id or _git_command_receipt_id(command_role, receipt),
        timestamp="",
        actor="git-worktree-sandbox",
        action=f"{command_role}_{status}",
        channel="git-worktree-command-receipt",
        message=f"{command_role} {status}",
        fields={
            "source_record_kind": "git_worktree_command_receipt",
            "command_role": command_role,
            "command_head": command_head,
            "command_arg_count": len(receipt.command),
            "returncode": receipt.returncode,
            "stdout_present": bool(receipt.stdout),
            "stderr_present": bool(receipt.stderr),
            "stdout_char_count": len(receipt.stdout),
            "stderr_char_count": len(receipt.stderr),
            **dict(fields or {}),
        },
        decorations={"source_record_kind": "git_worktree_command_receipt"},
    )


def git_worktree_sandbox_receipt_to_decoration_record(
    receipt: GitWorktreeSandboxReceipt,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a git-worktree sandbox receipt into the log pipeline."""

    return LogDecorationRecord(
        record_id=_git_worktree_sandbox_receipt_id(receipt),
        timestamp="",
        actor="git-worktree-sandbox",
        action=f"git_worktree_sandbox_{receipt.cleanup_state}",
        channel="git-worktree-sandbox-receipt",
        message=f"git-worktree sandbox cleanup_state={receipt.cleanup_state}",
        fields={
            "source_record_kind": "git_worktree_sandbox_receipt",
            "source_repository_root_present": bool(receipt.source_repository_root),
            "sandbox_root_present": bool(receipt.sandbox_root),
            "worktree_path_present": bool(receipt.worktree_path),
            "branch_name": receipt.branch_name,
            "base_ref": receipt.base_ref,
            "authorized_writable_path_count": len(receipt.authorized_writable_paths),
            "denied_writable_path_count": len(receipt.denied_writable_paths),
            "cleanup_state": receipt.cleanup_state,
            "allocation_returncode": receipt.allocation.returncode,
            "cleanup_returncode": receipt.cleanup.returncode,
            "branch_cleanup_returncode": receipt.branch_cleanup.returncode,
            "allocation_stderr_present": bool(receipt.allocation.stderr),
            "cleanup_stderr_present": bool(receipt.cleanup.stderr),
            "branch_cleanup_stderr_present": bool(receipt.branch_cleanup.stderr),
            **dict(fields or {}),
        },
        decorations={"source_record_kind": "git_worktree_sandbox_receipt"},
    )


def sandbox_allocation_to_decoration_record(
    allocation: SandboxAllocation,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a sandbox allocation receipt without copying paths or reasons."""

    return LogDecorationRecord(
        record_id=allocation.allocation_id,
        timestamp="",
        actor=allocation.provider,
        action=f"sandbox_allocation_{allocation.state}",
        channel="sandbox-allocation-receipt",
        message=f"sandbox allocation {allocation.state}",
        fields={
            "source_record_kind": "sandbox_allocation",
            "allocation_id": allocation.allocation_id,
            "provider": allocation.provider,
            "task_id": allocation.task_id,
            "profile_id": allocation.profile.profile_id,
            "profile_kind": allocation.profile.profile_kind,
            "state": allocation.state,
            "workspace_root_present": bool(allocation.workspace_root),
            "scratch_path_present": bool(allocation.scratch_path),
            "visible_mount_count": len(allocation.visible_mounts),
            "network_policy": allocation.network_policy,
            "secret_policy": allocation.secret_policy,
            "cleanup_required": allocation.cleanup_required,
            "lease_authorization_state": allocation.lease_authorization_state,
            "lease_authorization_count": len(allocation.lease_authorized_mounts),
            "lease_authorization_reason_present": bool(
                allocation.lease_authorization_reason
            ),
            "git_worktree_receipt_present": allocation.git_worktree_receipt is not None,
            "reason_present": bool(allocation.reason),
            **dict(fields or {}),
        },
        decorations={"source_record_kind": "sandbox_allocation"},
    )


def sandbox_allocation_receipt_evidence_to_decoration_record(
    evidence: SandboxAllocationReceiptEvidence,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project sandbox allocation receipt evidence into the log pipeline."""

    return LogDecorationRecord(
        record_id=evidence.evidence_id,
        timestamp=evidence.timestamp,
        actor="sandbox-allocation-evidence",
        action="sandbox_allocation_receipt_evidence_recorded",
        channel="sandbox-allocation-receipt-evidence",
        message=f"{len(evidence.allocations)} sandbox allocation receipt(s)",
        fields={
            "source_record_kind": "sandbox_allocation_receipt_evidence",
            "evidence_id": evidence.evidence_id,
            "product_type": evidence.product_type,
            "schema_version": evidence.schema_version,
            "allocation_count": len(evidence.allocations),
            "evidence_path_present": evidence.evidence_path is not None,
            "metadata_keys": sorted(str(key) for key in evidence.metadata.keys()),
            "authority_split_keys": sorted(
                str(key) for key in evidence.authority_split.keys()
            ),
            **dict(fields or {}),
        },
        decorations={"source_record_kind": "sandbox_allocation_receipt_evidence"},
    )


def sandbox_allocation_receipt_evidence_summary_to_decoration_record(
    summary: SandboxAllocationReceiptEvidenceSummary,
    *,
    fields: Mapping[str, object] | None = None,
) -> LogDecorationRecord:
    """Project a compact sandbox allocation evidence summary into the pipeline."""

    return LogDecorationRecord(
        record_id=summary.evidence_id,
        timestamp=summary.timestamp,
        actor="sandbox-allocation-evidence",
        action="sandbox_allocation_receipt_evidence_inspected",
        channel="sandbox-allocation-receipt-evidence-summary",
        message=f"{summary.allocation_count} sandbox allocation receipt(s)",
        fields={
            "source_record_kind": "sandbox_allocation_receipt_evidence_summary",
            "evidence_id": summary.evidence_id,
            "product_type": summary.product_type,
            "schema_version": summary.schema_version,
            "allocation_count": summary.allocation_count,
            "evidence_path_present": bool(summary.evidence_path),
            "metadata_keys": sorted(str(key) for key in summary.metadata.keys()),
            "authority_split_keys": sorted(
                str(key) for key in summary.authority_split.keys()
            ),
            **dict(fields or {}),
        },
        decorations={
            "source_record_kind": "sandbox_allocation_receipt_evidence_summary",
        },
    )


def _sequence_record_id(prefix: str, sequence: int | None) -> str:
    return f"{prefix}:{sequence}" if sequence is not None else ""


def _joined_record_id(prefix: str, values: tuple[str, ...]) -> str:
    cleaned = tuple(value for value in values if value)
    return f"{prefix}:{'+'.join(cleaned)}" if cleaned else ""


def _first_non_empty(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def _string_attr(value: object, name: str) -> str:
    raw = getattr(value, name, "")
    return "" if raw is None else str(raw)


def _mapping_attr(value: object, name: str) -> Mapping[str, object]:
    raw = getattr(value, name, {})
    return raw if isinstance(raw, Mapping) else {}


def _sequence_attr(value: object, name: str) -> tuple[object, ...]:
    raw = getattr(value, name, ())
    if raw is None or isinstance(raw, (str, bytes)):
        return ()
    try:
        return tuple(raw)
    except TypeError:
        return ()


def _iter_records(records: object) -> tuple[object, ...]:
    if records is None:
        return ()
    if isinstance(records, (str, bytes, Mapping)):
        return (records,)
    try:
        return tuple(records)  # type: ignore[arg-type]
    except TypeError:
        return (records,)


def _bounded_audit_summary(detail: Mapping[str, object], *, limit: int = 240) -> str:
    if not detail:
        return ""
    summary = detail.get("summary") or detail.get("message") or detail.get("reason") or ""
    if not summary:
        return f"audit detail keys: {', '.join(str(key) for key in sorted(detail.keys()))}"
    text = str(summary).replace("\r\n", "\n").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _bounded_text(value: str, *, limit: int = 240) -> str:
    text = str(value or "").replace("\r\n", "\n").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _basename_str(value: str) -> str:
    text = str(value or "").replace("\\", "/").rstrip("/")
    return text.rsplit("/", 1)[-1] if text else ""


def _command_receipt_status(receipt: GitWorktreeCommandReceipt) -> str:
    if receipt.returncode is None:
        return "not_run"
    return "succeeded" if receipt.returncode == 0 else "failed"


def _git_command_receipt_id(
    command_role: str,
    receipt: GitWorktreeCommandReceipt,
) -> str:
    if not receipt.command and receipt.returncode is None:
        return f"{command_role}:not-run"
    raw = "\0".join(str(part) for part in receipt.command)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{command_role}:{_command_receipt_status(receipt)}:{digest}"


def _git_worktree_sandbox_receipt_id(receipt: GitWorktreeSandboxReceipt) -> str:
    raw = "\0".join(
        (
            receipt.source_repository_root,
            receipt.sandbox_root,
            receipt.worktree_path,
            receipt.branch_name,
            receipt.base_ref,
        )
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"git-worktree-sandbox:{digest}"


def _lifecycle_event_record(
    *,
    source_record_kind: str,
    record_id: str,
    timestamp: str,
    actor: str,
    action: str,
    channel: str,
    message: str,
    metadata: Mapping[str, object],
    fields: Mapping[str, object],
) -> LogDecorationRecord:
    projected_fields = {
        "source_record_kind": source_record_kind,
        "metadata_keys": sorted(str(key) for key in metadata.keys()),
        **dict(fields),
    }
    return LogDecorationRecord(
        record_id=record_id,
        timestamp=timestamp,
        actor=actor,
        action=action,
        channel=channel,
        message=message,
        fields=projected_fields,
        decorations={"source_record_kind": source_record_kind},
    )


__all__ = [
    "agent_activation_event_to_decoration_record",
    "audit_event_to_decoration_record",
    "cleanup_receipt_to_decoration_record",
    "coordination_event_to_decoration_record",
    "continuous_worker_binding_event_to_decoration_record",
    "decorate_log_like_records",
    "decision_log_entry_to_decoration_record",
    "delivery_lease_event_to_decoration_record",
    "exchange_artifact_admission_record_to_decoration_record",
    "exchange_log_to_decoration_record",
    "git_worktree_command_receipt_to_decoration_record",
    "git_worktree_sandbox_receipt_to_decoration_record",
    "lane_ownership_event_to_decoration_record",
    "leader_worker_dispatcher_tick_record_to_decoration_record",
    "leader_worker_delivery_event_to_decoration_record",
    "LogLikeRecordBatchDecorationResult",
    "log_like_record_to_decoration_record",
    "opencode_serve_lifecycle_receipt_to_decoration_record",
    "runtime_invocation_record_to_decoration_record",
    "run_event_to_decoration_record",
    "sandbox_allocation_receipt_evidence_summary_to_decoration_record",
    "sandbox_allocation_receipt_evidence_to_decoration_record",
    "sandbox_allocation_to_decoration_record",
    "scheduler_event_to_decoration_record",
    "scheduler_merge_gate_event_to_decoration_record",
    "trajectory_team_continuity_event_to_decoration_record",
]
