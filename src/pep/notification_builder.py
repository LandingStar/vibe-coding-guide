"""Build an escalation notification from a decision envelope.

Pure function — no I/O.
"""

from __future__ import annotations


def build(envelope: dict, escalation_decision: dict) -> dict:
    """Assemble a notification dict from escalation context.

    Parameters
    ----------
    envelope : dict
        The PDP Decision Envelope.
    escalation_decision : dict
        The escalation decision (``envelope["escalation_decision"]``).
    """
    target = escalation_decision.get("target_authority", "main_agent")
    reason = escalation_decision.get("reason", "Escalation triggered.")
    context = escalation_decision.get("context_summary", "")

    intent = envelope.get("intent_result", {}).get("intent", "unknown")
    gate_level = envelope.get("gate_decision", {}).get("gate_level", "review")
    envelope_id = envelope.get("decision_id", "unknown")

    suggested_actions: list[str] = []
    if target == "human_reviewer":
        suggested_actions.append("Review the envelope and provide approval or rejection.")
        suggested_actions.append("Check intent classification accuracy.")
    else:
        suggested_actions.append("Re-evaluate intent classification with additional context.")
        suggested_actions.append("Consider re-running PDP with refined input.")

    return {
        "notification_id": f"notif-{envelope_id}",
        "envelope_id": envelope_id,
        "target": target,
        "reason": reason,
        "context": context,
        "intent": intent,
        "gate_level": gate_level,
        "suggested_actions": suggested_actions,
    }
