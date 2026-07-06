"""Unified surface dispatcher for trajectory team continuity.

This module is the shared adapter used by CLI and MCP. It keeps host/operator
input parsing out of the lower-level trajectory team bridge and provides one
readback shape for inspect/resolve/mutating actions.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .continuous_worker_binding import (
    DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH,
    DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH,
    DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH,
    DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH,
    DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH,
    ContinuousWorkerBinding,
    ContinuousWorkerBindingInspectRequest,
    ContinuousWorkerSessionSelector,
    DeliveryLease,
    DeliveryLeaseInspectRequest,
    LaneOwnership,
    LaneOwnershipInspectRequest,
    inspect_continuous_worker_bindings,
    inspect_delivery_leases,
    inspect_lane_ownerships,
)
from .runtime_adapter import RuntimeProviderKind
from .trajectory_team_continuity import (
    DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH,
    JsonlTrajectoryTeamContinuityEventLog,
    TrajectoryTeamContinuityActivateRequest,
    TrajectoryTeamContinuityAssignRequest,
    TrajectoryTeamContinuityEventRecord,
    TrajectoryTeamContinuityForkRequest,
    TrajectoryTeamContinuityNoContinuityRequest,
    TrajectoryTeamContinuityReleaseRequest,
    TrajectoryTeamContinuityResolveRequest,
    TrajectoryTeamContinuityResumeRequest,
    TrajectoryTeamContinuityResult,
    TrajectoryTeamContinuitySuspendRequest,
    TrajectoryTeamContinuityTransferRequest,
    activate_trajectory_lane_worker,
    assign_trajectory_lane_worker,
    fork_trajectory_lane_worker,
    record_trajectory_lane_no_continuity,
    release_trajectory_lane_worker,
    resolve_trajectory_lane_worker,
    resume_trajectory_lane_worker,
    suspend_trajectory_lane_worker,
    transfer_trajectory_lane_worker,
)
from .trajectory_team_continuity import _validate_no_raw_or_secret_fields

TrajectoryTeamSurfaceAction = Literal[
    "inspect",
    "resolve",
    "assign",
    "activate",
    "suspend",
    "resume",
    "transfer",
    "fork",
    "release",
    "noContinuity",
]
TrajectoryTeamCallerRole = Literal[
    "leader",
    "main",
    "supervisor",
    "guide",
    "worker",
    "subagent",
    "lane_worker",
    "bounded_worker",
]

READ_ONLY_ACTIONS = {"inspect", "resolve"}
MUTATING_ACTIONS = {
    "assign",
    "activate",
    "suspend",
    "resume",
    "transfer",
    "fork",
    "release",
    "noContinuity",
}
MUTATION_ALLOWED_ROLES = {"leader", "main", "supervisor", "guide"}
WORKER_REPORT_PROCEDURE = "docs/worker-trajectory-update-reporting.md"


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuitySurfaceRequest:
    """Shared request for CLI/MCP trajectory-team actions."""

    action: TrajectoryTeamSurfaceAction
    project_root: str | Path = "."
    caller_role: TrajectoryTeamCallerRole | str = "leader"
    trajectory_id: str = ""
    lane_id: str = ""
    leader_id: str = "agent:guide"
    worker_id: str = ""
    runtime_provider: RuntimeProviderKind | str = "opencode"
    binding_id: str = ""
    ownership_id: str = ""
    replacement_binding_id: str = ""
    new_binding_id: str = ""
    source_binding_id: str = ""
    no_continuity_reason: str = ""
    task_id: str = ""
    delivery_id: str = ""
    timestamp: str = ""
    reason: str = ""
    binding_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    binding_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH
    ownership_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    ownership_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_EVENT_LOG_RELATIVE_PATH
    lease_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH
    team_event_log_path: str | Path = DEFAULT_TRAJECTORY_TEAM_CONTINUITY_EVENT_LOG_RELATIVE_PATH
    scheduler_event_log_path: str | Path = ""
    attach_url: str = ""
    session_id: str = ""
    continue_session: bool = False
    fork_session: bool = False
    compact_context_ref: str = ""
    mailbox_cursor_ref: str = ""
    worker_report_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    include_inactive: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TrajectoryTeamLaneReadback:
    """Readback row for one lane in a trajectory team."""

    trajectory_id: str
    lane_id: str
    leader_id: str = ""
    worker_id: str = ""
    runtime_provider: str = ""
    binding_id: str = ""
    binding_status: str = ""
    ownership_id: str = ""
    ownership_status: str = ""
    compact_context_ref: str = ""
    mailbox_cursor_ref: str = ""
    worker_report_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    active_lease_id: str = ""
    active_lease_status: str = ""
    last_team_event_kind: str = ""
    last_team_event_id: str = ""
    no_continuity_reason: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "lane_id": self.lane_id,
            "leader_id": self.leader_id,
            "worker_id": self.worker_id,
            "runtime_provider": self.runtime_provider,
            "binding_id": self.binding_id,
            "binding_status": self.binding_status,
            "ownership_id": self.ownership_id,
            "ownership_status": self.ownership_status,
            "compact_context_ref": self.compact_context_ref,
            "mailbox_cursor_ref": self.mailbox_cursor_ref,
            "worker_report_refs": list(self.worker_report_refs),
            "audit_refs": list(self.audit_refs),
            "active_lease_id": self.active_lease_id,
            "active_lease_status": self.active_lease_status,
            "last_team_event_kind": self.last_team_event_kind,
            "last_team_event_id": self.last_team_event_id,
            "no_continuity_reason": self.no_continuity_reason,
        }


@dataclass(frozen=True, slots=True)
class TrajectoryTeamContinuitySurfaceResult:
    """Unified CLI/MCP result for trajectory-team actions."""

    ok: bool
    action: str
    status: str
    message: str
    trajectory_id: str = ""
    lane_id: str = ""
    rows: tuple[TrajectoryTeamLaneReadback, ...] = ()
    bridge_result: TrajectoryTeamContinuityResult | None = None
    paths: Mapping[str, str] = field(default_factory=dict)
    errors: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "action": self.action,
            "status": self.status,
            "message": self.message,
            "trajectory_id": self.trajectory_id,
            "lane_id": self.lane_id,
            "rows": [row.to_json_dict() for row in self.rows],
            "bridge_result": (
                None
                if self.bridge_result is None
                else self.bridge_result.to_json_dict()
            ),
            "paths": dict(self.paths),
            "errors": list(self.errors),
            "authority_split": {
                "trajectory_team_surface": True,
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "delivery_state_mutated": False,
                "local_work_trajectory_mutated": False,
                "worker_direct_mutation_allowed": False,
                "raw_transcript_persisted": False,
                "secret_value_persisted": False,
                "bridge_mutated": (
                    False
                    if self.bridge_result is None
                    else bool(
                        self.bridge_result.to_json_dict()["authority_split"][
                            "trajectory_team_continuity_event_log_mutated"
                        ]
                    )
                ),
            },
            "worker_report_procedure": WORKER_REPORT_PROCEDURE,
        }


def run_trajectory_team_continuity_surface(
    request: TrajectoryTeamContinuitySurfaceRequest,
) -> TrajectoryTeamContinuitySurfaceResult:
    """Run one trajectory-team CLI/MCP action through a shared dispatcher."""

    try:
        _validate_action(request.action)
        _validate_no_raw_or_secret_fields(
            "trajectory team continuity surface",
            request.trajectory_id or request.lane_id or request.action,
            request.metadata,
        )
    except Exception as exc:
        return TrajectoryTeamContinuitySurfaceResult(
            ok=False,
            action=str(request.action),
            status="invalid_request",
            message=str(exc),
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            errors=(str(exc),),
        )
    caller_role = str(request.caller_role).replace("-", "_")
    if request.action in MUTATING_ACTIONS and caller_role not in MUTATION_ALLOWED_ROLES:
        return _rejected_worker_mutation(request)

    paths = _paths(request)
    try:
        bridge_result = _run_bridge_action(request, paths)
        rows = _inspect_rows(request, paths)
        if request.action == "inspect":
            return TrajectoryTeamContinuitySurfaceResult(
                ok=True,
                action=request.action,
                status="inspected",
                message=f"{len(rows)} trajectory team lane row(s) matched",
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                rows=rows,
                paths=paths,
            )
        if request.action == "resolve":
            ok = bridge_result.ok if bridge_result is not None else bool(rows)
            return TrajectoryTeamContinuitySurfaceResult(
                ok=ok,
                action=request.action,
                status="resolved" if ok else "no_continuity",
                message=(
                    "trajectory team lane resolved"
                    if ok
                    else "trajectory team lane has no continuity"
                ),
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                rows=rows,
                bridge_result=bridge_result,
                paths=paths,
            )
        return TrajectoryTeamContinuitySurfaceResult(
            ok=bridge_result.ok if bridge_result is not None else False,
            action=request.action,
            status="" if bridge_result is None else bridge_result.status,
            message="" if bridge_result is None else bridge_result.message,
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            rows=rows,
            bridge_result=bridge_result,
            paths=paths,
        )
    except Exception as exc:
        return TrajectoryTeamContinuitySurfaceResult(
            ok=False,
            action=request.action,
            status="error",
            message=str(exc),
            trajectory_id=request.trajectory_id,
            lane_id=request.lane_id,
            paths=paths,
            errors=(str(exc),),
        )


def _run_bridge_action(
    request: TrajectoryTeamContinuitySurfaceRequest,
    paths: Mapping[str, str],
) -> TrajectoryTeamContinuityResult | None:
    if request.action == "inspect":
        return None
    if request.action == "resolve":
        return resolve_trajectory_lane_worker(
            TrajectoryTeamContinuityResolveRequest(
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                runtime_provider=request.runtime_provider,
                leader_id=request.leader_id,
                binding_ledger_path=paths["binding_ledger_path"],
                ownership_ledger_path=paths["ownership_ledger_path"],
                team_event_log_path=paths["team_event_log_path"],
                scheduler_event_log_path=paths["scheduler_event_log_path"],
                timestamp=request.timestamp,
                reason=request.reason or "trajectory lane worker resolved",
                metadata=request.metadata,
            )
        )
    if request.action == "assign":
        return assign_trajectory_lane_worker(
            TrajectoryTeamContinuityAssignRequest(
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                leader_id=request.leader_id,
                worker_id=request.worker_id,
                runtime_provider=request.runtime_provider,  # type: ignore[arg-type]
                binding_ledger_path=paths["binding_ledger_path"],
                binding_event_log_path=paths["binding_event_log_path"],
                ownership_ledger_path=paths["ownership_ledger_path"],
                ownership_event_log_path=paths["ownership_event_log_path"],
                team_event_log_path=paths["team_event_log_path"],
                scheduler_event_log_path=paths["scheduler_event_log_path"],
                binding_id=request.binding_id,
                ownership_id=request.ownership_id,
                active_session_selector=_session_selector(request),
                compact_context_ref=request.compact_context_ref,
                mailbox_cursor_ref=request.mailbox_cursor_ref,
                worker_report_refs=request.worker_report_refs,
                audit_refs=request.audit_refs,
                timestamp=request.timestamp,
                reason=request.reason or "trajectory lane worker assigned",
                metadata=request.metadata,
            )
        )
    if request.action == "activate":
        return activate_trajectory_lane_worker(
            TrajectoryTeamContinuityActivateRequest(
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                binding_id=request.binding_id,
                ownership_id=request.ownership_id,
                leader_id=request.leader_id,
                task_id=request.task_id,
                delivery_id=request.delivery_id,
                ownership_ledger_path=paths["ownership_ledger_path"],
                ownership_event_log_path=paths["ownership_event_log_path"],
                team_event_log_path=paths["team_event_log_path"],
                scheduler_event_log_path=paths["scheduler_event_log_path"],
                timestamp=request.timestamp,
                reason=request.reason or "trajectory lane worker activated",
                audit_refs=request.audit_refs,
                metadata=request.metadata,
            )
        )
    if request.action == "suspend":
        return suspend_trajectory_lane_worker(
            TrajectoryTeamContinuitySuspendRequest(
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                leader_id=request.leader_id,
                binding_id=request.binding_id,
                ownership_id=request.ownership_id,
                ownership_ledger_path=paths["ownership_ledger_path"],
                ownership_event_log_path=paths["ownership_event_log_path"],
                team_event_log_path=paths["team_event_log_path"],
                scheduler_event_log_path=paths["scheduler_event_log_path"],
                timestamp=request.timestamp,
                reason=request.reason or "trajectory lane worker suspended",
                audit_refs=request.audit_refs,
                metadata=request.metadata,
            )
        )
    if request.action == "resume":
        return resume_trajectory_lane_worker(
            TrajectoryTeamContinuityResumeRequest(
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                leader_id=request.leader_id,
                binding_id=request.binding_id,
                ownership_id=request.ownership_id,
                ownership_ledger_path=paths["ownership_ledger_path"],
                ownership_event_log_path=paths["ownership_event_log_path"],
                team_event_log_path=paths["team_event_log_path"],
                scheduler_event_log_path=paths["scheduler_event_log_path"],
                timestamp=request.timestamp,
                reason=request.reason or "trajectory lane worker resumed",
                audit_refs=request.audit_refs,
                metadata=request.metadata,
            )
        )
    if request.action == "transfer":
        return transfer_trajectory_lane_worker(
            TrajectoryTeamContinuityTransferRequest(
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                replacement_binding_id=request.replacement_binding_id,
                worker_id=request.worker_id,
                leader_id=request.leader_id,
                binding_id=request.binding_id,
                ownership_id=request.ownership_id,
                binding_ledger_path=paths["binding_ledger_path"],
                ownership_ledger_path=paths["ownership_ledger_path"],
                ownership_event_log_path=paths["ownership_event_log_path"],
                team_event_log_path=paths["team_event_log_path"],
                scheduler_event_log_path=paths["scheduler_event_log_path"],
                timestamp=request.timestamp,
                reason=request.reason or "trajectory lane worker transferred",
                audit_refs=request.audit_refs,
                metadata=request.metadata,
            )
        )
    if request.action == "fork":
        return fork_trajectory_lane_worker(
            TrajectoryTeamContinuityForkRequest(
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                new_binding_id=request.new_binding_id,
                worker_id=request.worker_id,
                leader_id=request.leader_id,
                source_binding_id=request.source_binding_id,
                ownership_id=request.ownership_id,
                binding_ledger_path=paths["binding_ledger_path"],
                binding_event_log_path=paths["binding_event_log_path"],
                ownership_ledger_path=paths["ownership_ledger_path"],
                ownership_event_log_path=paths["ownership_event_log_path"],
                team_event_log_path=paths["team_event_log_path"],
                scheduler_event_log_path=paths["scheduler_event_log_path"],
                active_session_selector=_session_selector(request),
                compact_context_ref=request.compact_context_ref,
                mailbox_cursor_ref=request.mailbox_cursor_ref,
                worker_report_refs=request.worker_report_refs,
                audit_refs=request.audit_refs,
                timestamp=request.timestamp,
                reason=request.reason or "trajectory lane worker forked",
                metadata=request.metadata,
            )
        )
    if request.action == "release":
        return release_trajectory_lane_worker(
            TrajectoryTeamContinuityReleaseRequest(
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                leader_id=request.leader_id,
                binding_id=request.binding_id,
                ownership_id=request.ownership_id,
                ownership_ledger_path=paths["ownership_ledger_path"],
                ownership_event_log_path=paths["ownership_event_log_path"],
                team_event_log_path=paths["team_event_log_path"],
                scheduler_event_log_path=paths["scheduler_event_log_path"],
                timestamp=request.timestamp,
                reason=request.reason or "trajectory lane worker released",
                audit_refs=request.audit_refs,
                metadata=request.metadata,
            )
        )
    if request.action == "noContinuity":
        return record_trajectory_lane_no_continuity(
            TrajectoryTeamContinuityNoContinuityRequest(
                trajectory_id=request.trajectory_id,
                lane_id=request.lane_id,
                no_continuity_reason=(
                    request.no_continuity_reason or "explicit_no_continuity"
                ),
                leader_id=request.leader_id,
                worker_id=request.worker_id,
                binding_id=request.binding_id,
                team_event_log_path=paths["team_event_log_path"],
                scheduler_event_log_path=paths["scheduler_event_log_path"],
                timestamp=request.timestamp,
                reason=request.reason or "trajectory lane has no continuous worker",
                metadata=request.metadata,
            )
        )
    raise ValueError(f"unsupported trajectory team action: {request.action}")


def _inspect_rows(
    request: TrajectoryTeamContinuitySurfaceRequest,
    paths: Mapping[str, str],
) -> tuple[TrajectoryTeamLaneReadback, ...]:
    bindings = inspect_continuous_worker_bindings(
        ContinuousWorkerBindingInspectRequest(
            ledger_path=paths["binding_ledger_path"],
            lane_id=request.lane_id,
            runtime_provider=request.runtime_provider if request.runtime_provider else "",
            include_inactive=request.include_inactive,
        )
    ).bindings
    ownerships = inspect_lane_ownerships(
        LaneOwnershipInspectRequest(
            ledger_path=paths["ownership_ledger_path"],
            lane_id=request.lane_id,
            include_inactive=request.include_inactive,
        )
    ).ownerships
    leases = inspect_delivery_leases(
        DeliveryLeaseInspectRequest(
            ledger_path=paths["lease_ledger_path"],
            include_inactive=False,
        )
    ).leases
    events = _team_events(paths["team_event_log_path"], request)
    lanes = _lane_ids(request, bindings, ownerships, events)
    rows: list[TrajectoryTeamLaneReadback] = []
    for lane_id in lanes:
        binding = _binding_for_lane(lane_id, bindings)
        ownership = _ownership_for_lane(lane_id, ownerships, binding)
        event = _last_event_for_lane(lane_id, events)
        lease = _active_lease_for_binding(
            "" if binding is None else binding.binding_id,
            leases,
        )
        rows.append(
            _readback_row(
                request,
                lane_id=lane_id,
                binding=binding,
                ownership=ownership,
                lease=lease,
                event=event,
            )
        )
    return tuple(rows)


def _readback_row(
    request: TrajectoryTeamContinuitySurfaceRequest,
    *,
    lane_id: str,
    binding: ContinuousWorkerBinding | None,
    ownership: LaneOwnership | None,
    lease: DeliveryLease | None,
    event: TrajectoryTeamContinuityEventRecord | None,
) -> TrajectoryTeamLaneReadback:
    binding_id = "" if binding is None else binding.binding_id
    worker_id = (
        ("" if ownership is None else ownership.worker_id)
        or ("" if binding is None else binding.worker_id)
        or ("" if event is None else event.worker_id)
    )
    return TrajectoryTeamLaneReadback(
        trajectory_id=request.trajectory_id,
        lane_id=lane_id,
        leader_id=request.leader_id or ("" if event is None else event.leader_id),
        worker_id=worker_id,
        runtime_provider="" if binding is None else binding.runtime_provider,
        binding_id=binding_id or ("" if event is None else event.binding_id),
        binding_status="" if binding is None else binding.lifecycle_status,
        ownership_id="" if ownership is None else ownership.ownership_id,
        ownership_status="" if ownership is None else ownership.status,
        compact_context_ref="" if binding is None else binding.compact_context_ref,
        mailbox_cursor_ref="" if binding is None else binding.mailbox_cursor_ref,
        worker_report_refs=() if binding is None else binding.worker_report_refs,
        audit_refs=() if binding is None else binding.audit_refs,
        active_lease_id="" if lease is None else lease.lease_id,
        active_lease_status="" if lease is None else lease.status,
        last_team_event_kind="" if event is None else event.event_kind,
        last_team_event_id="" if event is None else event.event_id,
        no_continuity_reason="" if event is None else event.no_continuity_reason,
    )


def _team_events(
    path: str,
    request: TrajectoryTeamContinuitySurfaceRequest,
) -> tuple[TrajectoryTeamContinuityEventRecord, ...]:
    events = JsonlTrajectoryTeamContinuityEventLog(path).read_all()
    filtered = tuple(
        event
        for event in events
        if (not request.trajectory_id or event.trajectory_id == request.trajectory_id)
        and (not request.lane_id or event.lane_id == request.lane_id)
    )
    return filtered


def _lane_ids(
    request: TrajectoryTeamContinuitySurfaceRequest,
    bindings: tuple[ContinuousWorkerBinding, ...],
    ownerships: tuple[LaneOwnership, ...],
    events: tuple[TrajectoryTeamContinuityEventRecord, ...],
) -> tuple[str, ...]:
    values: list[str] = []
    if request.lane_id:
        values.append(request.lane_id)
    for binding in bindings:
        values.extend(binding.lane_ids)
        if binding.scope_kind == "lane":
            values.append(binding.scope_id)
    for ownership in ownerships:
        values.extend(ownership.lane_ids)
        if ownership.scope_kind == "lane":
            values.append(ownership.scope_id)
    for event in events:
        values.append(event.lane_id)
    return _unique_nonempty(tuple(values))


def _binding_for_lane(
    lane_id: str,
    bindings: tuple[ContinuousWorkerBinding, ...],
) -> ContinuousWorkerBinding | None:
    for binding in bindings:
        if lane_id in binding.lane_ids or (
            binding.scope_kind == "lane" and binding.scope_id == lane_id
        ):
            return binding
    return None


def _ownership_for_lane(
    lane_id: str,
    ownerships: tuple[LaneOwnership, ...],
    binding: ContinuousWorkerBinding | None,
) -> LaneOwnership | None:
    binding_id = "" if binding is None else binding.binding_id
    for ownership in ownerships:
        if binding_id and ownership.binding_id != binding_id:
            continue
        if lane_id in ownership.lane_ids or (
            ownership.scope_kind == "lane" and ownership.scope_id == lane_id
        ):
            return ownership
    return None


def _active_lease_for_binding(
    binding_id: str,
    leases: tuple[DeliveryLease, ...],
) -> DeliveryLease | None:
    if not binding_id:
        return None
    for lease in leases:
        if lease.binding_id == binding_id:
            return lease
    return None


def _last_event_for_lane(
    lane_id: str,
    events: tuple[TrajectoryTeamContinuityEventRecord, ...],
) -> TrajectoryTeamContinuityEventRecord | None:
    matched = tuple(event for event in events if event.lane_id == lane_id)
    return matched[-1] if matched else None


def _session_selector(
    request: TrajectoryTeamContinuitySurfaceRequest,
) -> ContinuousWorkerSessionSelector | None:
    if not (request.attach_url or request.session_id):
        return None
    return ContinuousWorkerSessionSelector(
        provider=request.runtime_provider,  # type: ignore[arg-type]
        attach_url=request.attach_url,
        session_id=request.session_id,
        continue_session=request.continue_session,
        fork_session=request.fork_session,
    )


def _paths(request: TrajectoryTeamContinuitySurfaceRequest) -> dict[str, str]:
    root = Path(request.project_root)
    return {
        "binding_ledger_path": str(_resolve_path(root, request.binding_ledger_path)),
        "binding_event_log_path": str(_resolve_path(root, request.binding_event_log_path)),
        "ownership_ledger_path": str(_resolve_path(root, request.ownership_ledger_path)),
        "ownership_event_log_path": str(_resolve_path(root, request.ownership_event_log_path)),
        "lease_ledger_path": str(_resolve_path(root, request.lease_ledger_path)),
        "team_event_log_path": str(_resolve_path(root, request.team_event_log_path)),
        "scheduler_event_log_path": (
            ""
            if not request.scheduler_event_log_path
            else str(_resolve_path(root, request.scheduler_event_log_path))
        ),
    }


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else root / path


def _validate_action(action: str) -> None:
    if action not in READ_ONLY_ACTIONS and action not in MUTATING_ACTIONS:
        raise ValueError(f"unsupported trajectory team action: {action}")


def _rejected_worker_mutation(
    request: TrajectoryTeamContinuitySurfaceRequest,
) -> TrajectoryTeamContinuitySurfaceResult:
    message = (
        "trajectoryTeamContinuity mutating actions are leader/main/supervisor/"
        "guide authority. Workers and subagents must report requested "
        "trajectory-team changes through Subagent Report.trajectory_update or "
        f"mailbox/ExchangeArtifact feedback; see {WORKER_REPORT_PROCEDURE}."
    )
    return TrajectoryTeamContinuitySurfaceResult(
        ok=False,
        action=request.action,
        status="caller_role_rejected",
        message=message,
        trajectory_id=request.trajectory_id,
        lane_id=request.lane_id,
        errors=(message,),
    )


def _unique_nonempty(values: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return tuple(result)


__all__ = [
    "TrajectoryTeamCallerRole",
    "TrajectoryTeamContinuitySurfaceRequest",
    "TrajectoryTeamContinuitySurfaceResult",
    "TrajectoryTeamLaneReadback",
    "TrajectoryTeamSurfaceAction",
    "run_trajectory_team_continuity_surface",
]
