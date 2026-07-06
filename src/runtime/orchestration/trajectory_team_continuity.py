"""Trajectory-scoped leader/worker team continuity bridge.

This module keeps the trajectory-team concept thin: it records the roster and
delegates durable worker/session continuity to the existing continuous worker
binding, lane ownership, and delivery lease ledgers.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .artifact_paths import dbc_artifact_path
from .continuous_worker_binding import (
    DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH,
    DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH,
    DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH,
    DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH,
    ContinuousWorkerBinding,
    ContinuousWorkerBindingClaimRequest,
    ContinuousWorkerBindingForkRequest,
    ContinuousWorkerBindingInspectRequest,
    ContinuousWorkerBindingResult,
    ContinuousWorkerSessionSelector,
    LaneOwnership,
    LaneOwnershipActivateRequest,
    LaneOwnershipClaimRequest,
    LaneOwnershipInspectRequest,
    LaneOwnershipReleaseRequest,
    LaneOwnershipResumeRequest,
    LaneOwnershipSuspendRequest,
    LaneOwnershipResult,
    LaneOwnershipTransferRequest,
    activate_lane_ownership,
    claim_continuous_worker_binding,
    claim_lane_ownership,
    fork_continuous_worker_binding,
    inspect_continuous_worker_bindings,
    inspect_lane_ownerships,
    release_lane_ownership,
    resume_lane_ownership,
    suspend_lane_ownership,
    transfer_lane_ownership,
)
from .runtime_adapter import RuntimeProviderKind
from .scheduler import SchedulerEvent
from .scheduler_store import JsonlSchedulerEventLog


TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_SCHEMA_VERSION = (
    "trajectory-team-continuity-log.v1"
)
DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH = (
    dbc_artifact_path("runtime", "trajectory-team-continuity-events.jsonl")
)

TrajectoryTeamContinuityAction = Literal[
    "assign_lane_worker",
    "resolve_lane_worker",
    "activate_lane_worker",
    "suspend_lane_worker",
    "resume_lane_worker",
    "transfer_lane_worker",
    "fork_lane_worker",
    "release_lane_worker",
    "record_no_continuity",
]
TrajectoryTeamContinuityEventKind = Literal[
    "trajectory_team_lane_worker_assigned",
    "trajectory_team_lane_worker_resolved",
    "trajectory_team_lane_worker_activated",
    "trajectory_team_lane_worker_suspended",
    "trajectory_team_lane_worker_resumed",
    "trajectory_team_lane_worker_transferred",
    "trajectory_team_lane_worker_forked",
    "trajectory_team_lane_worker_released",
    "trajectory_team_no_continuity_recorded",
]
NoContinuityReason = Literal[
    "no_lane_assignment",
    "binding_not_found",
    "ownership_not_found",
    "ownership_not_selectable",
    "binding_not_selectable",
    "runtime_provider_mismatch",
    "explicit_no_continuity",
]


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuityEventRecord:
    """Append-only audit event for trajectory team roster changes."""

    event_id: str
    event_kind: TrajectoryTeamContinuityEventKind
    timestamp: str
    trajectory_id: str
    lane_id: str
    worker_id: str = ""
    leader_id: str = ""
    binding_id: str = ""
    ownership_id: str = ""
    action: str = ""
    reason: str = ""
    previous_binding_id: str = ""
    replacement_binding_id: str = ""
    task_id: str = ""
    delivery_id: str = ""
    no_continuity_reason: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_no_raw_or_secret_fields(
            "trajectory team continuity event",
            self.event_id,
            self.metadata,
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_SCHEMA_VERSION,
            "event_id": self.event_id,
            "event_kind": self.event_kind,
            "timestamp": self.timestamp,
            "trajectory_id": self.trajectory_id,
            "lane_id": self.lane_id,
            "worker_id": self.worker_id,
            "leader_id": self.leader_id,
            "binding_id": self.binding_id,
            "ownership_id": self.ownership_id,
            "action": self.action,
            "reason": self.reason,
            "previous_binding_id": self.previous_binding_id,
            "replacement_binding_id": self.replacement_binding_id,
            "task_id": self.task_id,
            "delivery_id": self.delivery_id,
            "no_continuity_reason": self.no_continuity_reason,
            "metadata": dict(self.metadata),
            "authority_split": {
                "trajectory_team_continuity_event_log_mutated": True,
                "continuous_worker_binding_ledger_mutated": False,
                "continuous_worker_lane_ownership_ledger_mutated": False,
                "delivery_state_mutated": False,
                "scheduler_state_mutated": False,
                "provider_executed": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_persisted": False,
                "secret_value_persisted": False,
            },
        }


@dataclass(frozen=True, slots=True)
class TrajectoryLaneWorkerAssignment:
    """Resolved roster row for one trajectory lane worker."""

    trajectory_id: str
    lane_id: str
    leader_id: str = ""
    worker_id: str = ""
    runtime_provider: RuntimeProviderKind | str = ""
    binding: ContinuousWorkerBinding | None = None
    ownership: LaneOwnership | None = None
    continuity_status: str = "unassigned"
    no_continuity_reason: str = ""

    @property
    def binding_id(self) -> str:
        return "" if self.binding is None else self.binding.binding_id

    @property
    def ownership_id(self) -> str:
        return "" if self.ownership is None else self.ownership.ownership_id

    def to_json_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "lane_id": self.lane_id,
            "leader_id": self.leader_id,
            "worker_id": self.worker_id,
            "runtime_provider": self.runtime_provider,
            "binding_id": self.binding_id,
            "ownership_id": self.ownership_id,
            "continuity_status": self.continuity_status,
            "no_continuity_reason": self.no_continuity_reason,
            "binding": None if self.binding is None else self.binding.to_json_dict(),
            "ownership": None if self.ownership is None else self.ownership.to_json_dict(),
        }


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuityAssignRequest:
    """Assign one trajectory lane to a continuous worker binding."""

    trajectory_id: str
    lane_id: str
    worker_id: str
    leader_id: str = "agent:guide"
    runtime_provider: RuntimeProviderKind = "opencode"
    binding_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    binding_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH
    ownership_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    ownership_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    team_event_log_path: str | Path = DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH
    scheduler_event_log_path: str | Path = ""
    binding_id: str = ""
    ownership_id: str = ""
    active_session_selector: ContinuousWorkerSessionSelector | None = None
    compact_context_ref: str = ""
    mailbox_cursor_ref: str = ""
    worker_report_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    timestamp: str = ""
    reason: str = "trajectory lane worker assigned"
    replace_existing_binding: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuityResolveRequest:
    """Resolve the continuity owner for one trajectory lane."""

    trajectory_id: str
    lane_id: str
    runtime_provider: RuntimeProviderKind | str = ""
    leader_id: str = ""
    binding_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    ownership_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    team_event_log_path: str | Path = DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH
    scheduler_event_log_path: str | Path = ""
    timestamp: str = ""
    reason: str = "trajectory lane worker resolved"
    record_event: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuityActivateRequest:
    """Activate a claimed trajectory lane ownership after first delivery."""

    trajectory_id: str
    lane_id: str
    binding_id: str = ""
    ownership_id: str = ""
    leader_id: str = "agent:guide"
    task_id: str = ""
    delivery_id: str = ""
    ownership_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    ownership_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    team_event_log_path: str | Path = DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH
    scheduler_event_log_path: str | Path = ""
    timestamp: str = ""
    reason: str = "trajectory lane worker activated"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuitySuspendRequest:
    """Suspend one trajectory lane ownership without releasing the worker."""

    trajectory_id: str
    lane_id: str
    leader_id: str = "agent:guide"
    binding_id: str = ""
    ownership_id: str = ""
    ownership_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    ownership_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    team_event_log_path: str | Path = DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH
    scheduler_event_log_path: str | Path = ""
    timestamp: str = ""
    reason: str = "trajectory lane worker suspended"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuityResumeRequest:
    """Resume one suspended trajectory lane ownership."""

    trajectory_id: str
    lane_id: str
    leader_id: str = "agent:guide"
    binding_id: str = ""
    ownership_id: str = ""
    ownership_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    ownership_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    team_event_log_path: str | Path = DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH
    scheduler_event_log_path: str | Path = ""
    timestamp: str = ""
    reason: str = "trajectory lane worker resumed"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuityTransferRequest:
    """Transfer one trajectory lane to a replacement worker binding."""

    trajectory_id: str
    lane_id: str
    replacement_binding_id: str
    worker_id: str
    leader_id: str = "agent:guide"
    binding_id: str = ""
    ownership_id: str = ""
    binding_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    ownership_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    ownership_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    team_event_log_path: str | Path = DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH
    scheduler_event_log_path: str | Path = ""
    timestamp: str = ""
    reason: str = "trajectory lane worker transferred"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuityForkRequest:
    """Fork one trajectory lane worker binding and transfer ownership to it."""

    trajectory_id: str
    lane_id: str
    new_binding_id: str
    worker_id: str
    leader_id: str = "agent:guide"
    source_binding_id: str = ""
    ownership_id: str = ""
    binding_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    binding_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH
    ownership_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    ownership_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    team_event_log_path: str | Path = DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH
    scheduler_event_log_path: str | Path = ""
    active_session_selector: ContinuousWorkerSessionSelector | None = None
    compact_context_ref: str = ""
    mailbox_cursor_ref: str = ""
    worker_report_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    timestamp: str = ""
    reason: str = "trajectory lane worker forked"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuityReleaseRequest:
    """Release one trajectory lane worker ownership."""

    trajectory_id: str
    lane_id: str
    leader_id: str = "agent:guide"
    binding_id: str = ""
    ownership_id: str = ""
    ownership_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    ownership_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    team_event_log_path: str | Path = DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH
    scheduler_event_log_path: str | Path = ""
    timestamp: str = ""
    reason: str = "trajectory lane worker released"
    audit_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuityNoContinuityRequest:
    """Record an explicit no-continuity decision for a trajectory lane."""

    trajectory_id: str
    lane_id: str
    no_continuity_reason: NoContinuityReason | str
    leader_id: str = "agent:guide"
    worker_id: str = ""
    binding_id: str = ""
    team_event_log_path: str | Path = DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH
    scheduler_event_log_path: str | Path = ""
    timestamp: str = ""
    reason: str = "trajectory lane has no continuous worker"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuityResult:
    """Result for trajectory team continuity bridge operations."""

    ok: bool
    action: TrajectoryTeamContinuityAction
    trajectory_id: str
    lane_id: str
    assignment: TrajectoryLaneWorkerAssignment | None = None
    binding_result: ContinuousWorkerBindingResult | None = None
    ownership_result: LaneOwnershipResult | None = None
    event_record: TrajectoryTeamContinuityEventRecord | None = None
    status: str = ""
    message: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "action": self.action,
            "status": self.status,
            "message": self.message,
            "trajectory_id": self.trajectory_id,
            "lane_id": self.lane_id,
            "assignment": (
                None if self.assignment is None else self.assignment.to_json_dict()
            ),
            "binding_result": (
                None if self.binding_result is None else self.binding_result.to_json_dict()
            ),
            "ownership_result": (
                None if self.ownership_result is None else self.ownership_result.to_json_dict()
            ),
            "event": (
                None if self.event_record is None else self.event_record.to_json_dict()
            ),
            "authority_split": {
                "trajectory_team_continuity_bridge": True,
                "continuous_worker_binding_ledger_mutated": (
                    False
                    if self.binding_result is None
                    else self.binding_result.ledger_mutated
                ),
                "continuous_worker_lane_ownership_ledger_mutated": (
                    False
                    if self.ownership_result is None
                    else self.ownership_result.ledger_mutated
                ),
                "trajectory_team_continuity_event_log_mutated": (
                    self.event_record is not None
                ),
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "delivery_state_mutated": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_persisted": False,
                "secret_value_persisted": False,
            },
        }


class JsonlTrajectoryTeamContinuityEventLog:
    """Append-only JSONL store for trajectory team continuity events."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(
        self,
        record: TrajectoryTeamContinuityEventRecord,
    ) -> TrajectoryTeamContinuityEventRecord:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record.to_json_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return record

    def read_all(self) -> tuple[TrajectoryTeamContinuityEventRecord, ...]:
        if not self.path.exists():
            return ()
        records: list[TrajectoryTeamContinuityEventRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(
                        trajectory_team_continuity_event_record_from_json_dict(
                            json.loads(stripped)
                        )
                    )
                except Exception as exc:
                    raise ValueError(
                        f"invalid trajectory team continuity event log line "
                        f"{line_number} in {self.path}: {exc}"
                    ) from exc
        return tuple(records)


def assign_trajectory_lane_worker(
    request: TrajectoryTeamContinuityAssignRequest,
) -> TrajectoryTeamContinuityResult:
    """Assign one trajectory lane to a continuous worker and claim ownership."""

    _require_common(request.trajectory_id, request.lane_id)
    if not request.worker_id:
        raise ValueError("trajectory team continuity assignment requires worker_id")
    _validate_runtime_provider(request.runtime_provider)
    _validate_no_raw_or_secret_fields(
        "trajectory team continuity assignment",
        request.trajectory_id,
        request.metadata,
    )
    binding = claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=request.binding_ledger_path,
            event_log_path=request.binding_event_log_path,
            worker_id=request.worker_id,
            runtime_provider=request.runtime_provider,
            scope_kind="lane",
            scope_id=request.lane_id,
            lane_ids=(request.lane_id,),
            binding_id=request.binding_id,
            active_session_selector=request.active_session_selector,
            compact_context_ref=request.compact_context_ref,
            mailbox_cursor_ref=request.mailbox_cursor_ref,
            worker_report_refs=_unique_nonempty(request.worker_report_refs),
            audit_refs=_unique_nonempty(request.audit_refs),
            timestamp=request.timestamp,
            reason=request.reason,
            replace_existing=request.replace_existing_binding,
            metadata={
                "trajectory_id": request.trajectory_id,
                "leader_id": request.leader_id,
                "team_continuity_action": "assign_lane_worker",
                **dict(request.metadata),
            },
        )
    )
    if not binding.ok or binding.binding is None:
        event = _append_team_event(
            request.team_event_log_path,
            "trajectory_team_no_continuity_recorded",
            scheduler_event_log_path=request.scheduler_event_log_path,
            timestamp=request.timestamp,
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            leader_id=request.leader_id,
            worker_id=request.worker_id,
            binding_id="" if binding.binding is None else binding.binding.binding_id,
            action="assign_lane_worker",
            reason=binding.message,
            no_continuity_reason="binding_not_selectable",
            metadata=request.metadata,
        )
        return TrajectoryTeamContinuityResult(
            ok=False,
            action="assign_lane_worker",
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            binding_result=binding,
            event_record=event,
            status=binding.status,
            message=binding.message,
        )

    ownership = claim_lane_ownership(
        LaneOwnershipClaimRequest(
            ledger_path=request.ownership_ledger_path,
            event_log_path=request.ownership_event_log_path,
            ownership_id=request.ownership_id,
            scope_kind="lane",
            scope_id=request.lane_id,
            lane_ids=(request.lane_id,),
            binding_id=binding.binding.binding_id,
            worker_id=request.worker_id,
            timestamp=request.timestamp,
            requested_by=request.leader_id,
            reason=request.reason,
            audit_refs=_unique_nonempty(request.audit_refs),
            metadata={
                "trajectory_id": request.trajectory_id,
                "leader_id": request.leader_id,
                "team_continuity_action": "assign_lane_worker",
                **dict(request.metadata),
            },
        )
    )
    if not ownership.ok or ownership.ownership is None:
        event = _append_team_event(
            request.team_event_log_path,
            "trajectory_team_no_continuity_recorded",
            scheduler_event_log_path=request.scheduler_event_log_path,
            timestamp=request.timestamp,
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            leader_id=request.leader_id,
            worker_id=request.worker_id,
            binding_id=binding.binding.binding_id,
            action="assign_lane_worker",
            reason=ownership.message,
            no_continuity_reason="ownership_not_selectable",
            metadata=request.metadata,
        )
        return TrajectoryTeamContinuityResult(
            ok=False,
            action="assign_lane_worker",
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            binding_result=binding,
            ownership_result=ownership,
            event_record=event,
            status=ownership.status,
            message=ownership.message,
        )

    assignment = TrajectoryLaneWorkerAssignment(
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        leader_id=request.leader_id,
        worker_id=request.worker_id,
        runtime_provider=request.runtime_provider,
        binding=binding.binding,
        ownership=ownership.ownership,
        continuity_status="claimed",
    )
    event = _append_team_event(
        request.team_event_log_path,
        "trajectory_team_lane_worker_assigned",
        scheduler_event_log_path=request.scheduler_event_log_path,
        timestamp=request.timestamp,
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        leader_id=request.leader_id,
        worker_id=request.worker_id,
        binding_id=binding.binding.binding_id,
        ownership_id=ownership.ownership.ownership_id,
        action="assign_lane_worker",
        reason=request.reason,
        metadata={
            "runtime_provider": request.runtime_provider,
            **dict(request.metadata),
        },
    )
    return TrajectoryTeamContinuityResult(
        ok=True,
        action="assign_lane_worker",
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        assignment=assignment,
        binding_result=binding,
        ownership_result=ownership,
        event_record=event,
        status="assigned",
        message="trajectory lane worker assigned and lane ownership claimed",
    )


