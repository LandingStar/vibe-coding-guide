"""Disposition artifacts for ExchangeArtifact action candidates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Mapping

from .agent_exchange_action_candidates import (
    AgentExchangeActionCandidate,
    inspect_agent_exchange_action_candidates,
)
from .exchange import (
    ExchangeArtifact,
    ExchangeCausality,
    ExchangeLog,
    ExchangePayloadPart,
    ExchangeReference,
    ExchangeScope,
)
from .exchange_store import JsonArtifactVersionStore

ACTION_CANDIDATE_DISPOSITION_PRODUCT_TYPE = "agent_exchange_action_candidate_disposition"
AgentExchangeActionCandidateDisposition = Literal["accept", "reject", "defer", "supersede"]


@dataclass(frozen=True, slots=True)
class AgentExchangeActionCandidateDispositionResult:
    """Result of writing one action-candidate disposition artifact."""

    store_path: Path
    source_artifact_id: str
    source_version: str
    candidate_id: str
    candidate_type: str
    disposition_artifact_id: str
    disposition_version: str
    disposition: str
    actor: str
    reason: str = ""
    target_surface: str = ""
    replacement_artifact_id: str = ""
    replacement_version: str = ""

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible disposition result."""

        return {
            "ok": True,
            "store_path": str(self.store_path),
            "source_artifact_id": self.source_artifact_id,
            "source_version": self.source_version,
            "source": f"{self.source_artifact_id}@{self.source_version}",
            "candidate_id": self.candidate_id,
            "candidate_type": self.candidate_type,
            "disposition_artifact_id": self.disposition_artifact_id,
            "disposition_version": self.disposition_version,
            "disposition": self.disposition,
            "actor": self.actor,
            "reason": self.reason,
            "target_surface": self.target_surface,
            "replacement_artifact_id": self.replacement_artifact_id,
            "replacement_version": self.replacement_version,
            "authority_split": {
                "exchange_store_authority": "JsonArtifactVersionStore",
                "coordination_product_only": True,
                "scheduler_mutated": False,
                "source_exchange_artifact_mutated": False,
                "admission_ledger_mutated": False,
                "review_state_mutated": False,
                "handoff_mutated": False,
                "merge_gate_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }


def decide_agent_exchange_action_candidate(
    *,
    store_path: str | Path,
    candidate_id: str,
    disposition_artifact_id: str,
    actor: str,
    disposition: AgentExchangeActionCandidateDisposition,
    disposition_version: str = "v1",
    reason: str = "",
    target_surface: str = "",
    replacement_artifact_id: str = "",
    replacement_version: str = "",
    timestamp: str = "",
    replace_existing: bool = False,
) -> AgentExchangeActionCandidateDispositionResult:
    """Write one disposition ExchangeArtifact for an existing action candidate."""

    if not candidate_id:
        raise ValueError("action candidate disposition requires a non-empty candidate_id")
    if not disposition_artifact_id:
        raise ValueError("action candidate disposition requires a non-empty disposition_artifact_id")
    if not actor:
        raise ValueError("action candidate disposition requires a non-empty actor")
    if disposition not in {"accept", "reject", "defer", "supersede"}:
        raise ValueError(
            "action candidate disposition must be one of: accept, reject, defer, supersede"
        )
    if disposition == "accept" and not target_surface:
        raise ValueError("accepted action candidate disposition requires target_surface")
    if disposition == "supersede" and not replacement_artifact_id:
        raise ValueError("superseded action candidate disposition requires replacement_artifact_id")

    path = Path(store_path)
    candidate = _find_candidate(path, candidate_id)
    event_timestamp = timestamp or datetime.now(UTC).isoformat()
    artifact = _build_disposition_artifact(
        candidate,
        disposition_artifact_id=disposition_artifact_id,
        disposition_version=disposition_version,
        actor=actor,
        disposition=disposition,
        reason=reason,
        target_surface=target_surface,
        replacement_artifact_id=replacement_artifact_id,
        replacement_version=replacement_version,
        timestamp=event_timestamp,
    )
    JsonArtifactVersionStore(path).put(artifact, replace_existing=replace_existing)
    return AgentExchangeActionCandidateDispositionResult(
        store_path=path,
        source_artifact_id=candidate.artifact_id,
        source_version=candidate.version,
        candidate_id=candidate.candidate_id,
        candidate_type=candidate.candidate_type,
        disposition_artifact_id=disposition_artifact_id,
        disposition_version=disposition_version,
        disposition=disposition,
        actor=actor,
        reason=reason,
        target_surface=target_surface,
        replacement_artifact_id=replacement_artifact_id,
        replacement_version=replacement_version,
    )


def _find_candidate(
    store_path: Path,
    candidate_id: str,
) -> AgentExchangeActionCandidate:
    summary = inspect_agent_exchange_action_candidates(store_path, include_archived=True)
    if summary.errors:
        raise ValueError("; ".join(summary.errors))
    for candidate in summary.candidates:
        if candidate.candidate_id == candidate_id:
            return candidate
    raise ValueError(f"action candidate not found in {store_path}: {candidate_id!r}")


def _build_disposition_artifact(
    candidate: AgentExchangeActionCandidate,
    *,
    disposition_artifact_id: str,
    disposition_version: str,
    actor: str,
    disposition: str,
    reason: str,
    target_surface: str,
    replacement_artifact_id: str,
    replacement_version: str,
    timestamp: str,
) -> ExchangeArtifact:
    payload: dict[str, object] = {
        "product_type": ACTION_CANDIDATE_DISPOSITION_PRODUCT_TYPE,
        "candidate_id": candidate.candidate_id,
        "candidate_type": candidate.candidate_type,
        "source_artifact_id": candidate.artifact_id,
        "source_version": candidate.version,
        "source": f"{candidate.artifact_id}@{candidate.version}",
        "disposition": disposition,
        "actor": actor,
        "reason": reason,
        "target_surface": target_surface,
        "replacement_artifact_id": replacement_artifact_id,
        "replacement_version": replacement_version,
    }
    return ExchangeArtifact(
        artifact_id=disposition_artifact_id,
        version=disposition_version,
        kind="proposal",
        intent="inform",
        producer=actor,
        audience=_disposition_audience(candidate),
        scope=ExchangeScope(
            trajectory_id=str(candidate.scope.get("trajectory_id", "")),
            lane_id=str(candidate.scope.get("lane_id", "")),
            event_id=str(candidate.scope.get("event_id", "")),
            task_id=str(candidate.scope.get("task_id", "")),
            context_id=str(candidate.scope.get("context_id", "")),
            agent_id=actor,
            runtime_session_id=str(candidate.scope.get("runtime_session_id", "")),
        ),
        causality=ExchangeCausality(
            caused_by=(f"{candidate.artifact_id}@{candidate.version}",),
            correlation_id=candidate.candidate_id,
        ),
        lifecycle_state="accepted" if disposition == "accept" else "proposed",
        created_at=timestamp,
        parts=(
            ExchangePayloadPart(part_type="structured", data=payload),
            ExchangePayloadPart(
                part_type="ref",
                ref=ExchangeReference(
                    ref_kind="exchange_artifact",
                    ref_id=candidate.artifact_id,
                    version=candidate.version,
                    label="source_action_candidate_artifact",
                ),
            ),
            ExchangePayloadPart(
                part_type="log",
                log=ExchangeLog(
                    timestamp=timestamp,
                    actor=actor,
                    action="action_candidate_disposition",
                    channel="agent-exchange-action-candidate",
                    summary=f"{disposition} {candidate.candidate_id}",
                    related_artifact_ids=(candidate.artifact_id, disposition_artifact_id),
                ),
            ),
        ),
    )


def _disposition_audience(candidate: AgentExchangeActionCandidate) -> tuple[str, ...]:
    values = [candidate.producer, *candidate.audience]
    return tuple(dict.fromkeys(value for value in values if value))
