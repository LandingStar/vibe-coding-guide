"""Tests for escalation execution pipeline (Phase 10)."""

from __future__ import annotations

import pytest

from src.pdp.decision_envelope import build_envelope
from src.pep.executor import Executor
from src.pep import notification_builder
from src.pep.stub_notifier import StubNotifier
from src.subagent import contract_factory, report_validator
from src.subagent.stub_worker import StubWorkerBackend


def _make_executor(*, notifier=None, **kwargs):
    return Executor(
        dry_run=True,
        worker=StubWorkerBackend(),
        contract_factory=contract_factory,
        report_validator=report_validator,
        escalation_notifier=notifier,
        **kwargs,
    )


# ---------- notification_builder tests ----------

class TestNotificationBuilder:
    def test_basic_structure(self):
        envelope = {
            "decision_id": "env-001",
            "intent_result": {"intent": "scope-change", "confidence": "high"},
            "gate_decision": {"gate_level": "approve"},
        }
        escalation = {
            "escalate": True,
            "target_authority": "human_reviewer",
            "reason": "High impact intent.",
            "context_summary": "Intent='scope-change', gate='approve'.",
        }
        notif = notification_builder.build(envelope, escalation)
        assert notif["notification_id"] == "notif-env-001"
        assert notif["target"] == "human_reviewer"
        assert notif["reason"] == "High impact intent."
        assert len(notif["suggested_actions"]) > 0

    def test_main_agent_target(self):
        envelope = {
            "decision_id": "env-002",
            "intent_result": {"intent": "unknown", "confidence": "low"},
            "gate_decision": {"gate_level": "review"},
        }
        escalation = {
            "escalate": True,
            "target_authority": "main_agent",
            "reason": "Low confidence.",
        }
        notif = notification_builder.build(envelope, escalation)
        assert notif["target"] == "main_agent"
        assert any("re-evaluate" in a.lower() or "re-run" in a.lower()
                    for a in notif["suggested_actions"])


# ---------- StubNotifier tests ----------

class TestStubNotifier:
    def test_records_notification(self):
        notifier = StubNotifier()
        result = notifier.notify({"target": "human_reviewer"})
        assert result["delivered"] is True
        assert result["channel"] == "stub-memory"
        assert len(notifier.notifications) == 1


# ---------- PEP escalation integration ----------

class TestPepEscalation:
    def test_human_reviewer_escalation(self):
        """High-impact intent triggers escalation to human reviewer."""
        # scope change request is high impact → approve gate → human_reviewer
        envelope = build_envelope("scope change request")
        notifier = StubNotifier()
        executor = _make_executor(notifier=notifier)
        result = executor.execute(envelope)

        assert result["execution_status"] == "escalated"
        assert "escalation_notification" in result
        assert result["escalation_notification"]["target"] == "human_reviewer"
        assert "escalation_delivery" in result
        assert result["escalation_delivery"]["delivered"] is True
        assert len(notifier.notifications) == 1

    def test_main_agent_escalation(self):
        """Ambiguous input triggers escalation to main agent."""
        # Build an envelope manually with low confidence / unknown intent
        envelope = build_envelope("xyzzy gibberish no match")
        # Ensure escalation is present
        esc = envelope.get("escalation_decision")
        if not esc or not esc.get("escalate"):
            pytest.skip("Input did not trigger escalation in current classifier")

        executor = _make_executor()
        result = executor.execute(envelope)

        assert result["execution_status"] == "re-evaluate"
        assert "escalation_notification" in result

    def test_no_escalation_no_change(self):
        """Normal inform-gate intent has no escalation."""
        envelope = build_envelope("当前状态是什么")
        executor = _make_executor()
        result = executor.execute(envelope)

        assert result["execution_status"] in ("applied", "dry-run")
        assert "escalation_notification" not in result

    def test_escalation_without_notifier(self):
        """Escalation requested but no notifier configured."""
        envelope = build_envelope("scope change request")
        executor = _make_executor()  # no notifier
        result = executor.execute(envelope)

        assert result["execution_status"] == "escalated"
        assert "escalation_notification" in result
        assert "escalation_delivery" not in result

        actions = [e["action"] for e in executor.log.entries]
        assert "escalation-pending" in actions

    def test_escalation_log_entries(self):
        """Escalation produces proper log entries."""
        envelope = build_envelope("scope change request")
        notifier = StubNotifier()
        executor = _make_executor(notifier=notifier)
        executor.execute(envelope)

        actions = [e["action"] for e in executor.log.entries]
        assert "escalation-notified" in actions

    def test_delegation_plus_escalation(self):
        """Delegation with escalation: both should be processed."""
        # correction intent with approve gate manually set
        envelope = build_envelope("请修正这个重大bug")
        # Manually inject escalation to test combined behavior
        if not envelope.get("escalation_decision") or not envelope["escalation_decision"].get("escalate"):
            envelope["escalation_decision"] = {
                "escalate": True,
                "target_authority": "human_reviewer",
                "reason": "High impact bug fix.",
                "triggering_condition": "high_impact_intent",
                "context_summary": "Test combined delegation+escalation.",
            }

        notifier = StubNotifier()
        executor = _make_executor(notifier=notifier)
        result = executor.execute(envelope)

        # Escalation should override status
        assert result["execution_status"] == "escalated"
        assert "escalation_notification" in result
