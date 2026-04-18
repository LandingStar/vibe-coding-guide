"""Dispatch a FeedbackPacket to consumers per the boundary matrix.

Implements the consumer boundary contract from:
- design_docs/dogfood-evidence-issue-feedback-boundary.md §消费者边界 Contract
"""

from __future__ import annotations

from src.dogfood.models import (
    ConsumerName,
    ConsumerPayload,
    FeedbackPacket,
)

# Consumer boundary matrix: maps each consumer to the packet fields it may access.
_CONSUMER_FIELDS: dict[ConsumerName, tuple[str, ...]] = {
    ConsumerName.DIRECTION_CANDIDATES: (
        "judgment",
        "next_step_implication",
        "affected_layers",
        "source_issues",
    ),
    ConsumerName.CHECKLIST: (
        "packet_id",
        "judgment",
        "affected_docs",
    ),
    ConsumerName.PHASE_MAP: (
        "packet_id",
        "affected_layers",
    ),
    ConsumerName.CHECKPOINT: (
        "packet_id",
        "judgment",
        "next_step_implication",
        "confidence",
    ),
    ConsumerName.HANDOFF: (
        "packet_id",
        "judgment",
        "next_step_implication",
        "affected_docs",
        "non_goals",
    ),
    ConsumerName.PLANNING_GATE: (
        "packet_id",
        "source_issues",
        "source_evidence",
        "judgment",
        "next_step_implication",
        "affected_docs",
        "affected_layers",
        "non_goals",
        "confidence",
        "supersedes",
        "blocking_issues",
        "raw_data_pointers",
    ),
}


def dispatch_to_consumers(
    packet: FeedbackPacket,
) -> dict[ConsumerName, ConsumerPayload]:
    """Trim *packet* per the consumer boundary matrix.

    Returns a dict mapping each consumer to a :class:`ConsumerPayload`
    containing only the allowed field subset.  The original *packet* is
    never modified (it is frozen/immutable by design).
    """
    result: dict[ConsumerName, ConsumerPayload] = {}
    for consumer, allowed in _CONSUMER_FIELDS.items():
        trimmed: dict[str, object] = {}
        for field_name in allowed:
            value = getattr(packet, field_name, None)
            if value is not None:
                trimmed[field_name] = value
        result[consumer] = ConsumerPayload(consumer=consumer, fields=trimmed)
    return result
