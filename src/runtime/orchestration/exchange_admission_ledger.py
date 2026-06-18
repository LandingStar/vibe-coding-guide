"""Durable local ledger for exact ExchangeArtifact scheduler admissions."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

EXCHANGE_ARTIFACT_ADMISSION_LEDGER_SCHEMA_VERSION = "exchange-artifact-admission-ledger.v1"
DEFAULT_EXCHANGE_ARTIFACT_ADMISSION_LEDGER_RELATIVE_PATH = (
    ".codex/orchestration/exchange-artifact-admissions.json"
)

ExchangeArtifactAdmissionStatus = Literal["admitted", "rejected_duplicate", "failed"]


@dataclass(frozen=True, slots=True)
class ExchangeArtifactAdmissionRecord:
    """One durable record for a stored-artifact scheduler admission attempt."""

    ledger_id: str
    artifact_store_path: Path
    artifact_id: str
    artifact_version: str
    product_type: str
    surface: str
    actor: str
    timestamp: str
    snapshot_path: Path
    event_log_path: Path
    status: ExchangeArtifactAdmissionStatus
    submitted_task_ids: tuple[str, ...] = ()
    dependency_ids: tuple[str, ...] = ()
    submission_event_ids: tuple[str, ...] = ()
    error_summary: str = ""
    duplicate_of: str = ""
    allow_duplicate: bool = False
    schema_version: str = EXCHANGE_ARTIFACT_ADMISSION_LEDGER_SCHEMA_VERSION

    def to_json_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible ledger record."""

        return {
            "schema_version": self.schema_version,
            "ledger_id": self.ledger_id,
            "artifact_store_path": str(self.artifact_store_path),
            "artifact_id": self.artifact_id,
            "artifact_version": self.artifact_version,
            "product_type": self.product_type,
            "surface": self.surface,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "snapshot_path": str(self.snapshot_path),
            "event_log_path": str(self.event_log_path),
            "status": self.status,
            "submitted_task_ids": list(self.submitted_task_ids),
            "dependency_ids": list(self.dependency_ids),
            "submission_event_ids": list(self.submission_event_ids),
            "error_summary": self.error_summary,
            "duplicate_of": self.duplicate_of,
            "allow_duplicate": self.allow_duplicate,
        }


