"""Consumers for accepted ExchangeArtifact action-candidate dispositions."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Mapping

from .agent_exchange_action_disposition import ACTION_CANDIDATE_DISPOSITION_PRODUCT_TYPE
from .exchange import ExchangeArtifact, ExchangeReference
from .exchange_admission_ledger import admit_exchange_artifact_version_with_ledger
from .exchange_store import JsonArtifactVersionStore
from .landing_consumers import BridgeLandingConsumerPayload
from .landing_dispatch import (
    HandoffConsumer,
    ReviewIntakeConsumer,
    dispatch_landing_consumer_payload,
)
from .scheduler import SchedulerEvent, resolve_scheduler_merge_gate
from .scheduler_store import (
    JsonlSchedulerEventLog,
    JsonlSchedulerMergeGateEventLog,
    read_scheduler_state_snapshot,
    write_scheduler_state_snapshot,
)
from src.subagent import handoff_validator

ACCEPTED_SCHEDULER_ADMISSION_TARGET_SURFACES = {
    "admitExchangeArtifact",
    "cli:scheduler admit-exchange-artifact",
    "mcp:admitExchangeArtifact",
    "scheduler:exact-admission",
}

ACCEPTED_REVIEW_INTAKE_TARGET_SURFACES = {
    "reviewIntake",
    "cli:scheduler consume-accepted-review-candidate",
    "mcp:agentExchangeAcceptedReviewCandidateConsume",
    "review:intake",
}

ACCEPTED_HANDOFF_INTAKE_TARGET_SURFACES = {
    "handoffIntake",
    "cli:scheduler consume-accepted-handoff-candidate",
    "mcp:agentExchangeAcceptedHandoffCandidateConsume",
    "handoff:intake",
}

ACCEPTED_MERGE_INTAKE_TARGET_SURFACES = {
    "mergeIntake",
    "cli:scheduler consume-accepted-merge-candidate",
    "mcp:agentExchangeAcceptedMergeCandidateConsume",
    "scheduler:merge-gate-intake",
}

ACCEPTED_BLOCKER_STATE_TARGET_SURFACES = {
    "blockerState",
    "cli:scheduler consume-accepted-blocker-candidate",
    "mcp:agentExchangeAcceptedBlockerCandidateConsume",
    "scheduler:blocker-state",
}


@dataclass(frozen=True, slots=True)
class AcceptedSchedulerCandidateConsumptionResult:
    """Result of consuming one accepted scheduler action-candidate disposition."""

    artifact_store_path: Path
    disposition_artifact_id: str
    disposition_version: str
    candidate_id: str
    source_artifact_id: str
    source_version: str
    actor: str
    target_surface: str
    admission_result: Mapping[str, object]

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible consumption result."""

        ok = bool(self.admission_result.get("ok"))
        return {
            "ok": ok,
            "artifact_store_path": str(self.artifact_store_path),
            "disposition_artifact_id": self.disposition_artifact_id,
            "disposition_version": self.disposition_version,
            "candidate_id": self.candidate_id,
            "source_artifact_id": self.source_artifact_id,
            "source_version": self.source_version,
            "source": f"{self.source_artifact_id}@{self.source_version}",
            "actor": self.actor,
            "target_surface": self.target_surface,
            "admission_result": dict(self.admission_result),
            "authority_split": {
                "source": "accepted_action_candidate_disposition",
                "scheduler_mutated": ok,
                "admission_ledger_mutated": True,
                "exchange_store_mutated": bool(
                    self.admission_result.get("consumption_state", {}).get(
                        "exchange_store_mutated"
                    )
                ),
                "review_state_mutated": False,
                "handoff_mutated": False,
                "merge_gate_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class AcceptedReviewCandidateConsumptionResult:
    """Result of consuming one accepted review action-candidate disposition."""

    artifact_store_path: Path
    disposition_artifact_id: str
    disposition_version: str
    candidate_id: str
    source_artifact_id: str
    source_version: str
    actor: str
    target_surface: str
    review_intake_payload: Mapping[str, object]
    dispatch_result: Mapping[str, object]

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible review consumption result."""

        delivered = bool(self.dispatch_result.get("delivered"))
        return {
            "ok": delivered,
            "artifact_store_path": str(self.artifact_store_path),
            "disposition_artifact_id": self.disposition_artifact_id,
            "disposition_version": self.disposition_version,
            "candidate_id": self.candidate_id,
            "source_artifact_id": self.source_artifact_id,
            "source_version": self.source_version,
            "source": f"{self.source_artifact_id}@{self.source_version}",
            "actor": self.actor,
            "target_surface": self.target_surface,
            "review_intake_payload": dict(self.review_intake_payload),
            "dispatch_result": dict(self.dispatch_result),
            "authority_split": {
                "source": "accepted_action_candidate_disposition",
                "scheduler_mutated": False,
                "admission_ledger_mutated": False,
                "exchange_store_mutated": False,
                "review_state_mutated": delivered,
                "handoff_mutated": False,
                "merge_gate_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class AcceptedHandoffCandidateConsumptionResult:
    """Result of consuming one accepted handoff action-candidate disposition."""

    artifact_store_path: Path
    disposition_artifact_id: str
    disposition_version: str
    candidate_id: str
    source_artifact_id: str
    source_version: str
    actor: str
    target_surface: str
    handoff_payload: Mapping[str, object]
    dispatch_result: Mapping[str, object]

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible handoff consumption result."""

        delivered = bool(self.dispatch_result.get("delivered"))
        return {
            "ok": delivered,
            "artifact_store_path": str(self.artifact_store_path),
            "disposition_artifact_id": self.disposition_artifact_id,
            "disposition_version": self.disposition_version,
            "candidate_id": self.candidate_id,
            "source_artifact_id": self.source_artifact_id,
            "source_version": self.source_version,
            "source": f"{self.source_artifact_id}@{self.source_version}",
            "actor": self.actor,
            "target_surface": self.target_surface,
            "handoff_payload": dict(self.handoff_payload),
            "dispatch_result": dict(self.dispatch_result),
            "authority_split": {
                "source": "accepted_action_candidate_disposition",
                "scheduler_mutated": False,
                "admission_ledger_mutated": False,
                "exchange_store_mutated": False,
                "review_state_mutated": False,
                "handoff_mutated": delivered,
                "merge_gate_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class AcceptedMergeCandidateConsumptionResult:
    """Result of consuming one accepted merge action-candidate disposition."""

    artifact_store_path: Path
    disposition_artifact_id: str
    disposition_version: str
    candidate_id: str
    source_artifact_id: str
    source_version: str
    actor: str
    target_surface: str
    gate_id: str
    approved: bool
    reason: str
    snapshot_path: Path
    merge_gate_event_log_path: Path | None
    previous_gate_state: str
    current_gate_state: str
    target_task_id: str

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible merge consumption result."""

        return {
            "ok": True,
            "artifact_store_path": str(self.artifact_store_path),
            "disposition_artifact_id": self.disposition_artifact_id,
            "disposition_version": self.disposition_version,
            "candidate_id": self.candidate_id,
            "source_artifact_id": self.source_artifact_id,
            "source_version": self.source_version,
            "source": f"{self.source_artifact_id}@{self.source_version}",
            "actor": self.actor,
            "target_surface": self.target_surface,
            "gate_id": self.gate_id,
            "approved": self.approved,
            "reason": self.reason,
            "snapshot_path": str(self.snapshot_path),
            "merge_gate_event_log_path": (
                ""
                if self.merge_gate_event_log_path is None
                else str(self.merge_gate_event_log_path)
            ),
            "previous_gate_state": self.previous_gate_state,
            "current_gate_state": self.current_gate_state,
            "target_task_id": self.target_task_id,
            "authority_split": {
                "source": "accepted_action_candidate_disposition",
                "scheduler_mutated": True,
                "admission_ledger_mutated": False,
                "exchange_store_mutated": False,
                "review_state_mutated": False,
                "handoff_mutated": False,
                "merge_gate_mutated": True,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class AcceptedBlockerCandidateConsumptionResult:
    """Result of consuming one accepted blocker action-candidate disposition."""

    artifact_store_path: Path
    disposition_artifact_id: str
    disposition_version: str
    candidate_id: str
    source_artifact_id: str
    source_version: str
    actor: str
    target_surface: str
    task_id: str
    reason: str
    snapshot_path: Path
    event_log_path: Path | None
    previous_task_state: str
    current_task_state: str

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible blocker consumption result."""

        return {
            "ok": True,
            "artifact_store_path": str(self.artifact_store_path),
            "disposition_artifact_id": self.disposition_artifact_id,
            "disposition_version": self.disposition_version,
            "candidate_id": self.candidate_id,
            "source_artifact_id": self.source_artifact_id,
            "source_version": self.source_version,
            "source": f"{self.source_artifact_id}@{self.source_version}",
            "actor": self.actor,
            "target_surface": self.target_surface,
            "task_id": self.task_id,
            "reason": self.reason,
            "snapshot_path": str(self.snapshot_path),
            "event_log_path": "" if self.event_log_path is None else str(self.event_log_path),
            "previous_task_state": self.previous_task_state,
            "current_task_state": self.current_task_state,
            "authority_split": {
                "source": "accepted_action_candidate_disposition",
                "scheduler_mutated": True,
                "admission_ledger_mutated": False,
                "exchange_store_mutated": False,
                "review_state_mutated": False,
                "handoff_mutated": False,
                "merge_gate_mutated": False,
                "blocker_state_mutated": True,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }


def consume_accepted_scheduler_action_candidate(
    *,
    artifact_store_path: str | Path,
    disposition_artifact_id: str,
    disposition_version: str,
    snapshot_path: str | Path,
    event_log_path: str | Path,
    admission_ledger_path: str | Path,
    allow_duplicate_admission: bool = False,
    replace_existing: bool = False,
    validate_binding_artifact_refs: bool = False,
    mark_consumed_on_success: bool = False,
    actor: str = "operator",
    timestamp: str = "",
) -> AcceptedSchedulerCandidateConsumptionResult:
    """Consume an accepted scheduler candidate disposition via exact admission."""

    if not disposition_artifact_id:
        raise ValueError("accepted scheduler candidate consumer requires disposition_artifact_id")
    if not disposition_version:
        raise ValueError("accepted scheduler candidate consumer requires disposition_version")

    store_path = Path(artifact_store_path)
    try:
        record = JsonArtifactVersionStore(store_path).get(
            disposition_artifact_id,
            disposition_version,
        )
    except KeyError as exc:
        raise ValueError(
            f"disposition artifact version not found in {store_path}: "
            f"{disposition_artifact_id!r}@{disposition_version!r}"
        ) from exc

    payload = _disposition_payload(record.artifact)
    _validate_disposition_payload(payload, record.artifact)
    source_artifact_id = _required_payload_str(payload, "source_artifact_id", record.artifact)
    source_version = _required_payload_str(payload, "source_version", record.artifact)
    candidate_id = _required_payload_str(payload, "candidate_id", record.artifact)
    target_surface = _required_payload_str(payload, "target_surface", record.artifact)

    admission = admit_exchange_artifact_version_with_ledger(
        artifact_store_path=store_path,
        artifact_id=source_artifact_id,
        version=source_version,
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        admission_ledger_path=admission_ledger_path,
        allow_duplicate_admission=allow_duplicate_admission,
        replace_existing=replace_existing,
        validate_binding_artifact_refs=validate_binding_artifact_refs,
        mark_consumed_on_success=mark_consumed_on_success,
        actor=actor,
        surface="runtime:consume_accepted_scheduler_action_candidate",
        timestamp=timestamp,
    )
    return AcceptedSchedulerCandidateConsumptionResult(
        artifact_store_path=store_path,
        disposition_artifact_id=disposition_artifact_id,
        disposition_version=disposition_version,
        candidate_id=candidate_id,
        source_artifact_id=source_artifact_id,
        source_version=source_version,
        actor=actor,
        target_surface=target_surface,
        admission_result=admission,
    )


def consume_accepted_review_action_candidate(
    *,
    artifact_store_path: str | Path,
    disposition_artifact_id: str,
    disposition_version: str,
    review_intake_consumer: ReviewIntakeConsumer,
    actor: str = "operator",
) -> AcceptedReviewCandidateConsumptionResult:
    """Consume an accepted review candidate disposition through review intake."""

    if not disposition_artifact_id:
        raise ValueError("accepted review candidate consumer requires disposition_artifact_id")
    if not disposition_version:
        raise ValueError("accepted review candidate consumer requires disposition_version")

    store_path = Path(artifact_store_path)
    store = JsonArtifactVersionStore(store_path)
    try:
        disposition_record = store.get(
            disposition_artifact_id,
            disposition_version,
        )
    except KeyError as exc:
        raise ValueError(
            f"disposition artifact version not found in {store_path}: "
            f"{disposition_artifact_id!r}@{disposition_version!r}"
        ) from exc

    payload = _disposition_payload(disposition_record.artifact)
    _validate_review_disposition_payload(payload, disposition_record.artifact)
    source_artifact_id = _required_payload_str(
        payload,
        "source_artifact_id",
        disposition_record.artifact,
    )
    source_version = _required_payload_str(payload, "source_version", disposition_record.artifact)
    candidate_id = _required_payload_str(payload, "candidate_id", disposition_record.artifact)
    target_surface = _required_payload_str(payload, "target_surface", disposition_record.artifact)

    try:
        source_record = store.get(source_artifact_id, source_version)
    except KeyError as exc:
        raise ValueError(
            f"source review candidate artifact version not found in {store_path}: "
            f"{source_artifact_id!r}@{source_version!r}"
        ) from exc

    review_payload = _build_review_intake_payload(
        source_record.artifact,
        disposition_record.artifact,
        candidate_id=candidate_id,
        actor=actor,
    )
    dispatch = dispatch_landing_consumer_payload(
        BridgeLandingConsumerPayload(
            consumer_kind="review_intake",
            payload=review_payload,
        ),
        review_intake_consumer=review_intake_consumer,
    )
    return AcceptedReviewCandidateConsumptionResult(
        artifact_store_path=store_path,
        disposition_artifact_id=disposition_artifact_id,
        disposition_version=disposition_version,
        candidate_id=candidate_id,
        source_artifact_id=source_artifact_id,
        source_version=source_version,
        actor=actor,
        target_surface=target_surface,
        review_intake_payload=review_payload,
        dispatch_result=dispatch,
    )


def consume_accepted_handoff_action_candidate(
    *,
    artifact_store_path: str | Path,
    disposition_artifact_id: str,
    disposition_version: str,
    handoff_consumer: HandoffConsumer,
    actor: str = "operator",
) -> AcceptedHandoffCandidateConsumptionResult:
    """Consume an accepted handoff candidate disposition through handoff delivery."""

    if not disposition_artifact_id:
        raise ValueError("accepted handoff candidate consumer requires disposition_artifact_id")
    if not disposition_version:
        raise ValueError("accepted handoff candidate consumer requires disposition_version")

    store_path = Path(artifact_store_path)
    store = JsonArtifactVersionStore(store_path)
    try:
        disposition_record = store.get(
            disposition_artifact_id,
            disposition_version,
        )
    except KeyError as exc:
        raise ValueError(
            f"disposition artifact version not found in {store_path}: "
            f"{disposition_artifact_id!r}@{disposition_version!r}"
        ) from exc

    payload = _disposition_payload(disposition_record.artifact)
    _validate_handoff_disposition_payload(payload, disposition_record.artifact)
    source_artifact_id = _required_payload_str(
        payload,
        "source_artifact_id",
        disposition_record.artifact,
    )
    source_version = _required_payload_str(payload, "source_version", disposition_record.artifact)
    candidate_id = _required_payload_str(payload, "candidate_id", disposition_record.artifact)
    target_surface = _required_payload_str(payload, "target_surface", disposition_record.artifact)

    try:
        source_record = store.get(source_artifact_id, source_version)
    except KeyError as exc:
        raise ValueError(
            f"source handoff candidate artifact version not found in {store_path}: "
            f"{source_artifact_id!r}@{source_version!r}"
        ) from exc

    handoff_payload = _build_handoff_payload(
        source_record.artifact,
        disposition_record.artifact,
        candidate_id=candidate_id,
        actor=actor,
    )
    validation = handoff_validator.validate(
        handoff_payload,
        context={"mode": "handoff", "requires_review": True},
    )
    if not validation["valid"]:
        raise ValueError(
            "accepted handoff candidate produced invalid handoff payload: "
            + "; ".join(validation["errors"])
        )

    dispatch = dispatch_landing_consumer_payload(
        BridgeLandingConsumerPayload(
            consumer_kind="handoff",
            payload=handoff_payload,
        ),
        handoff_consumer=handoff_consumer,
    )
    return AcceptedHandoffCandidateConsumptionResult(
        artifact_store_path=store_path,
        disposition_artifact_id=disposition_artifact_id,
        disposition_version=disposition_version,
        candidate_id=candidate_id,
        source_artifact_id=source_artifact_id,
        source_version=source_version,
        actor=actor,
        target_surface=target_surface,
        handoff_payload=handoff_payload,
        dispatch_result=dispatch,
    )


def consume_accepted_merge_action_candidate(
    *,
    artifact_store_path: str | Path,
    disposition_artifact_id: str,
    disposition_version: str,
    snapshot_path: str | Path,
    gate_id: str,
    approved: bool,
    reason: str = "",
    merge_gate_event_log_path: str | Path | None = None,
    actor: str = "operator",
    resolved_at: str = "",
    timestamp: str = "",
) -> AcceptedMergeCandidateConsumptionResult:
    """Consume an accepted merge candidate disposition by resolving a merge gate."""

    if not disposition_artifact_id:
        raise ValueError("accepted merge candidate consumer requires disposition_artifact_id")
    if not disposition_version:
        raise ValueError("accepted merge candidate consumer requires disposition_version")
    if not gate_id:
        raise ValueError("accepted merge candidate consumer requires gate_id")

    store_path = Path(artifact_store_path)
    store = JsonArtifactVersionStore(store_path)
    try:
        disposition_record = store.get(
            disposition_artifact_id,
            disposition_version,
        )
    except KeyError as exc:
        raise ValueError(
            f"disposition artifact version not found in {store_path}: "
            f"{disposition_artifact_id!r}@{disposition_version!r}"
        ) from exc

    payload = _disposition_payload(disposition_record.artifact)
    _validate_merge_disposition_payload(payload, disposition_record.artifact)
    source_artifact_id = _required_payload_str(
        payload,
        "source_artifact_id",
        disposition_record.artifact,
    )
    source_version = _required_payload_str(payload, "source_version", disposition_record.artifact)
    candidate_id = _required_payload_str(payload, "candidate_id", disposition_record.artifact)
    target_surface = _required_payload_str(payload, "target_surface", disposition_record.artifact)

    try:
        store.get(source_artifact_id, source_version)
    except KeyError as exc:
        raise ValueError(
            f"source merge candidate artifact version not found in {store_path}: "
            f"{source_artifact_id!r}@{source_version!r}"
        ) from exc

    snapshot = Path(snapshot_path)
    state = read_scheduler_state_snapshot(snapshot)
    previous_gate = next((gate for gate in state.merge_gates if gate.gate_id == gate_id), None)
    if previous_gate is None:
        raise ValueError(f"unknown merge gate: {gate_id}")
    event_log_path = None if merge_gate_event_log_path is None else Path(merge_gate_event_log_path)
    event_log = None if event_log_path is None else JsonlSchedulerMergeGateEventLog(event_log_path)
    decision_ref = _disposition_decision_ref(disposition_record.artifact)
    updated = resolve_scheduler_merge_gate(
        state,
        gate_id,
        approved=approved,
        reason=reason or ("merge candidate accepted" if approved else "merge candidate rejected"),
        decision_artifact_ref=decision_ref,
        resolved_at=resolved_at,
        event_log=event_log,
        timestamp=timestamp or resolved_at,
    )
    write_scheduler_state_snapshot(updated, snapshot)
    current_gate = next(gate for gate in updated.merge_gates if gate.gate_id == gate_id)
    return AcceptedMergeCandidateConsumptionResult(
        artifact_store_path=store_path,
        disposition_artifact_id=disposition_artifact_id,
        disposition_version=disposition_version,
        candidate_id=candidate_id,
        source_artifact_id=source_artifact_id,
        source_version=source_version,
        actor=actor,
        target_surface=target_surface,
        gate_id=gate_id,
        approved=approved,
        reason=reason,
        snapshot_path=snapshot,
        merge_gate_event_log_path=event_log_path,
        previous_gate_state=previous_gate.state,
        current_gate_state=current_gate.state,
        target_task_id=current_gate.target_task_id,
    )


def consume_accepted_blocker_action_candidate(
    *,
    artifact_store_path: str | Path,
    disposition_artifact_id: str,
    disposition_version: str,
    snapshot_path: str | Path,
    task_id: str,
    reason: str,
    event_log_path: str | Path | None = None,
    actor: str = "operator",
    timestamp: str = "",
) -> AcceptedBlockerCandidateConsumptionResult:
    """Consume an accepted blocker candidate by explicitly blocking one task."""

    if not disposition_artifact_id:
        raise ValueError("accepted blocker candidate consumer requires disposition_artifact_id")
    if not disposition_version:
        raise ValueError("accepted blocker candidate consumer requires disposition_version")
    if not task_id:
        raise ValueError("accepted blocker candidate consumer requires task_id")
    if not reason:
        raise ValueError("accepted blocker candidate consumer requires reason")

    store_path = Path(artifact_store_path)
    store = JsonArtifactVersionStore(store_path)
    try:
        disposition_record = store.get(
            disposition_artifact_id,
            disposition_version,
        )
    except KeyError as exc:
        raise ValueError(
            f"disposition artifact version not found in {store_path}: "
            f"{disposition_artifact_id!r}@{disposition_version!r}"
        ) from exc

    payload = _disposition_payload(disposition_record.artifact)
    _validate_blocker_disposition_payload(payload, disposition_record.artifact)
    source_artifact_id = _required_payload_str(
        payload,
        "source_artifact_id",
        disposition_record.artifact,
    )
    source_version = _required_payload_str(payload, "source_version", disposition_record.artifact)
    candidate_id = _required_payload_str(payload, "candidate_id", disposition_record.artifact)
    target_surface = _required_payload_str(payload, "target_surface", disposition_record.artifact)

    try:
        store.get(source_artifact_id, source_version)
    except KeyError as exc:
        raise ValueError(
            f"source blocker candidate artifact version not found in {store_path}: "
            f"{source_artifact_id!r}@{source_version!r}"
        ) from exc

    snapshot = Path(snapshot_path)
    state = read_scheduler_state_snapshot(snapshot)
    task = state.tasks.get(task_id)
    if task is None:
        raise ValueError(f"unknown scheduler task: {task_id}")
    blocked = replace(task, state="blocked", blocked_reason=reason)
    updated_tasks = dict(state.tasks)
    updated_tasks[task_id] = blocked
    updated = replace(state, tasks=updated_tasks)
    write_scheduler_state_snapshot(updated, snapshot)
    log_path = None if event_log_path is None else Path(event_log_path)
    if log_path is not None:
        JsonlSchedulerEventLog(log_path).append(
            SchedulerEvent(
                event_id=f"event-agent-exchange-blocker-{_safe_handoff_token(task_id)}",
                event_kind="task_blocked",
                timestamp=timestamp,
                task_id=task_id,
                from_state=task.state,
                to_state="blocked",
                reason=reason,
                related_artifact_ids=(disposition_artifact_id, source_artifact_id),
            )
        )
    return AcceptedBlockerCandidateConsumptionResult(
        artifact_store_path=store_path,
        disposition_artifact_id=disposition_artifact_id,
        disposition_version=disposition_version,
        candidate_id=candidate_id,
        source_artifact_id=source_artifact_id,
        source_version=source_version,
        actor=actor,
        target_surface=target_surface,
        task_id=task_id,
        reason=reason,
        snapshot_path=snapshot,
        event_log_path=log_path,
        previous_task_state=task.state,
        current_task_state="blocked",
    )


def _disposition_payload(artifact: ExchangeArtifact) -> Mapping[str, object]:
    matches = [
        part.data
        for part in artifact.parts
        if part.part_type == "structured"
        and part.data.get("product_type") == ACTION_CANDIDATE_DISPOSITION_PRODUCT_TYPE
    ]
    if not matches:
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} does not contain "
            f"product_type={ACTION_CANDIDATE_DISPOSITION_PRODUCT_TYPE!r}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} contains multiple "
            f"{ACTION_CANDIDATE_DISPOSITION_PRODUCT_TYPE!r} payloads"
        )
    return matches[0]


def _validate_disposition_payload(
    payload: Mapping[str, object],
    artifact: ExchangeArtifact,
) -> None:
    disposition = _required_payload_str(payload, "disposition", artifact)
    if disposition != "accept":
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} is {disposition!r}; "
            "only accepted scheduler candidates can be consumed"
        )
    candidate_type = _required_payload_str(payload, "candidate_type", artifact)
    if candidate_type != "scheduler_submission_candidate":
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} candidate_type "
            f"{candidate_type!r} is not scheduler_submission_candidate"
        )
    target_surface = _required_payload_str(payload, "target_surface", artifact)
    if target_surface not in ACCEPTED_SCHEDULER_ADMISSION_TARGET_SURFACES:
        allowed = ", ".join(sorted(ACCEPTED_SCHEDULER_ADMISSION_TARGET_SURFACES))
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} target_surface "
            f"{target_surface!r} is not an exact scheduler admission surface; "
            f"expected one of: {allowed}"
        )