def resolve_trajectory_lane_worker(
    request: TrajectoryTeamContinuityResolveRequest,
) -> TrajectoryTeamContinuityResult:
    """Resolve the worker binding and ownership for a trajectory lane."""

    _require_common(request.trajectory_id, request.lane_id)
    bindings = inspect_continuous_worker_bindings(
        ContinuousWorkerBindingInspectRequest(
            ledger_path=request.binding_ledger_path,
            runtime_provider=request.runtime_provider,  # type: ignore[arg-type]
            lane_id=request.lane_id,
        )
    )
    ownerships = inspect_lane_ownerships(
        LaneOwnershipInspectRequest(
            ledger_path=request.ownership_ledger_path,
            lane_id=request.lane_id,
        )
    )
    binding = bindings.bindings[0] if bindings.bindings else None
    ownership = None
    if binding is not None:
        for item in ownerships.ownerships:
            if item.binding_id == binding.binding_id:
                ownership = item
                break
    if binding is None:
        return _no_continuity_result(
            action="resolve_lane_worker",
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            leader_id=request.leader_id,
            reason="no binding for lane",
            no_continuity_reason="binding_not_found",
            team_event_log_path=request.team_event_log_path,
            scheduler_event_log_path=request.scheduler_event_log_path,
            timestamp=request.timestamp,
            record_event=request.record_event,
            metadata=request.metadata,
        )
    if ownership is None:
        return _no_continuity_result(
            action="resolve_lane_worker",
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            leader_id=request.leader_id,
            worker_id=binding.worker_id,
            binding_id=binding.binding_id,
            reason="no selectable lane ownership for binding",
            no_continuity_reason="ownership_not_found",
            team_event_log_path=request.team_event_log_path,
            scheduler_event_log_path=request.scheduler_event_log_path,
            timestamp=request.timestamp,
            record_event=request.record_event,
            metadata=request.metadata,
        )
    assignment = TrajectoryLaneWorkerAssignment(
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        leader_id=request.leader_id,
        worker_id=binding.worker_id,
        runtime_provider=binding.runtime_provider,
        binding=binding,
        ownership=ownership,
        continuity_status=ownership.status,
    )
    event = None
    if request.record_event:
        event = _append_team_event(
            request.team_event_log_path,
            "trajectory_team_lane_worker_resolved",
            scheduler_event_log_path=request.scheduler_event_log_path,
            timestamp=request.timestamp,
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            leader_id=request.leader_id,
            worker_id=binding.worker_id,
            binding_id=binding.binding_id,
            ownership_id=ownership.ownership_id,
            action="resolve_lane_worker",
            reason=request.reason,
            metadata={
                "continuity_status": ownership.status,
                **dict(request.metadata),
            },
        )
    return TrajectoryTeamContinuityResult(
        ok=True,
        action="resolve_lane_worker",
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        assignment=assignment,
        event_record=event,
        status="resolved",
        message="trajectory lane worker continuity resolved",
    )


