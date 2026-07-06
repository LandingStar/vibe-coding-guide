"""Recoverable leader/worker dispatcher tick over activation projection."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .artifact_paths import dbc_artifact_path
from .exchange_store import JsonArtifactVersionStore
from .leader_worker_activation import (
    AgentActivationEvent,
    AgentMailboxCursor,
    LeaderWorkerActivationResult,
    LeaderWorkerActivationState,
    run_leader_worker_activation_pass,
)
from .scheduler_store import recover_scheduler_state

LEADER_WORKER_DISPATCHER_STATE_SCHEMA_VERSION = "leader-worker-dispatcher-state.v1"
LEADER_WORKER_DISPATCHER_EVENT_LOG_SCHEMA_VERSION = "leader-worker-dispatcher-log.v1"
DEFAULT_LEADER_WORKER_DISPATCHER_STATE_RELATIVE_PATH = (
    dbc_artifact_path("scheduler", "leader-worker-dispatcher-state.json")
)
DEFAULT_LEADER_WORKER_DISPATCHER_EVENT_LOG_RELATIVE_PATH = (
    dbc_artifact_path("scheduler", "leader-worker-dispatcher-events.jsonl")
)

LeaderWorkerDispatcherLoopStopReason = Literal[
    "max_ticks_reached",
    "no_new_dispatch_decisions",
]


@dataclass(frozen=True, slots=True)
class LeaderWorkerDispatchDecision:
    """One idempotent dispatcher decision derived from an activation event."""

    decision_id: str
    source_key: str
    event_kind: str
    agent_id: str
    role: str
    next_action: str
    lane_id: str = ""
    task_id: str = ""
    source: str = ""
    reason: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "decision_id": self.decision_id,
            "source_key": self.source_key,
            "event_kind": self.event_kind,
            "agent_id": self.agent_id,
            "role": self.role,
            "next_action": self.next_action,
            "lane_id": self.lane_id,
            "task_id": self.task_id,
            "source": self.source,
            "reason": self.reason,
            "authority_split": {
                "dispatch_decision_only": True,
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class LeaderWorkerDispatcherState:
    """Durable dispatcher state for activation cursor and decision de-dup."""

    dispatcher_id: str = "leader-worker-dispatcher"
    trajectory_id: str = ""
    activation_state: LeaderWorkerActivationState = field(
        default_factory=LeaderWorkerActivationState
    )
    emitted_source_keys: tuple[str, ...] = ()
    tick_count: int = 0
    last_tick_id: str = ""
    last_tick_at: str = ""
    last_result_summary: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": LEADER_WORKER_DISPATCHER_STATE_SCHEMA_VERSION,
            "dispatcher_id": self.dispatcher_id,
            "trajectory_id": self.trajectory_id,
            "activation_state": self.activation_state.to_json_dict(),
            "emitted_source_keys": list(self.emitted_source_keys),
            "tick_count": self.tick_count,
            "last_tick_id": self.last_tick_id,
            "last_tick_at": self.last_tick_at,
            "last_result_summary": dict(self.last_result_summary),
            "metadata": dict(self.metadata),
            "authority_split": {
                "dispatcher_state_authority": "leader_worker_dispatcher_state_file",
                "activation_state_authority": "embedded_leader_worker_activation_state",
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class LeaderWorkerDispatcherTickRecord:
    """Append-only audit record for one dispatcher tick."""

    tick_id: str
    dispatcher_id: str
    timestamp: str
    scheduler_snapshot_path: str
    scheduler_event_log_path: str
    artifact_store_path: str
    recovery_event_count: int
    exchange_record_count: int
    decision_count: int
    suppressed_decision_count: int
    activation_event_count: int
    lifecycle_count: int
    decisions: tuple[LeaderWorkerDispatchDecision, ...] = ()
    policy: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": LEADER_WORKER_DISPATCHER_EVENT_LOG_SCHEMA_VERSION,
            "tick_id": self.tick_id,
            "dispatcher_id": self.dispatcher_id,
            "timestamp": self.timestamp,
            "scheduler_snapshot_path": self.scheduler_snapshot_path,
            "scheduler_event_log_path": self.scheduler_event_log_path,
            "artifact_store_path": self.artifact_store_path,
            "recovery_event_count": self.recovery_event_count,
            "exchange_record_count": self.exchange_record_count,
            "decision_count": self.decision_count,
            "suppressed_decision_count": self.suppressed_decision_count,
            "activation_event_count": self.activation_event_count,
            "lifecycle_count": self.lifecycle_count,
            "decisions": [decision.to_json_dict() for decision in self.decisions],
            "policy": dict(self.policy),
            "metadata": dict(self.metadata),
            "authority_split": {
                "dispatcher_log_authority": "leader_worker_dispatcher_event_log",
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class LeaderWorkerDispatcherTickRequest:
    """Request for one recoverable leader/worker dispatcher tick."""

    dispatcher_state_path: str | Path
    dispatch_event_log_path: str | Path
    scheduler_snapshot_path: str | Path
    scheduler_event_log_path: str | Path
    artifact_store_path: str | Path
    dispatcher_id: str = "leader-worker-dispatcher"
    trajectory_id: str = ""
    leader_agent_id: str = "agent:guide"
    worker_agent_ids: tuple[str, ...] = ()
    timestamp: str = ""
    strict_recovery: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LeaderWorkerDispatcherTickResult:
    """Result of one recoverable dispatcher tick."""

    request: LeaderWorkerDispatcherTickRequest
    state_before: LeaderWorkerDispatcherState
    state_after: LeaderWorkerDispatcherState
    activation: LeaderWorkerActivationResult
    tick_record: LeaderWorkerDispatcherTickRecord
    dispatch_event_log_path: Path
    dispatcher_state_path: Path

    @property
    def decisions(self) -> tuple[LeaderWorkerDispatchDecision, ...]:
        return self.tick_record.decisions

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": True,
            "dispatcher_state_path": str(self.dispatcher_state_path),
            "dispatch_event_log_path": str(self.dispatch_event_log_path),
            "dispatcher_id": self.state_after.dispatcher_id,
            "tick_id": self.tick_record.tick_id,
            "tick_count": self.state_after.tick_count,
            "decision_count": self.tick_record.decision_count,
            "suppressed_decision_count": self.tick_record.suppressed_decision_count,
            "decisions": [decision.to_json_dict() for decision in self.decisions],
            "activation": self.activation.to_json_dict(),
            "state_before": self.state_before.to_json_dict(),
            "state_after": self.state_after.to_json_dict(),
            "tick_record": self.tick_record.to_json_dict(),
            "authority_split": {
                "scheduler_state_authority": "scheduler_snapshot_and_event_log",
                "message_authority": "exchange_artifact_store",
                "dispatcher_state_authority": "leader_worker_dispatcher_state_file",
                "dispatcher_state_mutated": True,
                "dispatcher_log_mutated": True,
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class LeaderWorkerDispatcherLoopRequest:
    """Request for a bounded repeated dispatcher loop."""

    tick_request: LeaderWorkerDispatcherTickRequest
    max_ticks: int = 1


@dataclass(frozen=True, slots=True)
class LeaderWorkerDispatcherLoopResult:
    """Result of a bounded repeated dispatcher loop."""

    request: LeaderWorkerDispatcherLoopRequest
    iterations: tuple[LeaderWorkerDispatcherTickResult, ...]
    stop_reason: LeaderWorkerDispatcherLoopStopReason
    stop_detail: str = ""

    @property
    def tick_count(self) -> int:
        return len(self.iterations)

    @property
    def total_decision_count(self) -> int:
        return sum(iteration.tick_record.decision_count for iteration in self.iterations)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": True,
            "max_ticks": self.request.max_ticks,
            "tick_count": self.tick_count,
            "total_decision_count": self.total_decision_count,
            "stop_reason": self.stop_reason,
            "stop_detail": self.stop_detail,
            "iterations": [iteration.to_json_dict() for iteration in self.iterations],
            "authority_split": {
                "dispatcher_state_mutated": bool(self.iterations),
                "dispatcher_log_mutated": bool(self.iterations),
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


class JsonlLeaderWorkerDispatcherEventLog:
    """Append-only JSONL store for dispatcher tick records."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(
        self,
        record: LeaderWorkerDispatcherTickRecord,
    ) -> LeaderWorkerDispatcherTickRecord:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record.to_json_dict(), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return record

    def read_all(self) -> tuple[LeaderWorkerDispatcherTickRecord, ...]:
        if not self.path.exists():
            return ()
        records: list[LeaderWorkerDispatcherTickRecord] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    records.append(
                        leader_worker_dispatcher_tick_record_from_json_dict(
                            json.loads(stripped)
                        )
                    )
                except Exception as exc:
                    raise ValueError(
                        f"invalid leader-worker dispatcher log line {line_number} "
                        f"in {self.path}: {exc}"
                    ) from exc
        return tuple(records)