def _validate_review_disposition_payload(
    payload: Mapping[str, object],
    artifact: ExchangeArtifact,
) -> None:
    disposition = _required_payload_str(payload, "disposition", artifact)
    if disposition != "accept":
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} is {disposition!r}; "
            "only accepted review candidates can be consumed"
        )
    candidate_type = _required_payload_str(payload, "candidate_type", artifact)
    if candidate_type != "review_candidate":
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} candidate_type "
            f"{candidate_type!r} is not review_candidate"
        )
    target_surface = _required_payload_str(payload, "target_surface", artifact)
    if target_surface not in ACCEPTED_REVIEW_INTAKE_TARGET_SURFACES:
        allowed = ", ".join(sorted(ACCEPTED_REVIEW_INTAKE_TARGET_SURFACES))
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} target_surface "
            f"{target_surface!r} is not a review intake surface; expected one of: {allowed}"
        )


def _validate_handoff_disposition_payload(
    payload: Mapping[str, object],
    artifact: ExchangeArtifact,
) -> None:
    disposition = _required_payload_str(payload, "disposition", artifact)
    if disposition != "accept":
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} is {disposition!r}; "
            "only accepted handoff candidates can be consumed"
        )
    candidate_type = _required_payload_str(payload, "candidate_type", artifact)
    if candidate_type != "handoff_candidate":
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} candidate_type "
            f"{candidate_type!r} is not handoff_candidate"
        )
    target_surface = _required_payload_str(payload, "target_surface", artifact)
    if target_surface not in ACCEPTED_HANDOFF_INTAKE_TARGET_SURFACES:
        allowed = ", ".join(sorted(ACCEPTED_HANDOFF_INTAKE_TARGET_SURFACES))
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} target_surface "
            f"{target_surface!r} is not a handoff intake surface; expected one of: {allowed}"
        )


