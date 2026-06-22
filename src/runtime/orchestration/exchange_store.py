"""Storage helpers for coordination exchange artifacts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from .exchange import (
    ExchangeArtifact,
    ExchangeCausality,
    ExchangeContract,
    ExchangeLog,
    ExchangePayloadPart,
    ExchangeReference,
    ExchangeRelation,
    ExchangeScope,
    VisibilityPolicy,
    validate_exchange_artifact,
)
from .exchange_admission_ledger import (
    ExchangeArtifactAdmissionRecord,
    JsonExchangeArtifactAdmissionLedger,
)

CoordinationEventKind = Literal[
    "artifact_recorded",
    "artifact_superseded",
    "artifact_consumed",
    "artifact_archived",
    "validation_failed",
]
EXCHANGE_ARTIFACT_STORE_SCHEMA_VERSION = "exchange-artifact-store.v1"
DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH = ".codex/orchestration/exchange-artifacts.json"

ExchangeArtifactAdmissionProductType = Literal[
    "scheduler_task_submission",
    "scheduler_task_batch_submission",
]
ExchangeArtifactAdmissionProjectionStatus = Literal[
    "not_admitted",
    "admitted",
    "failed",
    "rejected_duplicate",
    "mixed",
    "unknown",
]


@dataclass(frozen=True, slots=True)
class ArtifactVersionRecord:
    """Stored version of an exchange artifact."""

    artifact_id: str
    version: str
    artifact: ExchangeArtifact


@dataclass(frozen=True, slots=True)
class ExchangeArtifactAdmissionCandidate:
    """Advisory admission-prep metadata for a stored artifact version."""

    product_type: ExchangeArtifactAdmissionProductType
    artifact_id: str
    version: str
    part_index: int
    valid: bool = True
    task_ids: tuple[str, ...] = ()
    batch_id: str = ""
    task_count: int = 0
    error: str = ""
    binding_reference_readiness: Mapping[str, object] | None = None
    latest_binding_reference_summary: Mapping[str, object] | None = None

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible inspection payload."""

        payload: dict[str, object] = {
            "product_type": self.product_type,
            "artifact_id": self.artifact_id,
            "version": self.version,
            "part_index": self.part_index,
            "valid": self.valid,
            "task_ids": list(self.task_ids),
            "batch_id": self.batch_id,
            "task_count": self.task_count,
            "error": self.error,
        }
        if self.binding_reference_readiness:
            payload["binding_reference_readiness"] = dict(
                self.binding_reference_readiness
            )
        if self.latest_binding_reference_summary:
            payload["latest_binding_reference_summary"] = dict(
                self.latest_binding_reference_summary
            )
        return payload


@dataclass(frozen=True, slots=True)
class ExchangeArtifactAdmissionStateProjection:
    """Ledger-derived read model for one exact exchange artifact version."""

    status: ExchangeArtifactAdmissionProjectionStatus = "not_admitted"
    record_count: int = 0
    status_counts: Mapping[str, int] = field(default_factory=dict)
    latest_record_id: str = ""
    latest_status: str = ""
    latest_timestamp: str = ""
    latest_actor: str = ""
    latest_surface: str = ""
    latest_error_summary: str = ""
    admitted_record_ids: tuple[str, ...] = ()
    rejected_duplicate_record_ids: tuple[str, ...] = ()
    failed_record_ids: tuple[str, ...] = ()
    source: str = "exchange_artifact_admission_ledger"

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible admission-state projection."""

        return {
            "status": self.status,
            "record_count": self.record_count,
            "status_counts": dict(self.status_counts),
            "latest_record_id": self.latest_record_id,
            "latest_status": self.latest_status,
            "latest_timestamp": self.latest_timestamp,
            "latest_actor": self.latest_actor,
            "latest_surface": self.latest_surface,
            "latest_error_summary": self.latest_error_summary,
            "admitted_record_ids": list(self.admitted_record_ids),
            "rejected_duplicate_record_ids": list(self.rejected_duplicate_record_ids),
            "failed_record_ids": list(self.failed_record_ids),
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class ExchangeArtifactVersionSummary:
    """Read-only summary for one stored exchange artifact version."""

    artifact_id: str
    version: str
    latest: bool
    kind: str
    intent: str
    producer: str
    lifecycle_state: str
    created_at: str = ""
    audience: tuple[str, ...] = ()
    part_types: tuple[str, ...] = ()
    scope: ExchangeScope = field(default_factory=ExchangeScope)
    contains_sensitive_content: bool = False
    redaction_required: bool = False
    admission_candidates: tuple[ExchangeArtifactAdmissionCandidate, ...] = ()
    admission_state: ExchangeArtifactAdmissionStateProjection = field(
        default_factory=ExchangeArtifactAdmissionStateProjection
    )

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible inspection payload."""

        return {
            "artifact_id": self.artifact_id,
            "version": self.version,
            "latest": self.latest,
            "kind": self.kind,
            "intent": self.intent,
            "producer": self.producer,
            "lifecycle_state": self.lifecycle_state,
            "created_at": self.created_at,
            "audience": list(self.audience),
            "part_types": list(self.part_types),
            "scope": _scope_to_json(self.scope),
            "contains_sensitive_content": self.contains_sensitive_content,
            "redaction_required": self.redaction_required,
            "admission_candidates": [
                candidate.to_json_dict()
                for candidate in self.admission_candidates
            ],
            "admission_state": self.admission_state.to_json_dict(),
        }


