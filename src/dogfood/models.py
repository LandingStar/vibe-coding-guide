"""Data structures for the dogfood promotion + feedback packet pipeline.

All structures map 1:1 to the contracts defined in:
- design_docs/dogfood-evidence-issue-feedback-boundary.md
- design_docs/dogfood-promotion-packet-interface-draft.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PromotionVerdict(Enum):
    PROMOTE = "promote"
    SUPPRESS = "suppress"


class IssueCategory(Enum):
    TRANSPORT_CREDENTIAL_ENDPOINT = "transport/credential/endpoint"
    CONTRACT_DRIFT = "contract drift/schema drift"
    OUTPUT_GUARD_REJECTION = "output guard rejection"
    WRITEBACK_BOUNDARY = "writeback boundary"
    WORDING_ADOPTION_BOUNDARY = "wording/adoption boundary"
    WORKFLOW_STATE_SYNC_GAP = "workflow/state-sync gap"


class ImpactLayer(Enum):
    RUNTIME = "runtime"
    CONTRACT = "contract"
    WORKFLOW = "workflow"
    STATE_SYNC = "state-sync"
    WORDING = "wording"


class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConsumerName(Enum):
    DIRECTION_CANDIDATES = "direction-candidates"
    CHECKLIST = "checklist"
    PHASE_MAP = "phase-map"
    CHECKPOINT = "checkpoint"
    HANDOFF = "handoff"
    PLANNING_GATE = "planning-gate"


# ---------------------------------------------------------------------------
# Evidence reference
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceRef:
    """Lightweight pointer to an evidence section — never copies full text."""

    path: str
    section: str | None = None
    summary: str = ""


# ---------------------------------------------------------------------------
# Promotion decision
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PromotionDecision:
    """Output of the promotion threshold evaluator for a single symptom."""

    symptom_id: str
    symptom_summary: str
    verdict: PromotionVerdict
    triggered_conditions: tuple[str, ...] = ()
    suppressed_conditions: tuple[str, ...] = ()
    reason: str = ""
    evidence_refs: tuple[EvidenceRef, ...] = ()


# ---------------------------------------------------------------------------
# Root-cause hypothesis (optional part of IssueCandidate)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RootCauseHypothesis:
    description: str
    basis: str
    confidence: Confidence


# ---------------------------------------------------------------------------
# Issue candidate
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IssueCandidate:
    """12-field issue candidate as specified by the contract."""

    issue_id: str
    title: str
    problem_statement: str
    category: IssueCategory
    impact_layers: tuple[ImpactLayer, ...]
    minimal_reproducer: str
    expected: str
    actual: str
    evidence_refs: tuple[EvidenceRef, ...]
    evidence_excerpt: str
    environment: str
    promotion_reason: str
    root_cause_hypothesis: RootCauseHypothesis | None = None
    non_goals: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Feedback packet
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeedbackPacket:
    """9 required + 3 optional fields as specified by the contract."""

    # Required
    packet_id: str
    source_issues: tuple[str, ...]
    source_evidence: tuple[str, ...]
    judgment: str
    next_step_implication: str
    affected_docs: tuple[str, ...]
    affected_layers: tuple[ImpactLayer, ...]
    non_goals: tuple[str, ...]
    confidence: Confidence

    # Optional
    supersedes: str | None = None
    blocking_issues: tuple[str, ...] | None = None
    raw_data_pointers: tuple[str, ...] | None = None


# ---------------------------------------------------------------------------
# Consumer payload
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConsumerPayload:
    """Per-consumer view of a FeedbackPacket, trimmed by the boundary matrix."""

    consumer: ConsumerName
    fields: dict[str, object] = field(default_factory=dict)
