"""Task submission adapter for scheduler-owned task graphs."""

from __future__ import annotations

from datetime import UTC, datetime
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Mapping

from .exchange import (
    ExchangeArtifact,
    ExchangeLog,
    ExchangePayloadPart,
    ExchangeReference,
    ExchangeScope,
)
from .runtime_adapter import AgentSpec
from .scheduler import (
    ContextScope,
    EditScopeLease,
    SandboxProfile,
    ScheduledTask,
    SchedulerEvent,
    SchedulerState,
    TaskDependency,
    build_requested_edit_lease_lifecycle,
)

TASK_SUBMISSION_PRODUCT_TYPE = "scheduler_task_submission"
TASK_BATCH_SUBMISSION_PRODUCT_TYPE = "scheduler_task_batch_submission"


@dataclass(frozen=True, slots=True)
class SchedulerTaskSubmission:
    """Structured product used to submit one task into scheduler state."""

    task_id: str
    title: str
    instruction: str
    agent: AgentSpec
    context_scope: ContextScope
    edit_lease: EditScopeLease | None = None
    sandbox_profile: SandboxProfile = field(
        default_factory=lambda: SandboxProfile(profile_id="shared-process")
    )
    input_artifact_refs: tuple[ExchangeReference, ...] = ()
    acceptance: tuple[str, ...] = ()
    output_artifact_id: str = ""
    dependencies: tuple[TaskDependency, ...] = ()


@dataclass(frozen=True, slots=True)
class SchedulerTaskSubmissionResult:
    """Result of submitting one task artifact into a scheduler snapshot."""

    state: SchedulerState
    task: ScheduledTask
    dependencies_added: tuple[TaskDependency, ...] = ()
    source_artifact_id: str = ""
    source_artifact_version: str = ""


@dataclass(frozen=True, slots=True)
class SchedulerTaskBatchSubmission:
    """Structured product used to submit multiple scheduler tasks at once."""

    batch_id: str
    tasks: tuple[SchedulerTaskSubmission, ...]
    title: str = ""
    summary: str = ""


@dataclass(frozen=True, slots=True)
class SchedulerTaskBatchSubmissionResult:
    """Result of submitting a batch artifact into a scheduler snapshot."""

    state: SchedulerState
    tasks: tuple[ScheduledTask, ...] = ()
    dependencies_added: tuple[TaskDependency, ...] = ()
    source_artifact_id: str = ""
    source_artifact_version: str = ""