def activate_trajectory_lane_worker(
    request: TrajectoryTeamContinuityActivateRequest,
) -> TrajectoryTeamContinuityResult:
    """Activate a trajectory lane worker ownership after successful delivery."""

    _require_common(request.trajectory_id, request.lane_id)
    if not request.task_id:
        raise ValueError("trajectory lane worker activation requires task_id")
    if not request.delivery_id:
        raise ValueError("trajectory lane worker activation requires delivery_id")
    ownership = activate_lane_ownership(
        LaneOwnershipActivateRequest(
            ledger_path=request.ownership_ledger_path,
            event_log_path=request.ownership_event_log_path,
            ownership_id=request.ownership_id,
            binding_id=request.binding_id,
            activated_at=request.timestamp,
            delivery_id=request.delivery_id,
            task_id=request.task_id,
            reason=request.reason,
            audit_refs=_unique_nonempty(request.audit_refs),
            metadata={
                "trajectory_id": request.trajectory_id,
                "leader_id": request.leader_id,
                "team_continuity_action": "activate_lane_worker",
                **dict(request.metadata),
            },
        )
    )
    event = _append_team_event(
        request.team_event_log_path,
        "trajectory_team_lane_worker_activated",
        scheduler_event_log_path=request.scheduler_event_log_path,
        timestamp=request.timestamp,
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        leader_id=request.leader_id,
        worker_id="" if ownership.ownership is None else ownership.ownership.worker_id,
        binding_id=request.binding_id
        or ("" if ownership.ownership is None else ownership.ownership.binding_id),
        ownership_id=request.ownership_id
        or ("" if ownership.ownership is None else ownership.ownership.ownership_id),
        action="activate_lane_worker",
        reason=request.reason,
        task_id=request.task_id,
        delivery_id=request.delivery_id,
        metadata=request.metadata,
    )
    assignment = None
    if ownership.ownership is not None:
        assignment = TrajectoryLaneWorkerAssignment(
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            leader_id=request.leader_id,
            worker_id=ownership.ownership.worker_id,
            binding=None,
            ownership=ownership.ownership,
            continuity_status=ownership.ownership.status,
        )
    return TrajectoryTeamContinuityResult(
        ok=ownership.ok,
        action="activate_lane_worker",
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        assignment=assignment,
        ownership_result=ownership,
        event_record=event,
        status="activated" if ownership.ok else ownership.status,
        message=ownership.message,
    )


