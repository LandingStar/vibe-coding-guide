"""Dogfood issue promotion and feedback packet pipeline.

Implements the evidence → issue promotion → feedback packet → consumer
dispatch pipeline defined in:
- design_docs/dogfood-evidence-issue-feedback-boundary.md
- design_docs/dogfood-promotion-packet-interface-draft.md
"""

from __future__ import annotations

from typing import Any

from .builder import assemble_feedback_packet, build_issue_candidate
from .dispatcher import dispatch_to_consumers
from .evaluator import evaluate_promotion
from .models import (
    Confidence,
    ConsumerName,
    ConsumerPayload,
    EvidenceRef,
    FeedbackPacket,
    ImpactLayer,
    IssueCandidate,
    IssueCategory,
    PromotionDecision,
    PromotionVerdict,
)


def run_full_pipeline(
    symptoms: list[dict[str, Any]],
    existing_issue_ids: list[str] | None = None,
    date: str = "",
    judgment: str = "",
    next_step_implication: str = "",
    confidence: str = "medium",
    non_goals: tuple[str, ...] = (),
    supersedes: str | None = None,
) -> dict[str, Any]:
    """Run the complete dogfood pipeline: evaluate → build → assemble → dispatch.

    This is the single-call coordinator used by the MCP tool.

    Parameters
    ----------
    symptoms:
        Each dict must include: symptom_id, symptom_summary, evidence_refs,
        category, affects_next_gate, requires_next_slice, occurrence_count.
        Additionally, for building issue candidates: impact_layers,
        minimal_reproducer, expected, actual, evidence_excerpt, environment,
        non_goals.
    existing_issue_ids:
        Previously known issue IDs for S2 de-duplication.
    date:
        Date label in ``YYYY-MM-DD`` format.
    judgment:
        Human/domain judgment summary for the feedback packet.
    next_step_implication:
        What the next planning step should consider.
    confidence:
        One of ``high``, ``medium``, ``low``.
    non_goals:
        Explicit list of what the feedback packet does NOT address.
    supersedes:
        Packet ID this feedback replaces, if any.

    Returns
    -------
    dict with keys: decisions, promoted_issues, packet, consumer_payloads.
    """
    # --- Build evidence refs from symptoms ---
    all_evidence_refs: list[EvidenceRef] = []
    for s in symptoms:
        for ref in s.get("evidence_refs", []):
            if isinstance(ref, EvidenceRef):
                all_evidence_refs.append(ref)
            elif isinstance(ref, dict):
                all_evidence_refs.append(EvidenceRef(
                    path=ref.get("path", ""),
                    section=ref.get("section"),
                    summary=ref.get("summary", ""),
                ))

    # --- Build stub existing_issues for S2 check ---
    existing_issues: list[IssueCandidate] = []
    for iid in (existing_issue_ids or []):
        existing_issues.append(IssueCandidate(
            issue_id=iid,
            title="",
            problem_statement=iid,
            category=IssueCategory.WORKFLOW_STATE_SYNC_GAP,
            impact_layers=(ImpactLayer.WORKFLOW,),
            minimal_reproducer="",
            expected="",
            actual="",
            evidence_refs=(),
            evidence_excerpt="",
            environment="",
            promotion_reason="",
        ))

    # --- Step 1: Evaluate ---
    decisions = evaluate_promotion(all_evidence_refs, existing_issues, symptoms)

    decisions_out = [
        {
            "symptom_id": d.symptom_id,
            "verdict": d.verdict.value,
            "reason": d.reason,
            "triggered_conditions": list(d.triggered_conditions),
            "suppressed_conditions": list(d.suppressed_conditions),
        }
        for d in decisions
    ]

    # --- Step 2: Build issue candidates for PROMOTE decisions ---
    promoted = [d for d in decisions if d.verdict is PromotionVerdict.PROMOTE]
    candidates: list[IssueCandidate] = []

    for seq, decision in enumerate(promoted, start=1):
        # Find matching symptom dict for domain-judgment fields
        sym = next(
            (s for s in symptoms if s["symptom_id"] == decision.symptom_id),
            {},
        )

        raw_category = sym.get("category", "workflow/state-sync gap")
        try:
            category = IssueCategory(raw_category)
        except ValueError:
            category = IssueCategory.WORKFLOW_STATE_SYNC_GAP

        raw_layers = sym.get("impact_layers", ["workflow"])
        impact_layers: list[ImpactLayer] = []
        for layer in raw_layers:
            try:
                impact_layers.append(ImpactLayer(layer))
            except ValueError:
                pass
        if not impact_layers:
            impact_layers.append(ImpactLayer.WORKFLOW)

        candidate = build_issue_candidate(
            decision,
            seq=seq,
            category=category,
            impact_layers=tuple(impact_layers),
            minimal_reproducer=sym.get("minimal_reproducer", ""),
            expected=sym.get("expected", ""),
            actual=sym.get("actual", ""),
            evidence_excerpt=sym.get("evidence_excerpt", ""),
            environment=sym.get("environment", ""),
            non_goals=tuple(sym.get("non_goals", ())),
        )
        candidates.append(candidate)

    promoted_out = [
        {
            "issue_id": c.issue_id,
            "title": c.title,
            "category": c.category.value,
            "impact_layers": [l.value for l in c.impact_layers],
            "promotion_reason": c.promotion_reason,
            "environment": c.environment,
        }
        for c in candidates
    ]

    # --- Step 3 & 4: Assemble packet + dispatch (only if any promoted) ---
    packet_out: dict[str, Any] | None = None
    payloads_out: dict[str, Any] | None = None

    if candidates:
        conf = Confidence(confidence) if confidence in ("high", "medium", "low") else Confidence.MEDIUM

        packet = assemble_feedback_packet(
            candidates,
            all_evidence_refs,
            seq=1,
            date=date,
            judgment=judgment,
            next_step_implication=next_step_implication,
            confidence=conf,
            non_goals=non_goals,
            supersedes=supersedes,
        )

        packet_out = {
            "packet_id": packet.packet_id,
            "source_issues": list(packet.source_issues),
            "source_evidence": list(packet.source_evidence),
            "judgment": packet.judgment,
            "next_step_implication": packet.next_step_implication,
            "affected_docs": list(packet.affected_docs),
            "affected_layers": [l.value for l in packet.affected_layers],
            "confidence": packet.confidence.value,
            "non_goals": list(packet.non_goals),
        }
        if packet.supersedes:
            packet_out["supersedes"] = packet.supersedes

        consumer_payloads = dispatch_to_consumers(packet)
        payloads_out = {}
        for consumer, payload in consumer_payloads.items():
            serialized_fields: dict[str, Any] = {}
            for k, v in payload.fields.items():
                if isinstance(v, tuple):
                    serialized_fields[k] = [
                        x.value if hasattr(x, "value") else x for x in v
                    ]
                elif hasattr(v, "value"):
                    serialized_fields[k] = v.value
                else:
                    serialized_fields[k] = v
            payloads_out[consumer.value] = serialized_fields

    return {
        "decisions": decisions_out,
        "promoted_issues": promoted_out,
        "packet": packet_out,
        "consumer_payloads": payloads_out,
    }