@dataclass(frozen=True, slots=True)
class PersistedSchedulerTaskBatchSubmissionResult:
    """Result of submitting a batch and persisting the scheduler snapshot."""

    submission: SchedulerTaskBatchSubmissionResult
    snapshot_path: Path
    event_log_path: Path
    submission_event_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PersistedSchedulerTaskSubmissionResult:
    """Result of submitting one task and persisting the scheduler snapshot."""

    submission: SchedulerTaskSubmissionResult
    snapshot_path: Path
    event_log_path: Path
    submission_event_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PersistedExchangeArtifactAdmissionResult:
    """Result of admitting one exact stored ExchangeArtifact version."""

    artifact_store_path: Path
    product_type: str
    source_artifact_id: str
    source_artifact_version: str
    snapshot_path: Path
    event_log_path: Path
    state: SchedulerState
    submitted_tasks: tuple[ScheduledTask, ...] = ()
    dependencies_added: tuple[TaskDependency, ...] = ()
    submission_event_ids: tuple[str, ...] = ()
    snapshot_existed: bool = False

    def to_json_dict(self) -> dict[str, object]:
        """Return compact admission metadata for host/review surfaces."""

        return {
            "artifact_store_path": str(self.artifact_store_path),
            "product_type": self.product_type,
            "source_artifact_id": self.source_artifact_id,
            "source_artifact_version": self.source_artifact_version,
            "snapshot_path": str(self.snapshot_path),
            "event_log_path": str(self.event_log_path),
            "snapshot_existed": self.snapshot_existed,
            "submitted_task_ids": [task.task_id for task in self.submitted_tasks],
            "submission_event_ids": list(self.submission_event_ids),
            "dependencies_added": [
                dependency.dependency_id for dependency in self.dependencies_added
            ],
            "task_count": len(self.submitted_tasks),
            "dependency_count": len(self.dependencies_added),
            "state_task_count": len(self.state.tasks),
            "state_dependency_count": len(self.state.dependencies),
            "state_written": True,
            "ran_tasks": False,
            "refreshed_projection": False,
            "authority_split": {
                "scheduler_state_authority": "scheduler_snapshot",
                "exchange_store_role": "exact-version-coordination-product-source",
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }


def scheduler_task_submission_to_artifact(
    submission: SchedulerTaskSubmission,
    *,
    artifact_id: str | None = None,
    producer: str = "scheduler-submission-adapter",
    created_at: str = "",
    version: str = "v1",
) -> ExchangeArtifact:
    """Encode a task submission as a structured exchange artifact."""

    task_artifact_id = artifact_id or f"scheduler-task-submission:{submission.task_id}"
    log_timestamp = created_at or _utc_timestamp()
    return ExchangeArtifact(
        artifact_id=task_artifact_id,
        kind="request",
        intent="propose",
        producer=producer,
        scope=submission_to_exchange_scope(submission),
        created_at=log_timestamp,
        version=version,
        parts=(
            ExchangePayloadPart(
                part_type="structured",
                data=_submission_to_payload(submission),
            ),
            _submission_log_part(
                timestamp=log_timestamp,
                actor=producer,
                action="scheduler_task_submitted",
                channel="scheduler-submission-artifact",
                summary=f"Submitted scheduler task {submission.task_id}.",
                related_artifact_ids=(task_artifact_id,),
            ),
        ),
    )


def scheduler_task_batch_submission_to_artifact(
    submission: SchedulerTaskBatchSubmission,
    *,
    artifact_id: str | None = None,
    producer: str = "scheduler-submission-adapter",
    created_at: str = "",
    version: str = "v1",
) -> ExchangeArtifact:
    """Encode a batch submission as a structured exchange artifact."""

    task_artifact_id = artifact_id or f"scheduler-task-batch-submission:{submission.batch_id}"
    log_timestamp = created_at or _utc_timestamp()
    return ExchangeArtifact(
        artifact_id=task_artifact_id,
        kind="request",
        intent="propose",
        producer=producer,
        scope=_batch_exchange_scope(submission),
        created_at=log_timestamp,
        version=version,
        parts=(
            ExchangePayloadPart(
                part_type="structured",
                data=_batch_submission_to_payload(submission),
            ),
            _submission_log_part(
                timestamp=log_timestamp,
                actor=producer,
                action="scheduler_task_batch_submitted",
                channel="scheduler-submission-artifact",
                summary=(
                    f"Submitted scheduler task batch {submission.batch_id} "
                    f"with {len(submission.tasks)} task(s)."
                ),
                related_artifact_ids=(task_artifact_id,),
            ),
        ),
    )


def submission_to_exchange_scope(submission: SchedulerTaskSubmission) -> ExchangeScope:
    """Return the exchange scope represented by a scheduler task submission."""

    return ExchangeScope(
        lane_id=submission.context_scope.lane_id,
        task_id=submission.task_id,
        context_id=submission.context_scope.context_id,
        agent_id=submission.agent.agent_id,
    )


def scheduler_task_batch_submission_from_artifact(
    artifact: ExchangeArtifact,
) -> SchedulerTaskBatchSubmission:
    """Parse a scheduler task batch submission from an exchange artifact."""

    payload = _find_batch_submission_payload(artifact)
    batch_id = _required_str(payload, "batch_id", artifact)
    tasks_value = payload.get("tasks")
    if not isinstance(tasks_value, (list, tuple)):
        raise ValueError(
            f"scheduler task batch submission {artifact.artifact_id!r} field 'tasks' must be a list"
        )
    tasks: list[SchedulerTaskSubmission] = []
    seen_task_ids: set[str] = set()
    for index, item in enumerate(tasks_value):
        if not isinstance(item, Mapping):
            raise ValueError(
                f"scheduler task batch submission {artifact.artifact_id!r} tasks[{index}] must be an object"
            )
        task = _submission_from_payload(item, artifact)
        if task.task_id in seen_task_ids:
            raise ValueError(
                f"scheduler task batch submission {artifact.artifact_id!r} contains duplicate task_id "
                f"{task.task_id!r}"
            )
        seen_task_ids.add(task.task_id)
        tasks.append(task)
    if not tasks:
        raise ValueError(
            f"scheduler task batch submission {artifact.artifact_id!r} requires at least one task"
        )
    return SchedulerTaskBatchSubmission(
        batch_id=batch_id,
        title=str(payload.get("title", "") or ""),
        summary=str(payload.get("summary", "") or ""),
        tasks=tuple(tasks),
    )


def scheduler_task_submission_from_artifact(
    artifact: ExchangeArtifact,
) -> SchedulerTaskSubmission:
    """Parse a scheduler task submission from an exchange artifact.

    The first version accepts exactly one structured payload part with
    ``product_type='scheduler_task_submission'``. Unknown keys are ignored, but
    missing or malformed first-version fields raise readable errors.
    """

    return _submission_from_payload(_find_submission_payload(artifact), artifact)


def submit_scheduler_task_batch(
    state: SchedulerState,
    artifact: ExchangeArtifact,
    *,
    replace_existing: bool = False,
) -> SchedulerTaskBatchSubmissionResult:
    """Submit a batch exchange-artifact task request into scheduler state."""

    batch = scheduler_task_batch_submission_from_artifact(artifact)
    current = state
    submitted_tasks: list[ScheduledTask] = []
    dependencies_added: list[TaskDependency] = []
    for submission in batch.tasks:
        result = _submit_scheduler_task_submission(
            current,
            artifact,
            submission,
            replace_existing=replace_existing,
        )
        current = result.state
        submitted_tasks.append(result.task)
        dependencies_added.extend(result.dependencies_added)
    return SchedulerTaskBatchSubmissionResult(
        state=current,
        tasks=tuple(submitted_tasks),
        dependencies_added=tuple(dependencies_added),
        source_artifact_id=artifact.artifact_id,
        source_artifact_version=artifact.version,
    )


def submit_scheduler_task_batch_with_persistence(
    state: SchedulerState,
    artifact: ExchangeArtifact,
    *,
    snapshot_path: str | Path,
    event_log_path: str | Path,
    replace_existing: bool = False,
    timestamp: str = "",
) -> PersistedSchedulerTaskBatchSubmissionResult:
    """Submit a batch, append submission audit events, and write a snapshot.

    The written snapshot remains the task-contract authority for recovery. The
    appended ``task_submitted`` events are audit breadcrumbs only.
    """

    from .scheduler_store import write_scheduler_state_snapshot

    result = submit_scheduler_task_batch(
        state,
        artifact,
        replace_existing=replace_existing,
    )
    event_ids = _append_scheduler_submission_events(
        event_log_path,
        artifact=artifact,
        tasks=result.tasks,
        dependencies_added=result.dependencies_added,
        timestamp=timestamp,
        reason="scheduler task batch submitted",
    )
    written_snapshot = write_scheduler_state_snapshot(result.state, snapshot_path)
    return PersistedSchedulerTaskBatchSubmissionResult(
        submission=result,
        snapshot_path=written_snapshot,
        event_log_path=Path(event_log_path),
        submission_event_ids=tuple(event_ids),
    )


def submit_scheduler_task_with_persistence(
    state: SchedulerState,
    artifact: ExchangeArtifact,
    *,
    snapshot_path: str | Path,
    event_log_path: str | Path,
    replace_existing: bool = False,
    timestamp: str = "",
) -> PersistedSchedulerTaskSubmissionResult:
    """Submit one task, append a submission audit event, and write a snapshot."""

    from .scheduler_store import write_scheduler_state_snapshot

    result = submit_scheduler_task(
        state,
        artifact,
        replace_existing=replace_existing,
    )
    event_ids = _append_scheduler_submission_events(
        event_log_path,
        artifact=artifact,
        tasks=(result.task,),
        dependencies_added=result.dependencies_added,
        timestamp=timestamp,
        reason="scheduler task submitted",
    )
    written_snapshot = write_scheduler_state_snapshot(result.state, snapshot_path)
    return PersistedSchedulerTaskSubmissionResult(
        submission=result,
        snapshot_path=written_snapshot,
        event_log_path=Path(event_log_path),
        submission_event_ids=event_ids,
    )


def admit_exchange_artifact_version_to_scheduler(
    *,
    artifact_store_path: str | Path,
    artifact_id: str,
    version: str,
    snapshot_path: str | Path,
    event_log_path: str | Path,
    replace_existing: bool = False,
    timestamp: str = "",
) -> PersistedExchangeArtifactAdmissionResult:
    """Admit one exact stored ExchangeArtifact version into scheduler state.

    The exchange artifact store supplies the exact coordination product. The
    scheduler snapshot and event log remain the recovery authority after
    admission.
    """

    from .exchange_store import JsonArtifactVersionStore
    from .scheduler_store import read_scheduler_state_snapshot

    if not artifact_id:
        raise ValueError("exact scheduler admission requires a non-empty artifact_id")
    if not version:
        raise ValueError(
            f"exact scheduler admission for {artifact_id!r} requires a non-empty version"
        )

    store_path = Path(artifact_store_path)
    try:
        record = JsonArtifactVersionStore(store_path).get(artifact_id, version)
    except KeyError as exc:
        raise ValueError(
            f"exchange artifact version not found in {store_path}: "
            f"{artifact_id!r}@{version!r}"
        ) from exc

    artifact = record.artifact
    product_type = _exact_scheduler_submission_product_type(artifact)
    snapshot = Path(snapshot_path)
    event_log = Path(event_log_path)
    snapshot_existed = snapshot.exists()
    state = read_scheduler_state_snapshot(snapshot) if snapshot_existed else SchedulerState()
    event_timestamp = timestamp or artifact.created_at

    if product_type == TASK_SUBMISSION_PRODUCT_TYPE:
        persisted_single = submit_scheduler_task_with_persistence(
            state,
            artifact,
            snapshot_path=snapshot,
            event_log_path=event_log,
            replace_existing=replace_existing,
            timestamp=event_timestamp,
        )
        return PersistedExchangeArtifactAdmissionResult(
            artifact_store_path=store_path,
            product_type=product_type,
            source_artifact_id=persisted_single.submission.source_artifact_id,
            source_artifact_version=persisted_single.submission.source_artifact_version,
            snapshot_path=persisted_single.snapshot_path,
            event_log_path=persisted_single.event_log_path,
            state=persisted_single.submission.state,
            submitted_tasks=(persisted_single.submission.task,),
            dependencies_added=persisted_single.submission.dependencies_added,
            submission_event_ids=persisted_single.submission_event_ids,
            snapshot_existed=snapshot_existed,
        )

    persisted_batch = submit_scheduler_task_batch_with_persistence(
        state,
        artifact,
        snapshot_path=snapshot,
        event_log_path=event_log,
        replace_existing=replace_existing,
        timestamp=event_timestamp,
    )
    return PersistedExchangeArtifactAdmissionResult(
        artifact_store_path=store_path,
        product_type=product_type,
        source_artifact_id=persisted_batch.submission.source_artifact_id,
        source_artifact_version=persisted_batch.submission.source_artifact_version,
        snapshot_path=persisted_batch.snapshot_path,
        event_log_path=persisted_batch.event_log_path,
        state=persisted_batch.submission.state,
        submitted_tasks=persisted_batch.submission.tasks,
        dependencies_added=persisted_batch.submission.dependencies_added,
        submission_event_ids=persisted_batch.submission_event_ids,
        snapshot_existed=snapshot_existed,
    )


def _submission_from_payload(
    payload: Mapping[str, object],
    artifact: ExchangeArtifact,
) -> SchedulerTaskSubmission:
    task_id = _required_str(payload, "task_id", artifact)
    title = _required_str(payload, "title", artifact)
    instruction = _required_str(payload, "instruction", artifact)
    return SchedulerTaskSubmission(
        task_id=task_id,
        title=title,
        instruction=instruction,
        agent=_agent_from_payload(payload.get("agent"), artifact),
        context_scope=_context_scope_from_payload(
            payload.get("context_scope"),
            artifact,
            task_id=task_id,
        ),
        edit_lease=_edit_lease_from_payload(payload.get("edit_lease"), artifact, task_id=task_id),
        sandbox_profile=_sandbox_profile_from_payload(payload.get("sandbox_profile"), artifact),
        input_artifact_refs=_refs_from_payload(payload.get("input_artifact_refs"), artifact),
        acceptance=_str_tuple(payload.get("acceptance"), "acceptance", artifact),
        output_artifact_id=str(payload.get("output_artifact_id", "") or ""),
        dependencies=_dependencies_from_payload(payload.get("dependencies"), artifact, target_task_id=task_id),
    )


def submit_scheduler_task(
    state: SchedulerState,
    artifact: ExchangeArtifact,
    *,
    replace_existing: bool = False,
) -> SchedulerTaskSubmissionResult:
    """Submit one exchange-artifact task request into scheduler state."""

    return _submit_scheduler_task_submission(
        state,
        artifact,
        scheduler_task_submission_from_artifact(artifact),
        replace_existing=replace_existing,
    )


def _submit_scheduler_task_submission(
    state: SchedulerState,
    artifact: ExchangeArtifact,
    submission: SchedulerTaskSubmission,
    *,
    replace_existing: bool,
) -> SchedulerTaskSubmissionResult:
    if submission.task_id in state.tasks and not replace_existing:
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} references existing task "
            f"{submission.task_id!r}; pass replace_existing=True to replace it"
        )

    task = ScheduledTask(
        task_id=submission.task_id,
        title=submission.title,
        instruction=submission.instruction,
        agent=submission.agent,
        context_scope=submission.context_scope,
        edit_lease=submission.edit_lease,
        sandbox_profile=submission.sandbox_profile,
        input_artifact_refs=submission.input_artifact_refs,
        acceptance=submission.acceptance,
        output_artifact_id=submission.output_artifact_id,
    )
    tasks = dict(state.tasks)
    tasks[task.task_id] = task
    edit_lease_lifecycle = dict(state.edit_lease_lifecycle)
    requested_lease = build_requested_edit_lease_lifecycle(task)
    if requested_lease is not None:
        edit_lease_lifecycle[requested_lease.lease_id] = requested_lease
    dependencies = tuple(
        dependency
        for dependency in state.dependencies
        if not replace_existing or dependency.target_task_id != task.task_id
    ) + submission.dependencies
    return SchedulerTaskSubmissionResult(
        state=replace(
            state,
            tasks=tasks,
            dependencies=dependencies,
            edit_lease_lifecycle=edit_lease_lifecycle,
        ),
        task=task,
        dependencies_added=submission.dependencies,
        source_artifact_id=artifact.artifact_id,
        source_artifact_version=artifact.version,
    )


