"""Mutation helpers for agent ExchangeArtifact communication actions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, Mapping

from .exchange import (
    ExchangeArtifact,
    ExchangeArtifactIntent,
    ExchangeArtifactKind,
    ExchangeArtifactLifecycleState,
    ExchangeCausality,
    ExchangeLog,
    ExchangePayloadPart,
    ExchangeScope,
    VisibilityPolicy,
)
from .exchange_store import JsonArtifactVersionStore

AgentExchangeTransitionState = Literal[
    "accepted",
    "rejected",
    "consumed",
    "superseded",
    "archived",
]

ALLOWED_AGENT_EXCHANGE_TRANSITIONS: tuple[AgentExchangeTransitionState, ...] = (
    "accepted",
    "rejected",
    "consumed",
    "superseded",
    "archived",
)


@dataclass(frozen=True, slots=True)
class AgentExchangeReplyResult:
    """Result of storing an agent reply artifact."""

    store_path: Path
    source_artifact_id: str
    source_version: str
    reply_artifact_id: str
    reply_version: str
    producer: str
    audience: tuple[str, ...]
    created: bool = True

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.created,
            "store_path": str(self.store_path),
            "source_artifact_id": self.source_artifact_id,
            "source_version": self.source_version,
            "reply_artifact_id": self.reply_artifact_id,
            "reply_version": self.reply_version,
            "producer": self.producer,
            "audience": list(self.audience),
            "created": self.created,
            "authority_split": {
                "exchange_store_mutated": self.created,
                "scheduler_state_mutated": False,
                "admission_ledger_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class AgentExchangeTransitionResult:
    """Result of transitioning one exact ExchangeArtifact version."""

    store_path: Path
    artifact_id: str
    version: str
    previous_lifecycle_state: str
    current_lifecycle_state: str
    actor: str
    timestamp: str
    reason: str = ""
    changed: bool = True

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": True,
            "store_path": str(self.store_path),
            "artifact_id": self.artifact_id,
            "version": self.version,
            "previous_lifecycle_state": self.previous_lifecycle_state,
            "current_lifecycle_state": self.current_lifecycle_state,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "reason": self.reason,
            "changed": self.changed,
            "already_in_target_state": not self.changed,
            "authority_split": {
                "exchange_store_mutated": self.changed,
                "scheduler_state_mutated": False,
                "admission_ledger_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }


def reply_to_exchange_artifact(
    *,
    store_path: str | Path,
    source_artifact_id: str,
    source_version: str,
    reply_artifact_id: str,
    reply_version: str = "v1",
    producer: str,
    text: str = "",
    structured: Mapping[str, object] | None = None,
    kind: ExchangeArtifactKind = "message",
    intent: ExchangeArtifactIntent = "inform",
    audience: tuple[str, ...] = (),
    created_at: str = "",
    replace_existing: bool = False,
) -> AgentExchangeReplyResult:
    """Create one exact-version reply artifact in the same exchange store."""

    if not source_artifact_id:
        raise ValueError("exchange reply requires a non-empty source_artifact_id")
    if not source_version:
        raise ValueError("exchange reply requires a non-empty source_version")
    if not reply_artifact_id:
        raise ValueError("exchange reply requires a non-empty reply_artifact_id")
    if not reply_version:
        raise ValueError("exchange reply requires a non-empty reply_version")
    if not producer:
        raise ValueError("exchange reply requires a non-empty producer")
    if not text and not structured:
        raise ValueError("exchange reply requires text or structured payload")

    path = Path(store_path)
    store = JsonArtifactVersionStore(path)
    try:
        source = store.get(source_artifact_id, source_version).artifact
    except KeyError as exc:
        raise ValueError(
            f"source exchange artifact version not found in {path}: "
            f"{source_artifact_id!r}@{source_version!r}"
        ) from exc

    timestamp = created_at or datetime.now(UTC).isoformat()
    target_audience = audience or ((source.producer,) if source.producer else ())
    source_token = _artifact_version_token(source_artifact_id, source_version)
    parts: list[ExchangePayloadPart] = []
    if text:
        parts.append(ExchangePayloadPart(part_type="text", text=text))
    if structured:
        parts.append(ExchangePayloadPart(part_type="structured", data=dict(structured)))
    parts.append(
        ExchangePayloadPart(
            part_type="log",
            log=ExchangeLog(
                timestamp=timestamp,
                actor=producer,
                action="exchange_artifact_replied",
                channel="agent-exchange-actions",
                summary=f"Reply to {source_token}",
                related_artifact_ids=(source_artifact_id, reply_artifact_id),
            ),
        )
    )

    reply = ExchangeArtifact(
        artifact_id=reply_artifact_id,
        kind=kind,
        intent=intent,
        producer=producer,
        audience=target_audience,
        scope=_reply_scope(source.scope, producer),
        causality=ExchangeCausality(
            replies_to=(source_token,),
            caused_by=(source_token,),
            correlation_id=source.causality.correlation_id or source.artifact_id,
        ),
        lifecycle_state="proposed",
        visibility_policy=VisibilityPolicy(
            audience=tuple(dict.fromkeys((*target_audience, producer))),
            cross_lane=source.visibility_policy.cross_lane,
            contains_sensitive_content=source.visibility_policy.contains_sensitive_content,
            redaction_required=source.visibility_policy.redaction_required,
        ),
        created_at=timestamp,
        version=reply_version,
        parts=tuple(parts),
    )
    store.put(reply, replace_existing=replace_existing)
    return AgentExchangeReplyResult(
        store_path=path,
        source_artifact_id=source_artifact_id,
        source_version=source_version,
        reply_artifact_id=reply_artifact_id,
        reply_version=reply_version,
        producer=producer,
        audience=target_audience,
    )


def transition_exchange_artifact_lifecycle(
    *,
    store_path: str | Path,
    artifact_id: str,
    version: str,
    target_state: AgentExchangeTransitionState,
    actor: str,
    reason: str = "",
    timestamp: str = "",
) -> AgentExchangeTransitionResult:
    """Transition one exact stored ExchangeArtifact version."""

    if not artifact_id:
        raise ValueError("exchange lifecycle transition requires a non-empty artifact_id")
    if not version:
        raise ValueError("exchange lifecycle transition requires a non-empty version")
    if target_state not in ALLOWED_AGENT_EXCHANGE_TRANSITIONS:
        allowed = ", ".join(ALLOWED_AGENT_EXCHANGE_TRANSITIONS)
        raise ValueError(
            f"unsupported exchange lifecycle target_state {target_state!r}; "
            f"expected one of: {allowed}"
        )
    if not actor:
        raise ValueError("exchange lifecycle transition requires a non-empty actor")

    path = Path(store_path)
    store = JsonArtifactVersionStore(path)
    try:
        record = store.get(artifact_id, version)
    except KeyError as exc:
        raise ValueError(
            f"exchange artifact version not found in {path}: "
            f"{artifact_id!r}@{version!r}"
        ) from exc

    event_timestamp = timestamp or datetime.now(UTC).isoformat()
    previous_state = record.artifact.lifecycle_state
    if previous_state == target_state:
        return AgentExchangeTransitionResult(
            store_path=path,
            artifact_id=artifact_id,
            version=version,
            previous_lifecycle_state=previous_state,
            current_lifecycle_state=previous_state,
            actor=actor,
            timestamp=event_timestamp,
            reason=reason,
            changed=False,
        )

    log_part = ExchangePayloadPart(
        part_type="log",
        log=ExchangeLog(
            timestamp=event_timestamp,
            actor=actor,
            action=f"exchange_artifact_{target_state}",
            channel="agent-exchange-actions",
            summary=reason or f"ExchangeArtifact exact version marked {target_state}.",
            related_artifact_ids=(artifact_id,),
        ),
    )
    transitioned = replace(
        record.artifact,
        lifecycle_state=target_state,  # type: ignore[arg-type]
        parts=(*record.artifact.parts, log_part),
    )
    store.replace_exact(transitioned)
    return AgentExchangeTransitionResult(
        store_path=path,
        artifact_id=artifact_id,
        version=version,
        previous_lifecycle_state=previous_state,
        current_lifecycle_state=target_state,
        actor=actor,
        timestamp=event_timestamp,
        reason=reason,
        changed=True,
    )


def _artifact_version_token(artifact_id: str, version: str) -> str:
    return f"{artifact_id}@{version}"


def _reply_scope(source_scope: ExchangeScope, producer: str) -> ExchangeScope:
    return ExchangeScope(
        trajectory_id=source_scope.trajectory_id,
        lane_id=source_scope.lane_id,
        event_id=source_scope.event_id,
        task_id=source_scope.task_id,
        context_id=source_scope.context_id,
        agent_id=producer or source_scope.agent_id,
        runtime_session_id=source_scope.runtime_session_id,
    )