def suspend_trajectory_lane_worker(
    request: TrajectoryTeamContinuitySuspendRequest,
) -> TrajectoryTeamContinuityResult:
    """Suspend a trajectory lane ownership while preserving continuity state."""

    _require_common(request.trajectory_id, request.lane_id)
    ownership = suspend_lane_ownership(
        LaneOwnershipSuspendRequest(
            ledger_path=request.ownership_ledger_path,
            event_log_path=request.ownership_event_log_path,
            ownership_id=request.ownership_id,
            binding_id=request.binding_id,
            timestamp=request.timestamp,
            reason=request.reason,
            audit_refs=_unique_nonempty(request.audit_refs),
            metadata={
                "trajectory_id": request.trajectory_id,
                "leader_id": request.leader_id,
                "team_continuity_action": "suspend_lane_worker",
                **dict(request.metadata),
            },
        )
    )
    return _ownership_transition_team_result(
        action="suspend_lane_worker",
        event_kind="trajectory_team_lane_worker_suspended",
        request_trajectory_id=request.trajectory_id,
        request_lane_id=request.lane_id,
        leader_id=request.leader_id,
        binding_id=request.binding_id,
        ownership_id=request.ownership_id,
        reason=request.reason,
        timestamp=request.timestamp,
        team_event_log_path=request.team_event_log_path,
        scheduler_event_log_path=request.scheduler_event_log_path,
        ownership=ownership,
        metadata=request.metadata,
        success_status="suspended",
    )