def _find_submission_payload(artifact: ExchangeArtifact) -> Mapping[str, object]:
    matches = [
        part.data
        for part in artifact.parts
        if part.part_type == "structured"
        and part.data.get("product_type") == TASK_SUBMISSION_PRODUCT_TYPE
    ]
    if not matches:
        raise ValueError(
            f"exchange artifact {artifact.artifact_id!r} does not contain structured "
            f"product_type={TASK_SUBMISSION_PRODUCT_TYPE!r}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"exchange artifact {artifact.artifact_id!r} contains multiple "
            f"{TASK_SUBMISSION_PRODUCT_TYPE!r} payloads"
        )
    return matches[0]


def _find_batch_submission_payload(artifact: ExchangeArtifact) -> Mapping[str, object]:
    matches = [
        part.data
        for part in artifact.parts
        if part.part_type == "structured"
        and part.data.get("product_type") == TASK_BATCH_SUBMISSION_PRODUCT_TYPE
    ]
    if not matches:
        raise ValueError(
            f"exchange artifact {artifact.artifact_id!r} does not contain structured "
            f"product_type={TASK_BATCH_SUBMISSION_PRODUCT_TYPE!r}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"exchange artifact {artifact.artifact_id!r} contains multiple "
            f"{TASK_BATCH_SUBMISSION_PRODUCT_TYPE!r} payloads"
        )
    return matches[0]


