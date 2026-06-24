"""Operator convenience surface for worker patch review actions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .agent_exchange_action_disposition import (
    AgentExchangeActionCandidateDispositionResult,
    decide_agent_exchange_action_candidate,
)
from .worker_patch_review_consumer import (
    WorkerPatchReviewConsumerResult,
    consume_worker_patch_review_decision,
)

WorkerPatchReviewOperatorAction = Literal["check", "reject"]


@dataclass(frozen=True, slots=True)
class WorkerPatchReviewOperatorResult:
    """Result of creating an accepted disposition and consuming it."""

    artifact_store_path: Path
    candidate_id: str
    action: str
    actor: str
    disposition: AgentExchangeActionCandidateDispositionResult
    consumer: WorkerPatchReviewConsumerResult

    @property
    def ok(self) -> bool:
        return self.consumer.ok

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "artifact_store_path": str(self.artifact_store_path),
            "candidate_id": self.candidate_id,
            "action": self.action,
            "actor": self.actor,
            "disposition": self.disposition.to_json_dict(),
            "consumer": self.consumer.to_json_dict(),
            "authority_split": {
                "exchange_store_mutated": True,
                "source_workspace_mutated": False,
                "patch_check_executed": self.consumer.git_check_returncode is not None,
                "patch_apply_executed": self.consumer.git_apply_returncode is not None,
                "scheduler_state_mutated": False,
                "merge_gate_mutated": False,
                "provider_executed": False,
                "sandbox_cleanup_executed": False,
                "local_work_trajectory_mutated": False,
            },
        }


def review_worker_patch_action_candidate(
    *,
    artifact_store_path: str | Path,
    candidate_id: str,
    action: WorkerPatchReviewOperatorAction,
    source_workspace_root: str | Path | None = None,
    actor: str = "operator",
    disposition_artifact_id: str = "",
    disposition_version: str = "v1",
    reason: str = "",
    timestamp: str = "",
    git_executable: str = "git",
    replace_existing_disposition: bool = True,
) -> WorkerPatchReviewOperatorResult:
    """Create an accepted worker-patch disposition and consume it explicitly."""

    if action not in {"check", "reject"}:
        raise ValueError("worker patch review operator action must be one of: check, reject")
    if not candidate_id:
        raise ValueError("worker patch review operator requires candidate_id")
    if action == "check" and source_workspace_root is None:
        raise ValueError(f"worker patch review operator action {action!r} requires source_workspace_root")
    if not actor:
        raise ValueError("worker patch review operator requires actor")

    store_path = Path(artifact_store_path)
    disposition_id = disposition_artifact_id or _default_disposition_artifact_id(
        candidate_id,
        action,
    )
    disposition = decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id=candidate_id,
        disposition_artifact_id=disposition_id,
        disposition_version=disposition_version,
        actor=actor,
        disposition="accept",
        reason=reason or f"worker patch review {action}",
        target_surface="workerPatchReview",
        timestamp=timestamp,
        replace_existing=replace_existing_disposition,
    )
    consumer = consume_worker_patch_review_decision(
        artifact_store_path=store_path,
        disposition_artifact_id=disposition.disposition_artifact_id,
        disposition_version=disposition.disposition_version,
        action=action,
        source_workspace_root=source_workspace_root,
        actor=actor,
        reason=reason,
        timestamp=timestamp,
        git_executable=git_executable,
    )
    return WorkerPatchReviewOperatorResult(
        artifact_store_path=store_path,
        candidate_id=candidate_id,
        action=action,
        actor=actor,
        disposition=disposition,
        consumer=consumer,
    )


def _default_disposition_artifact_id(candidate_id: str, action: str) -> str:
    token = "".join(
        ch if ch.isalnum() else "-"
        for ch in candidate_id
    ).strip("-").lower()
    token = token or "worker-patch"
    return f"{token}:{action}-disposition"
