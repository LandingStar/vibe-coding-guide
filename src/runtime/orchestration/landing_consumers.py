"""Consumer payload builders for orchestration landing artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import uuid4

from src.subagent import handoff_validator

from .landing import BridgeLandingArtifact

BridgeLandingConsumerKind = Literal[
    "handoff",
    "escalation_notification",
    "review_intake",
]


@dataclass(frozen=True, slots=True)
class BridgeLandingConsumerPayload:
    """A landing artifact mapped onto an existing consumer surface."""

    consumer_kind: BridgeLandingConsumerKind
    payload: dict[str, object]


def build_landing_consumer_payload(
    artifact: BridgeLandingArtifact,
) -> BridgeLandingConsumerPayload:
    """Map a landing artifact to the nearest existing consumer payload."""

    if artifact.landing_kind == "handoff":
        payload = _build_handoff_payload(artifact)
        validation = handoff_validator.validate(
            payload,
            context={"mode": "handoff", "requires_review": True},
        )
        if not validation["valid"]:
            raise ValueError(
                "landing handoff payload failed validation: "
                + "; ".join(validation["errors"])
            )
        return BridgeLandingConsumerPayload(consumer_kind="handoff", payload=payload)

    if artifact.landing_kind == "escalation":
        return BridgeLandingConsumerPayload(
            consumer_kind="escalation_notification",
            payload=_build_escalation_notification(artifact),
        )

    if artifact.landing_kind == "reviewer_takeover":
        return BridgeLandingConsumerPayload(
            consumer_kind="review_intake",
            payload=_build_review_intake_payload(artifact),
        )

    raise ValueError(f"unsupported landing kind: {artifact.landing_kind}")


def _build_handoff_payload(artifact: BridgeLandingArtifact) -> dict[str, object]:
    return {
        "handoff_id": f"handoff-{uuid4().hex[:12]}",
        "from_role": "main-ai",
        "to_role": "human-reviewer",
        "reason": artifact.reason or "handoff_requested",
        "active_scope": artifact.active_scope,
        "authoritative_refs": list(artifact.authoritative_refs) or ["AGENTS.md"],
        "carried_constraints": [],
        "open_items": list(artifact.open_items),
        "current_gate_state": artifact.current_gate_state or "waiting_review",
        "intake_requirements": list(artifact.intake_requirements)
        or ["Re-read authoritative_refs before proceeding"],
    }


def _build_escalation_notification(
    artifact: BridgeLandingArtifact,
) -> dict[str, object]:
    return {
        "type": "escalation",
        "escalate": True,
        "target_authority": "human_reviewer",
        "reason": artifact.reason or "escalation_requested",
        "active_scope": artifact.active_scope,
        "task_group_id": artifact.task_group_id,
        "dominant_group_item_ids": list(artifact.dominant_group_item_ids),
        "current_gate_state": artifact.current_gate_state or "waiting_review",
        "open_items": list(artifact.open_items),
        "suggested_action": "Review escalation landing artifact",
    }


def _build_review_intake_payload(
    artifact: BridgeLandingArtifact,
) -> dict[str, object]:
    return {
        "review_object_id": f"bridge-review-{artifact.work_item_id}",
        "review_state": artifact.current_gate_state or "waiting_review",
        "gate_level": "review",
        "reason": artifact.reason or "review_required",
        "active_scope": artifact.active_scope,
        "task_group_id": artifact.task_group_id,
        "dominant_group_item_ids": list(artifact.dominant_group_item_ids),
        "authoritative_refs": list(artifact.authoritative_refs) or ["AGENTS.md"],
        "open_items": list(artifact.open_items),
        "allowed_feedback": ["approve", "reject", "request_revision"],
    }