def _exact_scheduler_submission_product_type(artifact: ExchangeArtifact) -> str:
    product_types = [
        product_type
        for part in artifact.parts
        if part.part_type == "structured"
        for product_type in (part.data.get("product_type"),)
        if product_type in {
            TASK_SUBMISSION_PRODUCT_TYPE,
            TASK_BATCH_SUBMISSION_PRODUCT_TYPE,
        }
    ]
    if not product_types:
        raise ValueError(
            f"exchange artifact {artifact.artifact_id!r}@{artifact.version!r} is not a "
            "scheduler submission artifact; expected structured "
            f"product_type={TASK_SUBMISSION_PRODUCT_TYPE!r} or "
            f"product_type={TASK_BATCH_SUBMISSION_PRODUCT_TYPE!r}"
        )
    if len(product_types) > 1:
        raise ValueError(
            f"exchange artifact {artifact.artifact_id!r}@{artifact.version!r} contains "
            "multiple scheduler submission payloads; exact-version admission requires exactly one"
        )
    return str(product_types[0])


def _submission_to_payload(submission: SchedulerTaskSubmission) -> dict[str, object]:
    payload: dict[str, object] = {
        "product_type": TASK_SUBMISSION_PRODUCT_TYPE,
        "task_id": submission.task_id,
        "title": submission.title,
        "instruction": submission.instruction,
        "agent": {
            "agent_id": submission.agent.agent_id,
            "runtime_provider": submission.agent.runtime_provider,
            "display_name": submission.agent.display_name,
            "model": submission.agent.model,
            "tools": list(submission.agent.tools),
            "max_turns": submission.agent.max_turns,
        },
        "context_scope": {
            "context_id": submission.context_scope.context_id,
            "lane_id": submission.context_scope.lane_id,
            "required_refs": [_ref_to_payload(ref) for ref in submission.context_scope.required_refs],
            "visible_artifacts": list(submission.context_scope.visible_artifacts),
            "session_policy": submission.context_scope.session_policy,
            "redaction_policy": submission.context_scope.redaction_policy,
        },
        "sandbox_profile": {
            "profile_id": submission.sandbox_profile.profile_id,
            "profile_kind": submission.sandbox_profile.profile_kind,
            "network_policy": submission.sandbox_profile.network_policy,
            "secret_policy": submission.sandbox_profile.secret_policy,
            "mount_policy": submission.sandbox_profile.mount_policy,
        },
        "input_artifact_refs": [_ref_to_payload(ref) for ref in submission.input_artifact_refs],
        "acceptance": list(submission.acceptance),
        "output_artifact_id": submission.output_artifact_id,
        "dependencies": [
            {
                "dependency_id": dependency.dependency_id,
                "source_task_id": dependency.source_task_id,
                "target_task_id": dependency.target_task_id,
                "dependency_kind": dependency.dependency_kind,
                "required_state": dependency.required_state,
            }
            for dependency in submission.dependencies
        ],
    }
    if submission.edit_lease is not None:
        payload["edit_lease"] = {
            "lease_id": submission.edit_lease.lease_id,
            "task_id": submission.edit_lease.task_id,
            "allowed_artifacts": list(submission.edit_lease.allowed_artifacts),
            "denied_artifacts": list(submission.edit_lease.denied_artifacts),
            "lease_mode": submission.edit_lease.lease_mode,
            "conflict_policy": submission.edit_lease.conflict_policy,
            "expires_at": submission.edit_lease.expires_at,
        }
    return payload


