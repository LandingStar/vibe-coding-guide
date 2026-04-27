"""PEP executor with delegation, handoff, escalation, and review state machine."""

from __future__ import annotations

import json
import uuid
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING

from .action_log import ActionLog
from src.interfaces import (
    ChildExecutionRecord,
    GroupTerminalOutcome,
    GroupedReviewOutcome,
    MergeBarrierOutcome,
    ParallelChildTask,
    TaskGroup,
)
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
        if "grouped_review_outcome" in result:
            result["grouped_review_state"] = rsm.current_state

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
        if "grouped_review_outcome" in result:
            result["grouped_review_state"] = fb_result["review_state"]
            if self._audit_logger and trace_id:
                grouped_review = result.get("grouped_review_outcome") or {}
                self._audit_logger.emit(
                    "grouped_review_state_changed", "pep", trace_id,
                    detail={
                        "task_group_id": grouped_review.get("task_group_id"),
                        "feedback": feedback,
                        "grouped_review_state": fb_result["review_state"],
                    },
                )
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

        hints = delegation.get("contract_hints", {})
        parallel_children = hints.get("parallel_children")
        task_group_id = hints.get("task_group_id")
        child_task_id = hints.get("child_task_id")
        namespace = hints.get("namespace")
        task_group: TaskGroup | None = None
        child: ParallelChildTask | None = None

        if isinstance(parallel_children, list) and parallel_children:
            task_group = self._prepare_parallel_subgraph_task_group(
                envelope,
                parallel_children,
                task_group_id=task_group_id,
            )

        if task_group is None and task_group_id and child_task_id:
            resolved_namespace = namespace or f"{task_group_id}/{child_task_id}"
            child = ParallelChildTask(
                child_task_id=child_task_id,
                contract=contract,
                namespace=resolved_namespace,
                allowed_artifacts=list(contract.get("allowed_artifacts") or []),
                required_refs=list(contract.get("required_refs") or []),
            )
            task_group = TaskGroup(
                task_group_id=task_group_id,
                parent_envelope_id=envelope_id,
                parent_trace_id=trace_id,
                children=[child],
            )

        if task_group is not None:
            preflight = self.preflight_subgraph_task_group(task_group)
            if not preflight["valid"]:
                detail = (
                    f"Subgraph preflight failed for contract {contract.get('contract_id')}."
                )
                self.log.record("subgraph-preflight-failed", detail, envelope_id)
                result = self._result(
                    envelope_id,
                    "waiting_review",
                    detail,
                    trace_id=trace_id,
                    delegation_mode="subgraph",
                )
                result["mode"] = "subgraph"
                result["preflight"] = preflight
                result["task_group"] = self._task_group_to_dict(task_group)
                rsm.transition(SUBMIT_FOR_REVIEW, reason="subgraph preflight failed")
                return result

            child_contexts: list[dict] = []
            child_deltas: list[dict] = []
            child_record_dicts: list[dict] = []
            child_records: list[ChildExecutionRecord] = []

            for child in task_group.children:
                child_hints = dict(hints)
                child_hints.pop("parallel_children", None)
                child_hints["task_group_id"] = task_group.task_group_id
                child_hints["child_task_id"] = child.child_task_id
                child_hints["namespace"] = child.namespace
                child_delegation = dict(delegation)
                child_delegation["contract_hints"] = child_hints

                context = create_context(
                    child_delegation,
                    child.contract,
                    trace_id=trace_id,
                    namespace=child.namespace,
                    task_group_id=task_group.task_group_id,
                    child_task_id=child.child_task_id,
                )

                worker = (
                    self._resolve_worker(child_delegation, child.contract, trace_id, envelope_id)
                    or self._worker
                )
                if worker is None:
                    detail = "No worker available for subgraph batch delegation. Falling back to queue-for-review."
                    self.log.record("delegation-skipped", detail, envelope_id)
                    rsm.transition(SUBMIT_FOR_REVIEW, reason="no worker available")
                    return self._result(envelope_id, "waiting_review", detail, trace_id=trace_id)

                sg_result = subgraph_execute(
                    context,
                    child.contract,
                    worker,
                    audit_logger=self._audit_logger,
                    trace_id=trace_id,
                )

                if self._audit_logger and trace_id:
                    self._audit_logger.emit(
                        "subagent_report_received", "pep", trace_id,
                        detail={
                            "report_id": sg_result.get("report", {}).get("report_id"),
                            "mode": "subgraph",
                            "child_task_id": child.child_task_id,
                        },
                    )

                child_report = sg_result.get("report")
                if not isinstance(child_report, dict):
                    child_report = {
                        "status": "blocked",
                        "changed_artifacts": [],
                        "unresolved_items": [sg_result.get("error", "subgraph execution failed")],
                    }
                else:
                    child_report = self._normalize_subgraph_child_report(
                        child_report,
                        child_task_id=child.child_task_id,
                        delegation=child_delegation,
                        contract=child.contract,
                        envelope_id=envelope_id,
                        trace_id=trace_id,
                    )

                child_record = self.build_child_execution_record(
                    task_group,
                    child,
                    child_report,
                    trace_id=trace_id,
                )
                child_records.append(child_record)
                child_record_dicts.append(self._child_execution_record_to_dict(child_record))
                child_contexts.append(sg_result.get("context") or {})
                child_deltas.append(sg_result.get("delta") or {})

            group_terminal = self.build_group_terminal_outcome(task_group, child_records)

            result = self._result(
                envelope_id,
                "delegated",
                f"Subgraph completed via task group {task_group.task_group_id}.",
                trace_id=trace_id,
                delegation_mode="subgraph",
            )
            result["contract"] = contract
            result["report"] = {}
            result["mode"] = "subgraph"
            result["task_group"] = self._task_group_to_dict(task_group)
            result["preflight"] = preflight
            result["child_execution_records"] = child_record_dicts
            result["child_execution_record"] = child_record_dicts[0] if len(child_record_dicts) == 1 else None
            result["subgraph_contexts"] = child_contexts
            result["deltas"] = child_deltas

            if group_terminal is not None:
                result["group_terminal_outcome"] = self._group_terminal_to_dict(group_terminal)
            else:
                merge_barrier = self.classify_merge_barrier_outcome(
                    task_group,
                    child_records,
                    overlap_decisions=preflight.get("overlap_decisions"),
                )
                grouped_review = self.build_grouped_review_outcome(
                    task_group,
                    child_records,
                    merge_barrier,
                )
                result["merge_barrier_outcome"] = self._merge_barrier_to_dict(merge_barrier)
                result["grouped_review_outcome"] = self._grouped_review_to_dict(grouped_review)

            if len(child_contexts) == 1:
                result["subgraph_context"] = child_contexts[0]
            if len(child_deltas) == 1:
                result["delta"] = child_deltas[0]

            if self._audit_logger and trace_id:
                if group_terminal is not None:
                    self._audit_logger.emit(
                        "group_terminal_prepared", "pep", trace_id,
                        detail=self._group_terminal_audit_detail(group_terminal),
                    )
                else:
                    self._audit_logger.emit(
                        "merge_barrier_classified", "pep", trace_id,
                        detail={
                            "task_group_id": merge_barrier.task_group_id,
                            "conflict_classification": merge_barrier.conflict_classification,
                            "review_outcome": merge_barrier.review_outcome,
                            "review_driver": merge_barrier.review_driver,
                            "child_count": len(task_group.children),
                        },
                    )
                    self._audit_logger.emit(
                        "grouped_review_prepared", "pep", trace_id,
                        detail={
                            "task_group_id": grouped_review.task_group_id,
                            "outcome": grouped_review.outcome,
                            "review_driver": grouped_review.review_driver,
                            "child_count": len(grouped_review.child_reviews),
                            "unresolved_count": len(grouped_review.unresolved_items),
                        },
                    )

            rsm.transition(SUBMIT_FOR_REVIEW, reason="subgraph requires review before merge")
            return result

        context = create_context(
            delegation,
            contract,
            trace_id=trace_id,
            namespace=namespace,
            task_group_id=task_group_id,
            child_task_id=child_task_id,
        )

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

        if task_group is not None and child is not None:
            child_report = sg_result.get("report")
            if isinstance(child_report, dict):
                child_report = self._normalize_subgraph_child_report(
                    child_report,
                    child_task_id=child.child_task_id,
                    delegation=delegation,
                    contract=child.contract,
                    envelope_id=envelope_id,
                    trace_id=trace_id,
                )
            elif not isinstance(child_report, dict):
                child_report = {
                    "status": "blocked",
                    "changed_artifacts": [],
                    "unresolved_items": [sg_result.get("error", "subgraph execution failed")],
                }

            child.namespace = context.namespace
            child_record = self.build_child_execution_record(
                task_group,
                child,
                child_report,
                trace_id=trace_id,
            )
            child_record_dict = self._child_execution_record_to_dict(child_record)
            result["task_group"] = self._task_group_to_dict(task_group)
            result["child_execution_record"] = child_record_dict
            result["child_execution_records"] = [child_record_dict]
            group_terminal = self.build_group_terminal_outcome(task_group, [child_record])

            if group_terminal is not None:
                result["group_terminal_outcome"] = self._group_terminal_to_dict(group_terminal)
            else:
                merge_barrier = self.classify_merge_barrier_outcome(task_group, [child_record])
                grouped_review = self.build_grouped_review_outcome(
                    task_group,
                    [child_record],
                    merge_barrier,
                )
                result["merge_barrier_outcome"] = self._merge_barrier_to_dict(merge_barrier)
                result["grouped_review_outcome"] = self._grouped_review_to_dict(grouped_review)

            if self._audit_logger and trace_id:
                if group_terminal is not None:
                    self._audit_logger.emit(
                        "group_terminal_prepared", "pep", trace_id,
                        detail=self._group_terminal_audit_detail(group_terminal),
                    )
                else:
                    self._audit_logger.emit(
                        "merge_barrier_classified", "pep", trace_id,
                        detail={
                            "task_group_id": merge_barrier.task_group_id,
                            "conflict_classification": merge_barrier.conflict_classification,
                            "review_outcome": merge_barrier.review_outcome,
                            "child_count": len(task_group.children),
                        },
                    )
                    self._audit_logger.emit(
                        "grouped_review_prepared", "pep", trace_id,
                        detail={
                            "task_group_id": grouped_review.task_group_id,
                            "outcome": grouped_review.outcome,
                            "child_count": len(grouped_review.child_reviews),
                            "unresolved_count": len(grouped_review.unresolved_items),
                        },
                    )

        # Subgraph always requires review before merge
        rsm.transition(SUBMIT_FOR_REVIEW, reason="subgraph requires review before merge")

        return result

    def prepare_subgraph_task_group(
        self,
        envelope: dict,
        child_contracts: list[dict],
        *,
        merge_policy: str = "conflict-classification",
        task_group_id: str | None = None,
    ) -> TaskGroup:
        """Build a parent-managed task group for future subgraph fan-out."""
        resolved_task_group_id = task_group_id or f"tg-{uuid.uuid4().hex[:12]}"
        children: list[ParallelChildTask] = []

        for index, contract in enumerate(child_contracts, start=1):
            child_task_id = f"child-{index:02d}"
            children.append(ParallelChildTask(
                child_task_id=child_task_id,
                contract=contract,
                namespace=f"{resolved_task_group_id}/{child_task_id}",
                allowed_artifacts=list(contract.get("allowed_artifacts") or []),
                required_refs=list(contract.get("required_refs") or []),
            ))

        return TaskGroup(
            task_group_id=resolved_task_group_id,
            parent_envelope_id=envelope.get("decision_id", "unknown"),
            parent_trace_id=envelope.get("trace_id"),
            children=children,
            merge_policy=merge_policy,
        )

    def _prepare_parallel_subgraph_task_group(
        self,
        envelope: dict,
        parallel_children: list[object],
        *,
        task_group_id: str | None = None,
    ) -> TaskGroup:
        """Build a task group from parent-provided child batch hints."""
        child_contracts: list[dict] = []
        for entry in parallel_children:
            if isinstance(entry, dict) and isinstance(entry.get("contract"), dict):
                child_contracts.append(entry["contract"])
            elif isinstance(entry, dict):
                child_contracts.append(entry)
            else:
                child_contracts.append({})

        task_group = self.prepare_subgraph_task_group(
            envelope,
            child_contracts,
            task_group_id=task_group_id,
        )

        for child, entry in zip(task_group.children, parallel_children):
            if not isinstance(entry, dict):
                continue
            override_child_task_id = entry.get("child_task_id")
            if isinstance(override_child_task_id, str) and override_child_task_id:
                child.child_task_id = override_child_task_id
            override_namespace = entry.get("namespace")
            child.namespace = (
                override_namespace
                if isinstance(override_namespace, str) and override_namespace
                else f"{task_group.task_group_id}/{child.child_task_id}"
            )
            if "allowed_artifacts" in entry and isinstance(entry.get("allowed_artifacts"), list):
                child.allowed_artifacts = [str(item) for item in entry["allowed_artifacts"]]
            if "required_refs" in entry and isinstance(entry.get("required_refs"), list):
                child.required_refs = [str(item) for item in entry["required_refs"]]
            shared_review_zone_id = entry.get("shared_review_zone_id")
            if isinstance(shared_review_zone_id, str):
                child.shared_review_zone_id = shared_review_zone_id.strip()

        return task_group

    def preflight_subgraph_task_group(self, task_group: TaskGroup) -> dict:
        """Validate namespace and write-set boundaries before fan-out dispatch."""
        errors: list[str] = []
        normalized_boundaries: dict[str, list[str]] = {}
        overlap_decisions: list[dict[str, str]] = []
        seen_child_ids: set[str] = set()
        seen_namespaces: set[str] = set()
        children_by_id: dict[str, ParallelChildTask] = {}

        for child in task_group.children:
            children_by_id[child.child_task_id] = child
            expected_namespace = f"{task_group.task_group_id}/{child.child_task_id}"
            if child.child_task_id in seen_child_ids:
                errors.append(f"duplicate child_task_id: {child.child_task_id}")
            else:
                seen_child_ids.add(child.child_task_id)

            if child.namespace in seen_namespaces:
                errors.append(f"duplicate namespace: {child.namespace}")
            else:
                seen_namespaces.add(child.namespace)

            if child.namespace != expected_namespace:
                errors.append(
                    f"child {child.child_task_id} namespace must equal {expected_namespace}")

            contract = child.contract if isinstance(child.contract, dict) else {}
            if not contract.get("contract_id"):
                errors.append(f"child {child.child_task_id} missing contract.contract_id")
            if contract.get("mode") != "subgraph":
                errors.append(f"child {child.child_task_id} contract.mode must be 'subgraph'")

            required_refs = child.required_refs or list(contract.get("required_refs") or [])
            if not required_refs:
                errors.append(f"child {child.child_task_id} required_refs must not be empty")

            acceptance = contract.get("acceptance") or []
            if not acceptance:
                errors.append(f"child {child.child_task_id} acceptance must not be empty")

            isolation_level = contract.get("contract_hints", {}).get("isolation_level")
            if isolation_level == "per-thread":
                errors.append(
                    f"child {child.child_task_id} requests unsupported per-thread persistence")

            normalized: list[str] = []
            for raw_path in child.allowed_artifacts:
                normalized_path = self._normalize_contract_path(raw_path)
                if normalized_path is None:
                    errors.append(
                        f"child {child.child_task_id} has unsafe allowed_artifacts path: {raw_path}")
                    continue
                normalized.append(normalized_path)
            normalized_boundaries[child.child_task_id] = normalized

        child_ids = list(normalized_boundaries)
        for index, left_child_id in enumerate(child_ids):
            left_paths = normalized_boundaries[left_child_id]
            for right_child_id in child_ids[index + 1:]:
                right_paths = normalized_boundaries[right_child_id]
                for left_path in left_paths:
                    for right_path in right_paths:
                        if self._paths_overlap(left_path, right_path):
                            left_child = children_by_id[left_child_id]
                            right_child = children_by_id[right_child_id]
                            shared_review_zone_id = self._shared_review_zone_for_overlap(
                                left_child,
                                right_child,
                                left_path,
                                right_path,
                            )
                            if shared_review_zone_id:
                                overlap_decisions.append({
                                    "left_child_id": left_child_id,
                                    "right_child_id": right_child_id,
                                    "left_path": left_path,
                                    "right_path": right_path,
                                    "decision": "shared_review_zone_allowed",
                                    "shared_review_zone_id": shared_review_zone_id,
                                    "reason": "same-artifact overlap allowed by shared-review zone",
                                })
                                continue

                            overlap_decisions.append({
                                "left_child_id": left_child_id,
                                "right_child_id": right_child_id,
                                "left_path": left_path,
                                "right_path": right_path,
                                "decision": "blocked_overlap",
                                "shared_review_zone_id": "",
                                "reason": "overlap is outside shared-review zone exception",
                            })
                            errors.append(
                                "allowed_artifacts overlap between "
                                f"{left_child_id} ({left_path}) and {right_child_id} ({right_path})"
                            )

        return {
            "valid": not errors,
            "errors": errors,
            "normalized_boundaries": normalized_boundaries,
            "overlap_decisions": overlap_decisions,
        }

    @staticmethod
    def _shared_review_zone_for_overlap(
        left_child: ParallelChildTask,
        right_child: ParallelChildTask,
        left_path: str,
        right_path: str,
    ) -> str:
        """Return a shared-review zone id for an allowed same-artifact overlap."""
        left_zone = left_child.shared_review_zone_id.strip()
        right_zone = right_child.shared_review_zone_id.strip()
        if not left_zone or left_zone != right_zone:
            return ""
        if left_path != right_path:
            return ""
        return left_zone

    @staticmethod
    def build_child_execution_record(
        task_group: TaskGroup,
        child: ParallelChildTask,
        report: dict,
        *,
        trace_id: str | None = None,
        started_at: str = "",
        finished_at: str = "",
    ) -> ChildExecutionRecord:
        """Build execution evidence for a single child result."""
        return ChildExecutionRecord(
            child_task_id=child.child_task_id,
            task_group_id=task_group.task_group_id,
            trace_id=trace_id,
            namespace=child.namespace,
            status=report.get("status", "unknown") if isinstance(report, dict) else "unknown",
            report=report if isinstance(report, dict) else {},
            started_at=started_at,
            finished_at=finished_at,
        )

    def _normalize_subgraph_child_report(
        self,
        report: dict,
        *,
        child_task_id: str,
        delegation: dict,
        contract: dict,
        envelope_id: str,
        trace_id: str | None,
    ) -> dict:
        """Validate child handoff evidence before it can trigger a terminal bundle."""
        normalized_report = dict(report)
        handoff = normalized_report.get("handoff")
        if not isinstance(handoff, dict):
            return normalized_report

        handoff_validation = self._handoff_validator.validate(
            handoff,
            context={
                "mode": "subgraph",
                "requires_review": delegation.get("requires_review", True),
                "delegation": delegation,
                "contract": contract,
            },
        )
        handoff_id = handoff.get("handoff_id") if isinstance(handoff.get("handoff_id"), str) else None

        if handoff_validation.get("valid", False):
            self.log.record(
                "child-handoff-validated",
                f"Child {child_task_id} handoff {handoff_id or '<unknown>'} passed validation.",
                envelope_id,
            )
            if self._audit_logger and trace_id:
                self._audit_logger.emit(
                    "handoff_validated", "pep", trace_id,
                    detail={
                        "handoff_id": handoff_id,
                        "child_task_id": child_task_id,
                    },
                )
            return normalized_report

        self.log.record(
            "child-handoff-validation-failed",
            f"Child {child_task_id} handoff validation failed; downgrading child report to blocked.",
            envelope_id,
        )
        if self._audit_logger and trace_id:
            self._audit_logger.emit(
                "handoff_validation_failed", "pep", trace_id,
                detail={
                    "handoff_id": handoff_id,
                    "child_task_id": child_task_id,
                    "errors": handoff_validation.get("errors", []),
                },
            )

        normalized_report.pop("handoff", None)
        normalized_report["status"] = "blocked"
        unresolved_items = [str(item) for item in (normalized_report.get("unresolved_items") or [])]
        failure_message = f"child {child_task_id} handoff validation failed"
        if failure_message not in unresolved_items:
            unresolved_items.append(failure_message)
        normalized_report["unresolved_items"] = unresolved_items
        return normalized_report

    def classify_merge_barrier_outcome(
        self,
        task_group: TaskGroup,
        child_records: list[ChildExecutionRecord],
        *,
        overlap_decisions: list[dict] | None = None,
    ) -> MergeBarrierOutcome:
        """Classify the barrier result for a completed child group."""
        child_statuses = {
            record.child_task_id: record.status
            for record in child_records
        }

        blocked_children = [
            record.child_task_id
            for record in child_records
            if record.status in {"blocked", "cancelled"}
        ]
        if blocked_children:
            return MergeBarrierOutcome(
                task_group_id=task_group.task_group_id,
                child_statuses=child_statuses,
                conflict_classification="blocked",
                review_outcome="blocked",
                blocked_reason=(
                    "terminal blocked child results: "
                    + ", ".join(blocked_children)
                ),
            )

        artifact_owners: dict[str, str] = {}
        merged_artifacts: list[str] = []
        for record in child_records:
            changed_artifacts = record.report.get("changed_artifacts") or []
            for raw_path in changed_artifacts:
                normalized_path = self._normalize_contract_path(raw_path)
                if normalized_path is None:
                    return MergeBarrierOutcome(
                        task_group_id=task_group.task_group_id,
                        child_statuses=child_statuses,
                        conflict_classification="blocked",
                        review_outcome="blocked",
                        blocked_reason=(
                            f"child {record.child_task_id} produced unsafe changed_artifacts path: "
                            f"{raw_path}"
                        ),
                    )

                for existing_path, owner in artifact_owners.items():
                    if owner == record.child_task_id:
                        continue
                    if self._paths_overlap(existing_path, normalized_path):
                        return MergeBarrierOutcome(
                            task_group_id=task_group.task_group_id,
                            child_statuses=child_statuses,
                            conflict_classification="review_required",
                            review_outcome="review_required",
                            review_driver=self._resolve_review_driver(
                                existing_path,
                                normalized_path,
                                overlap_decisions,
                            )["review_driver"],
                            shared_review_zone_ids=self._resolve_review_driver(
                                existing_path,
                                normalized_path,
                                overlap_decisions,
                            )["shared_review_zone_ids"],
                            merged_delta={
                                "changed_artifacts": merged_artifacts + [normalized_path],
                            },
                            blocked_reason=(
                                f"changed_artifacts overlap between {owner} ({existing_path}) and "
                                f"{record.child_task_id} ({normalized_path})"
                            ),
                        )

                artifact_owners[normalized_path] = record.child_task_id
                if normalized_path not in merged_artifacts:
                    merged_artifacts.append(normalized_path)

        return MergeBarrierOutcome(
            task_group_id=task_group.task_group_id,
            child_statuses=child_statuses,
            conflict_classification="no_conflict",
            review_outcome="all_clear",
            review_driver="",
            shared_review_zone_ids=[],
            merged_delta={"changed_artifacts": merged_artifacts},
        )

    def build_grouped_review_outcome(
        self,
        task_group: TaskGroup,
        child_records: list[ChildExecutionRecord],
        merge_barrier: MergeBarrierOutcome,
    ) -> GroupedReviewOutcome:
        """Build a grouped review surface from child execution evidence."""
        child_reviews: dict[str, dict] = {}
        changed_artifacts: list[str] = []
        unresolved_items: list[str] = []
        assumptions: list[str] = []

        for record in child_records:
            report = record.report if isinstance(record.report, dict) else {}
            child_changed_artifacts: list[str] = []
            for raw_path in report.get("changed_artifacts") or []:
                normalized_path = self._normalize_contract_path(raw_path)
                artifact_path = normalized_path or str(raw_path)
                child_changed_artifacts.append(artifact_path)
                if artifact_path not in changed_artifacts:
                    changed_artifacts.append(artifact_path)

            child_unresolved = [str(item) for item in (report.get("unresolved_items") or [])]
            for item in child_unresolved:
                if item not in unresolved_items:
                    unresolved_items.append(item)

            child_assumptions = [str(item) for item in (report.get("assumptions") or [])]
            for item in child_assumptions:
                if item not in assumptions:
                    assumptions.append(item)

            child_reviews[record.child_task_id] = {
                "status": record.status,
                "changed_artifacts": child_changed_artifacts,
                "unresolved_items": child_unresolved,
                "assumptions": child_assumptions,
            }

        merged_delta_artifacts = merge_barrier.merged_delta.get("changed_artifacts") or []
        if isinstance(merged_delta_artifacts, list) and merged_delta_artifacts:
            changed_artifacts = []
            for item in merged_delta_artifacts:
                normalized_item = self._normalize_contract_path(item)
                artifact_path = normalized_item or str(item)
                if artifact_path not in changed_artifacts:
                    changed_artifacts.append(artifact_path)

        return GroupedReviewOutcome(
            task_group_id=task_group.task_group_id,
            outcome=merge_barrier.review_outcome,
            review_driver=merge_barrier.review_driver,
            shared_review_zone_ids=list(merge_barrier.shared_review_zone_ids),
            child_reviews=child_reviews,
            changed_artifacts=changed_artifacts,
            unresolved_items=unresolved_items,
            assumptions=assumptions,
            blocked_reason=merge_barrier.blocked_reason,
        )

    def build_group_terminal_outcome(
        self,
        task_group: TaskGroup,
        child_records: list[ChildExecutionRecord],
    ) -> GroupTerminalOutcome | None:
        """Build a terminal bundle when child results request handoff or escalation."""
        child_required_refs = {
            child.child_task_id: list(child.required_refs)
            for child in task_group.children
        }

        escalation_source_child_ids: list[str] = []
        escalation_trigger_evidence: list[dict] = []
        handoff_source_child_ids: list[str] = []
        handoff_trigger_evidence: list[dict] = []
        authoritative_refs: list[str] = []
        open_items: list[str] = []
        handoff_gate_state = ""

        for record in child_records:
            report = record.report if isinstance(record.report, dict) else {}
            handoff = report.get("handoff")
            if isinstance(handoff, dict) and isinstance(handoff.get("handoff_id"), str):
                normalized_handoff_id = handoff["handoff_id"].strip()
                if normalized_handoff_id:
                    handoff_source_child_ids.append(record.child_task_id)
                    handoff_trigger_evidence.append({
                        "child_task_id": record.child_task_id,
                        "type": "handoff",
                        "value": normalized_handoff_id,
                    })

                    for required_ref in child_required_refs.get(record.child_task_id, []):
                        if required_ref not in authoritative_refs:
                            authoritative_refs.append(required_ref)
                    for required_ref in handoff.get("authoritative_refs") or []:
                        normalized_ref = str(required_ref)
                        if normalized_ref and normalized_ref not in authoritative_refs:
                            authoritative_refs.append(normalized_ref)

                    for item in handoff.get("open_items") or report.get("unresolved_items") or []:
                        normalized_item = str(item)
                        if normalized_item and normalized_item not in open_items:
                            open_items.append(normalized_item)

                    current_gate_state = handoff.get("current_gate_state")
                    if (
                        not handoff_gate_state
                        and isinstance(current_gate_state, str)
                        and current_gate_state.strip()
                    ):
                        handoff_gate_state = current_gate_state.strip()

            escalation_recommendation = report.get("escalation_recommendation")
            if not isinstance(escalation_recommendation, str):
                continue

            normalized_recommendation = escalation_recommendation.strip()
            if not normalized_recommendation or normalized_recommendation == "none":
                continue

            escalation_source_child_ids.append(record.child_task_id)
            escalation_trigger_evidence.append({
                "child_task_id": record.child_task_id,
                "type": "escalation_recommendation",
                "value": normalized_recommendation,
            })

            for required_ref in child_required_refs.get(record.child_task_id, []):
                if required_ref not in authoritative_refs:
                    authoritative_refs.append(required_ref)

            for item in report.get("unresolved_items") or []:
                normalized_item = str(item)
                if normalized_item and normalized_item not in open_items:
                    open_items.append(normalized_item)

        if escalation_source_child_ids:
            return GroupTerminalOutcome(
                task_group_id=task_group.task_group_id,
                terminal_kind="escalation",
                source_child_ids=escalation_source_child_ids,
                trigger_evidence=escalation_trigger_evidence,
                suppressed_surfaces=[
                    "merge_barrier",
                    "grouped_review",
                    "grouped_child_writeback",
                ],
                authoritative_refs=authoritative_refs,
                open_items=open_items,
                current_gate_state="waiting_review",
                blocked_reason=(
                    "group terminal escalation requested by "
                    + ", ".join(escalation_source_child_ids)
                ),
            )

        if handoff_source_child_ids:
            return GroupTerminalOutcome(
                task_group_id=task_group.task_group_id,
                terminal_kind="handoff",
                source_child_ids=handoff_source_child_ids,
                trigger_evidence=handoff_trigger_evidence,
                suppressed_surfaces=[
                    "merge_barrier",
                    "grouped_review",
                    "grouped_child_writeback",
                ],
                authoritative_refs=authoritative_refs,
                open_items=open_items,
                current_gate_state=handoff_gate_state or "waiting_review",
                blocked_reason=(
                    "group terminal handoff requested by "
                    + ", ".join(handoff_source_child_ids)
                ),
            )

        return None

    @staticmethod
    def _resolve_review_driver(
        left_path: str,
        right_path: str,
        overlap_decisions: list[dict] | None,
    ) -> dict[str, object]:
        """Resolve why an overlap became review_required."""
        shared_review_zone_ids: list[str] = []
        for decision in overlap_decisions or []:
            if not isinstance(decision, dict):
                continue
            if decision.get("decision") != "shared_review_zone_allowed":
                continue
            decision_left = decision.get("left_path")
            decision_right = decision.get("right_path")
            if {decision_left, decision_right} != {left_path, right_path}:
                continue
            zone_id = decision.get("shared_review_zone_id")
            if isinstance(zone_id, str) and zone_id and zone_id not in shared_review_zone_ids:
                shared_review_zone_ids.append(zone_id)

        if shared_review_zone_ids:
            return {
                "review_driver": "shared-review-zone",
                "shared_review_zone_ids": shared_review_zone_ids,
            }
        return {
            "review_driver": "conflict-overlap",
            "shared_review_zone_ids": [],
        }

    @staticmethod
    def _task_group_to_dict(task_group: TaskGroup) -> dict:
        return {
            "task_group_id": task_group.task_group_id,
            "parent_envelope_id": task_group.parent_envelope_id,
            "parent_trace_id": task_group.parent_trace_id,
            "mode": task_group.mode,
            "join_policy": task_group.join_policy,
            "merge_policy": task_group.merge_policy,
            "children": [
                {
                    "child_task_id": child.child_task_id,
                    "namespace": child.namespace,
                    "allowed_artifacts": list(child.allowed_artifacts),
                    "required_refs": list(child.required_refs),
                    "shared_review_zone_id": child.shared_review_zone_id,
                }
                for child in task_group.children
            ],
        }

    @staticmethod
    def _child_execution_record_to_dict(child_record: ChildExecutionRecord) -> dict:
        return {
            "child_task_id": child_record.child_task_id,
            "task_group_id": child_record.task_group_id,
            "trace_id": child_record.trace_id,
            "namespace": child_record.namespace,
            "status": child_record.status,
            "report": child_record.report,
        }

    @staticmethod
    def _merge_barrier_to_dict(merge_barrier: MergeBarrierOutcome) -> dict:
        return {
            "task_group_id": merge_barrier.task_group_id,
            "child_statuses": merge_barrier.child_statuses,
            "conflict_classification": merge_barrier.conflict_classification,
            "review_outcome": merge_barrier.review_outcome,
            "review_driver": merge_barrier.review_driver,
            "shared_review_zone_ids": list(merge_barrier.shared_review_zone_ids),
            "merged_delta": merge_barrier.merged_delta,
            "blocked_reason": merge_barrier.blocked_reason,
        }

    @staticmethod
    def _grouped_review_to_dict(grouped_review: GroupedReviewOutcome) -> dict:
        return {
            "task_group_id": grouped_review.task_group_id,
            "outcome": grouped_review.outcome,
            "review_driver": grouped_review.review_driver,
            "shared_review_zone_ids": list(grouped_review.shared_review_zone_ids),
            "child_reviews": grouped_review.child_reviews,
            "changed_artifacts": grouped_review.changed_artifacts,
            "unresolved_items": grouped_review.unresolved_items,
            "assumptions": grouped_review.assumptions,
            "blocked_reason": grouped_review.blocked_reason,
        }

    @staticmethod
    def _group_terminal_to_dict(group_terminal: GroupTerminalOutcome) -> dict:
        return {
            "task_group_id": group_terminal.task_group_id,
            "terminal_kind": group_terminal.terminal_kind,
            "source_child_ids": list(group_terminal.source_child_ids),
            "trigger_evidence": list(group_terminal.trigger_evidence),
            "suppressed_surfaces": list(group_terminal.suppressed_surfaces),
            "authoritative_refs": list(group_terminal.authoritative_refs),
            "open_items": list(group_terminal.open_items),
            "current_gate_state": group_terminal.current_gate_state,
            "blocked_reason": group_terminal.blocked_reason,
        }

    @staticmethod
    def _group_terminal_audit_detail(group_terminal: GroupTerminalOutcome) -> dict:
        return {
            "task_group_id": group_terminal.task_group_id,
            "terminal_kind": group_terminal.terminal_kind,
            "source_child_ids": list(group_terminal.source_child_ids),
            "suppressed_surfaces": list(group_terminal.suppressed_surfaces),
            "blocked_reason": group_terminal.blocked_reason,
        }

    @staticmethod
    def _normalize_contract_path(raw_path: object) -> str | None:
        """Normalize a contract path into a safe project-relative POSIX path."""
        if not isinstance(raw_path, str):
            return None
        stripped = raw_path.strip()
        if not stripped:
            return None
        if PureWindowsPath(stripped).is_absolute() or PurePosixPath(stripped).is_absolute():
            return None

        candidate = PurePosixPath(stripped.replace("\\", "/"))
        normalized_parts: list[str] = []
        for part in candidate.parts:
            if part in ("", "."):
                continue
            if part == "..":
                return None
            normalized_parts.append(part)

        if not normalized_parts:
            return None
        return PurePosixPath(*normalized_parts).as_posix()

    @staticmethod
    def _paths_overlap(left: str, right: str) -> bool:
        """Return True when two relative paths overlap by equality or ancestry."""
        left_path = PurePosixPath(left)
        right_path = PurePosixPath(right)
        return (
            left_path == right_path
            or left_path in right_path.parents
            or right_path in left_path.parents
        )

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