def run_leader_worker_dispatcher_tick(
    request: LeaderWorkerDispatcherTickRequest,
) -> LeaderWorkerDispatcherTickResult:
    """Run one recoverable dispatcher tick without running providers."""

    state_path = Path(request.dispatcher_state_path)
    log_path = Path(request.dispatch_event_log_path)
    state_before = read_leader_worker_dispatcher_state(state_path)
    if state_before is None:
        state_before = LeaderWorkerDispatcherState(
            dispatcher_id=request.dispatcher_id,
            trajectory_id=request.trajectory_id,
            activation_state=LeaderWorkerActivationState(
                trajectory_id=request.trajectory_id,
                leader_agent_id=request.leader_agent_id,
                worker_agent_ids=request.worker_agent_ids,
            ),
            metadata=dict(request.metadata),
        )

    recovery = recover_scheduler_state(
        request.scheduler_snapshot_path,
        request.scheduler_event_log_path,
        strict=request.strict_recovery,
    )
    exchange_records = _read_exchange_records(request.artifact_store_path)
    activation = run_leader_worker_activation_pass(
        scheduler_state=recovery.recovered_state,
        exchange_records=exchange_records,
        activation_state=state_before.activation_state,
        leader_agent_id=request.leader_agent_id,
        worker_agent_ids=request.worker_agent_ids,
        trajectory_id=request.trajectory_id,
    )
    tick_id = f"{state_before.dispatcher_id}:tick-{state_before.tick_count + 1:04d}"
    decisions, suppressed = _new_dispatch_decisions(
        activation.events,
        emitted_source_keys=state_before.emitted_source_keys,
        tick_id=tick_id,
    )
    state_after = LeaderWorkerDispatcherState(
        dispatcher_id=state_before.dispatcher_id,
        trajectory_id=state_before.trajectory_id or request.trajectory_id,
        activation_state=activation.next_state,
        emitted_source_keys=tuple(
            dict.fromkeys(
                (*state_before.emitted_source_keys, *(decision.source_key for decision in decisions))
            )
        ),
        tick_count=state_before.tick_count + 1,
        last_tick_id=tick_id,
        last_tick_at=request.timestamp,
        last_result_summary={
            "decision_count": len(decisions),
            "suppressed_decision_count": suppressed,
            "activation_event_count": len(activation.events),
            "has_runnable_agents": activation.has_runnable_agents,
            "leader_worker_required": activation.policy.leader_worker_required,
            "recovery_event_count": recovery.event_count,
            "exchange_record_count": len(exchange_records),
        },
        metadata=dict(state_before.metadata),
    )
    tick_record = LeaderWorkerDispatcherTickRecord(
        tick_id=tick_id,
        dispatcher_id=state_after.dispatcher_id,
        timestamp=request.timestamp,
        scheduler_snapshot_path=str(request.scheduler_snapshot_path),
        scheduler_event_log_path=str(request.scheduler_event_log_path),
        artifact_store_path=str(request.artifact_store_path),
        recovery_event_count=recovery.event_count,
        exchange_record_count=len(exchange_records),
        decision_count=len(decisions),
        suppressed_decision_count=suppressed,
        activation_event_count=len(activation.events),
        lifecycle_count=len(activation.lifecycles),
        decisions=decisions,
        policy=activation.policy.to_json_dict(),
        metadata=dict(request.metadata),
    )
    write_leader_worker_dispatcher_state(state_after, state_path)
    JsonlLeaderWorkerDispatcherEventLog(log_path).append(tick_record)
    return LeaderWorkerDispatcherTickResult(
        request=request,
        state_before=state_before,
        state_after=state_after,
        activation=activation,
        tick_record=tick_record,
        dispatch_event_log_path=log_path,
        dispatcher_state_path=state_path,
    )