def _batch_submission_to_payload(submission: SchedulerTaskBatchSubmission) -> dict[str, object]:
    return {
        "product_type": TASK_BATCH_SUBMISSION_PRODUCT_TYPE,
        "batch_id": submission.batch_id,
        "title": submission.title,
        "summary": submission.summary,
        "tasks": [_submission_to_payload(task) for task in submission.tasks],
    }


def _batch_exchange_scope(submission: SchedulerTaskBatchSubmission) -> ExchangeScope:
    first = submission.tasks[0] if submission.tasks else None
    if first is None:
        return ExchangeScope()
    return ExchangeScope(
        trajectory_id="",
        lane_id=first.context_scope.lane_id,
        context_id=first.context_scope.context_id,
        agent_id=first.agent.agent_id,
    )


def _submission_log_part(
    *,
    timestamp: str,
    actor: str,
    action: str,
    channel: str,
    summary: str,
    related_artifact_ids: tuple[str, ...],
) -> ExchangePayloadPart:
    return ExchangePayloadPart(
        part_type="log",
        log=ExchangeLog(
            timestamp=timestamp,
            actor=actor,
            action=action,
            channel=channel,
            summary=summary,
            related_artifact_ids=related_artifact_ids,
        ),
    )


def _append_scheduler_submission_events(
    event_log_path: str | Path,
    *,
    artifact: ExchangeArtifact,
    tasks: tuple[ScheduledTask, ...],
    dependencies_added: tuple[TaskDependency, ...],
    timestamp: str,
    reason: str,
) -> tuple[str, ...]:
    from .scheduler_store import JsonlSchedulerEventLog

    event_log = JsonlSchedulerEventLog(event_log_path)
    existing_count = len(event_log.read_all())
    event_ids: list[str] = []
    for offset, task in enumerate(tasks, start=1):
        sequence = existing_count + offset
        event_id = f"scheduler-event-{sequence}"
        event_ids.append(event_id)
        event_log.append(
            SchedulerEvent(
                event_id=event_id,
                event_kind="task_submitted",
                timestamp=timestamp,
                task_id=task.task_id,
                from_state="",
                to_state=task.state,
                reason=reason,
                related_dependency_ids=tuple(
                    dependency.dependency_id
                    for dependency in dependencies_added
                    if dependency.target_task_id == task.task_id
                ),
                related_artifact_ids=((artifact.artifact_id,) if artifact.artifact_id else ()),
                lease_id=task.edit_lease.lease_id if task.edit_lease is not None else "",
                edit_lease_lifecycle=build_requested_edit_lease_lifecycle(
                    task,
                    timestamp=timestamp,
                ),
                sequence=sequence,
            )
        )
    return tuple(event_ids)


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _ref_to_payload(ref: ExchangeReference) -> dict[str, str]:
    return {
        "ref_kind": ref.ref_kind,
        "ref_id": ref.ref_id,
        "version": ref.version,
        "path": ref.path,
        "label": ref.label,
    }


