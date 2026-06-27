"""Leader/worker activation projection over scheduler and exchange state."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from typing import Literal

from .exchange_store import ArtifactVersionRecord
from .scheduler import SchedulerState

AgentLifecycleState = Literal[
    "idle",
    "runnable",
    "running",
    "waiting_message",
    "waiting_dependency",
    "waiting_review",
    "blocked",
    "stopped",
]

AgentActivationEventKind = Literal[
    "message_available",
    "task_ready",
    "dependency_wait",
    "blocked",
    "leader_required",
    "leader_recommended",
]

AgentActivationNextAction = Literal[
    "run_agent",
    "inspect_message",
    "wait",
    "resolve_blocker",
]


@dataclass(frozen=True, slots=True)
class AgentMailboxCursor:
    """Per-agent consumed mailbox position."""

    agent_id: str
    consumed_sources: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "agent_id": self.agent_id,
            "consumed_sources": list(self.consumed_sources),
        }


@dataclass(frozen=True, slots=True)
class AgentLifecycleRecord:
    """Projected lifecycle state for one leader or worker agent."""

    agent_id: str
    role: str
    lifecycle_state: AgentLifecycleState
    lane_ids: tuple[str, ...] = ()
    ready_task_ids: tuple[str, ...] = ()
    waiting_task_ids: tuple[str, ...] = ()
    blocked_task_ids: tuple[str, ...] = ()
    new_message_sources: tuple[str, ...] = ()
    reason: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "lifecycle_state": self.lifecycle_state,
            "lane_ids": list(self.lane_ids),
            "ready_task_ids": list(self.ready_task_ids),
            "waiting_task_ids": list(self.waiting_task_ids),
            "blocked_task_ids": list(self.blocked_task_ids),
            "new_message_sources": list(self.new_message_sources),
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class AgentActivationEvent:
    """One activation clue for an agent."""

    event_id: str
    event_kind: AgentActivationEventKind
    agent_id: str
    role: str
    lane_id: str = ""
    task_id: str = ""
    source: str = ""
    reason: str = ""
    next_action: AgentActivationNextAction = "wait"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "event_kind": self.event_kind,
            "agent_id": self.agent_id,
            "role": self.role,
            "lane_id": self.lane_id,
            "task_id": self.task_id,
            "source": self.source,
            "reason": self.reason,
            "next_action": self.next_action,
        }


@dataclass(frozen=True, slots=True)
class LeaderWorkerActivationState:
    """Persistent activation state owned by the activation loop."""

    trajectory_id: str = ""
    leader_agent_id: str = "agent:guide"
    worker_agent_ids: tuple[str, ...] = ()
    mailbox_cursors: Mapping[str, AgentMailboxCursor] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "leader_agent_id": self.leader_agent_id,
            "worker_agent_ids": list(self.worker_agent_ids),
            "mailbox_cursors": {
                agent_id: cursor.to_json_dict()
                for agent_id, cursor in sorted(self.mailbox_cursors.items())
            },
        }


@dataclass(frozen=True, slots=True)
class LeaderWorkerActivationPolicy:
    """Policy for leader-worker use in local work."""

    lane_count: int
    leader_worker_recommended: bool
    leader_worker_required: bool
    reason: str

    def to_json_dict(self) -> dict[str, object]:
        return {
            "lane_count": self.lane_count,
            "leader_worker_recommended": self.leader_worker_recommended,
            "leader_worker_required": self.leader_worker_required,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class LeaderWorkerActivationResult:
    """Result of one deterministic activation pass."""

    previous_state: LeaderWorkerActivationState
    next_state: LeaderWorkerActivationState
    policy: LeaderWorkerActivationPolicy
    lifecycles: tuple[AgentLifecycleRecord, ...]
    events: tuple[AgentActivationEvent, ...]

    @property
    def has_runnable_agents(self) -> bool:
        return any(item.lifecycle_state == "runnable" for item in self.lifecycles)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "previous_state": self.previous_state.to_json_dict(),
            "next_state": self.next_state.to_json_dict(),
            "policy": self.policy.to_json_dict(),
            "has_runnable_agents": self.has_runnable_agents,
            "lifecycles": [item.to_json_dict() for item in self.lifecycles],
            "events": [event.to_json_dict() for event in self.events],
            "authority_split": {
                "task_lifecycle_authority": "scheduler_snapshot_and_event_log",
                "message_authority": "exchange_artifact_store",
                "activation_state_authority": "leader_worker_activation_state",
                "read_model_only": True,
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


def evaluate_leader_worker_policy(lane_ids: Iterable[str]) -> LeaderWorkerActivationPolicy:
    """Return leader-worker policy for the current lane set."""

    lanes = tuple(dict.fromkeys(lane_id for lane_id in lane_ids if lane_id))
    lane_count = len(lanes)
    if lane_count >= 2:
        return LeaderWorkerActivationPolicy(
            lane_count=lane_count,
            leader_worker_recommended=True,
            leader_worker_required=True,
            reason="multi-lane local work requires leader-worker coordination",
        )
    return LeaderWorkerActivationPolicy(
        lane_count=lane_count,
        leader_worker_recommended=lane_count == 1,
        leader_worker_required=False,
        reason=(
            "single-lane local work recommends leader-worker coordination"
            if lane_count == 1
            else "no active lane detected"
        ),
    )


def run_leader_worker_activation_pass(
    *,
    scheduler_state: SchedulerState,
    exchange_records: Iterable[ArtifactVersionRecord],
    activation_state: LeaderWorkerActivationState | None = None,
    leader_agent_id: str = "agent:guide",
    worker_agent_ids: tuple[str, ...] = (),
    trajectory_id: str = "",
) -> LeaderWorkerActivationResult:
    """Project one activation pass without running providers or mutating inputs."""

    state = activation_state or LeaderWorkerActivationState(
        trajectory_id=trajectory_id,
        leader_agent_id=leader_agent_id,
        worker_agent_ids=worker_agent_ids,
    )
    leader_id = state.leader_agent_id or leader_agent_id
    workers = tuple(dict.fromkeys((*state.worker_agent_ids, *worker_agent_ids)))
    task_lane_ids = tuple(
        task.context_scope.lane_id
        for task in scheduler_state.tasks.values()
        if task.context_scope.lane_id
    )
    policy = evaluate_leader_worker_policy(task_lane_ids)

    records = tuple(exchange_records)
    agents = tuple(dict.fromkeys((leader_id, *workers, *_agents_from_tasks(scheduler_state))))
    events: list[AgentActivationEvent] = []
    lifecycles: list[AgentLifecycleRecord] = []
    next_cursors: dict[str, AgentMailboxCursor] = dict(state.mailbox_cursors)

    for agent_id in agents:
        role = "leader" if agent_id == leader_id else "worker"
        cursor = next_cursors.get(agent_id, AgentMailboxCursor(agent_id=agent_id))
        consumed = set(cursor.consumed_sources)
        new_sources = tuple(
            source for source in _new_message_sources(records, agent_id) if source not in consumed
        )
        task_summary = _task_summary_for_agent(scheduler_state, agent_id)
        lifecycle_state, reason = _lifecycle_for_agent(
            new_sources=new_sources,
            ready_task_ids=task_summary["ready"],
            waiting_task_ids=task_summary["waiting"],
            blocked_task_ids=task_summary["blocked"],
        )
        lifecycles.append(
            AgentLifecycleRecord(
                agent_id=agent_id,
                role=role,
                lifecycle_state=lifecycle_state,
                lane_ids=task_summary["lanes"],
                ready_task_ids=task_summary["ready"],
                waiting_task_ids=task_summary["waiting"],
                blocked_task_ids=task_summary["blocked"],
                new_message_sources=new_sources,
                reason=reason,
            )
        )
        if new_sources:
            for source in new_sources:
                events.append(
                    AgentActivationEvent(
                        event_id=f"activation:{len(events) + 1:04d}",
                        event_kind="message_available",
                        agent_id=agent_id,
                        role=role,
                        source=source,
                        reason="new addressed exchange artifact is available",
                        next_action="inspect_message",
                    )
                )
            next_cursors[agent_id] = replace(
                cursor,
                consumed_sources=tuple(dict.fromkeys((*cursor.consumed_sources, *new_sources))),
            )
        for task_id in task_summary["ready"]:
            task = scheduler_state.tasks[task_id]
            events.append(
                AgentActivationEvent(
                    event_id=f"activation:{len(events) + 1:04d}",
                    event_kind="task_ready",
                    agent_id=agent_id,
                    role=role,
                    lane_id=task.context_scope.lane_id,
                    task_id=task_id,
                    reason="scheduler task is ready",
                    next_action="run_agent",
                )
            )
        for task_id in task_summary["waiting"]:
            task = scheduler_state.tasks[task_id]
            events.append(
                AgentActivationEvent(
                    event_id=f"activation:{len(events) + 1:04d}",
                    event_kind="dependency_wait",
                    agent_id=agent_id,
                    role=role,
                    lane_id=task.context_scope.lane_id,
                    task_id=task_id,
                    reason=task.blocked_reason or "scheduler task is waiting",
                    next_action="wait",
                )
            )
        for task_id in task_summary["blocked"]:
            task = scheduler_state.tasks[task_id]
            events.append(
                AgentActivationEvent(
                    event_id=f"activation:{len(events) + 1:04d}",
                    event_kind="blocked",
                    agent_id=agent_id,
                    role=role,
                    lane_id=task.context_scope.lane_id,
                    task_id=task_id,
                    reason=task.blocked_reason or "scheduler task is blocked",
                    next_action="resolve_blocker",
                )
            )

    if policy.leader_worker_required:
        events.insert(
            0,
            AgentActivationEvent(
                event_id="activation:policy",
                event_kind="leader_required",
                agent_id=leader_id,
                role="leader",
                reason=policy.reason,
                next_action="wait",
            ),
        )
    elif policy.leader_worker_recommended:
        events.insert(
            0,
            AgentActivationEvent(
                event_id="activation:policy",
                event_kind="leader_recommended",
                agent_id=leader_id,
                role="leader",
                reason=policy.reason,
                next_action="wait",
            ),
        )

    next_state = LeaderWorkerActivationState(
        trajectory_id=state.trajectory_id or trajectory_id,
        leader_agent_id=leader_id,
        worker_agent_ids=workers,
        mailbox_cursors=next_cursors,
    )
    return LeaderWorkerActivationResult(
        previous_state=state,
        next_state=next_state,
        policy=policy,
        lifecycles=tuple(lifecycles),
        events=tuple(events),
    )


def _agents_from_tasks(state: SchedulerState) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            task.agent.agent_id
            for task in state.tasks.values()
            if task.agent.agent_id
        )
    )


def _new_message_sources(records: tuple[ArtifactVersionRecord, ...], agent_id: str) -> tuple[str, ...]:
    sources: list[str] = []
    for record in records:
        artifact = record.artifact
        if artifact.lifecycle_state == "archived":
            continue
        if agent_id not in artifact.audience and agent_id not in artifact.visibility_policy.audience:
            continue
        sources.append(f"{record.artifact_id}@{record.version}")
    return tuple(sources)


def _task_summary_for_agent(state: SchedulerState, agent_id: str) -> dict[str, tuple[str, ...]]:
    ready: list[str] = []
    waiting: list[str] = []
    blocked: list[str] = []
    lanes: list[str] = []
    for task_id, task in sorted(state.tasks.items()):
        if task.agent.agent_id != agent_id:
            continue
        if task.context_scope.lane_id:
            lanes.append(task.context_scope.lane_id)
        if task.state == "ready":
            ready.append(task_id)
        elif task.state in {"waiting", "review_required"}:
            waiting.append(task_id)
        elif task.state == "blocked":
            blocked.append(task_id)
    return {
        "ready": tuple(ready),
        "waiting": tuple(waiting),
        "blocked": tuple(blocked),
        "lanes": tuple(dict.fromkeys(lanes)),
    }


def _lifecycle_for_agent(
    *,
    new_sources: tuple[str, ...],
    ready_task_ids: tuple[str, ...],
    waiting_task_ids: tuple[str, ...],
    blocked_task_ids: tuple[str, ...],
) -> tuple[AgentLifecycleState, str]:
    if blocked_task_ids:
        return "blocked", "one or more tasks are blocked"
    if new_sources or ready_task_ids:
        return "runnable", "new message or ready task is available"
    if waiting_task_ids:
        return "waiting_dependency", "tasks are waiting for dependencies or review"
    return "waiting_message", "no ready task or new message"
