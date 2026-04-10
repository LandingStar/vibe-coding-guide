"""Validate a Subagent Report against the schema.

Implements the ReportValidator protocol defined in src.interfaces.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs" / "specs" / "subagent-report.schema.json"
)
_SCHEMA: dict | None = None


def _load_schema() -> dict:
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return _SCHEMA


def validate(report: dict) -> dict:
    """Validate *report* against ``subagent-report.schema.json``.

    Returns::

        {"valid": True,  "errors": []}
        {"valid": False, "errors": ["...description..."]}
    """
    schema = _load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(report), key=lambda e: list(e.path))
    if not errors:
        return {"valid": True, "errors": []}
    return {
        "valid": False,
        "errors": [e.message for e in errors],
    }
