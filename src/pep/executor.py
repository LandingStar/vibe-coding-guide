"""PEP executor with delegation, handoff, escalation, and review state machine."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from .action_log import ActionLog
from src.review.state_machine import (
    APPLY,
    APPROVE,
    SUBMIT_FOR_REVIEW,
    ReviewStateMachine,
)

if TYPE_CHECKING:
    from src.audit.audit_logger import AuditLogger
    from src.interfaces import (
        ContractFactory,
        EscalationNotifier,
        HandoffValidator,
        ReportValidator,
        WorkerBackend,
    )
    from src.pep.writeback_engine import WritebackEngine
    from src.validators.registry import ValidatorRegistry
    from src.workers.registry import WorkerRegistry


class Executor:
    """Execute actions permitted by a PDP Decision Envelope.

    In dry-run mode (default), no real side effects occur;
    all actions are recorded to the action log.

    When *worker*, *contract_factory*, and *report_validator* are
    provided, delegation envelopes are routed through the full
    contract → worker → report → validate pipeline.

    *handoff_dir* controls where handoff JSON files are persisted.
    Defaults to ``.codex/handoffs/`` relative to the project root.
    """

    def __init__(
        self,
        dry_run: bool = True,
        *,
        worker: WorkerBackend | None = None,
        worker_registry: WorkerRegistry | None = None,
        contract_factory: ContractFactory | None = None,
        report_validator: ReportValidator | None = None,
        handoff_validator: HandoffValidator | None = None,
        handoff_dir: str | Path | None = None,
        escalation_notifier: EscalationNotifier | None = None,
        writeback_engine: WritebackEngine | None = None,
        audit_logger: AuditLogger | None = None,
        validator_registry: ValidatorRegistry | None = None,
    ) -> None:
        self.dry_run = dry_run
        self.log = ActionLog()
        self._contract_factory = contract_factory
        self._report_validator = report_validator
        if handoff_validator is not None:
            self._handoff_validator = handoff_validator
        else:
            from src.subagent import handoff_validator as default_handoff_validator

            self._handoff_validator = default_handoff_validator
        self._handoff_dir = Path(handoff_dir) if handoff_dir else None
        self._escalation_notifier = escalation_notifier
        self._writeback_engine = writeback_engine
        self._audit_logger = audit_logger
        self._validator_registry = validator_registry

        # Worker resolution: registry takes precedence over single worker.
        # If only a single worker is provided, wrap it in a registry as "default".
        if worker_registry is not None:
            self._worker_registry = worker_registry
            # Also register the single worker as fallback if provided
            if worker is not None and "default" not in worker_registry:
                worker_registry.register("default", worker)
        elif worker is not None:
            from src.workers.registry import WorkerRegistry as _WR
            self._worker_registry = _WR()
            self._worker_registry.register("default", worker)
        else:
            self._worker_registry = None

        # Keep _worker for backward compat in checks
        self._worker = worker

    def execute(self, envelope: dict) -> dict:
        """Process a decision envelope and return an execution result."""
        envelope_id = envelope.get("decision_id", "unknown")
        gate = envelope.get("gate_decision", {})
        gate_level = gate.get("gate_level", "review")
        trace_id = envelope.get("trace_id")

        if self._audit_logger and trace_id:
            self._audit_logger.emit(
                "execution_started", "pep", trace_id,
                detail={"envelope_id": envelope_id, "gate_level": gate_level},
            )

        # Create a review state machine for this envelope.
        rsm = ReviewStateMachine(object_id=envelope_id, gate_level=gate_level)

        # Check for delegation first.
        delegation = envelope.get("delegation_decision")
        if delegation and delegation.get("delegate"):
            result = self._execute_delegation(envelope, envelope_id, delegation, rsm)
        elif gate_level == "inform":
            result = self._execute_inform(envelope, envelope_id, rsm)
        elif gate_level == "review":
            result = self._execute_review(envelope, envelope_id, rsm)
        elif gate_level == "approve":
            result = self._execute_approve(envelope, envelope_id, rsm)
        else:
            self.log.record("error", f"Unknown gate level: {gate_level}",
                            envelope_id)
            result = self._result(envelope_id, "error",
                                  f"Unknown gate level: {gate_level}",
                                  trace_id=trace_id)

        # Check for escalation after main routing.
        escalation = envelope.get("escalation_decision")
        if escalation and escalation.get("escalate"):
            result = self._apply_escalation(envelope, envelope_id, escalation, result)

        # Attach review state machine output.
        result["review_state"] = rsm.current_state
        result["review_history"] = rsm.history
        result["_rsm"] = rsm  # retained for reviewer feedback via orchestrator

        # Trigger write-back when review state is "applied".
        if self._writeback_engine and rsm.current_state == "applied":
            self._execute_writeback(envelope, result, envelope_id)

        return result

    def apply_review_feedback(
        self,
        envelope: dict,
        result: dict,
        feedback: str,
        *,
        reason: str = "",
    ) -> dict:
        """Apply reviewer feedback to a previously executed result.

        *result* must contain the ``_rsm`` key from a prior ``execute()``
        call that returned ``review_state == "waiting_review"``.
        """
        from src.pep.review_orchestrator import ReviewOrchestrator

        rsm = result.get("_rsm")
        if rsm is None:
            return {"error": "No review state machine in result."}

        orchestrator = ReviewOrchestrator(notifier=self._escalation_notifier)
        fb_result = orchestrator.submit_feedback(rsm, feedback, reason=reason)

        # Audit: review_feedback event
        trace_id = envelope.get("trace_id")
        if self._audit_logger and trace_id:
            self._audit_logger.emit(
                "review_feedback", "pep", trace_id,
                detail={"feedback": feedback, "new_state": fb_result["review_state"]},
            )

        # Update the execution result with new review state.
        result["review_state"] = fb_result["review_state"]
        result["review_history"] = fb_result["review_history"]
        if "notification" in fb_result:
            result["feedback_notification"] = fb_result["notification"]

        # Trigger write-back if now applied.
        if self._writeback_engine and fb_result["review_state"] == "applied":
            envelope_id = result.get("envelope_id", "unknown")
            self._execute_writeback(envelope, result, envelope_id)

        return result

    def _execute_inform(self, envelope: dict, envelope_id: str, rsm: ReviewStateMachine) -> dict:
        action = "apply" if not self.dry_run else "dry-run-apply"
        trace_id = envelope.get("trace_id")
        detail = (
            f"Gate=inform, fast path. "
            f"Intent='{envelope['intent_result']['intent']}'. "
            f"Would apply directly."
        )
        self.log.record(action, detail, envelope_id)
        # Inform fast-path: proposed → applied
        rsm.transition(APPLY, reason="inform fast-path")
        return self._result(envelope_id, "applied" if not self.dry_run else "dry-run",
                            detail, trace_id=trace_id)

    def _execute_review(self, envelope: dict, envelope_id: str, rsm: ReviewStateMachine) -> dict:
        trace_id = envelope.get("trace_id")
        detail = (
            f"Gate=review, entering waiting_review. "
            f"Intent='{envelope['intent_result']['intent']}'. "
            f"Awaiting reviewer decision."
        )
        self.log.record("queue-for-review", detail, envelope_id)
        rsm.transition(SUBMIT_FOR_REVIEW, reason="review gate")
        return self._result(envelope_id, "waiting_review", detail, trace_id=trace_id)

    def _execute_approve(self, envelope: dict, envelope_id: str, rsm: ReviewStateMachine) -> dict:
        trace_id = envelope.get("trace_id")
        detail = (
            f"Gate=approve, entering waiting_review. "
            f"Intent='{envelope['intent_result']['intent']}'. "
            f"Requires explicit approval before execution."
        )
        self.log.record("queue-for-approval", detail, envelope_id)
        rsm.transition(SUBMIT_FOR_REVIEW, reason="approve gate")
        return self._result(envelope_id, "waiting_review", detail, trace_id=trace_id)

    @staticmethod
    def _result(envelope_id: str, status: str, detail: str, *, trace_id: str | None = None, delegation_mode: str | None = None) -> dict:
        r: dict = {
            "envelope_id": envelope_id,
            "execution_status": status,
            "detail": detail,
        }
        if trace_id is not None:
            r["trace_id"] = trace_id
        if delegation_mode is not None:
            r["delegation_mode"] = delegation_mode
        return r

    # ---- worker resolution ----

    def _resolve_worker(
        self, delegation: dict, contract: dict, trace_id: str | None,
        envelope_id: str,
    ) -> WorkerBackend | None:
        """Resolve a worker from the registry based on delegation/contract hints.

        Resolution order:
        1. contract["worker_type"] (if present)
        2. delegation["worker_type"] (if present)
        3. "default"
        Returns None if no match found (caller should handle fallback).
        """
        if self._worker_registry is None:
            return None

        # Determine requested worker type
        requested = (
            contract.get("worker_type")
            or delegation.get("worker_type")
            or delegation.get("contract_hints", {}).get("worker_type")
        )
        if not requested:
            requested = "default"

        # Try exact match first
        if requested in self._worker_registry:
            worker = self._worker_registry.get(requested)
            if self._audit_logger and trace_id:
                self._audit_logger.emit(
                    "worker_selected", "pep", trace_id,
                    detail={
                        "worker_type": requested,
                        "source": "registry",
                        "available_types": self._worker_registry.list_types(),
                    },
                )
            return worker

        # Fallback to "default"
        if requested != "default" and "default" in self._worker_registry:
            if self._audit_logger and trace_id:
                self._audit_logger.emit(
                    "worker_fallback", "pep", trace_id,
                    detail={
                        "requested_type": requested,
                        "fallback_type": "default",
                        "available_types": self._worker_registry.list_types(),
                    },
                )
            self.log.record(
                "worker-fallback",
                f"Worker type '{requested}' not found, falling back to 'default'.",
                envelope_id,
            )
            return self._worker_registry.get("default")

        # Nothing available
        return None

    # ---- delegation pipeline ----

    def _execute_delegation(
        self, envelope: dict, envelope_id: str, delegation: dict, rsm: ReviewStateMachine,
    ) -> dict:
        """Route delegation through contract → worker → report → validate.

        Dispatches to mode-specific executors based on delegation['mode'].
        """
        trace_id = envelope.get("trace_id")

        if not self._contract_factory or (not self._worker and not self._worker_registry):
            detail = (
                "Delegation requested but worker/contract_factory not configured. "
                "Falling back to queue-for-review."
            )
            self.log.record("delegation-skipped", detail, envelope_id)
            rsm.transition(SUBMIT_FOR_REVIEW, reason="delegation fallback to review")
            return self._result(envelope_id, "waiting_review", detail, trace_id=trace_id)

        # 1. Build contract
        contract = self._contract_factory.build(delegation)
        self.log.record(
            "contract-created",
            f"Contract {contract.get('contract_id')} generated.",
            envelope_id,
        )

        # Audit: contract_generated event
        if self._audit_logger and trace_id:
            self._audit_logger.emit(
                "contract_generated", "pep", trace_id,
                detail={"contract_id": contract.get("contract_id"), "mode": delegation.get("mode", "supervisor-worker")},
            )

        # Dispatch by collaboration mode
        mode = delegation.get("mode", "supervisor-worker")

        if mode == "handoff":
            return self._execute_handoff_mode(
                envelope, envelope_id, delegation, contract, rsm, trace_id,
            )
        elif mode == "subgraph":
            return self._execute_subgraph_mode(
                envelope, envelope_id, delegation, contract, rsm, trace_id,
            )
        else:
            # Default: supervisor-worker
            return self._execute_worker_mode(
                envelope, envelope_id, delegation, contract, rsm, trace_id,
            )

    # -- Mode executors -------------------------------------------------------

    def _execute_worker_mode(
        self, envelope: dict, envelope_id: str, delegation: dict,
        contract: dict, rsm: ReviewStateMachine, trace_id: str | None,
    ) -> dict:
        """Supervisor-worker: direct worker execution with optional handoff."""
        # Resolve worker from registry (dynamic selection)
        worker = self._resolve_worker(delegation, contract, trace_id, envelope_id)
        if worker is None:
            # Legacy fallback: use directly injected worker
            worker = self._worker
        if worker is None:
            detail = "No worker available for delegation. Falling back to queue-for-review."
            self.log.record("delegation-skipped", detail, envelope_id)
            rsm.transition(SUBMIT_FOR_REVIEW, reason="no worker available")
            return self._result(envelope_id, "waiting_review", detail, trace_id=trace_id)

        # Execute via worker backend
        report = worker.execute(contract)
        self.log.record(
            "worker-executed",
            f"Worker returned report {report.get('report_id')} "
            f"with status={report.get('status')}.",
            envelope_id,
        )

        # Audit: subagent_report_received event
        if self._audit_logger and trace_id:
            self._audit_logger.emit(
                "subagent_report_received", "pep", trace_id,
                detail={"report_id": report.get("report_id"), "status": report.get("status"), "mode": "supervisor-worker"},
            )

        # Validate report (if validator provided)
        validation: dict | None = None
        if self._report_validator:
            validation = self._report_validator.validate(report)
            self.log.record(
                "report-validated",
                f"Validation result: valid={validation.get('valid')}.",
                envelope_id,
            )

        # Run pack validators on report (if registry provided)
        pack_validations: list[dict] = []
        if self._validator_registry:
            for name in self._validator_registry.list_validators():
                v = self._validator_registry.get_validator(name)
                if v is not None:
                    vr = v.validate(report)
                    pack_validations.append({
                        "name": name,
                        "valid": vr.valid,
                        "errors": vr.errors,
                        "warnings": vr.warnings,
                    })
                    self.log.record(
                        "pack-validator",
                        f"Pack validator '{name}': valid={vr.valid}.",
                        envelope_id,
                    )

        result = self._result(
            envelope_id,
            "delegated",
            f"Delegation completed via contract {contract.get('contract_id')}.",
            trace_id=trace_id,
            delegation_mode="supervisor-worker",
        )
        result["contract"] = contract
        result["report"] = report
        if validation is not None:
            result["validation"] = validation
        if pack_validations:
            result["pack_validations"] = pack_validations

        # Drive review state machine based on report status.
        rsm.transition(SUBMIT_FOR_REVIEW, reason="delegation submitted")
        if report.get("status") == "completed":
            rsm.transition(APPROVE, reason="delegation report completed")
            rsm.transition(APPLY, reason="auto-apply after successful delegation")

        # Build and persist handoff if allow_handoff is set.
        if delegation.get("allow_handoff"):
            from src.subagent import handoff_builder

            handoff = handoff_builder.build(envelope, delegation, contract, report)
            result["handoff"] = handoff

            if not self.dry_run and self._handoff_dir:
                self._persist_handoff(handoff, envelope_id)
            else:
                self.log.record(
                    "handoff-built",
                    f"Handoff {handoff['handoff_id']} built (dry-run, not persisted).",
                    envelope_id,
                )

        return result

    def _execute_handoff_mode(
        self, envelope: dict, envelope_id: str, delegation: dict,
        contract: dict, rsm: ReviewStateMachine, trace_id: str | None,
    ) -> dict:
        """Handoff mode: explicit control transfer with mandatory review."""
        from src.collaboration.handoff_mode import prepare, execute as handoff_execute

        # Resolve worker from registry
        worker = self._resolve_worker(delegation, contract, trace_id, envelope_id) or self._worker

        request = prepare(delegation, contract)
        handoff_result = handoff_execute(
            request, contract, worker,
            audit_logger=self._audit_logger,
            trace_id=trace_id,
            handoff_dir=self._handoff_dir if not self.dry_run else None,
        )

        # Audit: subagent_report_received event
        if self._audit_logger and trace_id:
            self._audit_logger.emit(
                "subagent_report_received", "pep", trace_id,
                detail={"report_id": handoff_result.get("report", {}).get("report_id"), "mode": "handoff"},
            )

        handoff = handoff_result.get("handoff")
        handoff_validation: dict | None = None
        if handoff is not None and self._handoff_validator is not None:
            handoff_validation = self._handoff_validator.validate(
                handoff,
                context={
                    "mode": "handoff",
                    "requires_review": delegation.get("requires_review", True),
                    "delegation": delegation,
                    "contract": contract,
                },
            )
        elif handoff is None:
            handoff_validation = {
                "valid": False,
                "errors": ["handoff execution did not produce a handoff object"],
            }

        if handoff_validation is not None and not handoff_validation.get("valid", False):
            self.log.record(
                "handoff-validation-failed",
                "Handoff validation failed; routing to review without persisting handoff.",
                envelope_id,
            )
            if self._audit_logger and trace_id:
                self._audit_logger.emit(
                    "handoff_validation_failed", "pep", trace_id,
                    detail={
                        "handoff_id": handoff.get("handoff_id") if handoff else None,
                        "errors": handoff_validation.get("errors", []),
                    },
                )

            result = self._result(
                envelope_id,
                "waiting_review",
                f"Handoff validation failed for contract {contract.get('contract_id')}.",
                trace_id=trace_id,
                delegation_mode="handoff",
            )
            result["contract"] = contract
            result["report"] = handoff_result.get("report", {})
            result["handoff_candidate"] = handoff
            result["handoff_validation"] = handoff_validation
            result["mode"] = "handoff"

            rsm.transition(SUBMIT_FOR_REVIEW, reason="handoff validation failed")
            return result

        if handoff_validation is not None:
            self.log.record(
                "handoff-validated",
                f"Handoff {handoff.get('handoff_id')} passed validation.",
                envelope_id,
            )
            if self._audit_logger and trace_id:
                self._audit_logger.emit(
                    "handoff_validated", "pep", trace_id,
                    detail={"handoff_id": handoff.get("handoff_id")},
                )

        result = self._result(
            envelope_id,
            "delegated",
            f"Handoff completed via contract {contract.get('contract_id')}.",
            trace_id=trace_id,
            delegation_mode="handoff",
        )
        result["contract"] = contract
        result["report"] = handoff_result.get("report", {})
        result["handoff"] = handoff
        if handoff_validation is not None:
            result["handoff_validation"] = handoff_validation
        result["mode"] = "handoff"

        # Handoff always requires review
        rsm.transition(SUBMIT_FOR_REVIEW, reason="handoff requires review")

        if not self.dry_run and self._handoff_dir and result.get("handoff"):
            self._persist_handoff(result["handoff"], envelope_id)

        return result

    def _execute_subgraph_mode(
        self, envelope: dict, envelope_id: str, delegation: dict,
        contract: dict, rsm: ReviewStateMachine, trace_id: str | None,
    ) -> dict:
        """Subgraph mode: isolated sub-process with namespace."""
        from src.collaboration.subgraph_mode import (
            create_context,
            execute as subgraph_execute,
        )

        context = create_context(delegation, contract, trace_id=trace_id)

        # Resolve worker from registry
        worker = self._resolve_worker(delegation, contract, trace_id, envelope_id) or self._worker

        sg_result = subgraph_execute(
            context, contract, worker,
            audit_logger=self._audit_logger,
            trace_id=trace_id,
        )

        # Audit: subagent_report_received event
        if self._audit_logger and trace_id:
            self._audit_logger.emit(
                "subagent_report_received", "pep", trace_id,
                detail={"report_id": sg_result.get("report", {}).get("report_id"), "mode": "subgraph"},
            )

        result = self._result(
            envelope_id,
            "delegated",
            f"Subgraph completed via contract {contract.get('contract_id')}.",
            trace_id=trace_id,
            delegation_mode="subgraph",
        )
        result["contract"] = contract
        result["report"] = sg_result.get("report", {})
        result["subgraph_context"] = sg_result.get("context")
        result["delta"] = sg_result.get("delta")
        result["mode"] = "subgraph"

        # Subgraph always requires review before merge
        rsm.transition(SUBMIT_FOR_REVIEW, reason="subgraph requires review before merge")

        return result

    def _persist_handoff(self, handoff: dict, envelope_id: str) -> None:
        """Write handoff JSON to the handoff directory."""
        assert self._handoff_dir is not None
        self._handoff_dir.mkdir(parents=True, exist_ok=True)
        path = self._handoff_dir / f"{handoff['handoff_id']}.json"
        path.write_text(json.dumps(handoff, indent=2, ensure_ascii=False), encoding="utf-8")
        self.log.record(
            "handoff-persisted",
            f"Handoff {handoff['handoff_id']} written to {path}.",
            envelope_id,
        )

    # ---- escalation pipeline ----

    def _apply_escalation(
        self,
        envelope: dict,
        envelope_id: str,
        escalation: dict,
        base_result: dict,
    ) -> dict:
        """Augment *base_result* with escalation handling."""
        from .notification_builder import build as build_notification

        target = escalation.get("target_authority", "main_agent")
        notification = build_notification(envelope, escalation)
        base_result["escalation_notification"] = notification

        if target == "human_reviewer":
            if self._escalation_notifier:
                delivery = self._escalation_notifier.notify(notification)
                base_result["escalation_delivery"] = delivery
                self.log.record(
                    "escalation-notified",
                    f"Human reviewer notified via {delivery.get('channel')}.",
                    envelope_id,
                )
            else:
                self.log.record(
                    "escalation-pending",
                    "Human reviewer escalation requested but no notifier configured.",
                    envelope_id,
                )
            base_result["execution_status"] = "escalated"
        else:
            # target == "main_agent"
            self.log.record(
                "escalation-re-evaluate",
                f"Escalation to main_agent: {escalation.get('reason', '')}",
                envelope_id,
            )
            base_result["execution_status"] = "re-evaluate"

        return base_result

    # ---- writeback pipeline ----

    def _execute_writeback(
        self, envelope: dict, result: dict, envelope_id: str,
    ) -> None:
        """Plan and execute write-back when review state is applied."""
        assert self._writeback_engine is not None
        trace_id = envelope.get("trace_id")

        # Run pack checks before writeback (if registry provided).
        if self._validator_registry:
            check_context = {"envelope": envelope, "result": result}
            for name in self._validator_registry.list_checks():
                c = self._validator_registry.get_check(name)
                if c is not None:
                    cr = c.check(check_context)
                    self.log.record(
                        "pack-check",
                        f"Pack check '{name}': passed={cr.passed}, {cr.message}",
                        envelope_id,
                    )
                    if not cr.passed:
                        result["writeback_blocked_by"] = name
                        result["writeback_block_message"] = cr.message

                        # Audit: writeback_blocked_by_check event
                        if self._audit_logger and trace_id:
                            self._audit_logger.emit(
                                "writeback_blocked_by_check", "writeback", trace_id,
                                detail={"check_name": name, "message": cr.message},
                            )
                        return

        plans = self._writeback_engine.plan(envelope, result)
        result["writeback_plans"] = [
            {"target_path": p.target_path, "operation": p.operation}
            for p in plans
        ]

        if not plans:
            return

        wb_results = self._writeback_engine.execute_all(
            plans, dry_run=self.dry_run,
            audit_logger=self._audit_logger, trace_id=trace_id,
        )
        result["writeback_results"] = [
            {"path": r.path, "success": r.success, "detail": r.detail}
            for r in wb_results
        ]

        for r in wb_results:
            action = "writeback-dry-run" if self.dry_run else "writeback-executed"
            self.log.record(action, r.detail, envelope_id)

        # Audit: writeback_completed event
        if self._audit_logger and trace_id:
            self._audit_logger.emit(
                "writeback_completed", "writeback", trace_id,
                detail={"plans_count": len(plans), "success_count": sum(1 for r in wb_results if r.success)},
            )