def resume_trajectory_lane_worker(
    request: TrajectoryTeamContinuityResumeRequest,
) -> TrajectoryTeamContinuityResult:
    """Resume a suspended trajectory lane ownership."""

    _require_common(request.trajectory_id, request.lane_id)
    ownership = resume_lane_ownership(
        LaneOwnershipResumeRequest(
            ledger_path=request.ownership_ledger_path,
            event_log_path=request.ownership_event_log_path,
            ownership_id=request.ownership_id,
            binding_id=request.binding_id,
            timestamp=request.timestamp,
            reason=request.reason,
            audit_refs=_unique_nonempty(request.audit_refs),
            metadata={
                "trajectory_id": request.trajectory_id,
                "leader_id": request.leader_id,
                "team_continuity_action": "resume_lane_worker",
                **dict(request.metadata),
            },
        )
    )
    return _ownership_transition_team_result(
        action="resume_lane_worker",
        event_kind="trajectory_team_lane_worker_resumed",
        request_trajectory_id=request.trajectory_id,
        request_lane_id=request.lane_id,
        leader_id=request.leader_id,
        binding_id=request.binding_id,
        ownership_id=request.ownership_id,
        reason=request.reason,
        timestamp=request.timestamp,
        team_event_log_path=request.team_event_log_path,
        scheduler_event_log_path=request.scheduler_event_log_path,
        ownership=ownership,
        metadata=request.metadata,
        success_status="resumed",
    )


def transfer_trajectory_lane_worker(
    request: TrajectoryTeamContinuityTransferRequest,
) -> TrajectoryTeamContinuityResult:
    """Transfer a trajectory lane to a replacement worker binding."""

    _require_common(request.trajectory_id, request.lane_id)
    if not request.replacement_binding_id:
        raise ValueError("trajectory lane worker transfer requires replacement_binding_id")
    if not request.worker_id:
        raise ValueError("trajectory lane worker transfer requires worker_id")
    target_binding_id = request.binding_id
    if not target_binding_id:
        resolved = resolve_trajectory_lane_worker(
            TrajectoryTeamContinuityResolveRequest(
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                binding_ledger_path=request.binding_ledger_path,
                ownership_ledger_path=request.ownership_ledger_path,
                record_event=False,
            )
        )
        target_binding_id = (
            "" if resolved.assignment is None else resolved.assignment.binding_id
        )
    ownership = transfer_lane_ownership(
        LaneOwnershipTransferRequest(
            ledger_path=request.ownership_ledger_path,
            event_log_path=request.ownership_event_log_path,
            ownership_id=request.ownership_id,
            binding_id=target_binding_id,
            replacement_binding_id=request.replacement_binding_id,
            timestamp=request.timestamp,
            reason=request.reason,
            audit_refs=_unique_nonempty(request.audit_refs),
            metadata={
                "trajectory_id": request.trajectory_id,
                "leader_id": request.leader_id,
                "worker_id": request.worker_id,
                "team_continuity_action": "transfer_lane_worker",
                **dict(request.metadata),
            },
        )
    )
    event = _append_team_event(
        request.team_event_log_path,
        "trajectory_team_lane_worker_transferred",
        scheduler_event_log_path=request.scheduler_event_log_path,
        timestamp=request.timestamp,
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        leader_id=request.leader_id,
        worker_id=request.worker_id,
        binding_id=target_binding_id,
        ownership_id=request.ownership_id
        or ("" if ownership.ownership is None else ownership.ownership.ownership_id),
        action="transfer_lane_worker",
        reason=request.reason,
        previous_binding_id=target_binding_id,
        replacement_binding_id=request.replacement_binding_id,
        metadata=request.metadata,
    )
    return TrajectoryTeamContinuityResult(
        ok=ownership.ok,
        action="transfer_lane_worker",
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        ownership_result=ownership,
        event_record=event,
        status="transferred" if ownership.ok else ownership.status,
        message=ownership.message,
    )


