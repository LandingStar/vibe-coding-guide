"""Read-only Codex worker runtime status summary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .exchange_store import (
    DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
    JsonArtifactVersionStore,
)
from .leader_worker_delivery import (
    DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
    LeaderWorkerDeliveryRecord,
    inspect_leader_worker_delivery_state,
    read_leader_worker_delivery_state,
)
from .runtime_invocation_audit import (
    DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
    RuntimeInvocationRecord,
    inspect_runtime_invocation_log,
)
from .scheduler_store import recover_scheduler_state


@dataclass(frozen=True, slots=True)
class CodexRuntimeStatusRequest:
    """Request for a compact read-only Codex runtime status summary."""

    scheduler_snapshot_path: str | Path
    scheduler_event_log_path: str | Path
    delivery_state_path: str | Path = DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH
    runtime_invocation_log_path: str | Path = DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH
    artifact_store_path: str | Path = DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH
    target_task_ids: tuple[str, ...] = ()
    latest_limit: int = 10
    strict_recovery: bool = True


@dataclass(frozen=True, slots=True)
class CodexRuntimeStatus:
    """Compact readback for operator or guide-agent decision making."""

    request: CodexRuntimeStatusRequest
    ok: bool
    scheduler_task_state_counts: Mapping[str, int]
    target_task_states: Mapping[str, str]
    waiting_task_ids: tuple[str, ...] = ()
    review_required_task_ids: tuple[str, ...] = ()
    completed_task_output_refs: tuple[Mapping[str, str], ...] = ()
    delivery_state_counts: Mapping[str, int] = field(default_factory=dict)
    latest_delivery_records: tuple[LeaderWorkerDeliveryRecord, ...] = ()
    runtime_invocation_counts: Mapping[str, int] = field(default_factory=dict)
    latest_runtime_invocations: tuple[RuntimeInvocationRecord, ...] = ()
    output_artifact_refs: tuple[Mapping[str, str], ...] = ()
    review_artifact_refs: tuple[Mapping[str, str], ...] = ()
    worker_patch_artifact_refs: tuple[Mapping[str, str], ...] = ()
    actionable_pending_codex_delivery_count: int = 0
    errors: tuple[str, ...] = ()

    @property
    def next_action(self) -> str:
        if self.errors:
            return "inspect_status_errors"
        if self.review_required_task_ids or self.review_artifact_refs:
            return "review_required_items"
        if self.delivery_state_counts.get("failed", 0):
            return "inspect_failed_delivery"
        if self.actionable_pending_codex_delivery_count:
            return "run_supervisor_loop"
        if self.waiting_task_ids:
            return "inspect_waiting_dependencies"
        return "idle"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "next_action": self.next_action,
            "paths": {
                "scheduler_snapshot_path": str(Path(self.request.scheduler_snapshot_path)),
                "scheduler_event_log_path": str(Path(self.request.scheduler_event_log_path)),
                "delivery_state_path": str(Path(self.request.delivery_state_path)),
                "runtime_invocation_log_path": str(Path(self.request.runtime_invocation_log_path)),
                "artifact_store_path": str(Path(self.request.artifact_store_path)),
            },
            "scheduler": {
                "task_state_counts": dict(self.scheduler_task_state_counts),
                "target_task_states": dict(self.target_task_states),
                "waiting_task_ids": list(self.waiting_task_ids),
                "review_required_task_ids": list(self.review_required_task_ids),
                "completed_task_output_refs": list(self.completed_task_output_refs),
            },
            "delivery": {
                "state_counts": dict(self.delivery_state_counts),
                "actionable_pending_codex_delivery_count": (
                    self.actionable_pending_codex_delivery_count
                ),
                "latest_records": [
                    record.to_json_dict()
                    for record in self.latest_delivery_records
                ],
            },
            "runtime_invocations": {
                "counts": dict(self.runtime_invocation_counts),
                "latest_records": [
                    record.to_json_dict()
                    for record in self.latest_runtime_invocations
                ],
            },
            "artifacts": {
                "output_artifact_refs": list(self.output_artifact_refs),
                "review_artifact_refs": list(self.review_artifact_refs),
                "worker_patch_artifact_refs": list(self.worker_patch_artifact_refs),
            },
            "errors": list(self.errors),
            "authority_split": {
                "read_model_only": True,
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "scheduler_event_log_mutated": False,
                "delivery_state_mutated": False,
                "delivery_log_mutated": False,
                "exchange_store_mutated": False,
                "runtime_invocation_log_mutated": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_exposed": False,
            },
        }


def inspect_codex_runtime_status(
    request: CodexRuntimeStatusRequest,
) -> CodexRuntimeStatus:
    """Build a compact read-only status summary for Codex worker delivery."""

    errors: list[str] = []
    try:
        recovery = recover_scheduler_state(
            request.scheduler_snapshot_path,
            request.scheduler_event_log_path,
            strict=request.strict_recovery,
        )
        scheduler_state = recovery.recovered_state
    except Exception as exc:
        return CodexRuntimeStatus(
            request=request,
            ok=False,
            scheduler_task_state_counts={},
            target_task_states={},
            errors=(f"scheduler recovery failed: {exc}",),
        )

    delivery = inspect_leader_worker_delivery_state(
        request.delivery_state_path,
        latest_limit=request.latest_limit,
    )
    if delivery.errors:
        errors.extend(f"delivery inspection failed: {error}" for error in delivery.errors)
    invocations = inspect_runtime_invocation_log(
        request.runtime_invocation_log_path,
        latest_limit=request.latest_limit,
    )
    if invocations.errors:
        errors.extend(
            f"runtime invocation inspection failed: {error}"
            for error in invocations.errors
        )
    output_refs, review_refs, patch_refs, artifact_errors = _artifact_refs(
        request.artifact_store_path,
        latest_limit=request.latest_limit,
    )
    errors.extend(artifact_errors)
    target_task_ids = request.target_task_ids or tuple(sorted(scheduler_state.tasks))
    return CodexRuntimeStatus(
        request=request,
        ok=not errors,
        scheduler_task_state_counts=_task_state_counts(scheduler_state.tasks.values()),
        target_task_states={
            task_id: scheduler_state.tasks[task_id].state
            if task_id in scheduler_state.tasks
            else "missing"
            for task_id in target_task_ids
        },
        waiting_task_ids=tuple(
            sorted(
                task.task_id
                for task in scheduler_state.tasks.values()
                if task.state == "waiting"
            )
        ),
        review_required_task_ids=tuple(
            sorted(
                task.task_id
                for task in scheduler_state.tasks.values()
                if task.state == "review_required"
            )
        ),
        completed_task_output_refs=tuple(
            _task_output_ref(task.task_id, task.output_artifact_ref)
            for task in sorted(
                scheduler_state.tasks.values(),
                key=lambda item: item.task_id,
            )
            if task.state == "complete" and task.output_artifact_ref is not None
        ),
        delivery_state_counts=delivery.state_counts,
        latest_delivery_records=delivery.latest_records,
        actionable_pending_codex_delivery_count=_actionable_pending_codex_delivery_count(
            request.delivery_state_path,
            scheduler_state.tasks,
        ),
        runtime_invocation_counts={
            "record_count": invocations.record_count,
            "succeeded": invocations.succeeded_count,
            "failed": invocations.failed_count,
            **{
                f"provider:{provider}": count
                for provider, count in invocations.provider_counts.items()
            },
        },
        latest_runtime_invocations=invocations.latest_records,
        output_artifact_refs=output_refs,
        review_artifact_refs=review_refs,
        worker_patch_artifact_refs=patch_refs,
        errors=tuple(errors),
    )


def _artifact_refs(
    artifact_store_path: str | Path,
    *,
    latest_limit: int,
) -> tuple[
    tuple[Mapping[str, str], ...],
    tuple[Mapping[str, str], ...],
    tuple[Mapping[str, str], ...],
    tuple[str, ...],
]:
    path = Path(artifact_store_path)
    if not path.exists():
        return (), (), (), ()
    try:
        records = JsonArtifactVersionStore(path).list_records()
    except Exception as exc:
        return (), (), (), (f"artifact store inspection failed: {exc}",)
    output_refs: list[Mapping[str, str]] = []
    review_refs: list[Mapping[str, str]] = []
    patch_refs: list[Mapping[str, str]] = []
    for record in records:
        ref = {
            "ref_kind": "exchange_artifact",
            "ref_id": record.artifact_id,
            "version": record.version,
        }
        product_type = _product_type(record.artifact)
        if product_type == "worker_patch_review_proposal":
            patch_refs.append({**ref, "product_type": product_type})
        elif "permission" in product_type or record.artifact.intent == "require_review":
            review_refs.append({**ref, "product_type": product_type})
        elif record.artifact.kind == "result":
            output_refs.append(ref)
    return (
        tuple(output_refs[-latest_limit:] if latest_limit >= 0 else output_refs),
        tuple(review_refs[-latest_limit:] if latest_limit >= 0 else review_refs),
        tuple(patch_refs[-latest_limit:] if latest_limit >= 0 else patch_refs),
        (),
    )


def _product_type(artifact: object) -> str:
    parts = getattr(artifact, "parts", ())
    for part in parts:
        data = getattr(part, "data", None)
        if isinstance(data, Mapping) and data.get("product_type"):
            return str(data["product_type"])
    return ""


def _task_output_ref(task_id: str, ref: object) -> Mapping[str, str]:
    return {
        "task_id": task_id,
        "ref_kind": str(getattr(ref, "ref_kind", "")),
        "ref_id": str(getattr(ref, "ref_id", "")),
        "version": str(getattr(ref, "version", "")),
    }


def _task_state_counts(tasks: object) -> dict[str, int]:
    counts: dict[str, int] = {}
    for task in tasks:  # type: ignore[assignment]
        state = getattr(task, "state", "")
        counts[state] = counts.get(state, 0) + 1
    return dict(sorted(counts.items()))


def _actionable_pending_codex_delivery_count(
    delivery_state_path: str | Path,
    tasks: Mapping[str, object],
) -> int:
    state = read_leader_worker_delivery_state(delivery_state_path)
    if state is None:
        return 0
    count = 0
    for record in state.records.values():
        if record.delivery_state != "pending":
            continue
        if record.event_kind != "task_ready" or record.next_action != "run_agent":
            continue
        task = tasks.get(record.task_id)
        if task is None:
            continue
        agent = getattr(task, "agent", None)
        if getattr(agent, "runtime_provider", "") != "codex":
            continue
        if getattr(task, "state", "") != "ready":
            continue
        count += 1
    return count


__all__ = [
    "CodexRuntimeStatus",
    "CodexRuntimeStatusRequest",
    "inspect_codex_runtime_status",
]
