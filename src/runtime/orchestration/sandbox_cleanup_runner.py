"""Explicit cleanup runner for durable sandbox allocation receipts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .sandbox import GitWorktreeSandboxProvider, SandboxAllocation
from .sandbox_allocation_evidence import (
    SandboxAllocationReceiptEvidenceWriteResult,
    build_sandbox_allocation_receipt_evidence,
    default_sandbox_allocation_receipt_evidence_path,
    read_sandbox_allocation_receipt_evidence_summary,
    write_sandbox_allocation_receipt_evidence,
)


@dataclass(frozen=True, slots=True)
class SandboxCleanupRunnerResult:
    """Result of one explicit cleanup pass over durable allocation evidence."""

    input_evidence_path: Path
    output_evidence_path: Path
    input_evidence_id: str
    output_evidence_id: str
    allocation_count: int
    selected_allocation_ids: tuple[str, ...]
    cleaned_allocation_ids: tuple[str, ...]
    failed_allocation_ids: tuple[str, ...]
    skipped_allocation_ids: tuple[str, ...]
    evidence_write: SandboxAllocationReceiptEvidenceWriteResult
    local_trajectory_mutated: bool = False

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-safe cleanup runner summary."""

        return {
            "ok": not self.failed_allocation_ids,
            "input_evidence_path": str(self.input_evidence_path),
            "output_evidence_path": str(self.output_evidence_path),
            "input_evidence_id": self.input_evidence_id,
            "output_evidence_id": self.output_evidence_id,
            "allocation_count": self.allocation_count,
            "selected_allocation_ids": list(self.selected_allocation_ids),
            "cleaned_allocation_ids": list(self.cleaned_allocation_ids),
            "failed_allocation_ids": list(self.failed_allocation_ids),
            "skipped_allocation_ids": list(self.skipped_allocation_ids),
            "cleanup_executed": bool(self.selected_allocation_ids),
            "local_trajectory_mutated": self.local_trajectory_mutated,
            "authority_split": {
                "scheduler_state_read": False,
                "scheduler_state_mutated": False,
                "runtime_provider_executed": False,
                "sandbox_provider_executed": bool(self.selected_allocation_ids),
                "cleanup_executed": bool(self.selected_allocation_ids),
                "evidence_written": True,
                "local_work_trajectory_mutated": self.local_trajectory_mutated,
            },
        }


def run_sandbox_allocation_cleanup_over_receipts(
    evidence_path: str | Path,
    *,
    output_evidence_path: str | Path | None = None,
    output_evidence_id: str = "",
    timestamp: str = "",
    git_executable: str = "git",
    metadata: Mapping[str, object] | None = None,
) -> SandboxCleanupRunnerResult:
    """Run explicit cleanup for cleanup-required git-worktree allocations."""

    summary = read_sandbox_allocation_receipt_evidence_summary(evidence_path)
    cleanup_evidence_id = output_evidence_id or f"{summary.evidence_id}:cleanup"
    target = (
        Path(output_evidence_path)
        if output_evidence_path is not None
        else default_sandbox_allocation_receipt_evidence_path(
            _project_root_from_evidence_path(summary.evidence_path),
            cleanup_evidence_id,
        )
    )

    updated_allocations: list[SandboxAllocation] = []
    selected_ids: list[str] = []
    cleaned_ids: list[str] = []
    failed_ids: list[str] = []
    skipped_ids: list[str] = []

    for allocation in summary.allocations:
        if _allocation_requires_git_worktree_cleanup(allocation):
            selected_ids.append(allocation.allocation_id)
            provider = _provider_for_git_worktree_allocation(
                allocation,
                git_executable=git_executable,
            )
            cleaned = provider.cleanup(allocation)
            updated_allocations.append(cleaned)
            if not cleaned.cleanup_required:
                cleaned_ids.append(allocation.allocation_id)
            else:
                failed_ids.append(allocation.allocation_id)
        else:
            skipped_ids.append(allocation.allocation_id)
            updated_allocations.append(allocation)

    cleanup_metadata: dict[str, object] = dict(summary.metadata)
    cleanup_metadata.update({
        "source_evidence_path": str(summary.evidence_path),
        "source_evidence_id": summary.evidence_id,
        "source_evidence_allocation_count": summary.allocation_count,
        "surface": "explicit-sandbox-allocation-cleanup-runner",
    })
    cleanup_metadata.update({} if metadata is None else dict(metadata))
    authority_split = {
        "scheduler_state_read": False,
        "scheduler_state_mutated": False,
        "runtime_provider_executed": False,
        "sandbox_provider_executed": bool(selected_ids),
        "cleanup_executed": bool(selected_ids),
        "evidence_written": True,
        "local_work_trajectory_mutated": False,
    }
    write = write_sandbox_allocation_receipt_evidence(
        build_sandbox_allocation_receipt_evidence(
            tuple(updated_allocations),
            evidence_id=cleanup_evidence_id,
            timestamp=timestamp or summary.timestamp,
            evidence_path=target,
            metadata=cleanup_metadata,
            authority_split=authority_split,
        ),
        target,
    )
    return SandboxCleanupRunnerResult(
        input_evidence_path=summary.evidence_path,
        output_evidence_path=write.evidence_path,
        input_evidence_id=summary.evidence_id,
        output_evidence_id=cleanup_evidence_id,
        allocation_count=summary.allocation_count,
        selected_allocation_ids=tuple(selected_ids),
        cleaned_allocation_ids=tuple(cleaned_ids),
        failed_allocation_ids=tuple(failed_ids),
        skipped_allocation_ids=tuple(skipped_ids),
        evidence_write=write,
    )


def _allocation_requires_git_worktree_cleanup(allocation: SandboxAllocation) -> bool:
    receipt = allocation.git_worktree_receipt
    return (
        allocation.provider == "git-worktree"
        and allocation.state == "allocated"
        and allocation.cleanup_required
        and receipt is not None
        and receipt.cleanup_state == "required"
    )


def _provider_for_git_worktree_allocation(
    allocation: SandboxAllocation,
    *,
    git_executable: str,
) -> GitWorktreeSandboxProvider:
    receipt = allocation.git_worktree_receipt
    if receipt is None or not receipt.sandbox_root:
        raise ValueError(
            "cleanup-required git-worktree allocation is missing "
            f"receipt.sandbox_root: {allocation.allocation_id}"
        )
    return GitWorktreeSandboxProvider(
        receipt.sandbox_root,
        git_executable=git_executable,
        base_ref=receipt.base_ref,
    )


def _project_root_from_evidence_path(evidence_path: Path) -> Path:
    parts = evidence_path.parts
    if ".codex" in parts:
        index = parts.index(".codex")
        if index > 0:
            return Path(*parts[:index])
        return Path(".")
    return evidence_path.parent
