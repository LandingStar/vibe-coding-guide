"""Controlled dogfood fixtures for scheduler operator workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .exchange import ExchangeArtifact
from .exchange_store import JsonArtifactVersionStore, default_exchange_artifact_store_path
from .runtime_adapter import AgentSpec
from .scheduler import ContextScope, TaskDependency
from .scheduler_submission import (
    SchedulerTaskBatchSubmission,
    SchedulerTaskSubmission,
    scheduler_task_batch_submission_to_artifact,
)

DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_ARTIFACT_ID = "fixture:scheduler-operator-dogfood"
DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_VERSION = "v1"
DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_BATCH_ID = "batch:scheduler-operator-dogfood"


@dataclass(frozen=True, slots=True)
class SchedulerOperatorDogfoodFixtureResult:
    """Result of writing one operator-visible scheduler admission fixture."""

    artifact_store_path: Path
    artifact_id: str
    version: str
    batch_id: str
    task_ids: tuple[str, ...]
    dependency_ids: tuple[str, ...]
    replaced_existing: bool = False

    def to_json_dict(self) -> dict[str, object]:
        """Return compact operator-facing fixture metadata."""

        return {
            "ok": True,
            "artifact_store_path": str(self.artifact_store_path),
            "artifact_id": self.artifact_id,
            "version": self.version,
            "product_type": "scheduler_task_batch_submission",
            "batch_id": self.batch_id,
            "task_ids": list(self.task_ids),
            "dependency_ids": list(self.dependency_ids),
            "candidate_created": True,
            "replaced_existing": self.replaced_existing,
            "authority_split": {
                "exchange_store_mutated": True,
                "scheduler_state_mutated": False,
                "admission_ledger_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "host_evidence_written": False,
                "local_work_trajectory_mutated": False,
            },
        }


def build_scheduler_operator_dogfood_batch() -> SchedulerTaskBatchSubmission:
    """Build the deterministic two-task scheduler operator dogfood batch."""

    prepare = SchedulerTaskSubmission(
        task_id="dogfood:prepare",
        title="Prepare scheduler operator dogfood fixture",
        instruction=(
            "Use the fake runtime to complete the first dogfood task. "
            "This task exists only to prove candidate admission and queue advancement."
        ),
        agent=AgentSpec(
            agent_id="agent:dogfood-prepare",
            runtime_provider="fake",
            display_name="Dogfood Prepare Agent",
            tools=("read",),
            max_turns=1,
        ),
        context_scope=ContextScope(
            context_id="context:dogfood-prepare",
            lane_id="lane:dogfood",
        ),
        acceptance=("fake runtime completes dogfood:prepare",),
        output_artifact_id="dogfood:prepare:result",
    )
    verify = SchedulerTaskSubmission(
        task_id="dogfood:verify",
        title="Verify scheduler operator dogfood fixture",
        instruction=(
            "Use the fake runtime to complete the dependent dogfood task after "
            "dogfood:prepare has completed."
        ),
        agent=AgentSpec(
            agent_id="agent:dogfood-verify",
            runtime_provider="fake",
            display_name="Dogfood Verify Agent",
            tools=("read",),
            max_turns=1,
        ),
        context_scope=ContextScope(
            context_id="context:dogfood-verify",
            lane_id="lane:dogfood",
        ),
        acceptance=("fake runtime completes dogfood:verify after dependency satisfaction",),
        output_artifact_id="dogfood:verify:result",
        dependencies=(
            TaskDependency(
                dependency_id="dep:dogfood-prepare->dogfood-verify",
                source_task_id="dogfood:prepare",
                target_task_id="dogfood:verify",
                required_state="complete",
            ),
        ),
    )
    return SchedulerTaskBatchSubmission(
        batch_id=DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_BATCH_ID,
        title="Scheduler operator dogfood fixture",
        summary="Two fake-runtime tasks used to validate the scheduler operator workflow.",
        tasks=(prepare, verify),
    )


def seed_scheduler_operator_dogfood_fixture(
    project_root: str | Path,
    *,
    artifact_store_path: str | Path | None = None,
    artifact_id: str = DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_ARTIFACT_ID,
    version: str = DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_VERSION,
    replace_existing: bool = False,
    created_at: str = "2026-06-19T00:00:00+00:00",
) -> SchedulerOperatorDogfoodFixtureResult:
    """Seed one deterministic scheduler admission candidate into the local store."""

    if not artifact_id:
        raise ValueError("scheduler operator dogfood fixture requires a non-empty artifact_id")
    if not version:
        raise ValueError(
            f"scheduler operator dogfood fixture {artifact_id!r} requires a non-empty version"
        )

    store_path = (
        Path(artifact_store_path)
        if artifact_store_path is not None
        else default_exchange_artifact_store_path(project_root)
    )
    batch = build_scheduler_operator_dogfood_batch()
    artifact = scheduler_task_batch_submission_to_artifact(
        batch,
        artifact_id=artifact_id,
        producer="scheduler-operator-dogfood-fixture",
        created_at=created_at,
        version=version,
    )
    replaced_existing = _store_fixture_artifact(
        store_path,
        artifact,
        replace_existing=replace_existing,
    )
    return SchedulerOperatorDogfoodFixtureResult(
        artifact_store_path=store_path,
        artifact_id=artifact.artifact_id,
        version=artifact.version,
        batch_id=batch.batch_id,
        task_ids=tuple(task.task_id for task in batch.tasks),
        dependency_ids=tuple(
            dependency.dependency_id
            for task in batch.tasks
            for dependency in task.dependencies
        ),
        replaced_existing=replaced_existing,
    )


def _store_fixture_artifact(
    store_path: Path,
    artifact: ExchangeArtifact,
    *,
    replace_existing: bool,
) -> bool:
    store = JsonArtifactVersionStore(store_path)
    replaced_existing = any(
        (record.artifact_id, record.version) == (artifact.artifact_id, artifact.version)
        for record in store.list_records()
    )
    store.put(artifact, replace_existing=replace_existing)
    return replaced_existing
