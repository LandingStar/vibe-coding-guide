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
    binding_reference_summary: Mapping[str, object] | None = None
    schema_version: str = EXCHANGE_ARTIFACT_ADMISSION_LEDGER_SCHEMA_VERSION

    def to_json_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible ledger record."""

        payload: dict[str, object] = {
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
        if self.binding_reference_summary:
            payload["binding_reference_summary"] = dict(self.binding_reference_summary)
        return payload


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


def admit_exchange_artifact_version_with_ledger(
    *,
    artifact_store_path: str | Path,
    artifact_id: str,
    version: str,
    snapshot_path: str | Path,
    event_log_path: str | Path,
    admission_ledger_path: str | Path,
    allow_duplicate_admission: bool = False,
    replace_existing: bool = False,
    validate_binding_artifact_refs: bool = False,
    mark_consumed_on_success: bool = False,
    actor: str = "operator",
    surface: str = "runtime:admit_exchange_artifact_version_with_ledger",
    timestamp: str = "",
) -> dict[str, object]:
    """Admit an exact stored scheduler artifact and record the admission ledger.

    This is the shared policy point for CLI and MCP admission. It rejects
    duplicate exact artifact/version admission before scheduler mutation unless
    an explicit duplicate override is provided.
    """

    from .scheduler_submission import admit_exchange_artifact_version_to_scheduler

    store_path = Path(artifact_store_path)
    snapshot = Path(snapshot_path)
    event_log = Path(event_log_path)
    ledger_path = Path(admission_ledger_path)
    ledger = JsonExchangeArtifactAdmissionLedger(ledger_path)
    binding_reference_summary = (
        _build_binding_reference_summary(
            artifact_store_path=store_path,
            artifact_id=artifact_id,
            version=version,
        )
        if validate_binding_artifact_refs
        else {}
    )

    try:
        previous_admissions = ledger.find_successful_admissions(artifact_id, version)
    except Exception as exc:
        return _admission_error_payload(
            error=str(exc),
            artifact_store_path=store_path,
            artifact_id=artifact_id,
            version=version,
            snapshot_path=snapshot,
            event_log_path=event_log,
            admission_ledger_path=ledger_path,
            mark_consumed_on_success=mark_consumed_on_success,
        )

    if previous_admissions and not allow_duplicate_admission:
        duplicate = previous_admissions[-1]
        record = ledger.append(
            ExchangeArtifactAdmissionRecord(
                ledger_id="",
                artifact_store_path=store_path,
                artifact_id=artifact_id,
                artifact_version=version,
                product_type=duplicate.product_type,
                surface=surface,
                actor=actor,
                timestamp=utc_admission_timestamp(),
                snapshot_path=snapshot,
                event_log_path=event_log,
                status="rejected_duplicate",
                error_summary=(
                    "duplicate exact exchange artifact admission rejected; "
                    "set allow_duplicate_admission=true to admit intentionally"
                ),
                duplicate_of=duplicate.ledger_id,
                binding_reference_summary=(
                    binding_reference_summary if binding_reference_summary else None
                ),
            )
        )
        return {
            "ok": False,
            "error": record.error_summary,
            "status": record.status,
            "artifact_store_path": str(store_path),
            "admission_ledger_path": str(ledger_path),
            "admission_ledger_record_id": record.ledger_id,
            "duplicate_of": record.duplicate_of,
            "allow_duplicate": record.allow_duplicate,
            "allow_duplicate_admission": allow_duplicate_admission,
            "artifact_id": artifact_id,
            "version": version,
            "snapshot_path": str(snapshot),
            "event_log_path": str(event_log),
            "scheduler_state_mutated": False,
            "event_log_mutated": False,
            "ran_tasks": False,
            "refreshed_projection": False,
            "binding_reference_summary": binding_reference_summary,
            "consumption_state": {
                "requested": mark_consumed_on_success,
                "consumed": False,
                "reason": "duplicate admission rejected before scheduler mutation",
            },
            "authority_split": _admission_authority_split(
                scheduler_state_mutated=False,
                exchange_store_mutated=False,
            ),
        }

    try:
        if validate_binding_artifact_refs and not bool(
            binding_reference_summary.get("ok")
        ):
            errors = binding_reference_summary.get("errors")
            if isinstance(errors, list) and errors:
                raise ValueError("; ".join(str(error) for error in errors))
            raise ValueError("supervisor storage binding artifact reference validation failed")
        result = admit_exchange_artifact_version_to_scheduler(
            artifact_store_path=store_path,
            artifact_id=artifact_id,
            version=version,
            snapshot_path=snapshot,
            event_log_path=event_log,
            replace_existing=replace_existing,
            timestamp=timestamp,
            validate_binding_artifact_refs=validate_binding_artifact_refs,
        )
    except Exception as exc:
        try:
            ledger.append(
                ExchangeArtifactAdmissionRecord(
                    ledger_id="",
                    artifact_store_path=store_path,
                    artifact_id=artifact_id,
                    artifact_version=version,
                    product_type="",
                    surface=surface,
                    actor=actor,
                    timestamp=utc_admission_timestamp(),
                    snapshot_path=snapshot,
                    event_log_path=event_log,
                    status="failed",
                    error_summary=str(exc),
                    allow_duplicate=allow_duplicate_admission,
                    binding_reference_summary=(
                        binding_reference_summary if binding_reference_summary else None
                    ),
                )
            )
        except Exception:
            pass
        return _admission_error_payload(
            error=str(exc),
            artifact_store_path=store_path,
            artifact_id=artifact_id,
            version=version,
            snapshot_path=snapshot,
            event_log_path=event_log,
            admission_ledger_path=ledger_path,
            allow_duplicate_admission=allow_duplicate_admission,
            binding_reference_summary=binding_reference_summary,
            mark_consumed_on_success=mark_consumed_on_success,
        )

    record = ledger.append(
        ExchangeArtifactAdmissionRecord(
            ledger_id="",
            artifact_store_path=store_path,
            artifact_id=artifact_id,
            artifact_version=version,
            product_type=result.product_type,
            surface=surface,
            actor=actor,
            timestamp=utc_admission_timestamp(),
            snapshot_path=result.snapshot_path,
            event_log_path=result.event_log_path,
            status="admitted",
            submitted_task_ids=tuple(task.task_id for task in result.submitted_tasks),
            dependency_ids=tuple(
                dependency.dependency_id
                for dependency in result.dependencies_added
            ),
            submission_event_ids=result.submission_event_ids,
            allow_duplicate=allow_duplicate_admission,
            binding_reference_summary=(
                binding_reference_summary if binding_reference_summary else None
            ),
        )
    )

    payload = {"ok": True}
    payload.update(result.to_json_dict())
    dependency_ids = [
        dependency.dependency_id
        for dependency in result.dependencies_added
    ]
    payload["admission_ledger_path"] = str(ledger_path)
    payload["admission_ledger_record_id"] = record.ledger_id
    payload["allow_duplicate_admission"] = allow_duplicate_admission
    payload["dependency_ids"] = dependency_ids
    payload["dependencies_added"] = dependency_ids
    payload["binding_reference_summary"] = binding_reference_summary
    consumption_state: dict[str, object] = {
        "requested": mark_consumed_on_success,
        "consumed": False,
    }
    exchange_store_mutated = False
    if mark_consumed_on_success:
        from .exchange_store import mark_exchange_artifact_version_consumed

        consumption = mark_exchange_artifact_version_consumed(
            store_path=store_path,
            artifact_id=artifact_id,
            version=version,
            actor=actor,
            reason=(
                "exact exchange artifact version consumed after successful "
                f"admission ledger record {record.ledger_id}"
            ),
            timestamp=timestamp,
        )
        consumption_state = consumption.to_json_dict()
        consumption_state["requested"] = True
        exchange_store_mutated = bool(consumption_state.get("exchange_store_mutated"))
    payload["consumption_state"] = consumption_state
    payload["authority_split"] = _admission_authority_split(
        scheduler_state_mutated=True,
        exchange_store_mutated=exchange_store_mutated,
    )
    return payload


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
        binding_reference_summary=_mapping_dict(payload, "binding_reference_summary"),
    )


def utc_admission_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp for local ledger events."""

    return datetime.now(UTC).isoformat()


