"""Storage helpers for coordination exchange artifacts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from .exchange import ExchangeArtifact, ExchangeLog, validate_exchange_artifact

CoordinationEventKind = Literal[
    "artifact_recorded",
    "artifact_superseded",
    "artifact_consumed",
    "artifact_archived",
    "validation_failed",
]


@dataclass(frozen=True, slots=True)
class ArtifactVersionRecord:
    """Stored version of an exchange artifact."""

    artifact_id: str
    version: str
    artifact: ExchangeArtifact


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
