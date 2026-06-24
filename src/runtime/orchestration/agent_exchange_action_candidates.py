"""Read-only action candidates over ExchangeArtifact communication products."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .exchange import ExchangeArtifact, ExchangePayloadPart, ExchangeReference
from .exchange_store import (
    ArtifactVersionRecord,
    ExchangeArtifactAdmissionCandidate,
    JsonArtifactVersionStore,
    detect_exchange_artifact_admission_candidates,
    inspect_exchange_artifact_store,
)

AgentExchangeActionCandidateType = Literal[
    "scheduler_submission_candidate",
    "review_candidate",
    "handoff_candidate",
    "blocker_candidate",
    "merge_candidate",
]

AgentExchangeActionCandidateConfidence = Literal["high", "medium", "low"]

ACTIVE_LIFECYCLE_STATES = {"draft", "proposed", "accepted"}


@dataclass(frozen=True, slots=True)
class AgentExchangeActionCandidate:
    """Compact read-only action candidate derived from one exact artifact version."""

    candidate_id: str
    candidate_type: AgentExchangeActionCandidateType
    artifact_id: str
    version: str
    confidence: AgentExchangeActionCandidateConfidence
    lifecycle_state: str
    kind: str
    intent: str
    producer: str
    audience: tuple[str, ...] = ()
    scope: Mapping[str, object] = field(default_factory=dict)
    reasons: tuple[str, ...] = ()
    relation_clues: tuple[Mapping[str, object], ...] = ()
    ref_clues: tuple[Mapping[str, object], ...] = ()
    contract_clues: tuple[Mapping[str, object], ...] = ()
    admission_clues: tuple[Mapping[str, object], ...] = ()
    suggested_next_surface: str = ""
    contains_sensitive_content: bool = False
    redaction_required: bool = False

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible action-candidate payload."""

        return {
            "candidate_id": self.candidate_id,
            "candidate_type": self.candidate_type,
            "artifact_id": self.artifact_id,
            "version": self.version,
            "source": _artifact_version_token(self.artifact_id, self.version),
            "confidence": self.confidence,
            "lifecycle_state": self.lifecycle_state,
            "kind": self.kind,
            "intent": self.intent,
            "producer": self.producer,
            "audience": list(self.audience),
            "scope": dict(self.scope),
            "reasons": list(self.reasons),
            "relation_clues": [dict(item) for item in self.relation_clues],
            "ref_clues": [dict(item) for item in self.ref_clues],
            "contract_clues": [dict(item) for item in self.contract_clues],
            "admission_clues": [dict(item) for item in self.admission_clues],
            "suggested_next_surface": self.suggested_next_surface,
            "contains_sensitive_content": self.contains_sensitive_content,
            "redaction_required": self.redaction_required,
        }


