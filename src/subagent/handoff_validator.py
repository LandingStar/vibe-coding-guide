"""Validate a Handoff object against schema plus platform invariants.

Implements the HandoffValidator protocol defined in src.interfaces.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "specs"
    / "handoff.schema.json"
)
_SCHEMA: dict | None = None


def _load_schema() -> dict:
    global _SCHEMA
    if _SCHEMA is None:
        _SCHEMA = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    return _SCHEMA


def _semantic_errors(handoff: dict, context: dict | None) -> list[str]:
    errors: list[str] = []

    active_scope = handoff.get("active_scope")
    if isinstance(active_scope, str) and not active_scope.strip():
        errors.append("active_scope must not be blank")

    authoritative_refs = handoff.get("authoritative_refs", [])
    if any(not isinstance(ref, str) or not ref.strip() for ref in authoritative_refs):
        errors.append("authoritative_refs must not contain blank entries")

    intake_requirements = handoff.get("intake_requirements", [])
    if any(
        not isinstance(requirement, str) or not requirement.strip()
        for requirement in intake_requirements
    ):
        errors.append("intake_requirements must not contain blank entries")

    if context:
        if context.get("mode") == "handoff" and context.get("requires_review", True):
            gate_state = handoff.get("current_gate_state")
            if gate_state == "proposed":
                errors.append(
                    "handoff mode with requires_review=True must not use current_gate_state='proposed'"
                )

    return errors


def validate(handoff: dict, context: dict | None = None) -> dict:
    """Validate *handoff* against schema and runtime invariants.

    Returns::

        {"valid": True,  "errors": []}
        {"valid": False, "errors": ["...description..."]}
    """
    schema = _load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    schema_errors = sorted(validator.iter_errors(handoff), key=lambda e: list(e.path))

    errors = [e.message for e in schema_errors]
    errors.extend(_semantic_errors(handoff, context))

    if not errors:
        return {"valid": True, "errors": []}
    return {"valid": False, "errors": errors}