def _admission_error_payload(
    *,
    error: str,
    artifact_store_path: Path,
    artifact_id: str,
    version: str,
    snapshot_path: Path,
    event_log_path: Path,
    admission_ledger_path: Path,
    allow_duplicate_admission: bool = False,
    binding_reference_summary: Mapping[str, object] | None = None,
    mark_consumed_on_success: bool = False,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "ok": False,
        "error": error,
        "artifact_store_path": str(artifact_store_path),
        "artifact_id": artifact_id,
        "version": version,
        "snapshot_path": str(snapshot_path),
        "event_log_path": str(event_log_path),
        "admission_ledger_path": str(admission_ledger_path),
        "allow_duplicate_admission": allow_duplicate_admission,
        "ran_tasks": False,
        "refreshed_projection": False,
        "consumption_state": {
            "requested": mark_consumed_on_success,
            "consumed": False,
            "reason": "admission failed before consumption",
        },
        "authority_split": _admission_authority_split(
            scheduler_state_mutated=False,
            exchange_store_mutated=False,
        ),
    }
    if binding_reference_summary:
        payload["binding_reference_summary"] = dict(binding_reference_summary)
    return payload


def _build_binding_reference_summary(
    *,
    artifact_store_path: Path,
    artifact_id: str,
    version: str,
) -> dict[str, object]:
    """Return compact binding-ref validation data for durable ledger records."""

    from .scheduler_submission import (
        inspect_supervisor_storage_binding_artifact_refs_for_submission,
    )

    inspection = inspect_supervisor_storage_binding_artifact_refs_for_submission(
        artifact_store_path=artifact_store_path,
        artifact_id=artifact_id,
        version=version,
    ).to_json_dict()
    tasks: list[dict[str, object]] = []
    for task in inspection.get("tasks", []):
        if not isinstance(task, Mapping):
            continue
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
        "enabled": True,
        "ok": bool(inspection.get("ok")),
        "source_artifact_id": str(inspection.get("source_artifact_id", artifact_id)),
        "source_artifact_version": str(
            inspection.get("source_artifact_version", version)
        ),
        "submission_product_type": str(inspection.get("submission_product_type", "")),
        "task_count": _int_value(inspection.get("task_count")),
        "binding_ref_count": _int_value(inspection.get("binding_ref_count")),
        "checked_ref_count": _int_value(inspection.get("checked_ref_count")),
        "error_count": _int_value(inspection.get("error_count")),
        "errors": _string_list(inspection.get("errors")),
        "tasks": tasks,
        "raw_evidence_json_read": False,
    }


