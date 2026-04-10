"""Validator / Check / Trigger protocols and result types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ValidationResult:
    """Result of a validator invocation."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class CheckResult:
    """Result of a check invocation."""
    passed: bool
    message: str = ""


@dataclass
class TriggerResult:
    """Result of a trigger invocation."""
    handled: bool
    output: dict = field(default_factory=dict)


class Validator(Protocol):
    """Validate data and return a ValidationResult."""

    def validate(self, data: dict) -> ValidationResult: ...


class Check(Protocol):
    """Run a check against context and return a CheckResult."""

    def check(self, context: dict) -> CheckResult: ...


class Trigger(Protocol):
    """Handle an event and return a TriggerResult."""

    def handle(self, event: dict) -> TriggerResult: ...
