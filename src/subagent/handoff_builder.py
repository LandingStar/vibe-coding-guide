"""Build a Handoff object from execution context.

Pure function — no I/O.  Outputs conform to ``handoff.schema.json``.
"""

from __future__ import annotations

import uuid


def build(
    envelope: dict,
    delegation: dict,
    contract: dict,
    report: dict,
) -> dict:
    """Assemble a Handoff dict from a completed delegation cycle.

    Parameters
    ----------
    envelope : dict
        The PDP Decision Envelope.
    delegation : dict
        The delegation decision (from ``envelope["delegation_decision"]``).
    contract : dict
        The generated Subagent Contract.
    report : dict
        The Subagent Report returned by the worker.
    """
    handoff_id = f"handoff-{uuid.uuid4().hex[:12]}"

    # Determine roles.
    from_role = "main-ai"
    to_role = "worker-ai"
    if delegation.get("requires_review"):
        to_role = "human-reviewer"

    # Derive reason from envelope context.
    intent = envelope.get("intent_result", {}).get("intent", "unknown")
    reason = (
        f"Delegation for intent '{intent}' completed; "
        f"transferring context to {to_role}."
    )

    # Active scope from contract.
    active_scope = contract.get("scope", "See contract for details.")

    # Authoritative refs from contract, fall back to defaults.
    authoritative_refs = contract.get("required_refs", ["docs/README.md"])

    # Carried constraints from contract out_of_scope.
    carried_constraints = contract.get("out_of_scope", [])

    # Open items from report.
    open_items = report.get("unresolved_items", [])

    # Gate state: if report completed, state is 'applied'; otherwise 'waiting_review'.
    status = report.get("status", "completed")
    if status == "completed":
        gate_state = "applied"
    elif status == "partial":
        gate_state = "waiting_review"
    else:  # blocked
        gate_state = "rejected"

    # Intake requirements.
    intake_requirements = [
        "Re-read authoritative references listed above.",
        "Verify report status and changed artifacts.",
    ]
    if open_items:
        intake_requirements.append("Address unresolved items before proceeding.")

    return {
        "handoff_id": handoff_id,
        "from_role": from_role,
        "to_role": to_role,
        "reason": reason,
        "active_scope": active_scope,
        "authoritative_refs": authoritative_refs,
        "carried_constraints": carried_constraints,
        "open_items": open_items,
        "current_gate_state": gate_state,
        "intake_requirements": intake_requirements,
    }
