"""Host-owned delivery acknowledgement over leader/worker dispatch decisions."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

from .artifact_paths import dbc_artifact_path
from .leader_worker_dispatcher import (
    JsonlLeaderWorkerDispatcherEventLog,
    LeaderWorkerDispatchDecision,
)

LEADER_WORKER_DELIVERY_STATE_SCHEMA_VERSION = "leader-worker-delivery-state.v1"
LEADER_WORKER_DELIVERY_EVENT_LOG_SCHEMA_VERSION = "leader-worker-delivery-log.v1"
DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH = (
    dbc_artifact_path("scheduler", "leader-worker-delivery-state.json")
)
DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH = (
    dbc_artifact_path("scheduler", "leader-worker-delivery-events.jsonl")
)

LeaderWorkerDeliveryStatus = Literal[
    "pending",
    "delivered",
    "review_required",
    "acknowledged",
    "failed",
]

LeaderWorkerDeliveryAckTargetState = Literal[
    "delivered",
    "review_required",
    "acknowledged",
    "failed",
]

LeaderWorkerDeliveryEventKind = Literal[
    "pending_synced",
    "delivery_marked_delivered",
    "delivery_review_required",
    "delivery_acknowledged",
    "delivery_failed",
]


@dataclass(frozen=True, slots=True)
class LeaderWorkerDeliveryRecord:
    """One host-owned delivery state record for a dispatcher decision."""

    delivery_id: str
    source_key: str
    decision_id: str
    tick_id: str
    dispatcher_id: str
    event_kind: str
    agent_id: str
    role: str
    next_action: str
    lane_id: str = ""
    task_id: str = ""
    source: str = ""
    reason: str = ""
    delivery_state: LeaderWorkerDeliveryStatus = "pending"
    created_at: str = ""
    updated_at: str = ""
    delivered_at: str = ""
    review_required_at: str = ""
    acknowledged_at: str = ""
    failed_at: str = ""
    host_id: str = ""
    runtime_provider: str = ""
    runtime_session_id: str = ""
    runtime_run_id: str = ""
    invocation_id: str = ""
    delivery_attempt_count: int = 0
    failure_kind: str = ""
    failure_detail: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "delivery_id": self.delivery_id,
            "source_key": self.source_key,
            "decision_id": self.decision_id,
            "tick_id": self.tick_id,
            "dispatcher_id": self.dispatcher_id,
            "event_kind": self.event_kind,
            "agent_id": self.agent_id,
            "role": self.role,
            "next_action": self.next_action,
            "lane_id": self.lane_id,
            "task_id": self.task_id,
            "source": self.source,
            "reason": self.reason,
            "delivery_state": self.delivery_state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "delivered_at": self.delivered_at,
            "review_required_at": self.review_required_at,
            "acknowledged_at": self.acknowledged_at,
            "failed_at": self.failed_at,
            "host_id": self.host_id,
            "runtime_provider": self.runtime_provider,
            "runtime_session_id": self.runtime_session_id,
            "runtime_run_id": self.runtime_run_id,
            "invocation_id": self.invocation_id,
            "delivery_attempt_count": self.delivery_attempt_count,
            "failure_kind": self.failure_kind,
            "failure_detail": self.failure_detail,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class LeaderWorkerDeliveryState:
    """Durable host-owned delivery acknowledgement state."""

    delivery_id: str = "leader-worker-delivery"
    dispatcher_id: str = "leader-worker-dispatcher"
    records: Mapping[str, LeaderWorkerDeliveryRecord] = field(default_factory=dict)
    sync_count: int = 0
    last_sync_at: str = ""
    last_ack_at: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": LEADER_WORKER_DELIVERY_STATE_SCHEMA_VERSION,
            "delivery_id": self.delivery_id,
            "dispatcher_id": self.dispatcher_id,
            "records": [
                record.to_json_dict()
                for _, record in sorted(self.records.items(), key=lambda item: item[1].created_at)
            ],
            "sync_count": self.sync_count,
            "last_sync_at": self.last_sync_at,
            "last_ack_at": self.last_ack_at,
            "metadata": dict(self.metadata),
            "authority_split": {
                "delivery_state_authority": "leader_worker_delivery_state_file",
                "dispatcher_authority": "leader_worker_dispatcher_event_log",
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "dispatcher_state_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class LeaderWorkerDeliveryEventRecord:
    """Append-only audit record for one delivery state transition."""

    event_id: str
    event_kind: LeaderWorkerDeliveryEventKind
    timestamp: str
    delivery_id: str
    source_key: str
    decision_id: str
    tick_id: str
    dispatcher_id: str
    agent_id: str
    role: str
    previous_state: str
    next_state: str
    changed: bool
    host_id: str = ""
    runtime_provider: str = ""
    runtime_session_id: str = ""
    runtime_run_id: str = ""
    invocation_id: str = ""
    failure_kind: str = ""
    failure_detail: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": LEADER_WORKER_DELIVERY_EVENT_LOG_SCHEMA_VERSION,
            "event_id": self.event_id,
            "event_kind": self.event_kind,
            "timestamp": self.timestamp,
            "delivery_id": self.delivery_id,
            "source_key": self.source_key,
            "decision_id": self.decision_id,
            "tick_id": self.tick_id,
            "dispatcher_id": self.dispatcher_id,
            "agent_id": self.agent_id,
            "role": self.role,
            "previous_state": self.previous_state,
            "next_state": self.next_state,
            "changed": self.changed,
            "host_id": self.host_id,
            "runtime_provider": self.runtime_provider,
            "runtime_session_id": self.runtime_session_id,
            "runtime_run_id": self.runtime_run_id,
            "invocation_id": self.invocation_id,
            "failure_kind": self.failure_kind,
            "failure_detail": self.failure_detail,
            "metadata": dict(self.metadata),
            "authority_split": {
                "delivery_log_authority": "leader_worker_delivery_event_log",
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "dispatcher_state_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class LeaderWorkerDeliverySyncRequest:
    """Request to sync missing delivery records from dispatcher decisions."""

    delivery_state_path: str | Path
    delivery_event_log_path: str | Path
    dispatch_event_log_path: str | Path
    delivery_id: str = "leader-worker-delivery"
    dispatcher_id: str = "leader-worker-dispatcher"
    timestamp: str = ""
    host_id: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LeaderWorkerDeliverySyncResult:
    """Result of syncing dispatcher decisions into delivery state."""

    request: LeaderWorkerDeliverySyncRequest
    state_before: LeaderWorkerDeliveryState
    state_after: LeaderWorkerDeliveryState
    synced_records: tuple[LeaderWorkerDeliveryRecord, ...]
    existing_count: int
    event_records: tuple[LeaderWorkerDeliveryEventRecord, ...]
    delivery_state_path: Path
    delivery_event_log_path: Path
    dispatch_event_log_path: Path

    @property
    def synced_count(self) -> int:
        return len(self.synced_records)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": True,
            "delivery_state_path": str(self.delivery_state_path),
            "delivery_event_log_path": str(self.delivery_event_log_path),
            "dispatch_event_log_path": str(self.dispatch_event_log_path),
            "delivery_id": self.state_after.delivery_id,
            "dispatcher_id": self.state_after.dispatcher_id,
            "synced_count": self.synced_count,
            "existing_count": self.existing_count,
            "record_count": len(self.state_after.records),
            "state_counts": _state_counts(self.state_after.records.values()),
            "synced_records": [record.to_json_dict() for record in self.synced_records],
            "events": [event.to_json_dict() for event in self.event_records],
            "authority_split": {
                "delivery_state_mutated": self.state_before != self.state_after,
                "delivery_log_mutated": bool(self.event_records),
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "dispatcher_state_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class LeaderWorkerDeliveryAckRequest:
    """Request to mark one delivery record as delivered, acknowledged, or failed."""

    delivery_state_path: str | Path
    delivery_event_log_path: str | Path
    target_state: LeaderWorkerDeliveryAckTargetState
    source_key: str = ""
    delivery_record_id: str = ""
    timestamp: str = ""
    host_id: str = ""
    runtime_provider: str = ""
    runtime_session_id: str = ""
    runtime_run_id: str = ""
    invocation_id: str = ""
    failure_kind: str = ""
    failure_detail: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LeaderWorkerDeliveryAckResult:
    """Result of one host-owned delivery acknowledgement transition."""

    request: LeaderWorkerDeliveryAckRequest
    previous_record: LeaderWorkerDeliveryRecord
    record: LeaderWorkerDeliveryRecord
    event_record: LeaderWorkerDeliveryEventRecord
    delivery_state_path: Path
    delivery_event_log_path: Path

    @property
    def changed(self) -> bool:
        return self.previous_record != self.record

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": True,
            "delivery_state_path": str(self.delivery_state_path),
            "delivery_event_log_path": str(self.delivery_event_log_path),
            "changed": self.changed,
            "delivery_record": self.record.to_json_dict(),
            "previous_record": self.previous_record.to_json_dict(),
            "event": self.event_record.to_json_dict(),
            "authority_split": {
                "delivery_state_mutated": self.changed,
                "delivery_log_mutated": True,
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "dispatcher_state_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class LeaderWorkerDeliveryInspection:
    """Readback summary for leader/worker delivery state."""

    path: Path
    exists: bool
    record_count: int = 0
    state_counts: Mapping[str, int] = field(default_factory=dict)
    latest_records: tuple[LeaderWorkerDeliveryRecord, ...] = ()
    errors: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "exists": self.exists,
            "record_count": self.record_count,
            "state_counts": dict(self.state_counts),
            "latest_records": [record.to_json_dict() for record in self.latest_records],
            "errors": list(self.errors),
            "authority_split": {
                "read_model_only": True,
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "dispatcher_state_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


class JsonlLeaderWorkerDeliveryEventLog:
    """Append-only JSONL store for leader/worker delivery events."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(
        self,
        record: LeaderWorkerDeliveryEventRecord,
    ) -> LeaderWorkerDeliveryEventRecord:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record.to_json_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return record

    def read_all(self) -> tuple[LeaderWorkerDeliveryEventRecord, ...]:
        if not self.path.exists():
            return ()
        records: list[LeaderWorkerDeliveryEventRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(
                        leader_worker_delivery_event_record_from_json_dict(
                            json.loads(stripped)
                        )
                    )
                except Exception as exc:
                    raise ValueError(
                        f"invalid leader-worker delivery log line {line_number} "
                        f"in {self.path}: {exc}"
                    ) from exc
        return tuple(records)


def sync_leader_worker_delivery_from_dispatch_log(
    request: LeaderWorkerDeliverySyncRequest,
) -> LeaderWorkerDeliverySyncResult:
    """Create missing pending delivery records from dispatcher tick records."""

    state_path = Path(request.delivery_state_path)
    log_path = Path(request.delivery_event_log_path)
    dispatch_log_path = Path(request.dispatch_event_log_path)
    state_before = read_leader_worker_delivery_state(state_path)
    if state_before is None:
        state_before = LeaderWorkerDeliveryState(
            delivery_id=request.delivery_id,
            dispatcher_id=request.dispatcher_id,
            metadata=dict(request.metadata),
        )

    existing = dict(state_before.records)
    synced: list[LeaderWorkerDeliveryRecord] = []
    events: list[LeaderWorkerDeliveryEventRecord] = []
    existing_count = 0
    dispatcher_records = JsonlLeaderWorkerDispatcherEventLog(dispatch_log_path).read_all()
    existing_event_count = len(JsonlLeaderWorkerDeliveryEventLog(log_path).read_all())
    for dispatcher_record in dispatcher_records:
        for decision in dispatcher_record.decisions:
            if decision.source_key in existing:
                existing_count += 1
                continue
            delivery_record = _delivery_record_from_decision(
                decision,
                tick_id=dispatcher_record.tick_id,
                dispatcher_id=dispatcher_record.dispatcher_id,
                timestamp=request.timestamp,
                host_id=request.host_id,
                metadata=request.metadata,
            )
            existing[decision.source_key] = delivery_record
            synced.append(delivery_record)
            events.append(
                _event_from_record(
                    delivery_record,
                    event_kind="pending_synced",
                    event_index=existing_event_count + len(events) + 1,
                    timestamp=request.timestamp,
                    previous_state="",
                    changed=True,
                    host_id=request.host_id,
                    metadata=request.metadata,
                )
            )

    state_after = LeaderWorkerDeliveryState(
        delivery_id=state_before.delivery_id or request.delivery_id,
        dispatcher_id=state_before.dispatcher_id or request.dispatcher_id,
        records=existing,
        sync_count=state_before.sync_count + 1,
        last_sync_at=request.timestamp,
        last_ack_at=state_before.last_ack_at,
        metadata=dict(state_before.metadata),
    )
    write_leader_worker_delivery_state(state_after, state_path)
    event_log = JsonlLeaderWorkerDeliveryEventLog(log_path)
    for event in events:
        event_log.append(event)
    return LeaderWorkerDeliverySyncResult(
        request=request,
        state_before=state_before,
        state_after=state_after,
        synced_records=tuple(synced),
        existing_count=existing_count,
        event_records=tuple(events),
        delivery_state_path=state_path,
        delivery_event_log_path=log_path,
        dispatch_event_log_path=dispatch_log_path,
    )


def acknowledge_leader_worker_delivery(
    request: LeaderWorkerDeliveryAckRequest,
) -> LeaderWorkerDeliveryAckResult:
    """Mark one known delivery record as delivered, acknowledged, or failed."""

    state_path = Path(request.delivery_state_path)
    log_path = Path(request.delivery_event_log_path)
    state = read_leader_worker_delivery_state(state_path)
    if state is None:
        raise ValueError(f"leader-worker delivery state does not exist: {state_path}")
    if not request.source_key and not request.delivery_record_id:
        raise ValueError("leader-worker delivery acknowledgement requires source_key or delivery_id")

    source_key = request.source_key or _source_key_for_delivery_id(
        state.records,
        request.delivery_record_id,
    )
    if source_key not in state.records:
        raise ValueError(
            "leader-worker delivery acknowledgement target not found: "
            f"source_key={source_key!r}, delivery_id={request.delivery_record_id!r}"
        )
    previous = state.records[source_key]
    updated = _acknowledged_record(previous, request)
    records = dict(state.records)
    records[source_key] = updated
    state_after = replace(
        state,
        records=records,
        last_ack_at=request.timestamp,
    )
    write_leader_worker_delivery_state(state_after, state_path)
    event = _event_from_record(
        updated,
        event_kind=_event_kind_for_target_state(request.target_state),
        event_index=len(JsonlLeaderWorkerDeliveryEventLog(log_path).read_all()) + 1,
        timestamp=request.timestamp,
        previous_state=previous.delivery_state,
        changed=previous != updated,
        host_id=request.host_id or updated.host_id,
        runtime_provider=request.runtime_provider or updated.runtime_provider,
        runtime_session_id=request.runtime_session_id or updated.runtime_session_id,
        runtime_run_id=request.runtime_run_id or updated.runtime_run_id,
        invocation_id=request.invocation_id or updated.invocation_id,
        failure_kind=request.failure_kind or updated.failure_kind,
        failure_detail=request.failure_detail or updated.failure_detail,
        metadata=request.metadata,
    )
    JsonlLeaderWorkerDeliveryEventLog(log_path).append(event)
    return LeaderWorkerDeliveryAckResult(
        request=request,
        previous_record=previous,
        record=updated,
        event_record=event,
        delivery_state_path=state_path,
        delivery_event_log_path=log_path,
    )


def inspect_leader_worker_delivery_state(
    path: str | Path,
    *,
    latest_limit: int = 20,
) -> LeaderWorkerDeliveryInspection:
    """Read delivery acknowledgement state without mutation."""

    state_path = Path(path)
    if not state_path.exists():
        return LeaderWorkerDeliveryInspection(path=state_path, exists=False)
    try:
        state = read_leader_worker_delivery_state(state_path)
    except Exception as exc:
        return LeaderWorkerDeliveryInspection(path=state_path, exists=True, errors=(str(exc),))
    if state is None:
        return LeaderWorkerDeliveryInspection(path=state_path, exists=False)
    records = tuple(state.records.values())
    latest = records[-latest_limit:] if latest_limit >= 0 else records
    return LeaderWorkerDeliveryInspection(
        path=state_path,
        exists=True,
        record_count=len(records),
        state_counts=_state_counts(records),
        latest_records=tuple(latest),
    )


def read_leader_worker_delivery_state(
    path: str | Path,
) -> LeaderWorkerDeliveryState | None:
    source = Path(path)
    if not source.exists():
        return None
    return leader_worker_delivery_state_from_json_dict(
        json.loads(source.read_text(encoding="utf-8"))
    )


def write_leader_worker_delivery_state(
    state: LeaderWorkerDeliveryState,
    path: str | Path,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(state.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return target


def leader_worker_delivery_state_from_json_dict(
    payload: Mapping[str, Any],
) -> LeaderWorkerDeliveryState:
    if str(payload.get("schema_version", "")) != LEADER_WORKER_DELIVERY_STATE_SCHEMA_VERSION:
        raise ValueError(
            "unsupported leader-worker delivery state version: "
            f"{payload.get('schema_version')!r}"
        )
    records_payload = payload.get("records", ())
    if not isinstance(records_payload, list):
        raise ValueError("leader-worker delivery state records must be a list")
    records = tuple(
        leader_worker_delivery_record_from_json_dict(item)
        for item in records_payload
    )
    return LeaderWorkerDeliveryState(
        delivery_id=str(payload.get("delivery_id", "leader-worker-delivery")),
        dispatcher_id=str(payload.get("dispatcher_id", "leader-worker-dispatcher")),
        records={record.source_key: record for record in records},
        sync_count=int(payload.get("sync_count", 0) or 0),
        last_sync_at=str(payload.get("last_sync_at", "")),
        last_ack_at=str(payload.get("last_ack_at", "")),
        metadata=dict(_mapping(payload.get("metadata"))),
    )


def leader_worker_delivery_record_from_json_dict(
    payload: Mapping[str, Any],
) -> LeaderWorkerDeliveryRecord:
    return LeaderWorkerDeliveryRecord(
        delivery_id=str(payload.get("delivery_id", "")),
        source_key=str(payload.get("source_key", "")),
        decision_id=str(payload.get("decision_id", "")),
        tick_id=str(payload.get("tick_id", "")),
        dispatcher_id=str(payload.get("dispatcher_id", "")),
        event_kind=str(payload.get("event_kind", "")),
        agent_id=str(payload.get("agent_id", "")),
        role=str(payload.get("role", "")),
        next_action=str(payload.get("next_action", "")),
        lane_id=str(payload.get("lane_id", "")),
        task_id=str(payload.get("task_id", "")),
        source=str(payload.get("source", "")),
        reason=str(payload.get("reason", "")),
        delivery_state=str(payload.get("delivery_state", "pending")),  # type: ignore[arg-type]
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        delivered_at=str(payload.get("delivered_at", "")),
        review_required_at=str(payload.get("review_required_at", "")),
        acknowledged_at=str(payload.get("acknowledged_at", "")),
        failed_at=str(payload.get("failed_at", "")),
        host_id=str(payload.get("host_id", "")),
        runtime_provider=str(payload.get("runtime_provider", "")),
        runtime_session_id=str(payload.get("runtime_session_id", "")),
        runtime_run_id=str(payload.get("runtime_run_id", "")),
        invocation_id=str(payload.get("invocation_id", "")),
        delivery_attempt_count=int(payload.get("delivery_attempt_count", 0) or 0),
        failure_kind=str(payload.get("failure_kind", "")),
        failure_detail=str(payload.get("failure_detail", "")),
        metadata=dict(_mapping(payload.get("metadata"))),
    )


def leader_worker_delivery_event_record_from_json_dict(
    payload: Mapping[str, Any],
) -> LeaderWorkerDeliveryEventRecord:
    if str(payload.get("schema_version", "")) != LEADER_WORKER_DELIVERY_EVENT_LOG_SCHEMA_VERSION:
        raise ValueError(
            "unsupported leader-worker delivery log version: "
            f"{payload.get('schema_version')!r}"
        )
    return LeaderWorkerDeliveryEventRecord(
        event_id=str(payload.get("event_id", "")),
        event_kind=str(payload.get("event_kind", "pending_synced")),  # type: ignore[arg-type]
        timestamp=str(payload.get("timestamp", "")),
        delivery_id=str(payload.get("delivery_id", "")),
        source_key=str(payload.get("source_key", "")),
        decision_id=str(payload.get("decision_id", "")),
        tick_id=str(payload.get("tick_id", "")),
        dispatcher_id=str(payload.get("dispatcher_id", "")),
        agent_id=str(payload.get("agent_id", "")),
        role=str(payload.get("role", "")),
        previous_state=str(payload.get("previous_state", "")),
        next_state=str(payload.get("next_state", "")),
        changed=bool(payload.get("changed", False)),
        host_id=str(payload.get("host_id", "")),
        runtime_provider=str(payload.get("runtime_provider", "")),
        runtime_session_id=str(payload.get("runtime_session_id", "")),
        runtime_run_id=str(payload.get("runtime_run_id", "")),
        invocation_id=str(payload.get("invocation_id", "")),
        failure_kind=str(payload.get("failure_kind", "")),
        failure_detail=str(payload.get("failure_detail", "")),
        metadata=dict(_mapping(payload.get("metadata"))),
    )


def _delivery_record_from_decision(
    decision: LeaderWorkerDispatchDecision,
    *,
    tick_id: str,
    dispatcher_id: str,
    timestamp: str,
    host_id: str,
    metadata: Mapping[str, object],
) -> LeaderWorkerDeliveryRecord:
    return LeaderWorkerDeliveryRecord(
        delivery_id=f"delivery:{hashlib.sha1(decision.source_key.encode('utf-8')).hexdigest()[:12]}",
        source_key=decision.source_key,
        decision_id=decision.decision_id,
        tick_id=tick_id,
        dispatcher_id=dispatcher_id,
        event_kind=decision.event_kind,
        agent_id=decision.agent_id,
        role=decision.role,
        next_action=decision.next_action,
        lane_id=decision.lane_id,
        task_id=decision.task_id,
        source=decision.source,
        reason=decision.reason,
        delivery_state="pending",
        created_at=timestamp,
        updated_at=timestamp,
        host_id=host_id,
        metadata=dict(metadata),
    )


def _acknowledged_record(
    record: LeaderWorkerDeliveryRecord,
    request: LeaderWorkerDeliveryAckRequest,
) -> LeaderWorkerDeliveryRecord:
    host_id = request.host_id or record.host_id
    runtime_provider = request.runtime_provider or record.runtime_provider
    runtime_session_id = request.runtime_session_id or record.runtime_session_id
    runtime_run_id = request.runtime_run_id or record.runtime_run_id
    invocation_id = request.invocation_id or record.invocation_id
    attempt_count = record.delivery_attempt_count
    delivered_at = record.delivered_at
    review_required_at = record.review_required_at
    acknowledged_at = record.acknowledged_at
    failed_at = record.failed_at
    failure_kind = record.failure_kind
    failure_detail = record.failure_detail

    if request.target_state == "delivered":
        attempt_count += 1
        delivered_at = request.timestamp or delivered_at
        failure_kind = ""
        failure_detail = ""
    elif request.target_state == "review_required":
        if not delivered_at:
            delivered_at = request.timestamp
        attempt_count += 1
        review_required_at = request.timestamp or review_required_at
        failure_kind = ""
        failure_detail = ""
    elif request.target_state == "acknowledged":
        if not delivered_at:
            delivered_at = request.timestamp
            attempt_count += 1
        acknowledged_at = request.timestamp or acknowledged_at
        failure_kind = ""
        failure_detail = ""
    elif request.target_state == "failed":
        attempt_count += 1
        failed_at = request.timestamp or failed_at
        failure_kind = request.failure_kind or failure_kind
        failure_detail = request.failure_detail or failure_detail
    else:
        raise ValueError(f"unsupported leader-worker delivery target state: {request.target_state!r}")

    return replace(
        record,
        delivery_state=request.target_state,
        updated_at=request.timestamp or record.updated_at,
        delivered_at=delivered_at,
        review_required_at=review_required_at,
        acknowledged_at=acknowledged_at,
        failed_at=failed_at,
        host_id=host_id,
        runtime_provider=runtime_provider,
        runtime_session_id=runtime_session_id,
        runtime_run_id=runtime_run_id,
        invocation_id=invocation_id,
        delivery_attempt_count=attempt_count,
        failure_kind=failure_kind,
        failure_detail=failure_detail,
        metadata={**dict(record.metadata), **dict(request.metadata)},
    )


def _event_from_record(
    record: LeaderWorkerDeliveryRecord,
    *,
    event_kind: LeaderWorkerDeliveryEventKind,
    event_index: int,
    timestamp: str,
    previous_state: str,
    changed: bool,
    host_id: str = "",
    runtime_provider: str = "",
    runtime_session_id: str = "",
    runtime_run_id: str = "",
    invocation_id: str = "",
    failure_kind: str = "",
    failure_detail: str = "",
    metadata: Mapping[str, object] | None = None,
) -> LeaderWorkerDeliveryEventRecord:
    return LeaderWorkerDeliveryEventRecord(
        event_id=f"leader-worker-delivery:event-{event_index:04d}",
        event_kind=event_kind,
        timestamp=timestamp,
        delivery_id=record.delivery_id,
        source_key=record.source_key,
        decision_id=record.decision_id,
        tick_id=record.tick_id,
        dispatcher_id=record.dispatcher_id,
        agent_id=record.agent_id,
        role=record.role,
        previous_state=previous_state,
        next_state=record.delivery_state,
        changed=changed,
        host_id=host_id or record.host_id,
        runtime_provider=runtime_provider or record.runtime_provider,
        runtime_session_id=runtime_session_id or record.runtime_session_id,
        runtime_run_id=runtime_run_id or record.runtime_run_id,
        invocation_id=invocation_id or record.invocation_id,
        failure_kind=failure_kind or record.failure_kind,
        failure_detail=failure_detail or record.failure_detail,
        metadata=dict(metadata or {}),
    )


def _event_kind_for_target_state(
    target_state: LeaderWorkerDeliveryAckTargetState,
) -> LeaderWorkerDeliveryEventKind:
    if target_state == "delivered":
        return "delivery_marked_delivered"
    if target_state == "review_required":
        return "delivery_review_required"
    if target_state == "acknowledged":
        return "delivery_acknowledged"
    if target_state == "failed":
        return "delivery_failed"
    raise ValueError(f"unsupported leader-worker delivery target state: {target_state!r}")


def _source_key_for_delivery_id(
    records: Mapping[str, LeaderWorkerDeliveryRecord],
    delivery_record_id: str,
) -> str:
    for source_key, record in records.items():
        if record.delivery_id == delivery_record_id:
            return source_key
    return ""


def _state_counts(records: object) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:  # type: ignore[assignment]
        state = getattr(record, "delivery_state", "")
        counts[state] = counts.get(state, 0) + 1
    return dict(sorted(counts.items()))


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
