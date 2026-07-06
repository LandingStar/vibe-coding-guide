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
