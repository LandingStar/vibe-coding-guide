"""Persistence helpers for scheduler state snapshots."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from .exchange import ExchangeReference
from .runtime_adapter import AgentSpec
from .scheduler import (
    ContextScope,
    EditScopeLease,
    SandboxProfile,
    ScheduledTask,
    ScheduledTaskState,
    SchedulerEvent,
    SchedulerMergeGate,
    SchedulerMergeGateEvent,
    SchedulerState,
    TaskDependency,
    TaskRunRecord,
)

SCHEDULER_STATE_SNAPSHOT_VERSION = "1"


@dataclass(frozen=True, slots=True)
class SchedulerRecoveryResult:
    """Recovered scheduler state plus the inputs used to derive it."""

    snapshot_path: Path
    event_log_path: Path
    strict: bool
    baseline_state: SchedulerState
    events: tuple[SchedulerEvent, ...]
    recovered_state: SchedulerState

    @property
    def event_count(self) -> int:
        """Return the number of replayed scheduler events."""

        return len(self.events)


@dataclass(frozen=True, slots=True)
class SchedulerCompactionResult:
    """Result of writing a recovered state into a compacted snapshot."""

    recovery: SchedulerRecoveryResult
    compacted_snapshot_path: Path
    archived_event_log_path: Path | None = None
    archive_requested: bool = False
    reset_event_log_requested: bool = False
    archived_event_count: int = 0
    active_event_count_after_compaction: int = 0
    event_log_truncated: bool = False

    @property
    def compacted_state(self) -> SchedulerState:
        """Return the recovered state persisted into the compacted snapshot."""

        return self.recovery.recovered_state

    @property
    def event_count(self) -> int:
        """Return the number of events represented by the compacted snapshot."""

        return self.recovery.event_count

    @property
    def replay_boundary_summary(self) -> dict[str, object]:
        """Return compact clues about the post-compaction replay boundary."""

        return {
            "snapshot_path": str(self.recovery.snapshot_path),
            "event_log_path": str(self.recovery.event_log_path),
            "compacted_snapshot_path": str(self.compacted_snapshot_path),
            "archived_event_log_path": (
                str(self.archived_event_log_path)
                if self.archived_event_log_path is not None
                else ""
            ),
            "strict": self.recovery.strict,
            "compacted_event_count": self.event_count,
            "archived_event_count": self.archived_event_count,
            "active_event_count_after_compaction": self.active_event_count_after_compaction,
            "archive_requested": self.archive_requested,
            "reset_event_log_requested": self.reset_event_log_requested,
            "event_log_truncated": self.event_log_truncated,
        }


class JsonlSchedulerEventLog:
    """Append-only JSONL scheduler event log."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, event: SchedulerEvent) -> SchedulerEvent:
        """Append one scheduler event."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(_scheduler_event_to_json(event), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return event

    def write_all(self, events: tuple[SchedulerEvent, ...]) -> Path:
        """Replace this log with exactly the provided events."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8", newline="\n") as handle:
            for event in events:
                handle.write(json.dumps(_scheduler_event_to_json(event), ensure_ascii=False, sort_keys=True))
                handle.write("\n")
        return self.path

    def clear(self) -> Path:
        """Reset this event log to an empty post-compaction boundary."""

        return self.write_all(())

    def read_all(self) -> tuple[SchedulerEvent, ...]:
        """Read all scheduler events from this log."""

        if not self.path.exists():
            return ()

        events: list[SchedulerEvent] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid scheduler event JSONL at {self.path}:{line_number}: {exc.msg}"
                    ) from exc
                events.append(_scheduler_event_from_json(payload))
        return tuple(events)


class JsonlSchedulerMergeGateEventLog:
    """Append-only JSONL scheduler merge-gate event log."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, event: SchedulerMergeGateEvent) -> SchedulerMergeGateEvent:
        """Append one scheduler merge-gate event."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(_merge_gate_event_to_json(event), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return event

    def read_all(self) -> tuple[SchedulerMergeGateEvent, ...]:
        """Read all scheduler merge-gate events from this log."""

        if not self.path.exists():
            return ()

        events: list[SchedulerMergeGateEvent] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid scheduler merge-gate event JSONL at {self.path}:{line_number}: {exc.msg}"
                    ) from exc
                events.append(_merge_gate_event_from_json(payload))
        return tuple(events)