@dataclass(frozen=True, slots=True)
class ExchangeArtifactAdmissionLedgerInspection:
    """Read-only summary over a local admission ledger."""

    ledger_path: Path
    exists: bool
    schema_version: str = EXCHANGE_ARTIFACT_ADMISSION_LEDGER_SCHEMA_VERSION
    records: tuple[ExchangeArtifactAdmissionRecord, ...] = ()
    errors: tuple[str, ...] = ()
    artifact_id_filter: str = ""
    artifact_version_filter: str = ""

    @property
    def record_count(self) -> int:
        """Return the number of records after filtering."""

        return len(self.records)

    @property
    def error_count(self) -> int:
        """Return isolated inspection error count."""

        return len(self.errors)

    @property
    def status_counts(self) -> dict[str, int]:
        """Return counts by ledger status."""

        counts: dict[str, int] = {}
        for record in self.records:
            counts[record.status] = counts.get(record.status, 0) + 1
        return counts

    def to_json_dict(self) -> dict[str, object]:
        """Return compact operator-facing JSON."""

        return {
            "ledger_path": str(self.ledger_path),
            "exists": self.exists,
            "schema_version": self.schema_version,
            "record_count": self.record_count,
            "error_count": self.error_count,
            "status_counts": self.status_counts,
            "artifact_id_filter": self.artifact_id_filter,
            "artifact_version_filter": self.artifact_version_filter,
            "artifact_ids": sorted({record.artifact_id for record in self.records}),
            "records": [record.to_json_dict() for record in self.records],
            "errors": list(self.errors),
            "authority_split": {
                "admission_ledger_authority": "exchange_artifact_admission_ledger",
                "scheduler_state_authority": "scheduler_snapshot",
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }


class JsonExchangeArtifactAdmissionLedger:
    """JSON-backed append-only admission ledger."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(
        self,
        record: ExchangeArtifactAdmissionRecord,
    ) -> ExchangeArtifactAdmissionRecord:
        """Append one admission record, assigning a local id when needed."""

        records = list(self.read_all())
        if record.ledger_id:
            if any(existing.ledger_id == record.ledger_id for existing in records):
                raise ValueError(
                    f"exchange artifact admission ledger id already exists: {record.ledger_id!r}"
                )
            final = record
        else:
            final = replace(record, ledger_id=_next_ledger_id(records))
        records.append(final)
        self._write_records(tuple(records))
        return final

    def read_all(self) -> tuple[ExchangeArtifactAdmissionRecord, ...]:
        """Read all ledger records in append order."""

        if not self.path.exists():
            return ()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"invalid exchange artifact admission ledger JSON at {self.path}: {exc.msg}"
            ) from exc
        if not isinstance(payload, Mapping):
            raise ValueError(
                f"exchange artifact admission ledger {self.path} must contain a JSON object"
            )
        schema_version = payload.get("schema_version")
        if schema_version != EXCHANGE_ARTIFACT_ADMISSION_LEDGER_SCHEMA_VERSION:
            raise ValueError(
                "unsupported exchange artifact admission ledger version "
                f"{schema_version!r}; expected "
                f"{EXCHANGE_ARTIFACT_ADMISSION_LEDGER_SCHEMA_VERSION!r}"
            )
        records_value = payload.get("records", [])
        if not isinstance(records_value, list):
            raise ValueError(
                f"exchange artifact admission ledger {self.path} field 'records' must be a list"
            )

        records: list[ExchangeArtifactAdmissionRecord] = []
        seen_ids: set[str] = set()
        for index, item in enumerate(records_value):
            if not isinstance(item, Mapping):
                raise ValueError(
                    f"exchange artifact admission ledger {self.path} records[{index}] must be an object"
                )
            record = exchange_artifact_admission_record_from_json_dict(item)
            if record.schema_version != EXCHANGE_ARTIFACT_ADMISSION_LEDGER_SCHEMA_VERSION:
                raise ValueError(
                    f"exchange artifact admission ledger {self.path} records[{index}] has "
                    f"unsupported schema_version {record.schema_version!r}; expected "
                    f"{EXCHANGE_ARTIFACT_ADMISSION_LEDGER_SCHEMA_VERSION!r}"
                )
            if not record.ledger_id:
                raise ValueError(
                    f"exchange artifact admission ledger {self.path} records[{index}] "
                    "requires non-empty ledger_id"
                )
            if record.ledger_id in seen_ids:
                raise ValueError(
                    f"exchange artifact admission ledger {self.path} contains duplicate "
                    f"ledger_id {record.ledger_id!r}"
                )
            seen_ids.add(record.ledger_id)
            records.append(record)
        return tuple(records)

    def find_successful_admissions(
        self,
        artifact_id: str,
        artifact_version: str,
    ) -> tuple[ExchangeArtifactAdmissionRecord, ...]:
        """Return previous successful admissions for an exact artifact version."""

        return tuple(
            record
            for record in self.read_all()
            if record.artifact_id == artifact_id
            and record.artifact_version == artifact_version
            and record.status == "admitted"
        )

    def _write_records(self, records: tuple[ExchangeArtifactAdmissionRecord, ...]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": EXCHANGE_ARTIFACT_ADMISSION_LEDGER_SCHEMA_VERSION,
            "records": [record.to_json_dict() for record in records],
        }
        temp_path = self.path.with_name(f"{self.path.name}.tmp")
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        temp_path.replace(self.path)


def default_exchange_artifact_admission_ledger_path(project_root: str | Path) -> Path:
    """Return the conventional local exchange-artifact admission ledger path."""

    return Path(project_root) / DEFAULT_EXCHANGE_ARTIFACT_ADMISSION_LEDGER_RELATIVE_PATH


def inspect_exchange_artifact_admission_ledger(
    path: str | Path,
    *,
    artifact_id: str = "",
    artifact_version: str = "",
) -> ExchangeArtifactAdmissionLedgerInspection:
    """Read a ledger into a non-mutating inspection bundle."""

    ledger_path = Path(path)
    if not ledger_path.exists():
        return ExchangeArtifactAdmissionLedgerInspection(
            ledger_path=ledger_path,
            exists=False,
            artifact_id_filter=artifact_id,
            artifact_version_filter=artifact_version,
        )

    try:
        records = JsonExchangeArtifactAdmissionLedger(ledger_path).read_all()
    except Exception as exc:
        return ExchangeArtifactAdmissionLedgerInspection(
            ledger_path=ledger_path,
            exists=True,
            errors=(str(exc),),
            artifact_id_filter=artifact_id,
            artifact_version_filter=artifact_version,
        )

    filtered = tuple(
        record
        for record in records
        if (not artifact_id or record.artifact_id == artifact_id)
        and (not artifact_version or record.artifact_version == artifact_version)
    )
    return ExchangeArtifactAdmissionLedgerInspection(
        ledger_path=ledger_path,
        exists=True,
        records=filtered,
        artifact_id_filter=artifact_id,
        artifact_version_filter=artifact_version,
    )


def exchange_artifact_admission_record_from_json_dict(
    payload: Mapping[str, object],
) -> ExchangeArtifactAdmissionRecord:
    """Deserialize a ledger record from JSON."""

    status = _mapping_str(payload, "status") or "failed"
    if status not in {"admitted", "rejected_duplicate", "failed"}:
        raise ValueError(f"unsupported exchange artifact admission status {status!r}")
    return ExchangeArtifactAdmissionRecord(
        schema_version=_mapping_str(payload, "schema_version"),
        ledger_id=_mapping_str(payload, "ledger_id"),
        artifact_store_path=Path(_mapping_str(payload, "artifact_store_path")),
        artifact_id=_mapping_str(payload, "artifact_id"),
        artifact_version=_mapping_str(payload, "artifact_version"),
        product_type=_mapping_str(payload, "product_type"),
        surface=_mapping_str(payload, "surface"),
        actor=_mapping_str(payload, "actor"),
        timestamp=_mapping_str(payload, "timestamp"),
        snapshot_path=Path(_mapping_str(payload, "snapshot_path")),
        event_log_path=Path(_mapping_str(payload, "event_log_path")),
        status=status,  # type: ignore[arg-type]
        submitted_task_ids=_string_tuple(payload.get("submitted_task_ids")),
        dependency_ids=_string_tuple(payload.get("dependency_ids")),
        submission_event_ids=_string_tuple(payload.get("submission_event_ids")),
        error_summary=_mapping_str(payload, "error_summary"),
        duplicate_of=_mapping_str(payload, "duplicate_of"),
        allow_duplicate=_mapping_bool(payload, "allow_duplicate"),
    )


def utc_admission_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp for local ledger events."""

    return datetime.now(UTC).isoformat()


def _next_ledger_id(records: list[ExchangeArtifactAdmissionRecord]) -> str:
    return f"exchange-artifact-admission-{len(records) + 1}"


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
