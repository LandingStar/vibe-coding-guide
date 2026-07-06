"""Deterministic guide/worker exchange dogfood workflow.

This helper proves the guide/worker communication product sequence by composing
the existing ExchangeArtifact mailbox, reply, history, action-candidate,
disposition, and accepted scheduler-candidate consumer surfaces.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from .artifact_paths import dbc_artifact_path
from .agent_communication import inspect_agent_exchange_mailbox
from .agent_exchange_action_candidates import inspect_agent_exchange_action_candidates
from .agent_exchange_action_consumers import consume_accepted_scheduler_action_candidate
from .agent_exchange_action_disposition import decide_agent_exchange_action_candidate
from .agent_exchange_actions import reply_to_exchange_artifact
from .agent_exchange_history import inspect_agent_exchange_history_summary
from .exchange import (
    ExchangeArtifact,
    ExchangeCausality,
    ExchangeLog,
    ExchangePayloadPart,
    ExchangeScope,
    VisibilityPolicy,
)
from .exchange_store import JsonArtifactVersionStore
from .runtime_adapter import AgentSpec
from .scheduler import ContextScope
from .scheduler_submission import (
    SchedulerTaskSubmission,
    scheduler_task_submission_to_artifact,
)

DEFAULT_GUIDE_WORKER_EXCHANGE_DOGFOOD_PREFIX = "guide-worker-exchange-dogfood"
DEFAULT_GUIDE_WORKER_EXCHANGE_DOGFOOD_SNAPSHOT_RELATIVE_PATH = (
    dbc_artifact_path("scheduler", "guide-worker-exchange-dogfood-state.json")
)
DEFAULT_GUIDE_WORKER_EXCHANGE_DOGFOOD_EVENT_LOG_RELATIVE_PATH = (
    dbc_artifact_path("scheduler", "guide-worker-exchange-dogfood-events.jsonl")
)


@dataclass(frozen=True, slots=True)
class GuideWorkerExchangeDogfoodRequest:
    """Inputs for the deterministic guide/worker exchange dogfood workflow."""

    artifact_store_path: Path
    admission_ledger_path: Path
    snapshot_path: Path
    event_log_path: Path
    guide_agent_id: str = "agent:guide"
    worker_agent_id: str = "agent:worker"
    artifact_id_prefix: str = DEFAULT_GUIDE_WORKER_EXCHANGE_DOGFOOD_PREFIX
    timestamp: str = "2026-06-23T00:00:00Z"
    replace_existing: bool = False
    allow_duplicate_admission: bool = False


@dataclass(frozen=True, slots=True)
class GuideWorkerExchangeDogfoodResult:
    """Compact result of the guide/worker exchange dogfood workflow."""

    request: GuideWorkerExchangeDogfoodRequest
    source_artifact_id: str
    source_version: str
    reply_artifact_id: str
    reply_version: str
    scheduler_artifact_id: str
    scheduler_version: str
    scheduler_candidate_id: str
    disposition_artifact_id: str
    disposition_version: str
    worker_mailbox: Mapping[str, object]
    reply_result: Mapping[str, object]
    history: Mapping[str, object]
    action_candidates: Mapping[str, object]
    disposition_result: Mapping[str, object]
    consumption_result: Mapping[str, object]

    @property
    def ok(self) -> bool:
        return bool(self.consumption_result.get("ok"))

    def to_json_dict(self) -> dict[str, object]:
        """Return a stable JSON-compatible dogfood result."""

        request = self.request
        return {
            "ok": self.ok,
            "product_type": "guide_worker_exchange_dogfood",
            "scenario": {
                "candidate_type": "scheduler_submission_candidate",
                "target_surface": "admitExchangeArtifact",
                "runtime_provider": "fake",
                "guide_agent_id": request.guide_agent_id,
                "worker_agent_id": request.worker_agent_id,
                "artifact_id_prefix": request.artifact_id_prefix,
            },
            "paths": {
                "artifact_store_path": str(request.artifact_store_path),
                "admission_ledger_path": str(request.admission_ledger_path),
                "snapshot_path": str(request.snapshot_path),
                "event_log_path": str(request.event_log_path),
            },
            "artifacts": {
                "source": f"{self.source_artifact_id}@{self.source_version}",
                "reply": f"{self.reply_artifact_id}@{self.reply_version}",
                "scheduler_candidate": (
                    f"{self.scheduler_artifact_id}@{self.scheduler_version}"
                ),
                "disposition": (
                    f"{self.disposition_artifact_id}@{self.disposition_version}"
                ),
            },
            "source_artifact_id": self.source_artifact_id,
            "source_version": self.source_version,
            "reply_artifact_id": self.reply_artifact_id,
            "reply_version": self.reply_version,
            "scheduler_artifact_id": self.scheduler_artifact_id,
            "scheduler_version": self.scheduler_version,
            "scheduler_candidate_id": self.scheduler_candidate_id,
            "disposition_artifact_id": self.disposition_artifact_id,
            "disposition_version": self.disposition_version,
            "worker_mailbox": dict(self.worker_mailbox),
            "reply_result": dict(self.reply_result),
            "history": dict(self.history),
            "action_candidates": dict(self.action_candidates),
            "disposition_result": dict(self.disposition_result),
            "consumption_result": dict(self.consumption_result),
            "authority_split": {
                "exchange_store_mutated": True,
                "scheduler_mutated": bool(
                    self.consumption_result.get("authority_split", {}).get(
                        "scheduler_mutated"
                    )
                ),
                "admission_ledger_mutated": True,
                "review_state_mutated": False,
                "handoff_mutated": False,
                "merge_gate_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_persisted": False,
            },
        }


def run_guide_worker_exchange_dogfood(
    request: GuideWorkerExchangeDogfoodRequest,
) -> GuideWorkerExchangeDogfoodResult:
    """Run the deterministic fake-runtime guide/worker exchange workflow."""

    _validate_request(request)

    source_artifact_id = f"{request.artifact_id_prefix}:coordination"
    reply_artifact_id = f"{request.artifact_id_prefix}:worker-reply"
    scheduler_artifact_id = f"{request.artifact_id_prefix}:scheduler-submission"
    disposition_artifact_id = f"{request.artifact_id_prefix}:scheduler-disposition"
    version = "v1"

    store = JsonArtifactVersionStore(request.artifact_store_path)
    store.put(
        _build_source_artifact(
            artifact_id=source_artifact_id,
            version=version,
            request=request,
        ),
        replace_existing=request.replace_existing,
    )
    worker_mailbox = inspect_agent_exchange_mailbox(
        request.artifact_store_path,
        agent_id=request.worker_agent_id,
    ).to_json_dict()

    reply_result = reply_to_exchange_artifact(
        store_path=request.artifact_store_path,
        source_artifact_id=source_artifact_id,
        source_version=version,
        reply_artifact_id=reply_artifact_id,
        reply_version=version,
        producer=request.worker_agent_id,
        text="Worker acknowledges the guide request and will submit a fake scheduler task.",
        structured={
            "product_type": "guide_worker_exchange_reply",
            "status": "acknowledged",
            "next_product": "scheduler_task_submission",
        },
        audience=(request.guide_agent_id,),
        created_at=request.timestamp,
        replace_existing=request.replace_existing,
    ).to_json_dict()

    scheduler_artifact = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id=f"task/{request.artifact_id_prefix}/worker",
            title="Guide/worker dogfood admitted worker task",
            instruction=(
                "Fake-runtime task admitted from the guide/worker exchange "
                "dogfood workflow."
            ),
            agent=AgentSpec(
                agent_id=request.worker_agent_id,
                runtime_provider="fake",
                display_name="Guide worker dogfood worker",
            ),
            context_scope=ContextScope(
                context_id=f"context/{request.artifact_id_prefix}",
                lane_id="lane:guide-worker-dogfood",
                visible_artifacts=(source_artifact_id, reply_artifact_id),
            ),
            acceptance=(
                "Scheduler admission records this task without running a provider.",
                "Authority split reports no Local Work Trajectory mutation.",
            ),
        ),
        artifact_id=scheduler_artifact_id,
        producer=request.worker_agent_id,
        created_at=request.timestamp,
        version=version,
    )
    scheduler_artifact = replace(
        scheduler_artifact,
        audience=(request.guide_agent_id,),
        causality=ExchangeCausality(
            caused_by=(f"{reply_artifact_id}@{version}",),
            correlation_id=source_artifact_id,
        ),
        visibility_policy=VisibilityPolicy(
            audience=(request.guide_agent_id, request.worker_agent_id),
        ),
    )
    store.put(scheduler_artifact, replace_existing=request.replace_existing)

    history = inspect_agent_exchange_history_summary(
        request.artifact_store_path,
        correlation_id=source_artifact_id,
    ).to_json_dict()
    action_candidates = inspect_agent_exchange_action_candidates(
        request.artifact_store_path,
        agent_id=request.guide_agent_id,
        candidate_type="scheduler_submission_candidate",
        admission_ledger_path=request.admission_ledger_path,
    ).to_json_dict()

    scheduler_candidate_id = (
        f"{scheduler_artifact_id}@{version}:scheduler:0"
    )
    disposition_result = decide_agent_exchange_action_candidate(
        store_path=request.artifact_store_path,
        candidate_id=scheduler_candidate_id,
        disposition_artifact_id=disposition_artifact_id,
        disposition_version=version,
        actor=request.guide_agent_id,
        disposition="accept",
        reason="Guide accepts the worker scheduler submission candidate.",
        target_surface="admitExchangeArtifact",
        timestamp=request.timestamp,
        replace_existing=request.replace_existing,
    ).to_json_dict()
    consumption_result = consume_accepted_scheduler_action_candidate(
        artifact_store_path=request.artifact_store_path,
        disposition_artifact_id=disposition_artifact_id,
        disposition_version=version,
        snapshot_path=request.snapshot_path,
        event_log_path=request.event_log_path,
        admission_ledger_path=request.admission_ledger_path,
        allow_duplicate_admission=request.allow_duplicate_admission,
        replace_existing=request.replace_existing,
        actor=request.guide_agent_id,
        timestamp=request.timestamp,
    ).to_json_dict()

    return GuideWorkerExchangeDogfoodResult(
        request=request,
        source_artifact_id=source_artifact_id,
        source_version=version,
        reply_artifact_id=reply_artifact_id,
        reply_version=version,
        scheduler_artifact_id=scheduler_artifact_id,
        scheduler_version=version,
        scheduler_candidate_id=scheduler_candidate_id,
        disposition_artifact_id=disposition_artifact_id,
        disposition_version=version,
        worker_mailbox=worker_mailbox,
        reply_result=reply_result,
        history=history,
        action_candidates=action_candidates,
        disposition_result=disposition_result,
        consumption_result=consumption_result,
    )


def _build_source_artifact(
    *,
    artifact_id: str,
    version: str,
    request: GuideWorkerExchangeDogfoodRequest,
) -> ExchangeArtifact:
    return ExchangeArtifact(
        artifact_id=artifact_id,
        version=version,
        kind="request",
        intent="ask",
        producer=request.guide_agent_id,
        audience=(request.worker_agent_id,),
        scope=ExchangeScope(
            trajectory_id="local-work:guide-worker-exchange-dogfood",
            lane_id="lane:guide-worker-dogfood",
            event_id="event:coordination",
            task_id=f"task/{request.artifact_id_prefix}/coordination",
            context_id=f"context/{request.artifact_id_prefix}",
            agent_id=request.worker_agent_id,
        ),
        causality=ExchangeCausality(correlation_id=artifact_id),
        lifecycle_state="proposed",
        visibility_policy=VisibilityPolicy(
            audience=(request.guide_agent_id, request.worker_agent_id),
        ),
        created_at=request.timestamp,
        parts=(
            ExchangePayloadPart(
                part_type="text",
                text=(
                    "Guide asks worker to acknowledge and produce one "
                    "fake-runtime scheduler submission candidate."
                ),
            ),
            ExchangePayloadPart(
                part_type="structured",
                data={
                    "product_type": "guide_worker_exchange_request",
                    "expected_candidate_type": "scheduler_submission_candidate",
                    "target_surface": "admitExchangeArtifact",
                    "provider_execution_expected": False,
                },
            ),
            ExchangePayloadPart(
                part_type="log",
                log=ExchangeLog(
                    timestamp=request.timestamp,
                    actor=request.guide_agent_id,
                    action="guide_worker_exchange_dogfood_started",
                    channel="guide-worker-exchange-dogfood",
                    summary="Guide created worker-addressed coordination product.",
                    related_artifact_ids=(artifact_id,),
                ),
            ),
        ),
    )


def _validate_request(request: GuideWorkerExchangeDogfoodRequest) -> None:
    if not request.artifact_store_path:
        raise ValueError("guide/worker dogfood requires artifact_store_path")
    if not request.admission_ledger_path:
        raise ValueError("guide/worker dogfood requires admission_ledger_path")
    if not request.snapshot_path:
        raise ValueError("guide/worker dogfood requires snapshot_path")
    if not request.event_log_path:
        raise ValueError("guide/worker dogfood requires event_log_path")
    if not request.guide_agent_id:
        raise ValueError("guide/worker dogfood requires guide_agent_id")
    if not request.worker_agent_id:
        raise ValueError("guide/worker dogfood requires worker_agent_id")
    if request.guide_agent_id == request.worker_agent_id:
        raise ValueError("guide/worker dogfood requires distinct guide and worker agents")
    if not request.artifact_id_prefix:
        raise ValueError("guide/worker dogfood requires artifact_id_prefix")
