"""Issue candidate builder and feedback packet assembler.

Implements the build_issue_candidate and assemble_feedback_packet functions from:
- design_docs/dogfood-promotion-packet-interface-draft.md §2.2, §2.3
"""

from __future__ import annotations

from src.dogfood.models import (
    Confidence,
    EvidenceRef,
    FeedbackPacket,
    ImpactLayer,
    IssueCandidate,
    IssueCategory,
    PromotionDecision,
    PromotionVerdict,
    RootCauseHypothesis,
)


def build_issue_candidate(
    decision: PromotionDecision,
    *,
    seq: int,
    category: IssueCategory,
    impact_layers: tuple[ImpactLayer, ...],
    minimal_reproducer: str,
    expected: str,
    actual: str,
    evidence_excerpt: str,
    environment: str,
    non_goals: tuple[str, ...],
    root_cause_hypothesis: RootCauseHypothesis | None = None,
) -> IssueCandidate:
    """Build an :class:`IssueCandidate` from a PROMOTE decision.

    The caller supplies the fields that require human/domain judgment
    (category, reproducer, expected/actual, etc.).  The builder takes
    structural fields (id, title, refs, promotion_reason) from *decision*.

    Raises
    ------
    ValueError
        If *decision* is not a PROMOTE verdict.
    """
    if decision.verdict is not PromotionVerdict.PROMOTE:
        raise ValueError(
            f"Cannot build issue from a {decision.verdict.value} decision."
        )

    return IssueCandidate(
        issue_id=f"IC-{seq:03d}",
        title=decision.symptom_summary,
        problem_statement=decision.reason,
        category=category,
        impact_layers=impact_layers,
        minimal_reproducer=minimal_reproducer,
        expected=expected,
        actual=actual,
        evidence_refs=decision.evidence_refs,
        evidence_excerpt=evidence_excerpt,
        environment=environment,
        promotion_reason=", ".join(decision.triggered_conditions),
        root_cause_hypothesis=root_cause_hypothesis,
        non_goals=non_goals,
    )


def assemble_feedback_packet(
    candidates: list[IssueCandidate],
    evidences: list[EvidenceRef],
    *,
    seq: int,
    date: str,
    judgment: str,
    next_step_implication: str,
    confidence: Confidence,
    non_goals: tuple[str, ...],
    supersedes: str | None = None,
) -> FeedbackPacket:
    """Assemble a :class:`FeedbackPacket` from issue candidates and evidences.

    Raises
    ------
    ValueError
        If *candidates* is empty.
    """
    if not candidates:
        raise ValueError("At least one IssueCandidate is required.")

    source_issues = tuple(c.issue_id for c in candidates)
    source_evidence = tuple(e.path for e in evidences)

    # Aggregate affected_docs and affected_layers from candidates
    docs_set: set[str] = set()
    layers_set: set[ImpactLayer] = set()
    for c in candidates:
        docs_set.add(c.environment)  # environment lists affected doc surfaces
        layers_set.update(c.impact_layers)

    return FeedbackPacket(
        packet_id=f"fp-{date}-{seq:03d}",
        source_issues=source_issues,
        source_evidence=source_evidence,
        judgment=judgment,
        next_step_implication=next_step_implication,
        affected_docs=tuple(sorted(docs_set)),
        affected_layers=tuple(sorted(layers_set, key=lambda x: x.value)),
        non_goals=non_goals,
        confidence=confidence,
        supersedes=supersedes,
    )
