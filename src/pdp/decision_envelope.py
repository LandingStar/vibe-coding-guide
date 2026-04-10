"""PDP Decision Envelope assembler."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from . import intent_classifier, gate_resolver, delegation_resolver
from . import escalation_resolver, precedence_resolver

if TYPE_CHECKING:
    from ..audit.audit_logger import AuditLogger
    from ..audit.trace_context import TraceContext
    from ..pack.override_resolver import RuleConfig


def build_envelope(
    input_text: str,
    *,
    active_rules: list[dict] | None = None,
    rule_config: RuleConfig | None = None,
    audit_logger: AuditLogger | None = None,
    trace_ctx: TraceContext | None = None,
) -> dict:
    """Build a full PDP Decision Envelope from raw input text.

    Args:
        input_text: The user input to classify.
        active_rules: Optional list of rule dicts (each with "rule_id" and
            "layer") for precedence resolution.
        rule_config: Optional RuleConfig from pack loader. When None,
            uses hardcoded platform defaults.
        audit_logger: Optional AuditLogger for governance tracing.
        trace_ctx: Optional TraceContext for correlation. If audit_logger
            is provided but trace_ctx is None, a new trace is created.

    Returns a dict conforming to pdp-decision-envelope.schema.json.
    """
    # Setup tracing
    trace_id: str | None = None
    if audit_logger:
        if trace_ctx is None:
            from ..audit.trace_context import new_trace
            trace_ctx = new_trace()
        trace_id = trace_ctx.trace_id
        audit_logger.emit(
            "input_received", "pdp", trace_id,
            detail={"input_summary": _summarize(input_text)},
            parent_trace_id=trace_ctx.parent_trace_id,
        )

    intent_result = intent_classifier.classify(input_text, rule_config=rule_config)
    if audit_logger and trace_id:
        audit_logger.emit(
            "intent_classified", "pdp", trace_id,
            detail={"intent": intent_result.get("intent"), "confidence": intent_result.get("confidence")},
        )

    gate_decision = gate_resolver.resolve(intent_result, rule_config=rule_config)
    if audit_logger and trace_id:
        audit_logger.emit(
            "gate_resolved", "pdp", trace_id,
            detail={"gate_level": gate_decision.get("gate_level")},
        )

    envelope: dict = {
        "decision_id": f"pdp-{uuid.uuid4().hex[:12]}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_summary": _summarize(input_text),
        "intent_result": intent_result,
        "gate_decision": gate_decision,
        "rationale": (
            f"Classified as '{intent_result['intent']}' "
            f"(confidence={intent_result['confidence']}), "
            f"gate='{gate_decision['gate_level']}'."
        ),
    }

    if trace_id:
        envelope["trace_id"] = trace_id

    # Optional: delegation decision
    deleg = delegation_resolver.resolve(intent_result, gate_decision, rule_config=rule_config)
    if deleg is not None:
        envelope["delegation_decision"] = deleg
        if audit_logger and trace_id:
            audit_logger.emit(
                "delegation_decided", "pdp", trace_id,
                detail={"delegate": deleg.get("delegate")},
            )

    # Optional: escalation decision
    esc = escalation_resolver.resolve(intent_result, gate_decision, rule_config=rule_config)
    if esc is not None:
        envelope["escalation_decision"] = esc
        if audit_logger and trace_id:
            audit_logger.emit(
                "escalation_decided", "pdp", trace_id,
                detail={"escalate": esc.get("escalate")},
            )

    # Optional: precedence resolution
    if active_rules:
        prec = precedence_resolver.resolve(active_rules, rule_config=rule_config)
        if prec is not None:
            envelope["precedence_resolution"] = prec
            if audit_logger and trace_id:
                audit_logger.emit(
                    "precedence_resolved", "pdp", trace_id,
                    detail={"winning_rule": prec.get("winning_rule")},
                )

    return envelope


def _summarize(text: str, max_len: int = 200) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."
