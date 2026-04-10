"""Handoff collaboration mode — explicit control transfer.

In handoff mode, the supervisor explicitly transfers control to a
specialized agent. The receiving agent becomes the new owner of
the scope. Unlike worker mode (fire-and-collect), handoff is
"fire-and-transfer".

Key differences from worker mode:
- Handoff always requires review (default)
- Handoff generates a persistent Handoff object
- Handoff emits dedicated audit events
- The receiving agent is expected to run independently
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.audit.audit_logger import AuditLogger
    from src.interfaces import WorkerBackend


@dataclass
class HandoffRequest:
    """A request to transfer control to another agent."""

    request_id: str
    from_role: str
    to_role: str
    reason: str
    scope: str
    constraints: list[str] = field(default_factory=list)
    requires_review: bool = True


def prepare(delegation: dict, contract: dict) -> HandoffRequest:
    """Create a HandoffRequest from delegation decision and contract.

    Handoff mode is triggered when delegation_decision has
    ``allow_handoff=True`` or ``mode="handoff"``.
    """
    return HandoffRequest(
        request_id=f"hreq-{uuid.uuid4().hex[:12]}",
        from_role="main-ai",
        to_role=delegation.get("contract_hints", {}).get("to_role", "specialist-ai"),
        reason=delegation.get("rationale", "Handoff requested"),
        scope=contract.get("scope", ""),
        constraints=contract.get("out_of_scope", []),
        requires_review=delegation.get("requires_review", True),
    )


def execute(
    request: HandoffRequest,
    contract: dict,
    worker: WorkerBackend,
    *,
    audit_logger: AuditLogger | None = None,
    trace_id: str | None = None,
    handoff_dir: str | None = None,
) -> dict:
    """Execute a handoff: run the worker, then build a Handoff object.

    Returns a result dict with:
    - mode: "handoff"
    - handoff_request: the request
    - handoff: the generated Handoff object
    - report: worker report
    - status: "handoff_completed" or "handoff_failed"
    """
    from src.subagent import handoff_builder

    # Audit: handoff initiated
    if audit_logger and trace_id:
        audit_logger.emit(
            "handoff_initiated", "pep", trace_id,
            detail={
                "request_id": request.request_id,
                "from_role": request.from_role,
                "to_role": request.to_role,
                "scope": request.scope,
            },
        )

    # Execute via worker (the receiving agent processes the contract)
    try:
        report = worker.execute(contract)
    except Exception as exc:
        if audit_logger and trace_id:
            audit_logger.emit(
                "handoff_failed", "pep", trace_id,
                detail={"request_id": request.request_id, "error": str(exc)},
            )
        return {
            "mode": "handoff",
            "handoff_request": _request_to_dict(request),
            "report": None,
            "handoff": None,
            "status": "handoff_failed",
            "error": str(exc),
        }

    # Build the Handoff object
    handoff = _build_handoff(request, contract, report)

    # Audit: handoff completed
    if audit_logger and trace_id:
        audit_logger.emit(
            "handoff_completed", "pep", trace_id,
            detail={
                "request_id": request.request_id,
                "handoff_id": handoff["handoff_id"],
                "report_status": report.get("status", "unknown"),
            },
        )

    return {
        "mode": "handoff",
        "handoff_request": _request_to_dict(request),
        "report": report,
        "handoff": handoff,
        "status": "handoff_completed",
    }


def _build_handoff(request: HandoffRequest, contract: dict, report: dict) -> dict:
    """Build a Handoff object conforming to handoff.schema.json."""
    return {
        "handoff_id": f"handoff-{uuid.uuid4().hex[:12]}",
        "from_role": request.from_role,
        "to_role": request.to_role,
        "reason": request.reason,
        "active_scope": request.scope or contract.get("scope", ""),
        "authoritative_refs": contract.get("required_refs", ["AGENTS.md"]) or ["AGENTS.md"],
        "carried_constraints": request.constraints,
        "open_items": report.get("unresolved_items", []),
        "current_gate_state": "waiting_review" if request.requires_review else "proposed",
        "intake_requirements": [
            f"Review handoff from {request.from_role}",
            "Re-read authoritative_refs before proceeding",
        ],
    }


def _request_to_dict(request: HandoffRequest) -> dict:
    """Convert HandoffRequest to a plain dict."""
    return {
        "request_id": request.request_id,
        "from_role": request.from_role,
        "to_role": request.to_role,
        "reason": request.reason,
        "scope": request.scope,
        "constraints": request.constraints,
        "requires_review": request.requires_review,
    }
