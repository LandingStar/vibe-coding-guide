"""Read-only communication history summaries over ExchangeArtifact records."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .exchange import ExchangeArtifact, ExchangeLog, ExchangePayloadPart, ExchangeReference
from .exchange_store import ArtifactVersionRecord, JsonArtifactVersionStore
from .log_decoration import LogDecorationPipeline, LogDecorationPipelineResult
from .log_decoration_adapters import exchange_log_to_decoration_record
from .log_readback import LogRecordRef


ACTION_EXPECTED_KINDS = {
    "query",
    "request",
    "proposal",
    "blocker",
    "review",
    "contract",
    "handoff",
    "retention",
}
ACTION_EXPECTED_INTENTS = {
    "ask",
    "propose",
    "require_review",
    "request_merge",
    "declare_blocked",
    "unblock",
    "request_registration",
    "request_retention",
}
ACTION_EXPECTED_LIFECYCLE_STATES = {"draft", "proposed", "accepted"}
SCHEDULER_SUBMISSION_PRODUCT_TYPES = {
    "scheduler_task_submission",
    "scheduler_task_batch_submission",
}


@dataclass(frozen=True, slots=True)
class AgentExchangeCausalityEdge:
    """Compact causality edge between exact exchange artifact versions."""

    source_artifact_id: str
    source_version: str
    relation_kind: str
    target: str

    def to_json_dict(self) -> dict[str, object]:
        return {
            "source_artifact_id": self.source_artifact_id,
            "source_version": self.source_version,
            "source": _artifact_version_token(self.source_artifact_id, self.source_version),
            "relation_kind": self.relation_kind,
            "target": self.target,
        }


@dataclass(frozen=True, slots=True)
class AgentExchangeHistoryLogEntry:
    """One compact log entry with source artifact/version clues."""

    source_artifact_id: str
    source_version: str
    timestamp: str
    actor: str
    action: str
    channel: str = ""
    summary: str = ""
    related_artifact_ids: tuple[str, ...] = ()
    related_event_ids: tuple[str, ...] = ()
    related_run_ids: tuple[str, ...] = ()
    sequence: int | None = None
    clock: str = "wall"
    source_redacted: bool = False

    def to_json_dict(self) -> dict[str, object]:
        return {
            "source_artifact_id": self.source_artifact_id,
            "source_version": self.source_version,
            "source": _artifact_version_token(self.source_artifact_id, self.source_version),
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "channel": self.channel,
            "summary": self.summary,
            "related_artifact_ids": list(self.related_artifact_ids),
            "related_event_ids": list(self.related_event_ids),
            "related_run_ids": list(self.related_run_ids),
            "sequence": self.sequence,
            "clock": self.clock,
            "source_redacted": self.source_redacted,
        }


@dataclass(frozen=True, slots=True)
class ExchangeCommunicationReadbackEnvelope:
    """Human/audit-oriented readback projection for one ExchangeArtifact version."""

    schema_version: str
    record_id: str
    record_kind: str
    timestamp: str
    actor: str
    action: str
    status: str
    summary: str
    reason: str = ""
    run_id: str = ""
    correlation_id: str = ""
    subject_refs: tuple[LogRecordRef, ...] = ()
    input_refs: tuple[LogRecordRef, ...] = ()
    output_refs: tuple[LogRecordRef, ...] = ()
    evidence_refs: tuple[LogRecordRef, ...] = ()
    related_record_ids: tuple[str, ...] = ()
    next_hint: str = ""
    sensitivity: str = "internal"
    redaction_state: str = "contains_no_raw_secret"
    raw_payload_persisted: bool = False
    artifact_kind: str = ""
    intent: str = ""
    lifecycle_state: str = ""
    producer: str = ""
    audience: tuple[str, ...] = ()
    part_types: tuple[str, ...] = ()
    relation_kinds: tuple[str, ...] = ()
    action_expected: bool = False
    action_expectation: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "record_kind": self.record_kind,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "status": self.status,
            "summary": self.summary,
            "reason": self.reason,
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "subject_refs": [ref.to_json_dict() for ref in self.subject_refs],
            "input_refs": [ref.to_json_dict() for ref in self.input_refs],
            "output_refs": [ref.to_json_dict() for ref in self.output_refs],
            "evidence_refs": [ref.to_json_dict() for ref in self.evidence_refs],
            "related_record_ids": list(self.related_record_ids),
            "next_hint": self.next_hint,
            "sensitivity": self.sensitivity,
            "redaction_state": self.redaction_state,
            "raw_payload_persisted": self.raw_payload_persisted,
            "artifact_kind": self.artifact_kind,
            "intent": self.intent,
            "lifecycle_state": self.lifecycle_state,
            "producer": self.producer,
            "audience": list(self.audience),
            "part_types": list(self.part_types),
            "relation_kinds": list(self.relation_kinds),
            "action_expected": self.action_expected,
            "action_expectation": self.action_expectation,
        }


@dataclass(frozen=True, slots=True)
class AgentExchangeHistorySummary:
    """Read-only communication history summary over exchange artifacts."""

    store_path: Path | None = None
    exists: bool = True
    agent_id_filter: str = ""
    correlation_id_filter: str = ""
    artifact_count: int = 0
    version_count: int = 0
    participant_counts: Mapping[str, int] = field(default_factory=dict)
    lifecycle_counts: Mapping[str, int] = field(default_factory=dict)
    causality_edges: tuple[AgentExchangeCausalityEdge, ...] = ()
    log_entries: tuple[AgentExchangeHistoryLogEntry, ...] = ()
    log_decoration_results: tuple[LogDecorationPipelineResult, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def participant_count(self) -> int:
        return len(self.participant_counts)

    @property
    def causality_edge_count(self) -> int:
        return len(self.causality_edges)

    @property
    def log_entry_count(self) -> int:
        return len(self.log_entries)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "store_path": "" if self.store_path is None else str(self.store_path),
            "exists": self.exists,
            "agent_id_filter": self.agent_id_filter,
            "correlation_id_filter": self.correlation_id_filter,
            "artifact_count": self.artifact_count,
            "version_count": self.version_count,
            "participant_count": self.participant_count,
            "participant_counts": dict(self.participant_counts),
            "lifecycle_counts": dict(self.lifecycle_counts),
            "causality_edge_count": self.causality_edge_count,
            "causality_edges": [edge.to_json_dict() for edge in self.causality_edges],
            "log_entry_count": self.log_entry_count,
            "log_entries": [entry.to_json_dict() for entry in self.log_entries],
            "log_decoration_results": [
                result.to_json_dict()
                for result in self.log_decoration_results
            ],
            "errors": list(self.errors),
            "authority_split": {
                "exchange_store_authority": "JsonArtifactVersionStore",
                "read_model_only": True,
                "scheduler_mutated": False,
                "exchange_store_mutated": False,
                "admission_ledger_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }


def build_agent_exchange_history_summary(
    records: Iterable[ArtifactVersionRecord],
    *,
    agent_id: str = "",
    correlation_id: str = "",
    include_archived: bool = False,
    decoration_pipeline: LogDecorationPipeline | None = None,
) -> AgentExchangeHistorySummary:
    """Build a read-only communication history summary over loaded records."""

    selected = tuple(
        record
        for record in records
        if _include_record(
            record,
            agent_id=agent_id,
            correlation_id=correlation_id,
            include_archived=include_archived,
        )
    )
    participant_counts: Counter[str] = Counter()
    lifecycle_counts: Counter[str] = Counter()
    causality_edges: list[AgentExchangeCausalityEdge] = []
    log_entries: list[tuple[int, AgentExchangeHistoryLogEntry]] = []

    for order, record in enumerate(selected):
        artifact = record.artifact
        lifecycle_counts[artifact.lifecycle_state] += 1
        for participant in _participants(artifact):
            participant_counts[participant] += 1
        causality_edges.extend(_causality_edges(record))
        for part in artifact.parts:
            if part.part_type == "log" and part.log is not None:
                log_entries.append((order, _log_entry(record, part)))

    ordered_logs = tuple(
        entry
        for _order, entry in sorted(
            log_entries,
            key=lambda item: (
                item[1].timestamp,
                -1 if item[1].sequence is None else item[1].sequence,
                item[0],
            ),
        )
    )
    decoration_results: tuple[LogDecorationPipelineResult, ...] = ()
    if decoration_pipeline is not None:
        decoration_results = tuple(
            decoration_pipeline.run(_log_entry_decoration_record(entry))
            for entry in ordered_logs
        )
    return AgentExchangeHistorySummary(
        agent_id_filter=agent_id,
        correlation_id_filter=correlation_id,
        artifact_count=len({record.artifact_id for record in selected}),
        version_count=len(selected),
        participant_counts=dict(sorted(participant_counts.items())),
        lifecycle_counts=dict(sorted(lifecycle_counts.items())),
        causality_edges=tuple(causality_edges),
        log_entries=ordered_logs,
        log_decoration_results=decoration_results,
    )


def inspect_agent_exchange_history_summary(
    path: str | Path,
    *,
    agent_id: str = "",
    correlation_id: str = "",
    include_archived: bool = False,
    decoration_pipeline: LogDecorationPipeline | None = None,
) -> AgentExchangeHistorySummary:
    """Read a JSON artifact store into a non-mutating history summary."""

    store_path = Path(path)
    if not store_path.exists():
        return AgentExchangeHistorySummary(
            store_path=store_path,
            exists=False,
            agent_id_filter=agent_id,
            correlation_id_filter=correlation_id,
        )

    try:
        records = JsonArtifactVersionStore(store_path).list_records()
    except Exception as exc:
        return AgentExchangeHistorySummary(
            store_path=store_path,
            exists=True,
            agent_id_filter=agent_id,
            correlation_id_filter=correlation_id,
            errors=(str(exc),),
        )

    summary = build_agent_exchange_history_summary(
        records,
        agent_id=agent_id,
        correlation_id=correlation_id,
        include_archived=include_archived,
        decoration_pipeline=decoration_pipeline,
    )
    return AgentExchangeHistorySummary(
        store_path=store_path,
        exists=True,
        agent_id_filter=summary.agent_id_filter,
        correlation_id_filter=summary.correlation_id_filter,
        artifact_count=summary.artifact_count,
        version_count=summary.version_count,
        participant_counts=summary.participant_counts,
        lifecycle_counts=summary.lifecycle_counts,
        causality_edges=summary.causality_edges,
        log_entries=summary.log_entries,
        log_decoration_results=summary.log_decoration_results,
        errors=summary.errors,
    )


def exchange_artifact_record_to_readback_envelope(
    record: ArtifactVersionRecord,
    *,
    actor: str = "agent-exchange",
) -> ExchangeCommunicationReadbackEnvelope:
    """Project one exact ExchangeArtifact version into a draft readback envelope.

    This is a read-only projection. It does not mutate the exchange store,
    lifecycle state, action candidates, scheduler state, or admission ledger.
    """

    artifact = record.artifact
    exact_id = _artifact_version_token(record.artifact_id, record.version)
    action_expectation = _action_expectation(artifact)
    return ExchangeCommunicationReadbackEnvelope(
        schema_version="exchange-communication-readback-envelope.v1",
        record_id=exact_id,
        record_kind="exchange_communication",
        timestamp=_primary_timestamp(artifact),
        actor=artifact.producer or _first_log_actor(artifact) or actor,
        action=f"exchange_{artifact.intent}",
        status=artifact.lifecycle_state,
        summary=_communication_summary(record),
        reason=_communication_reason(artifact, action_expectation=action_expectation),
        run_id=_first_related_run_id(artifact),
        correlation_id=_communication_correlation_id(record),
        subject_refs=_communication_subject_refs(record),
        input_refs=_communication_input_refs(record),
        output_refs=_communication_output_refs(record),
        evidence_refs=_communication_evidence_refs(record),
        related_record_ids=_communication_related_record_ids(record),
        next_hint=_communication_next_hint(record, action_expectation=action_expectation),
        sensitivity=_communication_sensitivity(artifact),
        redaction_state=_communication_redaction_state(artifact),
        raw_payload_persisted=False,
        artifact_kind=artifact.kind,
        intent=artifact.intent,
        lifecycle_state=artifact.lifecycle_state,
        producer=artifact.producer,
        audience=artifact.audience,
        part_types=tuple(part.part_type for part in artifact.parts),
        relation_kinds=_relation_kinds(artifact),
        action_expected=bool(action_expectation),
        action_expectation=action_expectation,
    )


def _include_record(
    record: ArtifactVersionRecord,
    *,
    agent_id: str,
    correlation_id: str,
    include_archived: bool,
) -> bool:
    artifact = record.artifact
    if artifact.lifecycle_state == "archived" and not include_archived:
        return False
    if agent_id and agent_id not in _participants(artifact):
        return False
    if correlation_id and correlation_id not in {
        artifact.causality.correlation_id,
        artifact.artifact_id,
        _artifact_version_token(artifact.artifact_id, artifact.version),
    }:
        return False
    return True


def _participants(artifact: ExchangeArtifact) -> tuple[str, ...]:
    participants: list[str] = []
    _append_nonempty(participants, artifact.producer)
    for value in artifact.audience:
        _append_nonempty(participants, value)
    for value in artifact.visibility_policy.audience:
        _append_nonempty(participants, value)
    _append_nonempty(participants, artifact.scope.agent_id)
    for part in artifact.parts:
        if part.log is not None:
            _append_nonempty(participants, part.log.actor)
        if part.ref is not None:
            _append_reference_participant(participants, part.ref)
        if part.relation is not None:
            _append_reference_participant(participants, part.relation.source)
            _append_reference_participant(participants, part.relation.target)
        if part.contract is not None:
            _append_nonempty(participants, part.contract.producer)
            for consumer in part.contract.consumers:
                _append_nonempty(participants, consumer)
            if part.contract.schema_ref is not None:
                _append_reference_participant(participants, part.contract.schema_ref)
    return tuple(dict.fromkeys(participants))


def _append_reference_participant(values: list[str], reference: ExchangeReference) -> None:
    if reference.ref_kind == "agent":
        _append_nonempty(values, reference.ref_id)


def _append_nonempty(values: list[str], value: str) -> None:
    if value:
        values.append(value)


def _causality_edges(record: ArtifactVersionRecord) -> tuple[AgentExchangeCausalityEdge, ...]:
    artifact = record.artifact
    edges: list[AgentExchangeCausalityEdge] = []
    for relation_kind, targets in (
        ("replies_to", artifact.causality.replies_to),
        ("depends_on", artifact.causality.depends_on),
        ("supersedes", artifact.causality.supersedes),
        ("caused_by", artifact.causality.caused_by),
    ):
        for target in targets:
            if target:
                edges.append(
                    AgentExchangeCausalityEdge(
                        source_artifact_id=record.artifact_id,
                        source_version=record.version,
                        relation_kind=relation_kind,
                        target=target,
                    )
                )
    return tuple(edges)


def _log_entry(
    record: ArtifactVersionRecord,
    part: ExchangePayloadPart,
) -> AgentExchangeHistoryLogEntry:
    assert part.log is not None
    artifact = record.artifact
    redacted = (
        artifact.visibility_policy.contains_sensitive_content
        or artifact.visibility_policy.redaction_required
    )
    return AgentExchangeHistoryLogEntry(
        source_artifact_id=record.artifact_id,
        source_version=record.version,
        timestamp=part.log.timestamp,
        actor=part.log.actor,
        action=part.log.action,
        channel=part.log.channel,
        summary=part.log.summary,
        related_artifact_ids=part.log.related_artifact_ids,
        related_event_ids=part.log.related_event_ids,
        related_run_ids=part.log.related_run_ids,
        sequence=part.log.sequence,
        clock=part.log.clock,
        source_redacted=redacted,
    )


def _log_entry_decoration_record(entry: AgentExchangeHistoryLogEntry):
    return exchange_log_to_decoration_record(
        ExchangeLog(
            timestamp=entry.timestamp,
            actor=entry.actor,
            action=entry.action,
            channel=entry.channel,
            summary=entry.summary,
            related_artifact_ids=entry.related_artifact_ids,
            related_event_ids=entry.related_event_ids,
            related_run_ids=entry.related_run_ids,
            sequence=entry.sequence,
            clock=entry.clock,  # type: ignore[arg-type]
        ),
        record_id=(
            f"exchange_history:{entry.source_artifact_id}@"
            f"{entry.source_version}:{entry.sequence}"
            if entry.sequence is not None
            else f"exchange_history:{entry.source_artifact_id}@{entry.source_version}"
        ),
        fields={
            "source_artifact_id": entry.source_artifact_id,
            "source_version": entry.source_version,
            "source": _artifact_version_token(
                entry.source_artifact_id,
                entry.source_version,
            ),
            "source_redacted": entry.source_redacted,
        },
    )


def _artifact_version_token(artifact_id: str, version: str) -> str:
    return f"{artifact_id}@{version}"


def _communication_summary(record: ArtifactVersionRecord) -> str:
    artifact = record.artifact
    exact_id = _artifact_version_token(record.artifact_id, record.version)
    audience = _audience_label(artifact)
    target = f" to {audience}" if audience else ""
    producer = artifact.producer or "unknown producer"
    summary = (
        f"Exchange artifact {exact_id} is a {artifact.lifecycle_state} "
        f"{artifact.kind} from {producer}{target} with intent {artifact.intent}."
    )
    log_summary = _first_log_summary(artifact)
    if log_summary:
        return f"{summary} Log summary: {_bounded_text(log_summary)}"
    return summary


def _communication_reason(
    artifact: ExchangeArtifact,
    *,
    action_expectation: str,
) -> str:
    if artifact.visibility_policy.redaction_required:
        return "Visibility policy requires redaction; payload body is omitted from readback."
    if artifact.visibility_policy.contains_sensitive_content:
        return "Visibility policy marks the artifact as sensitive; payload body is omitted from readback."
    if action_expectation:
        return (
            "Artifact kind, intent, lifecycle, or relation indicates expected "
            f"next action: {action_expectation}."
        )
    if _has_causality(artifact):
        return "Communication artifact is linked to an existing exchange thread."
    return "Communication artifact recorded for readback and audit."


def _communication_subject_refs(record: ArtifactVersionRecord) -> tuple[LogRecordRef, ...]:
    artifact = record.artifact
    refs: list[LogRecordRef] = [
        LogRecordRef(
            kind="exchange_artifact",
            id=record.artifact_id,
            version=record.version,
            role="subject",
        )
    ]
    if artifact.producer:
        refs.append(LogRecordRef(kind="agent", id=artifact.producer, role="subject"))
    refs.extend(LogRecordRef(kind="agent", id=agent, role="subject") for agent in artifact.audience)
    refs.extend(
        LogRecordRef(kind="agent", id=agent, role="subject")
        for agent in artifact.visibility_policy.audience
        if agent not in artifact.audience
    )
    refs.extend(_scope_refs(artifact, role="subject"))
    return tuple(refs)


def _communication_input_refs(record: ArtifactVersionRecord) -> tuple[LogRecordRef, ...]:
    artifact = record.artifact
    refs: list[LogRecordRef] = []
    refs.extend(_causality_refs(artifact))
    for part in artifact.parts:
        if part.ref is not None:
            refs.append(_reference_to_log_ref(part.ref, role="input"))
        if part.relation is not None:
            refs.append(
                _reference_to_log_ref(
                    part.relation.source,
                    role="input",
                    label=f"{part.relation.relation_kind}:source",
                )
            )
        if part.contract is not None and part.contract.schema_ref is not None:
            refs.append(_reference_to_log_ref(part.contract.schema_ref, role="input"))
    return tuple(refs)


def _communication_output_refs(record: ArtifactVersionRecord) -> tuple[LogRecordRef, ...]:
    artifact = record.artifact
    refs: list[LogRecordRef] = [
        LogRecordRef(
            kind="exchange_artifact",
            id=record.artifact_id,
            version=record.version,
            role="output",
        )
    ]
    for part in artifact.parts:
        if part.relation is not None:
            refs.append(
                _reference_to_log_ref(
                    part.relation.target,
                    role="output",
                    label=f"{part.relation.relation_kind}:target",
                )
            )
        if part.contract is not None:
            refs.append(
                LogRecordRef(
                    kind="contract",
                    id=part.contract.contract_id,
                    version=part.contract.version,
                    label=part.contract.contract_kind,
                    role="output",
                )
            )
        refs.extend(_scheduler_submission_refs(part))
    return tuple(refs)


def _communication_evidence_refs(record: ArtifactVersionRecord) -> tuple[LogRecordRef, ...]:
    artifact = record.artifact
    exact_id = _artifact_version_token(record.artifact_id, record.version)
    refs: list[LogRecordRef] = [
        LogRecordRef(
            kind="exchange_artifact",
            id=record.artifact_id,
            version=record.version,
            label=artifact.lifecycle_state,
            role="evidence",
        )
    ]
    for index, part in enumerate(artifact.parts):
        refs.append(
            LogRecordRef(
                kind="exchange_payload_part",
                id=f"{exact_id}:part-{index}",
                label=part.part_type,
                role="evidence",
            )
        )
        if part.log is not None:
            refs.append(
                LogRecordRef(
                    kind="exchange_log",
                    id=(
                        f"{exact_id}:log-{part.log.sequence}"
                        if part.log.sequence is not None
                        else f"{exact_id}:log-{index}"
                    ),
                    label=part.log.action,
                    role="evidence",
                )
            )
        if part.relation is not None:
            refs.append(
                LogRecordRef(
                    kind="exchange_relation",
                    id=part.relation.relation_id,
                    label=part.relation.relation_kind,
                    role="evidence",
                )
            )
        if part.contract is not None:
            refs.append(
                LogRecordRef(
                    kind="contract",
                    id=part.contract.contract_id,
                    version=part.contract.version,
                    label=part.contract.contract_kind,
                    role="evidence",
                )
            )
    return tuple(refs)


def _communication_related_record_ids(record: ArtifactVersionRecord) -> tuple[str, ...]:
    artifact = record.artifact
    related: list[str] = [
        _related_record_id(
            "exchange_artifact",
            _artifact_version_token(record.artifact_id, record.version),
        )
    ]
    for value in (artifact.producer, *artifact.audience, *artifact.visibility_policy.audience):
        if value:
            related.append(_related_record_id("agent", value))
    for ref in _scope_refs(artifact, role="related"):
        if ref.id:
            related.append(_related_record_id(ref.kind, ref.id))
    for relation_kind, targets in _causality_targets(artifact):
        related.extend(_related_record_id(relation_kind, target) for target in targets if target)
    for part in artifact.parts:
        if part.log is not None:
            related.extend(_related_record_id("artifact", item) for item in part.log.related_artifact_ids)
            related.extend(_related_record_id("event", item) for item in part.log.related_event_ids)
            related.extend(_related_record_id("run", item) for item in part.log.related_run_ids)
        if part.relation is not None:
            related.append(_related_record_id("relation", part.relation.relation_id))
        if part.contract is not None:
            related.append(_related_record_id("contract", part.contract.contract_id))
    return tuple(dict.fromkeys(related))


def _communication_next_hint(
    record: ArtifactVersionRecord,
    *,
    action_expectation: str,
) -> str:
    artifact = record.artifact
    exact_id = _artifact_version_token(record.artifact_id, record.version)
    if action_expectation == "scheduler_admission":
        return f"Inspect scheduler admission candidates for {exact_id}."
    if action_expectation == "review":
        return f"Inspect review intake or action candidates for {exact_id}."
    if action_expectation == "handoff_intake":
        return f"Inspect handoff intake or mailbox routing for {exact_id}."
    if action_expectation == "blocker_state":
        return f"Inspect blocker state or action candidates for {exact_id}."
    if action_expectation == "merge_intake":
        return f"Inspect merge intake or worker patch review candidates for {exact_id}."
    if action_expectation == "reply":
        return f"Inspect replies to {exact_id} or the audience mailbox."
    if action_expectation:
        return f"Inspect action candidates and mailbox routing for {exact_id}."
    if _has_causality(artifact):
        return f"Inspect exchange thread {artifact.causality.correlation_id or exact_id}."
    return f"Inspect ExchangeArtifact exact version {exact_id}."


def _communication_correlation_id(record: ArtifactVersionRecord) -> str:
    artifact = record.artifact
    return (
        artifact.causality.correlation_id
        or _first_related_run_id(artifact)
        or artifact.scope.runtime_session_id
        or artifact.scope.task_id
        or _artifact_version_token(record.artifact_id, record.version)
    )


def _communication_sensitivity(artifact: ExchangeArtifact) -> str:
    if artifact.visibility_policy.redaction_required:
        return "secret-bearing-redacted"
    if artifact.visibility_policy.contains_sensitive_content:
        return "sensitive"
    return "internal"


def _communication_redaction_state(artifact: ExchangeArtifact) -> str:
    if artifact.visibility_policy.redaction_required:
        return "redacted"
    if artifact.visibility_policy.contains_sensitive_content:
        return "requires_review"
    return "contains_no_raw_secret"


def _action_expectation(artifact: ExchangeArtifact) -> str:
    if artifact.lifecycle_state not in ACTION_EXPECTED_LIFECYCLE_STATES:
        return ""
    if _has_scheduler_submission_product(artifact):
        return "scheduler_admission"
    relation_kinds = set(_relation_kinds(artifact))
    if artifact.kind == "review" or artifact.intent == "require_review":
        return "review"
    if artifact.kind == "handoff" or "hands_off" in relation_kinds:
        return "handoff_intake"
    if (
        artifact.kind == "blocker"
        or artifact.intent == "declare_blocked"
        or relation_kinds.intersection({"blocks", "waits_for"})
    ):
        return "blocker_state"
    if artifact.intent == "request_merge" or "merges_into" in relation_kinds:
        return "merge_intake"
    if artifact.kind == "query" or artifact.intent == "ask":
        return "reply"
    if artifact.kind in ACTION_EXPECTED_KINDS or artifact.intent in ACTION_EXPECTED_INTENTS:
        return "decision"
    return ""


def _has_scheduler_submission_product(artifact: ExchangeArtifact) -> bool:
    for part in artifact.parts:
        if part.part_type != "structured":
            continue
        product_type = str(part.data.get("product_type", ""))
        if product_type in SCHEDULER_SUBMISSION_PRODUCT_TYPES:
            return True
    return False


def _scheduler_submission_refs(part: ExchangePayloadPart) -> tuple[LogRecordRef, ...]:
    if part.part_type != "structured":
        return ()
    product_type = str(part.data.get("product_type", ""))
    if product_type not in SCHEDULER_SUBMISSION_PRODUCT_TYPES:
        return ()
    refs: list[LogRecordRef] = [
        LogRecordRef(kind="scheduler_candidate", id=product_type, role="output")
    ]
    task_id = part.data.get("task_id")
    if isinstance(task_id, str) and task_id:
        refs.append(LogRecordRef(kind="task", id=task_id, label=product_type, role="output"))
    batch_id = part.data.get("batch_id")
    if isinstance(batch_id, str) and batch_id:
        refs.append(LogRecordRef(kind="task_batch", id=batch_id, label=product_type, role="output"))
    return tuple(refs)


def _scope_refs(artifact: ExchangeArtifact, *, role: str) -> tuple[LogRecordRef, ...]:
    scope = artifact.scope
    refs: list[LogRecordRef] = []
    for kind, value in (
        ("trajectory", scope.trajectory_id),
        ("lane", scope.lane_id),
        ("event", scope.event_id),
        ("task", scope.task_id),
        ("context", scope.context_id),
        ("agent", scope.agent_id),
        ("provider_session", scope.runtime_session_id),
    ):
        if value:
            refs.append(LogRecordRef(kind=kind, id=value, role=role))
    return tuple(refs)


def _causality_refs(artifact: ExchangeArtifact) -> tuple[LogRecordRef, ...]:
    refs: list[LogRecordRef] = []
    for relation_kind, targets in _causality_targets(artifact):
        refs.extend(
            LogRecordRef(
                kind="exchange_artifact",
                id=target,
                label=relation_kind,
                role="input",
            )
            for target in targets
            if target
        )
    return tuple(refs)


def _causality_targets(artifact: ExchangeArtifact) -> tuple[tuple[str, tuple[str, ...]], ...]:
    causality = artifact.causality
    return (
        ("replies_to", causality.replies_to),
        ("depends_on", causality.depends_on),
        ("supersedes", causality.supersedes),
        ("caused_by", causality.caused_by),
    )


def _has_causality(artifact: ExchangeArtifact) -> bool:
    return bool(
        artifact.causality.correlation_id
        or artifact.causality.replies_to
        or artifact.causality.depends_on
        or artifact.causality.supersedes
        or artifact.causality.caused_by
    )


def _relation_kinds(artifact: ExchangeArtifact) -> tuple[str, ...]:
    return tuple(
        part.relation.relation_kind
        for part in artifact.parts
        if part.relation is not None
    )


def _reference_to_log_ref(
    reference: ExchangeReference,
    *,
    role: str,
    label: str = "",
) -> LogRecordRef:
    return LogRecordRef(
        kind=reference.ref_kind,
        id=reference.ref_id,
        version=reference.version,
        path=reference.path,
        label=label or reference.label,
        role=role,
    )


def _primary_timestamp(artifact: ExchangeArtifact) -> str:
    if artifact.created_at:
        return artifact.created_at
    for part in artifact.parts:
        if part.log is not None and part.log.timestamp:
            return part.log.timestamp
    return ""


def _first_log_actor(artifact: ExchangeArtifact) -> str:
    for part in artifact.parts:
        if part.log is not None and part.log.actor:
            return part.log.actor
    return ""


def _first_log_summary(artifact: ExchangeArtifact) -> str:
    for part in artifact.parts:
        if part.log is not None and part.log.summary:
            return part.log.summary
    return ""


def _first_related_run_id(artifact: ExchangeArtifact) -> str:
    for part in artifact.parts:
        if part.log is not None and part.log.related_run_ids:
            return part.log.related_run_ids[0]
    return ""


def _audience_label(artifact: ExchangeArtifact) -> str:
    values = tuple(dict.fromkeys((*artifact.audience, *artifact.visibility_policy.audience)))
    return ", ".join(values)


def _related_record_id(kind: str, value: str) -> str:
    if value.startswith(f"{kind}:"):
        return value
    return f"{kind}:{value}"


def _bounded_text(value: str, *, limit: int = 240) -> str:
    text = str(value or "").replace("\r\n", "\n").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