def _required_str(
    payload: Mapping[str, object],
    key: str,
    artifact: ExchangeArtifact,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} requires non-empty string field {key!r}"
        )
    return value


def _agent_from_payload(value: object, artifact: ExchangeArtifact) -> AgentSpec:
    if not isinstance(value, Mapping):
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} requires object field 'agent'"
        )
    provider = value.get("runtime_provider")
    if provider not in ("fake", "qoder"):
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} has unsupported "
            f"agent.runtime_provider {provider!r}; expected 'fake' or 'qoder'"
        )
    agent_id = value.get("agent_id")
    if not isinstance(agent_id, str) or not agent_id:
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} requires agent.agent_id"
        )
    max_turns = value.get("max_turns")
    if max_turns is not None and not isinstance(max_turns, int):
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} field agent.max_turns must be int or null"
        )
    return AgentSpec(
        agent_id=agent_id,
        runtime_provider=provider,  # type: ignore[arg-type]
        display_name=str(value.get("display_name", "") or ""),
        model=str(value.get("model", "") or ""),
        tools=_str_tuple(value.get("tools"), "agent.tools", artifact),
        max_turns=max_turns,
    )


def _context_scope_from_payload(
    value: object,
    artifact: ExchangeArtifact,
    *,
    task_id: str,
) -> ContextScope:
    if value is None:
        return ContextScope(
            context_id=artifact.scope.context_id or f"context:{task_id}",
            lane_id=artifact.scope.lane_id,
        )
    if not isinstance(value, Mapping):
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} field 'context_scope' must be an object"
        )
    context_id = value.get("context_id")
    if not isinstance(context_id, str) or not context_id:
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} requires context_scope.context_id"
        )
    return ContextScope(
        context_id=context_id,
        lane_id=str(value.get("lane_id", "") or ""),
        required_refs=_refs_from_payload(value.get("required_refs"), artifact),
        visible_artifacts=_str_tuple(value.get("visible_artifacts"), "context_scope.visible_artifacts", artifact),
        session_policy=str(value.get("session_policy", "stateless") or "stateless"),
        redaction_policy=str(value.get("redaction_policy", "") or ""),
    )