def _validate_merge_disposition_payload(
    payload: Mapping[str, object],
    artifact: ExchangeArtifact,
) -> None:
    disposition = _required_payload_str(payload, "disposition", artifact)
    if disposition != "accept":
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} is {disposition!r}; "
            "only accepted merge candidates can be consumed"
        )
    candidate_type = _required_payload_str(payload, "candidate_type", artifact)
    if candidate_type != "merge_candidate":
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} candidate_type "
            f"{candidate_type!r} is not merge_candidate"
        )
    target_surface = _required_payload_str(payload, "target_surface", artifact)
    if target_surface not in ACCEPTED_MERGE_INTAKE_TARGET_SURFACES:
        allowed = ", ".join(sorted(ACCEPTED_MERGE_INTAKE_TARGET_SURFACES))
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} target_surface "
            f"{target_surface!r} is not a merge intake surface; expected one of: {allowed}"
        )


def _validate_blocker_disposition_payload(
    payload: Mapping[str, object],
    artifact: ExchangeArtifact,
) -> None:
    disposition = _required_payload_str(payload, "disposition", artifact)
    if disposition != "accept":
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} is {disposition!r}; "
            "only accepted blocker candidates can be consumed"
        )
    candidate_type = _required_payload_str(payload, "candidate_type", artifact)
    if candidate_type != "blocker_candidate":
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} candidate_type "
            f"{candidate_type!r} is not blocker_candidate"
        )
    target_surface = _required_payload_str(payload, "target_surface", artifact)
    if target_surface not in ACCEPTED_BLOCKER_STATE_TARGET_SURFACES:
        allowed = ", ".join(sorted(ACCEPTED_BLOCKER_STATE_TARGET_SURFACES))
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} target_surface "
            f"{target_surface!r} is not a blocker state surface; expected one of: {allowed}"
        )


