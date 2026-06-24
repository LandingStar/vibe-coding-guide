"""Agent-facing read models over ExchangeArtifact coordination products.

This module deliberately builds a mailbox view without mutating the exchange
store. The store remains the exact-version artifact authority; this read model
only answers how those artifacts route to one agent.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .exchange import ExchangeArtifact, ExchangePayloadPart, ExchangeReference
from .exchange_store import ArtifactVersionRecord, JsonArtifactVersionStore

MailboxBucket = Literal["inbox", "outbox", "related"]


ACTIONABLE_KINDS = {"query", "request", "proposal", "blocker", "review", "contract", "handoff", "retention"}
ACTIONABLE_INTENTS = {
    "ask",
    "propose",
    "require_review",
    "request_merge",
    "declare_blocked",
    "unblock",
    "request_registration",
    "request_retention",
}
ACTIONABLE_LIFECYCLE_STATES = {"draft", "proposed", "accepted"}
PREVIEW_TEXT_LIMIT = 240


@dataclass(frozen=True, slots=True)
class AgentMailboxItem:
    """Compact routing summary for one exact exchange artifact version."""

    artifact_id: str
    version: str
    bucket: MailboxBucket
    kind: str
    intent: str
    lifecycle_state: str
    producer: str
    audience: tuple[str, ...] = ()
    visibility_audience: tuple[str, ...] = ()
    part_types: tuple[str, ...] = ()
    routing_reasons: tuple[str, ...] = ()
    actionable: bool = False
    actionable_reasons: tuple[str, ...] = ()
    contains_sensitive_content: bool = False
    redaction_required: bool = False
    scope: Mapping[str, object] = field(default_factory=dict)
    preview: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-compatible mailbox item."""

        return {
            "artifact_id": self.artifact_id,
            "version": self.version,
            "bucket": self.bucket,
            "kind": self.kind,
            "intent": self.intent,
            "lifecycle_state": self.lifecycle_state,
            "producer": self.producer,
            "audience": list(self.audience),
            "visibility_audience": list(self.visibility_audience),
            "part_types": list(self.part_types),
            "routing_reasons": list(self.routing_reasons),
            "actionable": self.actionable,
            "actionable_reasons": list(self.actionable_reasons),
            "contains_sensitive_content": self.contains_sensitive_content,
            "redaction_required": self.redaction_required,
            "scope": dict(self.scope),
            "preview": dict(self.preview),
        }