def fork_trajectory_lane_worker(
    request: TrajectoryTeamContinuityForkRequest,
) -> TrajectoryTeamContinuityResult:
    """Fork a worker binding and transfer this lane ownership to the fork."""

    _require_common(request.trajectory_id, request.lane_id)
    if not request.new_binding_id:
        raise ValueError("trajectory lane worker fork requires new_binding_id")
    if not request.worker_id:
        raise ValueError("trajectory lane worker fork requires worker_id")
    source_binding_id = request.source_binding_id
    source_ownership_id = request.ownership_id
    if not source_binding_id or not source_ownership_id:
        resolved = resolve_trajectory_lane_worker(
            TrajectoryTeamContinuityResolveRequest(
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                binding_ledger_path=request.binding_ledger_path,
                ownership_ledger_path=request.ownership_ledger_path,
                record_event=False,
            )
        )
        if resolved.assignment is not None:
            source_binding_id = source_binding_id or resolved.assignment.binding_id
            source_ownership_id = source_ownership_id or resolved.assignment.ownership_id
    fork = fork_continuous_worker_binding(
        ContinuousWorkerBindingForkRequest(
            ledger_path=request.binding_ledger_path,
            event_log_path=request.binding_event_log_path,
            source_binding_id=source_binding_id,
            new_binding_id=request.new_binding_id,
            worker_id=request.worker_id,
            scope_kind="lane",
            scope_id=request.lane_id,
            lane_ids=(request.lane_id,),
            active_session_selector=request.active_session_selector,
            compact_context_ref=request.compact_context_ref,
            mailbox_cursor_ref=request.mailbox_cursor_ref,
            worker_report_refs=_unique_nonempty(request.worker_report_refs),
            audit_refs=_unique_nonempty(request.audit_refs),
            timestamp=request.timestamp,
            reason=request.reason,
            metadata={
                "trajectory_id": request.trajectory_id,
                "leader_id": request.leader_id,
                "team_continuity_action": "fork_lane_worker",
                **dict(request.metadata),
            },
        )
    )
    if not fork.ok or fork.binding is None:
        event = _append_team_event(
            request.team_event_log_path,
            "trajectory_team_no_continuity_recorded",
            scheduler_event_log_path=request.scheduler_event_log_path,
            timestamp=request.timestamp,
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            leader_id=request.leader_id,
            worker_id=request.worker_id,
            binding_id=source_binding_id,
            action="fork_lane_worker",
            reason=fork.message,
            no_continuity_reason="binding_not_selectable",
            metadata=request.metadata,
        )
        return TrajectoryTeamContinuityResult(
            ok=False,
            action="fork_lane_worker",
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            binding_result=fork,
            event_record=event,
            status=fork.status,
            message=fork.message,
        )
    transfer = transfer_lane_ownership(
        LaneOwnershipTransferRequest(
            ledger_path=request.ownership_ledger_path,
            event_log_path=request.ownership_event_log_path,
            ownership_id=source_ownership_id,
            binding_id=source_binding_id,
            replacement_binding_id=fork.binding.binding_id,
            timestamp=request.timestamp,
            reason=request.reason,
            audit_refs=_unique_nonempty(request.audit_refs),
            metadata={
                "trajectory_id": request.trajectory_id,
                "leader_id": request.leader_id,
                "worker_id": request.worker_id,
                "team_continuity_action": "fork_lane_worker",
                **dict(request.metadata),
            },
        )
    )
    event = _append_team_event(
        request.team_event_log_path,
        "trajectory_team_lane_worker_forked",
        scheduler_event_log_path=request.scheduler_event_log_path,
        timestamp=request.timestamp,
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        leader_id=request.leader_id,
        worker_id=request.worker_id,
        binding_id=source_binding_id,
        ownership_id=source_ownership_id,
        action="fork_lane_worker",
        reason=request.reason,
        previous_binding_id=source_binding_id,
        replacement_binding_id=fork.binding.binding_id,
        metadata=request.metadata,
    )
    assignment = TrajectoryLaneWorkerAssignment(
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        leader_id=request.leader_id,
        worker_id=request.worker_id,
        runtime_provider=fork.binding.runtime_provider,
        binding=fork.binding,
        ownership=None if not transfer.ok else transfer.ownership,
        continuity_status="forked" if transfer.ok else "fork_pending_transfer",
    )
    return TrajectoryTeamContinuityResult(
        ok=bool(fork.ok and transfer.ok),
        action="fork_lane_worker",
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        assignment=assignment,
        binding_result=fork,
        ownership_result=transfer,
        event_record=event,
        status="forked" if fork.ok and transfer.ok else transfer.status,
        message=(
            "trajectory lane worker forked and ownership transferred"
            if fork.ok and transfer.ok
            else transfer.message
        ),
    )


def release_trajectory_lane_worker(
    request: TrajectoryTeamContinuityReleaseRequest,
) -> TrajectoryTeamContinuityResult:
    """Release a trajectory lane ownership without deleting binding history."""

    _require_common(request.trajectory_id, request.lane_id)
    ownership = release_lane_ownership(
        LaneOwnershipReleaseRequest(
            ledger_path=request.ownership_ledger_path,
            event_log_path=request.ownership_event_log_path,
            ownership_id=request.ownership_id,
            binding_id=request.binding_id,
            timestamp=request.timestamp,
            reason=request.reason,
            audit_refs=_unique_nonempty(request.audit_refs),
            metadata={
                "trajectory_id": request.trajectory_id,
                "leader_id": request.leader_id,
                "team_continuity_action": "release_lane_worker",
                **dict(request.metadata),
            },
        )
    )
    event = _append_team_event(
        request.team_event_log_path,
        "trajectory_team_lane_worker_released",
        scheduler_event_log_path=request.scheduler_event_log_path,
        timestamp=request.timestamp,
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        leader_id=request.leader_id,
        worker_id="" if ownership.ownership is None else ownership.ownership.worker_id,
        binding_id=request.binding_id
        or ("" if ownership.ownership is None else ownership.ownership.binding_id),
        ownership_id=request.ownership_id
        or ("" if ownership.ownership is None else ownership.ownership.ownership_id),
        action="release_lane_worker",
        reason=request.reason,
        metadata=request.metadata,
    )
    return TrajectoryTeamContinuityResult(
        ok=ownership.ok,
        action="release_lane_worker",
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        ownership_result=ownership,
        event_record=event,
        status="released" if ownership.ok else ownership.status,
        message=ownership.message,
    )


def record_trajectory_lane_no_continuity(
    request: TrajectoryTeamContinuityNoContinuityRequest,
) -> TrajectoryTeamContinuityResult:
    """Record an explicit reason a lane will not use a continuous worker."""

    _require_common(request.trajectory_id, request.lane_id)
    return _no_continuity_result(
        action="record_no_continuity",
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        leader_id=request.leader_id,
        worker_id=request.worker_id,
        binding_id=request.binding_id,
        reason=request.reason,
        no_continuity_reason=str(request.no_continuity_reason),
        team_event_log_path=request.team_event_log_path,
        scheduler_event_log_path=request.scheduler_event_log_path,
        timestamp=request.timestamp,
        record_event=True,
        metadata=request.metadata,
    )


def trajectory_team_continuity_event_record_from_json_dict(
    payload: Mapping[str, object],
) -> TrajectoryTeamContinuityEventRecord:
    return TrajectoryTeamContinuityEventRecord(
        event_id=str(payload.get("event_id", "")),
        event_kind=str(payload.get("event_kind", "trajectory_team_no_continuity_recorded")),  # type: ignore[arg-type]
        timestamp=str(payload.get("timestamp", "")),
        trajectory_id=str(payload.get("trajectory_id", "")),
        lane_id=str(payload.get("lane_id", "")),
        worker_id=str(payload.get("worker_id", "")),
        leader_id=str(payload.get("leader_id", "")),
        binding_id=str(payload.get("binding_id", "")),
        ownership_id=str(payload.get("ownership_id", "")),
        action=str(payload.get("action", "")),
        reason=str(payload.get("reason", "")),
        previous_binding_id=str(payload.get("previous_binding_id", "")),
        replacement_binding_id=str(payload.get("replacement_binding_id", "")),
        task_id=str(payload.get("task_id", "")),
        delivery_id=str(payload.get("delivery_id", "")),
        no_continuity_reason=str(payload.get("no_continuity_reason", "")),
        metadata=dict(_mapping(payload.get("metadata"))),
    )


