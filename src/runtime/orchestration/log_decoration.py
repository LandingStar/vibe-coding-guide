"""Reusable log decoration primitives for runtime/orchestration records."""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Literal, Mapping, Protocol, runtime_checkable

LogDecoratorMode = Literal["append_only", "rewrite_allowed", "validator"]
LogDecorationStatus = Literal["ok", "failed"]


@dataclass(frozen=True, slots=True)
class LogDecorationRecord:
    """Neutral log/event record that decorators can enrich or rewrite."""

    record_id: str
    timestamp: str
    actor: str
    action: str
    channel: str = ""
    message: str = ""
    fields: Mapping[str, object] = field(default_factory=dict)
    decorations: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "channel": self.channel,
            "message": self.message,
            "fields": dict(self.fields),
            "decorations": dict(self.decorations),
        }


@dataclass(frozen=True, slots=True)
class LogDecorationResult:
    """Result emitted by one decorator."""

    decorator_id: str
    mode: LogDecoratorMode
    status: LogDecorationStatus
    record: LogDecorationRecord
    rewrote_record: bool = False
    appended_keys: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    summary: str = ""

    @property
    def ok(self) -> bool:
        return self.status == "ok" and not self.errors

    def to_json_dict(self) -> dict[str, object]:
        return {
            "decorator_id": self.decorator_id,
            "mode": self.mode,
            "status": self.status,
            "rewrote_record": self.rewrote_record,
            "appended_keys": list(self.appended_keys),
            "errors": list(self.errors),
            "summary": self.summary,
        }


@dataclass(frozen=True, slots=True)
class LogDecorationPipelineResult:
    """Final record and evidence for an ordered decoration pipeline."""

    initial_record: LogDecorationRecord
    record: LogDecorationRecord
    results: tuple[LogDecorationResult, ...] = ()

    @property
    def ok(self) -> bool:
        return all(result.ok for result in self.results)

    @property
    def rewrote_record(self) -> bool:
        return any(result.rewrote_record for result in self.results)

    @property
    def errors(self) -> tuple[str, ...]:
        return tuple(error for result in self.results for error in result.errors)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "rewrote_record": self.rewrote_record,
            "error_count": len(self.errors),
            "errors": list(self.errors),
            "initial_record_id": self.initial_record.record_id,
            "record": self.record.to_json_dict(),
            "results": [result.to_json_dict() for result in self.results],
            "authority_split": {
                "persistence_mutated": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
                "provider_executed": False,
                "raw_transcript_persisted": False,
            },
        }


@runtime_checkable
class LogDecorator(Protocol):
    """Protocol for append-only, validation, or controlled rewrite decorators."""

    decorator_id: str
    mode: LogDecoratorMode

    def decorate(self, record: LogDecorationRecord) -> LogDecorationResult: ...


@dataclass(frozen=True, slots=True)
class AppendFieldsLogDecorator:
    """Append stable decoration fields without changing the message."""

    decorator_id: str
    fields: Mapping[str, object]
    mode: LogDecoratorMode = "append_only"

    def decorate(self, record: LogDecorationRecord) -> LogDecorationResult:
        if not self.decorator_id:
            return LogDecorationResult(
                decorator_id="",
                mode=self.mode,
                status="failed",
                record=record,
                errors=("log decorator requires non-empty decorator_id",),
            )
        merged = {**dict(record.decorations), **dict(self.fields)}
        updated = replace(record, decorations=merged)
        return LogDecorationResult(
            decorator_id=self.decorator_id,
            mode=self.mode,
            status="ok",
            record=updated,
            appended_keys=tuple(self.fields.keys()),
            summary=f"appended {len(self.fields)} decoration field(s)",
        )


@dataclass(frozen=True, slots=True)
class RequiredFieldsLogDecorator:
    """Validate required fields on a log decoration record."""

    decorator_id: str
    required_fields: tuple[str, ...] = ("record_id", "timestamp", "actor", "action")
    mode: LogDecoratorMode = "validator"

    def decorate(self, record: LogDecorationRecord) -> LogDecorationResult:
        errors: list[str] = []
        if not self.decorator_id:
            errors.append("log decorator requires non-empty decorator_id")
        for field_name in self.required_fields:
            value = _record_field_value(record, field_name)
            if value in (None, ""):
                errors.append(
                    f"log record {record.record_id!r} requires non-empty field {field_name!r}"
                )
        return LogDecorationResult(
            decorator_id=self.decorator_id,
            mode=self.mode,
            status=("failed" if errors else "ok"),
            record=record,
            errors=tuple(errors),
            summary=(
                f"validated {len(self.required_fields)} required field(s)"
                if not errors
                else "required field validation failed"
            ),
        )


@dataclass(frozen=True, slots=True)
class BoundedTextRewriteLogDecorator:
    """Redact patterns and bound message length with explicit rewrite evidence."""

    decorator_id: str
    redaction_patterns: tuple[str, ...] = ()
    replacement: str = "[redacted]"
    max_message_chars: int = 500
    mode: LogDecoratorMode = "rewrite_allowed"

    def decorate(self, record: LogDecorationRecord) -> LogDecorationResult:
        errors: list[str] = []
        if not self.decorator_id:
            errors.append("log decorator requires non-empty decorator_id")
        if self.max_message_chars < 0:
            errors.append("bounded text rewrite max_message_chars must be >= 0")
        if errors:
            return LogDecorationResult(
                decorator_id=self.decorator_id,
                mode=self.mode,
                status="failed",
                record=record,
                errors=tuple(errors),
                summary="text rewrite validation failed",
            )

        message = record.message
        rewritten = message
        for pattern in self.redaction_patterns:
            rewritten = re.sub(pattern, self.replacement, rewritten)
        if len(rewritten) > self.max_message_chars:
            rewritten = rewritten[: self.max_message_chars].rstrip()
            if self.max_message_chars >= 3:
                rewritten = rewritten[: self.max_message_chars - 3].rstrip() + "..."
        rewrote = rewritten != message
        updated = replace(record, message=rewritten) if rewrote else record
        return LogDecorationResult(
            decorator_id=self.decorator_id,
            mode=self.mode,
            status="ok",
            record=updated,
            rewrote_record=rewrote,
            summary=("rewrote message text" if rewrote else "message unchanged"),
        )


class LogDecorationPipeline:
    """Ordered log decorator pipeline."""

    def __init__(self, decorators: tuple[LogDecorator, ...] = ()) -> None:
        self._decorators = decorators

    @property
    def decorators(self) -> tuple[LogDecorator, ...]:
        return self._decorators

    def run(self, record: LogDecorationRecord) -> LogDecorationPipelineResult:
        current = record
        results: list[LogDecorationResult] = []
        for decorator in self._decorators:
            result = decorator.decorate(current)
            results.append(result)
            current = result.record
        return LogDecorationPipelineResult(
            initial_record=record,
            record=current,
            results=tuple(results),
        )


def _record_field_value(record: LogDecorationRecord, field_name: str) -> object:
    if hasattr(record, field_name):
        return getattr(record, field_name)
    if field_name in record.fields:
        return record.fields[field_name]
    return record.decorations.get(field_name)