def run_leader_worker_dispatcher_loop(
    request: LeaderWorkerDispatcherLoopRequest,
) -> LeaderWorkerDispatcherLoopResult:
    """Run a bounded dispatcher loop until no new decisions remain."""

    if request.max_ticks < 0:
        raise ValueError("leader-worker dispatcher loop max_ticks must be non-negative")
    iterations: list[LeaderWorkerDispatcherTickResult] = []
    stop_reason: LeaderWorkerDispatcherLoopStopReason = "max_ticks_reached"
    stop_detail = "max_ticks reached"
    for _ in range(request.max_ticks):
        tick = run_leader_worker_dispatcher_tick(request.tick_request)
        iterations.append(tick)
        if tick.tick_record.decision_count == 0:
            stop_reason = "no_new_dispatch_decisions"
            stop_detail = "dispatcher tick emitted no new decisions"
            break
    if request.max_ticks == 0:
        stop_detail = "max_ticks is 0"
    return LeaderWorkerDispatcherLoopResult(
        request=request,
        iterations=tuple(iterations),
        stop_reason=stop_reason,
        stop_detail=stop_detail,
    )


def read_leader_worker_dispatcher_state(
    path: str | Path,
) -> LeaderWorkerDispatcherState | None:
    source = Path(path)
    if not source.exists():
        return None
    return leader_worker_dispatcher_state_from_json_dict(
        json.loads(source.read_text(encoding="utf-8"))
    )