def _disposition_decision_ref(artifact: ExchangeArtifact) -> ExchangeReference:
    return ExchangeReference(
        ref_kind="exchange_artifact",
        ref_id=artifact.artifact_id,
        version=artifact.version,
        label="accepted_action_candidate_disposition",
    )


def _build_handoff_payload(
    source: ExchangeArtifact,
    disposition: ExchangeArtifact,
    *,
    candidate_id: str,
    actor: str,
) -> dict[str, object]:
    authoritative_refs = _authoritative_refs(source)
    open_items = _review_open_items(source)
    return {
        "handoff_id": f"handoff-agent-exchange-{_safe_handoff_token(source.artifact_id)}-{_safe_handoff_token(source.version)}",
        "from_role": source.producer or "agent",
        "to_role": _handoff_target_role(source),
        "reason": _handoff_reason(source),
        "active_scope": _scope_summary(source),
        "authoritative_refs": authoritative_refs or ["AGENTS.md"],
        "carried_constraints": _carried_constraints(source),
        "open_items": open_items
        or [f"Continue from ExchangeArtifact {source.artifact_id}@{source.version}"],
        "current_gate_state": _handoff_gate_state(source),
        "intake_requirements": [
            "Re-read authoritative_refs before proceeding",
            f"Inspect source ExchangeArtifact {source.artifact_id}@{source.version}",
            f"Inspect disposition ExchangeArtifact {disposition.artifact_id}@{disposition.version}",
            f"Preserve action candidate id {candidate_id}",
            f"Requested by {actor}",
        ],
    }


