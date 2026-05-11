"""Dispatch landing consumer payloads onto existing delivery surfaces."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from src.interfaces import EscalationNotifier
from src.pep.executor import persist_handoff_json
from src.review.feedback_api import FeedbackAPI
from src.review.state_machine import PROPOSED, SUBMIT_FOR_REVIEW, ReviewStateMachine

from .landing_consumers import BridgeLandingConsumerPayload


class HandoffConsumer(Protocol):
    """Deliver a validated handoff payload to the chosen handoff surface."""

    def deliver(self, handoff: dict[str, object]) -> dict[str, object]:
        """Return a delivery result for *handoff*."""


class ReviewIntakeConsumer(Protocol):
    """Register a bridge review intake entry on the existing review surface."""

    def register(self, review_entry: dict[str, object]) -> dict[str, object]:
        """Return a registration result for *review_entry*."""


class FileHandoffConsumer:
    """Persist landing handoff payloads using the executor handoff layout."""

    def __init__(self, handoff_dir: str | Path) -> None:
        self._handoff_dir = Path(handoff_dir)

    def deliver(self, handoff: dict[str, object]) -> dict[str, object]:
        path = persist_handoff_json(self._handoff_dir, handoff)
        return {
            "delivered": True,
            "handoff_id": handoff.get("handoff_id"),
            "channel": "handoff-json",
            "path": str(path),
        }


class FeedbackAPIReviewIntakeConsumer:
    """Register bridge review intake payloads on the existing FeedbackAPI."""

    def __init__(self, feedback_api: FeedbackAPI) -> None:
        self._feedback_api = feedback_api

    def register(self, review_entry: dict[str, object]) -> dict[str, object]:
        envelope = _build_review_intake_envelope(review_entry)
        result = _build_review_intake_result(review_entry)
        self._feedback_api.register(envelope, result)
        return {
            "registered": True,
            "review_object_id": result["envelope_id"],
            "pending_count": len(self._feedback_api.list_pending()),
        }


def dispatch_landing_consumer_payload(
    consumer_payload: BridgeLandingConsumerPayload,
    *,
    handoff_consumer: HandoffConsumer | None = None,
    escalation_notifier: EscalationNotifier | None = None,
    review_intake_consumer: ReviewIntakeConsumer | None = None,
) -> dict[str, object]:
    """Dispatch a normalized landing payload to the matching owner surface."""

    if consumer_payload.consumer_kind == "handoff":
        if handoff_consumer is None:
            return _dispatch_failure(
                consumer_kind="handoff",
                target_surface="handoff_consumer.deliver",
                detail="handoff consumer is not configured",
            )
        return _dispatch_with_handler(
            consumer_kind="handoff",
            target_surface="handoff_consumer.deliver",
            payload=consumer_payload.payload,
            handler=handoff_consumer.deliver,
            record_id_key="handoff_id",
        )

    if consumer_payload.consumer_kind == "escalation_notification":
        if escalation_notifier is None:
            return _dispatch_failure(
                consumer_kind="escalation_notification",
                target_surface="EscalationNotifier.notify",
                detail="escalation notifier is not configured",
            )
        return _dispatch_with_handler(
            consumer_kind="escalation_notification",
            target_surface="EscalationNotifier.notify",
            payload=consumer_payload.payload,
            handler=escalation_notifier.notify,
        )

    if consumer_payload.consumer_kind == "review_intake":
        if review_intake_consumer is None:
            return _dispatch_failure(
                consumer_kind="review_intake",
                target_surface="review_intake_consumer.register",
                detail="review intake consumer is not configured",
            )
        return _dispatch_with_handler(
            consumer_kind="review_intake",
            target_surface="review_intake_consumer.register",
            payload=consumer_payload.payload,
            handler=review_intake_consumer.register,
            record_id_key="review_object_id",
        )

    return _dispatch_failure(
        consumer_kind=consumer_payload.consumer_kind,
        target_surface="unknown",
        detail=f"unsupported consumer kind: {consumer_payload.consumer_kind}",
    )


def _dispatch_with_handler(
    *,
    consumer_kind: str,
    target_surface: str,
    payload: dict[str, object],
    handler: object,
    record_id_key: str | None = None,
) -> dict[str, object]:
    try:
        consumer_result = handler(payload)
    except Exception as exc:
        return _dispatch_failure(
            consumer_kind=consumer_kind,
            target_surface=target_surface,
            detail=str(exc),
            consumer_result={"error": str(exc)},
            record_id=payload.get(record_id_key) if record_id_key else None,
        )

    normalized_result = _normalize_consumer_result(consumer_result)
    record_id = None
    if record_id_key is not None:
        record_id = normalized_result.get(record_id_key) or payload.get(record_id_key)

    delivered = _coerce_delivered(normalized_result)
    detail = (
        f"dispatched via {target_surface}"
        if delivered
        else f"dispatch via {target_surface} was not accepted"
    )
    return {
        "delivered": delivered,
        "consumer_kind": consumer_kind,
        "target_surface": target_surface,
        "record_id": record_id,
        "detail": detail,
        "consumer_result": normalized_result,
    }


def _normalize_consumer_result(result: object) -> dict[str, object]:
    if isinstance(result, dict):
        return result
    return {"raw_result": result}


def _coerce_delivered(result: dict[str, object]) -> bool:
    if "delivered" in result:
        return bool(result["delivered"])
    if "registered" in result:
        return bool(result["registered"])
    return True


def _dispatch_failure(
    *,
    consumer_kind: str,
    target_surface: str,
    detail: str,
    consumer_result: dict[str, object] | None = None,
    record_id: object = None,
) -> dict[str, object]:
    return {
        "delivered": False,
        "consumer_kind": consumer_kind,
        "target_surface": target_surface,
        "record_id": record_id,
        "detail": detail,
        "consumer_result": consumer_result or {},
    }


def _build_review_intake_envelope(review_entry: dict[str, object]) -> dict[str, object]:
    review_object_id = str(review_entry.get("review_object_id") or "bridge-review")
    gate_level = str(review_entry.get("gate_level") or "review")
    return {
        "decision_id": review_object_id,
        "intent_result": {"intent": "bridge_reviewer_takeover"},
        "gate_decision": {"gate_level": gate_level},
        "bridge_review_intake": review_entry,
    }


def _build_review_intake_result(review_entry: dict[str, object]) -> dict[str, object]:
    review_object_id = str(review_entry.get("review_object_id") or "bridge-review")
    gate_level = str(review_entry.get("gate_level") or "review")
    review_state = str(review_entry.get("review_state") or "waiting_review")

    if review_state == PROPOSED:
        rsm = ReviewStateMachine(object_id=review_object_id, gate_level=gate_level)
    elif review_state == "waiting_review":
        rsm = ReviewStateMachine(object_id=review_object_id, gate_level=gate_level)
        rsm.transition(
            SUBMIT_FOR_REVIEW,
            reason=str(review_entry.get("reason") or "bridge reviewer takeover"),
        )
    else:
        rsm = ReviewStateMachine(
            object_id=review_object_id,
            initial_state=review_state,
            gate_level=gate_level,
        )

    open_items = review_entry.get("open_items")
    unresolved_items = open_items if isinstance(open_items, list) else []
    task_group_id = review_entry.get("task_group_id")

    return {
        "envelope_id": review_object_id,
        "execution_status": rsm.current_state,
        "detail": str(review_entry.get("reason") or "bridge reviewer takeover"),
        "review_state": rsm.current_state,
        "review_history": rsm.history,
        "grouped_review_outcome": {
            "task_group_id": task_group_id,
            "outcome": "review_required",
            "unresolved_items": unresolved_items,
        },
        "grouped_review_state": rsm.current_state,
        "bridge_review_intake": review_entry,
        "_rsm": rsm,
    }