def _admission_authority_split(
    *,
    scheduler_state_mutated: bool,
    exchange_store_mutated: bool = False,
) -> dict[str, object]:
    return {
        "admission_ledger_authority": "exchange_artifact_admission_ledger",
        "scheduler_state_authority": "scheduler_snapshot",
        "exchange_store_role": "exact-version-coordination-product-source",
        "scheduler_state_mutated": scheduler_state_mutated,
        "exchange_store_mutated": exchange_store_mutated,
        "provider_executed": False,
        "scheduler_projection_refreshed": False,
        "local_work_trajectory_mutated": False,
    }


def _next_ledger_id(records: list[ExchangeArtifactAdmissionRecord]) -> str:
    return f"exchange-artifact-admission-{len(records) + 1}"


def _mapping_str(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    return value if isinstance(value, str) else ""


def _mapping_bool(mapping: Mapping[str, object], key: str) -> bool:
    value = mapping.get(key)
    return value if isinstance(value, bool) else False


def _mapping_dict(mapping: Mapping[str, object], key: str) -> dict[str, object]:
    value = mapping.get(key)
    return dict(value) if isinstance(value, Mapping) else {}


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _string_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [str(item) for item in value if isinstance(item, str)]


def _int_value(value: object) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _compact_ref_list(value: object) -> list[dict[str, str]]:
    if not isinstance(value, (list, tuple)):
        return []
    refs: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        refs.append(
            {
                "ref_kind": str(item.get("ref_kind", "")),
                "ref_id": str(item.get("ref_id", "")),
                "version": str(item.get("version", "")),
                "label": str(item.get("label", "")),
            }
        )
    return refs