def _no_continuity_result(
    *,
    action: TrajectoryTeamContinuityAction,
    trajectory_id: str,
    lane_id: str,
    leader_id: str,
    reason: str,
    no_continuity_reason: str,
    team_event_log_path: str | Path,
    scheduler_event_log_path: str | Path,
    timestamp: str,
    record_event: bool,
    worker_id: str = "",
    binding_id: str = "",
    metadata: Mapping[str, object] | None = None,
) -> TrajectoryTeamContinuityResult:
    assignment = TrajectoryLaneWorkerAssignment(
        trajectory_id=trajectory_id,
        lane_id=lane_id,
        leader_id=leader_id,
        worker_id=worker_id,
        binding=None,
        ownership=None,
        continuity_status="no_continuity",
        no_continuity_reason=no_continuity_reason,
    )
    event = None
    if record_event:
        event = _append_team_event(
            team_event_log_path,
            "trajectory_team_no_continuity_recorded",
            scheduler_event_log_path=scheduler_event_log_path,
            timestamp=timestamp,
            trajectory_id=trajectory_id,
            lane_id=lane_id,
            leader_id=leader_id,
            worker_id=worker_id,
            binding_id=binding_id,
            action=action,
            reason=reason,
            no_continuity_reason=no_continuity_reason,
            metadata=metadata or {},
        )
    return TrajectoryTeamContinuityResult(
        ok=False,
        action=action,
        trajectory_id=trajectory_id,
        lane_id=lane_id,
        assignment=assignment,
        event_record=event,
        status="no_continuity",
        message=reason,
    )


def _ownership_transition_team_result(
    *,
    action: TrajectoryTeamContinuityAction,
    event_kind: TrajectoryTeamContinuityEventKind,
    request_trajectory_id: str,
    request_lane_id: str,
    leader_id: str,
    binding_id: str,
    ownership_id: str,
    reason: str,
    timestamp: str,
    team_event_log_path: str | Path,
    scheduler_event_log_path: str | Path,
    ownership: LaneOwnershipResult,
    metadata: Mapping[str, object],
    success_status: str,
) -> TrajectoryTeamContinuityResult:
    current = ownership.ownership
    event = _append_team_event(
        team_event_log_path,
        event_kind,
        scheduler_event_log_path=scheduler_event_log_path,
        timestamp=timestamp,
        trajectory_id=request_trajectory_id,
        lane_id=request_lane_id,
        leader_id=leader_id,
        worker_id="" if current is None else current.worker_id,
        binding_id=binding_id or ("" if current is None else current.binding_id),
        ownership_id=ownership_id or ("" if current is None else current.ownership_id),
        action=action,
        reason=reason,
        metadata=metadata,
    )
    assignment = None
    if current is not None:
        assignment = TrajectoryLaneWorkerAssignment(
            trajectory_id=request_trajectory_id,
            lane_id=request_lane_id,
            leader_id=leader_id,
            worker_id=current.worker_id,
            binding=None,
            ownership=current,
            continuity_status=current.status,
        )
    return TrajectoryTeamContinuityResult(
        ok=ownership.ok,
        action=action,
        trajectory_id=request_trajectory_id,
        lane_id=request_lane_id,
        assignment=assignment,
        ownership_result=ownership,
        event_record=event,
        status=success_status if ownership.ok else ownership.status,
        message=ownership.message,
    )


def _append_team_event(
    path: str | Path,
    event_kind: TrajectoryTeamContinuityEventKind,
    *,
    scheduler_event_log_path: str | Path = "",
    timestamp: str,
    trajectory_id: str,
    lane_id: str,
    action: str,
    reason: str,
    worker_id: str = "",
    leader_id: str = "",
    binding_id: str = "",
    ownership_id: str = "",
    previous_binding_id: str = "",
    replacement_binding_id: str = "",
    task_id: str = "",
    delivery_id: str = "",
    no_continuity_reason: str = "",
    metadata: Mapping[str, object] | None = None,
) -> TrajectoryTeamContinuityEventRecord:
    log = JsonlTrajectoryTeamContinuityEventLog(path)
    record = TrajectoryTeamContinuityEventRecord(
        event_id=_event_id(trajectory_id, lane_id, action, len(log.read_all()) + 1),
        event_kind=event_kind,
        timestamp=timestamp,
        trajectory_id=trajectory_id,
        lane_id=lane_id,
        worker_id=worker_id,
        leader_id=leader_id,
        binding_id=binding_id,
        ownership_id=ownership_id,
        action=action,
        reason=reason,
        previous_binding_id=previous_binding_id,
        replacement_binding_id=replacement_binding_id,
        task_id=task_id,
        delivery_id=delivery_id,
        no_continuity_reason=no_continuity_reason,
        metadata=dict(metadata or {}),
    )
    appended = log.append(record)
    _append_scheduler_audit_event(scheduler_event_log_path, appended)
    return appended


