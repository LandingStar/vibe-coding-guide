"""Coordination exchange artifact primitives.

These models are intentionally small and runtime-neutral. They define the
artifact-centered communication surface used by the orchestration layer; raw
runtime transcripts remain outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping

ExchangeArtifactKind = Literal[
    "message",
    "request",
    "query",
    "proposal",
    "blocker",
    "result",
    "review",
    "contract",
    "handoff",
    "retention",
    "cleanup",
]

ExchangeArtifactIntent = Literal[
    "ask",
    "inform",
    "propose",
    "require_review",
    "request_merge",
    "declare_blocked",
    "unblock",
    "supersede",
    "request_registration",
    "request_retention",
]

ExchangeArtifactLifecycleState = Literal[
    "draft",
    "proposed",
    "accepted",
    "rejected",
    "consumed",
    "superseded",
    "archived",
]

ExchangePayloadPartType = Literal[
    "text",
    "structured",
    "ref",
    "artifact_delta",
    "contract",
    "evidence",
    "relation",
    "storage_manifest",
    "log",
]

RelationKind = Literal[
    "depends_on",
    "waits_for",
    "blocks",
    "unblocks",
    "merges_into",
    "hands_off",
    "proposes_new_lane",
    "approves_new_lane",
    "supersedes",
    "consumes_contract",
    "produces_contract",
]

RelationStatus = Literal["proposed", "active", "resolved", "rejected", "superseded"]

ContractKind = Literal[
    "api",
    "data_schema",
    "event_protocol",
    "cli_surface",
    "test_interface",
    "coordination_protocol",
    "storage_policy",
]

ContractStatus = Literal["draft", "proposed", "accepted", "deprecated", "superseded"]

LogClockKind = Literal["wall", "logical", "runtime"]


@dataclass(frozen=True, slots=True)
class ExchangeReference:
    """Typed reference to an orchestration, runtime, or artifact object."""

    ref_kind: str
    ref_id: str
    version: str = ""
    path: str = ""
    label: str = ""


@dataclass(frozen=True, slots=True)
class ExchangeCausality:
    """Causality links for an exchange artifact."""

    replies_to: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    supersedes: tuple[str, ...] = ()
    caused_by: tuple[str, ...] = ()
    correlation_id: str = ""


@dataclass(frozen=True, slots=True)
class ExchangeScope:
    """Scope where an exchange artifact is valid and visible."""

    trajectory_id: str = ""
    lane_id: str = ""
    event_id: str = ""
    task_id: str = ""
    context_id: str = ""
    agent_id: str = ""
    runtime_session_id: str = ""


@dataclass(frozen=True, slots=True)
class VisibilityPolicy:
    """Minimal visibility policy for a coordination artifact."""

    audience: tuple[str, ...] = ()
    cross_lane: bool = False
    contains_sensitive_content: bool = False
    redaction_required: bool = False


@dataclass(frozen=True, slots=True)
class ExchangeContract:
    """Versioned coordination contract consumed by other agents or tasks."""

    contract_id: str
    contract_kind: ContractKind
    version: str
    title: str = ""
    producer: str = ""
    consumers: tuple[str, ...] = ()
    status: ContractStatus = "draft"
    schema_ref: ExchangeReference | None = None
    content: Mapping[str, object] = field(default_factory=dict)
    compatibility: str = ""
    supersedes: tuple[str, ...] = ()
    effective_from: str = ""


@dataclass(frozen=True, slots=True)
class ExchangeRelation:
    """Scheduler-readable relationship declaration."""

    relation_id: str
    relation_kind: RelationKind
    source: ExchangeReference
    target: ExchangeReference
    direction: str = "source_to_target"
    strength: str = ""
    status: RelationStatus = "active"
    reason: str = ""
    since: str = ""
    until: str = ""


@dataclass(frozen=True, slots=True)
class ExchangeLog:
    """Compact historical communication entry, not a raw transcript."""

    timestamp: str
    actor: str
    action: str
    channel: str = ""
    summary: str = ""
    related_artifact_ids: tuple[str, ...] = ()
    related_event_ids: tuple[str, ...] = ()
    related_run_ids: tuple[str, ...] = ()
    sequence: int | None = None
    clock: LogClockKind = "wall"


@dataclass(frozen=True, slots=True)
class ExchangePayloadPart:
    """One typed part of an exchange artifact payload."""

    part_type: ExchangePayloadPartType
    text: str = ""
    data: Mapping[str, object] = field(default_factory=dict)
    ref: ExchangeReference | None = None
    relation: ExchangeRelation | None = None
    contract: ExchangeContract | None = None
    log: ExchangeLog | None = None


@dataclass(frozen=True, slots=True)
class ExchangeArtifact:
    """Versioned artifact-centered coordination product."""

    artifact_id: str
    kind: ExchangeArtifactKind
    intent: ExchangeArtifactIntent
    producer: str
    audience: tuple[str, ...] = ()
    scope: ExchangeScope = field(default_factory=ExchangeScope)
    causality: ExchangeCausality = field(default_factory=ExchangeCausality)
    lifecycle_state: ExchangeArtifactLifecycleState = "draft"
    visibility_policy: VisibilityPolicy = field(default_factory=VisibilityPolicy)
    created_at: str = ""
    version: str = ""
    parts: tuple[ExchangePayloadPart, ...] = ()


SCHEDULER_RELEVANT_PARTS_BY_KIND: dict[ExchangeArtifactKind, tuple[ExchangePayloadPartType, ...]] = {
    "blocker": ("relation",),
    "contract": ("contract",),
    "result": ("artifact_delta",),
    "review": ("structured",),
    "handoff": ("relation",),
    "retention": ("storage_manifest",),
    "cleanup": ("storage_manifest", "log"),
}


def part_types(artifact: ExchangeArtifact) -> tuple[ExchangePayloadPartType, ...]:
    """Return stable payload part types for validation and tests."""

    return tuple(part.part_type for part in artifact.parts)


def validate_exchange_artifact(artifact: ExchangeArtifact) -> tuple[str, ...]:
    """Return validation errors for scheduler-facing exchange constraints.

    This is deliberately non-raising so callers can surface all contract
    problems to an agent or reviewer at once.
    """

    errors: list[str] = []
    seen_types = set(part_types(artifact))
    required = SCHEDULER_RELEVANT_PARTS_BY_KIND.get(artifact.kind, ())

    for required_type in required:
        if required_type not in seen_types:
            errors.append(
                f"exchange artifact {artifact.artifact_id!r} with kind "
                f"{artifact.kind!r} requires payload part {required_type!r}; "
                "scheduler-relevant state must not exist only in text"
            )

    for index, part in enumerate(artifact.parts):
        if part.part_type == "relation" and part.relation is None:
            errors.append(f"payload part {index} is 'relation' but relation payload is missing")
        if part.part_type == "contract" and part.contract is None:
            errors.append(f"payload part {index} is 'contract' but contract payload is missing")
        if part.part_type == "log" and part.log is None:
            errors.append(f"payload part {index} is 'log' but log payload is missing")
        if part.part_type == "log" and part.log is not None:
            if not part.log.timestamp:
                errors.append(f"payload part {index} is 'log' but log.timestamp is empty")
            if not part.log.actor:
                errors.append(f"payload part {index} is 'log' but log.actor is empty")
            if not part.log.action:
                errors.append(f"payload part {index} is 'log' but log.action is empty")
        if part.part_type == "ref" and part.ref is None:
            errors.append(f"payload part {index} is 'ref' but reference payload is missing")
        if part.part_type == "text" and not part.text:
            errors.append(f"payload part {index} is 'text' but text is empty")

    return tuple(errors)


def has_scheduler_readable_relation(artifact: ExchangeArtifact, relation_kind: RelationKind) -> bool:
    """Check whether an artifact declares a relation of the requested kind."""

    return any(
        part.part_type == "relation"
        and part.relation is not None
        and part.relation.relation_kind == relation_kind
        for part in artifact.parts
    )