@dataclass(frozen=True, slots=True)
class AgentMailbox:
    """Per-agent read model over ExchangeArtifact records."""

    agent_id: str
    store_path: Path | None = None
    exists: bool = True
    inbox: tuple[AgentMailboxItem, ...] = ()
    outbox: tuple[AgentMailboxItem, ...] = ()
    related: tuple[AgentMailboxItem, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def inbox_count(self) -> int:
        return len(self.inbox)

    @property
    def outbox_count(self) -> int:
        return len(self.outbox)

    @property
    def related_count(self) -> int:
        return len(self.related)

    @property
    def actionable_count(self) -> int:
        return sum(1 for item in self.inbox if item.actionable)

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible mailbox payload."""

        return {
            "agent_id": self.agent_id,
            "store_path": "" if self.store_path is None else str(self.store_path),
            "exists": self.exists,
            "inbox_count": self.inbox_count,
            "outbox_count": self.outbox_count,
            "related_count": self.related_count,
            "actionable_count": self.actionable_count,
            "inbox": [item.to_json_dict() for item in self.inbox],
            "outbox": [item.to_json_dict() for item in self.outbox],
            "related": [item.to_json_dict() for item in self.related],
            "errors": list(self.errors),
            "authority_split": {
                "exchange_store_authority": "JsonArtifactVersionStore",
                "read_model_only": True,
                "scheduler_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


def build_agent_exchange_mailbox(
    records: Iterable[ArtifactVersionRecord],
    *,
    agent_id: str,
    include_archived: bool = False,
) -> AgentMailbox:
    """Build a mailbox over already-loaded exchange artifact records."""

    if not agent_id:
        raise ValueError("agent mailbox requires a non-empty agent_id")

    inbox: list[AgentMailboxItem] = []
    outbox: list[AgentMailboxItem] = []
    related: list[AgentMailboxItem] = []

    for record in records:
        artifact = record.artifact
        if artifact.lifecycle_state == "archived" and not include_archived:
            continue

        route = _route_artifact(artifact, agent_id)
        if route.bucket is None:
            continue

        item = _mailbox_item(record, route, agent_id)
        if route.bucket == "inbox":
            inbox.append(item)
        elif route.bucket == "outbox":
            outbox.append(item)
        else:
            related.append(item)

    return AgentMailbox(
        agent_id=agent_id,
        inbox=tuple(inbox),
        outbox=tuple(outbox),
        related=tuple(related),
    )


def inspect_agent_exchange_mailbox(
    path: str | Path,
    *,
    agent_id: str,
    include_archived: bool = False,
) -> AgentMailbox:
    """Read a JSON artifact store into a non-mutating per-agent mailbox."""

    if not agent_id:
        raise ValueError("agent mailbox inspection requires a non-empty agent_id")

    store_path = Path(path)
    if not store_path.exists():
        return AgentMailbox(agent_id=agent_id, store_path=store_path, exists=False)

    try:
        records = JsonArtifactVersionStore(store_path).list_records()
    except Exception as exc:
        return AgentMailbox(
            agent_id=agent_id,
            store_path=store_path,
            exists=True,
            errors=(str(exc),),
        )

    mailbox = build_agent_exchange_mailbox(
        records,
        agent_id=agent_id,
        include_archived=include_archived,
    )
    return AgentMailbox(
        agent_id=mailbox.agent_id,
        store_path=store_path,
        exists=True,
        inbox=mailbox.inbox,
        outbox=mailbox.outbox,
        related=mailbox.related,
        errors=mailbox.errors,
    )


@dataclass(frozen=True, slots=True)
class _RouteDecision:
    bucket: MailboxBucket | None
    reasons: tuple[str, ...]


def _route_artifact(artifact: ExchangeArtifact, agent_id: str) -> _RouteDecision:
    reasons: list[str] = []
    if artifact.producer == agent_id:
        reasons.append("producer")
        return _RouteDecision("outbox", tuple(reasons))

    if agent_id in artifact.audience:
        reasons.append("audience")
    if agent_id in artifact.visibility_policy.audience:
        reasons.append("visibility_policy.audience")
    if artifact.scope.agent_id == agent_id:
        reasons.append("scope.agent_id")

    if reasons:
        return _RouteDecision("inbox", tuple(reasons))

    related_reasons = _related_reasons(artifact, agent_id)
    if related_reasons:
        return _RouteDecision("related", related_reasons)

    return _RouteDecision(None, ())


def _related_reasons(artifact: ExchangeArtifact, agent_id: str) -> tuple[str, ...]:
    reasons: list[str] = []
    for index, part in enumerate(artifact.parts):
        prefix = f"parts[{index}]"
        if _part_mentions_agent(part, agent_id):
            reasons.append(prefix)
    return tuple(reasons)


def _part_mentions_agent(part: ExchangePayloadPart, agent_id: str) -> bool:
    if part.ref is not None and _reference_mentions_agent(part.ref, agent_id):
        return True
    if part.relation is not None:
        return (
            _reference_mentions_agent(part.relation.source, agent_id)
            or _reference_mentions_agent(part.relation.target, agent_id)
        )
    if part.contract is not None:
        return (
            part.contract.producer == agent_id
            or agent_id in part.contract.consumers
            or (
                part.contract.schema_ref is not None
                and _reference_mentions_agent(part.contract.schema_ref, agent_id)
            )
        )
    if part.log is not None:
        return part.log.actor == agent_id or agent_id in part.log.related_artifact_ids
    return _data_mentions_agent(part.data, agent_id)


def _reference_mentions_agent(reference: ExchangeReference, agent_id: str) -> bool:
    return (
        reference.ref_id == agent_id
        or (reference.ref_kind == "agent" and reference.ref_id == agent_id)
        or reference.label == agent_id
    )


def _data_mentions_agent(value: object, agent_id: str) -> bool:
    if value == agent_id:
        return True
    if isinstance(value, Mapping):
        return any(_data_mentions_agent(item, agent_id) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_data_mentions_agent(item, agent_id) for item in value)
    return False


def _mailbox_item(
    record: ArtifactVersionRecord,
    route: _RouteDecision,
    agent_id: str,
) -> AgentMailboxItem:
    artifact = record.artifact
    actionable_reasons = _actionable_reasons(artifact)
    sensitive = artifact.visibility_policy.contains_sensitive_content
    redaction_required = artifact.visibility_policy.redaction_required
    return AgentMailboxItem(
        artifact_id=record.artifact_id,
        version=record.version,
        bucket=route.bucket or "related",
        kind=artifact.kind,
        intent=artifact.intent,
        lifecycle_state=artifact.lifecycle_state,
        producer=artifact.producer,
        audience=artifact.audience,
        visibility_audience=artifact.visibility_policy.audience,
        part_types=tuple(part.part_type for part in artifact.parts),
        routing_reasons=route.reasons,
        actionable=route.bucket == "inbox" and bool(actionable_reasons),
        actionable_reasons=actionable_reasons if route.bucket == "inbox" else (),
        contains_sensitive_content=sensitive,
        redaction_required=redaction_required,
        scope=_scope_to_json(artifact),
        preview=_preview_artifact(artifact, agent_id, redacted=sensitive or redaction_required),
    )


def _actionable_reasons(artifact: ExchangeArtifact) -> tuple[str, ...]:
    reasons: list[str] = []
    has_action_signal = False
    if artifact.kind in ACTIONABLE_KINDS:
        reasons.append(f"kind:{artifact.kind}")
        has_action_signal = True
    if artifact.intent in ACTIONABLE_INTENTS:
        reasons.append(f"intent:{artifact.intent}")
        has_action_signal = True
    if not has_action_signal:
        return ()
    if artifact.lifecycle_state in ACTIONABLE_LIFECYCLE_STATES:
        reasons.append(f"lifecycle:{artifact.lifecycle_state}")
    return tuple(reasons)


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


def _preview_artifact(
    artifact: ExchangeArtifact,
    agent_id: str,
    *,
    redacted: bool,
) -> dict[str, object]:
    if redacted:
        return {
            "redacted": True,
            "reason": "visibility_policy requires sensitive-content redaction",
            "part_types": [part.part_type for part in artifact.parts],
        }

    text_preview = ""
    structured_preview: dict[str, object] = {}
    relation_kinds: list[str] = []
    ref_clues: list[dict[str, str]] = []
    log_actions: list[str] = []

    for part in artifact.parts:
        if part.part_type == "text" and part.text and not text_preview:
            text_preview = _truncate(part.text, PREVIEW_TEXT_LIMIT)
        elif part.part_type == "structured" and part.data and not structured_preview:
            structured_preview = _compact_mapping(part.data)
        elif part.part_type == "relation" and part.relation is not None:
            relation_kinds.append(part.relation.relation_kind)
        elif part.part_type == "ref" and part.ref is not None:
            ref_clues.append(_reference_clue(part.ref))
        elif part.part_type == "log" and part.log is not None:
            log_actions.append(part.log.action)

    preview: dict[str, object] = {}
    if text_preview:
        preview["text"] = text_preview
    if structured_preview:
        preview["structured"] = structured_preview
    if relation_kinds:
        preview["relation_kinds"] = relation_kinds
    if ref_clues:
        preview["refs"] = ref_clues
    if log_actions:
        preview["log_actions"] = log_actions
    if not preview:
        preview["agent_id"] = agent_id
    preview["redacted"] = False
    return preview


def _compact_mapping(value: Mapping[str, object]) -> dict[str, object]:
    compact: dict[str, object] = {}
    for key, item in value.items():
        if isinstance(item, (str, int, float, bool)) or item is None:
            compact[key] = item
        elif isinstance(item, (list, tuple)):
            compact[key] = f"<{len(item)} items>"
        elif isinstance(item, Mapping):
            compact[key] = f"<{len(item)} fields>"
        else:
            compact[key] = f"<{type(item).__name__}>"
        if len(compact) >= 8:
            break
    return compact


def _reference_clue(reference: ExchangeReference) -> dict[str, str]:
    return {
        "ref_kind": reference.ref_kind,
        "ref_id": reference.ref_id,
        "version": reference.version,
        "path": reference.path,
        "label": reference.label,
    }


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."