def _append_scheduler_audit_event(
    path: str | Path,
    record: TrajectoryTeamContinuityEventRecord,
) -> None:
    if not path:
        return
    JsonlSchedulerEventLog(path).append(
        SchedulerEvent(
            event_id=f"scheduler-audit:{record.event_id}",
            event_kind=_scheduler_event_kind_for_team_event(record.event_kind),
            timestamp=record.timestamp,
            task_id=record.task_id,
            from_state="",
            to_state="",
            reason=record.reason,
            run_id="",
            session_id="",
            related_artifact_ids=_unique_nonempty(
                (
                    record.binding_id,
                    record.ownership_id,
                    record.previous_binding_id,
                    record.replacement_binding_id,
                    record.delivery_id,
                )
            ),
            metadata={
                "audit_only": True,
                "audit_source": "trajectory_team_continuity",
                "trajectory_id": record.trajectory_id,
                "lane_id": record.lane_id,
                "leader_id": record.leader_id,
                "worker_id": record.worker_id,
                "binding_id": record.binding_id,
                "ownership_id": record.ownership_id,
                "action": record.action,
                "previous_binding_id": record.previous_binding_id,
                "replacement_binding_id": record.replacement_binding_id,
                "delivery_id": record.delivery_id,
                "no_continuity_reason": record.no_continuity_reason,
                "team_event_id": record.event_id,
                **dict(record.metadata),
            },
        )
    )


def _scheduler_event_kind_for_team_event(
    event_kind: TrajectoryTeamContinuityEventKind,
):
    return {
        "trajectory_team_lane_worker_assigned": "trajectory_team_worker_assigned",
        "trajectory_team_lane_worker_resolved": "trajectory_team_worker_resolved",
        "trajectory_team_lane_worker_activated": "trajectory_team_worker_activated",
        "trajectory_team_lane_worker_suspended": "trajectory_team_worker_suspended",
        "trajectory_team_lane_worker_resumed": "trajectory_team_worker_resumed",
        "trajectory_team_lane_worker_transferred": "trajectory_team_worker_transferred",
        "trajectory_team_lane_worker_forked": "trajectory_team_worker_forked",
        "trajectory_team_lane_worker_released": "trajectory_team_worker_released",
        "trajectory_team_no_continuity_recorded": "trajectory_team_no_continuity",
    }[event_kind]


def _event_id(trajectory_id: str, lane_id: str, action: str, index: int) -> str:
    return "trajectory-team:{trajectory}:{lane}:{action}:{index:04d}".format(
        trajectory=_safe_id(trajectory_id),
        lane=_safe_id(lane_id),
        action=_safe_id(action),
        index=index,
    )


def _safe_id(value: str) -> str:
    return value.replace("\\", "/").strip("/").replace("/", "-").replace(":", "-")


def _require_common(trajectory_id: str, lane_id: str) -> None:
    if not trajectory_id:
        raise ValueError("trajectory team continuity requires trajectory_id")
    if not lane_id:
        raise ValueError("trajectory team continuity requires lane_id")


def _validate_runtime_provider(provider: str) -> None:
    if provider not in {"fake", "qoder", "codex", "opencode"}:
        raise ValueError(
            "trajectory team continuity runtime_provider must be fake, qoder, codex, or opencode"
        )


def _validate_no_raw_or_secret_fields(
    layer: str,
    record_id: str,
    value: object,
) -> None:
    blocked_key_fragments = (
        "raw_transcript",
        "transcript_text",
        "transcript_body",
        "secret_value",
        "api_key",
        "access_token",
        "password",
        "credential",
    )
    for path, item in _walk_mapping_items(value):
        lowered_path = ".".join(path).lower()
        if any(fragment in lowered_path for fragment in blocked_key_fragments):
            raise ValueError(
                f"{layer} rejected: raw transcript or secret value is not allowed "
                f"id={record_id} field={'.'.join(path)}"
            )
        if any(segment.lower() in {"secret", "secrets"} for segment in path):
            raise ValueError(
                f"{layer} rejected: raw transcript or secret value is not allowed "
                f"id={record_id} field={'.'.join(path)}"
            )
        if isinstance(item, str) and _looks_like_secret_or_raw_transcript(item):
            raise ValueError(
                f"{layer} rejected: raw transcript or secret value is not allowed "
                f"id={record_id} field={'.'.join(path)}"
            )


def _walk_mapping_items(value: object) -> tuple[tuple[tuple[str, ...], object], ...]:
    items: list[tuple[tuple[str, ...], object]] = []

    def visit(current: object, path: tuple[str, ...]) -> None:
        if isinstance(current, Mapping):
            for key, nested in current.items():
                nested_path = (*path, str(key))
                items.append((nested_path, nested))
                visit(nested, nested_path)
        elif isinstance(current, (list, tuple)):
            for index, nested in enumerate(current):
                visit(nested, (*path, str(index)))

    visit(value, ())
    return tuple(items)


def _looks_like_secret_or_raw_transcript(value: str) -> bool:
    lowered = value.lower()
    if "raw transcript" in lowered or "raw_transcript" in lowered:
        return True
    return any(
        marker in lowered
        for marker in (
            "api_key=",
            "access_token=",
            "password=",
            "secret=",
            "bearer ",
        )
    )


def _unique_nonempty(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if value and value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


__all__ = [
    "DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH",
    "TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_SCHEMA_VERSION",
    "JsonlTrajectoryTeamContinuityEventLog",
    "NoContinuityReason",
    "TrajectoryLaneWorkerAssignment",
    "TrajectoryTeamContinuityAction",
    "TrajectoryTeamContinuityActivateRequest",
    "TrajectoryTeamContinuityAssignRequest",
    "TrajectoryTeamContinuityEventKind",
    "TrajectoryTeamContinuityEventRecord",
    "TrajectoryTeamContinuityForkRequest",
    "TrajectoryTeamContinuityNoContinuityRequest",
    "TrajectoryTeamContinuityReleaseRequest",
    "TrajectoryTeamContinuityResumeRequest",
    "TrajectoryTeamContinuityResolveRequest",
    "TrajectoryTeamContinuityResult",
    "TrajectoryTeamContinuitySuspendRequest",
    "TrajectoryTeamContinuityTransferRequest",
    "activate_trajectory_lane_worker",
    "assign_trajectory_lane_worker",
    "fork_trajectory_lane_worker",
    "record_trajectory_lane_no_continuity",
    "release_trajectory_lane_worker",
    "resume_trajectory_lane_worker",
    "resolve_trajectory_lane_worker",
    "suspend_trajectory_lane_worker",
    "trajectory_team_continuity_event_record_from_json_dict",
    "transfer_trajectory_lane_worker",
]