def write_scheduler_state_snapshot(state: SchedulerState, path: str | Path) -> Path:
    """Write scheduler state as a versioned JSON snapshot."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEDULER_STATE_SNAPSHOT_VERSION,
        "tasks": [_scheduled_task_to_json(task) for task in state.tasks.values()],
        "dependencies": [_dependency_to_json(dependency) for dependency in state.dependencies],
        "run_records": [_run_record_to_json(record) for record in state.run_records],
        "merge_gates": [_merge_gate_to_json(gate) for gate in state.merge_gates],
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return target


def read_scheduler_state_snapshot(path: str | Path) -> SchedulerState:
    """Read a scheduler state JSON snapshot."""

    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if str(payload.get("schema_version", "")) != SCHEDULER_STATE_SNAPSHOT_VERSION:
        raise ValueError(
            f"unsupported scheduler state snapshot version: {payload.get('schema_version')!r}"
        )

    tasks = {
        task.task_id: task
        for task in (_scheduled_task_from_json(item) for item in payload.get("tasks", ()))
    }
    dependencies = tuple(
        _dependency_from_json(item)
        for item in payload.get("dependencies", ())
    )
    run_records = tuple(
        _run_record_from_json(item)
        for item in payload.get("run_records", ())
    )
    merge_gates = tuple(
        _merge_gate_from_json(item)
        for item in payload.get("merge_gates", ())
    )
    return SchedulerState(
        tasks=tasks,
        dependencies=dependencies,
        run_records=run_records,
        merge_gates=merge_gates,
    )


def recover_scheduler_state(
    snapshot_path: str | Path,
    event_log_path: str | Path,
    *,
    strict: bool = True,
) -> SchedulerRecoveryResult:
    """Recover scheduler state from a baseline snapshot and JSONL event log.

    The snapshot remains the task-contract authority. Events only replay
    lifecycle and run-reference changes for tasks already present in that
    snapshot, matching ``replay_scheduler_events()`` semantics.
    """

    baseline = read_scheduler_state_snapshot(snapshot_path)
    event_log = JsonlSchedulerEventLog(event_log_path)
    events = event_log.read_all()
    recovered = replay_scheduler_events(baseline, events, strict=strict)
    return SchedulerRecoveryResult(
        snapshot_path=Path(snapshot_path),
        event_log_path=Path(event_log_path),
        strict=strict,
        baseline_state=baseline,
        events=events,
        recovered_state=recovered,
    )


def write_compacted_scheduler_snapshot(
    snapshot_path: str | Path,
    event_log_path: str | Path,
    compacted_snapshot_path: str | Path,
    *,
    strict: bool = True,
    archive_event_log_path: str | Path | None = None,
    reset_event_log: bool = False,
) -> SchedulerCompactionResult:
    """Write a recovered scheduler state into a new compacted snapshot.

    The default remains non-destructive for existing callers. When
    ``archive_event_log_path`` is provided, all events represented by the
    compacted snapshot are copied to that archive path. When ``reset_event_log``
    is true, the active event log is then reset to an empty post-compaction
    replay boundary after the compacted snapshot and archive have both been
    written.
    """

    if reset_event_log and archive_event_log_path is None:
        raise ValueError(
            "reset_event_log requires archive_event_log_path so compacted "
            "scheduler history is preserved before the active log is reset"
        )

    recovery = recover_scheduler_state(
        snapshot_path,
        event_log_path,
        strict=strict,
    )
    written = write_scheduler_state_snapshot(
        recovery.recovered_state,
        compacted_snapshot_path,
    )
    archived_path = None
    archived_event_count = 0
    if archive_event_log_path is not None:
        archive_log = JsonlSchedulerEventLog(archive_event_log_path)
        archived_path = archive_log.write_all(recovery.events)
        archived_event_count = recovery.event_count
    if reset_event_log:
        JsonlSchedulerEventLog(event_log_path).clear()
    active_event_count = len(JsonlSchedulerEventLog(event_log_path).read_all())
    return SchedulerCompactionResult(
        recovery=recovery,
        compacted_snapshot_path=written,
        archived_event_log_path=archived_path,
        archive_requested=archive_event_log_path is not None,
        reset_event_log_requested=reset_event_log,
        archived_event_count=archived_event_count,
        active_event_count_after_compaction=active_event_count,
        event_log_truncated=reset_event_log,
    )


def replay_scheduler_events(
    baseline: SchedulerState,
    events: tuple[SchedulerEvent, ...],
    *,
    strict: bool = True,
) -> SchedulerState:
    """Apply scheduler events to a baseline state.

    Replay updates lifecycle fields for tasks that already exist in the
    baseline. The event log is not a task-contract source; unknown task events
    are rejected in strict mode.
    """

    tasks = dict(baseline.tasks)
    run_records = list(baseline.run_records)
    known_run_keys = {
        (record.task_id, record.run_id, record.output_artifact_id, record.output_artifact_version)
        for record in run_records
    }

    for event in sorted(events, key=_scheduler_event_order_key):
        if event.task_id not in tasks:
            if strict:
                raise ValueError(
                    f"scheduler event {event.event_id!r} references unknown task "
                    f"{event.task_id!r}; replay requires a baseline snapshot task "
                    "contract. Scheduler event logs are replay/audit material "
                    "and do not create task contracts across a compaction "
                    "or recovery boundary."
                )
            continue
        task = tasks[event.task_id]
        next_state = _state_from_scheduler_event(event)
        output_ref = task.output_artifact_ref
        if event.output_artifact_id:
            output_ref = ExchangeReference(
                ref_kind="exchange_artifact",
                ref_id=event.output_artifact_id,
                version=event.output_artifact_version,
            )
        tasks[event.task_id] = replace(
            task,
            state=next_state,
            blocked_reason=(
                event.reason
                if next_state in {"waiting", "blocked", "review_required"}
                else ""
            ),
            run_id=event.run_id or task.run_id,
            output_artifact_ref=output_ref,
        )
        if event.event_kind in {
            "task_completed",
            "task_review_required",
            "task_permission_approved",
            "task_permission_rejected",
        }:
            _upsert_run_record_from_event(
                run_records,
                known_run_keys,
                event,
                state=next_state,
            )

    return SchedulerState(
        tasks=tasks,
        dependencies=baseline.dependencies,
        run_records=tuple(run_records),
        merge_gates=baseline.merge_gates,
    )


def _upsert_run_record_from_event(
    run_records: list[TaskRunRecord],
    known_run_keys: set[tuple[str, str, str, str]],
    event: SchedulerEvent,
    *,
    state: ScheduledTaskState,
) -> None:
    if not event.run_id or not event.output_artifact_id:
        return

    key = (
        event.task_id,
        event.run_id,
        event.output_artifact_id,
        event.output_artifact_version,
    )
    if key in known_run_keys:
        for index, record in enumerate(run_records):
            record_key = (
                record.task_id,
                record.run_id,
                record.output_artifact_id,
                record.output_artifact_version,
            )
            if record_key == key:
                run_records[index] = replace(
                    record,
                    session_id=event.session_id or record.session_id,
                    state=state,
                )
                return
    run_records.append(
        TaskRunRecord(
            task_id=event.task_id,
            run_id=event.run_id,
            session_id=event.session_id,
            output_artifact_id=event.output_artifact_id,
            output_artifact_version=event.output_artifact_version,
            state=state,
        )
    )
    known_run_keys.add(key)


def _reference_to_json(ref: ExchangeReference | None) -> dict[str, object] | None:
    if ref is None:
        return None
    return {
        "ref_kind": ref.ref_kind,
        "ref_id": ref.ref_id,
        "version": ref.version,
        "path": ref.path,
        "label": ref.label,
    }


def _reference_from_json(payload: dict[str, Any] | None) -> ExchangeReference | None:
    if payload is None:
        return None
    return ExchangeReference(
        ref_kind=str(payload.get("ref_kind", "")),
        ref_id=str(payload.get("ref_id", "")),
        version=str(payload.get("version", "")),
        path=str(payload.get("path", "")),
        label=str(payload.get("label", "")),
    )


def _agent_to_json(agent: AgentSpec) -> dict[str, object]:
    return {
        "agent_id": agent.agent_id,
        "runtime_provider": agent.runtime_provider,
        "display_name": agent.display_name,
        "model": agent.model,
        "tools": list(agent.tools),
        "max_turns": agent.max_turns,
    }


def _agent_from_json(payload: dict[str, Any]) -> AgentSpec:
    return AgentSpec(
        agent_id=str(payload.get("agent_id", "")),
        runtime_provider=str(payload.get("runtime_provider", "fake")),  # type: ignore[arg-type]
        display_name=str(payload.get("display_name", "")),
        model=str(payload.get("model", "")),
        tools=tuple(str(item) for item in payload.get("tools", ()) or ()),
        max_turns=payload.get("max_turns") if isinstance(payload.get("max_turns"), int) else None,
    )


def _context_to_json(context: ContextScope) -> dict[str, object]:
    return {
        "context_id": context.context_id,
        "lane_id": context.lane_id,
        "required_refs": [
            _reference_to_json(ref)
            for ref in context.required_refs
        ],
        "visible_artifacts": list(context.visible_artifacts),
        "session_policy": context.session_policy,
        "redaction_policy": context.redaction_policy,
    }


def _context_from_json(payload: dict[str, Any]) -> ContextScope:
    refs = tuple(
        ref
        for ref in (
            _reference_from_json(item)
            for item in payload.get("required_refs", ()) or ()
        )
        if ref is not None
    )
    return ContextScope(
        context_id=str(payload.get("context_id", "default")),
        lane_id=str(payload.get("lane_id", "")),
        required_refs=refs,
        visible_artifacts=tuple(str(item) for item in payload.get("visible_artifacts", ()) or ()),
        session_policy=str(payload.get("session_policy", "stateless")),
        redaction_policy=str(payload.get("redaction_policy", "")),
    )


def _lease_to_json(lease: EditScopeLease | None) -> dict[str, object] | None:
    if lease is None:
        return None
    return {
        "lease_id": lease.lease_id,
        "task_id": lease.task_id,
        "allowed_artifacts": list(lease.allowed_artifacts),
        "denied_artifacts": list(lease.denied_artifacts),
        "lease_mode": lease.lease_mode,
        "conflict_policy": lease.conflict_policy,
        "expires_at": lease.expires_at,
    }


def _lease_from_json(payload: dict[str, Any] | None) -> EditScopeLease | None:
    if payload is None:
        return None
    return EditScopeLease(
        lease_id=str(payload.get("lease_id", "")),
        task_id=str(payload.get("task_id", "")),
        allowed_artifacts=tuple(str(item) for item in payload.get("allowed_artifacts", ()) or ()),
        denied_artifacts=tuple(str(item) for item in payload.get("denied_artifacts", ()) or ()),
        lease_mode=str(payload.get("lease_mode", "read")),  # type: ignore[arg-type]
        conflict_policy=str(payload.get("conflict_policy", "block-on-overlap")),
        expires_at=str(payload.get("expires_at", "")),
    )


def _sandbox_to_json(sandbox: SandboxProfile) -> dict[str, object]:
    return {
        "profile_id": sandbox.profile_id,
        "profile_kind": sandbox.profile_kind,
        "network_policy": sandbox.network_policy,
        "secret_policy": sandbox.secret_policy,
        "mount_policy": sandbox.mount_policy,
    }


def _sandbox_from_json(payload: dict[str, Any]) -> SandboxProfile:
    return SandboxProfile(
        profile_id=str(payload.get("profile_id", "shared")),
        profile_kind=str(payload.get("profile_kind", "shared-process")),  # type: ignore[arg-type]
        network_policy=str(payload.get("network_policy", "disabled")),
        secret_policy=str(payload.get("secret_policy", "deny")),
        mount_policy=str(payload.get("mount_policy", "lease-scoped")),
    )


def _scheduled_task_to_json(task: ScheduledTask) -> dict[str, object]:
    return {
        "task_id": task.task_id,
        "title": task.title,
        "instruction": task.instruction,
        "agent": _agent_to_json(task.agent),
        "state": task.state,
        "context_scope": _context_to_json(task.context_scope),
        "edit_lease": _lease_to_json(task.edit_lease),
        "sandbox_profile": _sandbox_to_json(task.sandbox_profile),
        "input_artifact_refs": [
            _reference_to_json(ref)
            for ref in task.input_artifact_refs
        ],
        "acceptance": list(task.acceptance),
        "output_artifact_id": task.output_artifact_id,
        "blocked_reason": task.blocked_reason,
        "run_id": task.run_id,
        "output_artifact_ref": _reference_to_json(task.output_artifact_ref),
    }


def _scheduled_task_from_json(payload: dict[str, Any]) -> ScheduledTask:
    input_refs = tuple(
        ref
        for ref in (
            _reference_from_json(item)
            for item in payload.get("input_artifact_refs", ()) or ()
        )
        if ref is not None
    )
    return ScheduledTask(
        task_id=str(payload.get("task_id", "")),
        title=str(payload.get("title", "")),
        instruction=str(payload.get("instruction", "")),
        agent=_agent_from_json(payload.get("agent", {}) or {}),
        state=str(payload.get("state", "proposed")),  # type: ignore[arg-type]
        context_scope=_context_from_json(payload.get("context_scope", {}) or {}),
        edit_lease=_lease_from_json(payload.get("edit_lease")),
        sandbox_profile=_sandbox_from_json(payload.get("sandbox_profile", {}) or {}),
        input_artifact_refs=input_refs,
        acceptance=tuple(str(item) for item in payload.get("acceptance", ()) or ()),
        output_artifact_id=str(payload.get("output_artifact_id", "")),
        blocked_reason=str(payload.get("blocked_reason", "")),
        run_id=str(payload.get("run_id", "")),
        output_artifact_ref=_reference_from_json(payload.get("output_artifact_ref")),
    )


def _dependency_to_json(dependency: TaskDependency) -> dict[str, object]:
    return {
        "dependency_id": dependency.dependency_id,
        "source_task_id": dependency.source_task_id,
        "target_task_id": dependency.target_task_id,
        "dependency_kind": dependency.dependency_kind,
        "required_state": dependency.required_state,
    }


def _dependency_from_json(payload: dict[str, Any]) -> TaskDependency:
    return TaskDependency(
        dependency_id=str(payload.get("dependency_id", "")),
        source_task_id=str(payload.get("source_task_id", "")),
        target_task_id=str(payload.get("target_task_id", "")),
        dependency_kind=str(payload.get("dependency_kind", "depends_on")),  # type: ignore[arg-type]
        required_state=str(payload.get("required_state", "complete")),  # type: ignore[arg-type]
    )


def _merge_gate_to_json(gate: SchedulerMergeGate) -> dict[str, object]:
    return {
        "gate_id": gate.gate_id,
        "title": gate.title,
        "target_task_id": gate.target_task_id,
        "source_task_ids": list(gate.source_task_ids),
        "dependency_ids": list(gate.dependency_ids),
        "gate_kind": gate.gate_kind,
        "state": gate.state,
        "required_review": gate.required_review,
        "input_artifact_refs": [
            _reference_to_json(ref)
            for ref in gate.input_artifact_refs
        ],
        "output_artifact_id": gate.output_artifact_id,
        "decision_artifact_ref": _reference_to_json(gate.decision_artifact_ref),
        "blocked_reason": gate.blocked_reason,
        "created_at": gate.created_at,
        "resolved_at": gate.resolved_at,
    }


def _merge_gate_from_json(payload: dict[str, Any]) -> SchedulerMergeGate:
    input_refs = tuple(
        ref
        for ref in (
            _reference_from_json(item)
            for item in payload.get("input_artifact_refs", ()) or ()
        )
        if ref is not None
    )
    return SchedulerMergeGate(
        gate_id=str(payload.get("gate_id", "")),
        title=str(payload.get("title", "")),
        target_task_id=str(payload.get("target_task_id", "")),
        source_task_ids=tuple(str(item) for item in payload.get("source_task_ids", ()) or ()),
        dependency_ids=tuple(str(item) for item in payload.get("dependency_ids", ()) or ()),
        gate_kind=str(payload.get("gate_kind", "join_only")),  # type: ignore[arg-type]
        state=str(payload.get("state", "proposed")),  # type: ignore[arg-type]
        required_review=bool(payload.get("required_review", False)),
        input_artifact_refs=input_refs,
        output_artifact_id=str(payload.get("output_artifact_id", "")),
        decision_artifact_ref=_reference_from_json(payload.get("decision_artifact_ref")),
        blocked_reason=str(payload.get("blocked_reason", "")),
        created_at=str(payload.get("created_at", "")),
        resolved_at=str(payload.get("resolved_at", "")),
    )


def _run_record_to_json(record: TaskRunRecord) -> dict[str, object]:
    return {
        "task_id": record.task_id,
        "run_id": record.run_id,
        "session_id": record.session_id,
        "output_artifact_id": record.output_artifact_id,
        "output_artifact_version": record.output_artifact_version,
        "state": record.state,
    }


def _run_record_from_json(payload: dict[str, Any]) -> TaskRunRecord:
    return TaskRunRecord(
        task_id=str(payload.get("task_id", "")),
        run_id=str(payload.get("run_id", "")),
        session_id=str(payload.get("session_id", "")),
        output_artifact_id=str(payload.get("output_artifact_id", "")),
        output_artifact_version=str(payload.get("output_artifact_version", "")),
        state=str(payload.get("state", "complete")),  # type: ignore[arg-type]
    )


def _scheduler_event_order_key(event: SchedulerEvent) -> tuple[int, str, str]:
    sequence = event.sequence if event.sequence is not None else 10**9
    return (sequence, event.timestamp, event.event_id)


def _state_from_scheduler_event(event: SchedulerEvent) -> ScheduledTaskState:
    if event.event_kind == "task_submitted":
        return "proposed"
    if event.event_kind == "task_ready":
        return "ready"
    if event.event_kind == "task_waiting":
        return "waiting"
    if event.event_kind in {"task_blocked", "task_run_failed"}:
        return "blocked"
    if event.event_kind == "task_running":
        return "running"
    if event.event_kind == "task_completed":
        return "complete"
    if event.event_kind == "task_review_required":
        return "review_required"
    if event.event_kind == "task_permission_approved":
        return "complete"
    if event.event_kind == "task_permission_rejected":
        return "blocked"
    if event.to_state in {
        "proposed",
        "ready",
        "running",
        "waiting",
        "review_required",
        "complete",
        "blocked",
        "cancelled",
    }:
        return event.to_state
    return "proposed"


def _scheduler_event_to_json(event: SchedulerEvent) -> dict[str, object]:
    payload = asdict(event)
    payload["related_dependency_ids"] = list(event.related_dependency_ids)
    payload["related_artifact_ids"] = list(event.related_artifact_ids)
    return payload


def _scheduler_event_from_json(payload: dict[str, object]) -> SchedulerEvent:
    return SchedulerEvent(
        event_id=str(payload.get("event_id", "")),
        event_kind=str(payload.get("event_kind", "task_ready")),  # type: ignore[arg-type]
        timestamp=str(payload.get("timestamp", "")),
        task_id=str(payload.get("task_id", "")),
        from_state=str(payload.get("from_state", "")),
        to_state=str(payload.get("to_state", "")),
        reason=str(payload.get("reason", "")),
        run_id=str(payload.get("run_id", "")),
        session_id=str(payload.get("session_id", "")),
        output_artifact_id=str(payload.get("output_artifact_id", "")),
        output_artifact_version=str(payload.get("output_artifact_version", "")),
        related_dependency_ids=tuple(
            str(item) for item in payload.get("related_dependency_ids", ()) or ()
        ),
        related_artifact_ids=tuple(
            str(item) for item in payload.get("related_artifact_ids", ()) or ()
        ),
        sequence=payload.get("sequence") if isinstance(payload.get("sequence"), int) else None,
    )


def _merge_gate_event_to_json(event: SchedulerMergeGateEvent) -> dict[str, object]:
    payload = asdict(event)
    payload["related_dependency_ids"] = list(event.related_dependency_ids)
    payload["related_task_ids"] = list(event.related_task_ids)
    return payload


def _merge_gate_event_from_json(payload: dict[str, object]) -> SchedulerMergeGateEvent:
    return SchedulerMergeGateEvent(
        event_id=str(payload.get("event_id", "")),
        event_kind=str(payload.get("event_kind", "merge_gate_waiting")),  # type: ignore[arg-type]
        timestamp=str(payload.get("timestamp", "")),
        gate_id=str(payload.get("gate_id", "")),
        target_task_id=str(payload.get("target_task_id", "")),
        from_state=str(payload.get("from_state", "")),
        to_state=str(payload.get("to_state", "")),
        reason=str(payload.get("reason", "")),
        decision_artifact_id=str(payload.get("decision_artifact_id", "")),
        decision_artifact_version=str(payload.get("decision_artifact_version", "")),
        related_dependency_ids=tuple(
            str(item) for item in payload.get("related_dependency_ids", ()) or ()
        ),
        related_task_ids=tuple(
            str(item) for item in payload.get("related_task_ids", ()) or ()
        ),
        sequence=payload.get("sequence") if isinstance(payload.get("sequence"), int) else None,
    )