def _edit_lease_from_payload(
    value: object,
    artifact: ExchangeArtifact,
    *,
    task_id: str,
) -> EditScopeLease | None:
    if value in (None, ""):
        return None
    if not isinstance(value, Mapping):
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} field 'edit_lease' must be an object or null"
        )
    lease_mode = value.get("lease_mode", "read")
    if lease_mode not in ("read", "write", "review-zone"):
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} has unsupported "
            f"edit_lease.lease_mode {lease_mode!r}"
        )
    return EditScopeLease(
        lease_id=str(value.get("lease_id", "") or f"lease:{task_id}"),
        task_id=str(value.get("task_id", "") or task_id),
        allowed_artifacts=_str_tuple(value.get("allowed_artifacts"), "edit_lease.allowed_artifacts", artifact),
        denied_artifacts=_str_tuple(value.get("denied_artifacts"), "edit_lease.denied_artifacts", artifact),
        lease_mode=lease_mode,  # type: ignore[arg-type]
        conflict_policy=str(value.get("conflict_policy", "block-on-overlap") or "block-on-overlap"),
        expires_at=str(value.get("expires_at", "") or ""),
    )


def _sandbox_profile_from_payload(value: object, artifact: ExchangeArtifact) -> SandboxProfile:
    if value is None:
        return SandboxProfile(profile_id="shared-process", profile_kind="shared-process")
    if not isinstance(value, Mapping):
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} field 'sandbox_profile' must be an object"
        )
    profile_kind = value.get("profile_kind", "shared-process")
    if profile_kind not in ("none", "shared-process", "git-worktree", "docker", "remote-vm"):
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} has unsupported "
            f"sandbox_profile.profile_kind {profile_kind!r}"
        )
    return SandboxProfile(
        profile_id=str(value.get("profile_id", "") or str(profile_kind)),
        profile_kind=profile_kind,  # type: ignore[arg-type]
        network_policy=str(value.get("network_policy", "disabled") or "disabled"),
        secret_policy=str(value.get("secret_policy", "deny") or "deny"),
        mount_policy=str(value.get("mount_policy", "lease-scoped") or "lease-scoped"),
    )