def _handoff_target_role(source: ExchangeArtifact) -> str:
    for part in source.parts:
        if part.part_type == "structured":
            for key in ("to_role", "target_role", "handoff_to"):
                value = part.data.get(key)
                if isinstance(value, str) and value:
                    return value
    if source.audience:
        return source.audience[0]
    return "human-reviewer"


def _handoff_reason(source: ExchangeArtifact) -> str:
    for part in source.parts:
        if part.part_type == "structured":
            reason = part.data.get("reason")
            if isinstance(reason, str) and reason:
                return reason
    return f"handoff requested for {source.artifact_id}@{source.version}"


def _handoff_gate_state(source: ExchangeArtifact) -> str:
    allowed = {"waiting_review", "approved", "rejected", "revised", "applied"}
    for part in source.parts:
        if part.part_type == "structured":
            value = part.data.get("current_gate_state")
            if isinstance(value, str) and value in allowed:
                return value
    return "waiting_review"


def _carried_constraints(source: ExchangeArtifact) -> list[str]:
    constraints: list[str] = []
    for part in source.parts:
        if part.part_type == "structured":
            value = part.data.get("carried_constraints")
            if isinstance(value, list):
                constraints.extend(str(item) for item in value if item)
            item = part.data.get("carried_constraint")
            if item:
                constraints.append(str(item))
    return list(dict.fromkeys(constraints))


