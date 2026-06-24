"""Worker sandbox patch review artifacts.

This module exports worker sandbox changes into ExchangeArtifact review
products. It never applies patches to the source workspace.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .exchange import (
    ExchangeArtifact,
    ExchangePayloadPart,
    ExchangeReference,
    ExchangeRelation,
    ExchangeScope,
    VisibilityPolicy,
)
from .preflight import PreflightedTaskRunResult
from .runtime_adapter import ArtifactDelta
from .sandbox import SandboxAllocation

WORKER_PATCH_REVIEW_PRODUCT_TYPE = "worker_patch_review_proposal"
WORKER_PATCH_REVIEW_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class WorkerPatchReviewArtifact:
    """Patch review product derived from one worker run."""

    artifact: ExchangeArtifact
    changed_paths: tuple[str, ...]
    patch_text: str
    patch_state: str
    git_status: str = ""
    git_diff_returncode: int | None = None
    git_status_returncode: int | None = None

    def to_receipt_ref(self) -> dict[str, object]:
        return {
            "ref_kind": "exchange_artifact",
            "ref_id": self.artifact.artifact_id,
            "version": self.artifact.version,
            "patch_state": self.patch_state,
            "changed_paths": list(self.changed_paths),
        }


def build_worker_patch_review_artifacts(
    run_results: tuple[PreflightedTaskRunResult, ...],
    *,
    timestamp: str = "",
    guide_agent_id: str = "agent:guide",
    target_task_id: str = "",
    git_executable: str = "git",
) -> tuple[WorkerPatchReviewArtifact, ...]:
    """Build review artifacts for completed worker runs with sandbox changes."""

    artifacts: list[WorkerPatchReviewArtifact] = []
    for run in run_results:
        if run.preflight.sandbox_allocation.provider != "git-worktree":
            continue
        artifacts.append(
            build_worker_patch_review_artifact(
                run,
                timestamp=timestamp,
                guide_agent_id=guide_agent_id,
                target_task_id=target_task_id,
                git_executable=git_executable,
            )
        )
    return tuple(artifacts)


def build_worker_patch_review_artifact(
    run: PreflightedTaskRunResult,
    *,
    timestamp: str = "",
    guide_agent_id: str = "agent:guide",
    target_task_id: str = "",
    git_executable: str = "git",
) -> WorkerPatchReviewArtifact:
    """Build one worker patch review ExchangeArtifact from a completed run."""

    if run.runtime_result is None:
        raise ValueError("worker patch review artifact requires runtime_result")
    task = run.preflight.task
    allocation = run.preflight.sandbox_allocation
    delta = run.runtime_result.artifact_delta
    scope = task.context_scope
    worker_agent_id = task.agent.agent_id
    status = _collect_git_status(allocation, git_executable=git_executable)
    patch = _collect_git_diff(allocation, git_executable=git_executable)
    changed_paths = _changed_paths(status.stdout, delta)
    workspace_root = _patch_workspace_root(allocation)
    patch_state = "has_patch" if patch.stdout.strip() else "empty_patch"
    if status.returncode not in (0, None) or patch.returncode not in (0, None):
        patch_state = "patch_collection_failed"
    artifact_id = _patch_artifact_id(task.task_id)
    version = "v1"
    payload = {
        "product_type": WORKER_PATCH_REVIEW_PRODUCT_TYPE,
        "schema_version": WORKER_PATCH_REVIEW_SCHEMA_VERSION,
        "task_id": task.task_id,
        "lane_id": scope.lane_id,
        "worker_agent_id": worker_agent_id,
        "runtime_provider": task_agent_provider(run),
        "sandbox_provider": allocation.provider,
        "sandbox_allocation_id": allocation.allocation_id,
        "sandbox_workspace_root": workspace_root,
        "source_repository_root": _source_repository_root(allocation),
        "output_artifact_ref": {
            "ref_kind": "exchange_artifact",
            "ref_id": run.runtime_result.output_artifact.artifact_id,
            "version": run.runtime_result.output_artifact.version,
        },
        "changed_paths": list(changed_paths),
        "patch_state": patch_state,
        "git_status_returncode": status.returncode,
        "git_diff_returncode": patch.returncode,
        "merge_review_state": "review_required",
        "auto_merge_performed": False,
    }
    artifact = ExchangeArtifact(
        artifact_id=artifact_id,
        kind="proposal",
        intent="request_merge",
        producer=worker_agent_id,
        audience=tuple(dict.fromkeys((guide_agent_id, task.agent.agent_id))),
        scope=ExchangeScope(
            lane_id=scope.lane_id,
            task_id=task.task_id,
            context_id=scope.context_id,
            agent_id=worker_agent_id,
            runtime_session_id=run.runtime_result.run_handle.session_id,
        ),
        lifecycle_state="proposed",
        visibility_policy=VisibilityPolicy(
            audience=tuple(dict.fromkeys((guide_agent_id, task.agent.agent_id))),
            cross_lane=True,
        ),
        created_at=timestamp,
        version=version,
        parts=(
            ExchangePayloadPart(
                part_type="text",
                text=(
                    f"Worker patch review proposal for {task.task_id}: "
                    f"{patch_state}."
                ),
            ),
            ExchangePayloadPart(part_type="structured", data=payload),
            ExchangePayloadPart(
                part_type="artifact_delta",
                data={
                    "artifact_id": delta.artifact_id,
                    "version": delta.version,
                    "summary": delta.summary,
                    "changed_refs": [
                        {
                            "ref_kind": ref.ref_kind,
                            "ref_id": ref.ref_id,
                            "version": ref.version,
                            "path": ref.path,
                            "label": ref.label,
                        }
                        for ref in delta.changed_refs
                    ],
                },
            ),
            ExchangePayloadPart(
                part_type="evidence",
                data={
                    "git_status": status.stdout,
                    "git_status_stderr": status.stderr,
                    "git_diff": patch.stdout,
                    "git_diff_stderr": patch.stderr,
                },
            ),
            ExchangePayloadPart(
                part_type="relation",
                relation=ExchangeRelation(
                    relation_id=f"relation/{_safe_token(task.task_id)}/merge-target",
                    relation_kind="merges_into",
                    source=ExchangeReference(
                        ref_kind="exchange_artifact",
                        ref_id=artifact_id,
                        version=version,
                        label="worker_patch_review",
                    ),
                    target=ExchangeReference(
                        ref_kind="scheduler_task",
                        ref_id=target_task_id or task.task_id,
                        label="merge_review_target",
                    ),
                    reason="Worker sandbox patch requires explicit merge review.",
                ),
            ),
        ),
    )
    return WorkerPatchReviewArtifact(
        artifact=artifact,
        changed_paths=changed_paths,
        patch_text=patch.stdout,
        patch_state=patch_state,
        git_status=status.stdout,
        git_diff_returncode=patch.returncode,
        git_status_returncode=status.returncode,
    )


def task_agent_provider(run: PreflightedTaskRunResult) -> str:
    return run.preflight.task.agent.runtime_provider


@dataclass(frozen=True, slots=True)
class _GitCommandResult:
    returncode: int | None
    stdout: str = ""
    stderr: str = ""


def _collect_git_status(
    allocation: SandboxAllocation,
    *,
    git_executable: str,
) -> _GitCommandResult:
    if allocation.provider != "git-worktree":
        return _GitCommandResult(returncode=None)
    workspace = Path(_patch_workspace_root(allocation))
    if not workspace.exists():
        return _GitCommandResult(
            returncode=1,
            stderr=f"sandbox workspace does not exist: {workspace}",
        )
    return _run_git(git_executable, workspace, "status", "--porcelain")


def _collect_git_diff(
    allocation: SandboxAllocation,
    *,
    git_executable: str,
) -> _GitCommandResult:
    if allocation.provider != "git-worktree":
        return _GitCommandResult(returncode=None)
    workspace = Path(_patch_workspace_root(allocation))
    if not workspace.exists():
        return _GitCommandResult(
            returncode=1,
            stderr=f"sandbox workspace does not exist: {workspace}",
        )
    return _run_git(git_executable, workspace, "diff", "--binary")


def _run_git(git_executable: str, workspace: Path, *args: str) -> _GitCommandResult:
    completed = subprocess.run(
        (git_executable, "-C", str(workspace), *args),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return _GitCommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _changed_paths(status_output: str, delta: ArtifactDelta) -> tuple[str, ...]:
    paths: list[str] = []
    for line in status_output.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        if path:
            paths.append(path)
    for ref in delta.changed_refs:
        if ref.path:
            paths.append(ref.path)
    return tuple(dict.fromkeys(paths))


def _source_repository_root(allocation: SandboxAllocation) -> str:
    receipt = allocation.git_worktree_receipt
    if receipt is None:
        return ""
    return receipt.source_repository_root


def _patch_workspace_root(allocation: SandboxAllocation) -> str:
    receipt = allocation.git_worktree_receipt
    if receipt is not None and receipt.worktree_path:
        return receipt.worktree_path
    return allocation.workspace_root


def _patch_artifact_id(task_id: str) -> str:
    return f"{task_id}:patch-review"


def _safe_token(value: str) -> str:
    token = "".join(ch if ch.isalnum() else "-" for ch in value).strip("-").lower()
    return token or "worker"