@dataclass(frozen=True, slots=True)
class ExchangeArtifactInspectionBundle:
    """Read-only inspection bundle over a local exchange artifact store."""

    store_path: Path
    exists: bool
    schema_version: str = EXCHANGE_ARTIFACT_STORE_SCHEMA_VERSION
    summaries: tuple[ExchangeArtifactVersionSummary, ...] = ()
    errors: tuple[str, ...] = ()
    admission_ledger_path: Path | None = None
    admission_ledger_exists: bool = False

    @property
    def artifact_count(self) -> int:
        """Return the number of unique artifact ids in the bundle."""

        return len({summary.artifact_id for summary in self.summaries})

    @property
    def version_count(self) -> int:
        """Return the number of stored artifact versions in the bundle."""

        return len(self.summaries)

    @property
    def admission_candidate_count(self) -> int:
        """Return the number of detected admission-prep candidates."""

        return sum(len(summary.admission_candidates) for summary in self.summaries)

    @property
    def error_count(self) -> int:
        """Return the number of isolated inspection errors."""

        return len(self.errors)

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible inspection payload."""

        return {
            "store_path": str(self.store_path),
            "exists": self.exists,
            "schema_version": self.schema_version,
            "artifact_count": self.artifact_count,
            "version_count": self.version_count,
            "admission_candidate_count": self.admission_candidate_count,
            "admission_ledger_path": (
                "" if self.admission_ledger_path is None else str(self.admission_ledger_path)
            ),
            "admission_ledger_exists": self.admission_ledger_exists,
            "error_count": self.error_count,
            "summaries": [summary.to_json_dict() for summary in self.summaries],
            "errors": list(self.errors),
            "authority_split": {
                "scheduler_state_authority": "scheduler_snapshot",
                "admission_preparation_only": True,
                "admission_state_source": "exchange_artifact_admission_ledger",
                "scheduler_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class CoordinationEvent:
    """Compact orchestration event referencing exchange artifacts."""

    event_id: str
    event_kind: CoordinationEventKind
    timestamp: str
    actor: str
    artifact_id: str = ""
    artifact_version: str = ""
    summary: str = ""
    related_artifact_ids: tuple[str, ...] = ()
    related_event_ids: tuple[str, ...] = ()
    related_run_ids: tuple[str, ...] = ()
    sequence: int | None = None

    def to_exchange_log(self) -> ExchangeLog:
        """Project this event into the compact exchange log part shape."""

        return ExchangeLog(
            timestamp=self.timestamp,
            actor=self.actor,
            action=self.event_kind,
            channel="coordination-event-log",
            summary=self.summary,
            related_artifact_ids=self.related_artifact_ids
            or ((self.artifact_id,) if self.artifact_id else ()),
            related_event_ids=self.related_event_ids or (self.event_id,),
            related_run_ids=self.related_run_ids,
            sequence=self.sequence,
            clock="wall",
        )


class InMemoryArtifactVersionStore:
    """Append-only in-memory store for exchange artifact versions."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], ArtifactVersionRecord] = {}
        self._versions: dict[str, list[str]] = {}

    def put(self, artifact: ExchangeArtifact) -> ArtifactVersionRecord:
        """Store one artifact version after validating scheduler-facing shape."""

        if not artifact.artifact_id:
            raise ValueError("exchange artifact requires a non-empty artifact_id")
        if not artifact.version:
            raise ValueError(f"exchange artifact {artifact.artifact_id!r} requires a non-empty version")

        errors = validate_exchange_artifact(artifact)
        if errors:
            joined = "; ".join(errors)
            raise ValueError(f"exchange artifact {artifact.artifact_id!r} is invalid: {joined}")

        key = (artifact.artifact_id, artifact.version)
        if key in self._records:
            raise ValueError(
                f"exchange artifact version already exists: "
                f"{artifact.artifact_id!r}@{artifact.version!r}"
            )

        record = ArtifactVersionRecord(
            artifact_id=artifact.artifact_id,
            version=artifact.version,
            artifact=artifact,
        )
        self._records[key] = record
        self._versions.setdefault(artifact.artifact_id, []).append(artifact.version)
        return record

    def get(self, artifact_id: str, version: str) -> ArtifactVersionRecord:
        """Return a stored version or raise KeyError."""

        return self._records[(artifact_id, version)]

    def latest(self, artifact_id: str) -> ArtifactVersionRecord:
        """Return the most recently inserted version for an artifact id."""

        versions = self._versions[artifact_id]
        return self.get(artifact_id, versions[-1])

    def list_versions(self, artifact_id: str) -> tuple[str, ...]:
        """Return versions in insertion order."""

        return tuple(self._versions.get(artifact_id, ()))


