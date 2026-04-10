"""Validator backed by a plain Python callable."""

from __future__ import annotations

from typing import Callable

from .base import ValidationResult


class ScriptValidator:
    """Wrap a Python function as a Validator.

    The function signature must be ``(data: dict) -> dict`` and return
    ``{"valid": bool, "errors": [...]}`` (errors are optional when valid).
    """

    def __init__(self, func: Callable[[dict], dict]) -> None:
        self._func = func

    def validate(self, data: dict) -> ValidationResult:
        raw = self._func(data)
        valid = bool(raw.get("valid", False))
        errors = list(raw.get("errors", []))
        warnings = list(raw.get("warnings", []))
        return ValidationResult(valid=valid, errors=errors, warnings=warnings)
