"""Live concurrent worker smoke evidence products for CLI runtime providers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .artifact_paths import dbc_artifact_path
from .codex_delivery_smoke import (
    CodexDeliveryBoundedLoopRequest,
    CodexDeliveryBoundedLoopResult,
    CodexDeliveryE2ESmokeRequest,
    run_bounded_codex_delivery_supervisor_loop,
    run_bounded_opencode_delivery_supervisor_loop,
)
from .runtime_adapter import CodexCliClient, OpenCodeCliClient, RuntimeProviderKind
from .runtime_invocation_audit import (
    JsonlRuntimeInvocationLog,
    RuntimeInvocationRecord,
)
from .scheduler_store import recover_scheduler_state

DEFAULT_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_REPORT_RELATIVE_PATH = (
    dbc_artifact_path("scheduler", "live-codex-concurrent-worker-smoke-report.json")
)
DEFAULT_LIVE_OPENCODE_CONCURRENT_WORKER_SMOKE_REPORT_RELATIVE_PATH = (
    dbc_artifact_path("scheduler", "live-opencode-concurrent-worker-smoke-report.json")
)


@dataclass(frozen=True, slots=True)
class RuntimeInvocationOverlap:
    """Pairwise overlap evidence derived from compact runtime audit records."""

    first_invocation_id: str
    second_invocation_id: str
    first_task_id: str
    second_task_id: str
    first_started_at: str
    first_ended_at: str
    second_started_at: str
    second_ended_at: str

    def to_json_dict(self) -> dict[str, object]:
        return {
            "first_invocation_id": self.first_invocation_id,
            "second_invocation_id": self.second_invocation_id,
            "first_task_id": self.first_task_id,
            "second_task_id": self.second_task_id,
            "first_started_at": self.first_started_at,
            "first_ended_at": self.first_ended_at,
            "second_started_at": self.second_started_at,
            "second_ended_at": self.second_ended_at,
        }


@dataclass(frozen=True, slots=True)
class LiveCodexConcurrentWorkerSmokeRequest:
    """Request for the C9 live Codex concurrent worker smoke."""

    loop_request: CodexDeliveryBoundedLoopRequest = field(
        default_factory=lambda: CodexDeliveryBoundedLoopRequest(
            smoke_request=CodexDeliveryE2ESmokeRequest(
                initialize_fixture=True,
                fixture="multilane",
            ),
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=2,
            max_concurrent_deliveries=2,
        )
    )
    report_path: str | Path = DEFAULT_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_REPORT_RELATIVE_PATH
    write_report: bool = True


@dataclass(frozen=True, slots=True)
class LiveOpenCodeConcurrentWorkerSmokeRequest:
    """Request for the live OpenCode concurrent worker smoke."""

    loop_request: CodexDeliveryBoundedLoopRequest = field(
        default_factory=lambda: CodexDeliveryBoundedLoopRequest(
            smoke_request=CodexDeliveryE2ESmokeRequest(
                initialize_fixture=True,
                fixture="multilane",
                runtime_provider="opencode",
                target_task_id="opencode-smoke:worker",
                parallel_task_id="opencode-smoke:parallel-worker",
                waiting_task_id="opencode-smoke:waiting-non-opencode",
                followup_task_id="opencode-smoke:followup",
                codex_agent_id="agent:opencode-smoke-worker",
                parallel_agent_id="agent:opencode-smoke-parallel-worker",
                followup_agent_id="agent:opencode-smoke-followup",
                waiting_agent_id="agent:opencode-smoke-waiting",
                codex_lane_id="lane:opencode-smoke",
                parallel_lane_id="lane:opencode-smoke-parallel",
                followup_lane_id="lane:opencode-smoke",
                trajectory_id="opencode-live-concurrent-worker-smoke",
            ),
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=2,
            max_concurrent_deliveries=2,
        )
    )
    report_path: str | Path = DEFAULT_LIVE_OPENCODE_CONCURRENT_WORKER_SMOKE_REPORT_RELATIVE_PATH
    write_report: bool = True


@dataclass(frozen=True, slots=True)
class LiveCodexConcurrentWorkerSmokeResult:
    """Durable smoke report for live worker concurrency evidence."""

    request: LiveCodexConcurrentWorkerSmokeRequest | LiveOpenCodeConcurrentWorkerSmokeRequest
    loop_result: CodexDeliveryBoundedLoopResult
    runtime_records: tuple[RuntimeInvocationRecord, ...]
    first_concurrent_batch_task_ids: tuple[str, ...]
    first_concurrent_batch_invocation_ids: tuple[str, ...]
    overlaps: tuple[RuntimeInvocationOverlap, ...]
    timing_parse_errors: tuple[str, ...] = ()
    report_path: Path | None = None

    @property
    def runtime_provider(self) -> RuntimeProviderKind:
        provider = self.loop_result.request.smoke_request.runtime_provider
        if provider not in {"codex", "opencode"}:
            raise ValueError(f"unsupported live smoke runtime provider: {provider!r}")
        return provider

    @property
    def worker_task_count(self) -> int:
        recovery = self.loop_result.recovery
        if recovery is None:
            return 0
        return sum(
            1
            for task in recovery.recovered_state.tasks.values()
            if task.agent.runtime_provider == self.runtime_provider
        )

    @property
    def attempted_live_invocation_count(self) -> int:
        return sum(1 for record in self.runtime_records if record.provider == self.runtime_provider)

    @property
    def completed_worker_count(self) -> int:
        recovery = self.loop_result.recovery
        if recovery is None:
            return 0
        return sum(
            1
            for task in recovery.recovered_state.tasks.values()
            if task.agent.runtime_provider == self.runtime_provider
            and task.state == "complete"
        )

    @property
    def failed_worker_count(self) -> int:
        return sum(1 for record in self.runtime_records if record.status == "failed")

    @property
    def skipped_or_waiting_worker_count(self) -> int:
        recovery = self.loop_result.recovery
        if recovery is None:
            return 0
        return sum(
            1
            for task in recovery.recovered_state.tasks.values()
            if task.agent.runtime_provider == self.runtime_provider
            and task.state in {"proposed", "waiting", "blocked", "ready"}
        )

    @property
    def overlap_proven(self) -> bool:
        return bool(self.overlaps)

    @property
    def inconclusive(self) -> bool:
        return not self.overlap_proven

    @property
    def ok(self) -> bool:
        smoke = self.loop_result.request.smoke_request
        return (
            self.worker_task_count >= 3
            and self.attempted_live_invocation_count >= 2
            and self.completed_worker_count >= 3
            and self.failed_worker_count == 0
            and self.loop_result.request.max_concurrent_deliveries >= 2
            and self.loop_result.ok
            and tuple(sorted(self.first_concurrent_batch_task_ids))
            == tuple(sorted((smoke.target_task_id, smoke.parallel_task_id)))
            and self.overlap_proven
            and self.loop_result.to_json_dict()["authority_split"][
                "serialized_writeback"
            ]
            is True
            and self.loop_result.to_json_dict()["authority_split"][
                "local_work_trajectory_mutated"
            ]
            is False
        )

    def to_json_dict(self) -> dict[str, object]:
        provider = self.runtime_provider
        provider_label = _provider_label(provider)
        loop_payload = self.loop_result.to_json_dict()
        runtime_invocations = [
            _compact_runtime_invocation_record(record)
            for record in self.runtime_records
        ]
        counts = {
            "worker_tasks": self.worker_task_count,
            "attempted_live_provider_invocations": self.attempted_live_invocation_count,
            "attempted_live_codex_invocations": (
                self.attempted_live_invocation_count if provider == "codex" else 0
            ),
            "attempted_live_opencode_invocations": (
                self.attempted_live_invocation_count if provider == "opencode" else 0
            ),
            "completed_workers": self.completed_worker_count,
            "failed_workers": self.failed_worker_count,
            "skipped_or_waiting_workers": self.skipped_or_waiting_worker_count,
            "concurrent_batch_count": len(
                {
                    record["concurrent_batch_id"]
                    for iteration in loop_payload["iterations"]
                    for record in iteration["codex_delivery"]["records"]
                    if record.get("attempted")
                    and int(record.get("concurrent_batch_size", 0) or 0) >= 2
                }
            ),
            "overlap_pair_count": len(self.overlaps),
        }
        residual_gaps: list[str] = []
        if self.ok:
            verdict = "passed"
        else:
            verdict = "inconclusive"
            if not self.loop_result.ok:
                residual_gaps.append(
                    f"bounded {provider_label} supervisor loop did not complete successfully"
                )
            if self.attempted_live_invocation_count < 2:
                residual_gaps.append(
                    f"fewer than two live {provider_label} runtime invocations were attempted"
                )
            if self.failed_worker_count:
                residual_gaps.append(f"{self.failed_worker_count} worker invocation(s) failed")
            if self.completed_worker_count < 3:
                residual_gaps.append("fewer than three worker tasks completed")
            if not self.first_concurrent_batch_task_ids:
                residual_gaps.append(
                    f"no concurrent batch with at least two attempted {provider_label} tasks was recorded"
                )
            if self.timing_parse_errors:
                residual_gaps.append("runtime audit timing could not be fully parsed")
            if (
                self.attempted_live_invocation_count >= 2
                and self.first_concurrent_batch_task_ids
                and not self.timing_parse_errors
            ):
                residual_gaps.append(
                    "runtime audit intervals did not overlap despite concurrent batch metadata"
                )
        return {
            "ok": self.ok,
            "runtime_provider": provider,
            "verdict": verdict,
            "diagnostic": (
                f"live {provider_label} invocation overlap proven"
                if self.ok
                else "; ".join(residual_gaps)
                or f"live {provider_label} invocation overlap not proven"
            ),
            "report_path": "" if self.report_path is None else str(self.report_path),
            "counts": counts,
            "first_concurrent_batch": {
                "task_ids": list(self.first_concurrent_batch_task_ids),
                "invocation_ids": list(self.first_concurrent_batch_invocation_ids),
            },
            "overlap": {
                "proven": self.overlap_proven,
                "pairs": [item.to_json_dict() for item in self.overlaps],
                "timing_parse_errors": list(self.timing_parse_errors),
            },
            "runtime_invocations": runtime_invocations,
            "bounded_loop": loop_payload,
            "paths": {
                "scheduler_snapshot_path": str(
                    self.request.loop_request.smoke_request.scheduler_snapshot_path
                ),
                "scheduler_event_log_path": str(
                    self.request.loop_request.smoke_request.scheduler_event_log_path
                ),
                "dispatcher_state_path": str(
                    self.request.loop_request.smoke_request.dispatcher_state_path
                ),
                "dispatch_event_log_path": str(
                    self.request.loop_request.smoke_request.dispatch_event_log_path
                ),
                "delivery_state_path": str(
                    self.request.loop_request.smoke_request.delivery_state_path
                ),
                "delivery_event_log_path": str(
                    self.request.loop_request.smoke_request.delivery_event_log_path
                ),
                "runtime_invocation_log_path": (
                    ""
                    if self.request.loop_request.smoke_request.runtime_invocation_log_path
                    is None
                    else str(
                        self.request.loop_request.smoke_request.runtime_invocation_log_path
                    )
                ),
                "artifact_store_path": str(
                    self.request.loop_request.smoke_request.artifact_store_path
                ),
            },
            "authority_split": {
                "workflow_surface": f"host-owned-live-{provider}-concurrent-worker-smoke",
                "runtime_provider": provider,
                "provider_executed": self.attempted_live_invocation_count > 0,
                "process_parallel_execution": self.overlap_proven,
                "serialized_writeback": True,
                "scheduler_snapshot_mutated": loop_payload["authority_split"][
                    "scheduler_snapshot_mutated"
                ],
                "scheduler_event_log_mutated": loop_payload["authority_split"][
                    "scheduler_event_log_mutated"
                ],
                "dispatcher_state_mutated": loop_payload["authority_split"][
                    "dispatcher_state_mutated"
                ],
                "dispatcher_log_mutated": loop_payload["authority_split"][
                    "dispatcher_log_mutated"
                ],
                "delivery_state_mutated": loop_payload["authority_split"][
                    "delivery_state_mutated"
                ],
                "delivery_log_mutated": loop_payload["authority_split"][
                    "delivery_log_mutated"
                ],
                "exchange_store_mutated": loop_payload["authority_split"][
                    "exchange_store_mutated"
                ],
                "runtime_invocation_log_mutated": loop_payload["authority_split"][
                    "runtime_invocation_log_mutated"
                ],
                "worker_report_consumption_authority": "leader-owned-consumer-only",
                "worker_direct_local_trajectory_mutation": False,
                "mcp_live_provider_surface": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_persisted": False,
            },
            "residual_gaps": residual_gaps,
        }


LiveOpenCodeConcurrentWorkerSmokeResult = LiveCodexConcurrentWorkerSmokeResult


def run_live_codex_concurrent_worker_smoke(
    request: LiveCodexConcurrentWorkerSmokeRequest,
    *,
    codex_cli_client: CodexCliClient,
) -> LiveCodexConcurrentWorkerSmokeResult:
    """Run C9 and write a compact live-concurrency evidence report."""

    return _run_live_concurrent_worker_smoke(
        request,
        provider="codex",
        runtime_client=codex_cli_client,
    )


def run_live_opencode_concurrent_worker_smoke(
    request: LiveOpenCodeConcurrentWorkerSmokeRequest,
    *,
    opencode_cli_client: OpenCodeCliClient,
) -> LiveOpenCodeConcurrentWorkerSmokeResult:
    """Run an OpenCode live-concurrency evidence report."""

    return _run_live_concurrent_worker_smoke(
        request,
        provider="opencode",
        runtime_client=opencode_cli_client,
    )


def _run_live_concurrent_worker_smoke(
    request: LiveCodexConcurrentWorkerSmokeRequest | LiveOpenCodeConcurrentWorkerSmokeRequest,
    *,
    provider: RuntimeProviderKind,
    runtime_client: CodexCliClient | OpenCodeCliClient,
) -> LiveCodexConcurrentWorkerSmokeResult:
    provider_label = _provider_label(provider)
    if request.loop_request.smoke_request.fixture != "multilane":
        raise ValueError(
            f"live {provider_label} concurrent worker smoke requires fixture='multilane'"
        )
    if request.loop_request.max_concurrent_deliveries < 2:
        raise ValueError(
            f"live {provider_label} concurrent worker smoke requires max_concurrent_deliveries >= 2"
        )
    if (
        request.loop_request.smoke_request.initialize_fixture
        and request.loop_request.smoke_request.replace_existing_fixture
    ):
        _clear_rerunnable_smoke_auxiliary_state(request.loop_request.smoke_request)
    if provider == "codex":
        loop_result = run_bounded_codex_delivery_supervisor_loop(
            request.loop_request,
            codex_cli_client=runtime_client,  # type: ignore[arg-type]
        )
    elif provider == "opencode":
        loop_result = run_bounded_opencode_delivery_supervisor_loop(
            request.loop_request,
            opencode_cli_client=runtime_client,  # type: ignore[arg-type]
        )
    else:
        raise ValueError(f"unsupported live concurrent worker smoke provider: {provider!r}")
    runtime_records = _read_runtime_records(loop_result.request.smoke_request)
    first_task_ids, first_invocation_ids = _first_concurrent_batch(loop_result)
    overlaps, timing_errors = _detect_overlaps(runtime_records, provider=provider)
    report_path = Path(request.report_path)
    result = LiveCodexConcurrentWorkerSmokeResult(
        request=request,
        loop_result=loop_result,
        runtime_records=runtime_records,
        first_concurrent_batch_task_ids=first_task_ids,
        first_concurrent_batch_invocation_ids=first_invocation_ids,
        overlaps=overlaps,
        timing_parse_errors=timing_errors,
        report_path=report_path if request.write_report else None,
    )
    if request.write_report:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(result.to_json_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return result


def _read_runtime_records(
    request: CodexDeliveryE2ESmokeRequest,
) -> tuple[RuntimeInvocationRecord, ...]:
    if request.runtime_invocation_log_path is None:
        return ()
    return JsonlRuntimeInvocationLog(request.runtime_invocation_log_path).read_all()


def _clear_rerunnable_smoke_auxiliary_state(
    request: CodexDeliveryE2ESmokeRequest,
) -> None:
    paths: list[str | Path] = [
        request.dispatcher_state_path,
        request.dispatch_event_log_path,
        request.delivery_state_path,
        request.delivery_event_log_path,
        request.artifact_store_path,
    ]
    if request.runtime_invocation_log_path is not None:
        paths.append(request.runtime_invocation_log_path)
    for value in paths:
        path = Path(value)
        if path.exists() and path.is_file():
            path.unlink()


def _first_concurrent_batch(
    loop_result: CodexDeliveryBoundedLoopResult,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    for iteration in loop_result.iterations:
        records = [
            record
            for record in iteration.codex_delivery.records
            if record.attempted and record.concurrent_batch_size >= 2
        ]
        if records:
            return (
                tuple(record.task_id for record in records),
                tuple(record.invocation_id for record in records),
            )
    return (), ()


def _detect_overlaps(
    records: tuple[RuntimeInvocationRecord, ...],
    *,
    provider: RuntimeProviderKind = "codex",
) -> tuple[tuple[RuntimeInvocationOverlap, ...], tuple[str, ...]]:
    parsed: list[tuple[RuntimeInvocationRecord, datetime, datetime]] = []
    errors: list[str] = []
    for record in records:
        try:
            started = _parse_iso_datetime(record.started_at)
            ended = _parse_iso_datetime(record.ended_at)
        except ValueError as exc:
            errors.append(f"{record.invocation_id}: {exc}")
            continue
        parsed.append((record, started, ended))

    overlaps: list[RuntimeInvocationOverlap] = []
    for index, (left, left_started, left_ended) in enumerate(parsed):
        for right, right_started, right_ended in parsed[index + 1 :]:
            if left.task_id == right.task_id:
                continue
            if left.provider != provider or right.provider != provider:
                continue
            if left_started < right_ended and right_started < left_ended:
                overlaps.append(
                    RuntimeInvocationOverlap(
                        first_invocation_id=left.invocation_id,
                        second_invocation_id=right.invocation_id,
                        first_task_id=left.task_id,
                        second_task_id=right.task_id,
                        first_started_at=left.started_at,
                        first_ended_at=left.ended_at,
                        second_started_at=right.started_at,
                        second_ended_at=right.ended_at,
                    )
                )
    return tuple(overlaps), tuple(errors)


def _parse_iso_datetime(value: str) -> datetime:
    if not value:
        raise ValueError("missing ISO timestamp")
    normalized = value.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"invalid ISO timestamp {value!r}") from exc


def _compact_runtime_invocation_record(
    record: RuntimeInvocationRecord,
) -> dict[str, object]:
    return {
        "invocation_id": record.invocation_id,
        "provider": record.provider,
        "status": record.status,
        "started_at": record.started_at,
        "ended_at": record.ended_at,
        "task_id": record.task_id,
        "session_id": record.session_id,
        "run_id": record.run_id,
        "agent_id": record.agent_id,
        "runtime_surface": record.runtime_surface,
        "attempt_count": record.attempt_count,
        "metadata": {
            "lane_id": str(record.metadata.get("lane_id", "")),
            "context_id": str(record.metadata.get("context_id", "")),
            "host_invocation_id": str(record.metadata.get("host_invocation_id", "")),
        },
        "authority_split": record.to_json_dict()["authority_split"],
    }


def _provider_label(provider: RuntimeProviderKind) -> str:
    if provider == "codex":
        return "Codex"
    if provider == "opencode":
        return "OpenCode"
    return str(provider)


__all__ = [
    "DEFAULT_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_REPORT_RELATIVE_PATH",
    "DEFAULT_LIVE_OPENCODE_CONCURRENT_WORKER_SMOKE_REPORT_RELATIVE_PATH",
    "LiveCodexConcurrentWorkerSmokeRequest",
    "LiveCodexConcurrentWorkerSmokeResult",
    "LiveOpenCodeConcurrentWorkerSmokeRequest",
    "LiveOpenCodeConcurrentWorkerSmokeResult",
    "RuntimeInvocationOverlap",
    "run_live_codex_concurrent_worker_smoke",
    "run_live_opencode_concurrent_worker_smoke",
]