def _dependencies_from_payload(
    value: object,
    artifact: ExchangeArtifact,
    *,
    target_task_id: str,
) -> tuple[TaskDependency, ...]:
    if value in (None, ""):
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} field 'dependencies' must be a list"
        )
    dependencies: list[TaskDependency] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(
                f"scheduler task submission {artifact.artifact_id!r} dependencies[{index}] must be an object"
            )
        source_task_id = item.get("source_task_id")
        if not isinstance(source_task_id, str) or not source_task_id:
            raise ValueError(
                f"scheduler task submission {artifact.artifact_id!r} dependencies[{index}].source_task_id is required"
            )
        dependency_kind = item.get("dependency_kind", "depends_on")
        if dependency_kind not in ("depends_on", "waits_for"):
            raise ValueError(
                f"scheduler task submission {artifact.artifact_id!r} dependencies[{index}] "
                f"has unsupported dependency_kind {dependency_kind!r}"
            )
        required_state = item.get("required_state", "complete")
        if required_state not in (
            "proposed",
            "ready",
            "running",
            "waiting",
            "review_required",
            "complete",
            "blocked",
            "cancelled",
        ):
            raise ValueError(
                f"scheduler task submission {artifact.artifact_id!r} dependencies[{index}] "
                f"has unsupported required_state {required_state!r}"
            )
        dependencies.append(
            TaskDependency(
                dependency_id=str(item.get("dependency_id", "") or f"dep:{source_task_id}->{target_task_id}"),
                source_task_id=source_task_id,
                target_task_id=str(item.get("target_task_id", "") or target_task_id),
                dependency_kind=dependency_kind,  # type: ignore[arg-type]
                required_state=required_state,  # type: ignore[arg-type]
            )
        )
    return tuple(dependencies)


def _refs_from_payload(value: object, artifact: ExchangeArtifact) -> tuple[ExchangeReference, ...]:
    if value in (None, ""):
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} reference field must be a list"
        )
    refs: list[ExchangeReference] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise ValueError(
                f"scheduler task submission {artifact.artifact_id!r} reference item {index} must be an object"
            )
        ref_kind = item.get("ref_kind")
        ref_id = item.get("ref_id")
        if not isinstance(ref_kind, str) or not ref_kind:
            raise ValueError(
                f"scheduler task submission {artifact.artifact_id!r} reference item {index} requires ref_kind"
            )
        if not isinstance(ref_id, str) or not ref_id:
            raise ValueError(
                f"scheduler task submission {artifact.artifact_id!r} reference item {index} requires ref_id"
            )
        refs.append(
            ExchangeReference(
                ref_kind=ref_kind,
                ref_id=ref_id,
                version=str(item.get("version", "") or ""),
                path=str(item.get("path", "") or ""),
                label=str(item.get("label", "") or ""),
            )
        )
    return tuple(refs)


def _str_tuple(value: object, key: str, artifact: ExchangeArtifact) -> tuple[str, ...]:
    if value in (None, ""):
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError(
            f"scheduler task submission {artifact.artifact_id!r} field {key!r} must be a list of strings"
        )
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise ValueError(
                f"scheduler task submission {artifact.artifact_id!r} field {key!r} item {index} must be a string"
            )
        result.append(item)
    return tuple(result)
