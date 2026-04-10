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
            f"- Timestamp: {datetime.now(timezone.utc).isoformat()}\n"
        )

        plans.append(WritebackPlan(
            target_path=f".codex/writebacks/{envelope_id}.md",
            content=summary,
            operation="create",
            content_type="markdown",
        ))

        return plans

    # ── execution ───────────────────────────────────────

    def execute_plan(
        self, plan: WritebackPlan, *, dry_run: bool = True,
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
        return result

    def execute_all(
        self, plans: list[WritebackPlan], *, dry_run: bool = True,
    ) -> list[WritebackResult]:
        """Execute a list of write-back plans sequentially."""
        return [self.execute_plan(p, dry_run=dry_run) for p in plans]

    # ── atomic write helpers ────────────────────────────

    def _write_create(self, target: Path, plan: WritebackPlan) -> WritebackResult:
        target.parent.mkdir(parents=True, exist_ok=True)
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