def _safe_handoff_token(value: str) -> str:
    token = "".join(ch if ch.isalnum() else "-" for ch in value).strip("-").lower()
    return token or "artifact"


def _build_review_intake_payload(
    source: ExchangeArtifact,
    disposition: ExchangeArtifact,
    *,
    candidate_id: str,
    actor: str,
) -> dict[str, object]:
    open_items = _review_open_items(source)
    authoritative_refs = _authoritative_refs(source)
    return {
        "review_object_id": f"agent-exchange-review-{source.artifact_id}-{source.version}",
        "review_state": "waiting_review",
        "gate_level": "review",
        "reason": _review_reason(source),
        "active_scope": _scope_summary(source),
        "task_group_id": source.scope.task_id,
        "dominant_group_item_ids": [
            value for value in (source.scope.lane_id, source.scope.event_id) if value
        ],
        "authoritative_refs": authoritative_refs or ["AGENTS.md"],
        "open_items": open_items
        or [f"Review ExchangeArtifact {source.artifact_id}@{source.version}"],
        "allowed_feedback": ["approve", "reject", "request_revision"],
        "source_exchange_artifact": {
            "artifact_id": source.artifact_id,
            "version": source.version,
            "kind": source.kind,
            "intent": source.intent,
            "producer": source.producer,
            "audience": list(source.audience),
        },
        "disposition_exchange_artifact": {
            "artifact_id": disposition.artifact_id,
            "version": disposition.version,
            "producer": disposition.producer,
        },
        "action_candidate_id": candidate_id,
        "requested_by": actor,
    }


