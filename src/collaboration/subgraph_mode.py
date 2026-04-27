"""Subgraph collaboration mode — isolated sub-process with namespace.

In subgraph mode, a delegated task runs in an isolated namespace
with its own state snapshot. The result is merged back into the
parent context only after validation and review.

Key differences from worker mode:
- Subgraph creates an isolated execution context (namespace)
- State changes are captured in a delta for controlled merge
- Subgraph generates dedicated audit events
- The parent retains full authority; subgraph cannot write back directly
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
class SubgraphContext:
    """Isolated execution context for a subgraph."""

    context_id: str
    namespace: str
    parent_trace_id: str | None
    isolation_level: str  # "full" | "shared-read"
    task_group_id: str | None = None
    child_task_id: str | None = None
    state_snapshot: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def create_context(
    delegation: dict,
    contract: dict,
    *,
    trace_id: str | None = None,
    namespace: str | None = None,
    task_group_id: str | None = None,
    child_task_id: str | None = None,
) -> SubgraphContext:
    """Create a SubgraphContext from delegation decision and contract.

    The context provides an isolated namespace where the worker
    operates without direct access to the parent state.
    """
    ctx_id = f"sg-{uuid.uuid4().hex[:12]}"
    resolved_namespace = namespace or contract.get("contract_id", ctx_id)
    return SubgraphContext(
        context_id=ctx_id,
        namespace=resolved_namespace,
        parent_trace_id=trace_id,
        isolation_level=delegation.get("contract_hints", {}).get(
            "isolation_level", "full",
        ),
        task_group_id=task_group_id,
        child_task_id=child_task_id,
        state_snapshot={
            "scope": contract.get("scope", ""),
            "required_refs": contract.get("required_refs", []),
            "out_of_scope": contract.get("out_of_scope", []),
        },
    )


def execute(
    context: SubgraphContext,
    contract: dict,
    worker: WorkerBackend,
    *,
    audit_logger: AuditLogger | None = None,
    trace_id: str | None = None,
) -> dict:
    """Execute a subgraph: run the worker in isolation, capture delta.

    Returns a result dict with:
    - mode: "subgraph"
    - context: the SubgraphContext
    - report: worker report
    - delta: captured state changes
    - status: "subgraph_completed" or "subgraph_failed"
    """
    effective_trace = trace_id or context.parent_trace_id

    # Audit: subgraph created
    if audit_logger and effective_trace:
        audit_logger.emit(
            "subgraph_created", "pep", effective_trace,
            detail={
                "context_id": context.context_id,
                "namespace": context.namespace,
                "isolation_level": context.isolation_level,
            },
        )

    # Execute via worker (in isolated context)
    try:
        report = worker.execute(contract)
    except Exception as exc:
        if audit_logger and effective_trace:
            audit_logger.emit(
                "subgraph_failed", "pep", effective_trace,
                detail={"context_id": context.context_id, "error": str(exc)},
            )
        return {
            "mode": "subgraph",
            "context": _context_to_dict(context),
            "report": None,
            "delta": None,
            "status": "subgraph_failed",
            "error": str(exc),
        }

    # Capture delta: what the worker changed relative to the snapshot
    delta = _capture_delta(context, report)

    # Audit: subgraph completed
    if audit_logger and effective_trace:
        audit_logger.emit(
            "subgraph_completed", "pep", effective_trace,
            detail={
                "context_id": context.context_id,
                "report_status": report.get("status", "unknown"),
                "delta_keys": list(delta.keys()),
            },
        )

    return {
        "mode": "subgraph",
        "context": _context_to_dict(context),
        "report": report,
        "delta": delta,
        "status": "subgraph_completed",
    }


def merge_result(subgraph_result: dict, parent_state: dict) -> dict:
    """Merge subgraph delta into parent state.

    This is a controlled merge — only explicitly changed keys
    are applied. The parent retains authority over unmentioned keys.
    """
    delta = subgraph_result.get("delta") or {}
    merged = dict(parent_state)
    for key, value in delta.items():
        merged[key] = value
    return merged


def _capture_delta(context: SubgraphContext, report: dict) -> dict:
    """Extract state changes from a worker report.

    The delta captures artifacts changed, assumptions made,
    and unresolved items — the minimum information needed
    for the parent to decide whether to merge.
    """
    return {
        "artifacts_changed": report.get("artifacts_changed", []),
        "assumptions": report.get("assumptions", []),
        "unresolved_items": report.get("unresolved_items", []),
        "report_status": report.get("status", "unknown"),
        "namespace": context.namespace,
    }


def _context_to_dict(context: SubgraphContext) -> dict:
    """Convert SubgraphContext to a plain dict."""
    return {
        "context_id": context.context_id,
        "namespace": context.namespace,
        "parent_trace_id": context.parent_trace_id,
        "isolation_level": context.isolation_level,
        "task_group_id": context.task_group_id,
        "child_task_id": context.child_task_id,
        "state_snapshot": context.state_snapshot,
        "created_at": context.created_at,
    }
