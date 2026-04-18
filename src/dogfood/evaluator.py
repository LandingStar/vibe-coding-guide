"""Promotion threshold evaluator.

Implements the T1-T4 trigger / S1-S3 suppress logic from:
- design_docs/dogfood-evidence-issue-feedback-boundary.md §Issue Promotion Threshold Contract
"""

from __future__ import annotations

from src.dogfood.models import (
    EvidenceRef,
    IssueCandidate,
    PromotionDecision,
    PromotionVerdict,
)


def evaluate_promotion(
    evidences: list[EvidenceRef],
    existing_issues: list[IssueCandidate],
    symptoms: list[dict],
) -> list[PromotionDecision]:
    """Evaluate each symptom against the promotion threshold.

    Parameters
    ----------
    evidences:
        All evidence refs available for this evaluation round.
    existing_issues:
        Previously promoted issue candidates (used for S2 check).
    symptoms:
        Each dict describes one symptom with keys:

        - ``symptom_id`` (str): unique id, e.g. ``"symptom-1"``
        - ``symptom_summary`` (str): one-sentence summary
        - ``evidence_refs`` (list[EvidenceRef]): supporting evidence
        - ``category`` (str | None): proposed category value
        - ``affects_next_gate`` (bool): True if it changes next gate boundary
        - ``requires_next_slice`` (bool): True if next slice needs to know
        - ``occurrence_count`` (int): how many independent evidences show this

    Returns
    -------
    list[PromotionDecision]
        One decision per symptom.
    """
    results: list[PromotionDecision] = []
    for s in symptoms:
        triggered = _check_triggers(s, evidences)
        suppressed = _check_suppressions(s, existing_issues)

        if suppressed:
            verdict = PromotionVerdict.SUPPRESS
            reason = f"Suppressed by {', '.join(suppressed)}."
        elif triggered:
            verdict = PromotionVerdict.PROMOTE
            reason = f"Triggered by {', '.join(triggered)}."
        else:
            verdict = PromotionVerdict.SUPPRESS
            reason = "No trigger condition met."

        results.append(
            PromotionDecision(
                symptom_id=s["symptom_id"],
                symptom_summary=s["symptom_summary"],
                verdict=verdict,
                triggered_conditions=tuple(triggered),
                suppressed_conditions=tuple(suppressed),
                reason=reason,
                evidence_refs=tuple(s.get("evidence_refs", [])),
            )
        )
    return results


def _check_triggers(symptom: dict, evidences: list[EvidenceRef]) -> list[str]:
    """Return list of triggered condition IDs (T1-T4)."""
    triggered: list[str] = []

    # T1 — Repetition: same symptom in ≥2 independent evidences
    if symptom.get("occurrence_count", 0) >= 2:
        triggered.append("T1")

    # T2 — Boundary impact: changes next gate/direction boundary
    if symptom.get("affects_next_gate", False):
        triggered.append("T2")

    # T3 — Classifiable: can be assigned to a known category
    if symptom.get("category") is not None:
        triggered.append("T3")

    # T4 — Next-slice dependency
    if symptom.get("requires_next_slice", False):
        triggered.append("T4")

    return triggered


def _check_suppressions(
    symptom: dict,
    existing_issues: list[IssueCandidate],
) -> list[str]:
    """Return list of suppression condition IDs (S1-S3)."""
    suppressed: list[str] = []

    # S1 — Single transient noise: only 1 occurrence, no stable attribution
    if symptom.get("occurrence_count", 0) < 2 and not symptom.get("affects_next_gate", False):
        suppressed.append("S1")

    # S2 — Already covered by existing issue
    sym_summary_lower = symptom.get("symptom_summary", "").lower()
    for issue in existing_issues:
        if sym_summary_lower and sym_summary_lower in issue.problem_statement.lower():
            suppressed.append("S2")
            break

    # S3 — No referable evidence
    if not symptom.get("evidence_refs"):
        suppressed.append("S3")

    return suppressed