def _review_reason(source: ExchangeArtifact) -> str:
    for part in source.parts:
        if part.part_type == "structured":
            reason = part.data.get("reason")
            if isinstance(reason, str) and reason:
                return reason
    if source.intent == "require_review":
        return "agent exchange artifact requires review"
    return f"review requested for {source.artifact_id}@{source.version}"


def _review_open_items(source: ExchangeArtifact) -> list[str]:
    items: list[str] = []
    for part in source.parts:
        if part.part_type == "structured":
            value = part.data.get("open_items")
            if isinstance(value, list):
                items.extend(str(item) for item in value if item)
            item = part.data.get("open_item")
            if item:
                items.append(str(item))
        elif part.part_type == "text" and part.text:
            items.append(part.text)
    return list(dict.fromkeys(items))


def _authoritative_refs(source: ExchangeArtifact) -> list[str]:
    refs: list[str] = []
    for part in source.parts:
        if part.part_type == "ref" and part.ref is not None:
            refs.append(str(part.ref.label or part.ref.ref_id))
        elif part.part_type == "structured":
            value = part.data.get("authoritative_refs")
            if isinstance(value, list):
                refs.extend(str(item) for item in value if item)
    return list(dict.fromkeys(refs))


def _scope_summary(source: ExchangeArtifact) -> str:
    values = [
        source.scope.trajectory_id,
        source.scope.lane_id,
        source.scope.event_id,
        source.scope.task_id,
        source.scope.context_id,
        source.scope.agent_id,
    ]
    summary = " / ".join(value for value in values if value)
    return summary or f"exchange:{source.artifact_id}@{source.version}"


def _required_payload_str(
    payload: Mapping[str, object],
    key: str,
    artifact: ExchangeArtifact,
) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} requires non-empty string "
            f"field {key!r}"
        )
    return value