def write_leader_worker_dispatcher_state(
    state: LeaderWorkerDispatcherState,
    path: str | Path,
) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(state.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return target


def leader_worker_dispatcher_state_from_json_dict(
    payload: Mapping[str, Any],
) -> LeaderWorkerDispatcherState:
    if str(payload.get("schema_version", "")) != LEADER_WORKER_DISPATCHER_STATE_SCHEMA_VERSION:
        raise ValueError(
            "unsupported leader-worker dispatcher state version: "
            f"{payload.get('schema_version')!r}"
        )
    return LeaderWorkerDispatcherState(
        dispatcher_id=str(payload.get("dispatcher_id", "leader-worker-dispatcher")),
        trajectory_id=str(payload.get("trajectory_id", "")),
        activation_state=_activation_state_from_json_dict(
            _mapping(payload.get("activation_state"))
        ),
        emitted_source_keys=_str_tuple(payload.get("emitted_source_keys")),
        tick_count=int(payload.get("tick_count", 0) or 0),
        last_tick_id=str(payload.get("last_tick_id", "")),
        last_tick_at=str(payload.get("last_tick_at", "")),
        last_result_summary=dict(_mapping(payload.get("last_result_summary"))),
        metadata=dict(_mapping(payload.get("metadata"))),
    )


def leader_worker_dispatcher_tick_record_from_json_dict(
    payload: Mapping[str, Any],
) -> LeaderWorkerDispatcherTickRecord:
    if str(payload.get("schema_version", "")) != LEADER_WORKER_DISPATCHER_EVENT_LOG_SCHEMA_VERSION:
        raise ValueError(
            "unsupported leader-worker dispatcher log version: "
            f"{payload.get('schema_version')!r}"
        )
    decisions_payload = payload.get("decisions", ())
    if not isinstance(decisions_payload, list):
        raise ValueError("leader-worker dispatcher decisions must be a list")
    return LeaderWorkerDispatcherTickRecord(
        tick_id=str(payload.get("tick_id", "")),
        dispatcher_id=str(payload.get("dispatcher_id", "")),
        timestamp=str(payload.get("timestamp", "")),
        scheduler_snapshot_path=str(payload.get("scheduler_snapshot_path", "")),
        scheduler_event_log_path=str(payload.get("scheduler_event_log_path", "")),
        artifact_store_path=str(payload.get("artifact_store_path", "")),
        recovery_event_count=int(payload.get("recovery_event_count", 0) or 0),
        exchange_record_count=int(payload.get("exchange_record_count", 0) or 0),
        decision_count=int(payload.get("decision_count", 0) or 0),
        suppressed_decision_count=int(payload.get("suppressed_decision_count", 0) or 0),
        activation_event_count=int(payload.get("activation_event_count", 0) or 0),
        lifecycle_count=int(payload.get("lifecycle_count", 0) or 0),
        decisions=tuple(_dispatch_decision_from_json_dict(item) for item in decisions_payload),
        policy=dict(_mapping(payload.get("policy"))),
        metadata=dict(_mapping(payload.get("metadata"))),
    )


def _new_dispatch_decisions(
    events: Iterable[AgentActivationEvent],
    *,
    emitted_source_keys: tuple[str, ...],
    tick_id: str,
) -> tuple[tuple[LeaderWorkerDispatchDecision, ...], int]:
    emitted = set(emitted_source_keys)
    decisions: list[LeaderWorkerDispatchDecision] = []
    suppressed = 0
    for event in events:
        source_key = _dispatch_source_key(event)
        if source_key in emitted:
            suppressed += 1
            continue
        decisions.append(
            LeaderWorkerDispatchDecision(
                decision_id=f"{tick_id}:decision-{len(decisions) + 1:04d}",
                source_key=source_key,
                event_kind=event.event_kind,
                agent_id=event.agent_id,
                role=event.role,
                next_action=event.next_action,
                lane_id=event.lane_id,
                task_id=event.task_id,
                source=event.source,
                reason=event.reason,
            )
        )
    return tuple(decisions), suppressed


def _dispatch_source_key(event: AgentActivationEvent) -> str:
    return "|".join(
        (
            event.event_kind,
            event.agent_id,
            event.role,
            event.lane_id,
            event.task_id,
            event.source,
            event.next_action,
        )
    )


def _read_exchange_records(path: str | Path) -> tuple[object, ...]:
    source = Path(path)
    if not source.exists():
        return ()
    return JsonArtifactVersionStore(source).list_records()


def _activation_state_from_json_dict(payload: Mapping[str, Any]) -> LeaderWorkerActivationState:
    cursors_payload = payload.get("mailbox_cursors", {})
    cursors: dict[str, AgentMailboxCursor] = {}
    if isinstance(cursors_payload, Mapping):
        for agent_id, cursor_payload in cursors_payload.items():
            cursor_map = _mapping(cursor_payload)
            cursors[str(agent_id)] = AgentMailboxCursor(
                agent_id=str(cursor_map.get("agent_id", agent_id)),
                consumed_sources=_str_tuple(cursor_map.get("consumed_sources")),
            )
    return LeaderWorkerActivationState(
        trajectory_id=str(payload.get("trajectory_id", "")),
        leader_agent_id=str(payload.get("leader_agent_id", "agent:guide")),
        worker_agent_ids=_str_tuple(payload.get("worker_agent_ids")),
        mailbox_cursors=cursors,
    )


def _dispatch_decision_from_json_dict(payload: Mapping[str, Any]) -> LeaderWorkerDispatchDecision:
    return LeaderWorkerDispatchDecision(
        decision_id=str(payload.get("decision_id", "")),
        source_key=str(payload.get("source_key", "")),
        event_kind=str(payload.get("event_kind", "")),
        agent_id=str(payload.get("agent_id", "")),
        role=str(payload.get("role", "")),
        next_action=str(payload.get("next_action", "")),
        lane_id=str(payload.get("lane_id", "")),
        task_id=str(payload.get("task_id", "")),
        source=str(payload.get("source", "")),
        reason=str(payload.get("reason", "")),
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _str_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(str(item) for item in value)