@dataclass(frozen=True, slots=True)
class AgentExchangeActionCandidateSummary:
    """Read-only action-candidate summary over ExchangeArtifact records."""

    store_path: Path | None = None
    exists: bool = True
    agent_id_filter: str = ""
    candidate_type_filter: str = ""
    artifact_count: int = 0
    version_count: int = 0
    candidates: tuple[AgentExchangeActionCandidate, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    @property
    def candidate_type_counts(self) -> Mapping[str, int]:
        return dict(sorted(Counter(candidate.candidate_type for candidate in self.candidates).items()))

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible action-candidate summary."""

        return {
            "store_path": "" if self.store_path is None else str(self.store_path),
            "exists": self.exists,
            "agent_id_filter": self.agent_id_filter,
            "candidate_type_filter": self.candidate_type_filter,
            "artifact_count": self.artifact_count,
            "version_count": self.version_count,
            "candidate_count": self.candidate_count,
            "candidate_type_counts": dict(self.candidate_type_counts),
            "candidates": [candidate.to_json_dict() for candidate in self.candidates],
            "errors": list(self.errors),
            "authority_split": {
                "exchange_store_authority": "JsonArtifactVersionStore",
                "read_model_only": True,
                "scheduler_mutated": False,
                "exchange_store_mutated": False,
                "admission_ledger_mutated": False,
                "review_state_mutated": False,
                "handoff_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }


def build_agent_exchange_action_candidates(
    records: Iterable[ArtifactVersionRecord],
    *,
    agent_id: str = "",
    candidate_type: str = "",
    include_archived: bool = False,
    admission_candidates_by_key: Mapping[
        tuple[str, str],
        tuple[ExchangeArtifactAdmissionCandidate, ...],
    ] | None = None,
) -> AgentExchangeActionCandidateSummary:
    """Build a non-mutating action-candidate summary over loaded records."""

    selected: list[ArtifactVersionRecord] = []
    candidates: list[AgentExchangeActionCandidate] = []
    admission_candidates_by_key = admission_candidates_by_key or {}

    for record in records:
        artifact = record.artifact
        if artifact.lifecycle_state == "archived" and not include_archived:
            continue
        if agent_id and not _artifact_mentions_agent(artifact, agent_id):
            continue
        selected.append(record)

        admission_candidates = tuple(
            admission_candidates_by_key.get((record.artifact_id, record.version), ())
        ) or detect_exchange_artifact_admission_candidates(artifact)
        artifact_candidates = _artifact_action_candidates(record, admission_candidates)
        for candidate in artifact_candidates:
            if candidate_type and candidate.candidate_type != candidate_type:
                continue
            candidates.append(candidate)

    return AgentExchangeActionCandidateSummary(
        agent_id_filter=agent_id,
        candidate_type_filter=candidate_type,
        artifact_count=len({record.artifact_id for record in selected}),
        version_count=len(selected),
        candidates=tuple(candidates),
    )


def inspect_agent_exchange_action_candidates(
    path: str | Path,
    *,
    agent_id: str = "",
    candidate_type: str = "",
    include_archived: bool = False,
    admission_ledger_path: str | Path | None = None,
) -> AgentExchangeActionCandidateSummary:
    """Read a JSON artifact store into a non-mutating action-candidate summary."""

    store_path = Path(path)
    if not store_path.exists():
        return AgentExchangeActionCandidateSummary(
            store_path=store_path,
            exists=False,
            agent_id_filter=agent_id,
            candidate_type_filter=candidate_type,
        )

    try:
        records = JsonArtifactVersionStore(store_path).list_records()
        inspection = inspect_exchange_artifact_store(
            store_path,
            admission_ledger_path=admission_ledger_path,
        )
    except Exception as exc:
        return AgentExchangeActionCandidateSummary(
            store_path=store_path,
            exists=True,
            agent_id_filter=agent_id,
            candidate_type_filter=candidate_type,
            errors=(str(exc),),
        )

    admission_candidates_by_key = {
        (summary.artifact_id, summary.version): tuple(summary.admission_candidates)
        for summary in inspection.summaries
    }
    summary = build_agent_exchange_action_candidates(
        records,
        agent_id=agent_id,
        candidate_type=candidate_type,
        include_archived=include_archived,
        admission_candidates_by_key=admission_candidates_by_key,
    )
    return AgentExchangeActionCandidateSummary(
        store_path=store_path,
        exists=True,
        agent_id_filter=summary.agent_id_filter,
        candidate_type_filter=summary.candidate_type_filter,
        artifact_count=summary.artifact_count,
        version_count=summary.version_count,
        candidates=summary.candidates,
        errors=(*inspection.errors, *summary.errors),
    )


def _artifact_action_candidates(
    record: ArtifactVersionRecord,
    admission_candidates: tuple[ExchangeArtifactAdmissionCandidate, ...],
) -> tuple[AgentExchangeActionCandidate, ...]:
    artifact = record.artifact
    candidates: list[AgentExchangeActionCandidate] = []

    for index, admission_candidate in enumerate(admission_candidates):
        confidence: AgentExchangeActionCandidateConfidence = (
            "high" if admission_candidate.valid and _active_lifecycle(artifact) else "medium"
        )
        reasons = [
            f"admission_candidate:{admission_candidate.product_type}",
            "valid" if admission_candidate.valid else f"invalid:{admission_candidate.error}",
            f"lifecycle:{artifact.lifecycle_state}",
        ]
        candidates.append(
            _candidate(
                record,
                candidate_type="scheduler_submission_candidate",
                suffix=f"scheduler:{index}",
                confidence=confidence,
                reasons=tuple(reasons),
                admission_clues=(admission_candidate.to_json_dict(),),
                suggested_next_surface=(
                    "admitExchangeArtifact"
                    if admission_candidate.valid
                    else "fix-source-exchange-artifact"
                ),
            )
        )

    review_reasons = _review_reasons(artifact)
    if review_reasons:
        candidates.append(
            _candidate(
                record,
                candidate_type="review_candidate",
                suffix="review",
                confidence="high" if _active_lifecycle(artifact) else "medium",
                reasons=review_reasons,
                suggested_next_surface="reviewIntake",
            )
        )

    handoff_reasons = _handoff_reasons(artifact)
    if handoff_reasons:
        candidates.append(
            _candidate(
                record,
                candidate_type="handoff_candidate",
                suffix="handoff",
                confidence="high" if _active_lifecycle(artifact) else "medium",
                reasons=handoff_reasons,
                suggested_next_surface="handoffIntake",
            )
        )

    blocker_reasons = _blocker_reasons(artifact)
    if blocker_reasons:
        candidates.append(
            _candidate(
                record,
                candidate_type="blocker_candidate",
                suffix="blocker",
                confidence="high" if _active_lifecycle(artifact) else "medium",
                reasons=blocker_reasons,
                suggested_next_surface="blockerState",
            )
        )

    merge_reasons = _merge_reasons(artifact)
    if merge_reasons:
        candidates.append(
            _candidate(
                record,
                candidate_type="merge_candidate",
                suffix="merge",
                confidence="high" if _active_lifecycle(artifact) else "medium",
                reasons=merge_reasons,
                suggested_next_surface=(
                    "workerPatchReview" if _is_worker_patch_review_artifact(artifact) else "mergeIntake"
                ),
            )
        )

    return tuple(candidates)


def _candidate(
    record: ArtifactVersionRecord,
    *,
    candidate_type: AgentExchangeActionCandidateType,
    suffix: str,
    confidence: AgentExchangeActionCandidateConfidence,
    reasons: tuple[str, ...],
    admission_clues: tuple[Mapping[str, object], ...] = (),
    suggested_next_surface: str,
) -> AgentExchangeActionCandidate:
    artifact = record.artifact
    redacted = (
        artifact.visibility_policy.contains_sensitive_content
        or artifact.visibility_policy.redaction_required
    )
    return AgentExchangeActionCandidate(
        candidate_id=f"{record.artifact_id}@{record.version}:{suffix}",
        candidate_type=candidate_type,
        artifact_id=record.artifact_id,
        version=record.version,
        confidence=confidence,
        lifecycle_state=artifact.lifecycle_state,
        kind=artifact.kind,
        intent=artifact.intent,
        producer=artifact.producer,
        audience=artifact.audience,
        scope=_scope_to_json(artifact),
        reasons=reasons,
        relation_clues=_relation_clues(artifact),
        ref_clues=_ref_clues(artifact),
        contract_clues=_contract_clues(artifact),
        admission_clues=admission_clues,
        suggested_next_surface=suggested_next_surface,
        contains_sensitive_content=artifact.visibility_policy.contains_sensitive_content,
        redaction_required=redacted,
    )


def _review_reasons(artifact: ExchangeArtifact) -> tuple[str, ...]:
    reasons: list[str] = []
    if artifact.kind == "review":
        reasons.append("kind:review")
    if artifact.intent == "require_review":
        reasons.append("intent:require_review")
    for relation_kind in _relation_kinds(artifact):
        if relation_kind in {"approves_new_lane", "consumes_contract"}:
            reasons.append(f"relation:{relation_kind}")
    return tuple(reasons)


def _handoff_reasons(artifact: ExchangeArtifact) -> tuple[str, ...]:
    reasons: list[str] = []
    if artifact.kind == "handoff":
        reasons.append("kind:handoff")
    for relation_kind in _relation_kinds(artifact):
        if relation_kind == "hands_off":
            reasons.append("relation:hands_off")
    return tuple(reasons)


def _blocker_reasons(artifact: ExchangeArtifact) -> tuple[str, ...]:
    reasons: list[str] = []
    if artifact.kind == "blocker":
        reasons.append("kind:blocker")
    if artifact.intent == "declare_blocked":
        reasons.append("intent:declare_blocked")
    for relation_kind in _relation_kinds(artifact):
        if relation_kind in {"blocks", "waits_for"}:
            reasons.append(f"relation:{relation_kind}")
    return tuple(reasons)


def _merge_reasons(artifact: ExchangeArtifact) -> tuple[str, ...]:
    reasons: list[str] = []
    if artifact.intent == "request_merge":
        reasons.append("intent:request_merge")
    for relation_kind in _relation_kinds(artifact):
        if relation_kind == "merges_into":
            reasons.append("relation:merges_into")
    return tuple(reasons)


def _is_worker_patch_review_artifact(artifact: ExchangeArtifact) -> bool:
    return any(
        part.part_type == "structured"
        and part.data.get("product_type") == "worker_patch_review_proposal"
        for part in artifact.parts
    )


def _relation_kinds(artifact: ExchangeArtifact) -> tuple[str, ...]:
    return tuple(
        part.relation.relation_kind
        for part in artifact.parts
        if part.relation is not None
    )


def _relation_clues(artifact: ExchangeArtifact) -> tuple[Mapping[str, object], ...]:
    clues: list[Mapping[str, object]] = []
    for part in artifact.parts:
        if part.relation is None:
            continue
        relation = part.relation
        clues.append(
            {
                "relation_id": relation.relation_id,
                "relation_kind": relation.relation_kind,
                "status": relation.status,
                "source": _reference_clue(relation.source),
                "target": _reference_clue(relation.target),
                "direction": relation.direction,
                "strength": relation.strength,
            }
        )
    return tuple(clues)


def _ref_clues(artifact: ExchangeArtifact) -> tuple[Mapping[str, object], ...]:
    return tuple(
        _reference_clue(part.ref)
        for part in artifact.parts
        if part.ref is not None
    )


def _contract_clues(artifact: ExchangeArtifact) -> tuple[Mapping[str, object], ...]:
    clues: list[Mapping[str, object]] = []
    for part in artifact.parts:
        if part.contract is None:
            continue
        contract = part.contract
        clues.append(
            {
                "contract_id": contract.contract_id,
                "contract_kind": contract.contract_kind,
                "version": contract.version,
                "title": contract.title,
                "producer": contract.producer,
                "consumers": list(contract.consumers),
                "status": contract.status,
            }
        )
    return tuple(clues)


def _artifact_mentions_agent(artifact: ExchangeArtifact, agent_id: str) -> bool:
    if artifact.producer == agent_id:
        return True
    if agent_id in artifact.audience or agent_id in artifact.visibility_policy.audience:
        return True
    if artifact.scope.agent_id == agent_id:
        return True
    for part in artifact.parts:
        if part.ref is not None and _reference_mentions_agent(part.ref, agent_id):
            return True
        if part.relation is not None and (
            _reference_mentions_agent(part.relation.source, agent_id)
            or _reference_mentions_agent(part.relation.target, agent_id)
        ):
            return True
        if part.contract is not None and (
            part.contract.producer == agent_id
            or agent_id in part.contract.consumers
            or (
                part.contract.schema_ref is not None
                and _reference_mentions_agent(part.contract.schema_ref, agent_id)
            )
        ):
            return True
        if part.log is not None and part.log.actor == agent_id:
            return True
    return False


def _reference_mentions_agent(reference: ExchangeReference, agent_id: str) -> bool:
    return (
        reference.ref_id == agent_id
        or (reference.ref_kind == "agent" and reference.ref_id == agent_id)
        or reference.label == agent_id
    )


def _reference_clue(reference: ExchangeReference) -> dict[str, str]:
    return {
        "ref_kind": reference.ref_kind,
        "ref_id": reference.ref_id,
        "version": reference.version,
        "path": reference.path,
        "label": reference.label,
    }


def _scope_to_json(artifact: ExchangeArtifact) -> dict[str, object]:
    scope = artifact.scope
    return {
        "trajectory_id": scope.trajectory_id,
        "lane_id": scope.lane_id,
        "event_id": scope.event_id,
        "task_id": scope.task_id,
        "context_id": scope.context_id,
        "agent_id": scope.agent_id,
        "runtime_session_id": scope.runtime_session_id,
    }


def _active_lifecycle(artifact: ExchangeArtifact) -> bool:
    return artifact.lifecycle_state in ACTIVE_LIFECYCLE_STATES


def _artifact_version_token(artifact_id: str, version: str) -> str:
    return f"{artifact_id}@{version}"
