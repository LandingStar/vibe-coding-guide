"""Write-back engine — plan and execute artifact writes.

Implements the PEP write-back capability defined in
``docs/governance-flow.md`` (step 7) and ``docs/core-model.md``.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.audit.audit_logger import AuditLogger


@dataclass
class WritebackPlan:
    """A single write-back action to perform."""

    target_path: str
    content: str
    operation: str = "create"   # create | update | append | section_replace | section_append | line_insert | line_replace
    content_type: str = "markdown"  # markdown | json | yaml | text
    match: str = ""             # heading name or regex pattern for section/line ops


@dataclass
class WritebackResult:
    """Outcome of executing a single WritebackPlan."""

    path: str
    operation: str
    success: bool
    detail: str = ""
    error: str = ""


class WritebackEngine:
    """Plan and execute artifact writes with audit trail.

    In dry-run mode (default) no files are modified; plans are
    generated and returned for inspection.  In non-dry-run mode,
    files are written atomically (write-to-temp then rename).
    """

    def __init__(self, *, base_dir: str | Path = ".") -> None:
        self._base_dir = Path(base_dir)
        self._history: list[dict] = []

    @property
    def history(self) -> list[dict]:
        return list(self._history)

    # ── planning ────────────────────────────────────────

    def plan(self, envelope: dict, execution_result: dict) -> list[WritebackPlan]:
        """Derive write-back plans from an execution result.

        Only produces plans when the review state is ``applied``.
        """
        review_state = execution_result.get("review_state", "")
        if review_state != "applied":
            return []

        plans: list[WritebackPlan] = []
        child_execution_records = execution_result.get("child_execution_records") or []
        if isinstance(child_execution_records, list) and child_execution_records:
            report_plans = []
            report_summary = {
                "planned_payloads": [],
                "skipped_payloads": [],
            }
        else:
            report_plans, report_summary = self._plan_report_payloads(execution_result)
        execution_result["report_writeback_summary"] = report_summary
        grouped_review_summary = self._summarize_grouped_review(execution_result)
        execution_result["grouped_review_writeback_summary"] = grouped_review_summary
        grouped_child_plans, grouped_child_summary = self._plan_grouped_review_payloads(execution_result)
        execution_result["grouped_child_writeback_summary"] = grouped_child_summary

        # Build a default plan from the execution detail.
        envelope_id = execution_result.get("envelope_id", "unknown")
        intent = envelope.get("intent_result", {}).get("intent", "unknown")
        gate_level = envelope.get("gate_decision", {}).get("gate_level", "unknown")
        detail = execution_result.get("detail", "")

        summary = (
            f"# Write-back: {envelope_id}\n\n"
            f"- Intent: {intent}\n"
            f"- Gate: {gate_level}\n"
            f"- Status: {review_state}\n"
            f"- Detail: {detail}\n"
            f"- Report payload-derived plans: {len(report_summary['planned_payloads'])}\n"
            f"- Report payloads skipped: {len(report_summary['skipped_payloads'])}\n"
            f"- Grouped child payload-derived plans: {len(grouped_child_summary['planned_payloads'])}\n"
            f"- Grouped child payloads skipped: {len(grouped_child_summary['skipped_payloads'])}\n"
            f"- Grouped child writeback eligibility: {grouped_child_summary['eligibility_basis']}\n"
            f"- Grouped review outcome: {grouped_review_summary['outcome']}\n"
            f"- Grouped review driver: {grouped_review_summary['review_driver']}\n"
            f"- Shared-review zones: {', '.join(grouped_review_summary['shared_review_zone_ids'])}\n"
            f"- Grouped review child count: {grouped_review_summary['child_count']}\n"
            f"- Grouped review unresolved items: {grouped_review_summary['unresolved_count']}\n"
            f"- Merge barrier classification: {grouped_review_summary['conflict_classification']}\n"
            f"- Children with payload candidates: {len(grouped_review_summary['children_with_payloads'])}\n"
            f"- Merge barrier blocked reason: {grouped_review_summary['blocked_reason']}\n"
            f"- Timestamp: {datetime.now(timezone.utc).isoformat()}\n"
        )
        terminal_kind = grouped_review_summary.get("terminal_kind")
        if isinstance(terminal_kind, str) and terminal_kind:
            summary += f"- Group terminal kind: {terminal_kind}\n"
        suppressed_surfaces = grouped_review_summary.get("suppressed_surfaces")
        if isinstance(suppressed_surfaces, list) and suppressed_surfaces:
            summary += f"- Suppressed surfaces: {', '.join(str(item) for item in suppressed_surfaces)}\n"

        plans.append(WritebackPlan(
            target_path=f".codex/writebacks/{envelope_id}.md",
            content=summary,
            operation="create",
            content_type="markdown",
        ))
        plans.extend(report_plans)
        plans.extend(grouped_child_plans)

        return plans

    def _plan_grouped_review_payloads(
        self, execution_result: dict,
    ) -> tuple[list[WritebackPlan], dict[str, object]]:
        """Plan child payload writeback for all_clear or zone-approved grouped review."""
        grouped_review = execution_result.get("grouped_review_outcome") or {}
        group_terminal = execution_result.get("group_terminal_outcome") or {}
        child_execution_records = execution_result.get("child_execution_records") or []
        task_group = execution_result.get("task_group") or {}

        summary: dict[str, object] = {
            "planned_payloads": [],
            "skipped_payloads": [],
            "eligibility_basis": "",
        }
        if isinstance(group_terminal, dict) and group_terminal:
            suppressed_surfaces = list(group_terminal.get("suppressed_surfaces") or [])
            if "grouped_child_writeback" in suppressed_surfaces:
                summary["eligibility_basis"] = "group_terminal_suppressed"
                summary["terminal_kind"] = group_terminal.get("terminal_kind", "")
                summary["suppressed_surfaces"] = suppressed_surfaces
                skipped_payloads = summary["skipped_payloads"]
                assert isinstance(skipped_payloads, list)
                skipped_payloads.append({
                    "path": "",
                    "reason": "group terminal outcome suppresses grouped child writeback",
                })
                return [], summary

        if not isinstance(child_execution_records, list) or not child_execution_records:
            return [], summary

        outcome = grouped_review.get("outcome") if isinstance(grouped_review, dict) else None
        eligibility_basis = self._resolve_grouped_review_payload_writeback_eligibility(
            execution_result,
        )
        summary["eligibility_basis"] = eligibility_basis
        if not eligibility_basis:
            skipped_payloads = summary["skipped_payloads"]
            assert isinstance(skipped_payloads, list)
            skipped_payloads.append({
                "path": "",
                "reason": f"grouped review outcome is {outcome or 'unknown'} without writeback eligibility",
            })
            return [], summary

        child_boundaries: dict[str, list[object]] = {}
        children = task_group.get("children") if isinstance(task_group, dict) else None
        if isinstance(children, list):
            for child in children:
                if not isinstance(child, dict):
                    continue
                child_task_id = child.get("child_task_id")
                if isinstance(child_task_id, str):
                    child_boundaries[child_task_id] = list(child.get("allowed_artifacts") or [])

        plans: list[WritebackPlan] = []
        for record in child_execution_records:
            if not isinstance(record, dict):
                skipped_payloads = summary["skipped_payloads"]
                assert isinstance(skipped_payloads, list)
                skipped_payloads.append({
                    "path": "",
                    "reason": "child execution record must be an object",
                })
                continue

            child_task_id = record.get("child_task_id")
            if not isinstance(child_task_id, str):
                skipped_payloads = summary["skipped_payloads"]
                assert isinstance(skipped_payloads, list)
                skipped_payloads.append({
                    "path": "",
                    "reason": "child execution record missing child_task_id",
                })
                continue

            report = record.get("report") or {}
            payloads = report.get("artifact_payloads") if isinstance(report, dict) else None
            child_plans, child_summary = self._plan_payload_entries(
                payloads,
                child_boundaries.get(child_task_id, []),
                summary_context={"child_task_id": child_task_id},
                empty_boundary_reason="child allowed_artifacts is empty",
            )
            plans.extend(child_plans)
            planned_payloads = summary["planned_payloads"]
            skipped_payloads = summary["skipped_payloads"]
            assert isinstance(planned_payloads, list)
            assert isinstance(skipped_payloads, list)
            planned_payloads.extend(child_summary["planned_payloads"])
            skipped_payloads.extend(child_summary["skipped_payloads"])

        return plans, summary

    def _resolve_grouped_review_payload_writeback_eligibility(
        self,
        execution_result: dict,
    ) -> str:
        """Return the basis that allows grouped child payload writeback."""
        grouped_review = execution_result.get("grouped_review_outcome") or {}
        merge_barrier = execution_result.get("merge_barrier_outcome") or {}
        if not isinstance(grouped_review, dict):
            grouped_review = {}
        if not isinstance(merge_barrier, dict):
            merge_barrier = {}

        outcome = grouped_review.get("outcome")
        if outcome == "all_clear":
            return "all_clear"

        review_state = execution_result.get("review_state")
        review_driver = grouped_review.get("review_driver") or merge_barrier.get("review_driver")
        shared_review_zone_ids = list(
            grouped_review.get("shared_review_zone_ids")
            or merge_barrier.get("shared_review_zone_ids")
            or []
        )
        if (
            review_state == "applied"
            and outcome == "review_required"
            and review_driver == "shared-review-zone"
            and shared_review_zone_ids
        ):
            return "shared-review-zone-approved"

        return ""

    def _summarize_grouped_review(self, execution_result: dict) -> dict[str, object]:
        """Summarize grouped review and merge barrier metadata for writeback."""
        grouped_review = execution_result.get("grouped_review_outcome")
        merge_barrier = execution_result.get("merge_barrier_outcome")
        group_terminal = execution_result.get("group_terminal_outcome")
        child_execution_records = execution_result.get("child_execution_records") or []

        children_with_payloads: list[str] = []
        if isinstance(child_execution_records, list):
            for record in child_execution_records:
                if not isinstance(record, dict):
                    continue
                report = record.get("report") or {}
                payloads = report.get("artifact_payloads") if isinstance(report, dict) else None
                if isinstance(payloads, list) and payloads:
                    child_task_id = record.get("child_task_id")
                    if isinstance(child_task_id, str):
                        children_with_payloads.append(child_task_id)

        if not isinstance(grouped_review, dict):
            grouped_review = {}
        if not isinstance(merge_barrier, dict):
            merge_barrier = {}
        if not isinstance(group_terminal, dict):
            group_terminal = {}

        if group_terminal:
            return {
                "outcome": "suppressed_by_group_terminal",
                "review_driver": "",
                "shared_review_zone_ids": [],
                "child_count": 0,
                "unresolved_count": 0,
                "conflict_classification": "",
                "children_with_payloads": children_with_payloads,
                "blocked_reason": group_terminal.get("blocked_reason", ""),
                "terminal_kind": group_terminal.get("terminal_kind", ""),
                "suppressed_surfaces": list(group_terminal.get("suppressed_surfaces") or []),
            }

        child_reviews = grouped_review.get("child_reviews")
        unresolved_items = grouped_review.get("unresolved_items")

        return {
            "outcome": grouped_review.get("outcome", ""),
            "review_driver": grouped_review.get("review_driver") or merge_barrier.get("review_driver", ""),
            "shared_review_zone_ids": list(grouped_review.get("shared_review_zone_ids") or merge_barrier.get("shared_review_zone_ids") or []),
            "child_count": len(child_reviews) if isinstance(child_reviews, dict) else 0,
            "unresolved_count": len(unresolved_items) if isinstance(unresolved_items, list) else 0,
            "conflict_classification": merge_barrier.get("conflict_classification", ""),
            "children_with_payloads": children_with_payloads,
            "blocked_reason": merge_barrier.get("blocked_reason") or grouped_review.get("blocked_reason", ""),
        }

    def _plan_report_payloads(
        self, execution_result: dict,
    ) -> tuple[list[WritebackPlan], dict[str, list[dict[str, str]]]]:
        """Convert report artifact payloads into safe writeback plans."""
        report = execution_result.get("report") or {}
        contract = execution_result.get("contract") or {}
        payloads = report.get("artifact_payloads")

        return self._plan_payload_entries(
            payloads,
            contract.get("allowed_artifacts") or [],
        )

    def _plan_payload_entries(
        self,
        payloads: object,
        allowed_artifacts: list[object],
        *,
        summary_context: dict[str, str] | None = None,
        empty_boundary_reason: str = "contract.allowed_artifacts is empty",
    ) -> tuple[list[WritebackPlan], dict[str, list[dict[str, str]]]]:
        """Convert payload entries into safe writeback plans under a boundary."""

        summary: dict[str, list[dict[str, str]]] = {
            "planned_payloads": [],
            "skipped_payloads": [],
        }
        if not isinstance(payloads, list) or not payloads:
            return [], summary

        normalized_allowed_artifacts = self._normalize_allowed_artifacts(allowed_artifacts)
        plans: list[WritebackPlan] = []

        for payload in payloads:
            entry_prefix = dict(summary_context or {})
            if not isinstance(payload, dict):
                summary["skipped_payloads"].append({
                    **entry_prefix,
                    "path": "",
                    "reason": "payload must be an object",
                })
                continue

            raw_path = str(payload.get("path", "")) if payload.get("path") is not None else ""
            normalized_path = self._normalize_relative_path(raw_path)
            if normalized_path is None:
                summary["skipped_payloads"].append({
                    **entry_prefix,
                    "path": raw_path,
                    "reason": "path must be a non-empty project-relative path inside base_dir",
                })
                continue

            if not normalized_allowed_artifacts:
                summary["skipped_payloads"].append({
                    **entry_prefix,
                    "path": normalized_path,
                    "reason": empty_boundary_reason,
                })
                continue

            if not self._is_path_allowed(normalized_path, normalized_allowed_artifacts):
                summary["skipped_payloads"].append({
                    **entry_prefix,
                    "path": normalized_path,
                    "reason": "path is outside contract.allowed_artifacts",
                })
                continue

            content = payload.get("content")
            if not isinstance(content, str):
                summary["skipped_payloads"].append({
                    **entry_prefix,
                    "path": normalized_path,
                    "reason": "content must be a string",
                })
                continue

            operation = payload.get("operation")
            if operation not in {"create", "update", "append"}:
                summary["skipped_payloads"].append({
                    **entry_prefix,
                    "path": normalized_path,
                    "reason": f"unsupported operation: {operation}",
                })
                continue

            content_type = payload.get("content_type")
            if content_type not in {"markdown", "json", "yaml", "text"}:
                summary["skipped_payloads"].append({
                    **entry_prefix,
                    "path": normalized_path,
                    "reason": f"unsupported content_type: {content_type}",
                })
                continue

            plans.append(WritebackPlan(
                target_path=normalized_path,
                content=content,
                operation=operation,
                content_type=content_type,
            ))
            summary["planned_payloads"].append({
                **entry_prefix,
                "path": normalized_path,
                "operation": operation,
            })

        return plans, summary

    def _normalize_allowed_artifacts(self, allowed_artifacts: list[object]) -> list[str]:
        """Normalize contract allowed_artifacts entries into safe relative paths."""
        normalized: list[str] = []
        for value in allowed_artifacts:
            if not isinstance(value, str):
                continue
            normalized_value = self._normalize_relative_path(value)
            if normalized_value is not None:
                normalized.append(normalized_value)
        return normalized

    def _normalize_relative_path(self, raw_path: str) -> str | None:
        """Return a project-root relative POSIX path or ``None`` if unsafe."""
        if not isinstance(raw_path, str):
            return None
        stripped = raw_path.strip()
        if not stripped:
            return None

        candidate = Path(stripped)
        if candidate.is_absolute():
            return None

        resolved_base = self._base_dir.resolve()
        resolved_target = (resolved_base / candidate).resolve()
        try:
            relative = resolved_target.relative_to(resolved_base)
        except ValueError:
            return None
        return relative.as_posix()

    @staticmethod
    def _is_path_allowed(path: str, allowed_artifacts: list[str]) -> bool:
        """Check whether *path* is inside the declared contract boundary."""
        for allowed in allowed_artifacts:
            if path == allowed or path.startswith(f"{allowed.rstrip('/')}/"):
                return True
        return False

    # ── execution ───────────────────────────────────────

    def execute_plan(
        self, plan: WritebackPlan, *, dry_run: bool = True,
        audit_logger: AuditLogger | None = None, trace_id: str | None = None,
    ) -> WritebackResult:
        """Execute a single write-back plan."""
        target = self._base_dir / plan.target_path

        if dry_run:
            result = WritebackResult(
                path=str(plan.target_path),
                operation=plan.operation,
                success=True,
                detail=f"dry-run: would {plan.operation} {plan.target_path}",
            )
            self._record(plan, result, dry_run=True)
            return result

        try:
            if plan.operation == "create":
                result = self._write_create(target, plan)
            elif plan.operation == "update":
                result = self._write_update(target, plan)
            elif plan.operation == "append":
                result = self._write_append(target, plan)
            elif plan.operation in (
                "section_replace", "section_append",
                "line_insert", "line_replace",
            ):
                result = self._write_directive(target, plan)
            else:
                result = WritebackResult(
                    path=str(plan.target_path),
                    operation=plan.operation,
                    success=False,
                    error=f"Unknown operation: {plan.operation}",
                )
        except Exception as exc:  # noqa: BLE001
            result = WritebackResult(
                path=str(plan.target_path),
                operation=plan.operation,
                success=False,
                error=str(exc),
            )

        self._record(plan, result, dry_run=False)

        # Audit: artifact_changed event for successful writes
        if result.success and audit_logger and trace_id:
            audit_logger.emit(
                "artifact_changed", "writeback", trace_id,
                detail={"path": result.path, "operation": result.operation},
            )

        return result

    def execute_all(
        self, plans: list[WritebackPlan], *, dry_run: bool = True,
        audit_logger: AuditLogger | None = None, trace_id: str | None = None,
    ) -> list[WritebackResult]:
        """Execute a list of write-back plans sequentially."""
        # Audit: writeback_planned event
        if audit_logger and trace_id and plans:
            audit_logger.emit(
                "writeback_planned", "writeback", trace_id,
                detail={"plans_count": len(plans), "targets": [p.target_path for p in plans]},
            )

        return [self.execute_plan(p, dry_run=dry_run, audit_logger=audit_logger, trace_id=trace_id) for p in plans]

    # ── atomic write helpers ────────────────────────────

    def _write_create(self, target: Path, plan: WritebackPlan) -> WritebackResult:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            return WritebackResult(
                path=str(plan.target_path),
                operation="create",
                success=False,
                error=f"Target already exists: {plan.target_path}",
            )
        self._atomic_write(target, plan.content)
        return WritebackResult(
            path=str(plan.target_path),
            operation="create",
            success=True,
            detail=f"Created {plan.target_path} ({len(plan.content)} bytes)",
        )

    def _write_update(self, target: Path, plan: WritebackPlan) -> WritebackResult:
        if not target.exists():
            return WritebackResult(
                path=str(plan.target_path),
                operation="update",
                success=False,
                error=f"Target does not exist: {plan.target_path}",
            )
        self._atomic_write(target, plan.content)
        return WritebackResult(
            path=str(plan.target_path),
            operation="update",
            success=True,
            detail=f"Updated {plan.target_path} ({len(plan.content)} bytes)",
        )

    def _write_append(self, target: Path, plan: WritebackPlan) -> WritebackResult:
        target.parent.mkdir(parents=True, exist_ok=True)
        existing = target.read_text(encoding="utf-8") if target.exists() else ""
        self._atomic_write(target, existing + plan.content)
        return WritebackResult(
            path=str(plan.target_path),
            operation="append",
            success=True,
            detail=f"Appended to {plan.target_path} ({len(plan.content)} bytes added)",
        )

    @staticmethod
    def _atomic_write(target: Path, content: str) -> None:
        """Write content atomically via temp-file + rename."""
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(target.parent), suffix=".tmp",
        )
        try:
            os.write(fd, content.encode("utf-8"))
            os.close(fd)
            # On Windows, os.replace is atomic when same volume.
            os.replace(tmp_path, str(target))
        except BaseException:
            os.close(fd) if not os.get_inheritable(fd) else None
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    # ── directive-based write helpers ──────────────────────

    def _write_directive(self, target: Path, plan: WritebackPlan) -> WritebackResult:
        """Execute a section/line-level directive operation."""
        from . import markdown_updater as mu

        if not target.exists():
            return WritebackResult(
                path=str(plan.target_path),
                operation=plan.operation,
                success=False,
                error=f"Target does not exist: {plan.target_path}",
            )

        lines = target.read_text(encoding="utf-8").splitlines(keepends=True)

        try:
            if plan.operation == "section_replace":
                lines = mu.replace_section(lines, plan.match, plan.content)
            elif plan.operation == "section_append":
                lines = mu.append_to_section(lines, plan.match, plan.content)
            elif plan.operation == "line_insert":
                lines = mu.insert_after_line(lines, plan.match, plan.content)
            elif plan.operation == "line_replace":
                lines = mu.replace_line(lines, plan.match, plan.content)
        except KeyError as exc:
            return WritebackResult(
                path=str(plan.target_path),
                operation=plan.operation,
                success=False,
                error=str(exc),
            )

        self._atomic_write(target, "".join(lines))
        return WritebackResult(
            path=str(plan.target_path),
            operation=plan.operation,
            success=True,
            detail=f"{plan.operation} on {plan.target_path} (match={plan.match!r})",
        )

    # ── audit ───────────────────────────────────────────

    def _record(
        self, plan: WritebackPlan, result: WritebackResult, *, dry_run: bool,
    ) -> None:
        self._history.append({
            "target_path": plan.target_path,
            "operation": plan.operation,
            "content_type": plan.content_type,
            "dry_run": dry_run,
            "success": result.success,
            "detail": result.detail,
            "error": result.error,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
