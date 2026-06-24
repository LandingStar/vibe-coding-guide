"""Explicit consumers for worker patch review proposals."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Mapping

from .agent_exchange_action_consumers import _disposition_payload
from .agent_exchange_action_consumers import _required_payload_str
from .agent_exchange_actions import (
    AgentExchangeTransitionResult,
    transition_exchange_artifact_lifecycle,
)
from .exchange import ExchangeArtifact
from .exchange_store import JsonArtifactVersionStore
from .worker_patch_review import WORKER_PATCH_REVIEW_PRODUCT_TYPE

WorkerPatchReviewDecisionAction = Literal["check", "apply", "reject"]

WORKER_PATCH_REVIEW_DECISION_TARGET_SURFACES = {
    "workerPatchReview",
    "cli:scheduler consume-worker-patch-review",
    "scheduler:worker-patch-review",
}


@dataclass(frozen=True, slots=True)
class WorkerPatchReviewConsumerResult:
    """Result of explicitly checking, applying, or rejecting a worker patch."""

    artifact_store_path: Path
    disposition_artifact_id: str
    disposition_version: str
    candidate_id: str
    source_artifact_id: str
    source_version: str
    action: str
    actor: str
    source_workspace_root: Path | None
    patch_state: str
    changed_paths: tuple[str, ...]
    git_check_returncode: int | None = None
    git_check_stdout: str = ""
    git_check_stderr: str = ""
    git_apply_returncode: int | None = None
    git_apply_stdout: str = ""
    git_apply_stderr: str = ""
    lifecycle_transition: AgentExchangeTransitionResult | None = None
    cleanup_recommended: bool = False

    @property
    def ok(self) -> bool:
        if self.action == "reject":
            return self.lifecycle_transition is not None
        if self.action == "check":
            return self.git_check_returncode == 0
        if self.action == "apply":
            return self.git_check_returncode == 0 and self.git_apply_returncode == 0
        return False

    def to_json_dict(self) -> dict[str, object]:
        transition_payload: Mapping[str, object] = (
            {}
            if self.lifecycle_transition is None
            else self.lifecycle_transition.to_json_dict()
        )
        return {
            "ok": self.ok,
            "artifact_store_path": str(self.artifact_store_path),
            "disposition_artifact_id": self.disposition_artifact_id,
            "disposition_version": self.disposition_version,
            "candidate_id": self.candidate_id,
            "source_artifact_id": self.source_artifact_id,
            "source_version": self.source_version,
            "source": f"{self.source_artifact_id}@{self.source_version}",
            "action": self.action,
            "actor": self.actor,
            "source_workspace_root": (
                "" if self.source_workspace_root is None else str(self.source_workspace_root)
            ),
            "patch_state": self.patch_state,
            "changed_paths": list(self.changed_paths),
            "git_check": {
                "returncode": self.git_check_returncode,
                "stdout": self.git_check_stdout,
                "stderr": self.git_check_stderr,
            },
            "git_apply": {
                "returncode": self.git_apply_returncode,
                "stdout": self.git_apply_stdout,
                "stderr": self.git_apply_stderr,
            },
            "lifecycle_transition": dict(transition_payload),
            "cleanup_recommended": self.cleanup_recommended,
            "cleanup_surface": "scheduler cleanup-receipts" if self.cleanup_recommended else "",
            "authority_split": {
                "source": "accepted_worker_patch_review_disposition",
                "exchange_store_mutated": bool(
                    transition_payload.get("authority_split", {}).get(
                        "exchange_store_mutated",
                        False,
                    )
                )
                if transition_payload
                else False,
                "source_workspace_mutated": self.action == "apply" and self.git_apply_returncode == 0,
                "patch_check_executed": self.git_check_returncode is not None,
                "patch_apply_executed": self.git_apply_returncode is not None,
                "scheduler_state_mutated": False,
                "merge_gate_mutated": False,
                "provider_executed": False,
                "sandbox_cleanup_executed": False,
                "local_work_trajectory_mutated": False,
            },
        }


def consume_worker_patch_review_decision(
    *,
    artifact_store_path: str | Path,
    disposition_artifact_id: str,
    disposition_version: str,
    action: WorkerPatchReviewDecisionAction,
    source_workspace_root: str | Path | None = None,
    actor: str = "operator",
    reason: str = "",
    timestamp: str = "",
    git_executable: str = "git",
) -> WorkerPatchReviewConsumerResult:
    """Consume an accepted worker patch proposal disposition explicitly."""

    if action not in {"check", "apply", "reject"}:
        raise ValueError("worker patch review action must be one of: check, apply, reject")
    if not disposition_artifact_id:
        raise ValueError("worker patch review consumer requires disposition_artifact_id")
    if not disposition_version:
        raise ValueError("worker patch review consumer requires disposition_version")
    if action in {"check", "apply"} and source_workspace_root is None:
        raise ValueError(f"worker patch review action {action!r} requires source_workspace_root")
    if not actor:
        raise ValueError("worker patch review consumer requires actor")

    store_path = Path(artifact_store_path)
    store = JsonArtifactVersionStore(store_path)
    try:
        disposition_record = store.get(disposition_artifact_id, disposition_version)
    except KeyError as exc:
        raise ValueError(
            f"disposition artifact version not found in {store_path}: "
            f"{disposition_artifact_id!r}@{disposition_version!r}"
        ) from exc

    disposition_payload = _disposition_payload(disposition_record.artifact)
    _validate_worker_patch_disposition_payload(
        disposition_payload,
        disposition_record.artifact,
    )
    source_artifact_id = _required_payload_str(
        disposition_payload,
        "source_artifact_id",
        disposition_record.artifact,
    )
    source_version = _required_payload_str(
        disposition_payload,
        "source_version",
        disposition_record.artifact,
    )
    candidate_id = _required_payload_str(
        disposition_payload,
        "candidate_id",
        disposition_record.artifact,
    )

    try:
        source_record = store.get(source_artifact_id, source_version)
    except KeyError as exc:
        raise ValueError(
            f"source worker patch artifact version not found in {store_path}: "
            f"{source_artifact_id!r}@{source_version!r}"
        ) from exc

    source_artifact = source_record.artifact
    patch_payload = _worker_patch_payload(source_artifact)
    patch_state = str(patch_payload.get("patch_state", ""))
    patch_text = _worker_patch_text(source_artifact)
    changed_paths = _string_tuple(patch_payload.get("changed_paths"))

    workspace = None if source_workspace_root is None else Path(source_workspace_root)
    git_check: _GitCommandResult | None = None
    git_apply: _GitCommandResult | None = None
    transition: AgentExchangeTransitionResult

    if action in {"check", "apply"}:
        if patch_state != "has_patch":
            raise ValueError(
                f"worker patch artifact {source_artifact_id!r}@{source_version!r} "
                f"patch_state is {patch_state!r}; expected 'has_patch'"
            )
        if not patch_text.strip():
            raise ValueError(
                f"worker patch artifact {source_artifact_id!r}@{source_version!r} "
                "does not contain git_diff evidence"
            )
        assert workspace is not None
        git_check = _git_apply_check(
            git_executable,
            workspace,
            patch_text,
        )
        if git_check.returncode != 0:
            return WorkerPatchReviewConsumerResult(
                artifact_store_path=store_path,
                disposition_artifact_id=disposition_artifact_id,
                disposition_version=disposition_version,
                candidate_id=candidate_id,
                source_artifact_id=source_artifact_id,
                source_version=source_version,
                action=action,
                actor=actor,
                source_workspace_root=workspace,
                patch_state=patch_state,
                changed_paths=changed_paths,
                git_check_returncode=git_check.returncode,
                git_check_stdout=git_check.stdout,
                git_check_stderr=git_check.stderr,
            )
        if action == "check":
            transition = transition_exchange_artifact_lifecycle(
                store_path=store_path,
                artifact_id=source_artifact_id,
                version=source_version,
                target_state="accepted",
                actor=actor,
                reason=reason or "worker patch proposal passed apply check",
                timestamp=timestamp,
            )
            return WorkerPatchReviewConsumerResult(
                artifact_store_path=store_path,
                disposition_artifact_id=disposition_artifact_id,
                disposition_version=disposition_version,
                candidate_id=candidate_id,
                source_artifact_id=source_artifact_id,
                source_version=source_version,
                action=action,
                actor=actor,
                source_workspace_root=workspace,
                patch_state=patch_state,
                changed_paths=changed_paths,
                git_check_returncode=git_check.returncode,
                git_check_stdout=git_check.stdout,
                git_check_stderr=git_check.stderr,
                lifecycle_transition=transition,
            )
        git_apply = _git_apply(git_executable, workspace, patch_text)
        transition = transition_exchange_artifact_lifecycle(
            store_path=store_path,
            artifact_id=source_artifact_id,
            version=source_version,
            target_state="consumed" if git_apply.returncode == 0 else "accepted",
            actor=actor,
            reason=reason
            or (
                "worker patch applied to source workspace"
                if git_apply.returncode == 0
                else "worker patch apply failed after successful check"
            ),
            timestamp=timestamp,
        )
        return WorkerPatchReviewConsumerResult(
            artifact_store_path=store_path,
            disposition_artifact_id=disposition_artifact_id,
            disposition_version=disposition_version,
            candidate_id=candidate_id,
            source_artifact_id=source_artifact_id,
            source_version=source_version,
            action=action,
            actor=actor,
            source_workspace_root=workspace,
            patch_state=patch_state,
            changed_paths=changed_paths,
            git_check_returncode=git_check.returncode,
            git_check_stdout=git_check.stdout,
            git_check_stderr=git_check.stderr,
            git_apply_returncode=git_apply.returncode,
            git_apply_stdout=git_apply.stdout,
            git_apply_stderr=git_apply.stderr,
            lifecycle_transition=transition,
            cleanup_recommended=git_apply.returncode == 0,
        )

    transition = transition_exchange_artifact_lifecycle(
        store_path=store_path,
        artifact_id=source_artifact_id,
        version=source_version,
        target_state="rejected",
        actor=actor,
        reason=reason or "worker patch proposal rejected",
        timestamp=timestamp,
    )
    return WorkerPatchReviewConsumerResult(
        artifact_store_path=store_path,
        disposition_artifact_id=disposition_artifact_id,
        disposition_version=disposition_version,
        candidate_id=candidate_id,
        source_artifact_id=source_artifact_id,
        source_version=source_version,
        action=action,
        actor=actor,
        source_workspace_root=workspace,
        patch_state=patch_state,
        changed_paths=changed_paths,
        lifecycle_transition=transition,
        cleanup_recommended=True,
    )


@dataclass(frozen=True, slots=True)
class _GitCommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def _git_apply_check(
    git_executable: str,
    workspace: Path,
    patch_text: str,
) -> _GitCommandResult:
    return _run_git_apply(git_executable, workspace, patch_text, "--check")


def _git_apply(
    git_executable: str,
    workspace: Path,
    patch_text: str,
) -> _GitCommandResult:
    return _run_git_apply(git_executable, workspace, patch_text)


def _run_git_apply(
    git_executable: str,
    workspace: Path,
    patch_text: str,
    *args: str,
) -> _GitCommandResult:
    if not workspace.exists():
        raise ValueError(f"source workspace root does not exist: {workspace}")
    completed = subprocess.run(
        (git_executable, "-C", str(workspace), "apply", *args),
        input=patch_text,
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


def _validate_worker_patch_disposition_payload(
    payload: Mapping[str, object],
    artifact: ExchangeArtifact,
) -> None:
    disposition = _required_payload_str(payload, "disposition", artifact)
    if disposition != "accept":
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} is {disposition!r}; "
            "only accepted worker patch review candidates can be consumed"
        )
    candidate_type = _required_payload_str(payload, "candidate_type", artifact)
    if candidate_type != "merge_candidate":
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} candidate_type "
            f"{candidate_type!r} is not merge_candidate"
        )
    target_surface = _required_payload_str(payload, "target_surface", artifact)
    if target_surface not in WORKER_PATCH_REVIEW_DECISION_TARGET_SURFACES:
        allowed = ", ".join(sorted(WORKER_PATCH_REVIEW_DECISION_TARGET_SURFACES))
        raise ValueError(
            f"disposition artifact {artifact.artifact_id!r} target_surface "
            f"{target_surface!r} is not a worker patch review surface; "
            f"expected one of: {allowed}"
        )


def _worker_patch_payload(artifact: ExchangeArtifact) -> Mapping[str, object]:
    matches = [
        part.data
        for part in artifact.parts
        if part.part_type == "structured"
        and part.data.get("product_type") == WORKER_PATCH_REVIEW_PRODUCT_TYPE
    ]
    if not matches:
        raise ValueError(
            f"source artifact {artifact.artifact_id!r}@{artifact.version!r} "
            f"does not contain product_type={WORKER_PATCH_REVIEW_PRODUCT_TYPE!r}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"source artifact {artifact.artifact_id!r}@{artifact.version!r} "
            f"contains multiple {WORKER_PATCH_REVIEW_PRODUCT_TYPE!r} payloads"
        )
    return matches[0]


def _worker_patch_text(artifact: ExchangeArtifact) -> str:
    for part in artifact.parts:
        if part.part_type == "evidence":
            value = part.data.get("git_diff")
            if isinstance(value, str):
                return value
    return ""


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value if item)