class JsonArtifactVersionStore:
    """Local JSON-backed append-only store for exchange artifact versions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def put(
        self,
        artifact: ExchangeArtifact,
        *,
        replace_existing: bool = False,
    ) -> ArtifactVersionRecord:
        """Store one artifact version after validating scheduler-facing shape."""

        _validate_storable_exchange_artifact(artifact)
        records = list(self._read_records())
        key = (artifact.artifact_id, artifact.version)
        if any((record.artifact_id, record.version) == key for record in records) and not replace_existing:
            raise ValueError(
                f"exchange artifact version already exists: "
                f"{artifact.artifact_id!r}@{artifact.version!r}"
            )
        records = [
            record
            for record in records
            if replace_existing is False or (record.artifact_id, record.version) != key
        ]
        record = ArtifactVersionRecord(
            artifact_id=artifact.artifact_id,
            version=artifact.version,
            artifact=artifact,
        )
        records.append(record)
        self._write_records(tuple(records))
        return record

    def get(self, artifact_id: str, version: str) -> ArtifactVersionRecord:
        """Return a stored version or raise KeyError."""

        for record in self._read_records():
            if record.artifact_id == artifact_id and record.version == version:
                return record
        raise KeyError((artifact_id, version))

    def latest(self, artifact_id: str) -> ArtifactVersionRecord:
        """Return the most recently inserted version for an artifact id."""

        versions = [record for record in self._read_records() if record.artifact_id == artifact_id]
        if not versions:
            raise KeyError(artifact_id)
        return versions[-1]

    def list_versions(self, artifact_id: str) -> tuple[str, ...]:
        """Return versions in insertion order."""

        return tuple(
            record.version
            for record in self._read_records()
            if record.artifact_id == artifact_id
        )

    def list_records(self) -> tuple[ArtifactVersionRecord, ...]:
        """Return all stored artifact version records in insertion order."""

        return self._read_records()

    def _read_records(self) -> tuple[ArtifactVersionRecord, ...]:
        if not self.path.exists():
            return ()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid exchange artifact store JSON at {self.path}: {exc.msg}") from exc
        if not isinstance(payload, Mapping):
            raise ValueError(f"exchange artifact store {self.path} must contain a JSON object")
        schema_version = payload.get("schema_version")
        if schema_version != EXCHANGE_ARTIFACT_STORE_SCHEMA_VERSION:
            raise ValueError(
                f"unsupported exchange artifact store version {schema_version!r}; "
                f"expected {EXCHANGE_ARTIFACT_STORE_SCHEMA_VERSION!r}"
            )
        records_value = payload.get("records", [])
        if not isinstance(records_value, list):
            raise ValueError(f"exchange artifact store {self.path} field 'records' must be a list")
        records: list[ArtifactVersionRecord] = []
        for index, item in enumerate(records_value):
            if not isinstance(item, Mapping):
                raise ValueError(
                    f"exchange artifact store {self.path} records[{index}] must be an object"
                )
            artifact_payload = item.get("artifact")
            if not isinstance(artifact_payload, Mapping):
                raise ValueError(
                    f"exchange artifact store {self.path} records[{index}].artifact must be an object"
                )
            artifact = exchange_artifact_from_json_dict(artifact_payload)
            _validate_storable_exchange_artifact(artifact)
            records.append(
                ArtifactVersionRecord(
                    artifact_id=artifact.artifact_id,
                    version=artifact.version,
                    artifact=artifact,
                )
            )
        return tuple(records)

    def _write_records(self, records: tuple[ArtifactVersionRecord, ...]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": EXCHANGE_ARTIFACT_STORE_SCHEMA_VERSION,
            "records": [
                {
                    "artifact_id": record.artifact_id,
                    "version": record.version,
                    "artifact": exchange_artifact_to_json_dict(record.artifact),
                }
                for record in records
            ],
        }
        temp_path = self.path.with_name(f"{self.path.name}.tmp")
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temp_path.replace(self.path)


class JsonlCoordinationEventLog:
    """Append-only JSONL coordination event log."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, event: CoordinationEvent) -> CoordinationEvent:
        """Append one event as a compact JSON object."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(_event_to_json(event), ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return event

    def read_all(self) -> tuple[CoordinationEvent, ...]:
        """Read all events from the JSONL log."""

        if not self.path.exists():
            return ()

        events: list[CoordinationEvent] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"invalid coordination event JSONL at {self.path}:{line_number}: {exc.msg}"
                    ) from exc
                events.append(_event_from_json(payload))
        return tuple(events)


def default_exchange_artifact_store_path(project_root: str | Path) -> Path:
    """Return the conventional local exchange artifact store path."""

    return Path(project_root) / DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH


def inspect_exchange_artifact_store(
    path: str | Path,
    *,
    admission_ledger_path: str | Path | None = None,
) -> ExchangeArtifactInspectionBundle:
    """Read a local JSON artifact store into a non-mutating inspection bundle."""

    store_path = Path(path)
    return build_exchange_artifact_inspection_bundle(
        store_path,
        exists=store_path.exists(),
        admission_ledger_path=admission_ledger_path,
    )


def build_exchange_artifact_inspection_bundle(
    path: str | Path,
    *,
    exists: bool | None = None,
    admission_ledger_path: str | Path | None = None,
) -> ExchangeArtifactInspectionBundle:
    """Build a read-only summary over stored artifact versions.

    Malformed stores are isolated as bundle errors so operator/resource
    inspection can report the problem without mutating scheduler state.
    """

    store_path = Path(path)
    ledger_path = Path(admission_ledger_path) if admission_ledger_path is not None else None
    file_exists = store_path.exists() if exists is None else exists
    if not file_exists:
        return ExchangeArtifactInspectionBundle(
            store_path=store_path,
            exists=False,
            admission_ledger_path=ledger_path,
            admission_ledger_exists=ledger_path.exists() if ledger_path is not None else False,
        )

    try:
        records = JsonArtifactVersionStore(store_path).list_records()
    except Exception as exc:
        return ExchangeArtifactInspectionBundle(
            store_path=store_path,
            exists=True,
            errors=(str(exc),),
            admission_ledger_path=ledger_path,
            admission_ledger_exists=ledger_path.exists() if ledger_path is not None else False,
        )

    ledger_records: tuple[ExchangeArtifactAdmissionRecord, ...] = ()
    ledger_errors: tuple[str, ...] = ()
    ledger_exists = ledger_path.exists() if ledger_path is not None else False
    if ledger_path is not None and ledger_exists:
        try:
            ledger_records = JsonExchangeArtifactAdmissionLedger(ledger_path).read_all()
        except Exception as exc:
            ledger_errors = (str(exc),)

    records_by_key: dict[tuple[str, str], list[ExchangeArtifactAdmissionRecord]] = {}
    for record in ledger_records:
        records_by_key.setdefault(
            (record.artifact_id, record.artifact_version),
            [],
        ).append(record)

    latest_keys: dict[str, str] = {}
    for record in records:
        latest_keys[record.artifact_id] = record.version

    summaries = tuple(
        _summarize_artifact_record(
            record,
            latest=latest_keys.get(record.artifact_id) == record.version,
            store_path=store_path,
            admission_state=_build_admission_state_projection(
                tuple(records_by_key.get((record.artifact_id, record.version), ()))
            ),
            admission_records=tuple(
                records_by_key.get((record.artifact_id, record.version), ())
            ),
        )
        for record in records
    )
    return ExchangeArtifactInspectionBundle(
        store_path=store_path,
        exists=True,
        summaries=summaries,
        errors=ledger_errors,
        admission_ledger_path=ledger_path,
        admission_ledger_exists=ledger_exists,
    )


def _summarize_artifact_record(
    record: ArtifactVersionRecord,
    *,
    latest: bool,
    store_path: Path | None = None,
    admission_state: ExchangeArtifactAdmissionStateProjection | None = None,
    admission_records: tuple[ExchangeArtifactAdmissionRecord, ...] = (),
) -> ExchangeArtifactVersionSummary:
    artifact = record.artifact
    return ExchangeArtifactVersionSummary(
        artifact_id=record.artifact_id,
        version=record.version,
        latest=latest,
        kind=artifact.kind,
        intent=artifact.intent,
        producer=artifact.producer,
        lifecycle_state=artifact.lifecycle_state,
        created_at=artifact.created_at,
        audience=artifact.audience,
        part_types=tuple(part.part_type for part in artifact.parts),
        scope=artifact.scope,
        contains_sensitive_content=artifact.visibility_policy.contains_sensitive_content,
        redaction_required=artifact.visibility_policy.redaction_required,
        admission_candidates=_detect_admission_candidates(
            artifact,
            store_path=store_path,
            admission_records=admission_records,
        ),
        admission_state=admission_state or ExchangeArtifactAdmissionStateProjection(),
    )


def _build_admission_state_projection(
    records: tuple[ExchangeArtifactAdmissionRecord, ...],
) -> ExchangeArtifactAdmissionStateProjection:
    if not records:
        return ExchangeArtifactAdmissionStateProjection()

    status_counts: dict[str, int] = {}
    admitted_ids: list[str] = []
    rejected_ids: list[str] = []
    failed_ids: list[str] = []
    for record in records:
        status_counts[record.status] = status_counts.get(record.status, 0) + 1
        if record.status == "admitted":
            admitted_ids.append(record.ledger_id)
        elif record.status == "rejected_duplicate":
            rejected_ids.append(record.ledger_id)
        elif record.status == "failed":
            failed_ids.append(record.ledger_id)

    latest = records[-1]
    if admitted_ids:
        status: ExchangeArtifactAdmissionProjectionStatus = "admitted"
    elif len(status_counts) > 1:
        status = "mixed"
    elif failed_ids:
        status = "failed"
    elif rejected_ids:
        status = "rejected_duplicate"
    else:
        status = "unknown"

    return ExchangeArtifactAdmissionStateProjection(
        status=status,
        record_count=len(records),
        status_counts=status_counts,
        latest_record_id=latest.ledger_id,
        latest_status=latest.status,
        latest_timestamp=latest.timestamp,
        latest_actor=latest.actor,
        latest_surface=latest.surface,
        latest_error_summary=latest.error_summary,
        admitted_record_ids=tuple(admitted_ids),
        rejected_duplicate_record_ids=tuple(rejected_ids),
        failed_record_ids=tuple(failed_ids),
    )


def _detect_admission_candidates(
    artifact: ExchangeArtifact,
    *,
    store_path: Path | None = None,
    admission_records: tuple[ExchangeArtifactAdmissionRecord, ...] = (),
) -> tuple[ExchangeArtifactAdmissionCandidate, ...]:
    candidates: list[ExchangeArtifactAdmissionCandidate] = []
    for index, part in enumerate(artifact.parts):
        if part.part_type != "structured":
            continue
        product_type = part.data.get("product_type")
        if product_type == "scheduler_task_submission":
            candidates.append(_with_binding_projection(
                _task_submission_candidate(artifact, index, part.data),
                store_path=store_path,
                admission_records=admission_records,
            ))
        elif product_type == "scheduler_task_batch_submission":
            candidates.append(_with_binding_projection(
                _batch_submission_candidate(artifact, index, part.data),
                store_path=store_path,
                admission_records=admission_records,
            ))
    return tuple(candidates)


def _task_submission_candidate(
    artifact: ExchangeArtifact,
    part_index: int,
    payload: Mapping[str, object],
) -> ExchangeArtifactAdmissionCandidate:
    task_id = payload.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        return ExchangeArtifactAdmissionCandidate(
            product_type="scheduler_task_submission",
            artifact_id=artifact.artifact_id,
            version=artifact.version,
            part_index=part_index,
            valid=False,
            error="scheduler_task_submission candidate requires non-empty task_id",
        )
    return ExchangeArtifactAdmissionCandidate(
        product_type="scheduler_task_submission",
        artifact_id=artifact.artifact_id,
        version=artifact.version,
        part_index=part_index,
        task_ids=(task_id,),
        task_count=1,
    )


def _batch_submission_candidate(
    artifact: ExchangeArtifact,
    part_index: int,
    payload: Mapping[str, object],
) -> ExchangeArtifactAdmissionCandidate:
    batch_id = payload.get("batch_id")
    tasks = payload.get("tasks")
    if not isinstance(batch_id, str) or not batch_id:
        return ExchangeArtifactAdmissionCandidate(
            product_type="scheduler_task_batch_submission",
            artifact_id=artifact.artifact_id,
            version=artifact.version,
            part_index=part_index,
            valid=False,
            error="scheduler_task_batch_submission candidate requires non-empty batch_id",
        )
    if not isinstance(tasks, list):
        return ExchangeArtifactAdmissionCandidate(
            product_type="scheduler_task_batch_submission",
            artifact_id=artifact.artifact_id,
            version=artifact.version,
            part_index=part_index,
            valid=False,
            batch_id=batch_id,
            error="scheduler_task_batch_submission candidate requires tasks list",
        )

    task_ids: list[str] = []
    for index, item in enumerate(tasks):
        if not isinstance(item, Mapping):
            return ExchangeArtifactAdmissionCandidate(
                product_type="scheduler_task_batch_submission",
                artifact_id=artifact.artifact_id,
                version=artifact.version,
                part_index=part_index,
                valid=False,
                batch_id=batch_id,
                task_count=len(tasks),
                error=f"scheduler_task_batch_submission candidate tasks[{index}] must be an object",
            )
        task_id = item.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            return ExchangeArtifactAdmissionCandidate(
                product_type="scheduler_task_batch_submission",
                artifact_id=artifact.artifact_id,
                version=artifact.version,
                part_index=part_index,
                valid=False,
                batch_id=batch_id,
                task_count=len(tasks),
                error=(
                    "scheduler_task_batch_submission candidate "
                    f"tasks[{index}].task_id is required"
                ),
            )
        task_ids.append(task_id)

    return ExchangeArtifactAdmissionCandidate(
        product_type="scheduler_task_batch_submission",
        artifact_id=artifact.artifact_id,
        version=artifact.version,
        part_index=part_index,
        task_ids=tuple(task_ids),
        batch_id=batch_id,
        task_count=len(tasks),
    )


def _with_binding_projection(
    candidate: ExchangeArtifactAdmissionCandidate,
    *,
    store_path: Path | None,
    admission_records: tuple[ExchangeArtifactAdmissionRecord, ...],
) -> ExchangeArtifactAdmissionCandidate:
    from dataclasses import replace

    readiness = (
        {}
        if store_path is None
        else _build_binding_readiness_projection(candidate, store_path)
    )
    latest_summary = _latest_binding_reference_summary(admission_records)
    if not readiness and not latest_summary:
        return candidate
    return replace(
        candidate,
        binding_reference_readiness=readiness or None,
        latest_binding_reference_summary=latest_summary or None,
    )


def _build_binding_readiness_projection(
    candidate: ExchangeArtifactAdmissionCandidate,
    store_path: Path,
) -> dict[str, object]:
    if not candidate.valid:
        return {}
    try:
        from .scheduler_submission import (
            inspect_supervisor_storage_binding_artifact_refs_for_submission,
        )

        inspection = inspect_supervisor_storage_binding_artifact_refs_for_submission(
            artifact_store_path=store_path,
            artifact_id=candidate.artifact_id,
            version=candidate.version,
        ).to_json_dict()
    except Exception as exc:
        return {
            "enabled": True,
            "ok": False,
            "source_artifact_id": candidate.artifact_id,
            "source_artifact_version": candidate.version,
            "submission_product_type": candidate.product_type,
            "task_count": candidate.task_count,
            "binding_ref_count": 0,
            "checked_ref_count": 0,
            "error_count": 1,
            "errors": [str(exc)],
            "tasks": [],
            "raw_evidence_json_read": False,
        }
    return _compact_binding_projection(inspection, enabled=True)


def _latest_binding_reference_summary(
    admission_records: tuple[ExchangeArtifactAdmissionRecord, ...],
) -> dict[str, object]:
    for record in reversed(admission_records):
        summary = record.binding_reference_summary
        if isinstance(summary, Mapping) and summary:
            compact = _compact_binding_projection(summary, enabled=True)
            compact["ledger_id"] = record.ledger_id
            compact["status"] = record.status
            compact["timestamp"] = record.timestamp
            compact["actor"] = record.actor
            compact["surface"] = record.surface
            compact["error_summary"] = record.error_summary
            return compact
    return {}


def _compact_binding_projection(
    payload: Mapping[str, object],
    *,
    enabled: bool,
) -> dict[str, object]:
    tasks: list[dict[str, object]] = []
    for task in _mapping_list(payload.get("tasks")):
        tasks.append(
            {
                "task_id": str(task.get("task_id", "")),
                "title": str(task.get("title", "")),
                "ok": bool(task.get("ok")),
                "binding_ref_count": _int_value(task.get("binding_ref_count")),
                "checked_ref_count": _int_value(task.get("checked_ref_count")),
                "error_count": _int_value(task.get("error_count")),
                "binding_refs": _compact_ref_list(task.get("binding_refs")),
                "checked_refs": _compact_ref_list(task.get("checked_refs")),
                "errors": _string_list(task.get("errors")),
            }
        )
    return {
        "enabled": bool(payload.get("enabled", enabled)),
        "ok": bool(payload.get("ok")),
        "source_artifact_id": str(payload.get("source_artifact_id", "")),
        "source_artifact_version": str(payload.get("source_artifact_version", "")),
        "submission_product_type": str(payload.get("submission_product_type", "")),
        "task_count": _int_value(payload.get("task_count")),
        "binding_ref_count": _int_value(payload.get("binding_ref_count")),
        "checked_ref_count": _int_value(payload.get("checked_ref_count")),
        "error_count": _int_value(payload.get("error_count")),
        "errors": _string_list(payload.get("errors")),
        "tasks": tasks,
        "raw_evidence_json_read": False,
    }


def _compact_ref_list(value: object) -> list[dict[str, object]]:
    refs: list[dict[str, object]] = []
    for item in _mapping_list(value):
        refs.append(
            {
                "ref_kind": str(item.get("ref_kind", "")),
                "ref_id": str(item.get("ref_id", "")),
                "version": str(item.get("version", "")),
                "path": str(item.get("path", "")),
                "label": str(item.get("label", "")),
            }
        )
    return refs


def _mapping_list(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return 0


def exchange_artifact_to_json_dict(artifact: ExchangeArtifact) -> dict[str, object]:
    """Serialize an exchange artifact to a stable JSON-compatible dict."""

    return {
        "artifact_id": artifact.artifact_id,
        "kind": artifact.kind,
        "intent": artifact.intent,
        "producer": artifact.producer,
        "audience": list(artifact.audience),
        "scope": _scope_to_json(artifact.scope),
        "causality": _causality_to_json(artifact.causality),
        "lifecycle_state": artifact.lifecycle_state,
        "visibility_policy": _visibility_policy_to_json(artifact.visibility_policy),
        "created_at": artifact.created_at,
        "version": artifact.version,
        "parts": [_payload_part_to_json(part) for part in artifact.parts],
    }


def exchange_artifact_from_json_dict(payload: Mapping[str, object]) -> ExchangeArtifact:
    """Deserialize an exchange artifact from a JSON-compatible dict."""

    parts_value = payload.get("parts", [])
    if not isinstance(parts_value, list):
        raise ValueError("exchange artifact field 'parts' must be a list")
    return ExchangeArtifact(
        artifact_id=_mapping_str(payload, "artifact_id"),
        kind=_mapping_str(payload, "kind") or "message",  # type: ignore[arg-type]
        intent=_mapping_str(payload, "intent") or "inform",  # type: ignore[arg-type]
        producer=_mapping_str(payload, "producer"),
        audience=_string_tuple(payload.get("audience")),
        scope=_scope_from_json(_mapping(payload.get("scope"))),
        causality=_causality_from_json(_mapping(payload.get("causality"))),
        lifecycle_state=_mapping_str(payload, "lifecycle_state") or "draft",  # type: ignore[arg-type]
        visibility_policy=_visibility_policy_from_json(_mapping(payload.get("visibility_policy"))),
        created_at=_mapping_str(payload, "created_at"),
        version=_mapping_str(payload, "version"),
        parts=tuple(_payload_part_from_json(_mapping(part)) for part in parts_value),
    )


def _event_to_json(event: CoordinationEvent) -> dict[str, object]:
    payload = asdict(event)
    payload["related_artifact_ids"] = list(event.related_artifact_ids)
    payload["related_event_ids"] = list(event.related_event_ids)
    payload["related_run_ids"] = list(event.related_run_ids)
    return payload


def _event_from_json(payload: dict[str, object]) -> CoordinationEvent:
    return CoordinationEvent(
        event_id=str(payload.get("event_id", "")),
        event_kind=str(payload.get("event_kind", "artifact_recorded")),  # type: ignore[arg-type]
        timestamp=str(payload.get("timestamp", "")),
        actor=str(payload.get("actor", "")),
        artifact_id=str(payload.get("artifact_id", "")),
        artifact_version=str(payload.get("artifact_version", "")),
        summary=str(payload.get("summary", "")),
        related_artifact_ids=tuple(str(item) for item in payload.get("related_artifact_ids", ()) or ()),
        related_event_ids=tuple(str(item) for item in payload.get("related_event_ids", ()) or ()),
        related_run_ids=tuple(str(item) for item in payload.get("related_run_ids", ()) or ()),
        sequence=payload.get("sequence") if isinstance(payload.get("sequence"), int) else None,
    )


def _validate_storable_exchange_artifact(artifact: ExchangeArtifact) -> None:
    if not artifact.artifact_id:
        raise ValueError("exchange artifact requires a non-empty artifact_id")
    if not artifact.version:
        raise ValueError(f"exchange artifact {artifact.artifact_id!r} requires a non-empty version")

    errors = validate_exchange_artifact(artifact)
    if errors:
        joined = "; ".join(errors)
        raise ValueError(f"exchange artifact {artifact.artifact_id!r} is invalid: {joined}")


def _scope_to_json(scope: ExchangeScope) -> dict[str, str]:
    return {
        "trajectory_id": scope.trajectory_id,
        "lane_id": scope.lane_id,
        "event_id": scope.event_id,
        "task_id": scope.task_id,
        "context_id": scope.context_id,
        "agent_id": scope.agent_id,
        "runtime_session_id": scope.runtime_session_id,
    }


def _scope_from_json(payload: Mapping[str, object]) -> ExchangeScope:
    return ExchangeScope(
        trajectory_id=_mapping_str(payload, "trajectory_id"),
        lane_id=_mapping_str(payload, "lane_id"),
        event_id=_mapping_str(payload, "event_id"),
        task_id=_mapping_str(payload, "task_id"),
        context_id=_mapping_str(payload, "context_id"),
        agent_id=_mapping_str(payload, "agent_id"),
        runtime_session_id=_mapping_str(payload, "runtime_session_id"),
    )


def _causality_to_json(causality: ExchangeCausality) -> dict[str, object]:
    return {
        "replies_to": list(causality.replies_to),
        "depends_on": list(causality.depends_on),
        "supersedes": list(causality.supersedes),
        "caused_by": list(causality.caused_by),
        "correlation_id": causality.correlation_id,
    }


def _causality_from_json(payload: Mapping[str, object]) -> ExchangeCausality:
    return ExchangeCausality(
        replies_to=_string_tuple(payload.get("replies_to")),
        depends_on=_string_tuple(payload.get("depends_on")),
        supersedes=_string_tuple(payload.get("supersedes")),
        caused_by=_string_tuple(payload.get("caused_by")),
        correlation_id=_mapping_str(payload, "correlation_id"),
    )


def _visibility_policy_to_json(policy: VisibilityPolicy) -> dict[str, object]:
    return {
        "audience": list(policy.audience),
        "cross_lane": policy.cross_lane,
        "contains_sensitive_content": policy.contains_sensitive_content,
        "redaction_required": policy.redaction_required,
    }


def _visibility_policy_from_json(payload: Mapping[str, object]) -> VisibilityPolicy:
    return VisibilityPolicy(
        audience=_string_tuple(payload.get("audience")),
        cross_lane=_mapping_bool(payload, "cross_lane"),
        contains_sensitive_content=_mapping_bool(payload, "contains_sensitive_content"),
        redaction_required=_mapping_bool(payload, "redaction_required"),
    )


def _payload_part_to_json(part: ExchangePayloadPart) -> dict[str, object]:
    return {
        "part_type": part.part_type,
        "text": part.text,
        "data": dict(part.data),
        "ref": None if part.ref is None else _reference_to_json(part.ref),
        "relation": None if part.relation is None else _relation_to_json(part.relation),
        "contract": None if part.contract is None else _contract_to_json(part.contract),
        "log": None if part.log is None else _log_to_json(part.log),
    }


def _payload_part_from_json(payload: Mapping[str, object]) -> ExchangePayloadPart:
    ref = payload.get("ref")
    relation = payload.get("relation")
    contract = payload.get("contract")
    log = payload.get("log")
    return ExchangePayloadPart(
        part_type=_mapping_str(payload, "part_type") or "text",  # type: ignore[arg-type]
        text=_mapping_str(payload, "text"),
        data=dict(_mapping(payload.get("data"))),
        ref=None if ref is None else _reference_from_json(_mapping(ref)),
        relation=None if relation is None else _relation_from_json(_mapping(relation)),
        contract=None if contract is None else _contract_from_json(_mapping(contract)),
        log=None if log is None else _log_from_json(_mapping(log)),
    )


def _reference_to_json(ref: ExchangeReference) -> dict[str, str]:
    return {
        "ref_kind": ref.ref_kind,
        "ref_id": ref.ref_id,
        "version": ref.version,
        "path": ref.path,
        "label": ref.label,
    }


def _reference_from_json(payload: Mapping[str, object]) -> ExchangeReference:
    return ExchangeReference(
        ref_kind=_mapping_str(payload, "ref_kind"),
        ref_id=_mapping_str(payload, "ref_id"),
        version=_mapping_str(payload, "version"),
        path=_mapping_str(payload, "path"),
        label=_mapping_str(payload, "label"),
    )


def _relation_to_json(relation: ExchangeRelation) -> dict[str, object]:
    return {
        "relation_id": relation.relation_id,
        "relation_kind": relation.relation_kind,
        "source": _reference_to_json(relation.source),
        "target": _reference_to_json(relation.target),
        "direction": relation.direction,
        "strength": relation.strength,
        "status": relation.status,
        "reason": relation.reason,
        "since": relation.since,
        "until": relation.until,
    }


def _relation_from_json(payload: Mapping[str, object]) -> ExchangeRelation:
    return ExchangeRelation(
        relation_id=_mapping_str(payload, "relation_id"),
        relation_kind=_mapping_str(payload, "relation_kind") or "depends_on",  # type: ignore[arg-type]
        source=_reference_from_json(_mapping(payload.get("source"))),
        target=_reference_from_json(_mapping(payload.get("target"))),
        direction=_mapping_str(payload, "direction") or "source_to_target",
        strength=_mapping_str(payload, "strength"),
        status=_mapping_str(payload, "status") or "active",  # type: ignore[arg-type]
        reason=_mapping_str(payload, "reason"),
        since=_mapping_str(payload, "since"),
        until=_mapping_str(payload, "until"),
    )


def _contract_to_json(contract: ExchangeContract) -> dict[str, object]:
    return {
        "contract_id": contract.contract_id,
        "contract_kind": contract.contract_kind,
        "version": contract.version,
        "title": contract.title,
        "producer": contract.producer,
        "consumers": list(contract.consumers),
        "status": contract.status,
        "schema_ref": None if contract.schema_ref is None else _reference_to_json(contract.schema_ref),
        "content": dict(contract.content),
        "compatibility": contract.compatibility,
        "supersedes": list(contract.supersedes),
        "effective_from": contract.effective_from,
    }


def _contract_from_json(payload: Mapping[str, object]) -> ExchangeContract:
    schema_ref = payload.get("schema_ref")
    return ExchangeContract(
        contract_id=_mapping_str(payload, "contract_id"),
        contract_kind=_mapping_str(payload, "contract_kind") or "coordination_protocol",  # type: ignore[arg-type]
        version=_mapping_str(payload, "version"),
        title=_mapping_str(payload, "title"),
        producer=_mapping_str(payload, "producer"),
        consumers=_string_tuple(payload.get("consumers")),
        status=_mapping_str(payload, "status") or "draft",  # type: ignore[arg-type]
        schema_ref=None if schema_ref is None else _reference_from_json(_mapping(schema_ref)),
        content=dict(_mapping(payload.get("content"))),
        compatibility=_mapping_str(payload, "compatibility"),
        supersedes=_string_tuple(payload.get("supersedes")),
        effective_from=_mapping_str(payload, "effective_from"),
    )


def _log_to_json(log: ExchangeLog) -> dict[str, object]:
    return {
        "timestamp": log.timestamp,
        "actor": log.actor,
        "action": log.action,
        "channel": log.channel,
        "summary": log.summary,
        "related_artifact_ids": list(log.related_artifact_ids),
        "related_event_ids": list(log.related_event_ids),
        "related_run_ids": list(log.related_run_ids),
        "sequence": log.sequence,
        "clock": log.clock,
    }


def _log_from_json(payload: Mapping[str, object]) -> ExchangeLog:
    sequence = payload.get("sequence")
    return ExchangeLog(
        timestamp=_mapping_str(payload, "timestamp"),
        actor=_mapping_str(payload, "actor"),
        action=_mapping_str(payload, "action"),
        channel=_mapping_str(payload, "channel"),
        summary=_mapping_str(payload, "summary"),
        related_artifact_ids=_string_tuple(payload.get("related_artifact_ids")),
        related_event_ids=_string_tuple(payload.get("related_event_ids")),
        related_run_ids=_string_tuple(payload.get("related_run_ids")),
        sequence=sequence if isinstance(sequence, int) else None,
        clock=_mapping_str(payload, "clock") or "wall",  # type: ignore[arg-type]
    )


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_str(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    return value if isinstance(value, str) else ""


def _mapping_bool(mapping: Mapping[str, object], key: str) -> bool:
    value = mapping.get(key)
    return value if isinstance(value, bool) else False


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, str))
