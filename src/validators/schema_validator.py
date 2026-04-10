"""Built-in JSON Schema validator."""

from __future__ import annotations

import jsonschema

from .base import ValidationResult


class SchemaValidator:
    """Validate data against a JSON Schema."""

    def __init__(self, schema: dict) -> None:
        self._schema = schema

    def validate(self, data: dict) -> ValidationResult:
        validator = jsonschema.Draft202012Validator(self._schema)
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.path))
        if not errors:
            return ValidationResult(valid=True)
        return ValidationResult(
            valid=False,
            errors=[e.message for e in errors],
        )
